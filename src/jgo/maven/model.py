"""
Maven dependency model and resolution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from re import findall
from typing import TYPE_CHECKING, Iterable

from .core import Dependency, MavenContext, Project
from .pom import POM

if TYPE_CHECKING:
    pass

_log = logging.getLogger(__name__)

# (groupId, artifactId, classifier, type)
GACT = tuple[str, str, str, str]


@dataclass
class ProfileConstraints:
    """Constraints for profile activation."""

    jdk: str | None = None
    os_name: str | None = None
    os_family: str | None = None
    os_arch: str | None = None
    os_version: str | None = None
    properties: dict[str, str] = field(default_factory=dict)


class Model:
    """
    A minimal Maven metadata model, tracking only dependencies and properties.
    """

    def __init__(
        self,
        pom: POM,
        context: MavenContext | None = None,
        root_dep_mgmt: dict[GACT, "Dependency"] | None = None,
        profile_constraints: ProfileConstraints | None = None,
    ):
        """
        Build a Maven metadata model from the given POM.

        Args:
            pom: A source POM from which to extract metadata (e.g. dependencies).
            context: Maven context for dependency resolution. If None, creates a default context.
            root_dep_mgmt: Optional dependency management from the root project.
                This takes precedence over the local dependency management and is used
                to ensure consistent versions across all transitive dependencies.
            profile_constraints: Optional constraints for profile activation.
        """
        from .core import MavenContext

        self.context = context or MavenContext()
        self.root_dep_mgmt = root_dep_mgmt
        self.profile_constraints = profile_constraints
        self.gav = f"{pom.groupId}:{pom.artifactId}:{pom.version}"
        _log.debug(f"{self.gav}: begin model initialization")

        # Transfer raw metadata from POM source to target model.
        # For now, we handle only dependencies, dependencyManagement, and properties.
        self.deps: dict[GACT, Dependency] = {}
        self.dep_mgmt: dict[GACT, Dependency] = {}
        self.props: dict[str, str] = {}

        # The following steps are adapted from the maven-model-builder:
        # https://maven.apache.org/ref/3.3.9/maven-model-builder/

        # -- PROFILE ACTIVATION AND INJECTION --

        _log.debug(f"{self.gav}: profile activation and injection")

        self._inject_profiles(pom)
        self._merge(pom)

        # -- PARENT RESOLUTION AND INHERITANCE ASSEMBLY --

        _log.debug(f"{self.gav}: parent resolution and inheritance assembly")

        # Merge values up the parent chain into the current model.
        parent = self.context.pom_parent(pom)
        while parent:
            self._inject_profiles(parent)
            self._merge(parent)
            parent = self.context.pom_parent(parent)

        # -- MODEL INTERPOLATION --

        _log.debug(f"{self.gav}: model interpolation")

        # Inject OS-related properties from profile constraints.
        # These are needed for interpolating classifiers like:
        # natives-${scijava.platform.family.longest}-${os.arch}
        if self.profile_constraints:
            os_props = {}
            if self.profile_constraints.os_name:
                os_props["os.name"] = self.profile_constraints.os_name
            if self.profile_constraints.os_arch:
                os_props["os.arch"] = self.profile_constraints.os_arch
            if self.profile_constraints.os_family:
                os_props["os.family"] = self.profile_constraints.os_family
            if self.profile_constraints.os_version:
                os_props["os.version"] = self.profile_constraints.os_version
            # Also inject any explicit properties from constraints
            for k, v in self.profile_constraints.properties.items():
                if k not in os_props:
                    os_props[k] = v
            # Merge with lowest priority (don't override existing props)
            self._merge_props(os_props)

        # Replace ${...} expressions in property values.
        for k in self.props:
            Model._propvalue(k, self.props)

        # Replace ${...} expressions in dependency coordinate values.
        # We must rebuild the dicts because interpolation can change GACT keys.
        self.deps = self._interpolate_deps(self.deps)
        self.dep_mgmt = self._interpolate_deps(self.dep_mgmt)

        # -- DEPENDENCY MANAGEMENT IMPORT --

        _log.debug(f"{self.gav}: dependency management import")

        # NB: BOM-type dependencies imported in the <dependencyManagement> section are
        # fully interpolated before merging their dependencyManagement into this model,
        # without any consideration for differing property values set in this POM's
        # inheritance chain. Therefore, unlike with parent POMs, dependency versions
        # defined indirectly via version properties cannot be overridden by setting
        # those version properties in the consuming POM!
        # NB: We need to copy the dep_mgmt dict to avoid mutating while iterating it.
        self._import_boms(self.dep_mgmt.copy())

        # -- DEPENDENCY MANAGEMENT INJECTION --

        _log.debug(f"{self.gav}: dependency management injection")

        # Log how many managed dependencies we have (including from BOMs)
        if self.root_dep_mgmt:
            _log.debug(
                f"{self.gav}: root_dep_mgmt has {len(self.root_dep_mgmt)} entries"
            )

        _log.debug(f"{self.gav}: local dep_mgmt has {len(self.dep_mgmt)} entries")

        # Handles injection of dependency management into the model.
        # According to Maven semantics, dependency management provides default values for:
        # version, scope, type, classifier, exclusions, and optional flag.
        #
        # IMPORTANT: Root dependency management (from the wrapper/entry point) takes
        # precedence over local dependency management. This ensures that the root project's
        # version constraints are applied consistently across all transitive dependencies.
        for gact, dep in self.deps.items():
            # First check root_dep_mgmt (highest priority), then local dep_mgmt
            root_managed = self.root_dep_mgmt.get(gact) if self.root_dep_mgmt else None
            local_managed = self.dep_mgmt.get(gact, None)
            managed = root_managed or local_managed

            if managed is None:
                # No managed version available
                if not dep.version:  # Check for None or empty string
                    raise ValueError(f"No version available for dependency {dep}")
                continue

            dep_ga = f"{dep.groupId}:{dep.artifactId}"
            source = (
                "root dependencyManagement" if root_managed else "dependencyManagement"
            )

            # Inject version if not set, or if root_dep_mgmt overrides it
            if not dep.version:  # Check for None or empty string
                _log.debug(
                    f"{self.gav}: {dep_ga}: version set to {managed.version} (from {source})"
                )
                dep.set_version(managed.version)
            elif root_managed and dep.version != root_managed.version:
                # Root dep management overrides the version even if already set
                _log.debug(
                    f"{self.gav}: {dep_ga}: version overridden {dep.version} -> {root_managed.version} (from {source})"
                )
                dep.set_version(root_managed.version)

            # Inject scope if not explicitly set
            if dep.scope is None and managed.scope is not None:
                _log.debug(
                    f"{self.gav}: {dep_ga}: scope set to {managed.scope} (from {source})"
                )
                dep.scope = managed.scope

            # Inject exclusions if managed dependency has them and current doesn't
            if managed.exclusions and not dep.exclusions:
                _log.debug(
                    f"{self.gav}: {dep_ga}: exclusions inherited from {source}: {managed.exclusions}"
                )
                dep.exclusions = managed.exclusions
            elif managed.exclusions:
                _log.debug(
                    f"{self.gav}: {dep_ga}: NOT inheriting exclusions (dep already has exclusions: {dep.exclusions})"
                )

        # Any dependencies that still don't have a scope get the default
        for dep in self.deps.values():
            if dep.scope is None:
                dep.scope = "test" if dep.classifier == "tests" else "compile"

        _log.debug(f"{self.gav}: model construction complete")

    def dependencies(
        self,
        resolved: dict[GACT, Dependency] | None = None,
        root_dep_mgmt: dict[GACT, Dependency] | None = None,
        max_depth: int | None = None,
    ) -> list[Dependency]:
        """
        Compute the component's list of dependencies, including transitive dependencies.

        Uses breadth-first traversal (nearest-wins algorithm) to match Maven's behavior.
        Dependencies at depth N are all processed before moving to depth N+1.

        Args:
            resolved:
                Optional dictionary of already-resolved dependency coordinates.
                Items present in this structure will be pruned from the
                returned dependency list rather than recursively explored.
            root_dep_mgmt:
                Optional dependency management from the root project.
                This will be used to override versions of transitive dependencies.
            max_depth:
                Maximum depth to recurse when resolving dependencies. None means unlimited
                (fully transitive). 1 means direct dependencies only (when called on a
                synthetic wrapper POM, this gives the direct dependencies of the wrapped
                components). 0 would mean no dependencies at all.

        Returns:
            The list of Dependency objects.
        """
        all_deps: dict[GACT, Dependency] = {}

        # Determine whether we are currently diving into transitive dependencies.
        recursing: bool = resolved is not None
        if resolved is None:
            resolved = {}
            # At the root level, use our own dependency management for transitive deps
            root_dep_mgmt = self.dep_mgmt

        # Queue for breadth-first traversal: (model, parent_dep, parent_scope, accumulated_exclusions)
        # parent_dep is None for root level
        # parent_scope is used for scope transformation
        # accumulated_exclusions tracks all exclusions from ancestors
        queue: list[tuple[Model, Dependency | None, str | None, tuple]] = [
            (self, None, None, tuple())
        ]
        current_depth = 0

        while queue and (max_depth is None or current_depth <= max_depth):
            # Process all items at current depth
            next_queue: list[tuple[Model, Dependency | None, str | None]] = []

            for model, parent_dep, parent_scope, accumulated_exclusions in queue:
                for gact, dep in model.deps.items():
                    dep_ga = f"{dep.groupId}:{dep.artifactId}"

                    # Skip if already resolved (nearest-wins)
                    if gact in resolved:
                        _log.debug(f"{model.gav}: {dep_ga}: skipped (already resolved)")
                        continue

                    # Skip non-transitive scopes when recursing
                    if recursing and dep.scope not in ("compile", "runtime"):
                        _log.debug(
                            f"{model.gav}: {dep_ga}: skipped (non-transitive scope: {dep.scope})"
                        )
                        continue

                    # Skip optional dependencies when recursing
                    if recursing and dep.optional:
                        _log.debug(f"{model.gav}: {dep_ga}: skipped (optional)")
                        continue

                    # Check exclusions from all ancestors (not just immediate parent)
                    if accumulated_exclusions and Model._is_excluded(
                        dep, accumulated_exclusions
                    ):
                        ancestor_info = (
                            "ancestor"
                            if not parent_dep
                            else f"{parent_dep.groupId}:{parent_dep.artifactId} or ancestor"
                        )
                        _log.debug(
                            f"{model.gav}: {dep_ga}: excluded by {ancestor_info}"
                        )
                        continue

                    # Record this dependency
                    resolved[gact] = dep
                    all_deps[gact] = dep

                    # Apply scope transformation based on parent scope
                    original_scope = dep.scope
                    if parent_scope == "runtime":
                        dep.scope = "runtime"
                    elif parent_scope == "test":
                        dep.scope = "test"

                    if dep.scope != original_scope:
                        _log.debug(
                            f"{model.gav}: {dep_ga}: scope transformed {original_scope} -> {dep.scope}"
                        )

                    # Log the dependency
                    if parent_dep:
                        _log.debug(f"{model.gav}: {parent_dep} -> {dep}")
                    else:
                        _log.debug(f"{model.gav}: {dep}")

                    # Queue this dependency's model for next depth level
                    if max_depth is None or current_depth < max_depth:
                        try:
                            dep_model = Model(
                                dep.artifact.component.pom(),
                                model.context,
                                root_dep_mgmt,
                                model.profile_constraints,
                            )
                            # Accumulate exclusions: combine ancestor exclusions with this dep's exclusions
                            new_exclusions = accumulated_exclusions + dep.exclusions
                            next_queue.append(
                                (dep_model, dep, dep.scope, new_exclusions)
                            )
                        except Exception as e:
                            _log.debug(f"Could not build model for {dep}: {e}")

            # Move to next depth level
            queue = next_queue
            current_depth += 1
            recursing = True  # After first level, we're always recursing

        return list(all_deps.values())

    def _import_boms(self, candidates: dict[GACT, Dependency]) -> None:
        """
        Scan the candidates for dependencies of type pom with scope import.

        For each such dependency found, import its dependencyManagement section
        into ours, scanning it recursively for more BOMs to import.

        Args:
            candidates: The candidate dependencies, which might be BOMs.
        """
        for dep in candidates.values():
            if not (dep.scope == "import" and dep.type == "pom"):
                continue

            bom_gav = f"{dep.groupId}:{dep.artifactId}:{dep.version}"
            _log.debug(f"{self.gav}: importing BOM {bom_gav}")

            # Load the POM to import.
            bom_project = self.context.project(dep.groupId, dep.artifactId)
            bom_pom = bom_project.at_version(dep.version).pom()

            # Fully build the BOM's model, agnostic of this one.
            bom_model = Model(
                bom_pom, self.context, profile_constraints=self.profile_constraints
            )

            # Count how many managed deps we're importing
            before_count = len(self.dep_mgmt)

            # Merge the BOM model's <dependencyManagement> into this model.
            self._merge_deps(bom_model.dep_mgmt.values(), managed=True)

            after_count = len(self.dep_mgmt)
            new_count = after_count - before_count
            _log.debug(
                f"{self.gav}: imported {new_count} managed deps from BOM {bom_gav} "
                f"(total: {after_count})"
            )

            # Scan BOM <dependencyManagement> for additional potential BOMs.
            self._import_boms(bom_model.dep_mgmt)

    def _merge_deps(self, source: Iterable[Dependency], managed: bool = False) -> None:
        target = self.dep_mgmt if managed else self.deps
        for dep in source:
            # Interpolate coordinates early using available properties
            g = Model._evaluate(dep.groupId, self.props) if dep.groupId else dep.groupId
            a = (
                Model._evaluate(dep.artifactId, self.props)
                if dep.artifactId
                else dep.artifactId
            )
            c = (
                Model._evaluate(dep.classifier, self.props)
                if dep.classifier
                else dep.classifier
            )
            t = Model._evaluate(dep.type, self.props) if dep.type else dep.type

            # Update dep coordinates if interpolation changed them
            if g != dep.groupId:
                dep.artifact.component.project.groupId = g
            if a != dep.artifactId:
                dep.artifact.component.project.artifactId = a
            if c != dep.classifier:
                dep.artifact.classifier = c
            if t != dep.type:
                dep.artifact.packaging = t

            k = (g, a, c, t)
            if k not in target:
                target[k] = dep

    def _merge_props(self, source: dict[str, str]) -> None:
        for k, v in source.items():
            if v is not None and k not in self.props:
                self.props[k] = v

    def _merge(self, pom: POM) -> None:
        """
        Merge metadata from the given POM source into this model.
        For now, we handle only dependencies, dependencyManagement, and properties.
        """
        # Merge special properties first, before dependencies, so that _merge_deps
        # can interpolate dependency coordinates using properties like ${project.groupId}
        self._merge_props(
            {
                "project.groupId": pom.groupId,
                "project.artifactId": pom.artifactId,
                "project.version": pom.version,
                "project.name": pom.name,
                "project.description": pom.description,
            }
        )
        self._merge_props(pom.properties)

        self._merge_deps(self.context.pom_dependencies(pom))
        self._merge_deps(self.context.pom_dependencies(pom, managed=True), managed=True)

    def _inject_profiles(self, pom: POM) -> None:
        """
        Activate and inject profiles from the given POM.
        """
        # Compute active profiles.
        active_profiles = [
            profile
            for profile in pom.elements("profiles/profile")
            if self._is_active_profile(profile)
        ]

        # Merge values from the active profiles into the model.
        for profile in active_profiles:
            profile_dep_els = profile.findall("dependencies/dependency")
            profile_deps = [
                self.context.parse_dependency_element(el) for el in profile_dep_els
            ]
            self._merge_deps(profile_deps)

            profile_dep_mgmt_els = profile.findall(
                "dependencyManagement/dependencies/dependency"
            )
            profile_dep_mgmt = [
                self.context.parse_dependency_element(el) for el in profile_dep_mgmt_els
            ]
            self._merge_deps(profile_dep_mgmt, managed=True)

            profile_props_els = profile.findall("properties/*")
            profile_props = {el.tag: el.text for el in profile_props_els}
            self._merge_props(profile_props)

    def _interpolate_deps(self, deps: dict[GACT, Dependency]) -> dict[GACT, Dependency]:
        """
        Interpolate ${...} expressions in dependency coordinates.

        This rebuilds the deps dict because interpolation can change GACT keys.
        For example, if a dependency has groupId="${project.groupId}", after
        interpolation the GACT key will be different.
        """
        new_deps = {}
        for old_gact, dep in deps.items():
            # Interpolate each coordinate field
            g = Model._evaluate(dep.groupId, self.props) if dep.groupId else dep.groupId
            a = (
                Model._evaluate(dep.artifactId, self.props)
                if dep.artifactId
                else dep.artifactId
            )
            c = (
                Model._evaluate(dep.classifier, self.props)
                if dep.classifier
                else dep.classifier
            )
            t = Model._evaluate(dep.type, self.props) if dep.type else dep.type
            v = Model._evaluate(dep.version, self.props) if dep.version else dep.version

            # Mutate the underlying artifact/component to match interpolated values
            # (This is what set_version() does for the version field)
            if g != dep.groupId:
                dep.artifact.component.project.groupId = g
            if a != dep.artifactId:
                dep.artifact.component.project.artifactId = a
            if c != dep.classifier:
                dep.artifact.classifier = c
            if t != dep.type:
                dep.artifact.packaging = t
            if v != dep.version:
                dep.set_version(v)

            # Build new GACT key with interpolated values
            new_gact = (g, a, c, t)

            # Check for collisions (rare, but possible)
            if new_gact in new_deps and new_gact != old_gact:
                _log.warning(
                    f"Interpolation caused GACT key collision: "
                    f"{old_gact} -> {new_gact}. "
                    f"Keeping first occurrence (nearest wins)."
                )
                continue

            new_deps[new_gact] = dep

        return new_deps

    @staticmethod
    def _is_excluded(dep: Dependency, exclusions: Iterable[Project]):
        return any(
            (
                exclusion.groupId in ["*", dep.groupId]
                and exclusion.artifactId in ["*", dep.artifactId]
            )
            for exclusion in exclusions
        )

    def _is_active_profile(self, el):
        activation = el.find("activation")
        if activation is None:
            return False

        profile_id_el = el.find("id")
        profile_id = profile_id_el.text if profile_id_el is not None else "<unknown>"

        # Check all conditions in the activation block.
        # If ANY condition is met, the profile is active?
        # Actually, Maven documentation says:
        # "The activation element is not a list of conditions, but a list of activators.
        # If any of the activators is triggered, the profile is active."
        # BUT, within a single activator (like <os>), all sub-conditions must match.
        # Wait, no. <activation> contains a list of criteria.
        # If <activeByDefault> is true, it's active.
        # If <jdk> matches, it's active.
        # If <os> matches, it's active.
        # If <property> matches, it's active.
        # If <file> matches, it's active.
        # So it IS an OR logic between top-level elements.

        # However, the issue reported is that 'windows' profile is activated on Linux.
        # This implies that the <os> check is returning True when it shouldn't.

        # Check all conditions in the activation block.
        # If ANY condition is met, the profile is active?
        # Actually, Maven documentation says:
        # "The activation element is not a list of conditions, but a list of activators.
        # If any of the activators is triggered, the profile is active."
        # BUT, within a single activator (like <os>), all sub-conditions must match.
        # Wait, no. <activation> contains a list of criteria.
        # If <activeByDefault> is true, it's active.
        # If <jdk> matches, it's active.
        # If <os> matches, it's active.
        # If <property> matches, it's active.
        # If <file> matches, it's active.
        # So it IS an OR logic between top-level elements.
        #
        # However, the issue reported is that 'windows' profile is activated on Linux.
        # This implies that the <os> check is returning True when it shouldn't.
        #
        # Wait, looking at the code again:
        # The loop `for condition in activation:` iterates over children of <activation>.
        # If ANY child matches, we return True.
        #
        # If a profile has:
        # <activation>
        #   <os>
        #     <family>Windows</family>
        #   </os>
        # </activation>
        #
        # Then `condition` is the <os> element.
        # We check if it matches. If so, return True.
        #
        # If a profile has:
        # <activation>
        #   <activeByDefault>true</activeByDefault>
        #   <os>
        #     <family>Windows</family>
        #   </os>
        # </activation>
        #
        # Then we check activeByDefault. If true, return True.
        # Then we check os. If matches, return True.
        #
        # This seems correct for OR logic between activators.
        #
        # But wait! The `windows` profile in scijava-common (or wherever) probably looks like:
        # <profile>
        #   <id>windows</id>
        #   <activation>
        #     <os>
        #       <family>Windows</family>
        #     </os>
        #   </activation>
        # ...
        # </profile>
        #
        # If I run with `--os-name Linux`, then `self.profile_constraints.os_family` is None (unless I set it).
        # If `os_family` is None, the check:
        #
        # elif os_condition.tag == "family":
        #     text = os_condition.text
        #     if text.startswith("!"):
        #         if self.profile_constraints.os_family == text[1:]:
        #             match = False
        #     elif (
        #         self.profile_constraints.os_family
        #         and self.profile_constraints.os_family != text
        #     ):
        #         match = False
        #
        # If `self.profile_constraints.os_family` is None (falsy), the `elif` condition is False.
        # So `match` remains True!
        #
        # This is the bug. If a constraint is NOT specified in `profile_constraints`,
        # we should probably NOT match against it?
        #
        # No, if I don't specify `--os-family`, I probably don't want to restrict based on it?
        # But here we are checking if the *profile* requires a specific family.
        # If the profile requires "Windows", and I haven't told jgo what my OS family is,
        # should it match?
        #
        # If I say `--os-name Linux`, I haven't explicitly said "My family is NOT Windows".
        # But usually "Linux" implies family "Unix" or similar.
        #
        # If the user provides *any* OS info, we should probably assume they are providing *complete* OS info
        # for the purpose of matching?
        #
        # Or rather: if the profile *requires* a value for a field, and we don't have it,
        # we can't say it matches.
        #
        # So:
        # if os_condition.tag == "family":
        #    if not self.profile_constraints.os_family:
        #        # We don't know our OS family, so we can't satisfy this condition?
        #        # Or should we assume mismatch?
        #        # If I run on Linux, I might not know my family is "unix".
        #        # But I definitely know it's not "Windows".
        #
        # If the user supplies `--os-name Linux`, they are providing partial info.
        #
        # Let's look at how `mvn` does it. It detects the OS properties from Java system properties.
        # `os.name`, `os.arch`, `os.version`.
        # `os.family` is derived.
        #
        # If we are simulating this, we need to be careful.
        #
        # If `self.profile_constraints.os_family` is None, it means "unknown".
        # If the profile says `<family>Windows</family>`, and we have "unknown" family,
        # should we match?
        #
        # If we match, we might activate Windows profiles on Linux (as seen).
        # If we don't match, we might fail to activate a profile that should be active.
        #
        # Given the user explicitly passed `--os-name Linux`, they are trying to simulate a specific environment.
        # If they didn't pass `--os-family`, maybe we should try to derive it?
        # Or just assume that if a profile requires a family, and we didn't provide one, it's a mismatch.
        #
        # Let's try changing the logic to: if the profile has a condition on a field,
        # and we have a value for that field, check it.
        # If we *don't* have a value for that field, what then?
        #
        # If I say `--os-name Linux`, and the profile wants `<family>Windows</family>`.
        # I have `os_name="Linux"`, `os_family=None`.
        # The profile checks `family`. I have None.
        # Current logic: `if (None and None != "Windows"):` -> False. Match stays True.
        #
        # If I change it to:
        # `if self.profile_constraints.os_family != text:`
        # Then `None != "Windows"` is True. Match becomes False.
        #
        # But what if the profile wants `<family>!Windows</family>`?
        # `text` is "!Windows".
        # `if self.profile_constraints.os_family == "Windows":` -> `None == "Windows"` -> False. Match stays True.
        # This seems correct: if I don't know my family, I can't say it IS Windows, so "Not Windows" is a safe bet?
        # Or is it? "Not Windows" usually means "I know it is something else".
        #
        # If I have NO os info at all, `self.profile_constraints` might be None (handled at top).
        # Or it might be all Nones.
        #
        # If I have all Nones, and profile wants "Windows".
        # `None != "Windows"` -> Match = False.
        # So an empty constraint set would match nothing that requires specific values.
        # This seems safer than matching everything.
        #
        # What about negation?
        # Profile: `!Windows`. Constraint: `None`.
        # `None == "Windows"` is False. Match stays True.
        # So "unknown" matches "!Windows". This seems acceptable.
        #
        # So the fix is to remove the `self.profile_constraints.os_field and` check.
        # Just compare the values directly, treating None as a distinct value that won't equal any string.

        for condition in activation:
            if condition.tag == "activeByDefault":
                if condition.text == "true":
                    _log.debug(f"Profile '{profile_id}' activated by activeByDefault")
                    return True

            elif condition.tag == "jdk":
                # TODO: Tricky...
                pass

            elif condition.tag == "os":
                if not self.profile_constraints:
                    continue

                # <name>Windows XP</name>
                # <family>Windows</family>
                # <arch>x86</arch>
                # <version>5.1.2600</version>
                match = True
                for os_condition in condition:
                    if os_condition.tag == "name":
                        # Maven uses ! to negate
                        text = os_condition.text
                        if text.startswith("!"):
                            if self.profile_constraints.os_name == text[1:]:
                                match = False
                        elif self.profile_constraints.os_name != text:
                            match = False
                    elif os_condition.tag == "family":
                        text = os_condition.text
                        if text.startswith("!"):
                            if self.profile_constraints.os_family == text[1:]:
                                match = False
                        elif self.profile_constraints.os_family != text:
                            match = False
                    elif os_condition.tag == "arch":
                        text = os_condition.text
                        if text.startswith("!"):
                            if self.profile_constraints.os_arch == text[1:]:
                                match = False
                        elif self.profile_constraints.os_arch != text:
                            match = False
                    elif os_condition.tag == "version":
                        text = os_condition.text
                        if text.startswith("!"):
                            if self.profile_constraints.os_version == text[1:]:
                                match = False
                        elif self.profile_constraints.os_version != text:
                            match = False
                if match:
                    _log.debug(f"Profile '{profile_id}' activated by os")
                    return True

            elif condition.tag == "property":
                if not self.profile_constraints:
                    continue

                # <name>sparrow-type</name>
                # <value>African</value>
                name = condition.find("name").text
                value = condition.find("value")
                value = value.text if value is not None else None

                if name in self.profile_constraints.properties:
                    if value is None:
                        # Property existence check
                        _log.debug(
                            f"Profile '{profile_id}' activated by property {name}"
                        )
                        return True
                    elif self.profile_constraints.properties[name] == value:
                        # Property value check
                        _log.debug(
                            f"Profile '{profile_id}' activated by property {name}={value}"
                        )
                        return True

            elif condition.tag == "file":
                # <file>
                # <exists>${basedir}/file2.properties</exists>
                # <missing>${basedir}/file1.properties</missing>
                pass

        return False

    @staticmethod
    def _evaluate(
        expression: str, props: dict[str, str], visited: set[str] | None = None
    ) -> str:
        props_referenced = set(findall(r"\${([^}]*)}", expression))
        if not props_referenced:
            return expression

        value = expression
        for prop_reference in props_referenced:
            replacement = Model._propvalue(prop_reference, props, visited)
            if replacement is None:
                # NB: Leave "${...}" expressions alone when property is absent.
                # This matches Maven behavior, but it still makes me nervous.
                if prop_reference.startswith("project.groupId"):
                    raise ValueError(f"No replacement for {prop_reference}")
                continue
            value = value.replace("${" + prop_reference + "}", replacement)
        return value

    @staticmethod
    def _propvalue(
        propname: str, props: dict[str, str], visited: set[str] | None = None
    ) -> str | None:
        if visited is None:
            visited = set()
        if propname in visited:
            raise ValueError(f"Infinite reference loop for property '{propname}'")
        visited.add(propname)

        expression = props.get(propname, None)
        if expression is None:
            return None
        evaluated = Model._evaluate(expression, props, visited)
        props[propname] = evaluated
        return evaluated

"""
Maven dependency model and resolution.
"""

from __future__ import annotations

import logging
from re import findall
from typing import TYPE_CHECKING, Iterable

from .core import Dependency, MavenContext, Project
from .pom import POM

if TYPE_CHECKING:
    pass

_log = logging.getLogger(__name__)

# (groupId, artifactId, classifier, type)
GACT = tuple[str, str, str, str]


class Model:
    """
    A minimal Maven metadata model, tracking only dependencies and properties.
    """

    def __init__(self, pom: POM, context: MavenContext | None = None):
        """
        Build a Maven metadata model from the given POM.

        Args:
            pom: A source POM from which to extract metadata (e.g. dependencies).
            context: Maven context for dependency resolution. If None, creates a default context.
        """
        from .core import MavenContext

        self.context = context or MavenContext()
        self.gav = f"{pom.groupId}:{pom.artifactId}:{pom.version}"
        _log.debug(f"{self.gav}: begin model initialization")

        # Transfer raw metadata from POM source to target model.
        # For now, we handle only dependencies, dependencyManagement, and properties.
        self.deps: dict[GACT, Dependency] = {}
        self.dep_mgmt: dict[GACT, Dependency] = {}
        self.props: dict[str, str] = {}
        self._merge(pom)

        # The following steps are adapted from the maven-model-builder:
        # https://maven.apache.org/ref/3.3.9/maven-model-builder/

        # -- profile activation and injection --
        _log.debug(f"{self.gav}: profile activation and injection")

        # Compute active profiles.
        active_profiles = [
            profile
            for profile in pom.elements("profiles/profile")
            if Model._is_active_profile(profile)
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

        # -- parent resolution and inheritance assembly --
        _log.debug(f"{self.gav}: parent resolution and inheritance assembly")

        # Merge values up the parent chain into the current model.
        parent = self.context.pom_parent(pom)
        while parent:
            self._merge(parent)
            parent = self.context.pom_parent(parent)

        # -- model interpolation --
        _log.debug(f"{self.gav}: model interpolation")

        # Replace ${...} expressions in property values.
        for k in self.props:
            Model._propvalue(k, self.props)

        # Replace ${...} expressions in dependency coordinate values.
        # We must rebuild the dicts because interpolation can change GACT keys.
        self.deps = self._interpolate_deps(self.deps)
        self.dep_mgmt = self._interpolate_deps(self.dep_mgmt)

        # -- dependency management import --
        _log.debug(f"{self.gav}: dependency management import")

        # NB: BOM-type dependencies imported in the <dependencyManagement> section are
        # fully interpolated before merging their dependencyManagement into this model,
        # without any consideration for differing property values set in this POM's
        # inheritance chain. Therefore, unlike with parent POMs, dependency versions
        # defined indirectly via version properties cannot be overridden by setting
        # those version properties in the consuming POM!
        # NB: We need to copy the dep_mgmt dict to avoid mutating while iterating it.
        self._import_boms(self.dep_mgmt.copy())

        # -- dependency management injection --
        _log.debug(f"{self.gav}: dependency management injection")

        # Handles injection of dependency management into the model.
        # According to Maven semantics, dependency management provides default values for:
        # version, scope, type, classifier, exclusions, and optional flag.
        for gact, dep in self.deps.items():
            managed = self.dep_mgmt.get(gact, None)
            if managed is None:
                # No managed version available
                if not dep.version:  # Check for None or empty string
                    raise ValueError(f"No version available for dependency {dep}")
                continue

            # Inject version if not set
            if not dep.version:  # Check for None or empty string
                dep.set_version(managed.version)

            # Inject scope if not explicitly set
            if dep.scope is None and managed.scope is not None:
                dep.scope = managed.scope

            # Inject exclusions if managed dependency has them and current doesn't
            if managed.exclusions and not dep.exclusions:
                dep.exclusions = managed.exclusions

        # -- set default scopes --
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
        deps: dict[GACT, Dependency] = {}

        # Determine whether we are currently diving into transitive dependencies.
        recursing: bool = resolved is not None
        if resolved is None:
            resolved = {}
            # At the root level, use our own dependency management for transitive deps
            root_dep_mgmt = self.dep_mgmt

        # Process direct dependencies.
        direct_deps: dict[GACT, Dependency] = {}
        for gact, dep in self.deps.items():
            if gact in resolved:
                continue  # Dependency has already been processed.
            if recursing and dep.scope not in ("compile", "runtime"):
                continue  # Non-transitive scope.
            if recursing and dep.optional:
                continue  # Optional dependencies are not transitive.

            # Record this new direct dependency.
            deps[gact] = direct_deps[gact] = dep
            _log.debug(f"{self.gav}: {dep}")

        # Stop if we've reached the maximum depth.
        if max_depth is not None and max_depth <= 0:
            return list(deps.values())

        # Look for transitive dependencies (i.e. dependencies of direct dependencies).
        for dep in direct_deps.values():
            dep_model = Model(dep.artifact.component.pom(), self.context)
            dep_deps = dep_model.dependencies(
                deps,
                root_dep_mgmt,
                max_depth=None if max_depth is None else max_depth - 1,
            )
            for dep_dep in dep_deps:
                if dep_dep.optional:
                    continue  # Optional dependency is not transitive.
                if dep_dep.scope not in ("compile", "runtime"):
                    continue  # Non-transitive scope.
                if Model._is_excluded(dep_dep, dep.exclusions):
                    continue  # Dependency is excluded.
                dep_dep_gact = (
                    dep_dep.groupId,
                    dep_dep.artifactId,
                    dep_dep.classifier,
                    dep_dep.type,
                )
                if dep_dep_gact in resolved:
                    continue  # Dependency has already been processed.

                # Record the transitive dependency.
                deps[dep_dep_gact] = dep_dep

                # Adjust scope of transitive dependency appropriately.
                if dep.scope == "runtime":
                    dep_dep.scope = (
                        "runtime"  # We only need this dependency at runtime.
                    )
                elif dep.scope == "test":
                    dep_dep.scope = "test"  # We only need this dependency for testing.

                # If the transitive dependency has a managed version in the root, prefer it.
                # This ensures the root project's dependency management applies to all dependencies.
                managed_note = ""
                if root_dep_mgmt and dep_dep_gact in root_dep_mgmt:
                    managed_dep = root_dep_mgmt.get(dep_dep_gact)
                    managed_note = f" (managed from {dep_dep.version})"
                    dep_dep.set_version(managed_dep.version)

                _log.debug(f"{self.gav}: {dep} -> {dep_dep}{managed_note}")
        return list(deps.values())

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

            # Load the POM to import.
            bom_project = self.context.project(dep.groupId, dep.artifactId)
            bom_pom = bom_project.at_version(dep.version).pom()

            # Fully build the BOM's model, agnostic of this one.
            bom_model = Model(bom_pom, self.context)

            # Merge the BOM model's <dependencyManagement> into this model.
            self._merge_deps(bom_model.dep_mgmt.values(), managed=True)

            # Scan BOM <dependencyManagement> for additional potential BOMs.
            self._import_boms(bom_model.dep_mgmt)

    def _merge_deps(self, source: Iterable[Dependency], managed: bool = False) -> None:
        target = self.dep_mgmt if managed else self.deps
        for dep in source:
            k = (dep.groupId, dep.artifactId, dep.classifier, dep.type)
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
        self._merge_deps(self.context.pom_dependencies(pom))
        self._merge_deps(self.context.pom_dependencies(pom, managed=True), managed=True)
        self._merge_props(pom.properties)

        # Make an effort to populate Maven special properties.
        # https://github.com/cko/predefined_maven_properties/blob/master/README.md
        self._merge_props(
            {
                "project.groupId": pom.groupId,
                "project.artifactId": pom.artifactId,
                "project.version": pom.version,
                "project.name": pom.name,
                "project.description": pom.description,
            }
        )

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

    @staticmethod
    def _is_active_profile(el):
        activation = el.find("activation")
        if activation is None:
            return False

        for condition in activation:
            if condition.tag == "activeByDefault":
                if condition.text == "true":
                    return True

            elif condition.tag == "jdk":
                # TODO: Tricky...
                pass

            elif condition.tag == "os":
                # <name>Windows XP</name>
                # <family>Windows</family>
                # <arch>x86</arch>
                # <version>5.1.2600</version>
                # TODO: The db.xml generator would benefit from being able to glean
                # platform-specific dependencies. We can support it in the PythonResolver
                # by inventing our own `platforms` field in the Dependency class and
                # changing this method to return a list of platforms rather than True.
                # But the MvnResolver won't be able to populate it naively.
                pass

            elif condition.tag == "property":
                # <name>sparrow-type</name>
                # <value>African</value>
                pass

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

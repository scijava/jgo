"""
Core Maven data structures and configuration.
"""

from hashlib import md5, sha1
from os import environ
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Tuple
from xml.etree import ElementTree

from .util import coord2str, text, binary

if TYPE_CHECKING:
    from .metadata import Metadata
    from .pom import POM
    from .resolver import Resolver

# -- Constants --

DEFAULT_LOCAL_REPOS = []
DEFAULT_REMOTE_REPOS = {"central": "https://repo.maven.apache.org/maven2"}
DEFAULT_CLASSIFIER = ""
DEFAULT_PACKAGING = "jar"


class MavenContext:
    """
    Maven configuration and settings.
    * Local repo cache folder.
    * Local repository storage folders.
    * Remote repository name:URL pairs.
    * Artifact resolution mechanism.
    """

    def __init__(
            self,
            repo_cache: Optional[Path] = None,
            local_repos: Optional[List[Path]] = None,
            remote_repos: Optional[Dict[str, str]] = None,
            resolver: Optional["Resolver"] = None,
    ):
        """
        Create a Maven context.

        :param repo_cache:
            Optional path to Maven local repository cache directory, i.e. destination
            of `mvn install`. Maven typically uses ~/.m2/repository by default.
            This directory is treated as *read-write* by this library, e.g.
            the download() function will store downloaded artifacts there.
            If no local repository cache path is given, Maven defaults will be used
            (M2_REPO environment variable, or ~/.m2/repository by default).
        :param local_repos:
            Optional list of Maven repository storage local paths to check for artifacts.
            These are real Maven repositories, such as those managed by a Sonatype Nexus v2 instance,
            i.e. ultimate destinations of `mvn deploy`, *not* local repository caches!
            These directories are treated as *read-only* by this library.
            If no local repository paths are given, none will be inferred.
        :param remote_repos:
            Optional dict of remote name:URL pairs, with each URL corresponding
            to a remote Maven repository accessible via HTTP/HTTPS.
            If no remote repository paths are given, only Maven Central will be used.
        :param resolver:
            Optional mechanism to use for resolving local paths to artifacts.
            By default, the SimpleResolver will be used.
        """
        self.repo_cache: Path = repo_cache or Path(
            environ.get("M2_REPO", str(Path("~").expanduser() / ".m2" / "repository"))
        )
        self.local_repos: List[Path] = (
            DEFAULT_LOCAL_REPOS if local_repos is None else local_repos
        ).copy()
        self.remote_repos: Dict[str, str] = (
            DEFAULT_REMOTE_REPOS if remote_repos is None else remote_repos
        ).copy()
        # Import here to avoid circular dependency
        if resolver is None:
            from .resolver import SimpleResolver
            resolver = SimpleResolver()
        self.resolver: "Resolver" = resolver

    def project(self, groupId: str, artifactId: str) -> "Project":
        """
        Get a project (G:A) with the given groupId and artifactId.
        :param groupId: The groupId of the project.
        :param artifactId: The artifactId of the project.
        :return: The Project object.
        """
        return Project(self, groupId, artifactId)

    def dependency(self, el: ElementTree.Element) -> "Dependency":
        """
        Create a Dependency object from the given XML element.
        :param el: The XML element from which to create the dependency.
        :return: The Dependency object.
        """
        groupId = el.findtext("groupId")
        artifactId = el.findtext("artifactId")
        assert groupId and artifactId
        version = el.findtext("version")  # NB: Might be None, which means managed.
        classifier = el.findtext("classifier") or DEFAULT_CLASSIFIER
        packaging = el.findtext("type") or DEFAULT_PACKAGING
        scope = el.findtext("scope") or ("test" if packaging == "tests" else "compile")
        optional = el.findtext("optional") == "true" or False
        exclusions = [
            self.project(ex.findtext("groupId"), ex.findtext("artifactId"))
            for ex in el.findall("exclusions/exclusion")
        ]
        project = self.project(groupId, artifactId)
        artifact = project.at_version(version).artifact(classifier, packaging)
        return Dependency(artifact, scope, optional, exclusions)


class Project:
    """
    This is a Maven project: i.e. a groupId+artifactId (G:A) pair.
    """

    def __init__(self, maven_context: MavenContext, groupId: str, artifactId: str):
        self.maven_context = maven_context
        self.groupId = groupId
        self.artifactId = artifactId
        self._metadata: Optional["Metadata"] = None

    def __eq__(self, other):
        return (
            other is not None
            and self.groupId == other.groupId
            and self.artifactId == other.artifactId
        )

    def __hash__(self):
        return hash((self.groupId, self.artifactId))

    def __str__(self):
        return coord2str(self.groupId, self.artifactId)

    @property
    def path_prefix(self) -> Path:
        """
        Relative directory where artifacts of this project are organized.
        E.g. org.jruby:jruby-core -> org/jruby/jruby-core
        """
        return Path(*self.groupId.split("."), self.artifactId)

    def at_version(self, version: str) -> "Component":
        """
        Fix this project (G:A) at a particular version (G:A:V).
        :param version: The version of the project.
        :return: Component at the given version.
        """
        return Component(self, version)

    @property
    def metadata(self) -> "Metadata":
        """Maven metadata about this project, encompassing all known sources."""
        if self._metadata is None:
            from .metadata import Metadatas, MetadataXML
            # Aggregate all locally available project maven-metadata.xml sources.
            repo_cache_dir = self.maven_context.repo_cache / self.path_prefix
            paths = (
                [p for p in repo_cache_dir.glob("maven-metadata*.xml")] +
                [r / self.path_prefix / "maven-metadata.xml"
                 for r in self.maven_context.local_repos]
            )
            self._metadata = Metadatas([MetadataXML(p) for p in paths if p.exists()])
        return self._metadata

    def update(self) -> None:
        """Update metadata from remote sources."""
        raise RuntimeError("Unimplemented")

    @property
    def release(self) -> str:
        """
        The newest release version of this project.
        This is the equivalent of Maven's RELEASE version.
        """
        return self.metadata.release

    @property
    def latest(self) -> str:
        """
        The latest SNAPSHOT version of this project.
        This is the equivalent of Maven's LATEST version.
        """
        return self.metadata.latest

    def versions(
        self, releases: bool = True, snapshots: bool = False, locked: bool = False
    ) -> List["Component"]:
        """
        Get a list of all known versions of this project.

        :param releases:
            If True, include release versions (those not ending in -SNAPSHOT) in the results.
        :param snapshots:
            If True, include snapshot versions (those ending in -SNAPSHOT) in the results.
        :param locked:
            If True, returned snapshot versions will include the timestamp or "lock" flavor
            of the version strings;
            For example: 2.94.3-20230706.150124-1 rather than 2.94.3-SNAPSHOT.
            As such, there may be more entries returned than when this flag is False.
        :return: List of Component objects, each of which represents a known version.
        """
        # TODO: Think about whether multiple timestamped snapshots at the same snapshot
        # version should be one Component, or multiple Components.
        if locked:
            raise RuntimeError("Locked snapshot reporting is unimplemented")
        return [
            self.at_version(v)
            for v in self.metadata.versions
            if (
                (snapshots and v.endswith("-SNAPSHOT")) or
                (releases and not v.endswith("-SNAPSHOT"))
            )
        ]


class Component:
    """
    This is a Project at a particular version -- i.e. a G:A:V.
    One POM per component.
    """

    def __init__(self, project: Project, version: str):
        self.project = project
        self.version = version

    def __eq__(self, other):
        return (
            other is not None
            and self.project == other.project
            and self.version == other.version
        )

    def __hash__(self):
        return hash((self.project, self.version))

    def __str__(self):
        return coord2str(self.groupId, self.artifactId, self.version)

    @property
    def maven_context(self) -> MavenContext:
        """The component's Maven context."""
        return self.project.maven_context

    @property
    def groupId(self) -> str:
        """The component's groupId."""
        return self.project.groupId

    @property
    def artifactId(self) -> str:
        """The component's artifactId."""
        return self.project.artifactId

    @property
    def path_prefix(self) -> Path:
        """
        Relative directory where artifacts of this component are organized.
        E.g. org.jruby:jruby-core:9.3.3.0 -> org/jruby/jruby-core/9.3.3.0
        """
        return self.project.path_prefix / self.version

    def artifact(
        self, classifier: str = DEFAULT_CLASSIFIER, packaging: str = DEFAULT_PACKAGING
    ) -> "Artifact":
        """
        Get an artifact (G:A:P:C:V) associated with this component.

        :param classifier: Classifier of the artifact.
        :param packaging: Packaging/type of the artifact.
        :return:
            The Artifact object representing this component
            with particular classifier and packaging.
        """
        return Artifact(self, classifier, packaging)

    def pom(self) -> "POM":
        """
        Get a data structure with the contents of the POM.

        :return: The POM content.
        """
        from .pom import POM
        pom_artifact = self.artifact(packaging="pom")
        return POM(pom_artifact.resolve(), self.maven_context)


class Artifact:
    """
    This is a Component plus classifier and packaging (G:A:P:C:V).
    One file per artifact.
    """

    def __init__(
        self,
        component: Component,
        classifier: str = DEFAULT_CLASSIFIER,
        packaging: str = DEFAULT_PACKAGING
    ):
        self.component = component
        self.classifier = classifier
        self.packaging = packaging

    def __eq__(self, other):
        return (
            other is not None
            and self.component == other.component
            and self.classifier == other.classifier
            and self.packaging == other.packaging
        )

    def __hash__(self):
        return hash((self.component, self.classifier, self.packaging))

    def __str__(self):
        return coord2str(
            self.groupId, self.artifactId, self.version, self.classifier, self.packaging
        )

    @property
    def maven_context(self) -> MavenContext:
        return self.component.maven_context

    @property
    def groupId(self) -> str:
        """The artifact's groupId."""
        return self.component.groupId

    @property
    def artifactId(self) -> str:
        """The artifact's artifactId."""
        return self.component.artifactId

    @property
    def version(self) -> str:
        """The artifact's version."""
        return self.component.version

    @property
    def filename(self) -> str:
        """
        Filename portion of the artifact path. E.g.:
        - g=org.python a=jython v=2.7.0 -> jython-2.7.0.jar
        - g=org.lwjgl a=lwjgl v=3.3.1 c=natives-linux -> lwjgl-3.3.1-natives-linux.jar
        - g=org.scijava a=scijava-common v=2.94.2 p=pom -> scijava-common-2.94.2.pom
        """
        classifier_suffix = f"-{self.classifier}" if self.classifier else ""
        return f"{self.artifactId}-{self.version}{classifier_suffix}.{self.packaging}"

    @property
    def cached_path(self) -> Optional[Path]:
        """
        Path to the artifact in the linked context's local repository cache.
        Might not actually exist! This just returns where it *would be* if present.
        """
        return (
            self.maven_context.repo_cache / self.component.path_prefix / self.filename
            if self.maven_context.repo_cache
            else None
        )

    def resolve(self) -> Path:
        """
        Resolve a local path to the artifact, downloading it as needed:

        1. If present in the linked local repository cache, use that path.
        2. Else if present in a linked locally available repository storage directory,
           use that path.
        3. Otherwise, invoke the context's resolver to download it.
        """

        # Check Maven local repository cache first if available.
        cached_file = self.cached_path
        if cached_file and cached_file.exists():
            return cached_file

        # Check any locally available Maven repository storage directories.
        for base in self.maven_context.local_repos:
            # TODO: Be smarter than this when version is a SNAPSHOT,
            # because local repo storage has timestamped SNAPSHOT filenames.
            p = base / self.component.path_prefix / self.filename
            if p.exists():
                return p

        # Artifact was not found locally; need to download it.
        return self.maven_context.resolver.download(self)

    def md5(self) -> str:
        """Compute the MD5 hash of the artifact."""
        return self._checksum("md5", md5)

    def sha1(self) -> str:
        """Compute the SHA1 hash of the artifact."""
        return self._checksum("sha1", sha1)

    def _checksum(self, suffix, func):
        p = self.resolve()
        checksum_path = p.parent / f"{p.name}.{suffix}"
        return text(checksum_path) or func(binary(p)).hexdigest()


class Dependency:
    """
    This is an Artifact with scope, optional flag, and exclusions list.
    """

    def __init__(
            self,
            artifact: Artifact,
            scope: str = None,
            optional: bool = False,
            exclusions: Iterable[Project] = None
    ):
        if scope is None:
            scope = "test" if artifact.classifier == "tests" else "compile"
        self.artifact = artifact
        self.scope = scope
        self.optional = optional
        self.exclusions: Tuple[Project] = tuple() if exclusions is None else tuple(exclusions)

    def __str__(self):
        return coord2str(
            self.groupId, self.artifactId, self.version,
            self.classifier, self.type, self.scope, self.optional
        )

    @property
    def maven_context(self) -> MavenContext:
        """The dependency's Maven context."""
        return self.artifact.maven_context

    @property
    def groupId(self) -> str:
        """The dependency's groupId."""
        return self.artifact.groupId

    @property
    def artifactId(self) -> str:
        """The dependency's artifactId."""
        return self.artifact.artifactId

    @property
    def version(self) -> str:
        """The dependency's version."""
        return self.artifact.version

    @property
    def classifier(self) -> str:
        """The dependency's classifier."""
        return self.artifact.classifier

    @property
    def type(self) -> str:
        """The dependency's packaging/type."""
        return self.artifact.packaging

    def set_version(self, version: str) -> None:
        """
        Alter the dependency's version.
        :param version: The new version to use.
        """
        assert isinstance(version, str)
        self.artifact.component.version = version


class XML:
    """Base class for XML document wrappers."""

    def __init__(self, source: Path | str, maven_context: Optional[MavenContext] = None):
        self.source = source
        self.maven_context: MavenContext = maven_context or MavenContext()
        self.tree: ElementTree.ElementTree = (
            ElementTree.ElementTree(ElementTree.fromstring(source))
            if isinstance(source, str)
            else ElementTree.parse(source)
        )
        XML._strip_ns(self.tree.getroot())

    def dump(self, el: ElementTree.Element = None) -> str:
        """
        Get a string representation of the given XML element.
        :param el: Element to stringify, or None to stringify the root node.
        :return: The XML as a string.
        """
        # NB: Be careful: childless ElementTree.Element objects are falsy!
        if el is None:
            el = self.tree.getroot()
        return ElementTree.tostring(el).decode()

    def elements(self, path: str) -> List[ElementTree.Element]:
        return self.tree.findall(path)

    def element(self, path: str) -> Optional[ElementTree.Element]:
        els = self.elements(path)
        assert len(els) <= 1
        return els[0] if els else None

    def values(self, path: str) -> List[str]:
        return [el.text for el in self.elements(path)]

    def value(self, path: str) -> Optional[str]:
        el = self.element(path)
        # NB: Be careful: childless ElementTree.Element objects are falsy!
        return None if el is None else el.text

    @staticmethod
    def _strip_ns(el: ElementTree.Element) -> None:
        """
        Remove namespace prefixes from elements and attributes.
        Credit: https://stackoverflow.com/a/32552776/1207769
        """
        if el.tag.startswith("{"):
            el.tag = el.tag[el.tag.find("}") + 1:]
        for k in list(el.attrib.keys()):
            if k.startswith("{"):
                k2 = k[k.find("}") + 1:]
                el.attrib[k2] = el.attrib[k]
                del el.attrib[k]
        for child in el:
            XML._strip_ns(child)

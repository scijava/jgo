"""
A Python implementation of Maven-related functionality, including parsing of Maven POMs
and Maven metadata files, download of remote artifacts, and calculation of dependencies.
"""

import logging
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from hashlib import md5, sha1
from itertools import combinations
from os import environ
from pathlib import Path
from re import findall, match
from subprocess import run
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union
from xml.etree import ElementTree

import requests


# -- Constants --

DEFAULT_LOCAL_REPOS = []
DEFAULT_REMOTE_REPOS = {"central": "https://repo.maven.apache.org/maven2"}
DEFAULT_CLASSIFIER = ""
DEFAULT_PACKAGING = "jar"


# -- Logging --

_log = logging.getLogger(__name__)


# -- Functions --

def ts2dt(ts: str) -> datetime:
    """
    Convert a Maven-style timestamp string into a Python datetime object.

    Valid forms:
    * 20210702144918 (seen in <lastUpdated> in maven-metadata.xml)
    * 20210702.144917 (seen in deployed SNAPSHOT filenames and <snapshotVersion><value>)
    """
    m = match("(\\d{4})(\\d\\d)(\\d\\d)\\.?(\\d\\d)(\\d\\d)(\\d\\d)", ts)
    if not m: raise ValueError(f"Invalid timestamp: {ts}")
    return datetime(*map(int, m.groups()))  # noqa


def coord2str(
    groupId: str,
    artifactId: str,
    version: Optional[str] = None,
    classifier: Optional[str] = None,
    packaging: Optional[str] = None,
    scope: Optional[str] = None,
    optional: bool = False
):
    """
    Return a string representation of the given Maven coordinates.

    For an overview of Maven coordinates, see:
    * https://maven.apache.org/pom.html#Maven_Coordinates
    * https://maven.apache.org/pom.html#dependencies

    :param groupId: The groupId of the Maven coordinate.
    :param artifactId: The artifactId of the Maven coordinate.
    :param version The version of the Maven coordinate.
    :param classifier: The classifier of the Maven coordinate.
    :param packaging: The packaging/type of the Maven coordinate.
    :param scope: The scope of the Maven dependency.
    :param optional: Whether the Maven dependency is optional.
    :return:
        A string encompassing the given fields, matching the
        G:A:P:C:V:S order used by mvn's dependency:list goal.
    """
    s = f"{groupId}:{artifactId}"
    if packaging: s += f":{packaging}"
    if classifier: s += f":{classifier}"
    if version: s += f":{version}"
    if scope: s += f":{scope}"
    if optional: s += " (optional)"
    return s


def read(p: Path, mode: str) -> Union[str, bytes]:
    with open(p, mode) as f:
        return f.read()


def text(p: Path) -> str:
    return read(p, "r")


def binary(p: Path) -> bytes:
    return read(p, "rb")


# -- Classes --

class Resolver(ABC):
    """
    Logic for doing non-trivial Maven-related things, including:
    * downloading and caching an artifact from a remote repository; and
    * determining the dependencies of a particular Maven component.
    """

    @abstractmethod
    def download(self, artifact: "Artifact") -> Optional[Path]:
        """
        Download an artifact file from a remote repository.
        :param artifact: The artifact for which a local path should be resolved.
        :return: Local path to the saved artifact, or None if the artifact cannot be resolved.
        """
        ...

    @abstractmethod
    def dependencies(self, component: "Component") -> List["Dependency"]:
        """
        Determine dependencies for the given Maven component.
        :param component: The component for which to determine the dependencies.
        :return: The list of dependencies.
        """
        ...


class SimpleResolver(Resolver):
    """
    A resolver that works by pure Python code.
    Low overhead, but less feature complete than mvn.
    """

    def download(self, artifact: "Artifact") -> Optional[Path]:
        if artifact.version.endswith("-SNAPSHOT"):
            raise RuntimeError("Downloading of snapshots is not yet implemented.")

        for remote_repo in artifact.env.remote_repos.values():
            url = f"{remote_repo}/{artifact.component.path_prefix}/{artifact.filename}"
            response: requests.Response = requests.get(url)
            if response.status_code == 200:
                # Artifact downloaded successfully.
                # TODO: Also get MD5 and SHA1 files if available.
                # And for each, if it *is* available and successfully gotten,
                # check the actual hash of the downloaded file contents against the expected one.
                cached_file = artifact.cached_path
                assert not cached_file.exists()
                cached_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cached_file, "wb") as f:
                    f.write(response.content)
                _log.debug(f"Downloaded {url} to {cached_file}")
                return cached_file

        raise RuntimeError(f"Artifact {artifact} not found in remote repositories {artifact.env.remote_repos}")

    def dependencies(self, component: "Component") -> List["Dependency"]:
        model = Model(component.pom())
        return list(model.deps.values())


class SysCallResolver(Resolver):
    """
    A resolver that works by shelling out to mvn.
    Requires Maven to be installed.
    """

    def __init__(self, mvn_command: Path):
        self.mvn_command = mvn_command
        self.mvn_flags = ["-B", "-T8"]

    def download(self, artifact: "Artifact") -> Optional[Path]:
        _log.info(f"Downloading artifact: {artifact}")
        assert artifact.env.repo_cache
        assert artifact.groupId
        assert artifact.artifactId
        assert artifact.version
        assert artifact.packaging
        args = [
            f"-Dmaven.repo.local={artifact.env.repo_cache}",
            f"-DgroupId={artifact.groupId}",
            f"-DartifactId={artifact.artifactId}",
            f"-Dversion={artifact.version}",
            f"-Dpackaging={artifact.packaging}",
        ]
        if artifact.classifier:
            args.append(f"-Dclassifier={artifact.classifier}")
        if artifact.env.remote_repos:
            remote_repos = ",".join(f"{name}::::{url}" for name, url in artifact.env.remote_repos.items())
            args.append(f"-DremoteRepositories={remote_repos}")

        self._mvn("dependency:get", *args)

        # The file should now exist in the local repo cache.
        assert artifact.cached_path and artifact.cached_path.exists()
        return artifact.cached_path

    def dependencies(self, component: "Component") -> List["Dependency"]:
        # Invoke the dependency:list goal, direct dependencies only.
        pom_artifact = component.artifact(packaging="pom")
        assert pom_artifact.env.repo_cache
        output = self._mvn(
            "dependency:list",
            "-f", pom_artifact.resolve(),
            "-DexcludeTransitive=true",
            f"-Dmaven.repo.local={pom_artifact.env.repo_cache}"
        )

        # FIXME: Fix the following logic to parse dependency:list output.

        # Filter to include only the actual lines of XML.
        lines = output.splitlines()
        snip = snap = None
        for i, line in enumerate(lines):
            if snip is None and line.startswith("<?xml"):
                snip = i
            elif line == "</project>":
                snap = i
                break
        assert snip is not None and snap is not None
        pom = POM("\n".join(lines[snip:snap + 1]), pom_artifact.env)

        # Extract the flattened dependencies.
        return pom.dependencies()

    def _mvn(self, *args) -> str:
        # TODO: Windows.
        return SysCallResolver._run(self.mvn_command, *self.mvn_flags, *args)

    @staticmethod
    def _run(command, *args) -> str:
        command_and_args = (command,) + args
        _log.debug(f"Executing: {command_and_args}")
        result = run(command_and_args, capture_output=True)
        if result.returncode == 0: return result.stdout.decode()

        error_message = (
            f"Command failed with exit code {result.returncode}:\n"
            f"{command_and_args}"
        )
        if result.stdout: error_message += f"\n\n[stdout]\n{result.stdout.decode()}"
        if result.stderr: error_message += f"\n\n[stderr]\n{result.stderr.decode()}"
        raise RuntimeError(error_message)


class Environment:
    """
    Maven environment.
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
            resolver: Optional[Resolver] = None,
    ):
        """
        Create a Maven environment.

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
            If no local repository paths are given, only Maven Central will be used.
        :param resolver:
            Optional mechanism to use for resolving local paths to artifacts.
            By default, the SimpleResolver will be used.
        """
        self.repo_cache: Path = repo_cache or environ.get("M2_REPO", Path("~").expanduser() / ".m2" / "repository")
        self.local_repos: List[Path] = (DEFAULT_LOCAL_REPOS if local_repos is None else local_repos).copy()
        self.remote_repos: Dict[str, str] = (DEFAULT_REMOTE_REPOS if remote_repos is None else remote_repos).copy()
        self.resolver: Resolver = resolver or SimpleResolver()

    def project(self, groupId: str, artifactId: str) -> "Project":
        """
        TODO
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
    This is a Maven project: i.e. a groupId+artifact (G:A) pair.
    """

    def __init__(self, env: Environment, groupId: str, artifactId: str):
        self.env = env
        self.groupId = groupId
        self.artifactId = artifactId
        self._metadata: Optional[Metadata] = None

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
            # Aggregate all locally available project maven-metadata.xml sources.
            repo_cache_dir = self.env.repo_cache / self.path_prefix
            paths = (
                [p for p in repo_cache_dir.glob("maven-metadata*.xml")] +
                [r / self.path_prefix / "maven-metadata.xml" for r in self.env.local_repos]
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

    def versions(self, releases: bool = True, snapshots: bool = False, locked: bool = False) -> List["Component"]:
        """
        Get a list of all known versions of this project.

        :param releases:
            If True, include release versions (those not ending in -SNAPSHOT) in the results.
        :param snapshots:
            If True, include snapshot versions (those ending in -SNAPSHOT) in the results.
        :param locked:
            If True, returned snapshot versions will include the timestamp or "lock" flavor of the version strings;
            For example: 2.94.3-20230706.150124-1 rather than 2.94.3-SNAPSHOT.
            As such, there may be more entries returned than when this flag is False.
        :return: List of Component objects, each of which represents a known version.
        """
        # TODO: Think about whether multiple timestamped snapshots at the same snapshot version should be
        # one Component, or multiple Components. because we could just have a list of timestamps in the Component
        # as a field... but then we probably violate existing 1-to-many vs 1-to-1 type assumptions regarding how Components and Artifacts relate.
        # You can only "sort of" have an artifact for a SNAPSHOT without a timestamp lock... it's always timestamped on the remote side,
        # but on the local side only implicitly unless Maven's snapshot locking feature is used... confusing.
        if locked: raise RuntimeError("Locked snapshot reporting is unimplemented")
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
    def env(self) -> Environment:
        """The component's Maven environment."""
        return self.project.env

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

    def artifact(self, classifier: str = DEFAULT_CLASSIFIER, packaging: str = DEFAULT_PACKAGING) -> "Artifact":
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
        pom_artifact = self.artifact(packaging="pom")
        return POM(pom_artifact.resolve(), self.env)


class Artifact:
    """
    This is a Component plus classifier and packaging (G:A:P:C:V).
    One file per artifact.
    """

    def __init__(self, component: Component, classifier: str = DEFAULT_CLASSIFIER, packaging: str = DEFAULT_PACKAGING):
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
        return coord2str(self.groupId, self.artifactId, self.version, self.classifier, self.packaging)

    @property
    def env(self) -> Environment:
        return self.component.env

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
        Path to the artifact in the linked environment's local repository cache.
        Might not actually exist! This just returns where it *would be* if present.
        """
        return (
            self.env.repo_cache / self.component.path_prefix / self.filename
            if self.env.repo_cache
            else None
        )

    def resolve(self) -> Path:
        """
        Resolve a local path to the artifact, downloading it as needed:

        1. If present in the linked local repository cache, use that path.
        2. Else if present in a linked locally available repository storage directory, use that path.
        3. Otherwise, invoke the environment's resolver to download it.
        """

        # Check Maven local repository cache first if available.
        cached_file = self.cached_path
        if cached_file and cached_file.exists(): return cached_file

        # Check any locally available Maven repository storage directories.
        for base in self.env.local_repos:
            # TODO: Be smarter than this when version is a SNAPSHOT,
            # because local repo storage has timestamped SNAPSHOT filenames.
            p = base / self.component.path_prefix / self.filename
            if p.exists(): return p

        # Artifact was not found locally; need to download it.
        return self.env.resolver.download(self)

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
        if scope is None: scope = "test" if artifact.classifier == "tests" else "compile"
        self.artifact = artifact
        self.scope = scope
        self.optional = optional
        self.exclusions: Tuple[Project] = tuple() if exclusions is None else tuple(exclusions)

    def __str__(self):
        return coord2str(self.groupId, self.artifactId, self.version, self.classifier, self.type, self.scope, self.optional)

    @property
    def env(self) -> Environment:
        """The dependency's Maven environment."""
        return self.artifact.env

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

    def __init__(self, source: Union[str, Path], env: Optional[Environment] = None):
        self.source = source
        self.env: Environment = env or Environment()
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
        if el is None: el = self.tree.getroot()
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


class POM(XML):
    """
    Convenience wrapper around a Maven POM XML document.
    """

    def artifact(self) -> Artifact:
        """
        Get an Artifact object representing this POM.
        """
        project = self.env.project(self.groupId, self.artifactId)
        return project.at_version(self.version).artifact(packaging="pom")

    def parent(self) -> Optional["POM"]:
        """
        Get POM data for this POM's parent POM, or None if no parent is declared.
        """
        if not self.element("parent"): return None

        g = self.value("parent/groupId")
        a = self.value("parent/artifactId")
        v = self.value("parent/version")
        assert g and a and v
        relativePath = self.value("parent/relativePath")

        if (
            isinstance(self.source, Path) and
            relativePath and
            (parent_path := self.source / relativePath).exists()
        ):
            # Use locally available parent POM file.
            parent_pom = POM(parent_path, self.env)
            if (
                g == parent_pom.groupId and
                a == parent_pom.artifactId and
                v == parent_pom.version
            ):
                return parent_pom

        pom_artifact = self.env.project(g, a).at_version(v).artifact(packaging="pom")
        return POM(pom_artifact.resolve(), self.env)

    @property
    def groupId(self) -> Optional[str]:
        """The POM's <groupId> (or <parent><groupId>) value."""
        return self.value("groupId") or self.value("parent/groupId")

    @property
    def artifactId(self) -> Optional[str]:
        """The POM's <artifactId> value."""
        return self.value("artifactId")

    @property
    def version(self) -> Optional[str]:
        """The POM's <version> (or <parent><version>) value."""
        return self.value("version") or self.value("parent/version")

    @property
    def name(self) -> Optional[str]:
        """The POM's <name> value."""
        return self.value("name")

    @property
    def description(self) -> Optional[str]:
        """The POM's <description> value."""
        return self.value("description")

    @property
    def scmURL(self) -> Optional[str]:
        """The POM's <scm><url> value."""
        return self.value("scm/url")

    @property
    def issuesURL(self) -> Optional[str]:
        """The POM's <issueManagement><url> value."""
        return self.value("issueManagement/url")

    @property
    def ciURL(self) -> Optional[str]:
        """The POM's <ciManagement><url> value."""
        return self.value("ciManagement/url")

    @property
    def developers(self) -> List[Dict[str, Any]]:
        """Dictionary of the POM's <developer> entries."""
        return self._people("developers/developer")

    @property
    def contributors(self) -> List[Dict[str, Any]]:
        """Dictionary of the POM's <contributor> entries."""
        return self._people("contributors/contributor")

    def _people(self, path: str) -> List[Dict[str, Any]]:
        people = []
        for el in self.elements(path):
            person: Dict[str, Any] = {}
            for child in el:
                if len(child) == 0:
                    person[child.tag] = child.text
                else:
                    if child.tag == "properties":
                        for grand in child:
                            person[grand.tag] = grand.text
                    else:
                        person[child.tag] = [grand.text for grand in child]
            people.append(person)
        return people

    @property
    def properties(self) -> Dict[str, str]:
        """Dictionary of key/value pairs from the POM's <properties>."""
        return {el.tag: el.text for el in self.elements("properties/*")}

    def dependencies(self, managed: bool = False) -> List[Dependency]:
        """
        Gets a list of the POM's <dependency> entries,
        represented as Dependency objects.

        :param managed:
            If True, dependency entries will correspond to the POM's
            <dependencyManagement> instead of <dependencies>.
        :return: The list of Dependency objects.
        """
        xpath = "dependencies/dependency"
        if managed: xpath = f"dependencyManagement/{xpath}"
        return [
            self.env.dependency(el)
            for el in self.elements(xpath)
        ]


class Metadata(ABC):

    @property
    @abstractmethod
    def groupId(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def artifactId(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def lastUpdated(self) -> Optional[datetime]: ...

    @property
    @abstractmethod
    def latest(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def versions(self) -> List[str]: ...

    @property
    @abstractmethod
    def lastVersion(self) -> Optional[str]: ...

    @property
    @abstractmethod
    def release(self) -> Optional[str]: ...


class MetadataXML(XML, Metadata):
    """
    Convenience wrapper around a maven-metadata.xml document.
    """

    @property
    def groupId(self) -> Optional[str]:
        return self.value("groupId")

    @property
    def artifactId(self) -> Optional[str]:
        return self.value("artifactId")

    @property
    def lastUpdated(self) -> Optional[datetime]:
        value = self.value("versioning/lastUpdated")
        return ts2dt(value) if value else None

    @property
    def latest(self) -> Optional[str]:
        # WARNING: The <latest> value is often wrong, for reasons I don't know.
        # However, the last <version> under <versions> has the correct value.
        # Consider using lastVersion instead of latest.
        return self.value("versioning/latest")

    @property
    def versions(self) -> List[str]:
        return self.values("versioning/versions/version")

    @property
    def lastVersion(self) -> Optional[str]:
        return vs[-1] if (vs := self.versions) else None

    @property
    def release(self) -> Optional[str]:
        return self.value("versioning/release")


class Metadatas(Metadata):
    """
    A unified Maven metadata combined over a collection of individual Maven metadata.
    The typical use case for this class is to aggregate multiple maven-metadata.xml files
    describing the same project, across multiple local repository cache and storage directories.
    """

    def __init__(self, metadatas: Iterable[Metadata]):
        self.metadatas: List[Metadata] = sorted(metadatas, key=lambda m: m.lastUpdated)
        for a, b in combinations(self.metadatas, 2):
            assert a.groupId == b.groupId and a.artifactId == b.artifactId

    @property
    def groupId(self) -> Optional[str]:
        return self.metadatas[0].groupId if self.metadatas else None

    @property
    def artifactId(self) -> Optional[str]:
        return self.metadatas[0].artifactId if self.metadatas else None

    @property
    def lastUpdated(self) -> Optional[datetime]:
        return self.metadatas[-1].lastUpdated if self.metadatas else None

    @property
    def latest(self) -> Optional[str]:
        return next((m.latest for m in reversed(self.metadatas) if m.latest), None)

    @property
    def versions(self) -> List[str]:
        return [v for m in self.metadatas for v in m.versions]

    @property
    def lastVersion(self) -> Optional[str]:
        return versions[-1] if (versions := self.versions) else None

    @property
    def release(self) -> Optional[str]:
        return next((m.release for m in reversed(self.metadatas) if m.release), None)


# (groupId, artifactId, classifier, type)
GACT = Tuple[str, str, str, str]


class Model:
    """
    A minimal Maven metadata model, tracking only dependencies and properties.
    """

    def __init__(self, pom: "POM"):
        """
        Build a Maven metadata model from the given POM.

        :param pom: A source POM from which to extract metadata (e.g. dependencies).
        """
        self.env = pom.env
        self.gav = f"{pom.groupId}:{pom.artifactId}:{pom.version}"
        _log.debug(f"{self.gav}: begin model initialization")

        # Transfer raw metadata from POM source to target model.
        # For now, we handle only dependencies, dependencyManagement, and properties.
        self.deps: Dict[GACT, Dependency] = {}
        self.dep_mgmt: Dict[GACT, Dependency] = {}
        self.props: Dict[str, str] = {}
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
            profile_deps = [self.env.dependency(el) for el in profile_dep_els]
            self._merge_deps(profile_deps)

            profile_dep_mgmt_els = profile.findall("dependencyManagement/dependencies/dependency")
            profile_dep_mgmt = [self.env.dependency(el) for el in profile_dep_mgmt_els]
            self._merge_deps(profile_dep_mgmt, managed=True)

            profile_props_els = profile.findall("properties/*")
            profile_props = {el.tag: el.text for el in profile_props_els}
            self._merge_props(profile_props)

        # -- parent resolution and inheritance assembly --
        _log.debug(f"{self.gav}: parent resolution and inheritance assembly")

        # Merge values up the parent chain into the current model.
        parent = pom.parent()
        while parent:
            self._merge(parent)
            parent = parent.parent()

        # -- model interpolation --
        _log.debug(f"{self.gav}: model interpolation")

        # Replace ${...} expressions in property values.
        for k in self.props: Model._propvalue(k, self.props)

        # Replace ${...} expressions in dependency coordinate values.
        for dep in list(self.deps.values()) + list(self.dep_mgmt.values()):
            # CTR START HERE --
            # We need to interpolate into dep fields other than version.
            # But changing GACT changes the dict key, which moves the
            # dependency around... so maybe we need to interpolate it
            # sooner? Look more closely at the order of logic here.
            #g = dep.groupId
            #a = dep.artifactId
            v = dep.version
            #if g is not None: dep.set_groupId(Model._evaluate(g, self.props))
            #if g is not None: dep.set_artifactId(Model._evaluate(g, self.props))
            if v is not None: dep.set_version(Model._evaluate(v, self.props))

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
        for gact, dep in self.deps.items():
            if dep.version is not None: continue
            # This dependency's version is still unset; use managed version.
            managed = self.dep_mgmt.get(gact, None)
            if managed is None:
                raise ValueError("No version available for dependency {dep}")
            dep.set_version(managed.version)

        _log.debug(f"{self.gav}: model construction complete")

    def dependencies(self, resolved: Dict[GACT, Dependency] = None) -> List[Dependency]:
        """
        Compute the component's list of dependencies, including transitive dependencies.

        :param resolved:
            Optional dictionary of already-resolved dependency coordinates.
            Items present in this structure will be pruned from the
            returned dependency list rather than recursively explored.
        :return: The list of Dependency objects.
        """
        deps: Dict[GACT, Dependency] = {}

        # Determine whether we are currently diving into transitive dependencies.
        recursing: bool = resolved is not None
        if resolved is None: resolved = {}

        # Process direct dependencies.
        direct_deps: Dict[GACT, Dependency] = {}
        for gact, dep in self.deps.items():
            if gact in resolved: continue  # Dependency has already been processed.
            if recursing and dep.scope not in ("compile", "runtime"): continue  # Non-transitive scope.

            # Record this new direct dependency.
            deps[gact] = direct_deps[gact] = dep
            _log.debug(f"{self.gav}: {dep}")

        # Look for transitive dependencies (i.e. dependencies of direct dependencies).
        for dep in direct_deps.values():
            dep_model = Model(dep.artifact.component.pom())
            dep_deps = dep_model.dependencies(deps)
            for dep_dep in dep_deps:
                if dep_dep.optional: continue  # Optional dependency is not transitive.
                if dep_dep.scope not in ("compile", "runtime"): continue  # Non-transitive scope.
                if Model._is_excluded(dep_dep, dep.exclusions): continue  # Dependency is excluded.
                dep_dep_gact = (dep_dep.groupId, dep_dep.artifactId, dep_dep.classifier, dep_dep.type)
                if dep_dep_gact in resolved: continue  # Dependency has already been processed.

                # Record the transitive dependency.
                deps[dep_dep_gact] = dep_dep

                # Adjust scope of transitive dependency appropriately.
                if dep.scope == "runtime": dep_dep.scope = "runtime"  # We only need this dependency at runtime.
                elif dep.scope == "test": dep_dep.scope = "test"  # We only need this dependency for testing.

                # If the transitive dependency has a managed version, prefer it.
                managed_note = ""
                if dep_dep_gact in self.dep_mgmt:
                    managed_dep = self.dep_mgmt.get(dep_dep_gact)
                    managed_note = f" (managed from {dep_dep.version})"
                    dep_dep.set_version(managed_dep.version)

                _log.debug(f"{self.gav}: {dep} -> {dep_dep}{managed_note}")

        return list(deps.values())

    def _import_boms(self, candidates: Dict[GACT, Dependency]) -> None:
        """
        Scan the candidates for dependencies of type pom with scope import.
        For each such dependency found, import its dependencyManagement section
        into ours, scanning it recursively for more BOMs to import.
        :param candidates: The candidate dependencies, which might be BOMs.
        """
        for dep in candidates.values():
            if not (dep.scope == "import" and dep.type == "pom"): continue

            # Load the POM to import.
            bom_project = self.env.project(dep.groupId, dep.artifactId)
            bom_pom = bom_project.at_version(dep.version).pom()

            # Fully build the BOM's model, agnostic of this one.
            bom_model = Model(bom_pom)

            # Merge the BOM model's <dependencyManagement> into this model.
            self._merge_deps(bom_model.dep_mgmt.values(), managed=True)

            # Scan BOM <dependencyManagement> for additional potential BOMs.
            self._import_boms(bom_model.dep_mgmt)

    def _merge_deps(self, source: Iterable[Dependency], managed: bool = False) -> None:
        target = self.dep_mgmt if managed else self.deps
        for dep in source:
            k = (dep.groupId, dep.artifactId, dep.classifier, dep.type)
            if k not in target: target[k] = dep

    def _merge_props(self, source: Dict[str, str]) -> None:
        for k, v in source.items():
            if v is not None and k not in self.props: self.props[k] = v

    def _merge(self, pom: POM) -> None:
        """
        Merge metadata from the given POM source into this model.
        For now, we handle only dependencies, dependencyManagement, and properties.
        """
        self._merge_deps(pom.dependencies())
        self._merge_deps(pom.dependencies(managed=True), managed=True)
        self._merge_props(pom.properties)

        # Make an effort to populate Maven special properties.
        # https://github.com/cko/predefined_maven_properties/blob/master/README.md
        self._merge_props({
            "project.groupId":     pom.groupId,
            "project.artifactId":  pom.artifactId,
            "project.version":     pom.version,
            "project.name":        pom.name,
            "project.description": pom.description,
        })

    @staticmethod
    def _is_excluded(dep: Dependency, exclusions: Iterable[Project]):
        return any(
            (
                exclusion.groupId in ["*", dep.groupId] and
                exclusion.artifactId in ["*", dep.artifactId]
            )
            for exclusion in exclusions
        )

    @staticmethod
    def _is_active_profile(el):
        activation = el.find("activation")
        if activation is None: return False

        for condition in activation:
            if condition.tag == "activeByDefault":
                if condition.text == "true": return True

            elif condition.tag == "jdk":
                # TODO: Tricky...
                pass

            elif condition.tag == "os":
                # <name>Windows XP</name>
                # <family>Windows</family>
                # <arch>x86</arch>
                # <version>5.1.2600</version>
                # TODO: The db.xml generator would benefit from being able to glean
                # platform-specific dependencies. We can support it in the SimpleResolver
                # by inventing our own `platforms` field in the Dependency class and
                # changing this method to return a list of platforms rather than True.
                # But the SysCallResolver won't be able to populate it naively.
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
            expression: str,
            props: Dict[str, str],
            visited: Optional[Set[str]] = None
    ) -> str:
        props_referenced = set(findall("\\${([^}]*)}", expression))
        if not props_referenced: return expression

        value = expression
        for prop_reference in props_referenced:
            replacement = Model._propvalue(prop_reference, props, visited)
            if replacement is None:
                # NB: Leave "${...}" expressions alone when property is absent.
                # This matches Maven behavior, but it still makes me nervous.
                if prop_reference.startswith("project.groupId"): raise ValueError(f"No replacement for {prop_reference}")
                continue
            value = value.replace("${" + prop_reference + "}", replacement)
        return value

    @staticmethod
    def _propvalue(
            propname: str,
            props: Dict[str, str],
            visited: Optional[Set[str]] = None
    ) -> Optional[str]:
        if visited is None: visited = set()
        if propname in visited:
            raise ValueError("Infinite reference loop for property '{propname}'")
        visited.add(propname)

        expression = props.get(propname, None)
        if expression is None: return None
        evaluated = Model._evaluate(expression, props, visited)
        props[propname] = evaluated
        return evaluated


# -- Main --

def main(args):
    """Main entry point, for use as a standalone command line tool."""
    log_format = "[%(levelname)s] %(message)s"
    log_level = logging.DEBUG if "-d" in args else logging.INFO
    logging.basicConfig(format=log_format, level=log_level)

    env = Environment()

    coords = [arg for arg in args if ":" in arg]
    for coord in coords:
        print(f"[{coord}]")
        tokens = coord.split(":")

        if len(tokens) == 2:
            # Print information about this project (G:A).
            g, a = tokens
            metadata = env.project(g, a).metadata
            for field in (
                "groupId", "artifactId", "lastUpdated",
                "latest", "lastVersion", "release"
            ):
                print(f"{field} = {getattr(metadata, field)}")
            snapshot_count = sum(v.endswith("-SNAPSHOT") for v in metadata.versions)
            release_count = len(metadata.versions) - snapshot_count
            print(f"release version count = {release_count}")
            print(f"snapshot version count = {snapshot_count}")

        elif len(tokens) == 3:
            # Print dependencies of this component (G:A:V).
            g, a, v = tokens
            model = Model(env.project(g, a).at_version(v).pom())
            for dep in model.dependencies():
                print(dep)

        print()


if __name__ == "__main__":
    main(sys.argv[1:])

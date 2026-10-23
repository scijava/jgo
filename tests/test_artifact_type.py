"""
Tests for artifact packaging types vs. file extensions, the deprecated
Artifact.packaging alias, and Component.packaging.
"""

from pathlib import Path

import pytest

from jgo.env._lockfile import LockedDependency, LockFile, compute_sha256
from jgo.maven import MavenContext, PythonResolver, artifact_handler


class NoDownloadResolver(PythonResolver):
    def download(self, artifact):
        raise AssertionError(f"Attempted to download {artifact}")


def _context(repo_cache: Path) -> MavenContext:
    return MavenContext(
        resolver=NoDownloadResolver(),
        repo_cache=repo_cache,
        local_repos=[],
        offline=True,
    )


@pytest.fixture
def component(tmp_path):
    return _context(tmp_path).project("org.example", "foo").at_version("1.0")


# -- Artifact handlers --


@pytest.mark.parametrize(
    "type,expected",
    [
        ("jar", ("jar", "")),
        ("pom", ("pom", "")),
        ("war", ("war", "")),
        ("maven-plugin", ("jar", "")),
        ("bundle", ("jar", "")),
        ("ejb-client", ("jar", "client")),
        ("test-jar", ("jar", "tests")),
        ("java-source", ("jar", "sources")),
        ("javadoc", ("jar", "javadoc")),
    ],
)
def test_artifact_handler(type, expected):
    assert artifact_handler(type) == expected


def test_artifact_handler_unknown_type():
    # Unknown types use the type itself as the extension.
    assert artifact_handler("zip") == ("zip", "")


# -- Artifact type, extension, and filenames --


@pytest.mark.parametrize(
    "type,classifier,filename",
    [
        ("jar", "", "foo-1.0.jar"),
        ("pom", "", "foo-1.0.pom"),
        ("test-jar", "", "foo-1.0-tests.jar"),
        ("maven-plugin", "", "foo-1.0.jar"),
        ("bundle", "", "foo-1.0.jar"),
        ("jar", "sources", "foo-1.0-sources.jar"),
        ("zip", "", "foo-1.0.zip"),
        # An explicit classifier wins over the type's implied one.
        ("test-jar", "other", "foo-1.0-other.jar"),
    ],
)
def test_artifact_filenames(component, type, classifier, filename):
    artifact = component.artifact(classifier, type)
    assert artifact.type == type
    assert artifact.filename == filename
    assert artifact.cached_filename == filename


def test_artifact_extension_and_effective_classifier(component):
    artifact = component.artifact(type="test-jar")
    assert artifact.extension == "jar"
    assert artifact.classifier == ""
    assert artifact.effective_classifier == "tests"
    assert str(artifact) == "org.example:foo:test-jar:1.0"


def test_artifact_default_type(component):
    artifact = component.artifact()
    assert artifact.type == "jar"
    assert artifact.extension == "jar"


def test_test_jar_resolves_tests_classifier_file(tmp_path, component):
    jar = tmp_path / "org/example/foo/1.0/foo-1.0-tests.jar"
    jar.parent.mkdir(parents=True)
    jar.write_bytes(b"tests")
    assert component.artifact(type="test-jar").resolve() == jar


def test_dependency_type(tmp_path):
    dep = _context(tmp_path).create_dependency("org.example:foo:test-jar:1.0")
    assert dep.type == "test-jar"
    assert dep.artifact.type == "test-jar"
    assert dep.artifact.filename == "foo-1.0-tests.jar"


# -- Deprecated packaging alias --


def test_artifact_packaging_keyword_is_deprecated(component):
    with pytest.warns(DeprecationWarning, match="'packaging' is deprecated"):
        artifact = component.artifact(packaging="pom")
    assert artifact.type == "pom"


def test_artifact_constructor_packaging_keyword_is_deprecated(component):
    from jgo.maven import Artifact

    with pytest.warns(DeprecationWarning, match="'packaging' is deprecated"):
        artifact = Artifact(component, packaging="pom")
    assert artifact.type == "pom"


def test_artifact_positional_type_still_works(component):
    from jgo.maven import Artifact

    assert Artifact(component, "", "pom").type == "pom"
    assert component.artifact("", "pom").type == "pom"


def test_artifact_packaging_property_is_deprecated(component):
    artifact = component.artifact(type="test-jar")
    with pytest.warns(DeprecationWarning, match="'packaging' is deprecated"):
        assert artifact.packaging == "test-jar"
    with pytest.warns(DeprecationWarning, match="'packaging' is deprecated"):
        artifact.packaging = "pom"
    assert artifact.type == "pom"


def test_artifact_conflicting_type_and_packaging(component):
    with pytest.warns(DeprecationWarning), pytest.raises(TypeError, match="Conflict"):
        component.artifact(type="jar", packaging="pom")


def test_default_packaging_alias():
    from jgo.maven._core import DEFAULT_PACKAGING, DEFAULT_TYPE

    assert DEFAULT_PACKAGING == DEFAULT_TYPE == "jar"


# -- SNAPSHOT metadata lookup --

SNAPSHOT_METADATA = """\
<metadata>
  <groupId>org.example</groupId>
  <artifactId>foo</artifactId>
  <version>1.0-SNAPSHOT</version>
  <versioning>
    <snapshot>
      <timestamp>20230706.150124</timestamp>
      <buildNumber>1</buildNumber>
    </snapshot>
    <snapshotVersions>
      <snapshotVersion>
        <extension>jar</extension>
        <value>1.0-20230706.150124-1</value>
      </snapshotVersion>
      <snapshotVersion>
        <classifier>tests</classifier>
        <extension>jar</extension>
        <value>1.0-20230706.150124-2</value>
      </snapshotVersion>
    </snapshotVersions>
  </versioning>
</metadata>
"""


def test_snapshot_test_jar_filename(tmp_path):
    snapshot_dir = tmp_path / "org/example/foo/1.0-SNAPSHOT"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "maven-metadata-central.xml").write_text(SNAPSHOT_METADATA)

    component = _context(tmp_path).project("org.example", "foo")
    component = component.at_version("1.0-SNAPSHOT")
    artifact = component.artifact(type="test-jar")
    assert artifact.filename == "foo-1.0-20230706.150124-2-tests.jar"
    assert artifact.cached_filename == "foo-1.0-SNAPSHOT-tests.jar"


def test_get_timestamped_version_packaging_keyword_is_deprecated(tmp_path):
    snapshot_dir = tmp_path / "org/example/foo/1.0-SNAPSHOT"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "maven-metadata-central.xml").write_text(SNAPSHOT_METADATA)

    component = _context(tmp_path).project("org.example", "foo")
    metadata = component.at_version("1.0-SNAPSHOT").snapshot_metadata
    assert metadata is not None
    assert metadata.get_timestamped_version("jar", "tests") == "1.0-20230706.150124-2"
    with pytest.warns(DeprecationWarning, match="'packaging' is deprecated"):
        version = metadata.get_timestamped_version(packaging="jar")
    assert version == "1.0-20230706.150124-1"


# -- Component.packaging --


def _write_pom(repo: Path, packaging: str | None) -> None:
    pom = repo / "org/example/foo/1.0/foo-1.0.pom"
    pom.parent.mkdir(parents=True)
    packaging_el = f"<packaging>{packaging}</packaging>" if packaging else ""
    pom.write_text(
        "<project>"
        "<groupId>org.example</groupId>"
        "<artifactId>foo</artifactId>"
        "<version>1.0</version>"
        f"{packaging_el}"
        "</project>"
    )


@pytest.mark.parametrize("packaging", ["pom", "bundle", "maven-plugin", "war"])
def test_component_packaging(tmp_path, component, packaging):
    _write_pom(tmp_path, packaging)
    assert component.packaging == packaging


def test_component_packaging_defaults_to_jar(tmp_path, component):
    _write_pom(tmp_path, None)
    assert component.packaging == "jar"


def test_component_packaging_reset_by_set_version(tmp_path):
    _write_pom(tmp_path, "bundle")
    pom2 = tmp_path / "org/example/foo/2.0/foo-2.0.pom"
    pom2.parent.mkdir(parents=True)
    pom2.write_text("<project><packaging>pom</packaging></project>")

    dep = _context(tmp_path).create_dependency("org.example:foo:1.0")
    assert dep.artifact.component.packaging == "bundle"
    dep.set_version("2.0")
    assert dep.artifact.component.packaging == "pom"


# -- Lock file --


def test_lockfile_verify_checksums_test_jar(tmp_path):
    jar = tmp_path / "org/example/foo/1.0/foo-1.0-tests.jar"
    jar.parent.mkdir(parents=True)
    jar.write_bytes(b"tests")

    locked = LockedDependency(
        groupId="org.example",
        artifactId="foo",
        version="1.0",
        packaging="test-jar",
        sha256=compute_sha256(jar),
    )
    assert LockFile(dependencies=[locked]).verify_checksums(tmp_path) == []

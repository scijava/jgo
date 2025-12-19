"""
Tests for Coordinate parsing and stringification.
"""

from jgo.parse.coordinate import Coordinate, coord2str

# =============================================================================
# Coordinate.parse() tests
# =============================================================================


def test_parse_minimal():
    """Test parsing minimal G:A coordinate."""
    result = Coordinate.parse("org.example:my-artifact")
    assert result.groupId == "org.example"
    assert result.artifactId == "my-artifact"
    assert result.version is None
    assert result.classifier is None
    assert result.packaging is None
    assert result.scope is None
    assert result.optional is False


def test_parse_with_version():
    """Test parsing G:A:V coordinate."""
    result = Coordinate.parse("org.example:my-artifact:1.2.3")
    assert result.groupId == "org.example"
    assert result.artifactId == "my-artifact"
    assert result.version == "1.2.3"
    assert result.classifier is None
    assert result.packaging is None
    assert result.scope is None


def test_parse_with_version_and_classifier():
    """Test parsing G:A:V:C coordinate."""
    result = Coordinate.parse("org.example:my-artifact:1.2.3:natives-linux")
    assert result.groupId == "org.example"
    assert result.artifactId == "my-artifact"
    assert result.version == "1.2.3"
    assert result.classifier == "natives-linux"
    assert result.packaging is None
    assert result.scope is None


def test_parse_with_packaging_and_version():
    """Test parsing G:A:P:V coordinate (mvn dependency:get format)."""
    result = Coordinate.parse("sc.fiji:trakem2-transform:jar:1.0.1")
    assert result.groupId == "sc.fiji"
    assert result.artifactId == "trakem2-transform"
    assert result.version == "1.0.1"
    assert result.classifier is None
    assert result.packaging == "jar"
    assert result.scope is None


def test_parse_dependency_list_format():
    """Test parsing G:A:P:V:S coordinate (mvn dependency:list format without classifier)."""
    result = Coordinate.parse("args4j:args4j:jar:2.33:runtime")
    assert result.groupId == "args4j"
    assert result.artifactId == "args4j"
    assert result.version == "2.33"
    assert result.classifier is None
    assert result.packaging == "jar"
    assert result.scope == "runtime"


def test_parse_dependency_list_with_classifier():
    """Test parsing G:A:P:C:V:S coordinate (mvn dependency:list format with classifier)."""
    result = Coordinate.parse(
        "org.jogamp.gluegen:gluegen-rt:jar:natives-macosx-universal:2.5.0:compile"
    )
    assert result.groupId == "org.jogamp.gluegen"
    assert result.artifactId == "gluegen-rt"
    assert result.version == "2.5.0"
    assert result.classifier == "natives-macosx-universal"
    assert result.packaging == "jar"
    assert result.scope == "compile"


def test_parse_with_packaging_classifier_version():
    """Test parsing G:A:P:C:V coordinate (user input with packaging and classifier)."""
    result = Coordinate.parse("org.lwjgl:lwjgl:jar:natives-windows:3.3.1")
    assert result.groupId == "org.lwjgl"
    assert result.artifactId == "lwjgl"
    assert result.version == "3.3.1"
    assert result.classifier == "natives-windows"
    assert result.packaging == "jar"
    assert result.scope is None


def test_parse_with_optional():
    """Test parsing coordinate with optional flag."""
    result = Coordinate.parse("org.example:my-artifact:jar:1.2.3:compile (optional)")
    assert result.groupId == "org.example"
    assert result.artifactId == "my-artifact"
    assert result.version == "1.2.3"
    assert result.packaging == "jar"
    assert result.scope == "compile"
    assert result.optional is True


def test_parse_pom_packaging():
    """Test parsing coordinate with pom packaging."""
    result = Coordinate.parse("org.scijava:pom-scijava:pom:37.0.0")
    assert result.groupId == "org.scijava"
    assert result.artifactId == "pom-scijava"
    assert result.version == "37.0.0"
    assert result.packaging == "pom"


def test_parse_war_packaging():
    """Test parsing coordinate with war packaging."""
    result = Coordinate.parse("org.example:my-webapp:war:1.0.0:compile")
    assert result.groupId == "org.example"
    assert result.artifactId == "my-webapp"
    assert result.version == "1.0.0"
    assert result.packaging == "war"
    assert result.scope == "compile"


def test_parse_snapshot_version():
    """Test parsing coordinate with SNAPSHOT version."""
    result = Coordinate.parse("org.example:my-artifact:1.0-SNAPSHOT")
    assert result.groupId == "org.example"
    assert result.artifactId == "my-artifact"
    assert result.version == "1.0-SNAPSHOT"


def test_parse_version_without_digits():
    """Test parsing coordinate with non-numeric version like RELEASE."""
    result = Coordinate.parse("org.example:my-artifact:RELEASE")
    assert result.groupId == "org.example"
    assert result.artifactId == "my-artifact"
    assert result.version == "RELEASE"


def test_parse_test_scope():
    """Test parsing coordinate with test scope."""
    result = Coordinate.parse("junit:junit:jar:4.13.2:test")
    assert result.groupId == "junit"
    assert result.artifactId == "junit"
    assert result.version == "4.13.2"
    assert result.packaging == "jar"
    assert result.scope == "test"


def test_parse_provided_scope():
    """Test parsing coordinate with provided scope."""
    result = Coordinate.parse("javax.servlet:servlet-api:jar:2.5:provided")
    assert result.groupId == "javax.servlet"
    assert result.artifactId == "servlet-api"
    assert result.version == "2.5"
    assert result.packaging == "jar"
    assert result.scope == "provided"


def test_parse_invalid_too_few_parts():
    """Test that parsing fails with too few parts."""
    try:
        Coordinate.parse("org.example")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must have at least groupId and artifactId" in str(e)


def test_parse_edge_case_just_packaging():
    """Test parsing G:A:P where P is a known packaging type."""
    result = Coordinate.parse("org.example:my-artifact:jar")
    assert result.groupId == "org.example"
    assert result.artifactId == "my-artifact"
    assert result.packaging == "jar"
    assert result.version is None


def test_parse_classifier_only_natives():
    """Test parsing G:A:C with natives classifier."""
    result = Coordinate.parse("org.lwjgl:lwjgl:natives-linux")
    assert result.groupId == "org.lwjgl"
    assert result.artifactId == "lwjgl"
    assert result.classifier == "natives-linux"
    assert result.version is None
    assert result.packaging is None


def test_parse_classifier_only_sources():
    """Test parsing G:A:C with sources classifier."""
    result = Coordinate.parse("org.example:my-lib:sources")
    assert result.groupId == "org.example"
    assert result.artifactId == "my-lib"
    assert result.classifier == "sources"
    assert result.version is None


def test_parse_classifier_only_javadoc():
    """Test parsing G:A:C with javadoc classifier."""
    result = Coordinate.parse("org.example:my-lib:javadoc")
    assert result.groupId == "org.example"
    assert result.artifactId == "my-lib"
    assert result.classifier == "javadoc"
    assert result.version is None


def test_parse_classifier_only_tests():
    """Test parsing G:A:C with tests classifier."""
    result = Coordinate.parse("junit:junit:tests")
    assert result.groupId == "junit"
    assert result.artifactId == "junit"
    assert result.classifier == "tests"
    assert result.version is None


def test_parse_classifier_architecture():
    """Test parsing G:A:C with architecture in classifier."""
    result = Coordinate.parse("org.example:native-lib:linux-x86_64")
    assert result.groupId == "org.example"
    assert result.artifactId == "native-lib"
    assert result.classifier == "linux-x86_64"
    assert result.version is None


def test_parse_classifier_macos():
    """Test parsing G:A:C with macos classifier."""
    result = Coordinate.parse("org.jogamp:gluegen-rt:natives-macos")
    assert result.groupId == "org.jogamp"
    assert result.artifactId == "gluegen-rt"
    assert result.classifier == "natives-macos"
    assert result.version is None


# =============================================================================
# Coordinate stringification tests (via str() and coord2str())
# =============================================================================


def test_str_minimal():
    """Test str() on minimal G:A coordinate."""
    coord = Coordinate(groupId="org.example", artifactId="my-artifact")
    assert str(coord) == "org.example:my-artifact"


def test_str_with_version():
    """Test str() on G:A:V coordinate."""
    coord = Coordinate(groupId="org.example", artifactId="my-artifact", version="1.2.3")
    assert str(coord) == "org.example:my-artifact:1.2.3"


def test_str_with_packaging_and_version():
    """Test str() on G:A:P:V coordinate."""
    coord = Coordinate(
        groupId="org.example",
        artifactId="my-artifact",
        version="1.2.3",
        packaging="jar",
    )
    assert str(coord) == "org.example:my-artifact:jar:1.2.3"


def test_str_with_packaging_classifier_version():
    """Test str() on G:A:P:C:V coordinate."""
    coord = Coordinate(
        groupId="org.example",
        artifactId="my-artifact",
        version="1.2.3",
        classifier="natives-linux",
        packaging="jar",
    )
    assert str(coord) == "org.example:my-artifact:jar:natives-linux:1.2.3"


def test_str_full():
    """Test str() on G:A:P:C:V:S coordinate."""
    coord = Coordinate(
        groupId="org.example",
        artifactId="my-artifact",
        version="1.2.3",
        classifier="natives-linux",
        packaging="jar",
        scope="compile",
    )
    assert str(coord) == "org.example:my-artifact:jar:natives-linux:1.2.3:compile"


def test_str_with_optional():
    """Test str() on coordinate with optional flag."""
    coord = Coordinate(
        groupId="org.example",
        artifactId="my-artifact",
        version="1.2.3",
        packaging="jar",
        scope="compile",
        optional=True,
    )
    assert str(coord) == "org.example:my-artifact:jar:1.2.3:compile (optional)"


def test_coord2str_minimal():
    """Test coord2str with minimal G:A."""
    result = coord2str("org.example", "my-artifact")
    assert result == "org.example:my-artifact"


def test_coord2str_with_version():
    """Test coord2str with G:A:V."""
    result = coord2str("org.example", "my-artifact", version="1.2.3")
    assert result == "org.example:my-artifact:1.2.3"


def test_coord2str_with_packaging_and_version():
    """Test coord2str with G:A:P:V."""
    result = coord2str("org.example", "my-artifact", version="1.2.3", packaging="jar")
    assert result == "org.example:my-artifact:jar:1.2.3"


def test_coord2str_with_packaging_classifier_version():
    """Test coord2str with G:A:P:C:V."""
    result = coord2str(
        "org.example",
        "my-artifact",
        version="1.2.3",
        classifier="natives-linux",
        packaging="jar",
    )
    assert result == "org.example:my-artifact:jar:natives-linux:1.2.3"


def test_coord2str_full():
    """Test coord2str with G:A:P:C:V:S."""
    result = coord2str(
        "org.example",
        "my-artifact",
        version="1.2.3",
        classifier="natives-linux",
        packaging="jar",
        scope="compile",
    )
    assert result == "org.example:my-artifact:jar:natives-linux:1.2.3:compile"


def test_coord2str_with_optional():
    """Test coord2str with optional flag."""
    result = coord2str(
        "org.example",
        "my-artifact",
        version="1.2.3",
        packaging="jar",
        scope="compile",
        optional=True,
    )
    assert result == "org.example:my-artifact:jar:1.2.3:compile (optional)"


# =============================================================================
# Round-trip tests
# =============================================================================


def test_roundtrip_simple():
    """Test that parsing and stringifying a simple coordinate is idempotent."""
    original = "org.example:my-artifact:1.2.3"
    coord = Coordinate.parse(original)
    assert str(coord) == original


def test_roundtrip_with_classifier():
    """Test that parsing and stringifying with classifier is idempotent."""
    original = "org.lwjgl:lwjgl:jar:natives-linux:3.3.1"
    coord = Coordinate.parse(original)
    assert str(coord) == original


def test_roundtrip_with_scope():
    """Test that parsing and stringifying with scope is idempotent."""
    original = "junit:junit:jar:4.13.2:test"
    coord = Coordinate.parse(original)
    assert str(coord) == original

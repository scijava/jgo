#!/usr/bin/env python3
"""
Tests for jgo.maven.util functions.
"""

from datetime import datetime

from jgo.maven import util


def test_ts2dt_with_dot():
    """Test the ts2dt function with dot separator."""
    ts = "20210702.144917"
    result = util.ts2dt(ts)
    assert result == datetime(2021, 7, 2, 14, 49, 17)


def test_ts2dt_without_dot():
    """Test the ts2dt function without dot separator."""
    ts = "20210702144918"
    result = util.ts2dt(ts)
    assert result == datetime(2021, 7, 2, 14, 49, 18)


def test_ts2dt_invalid():
    """Test the ts2dt function with invalid timestamp."""
    try:
        util.ts2dt("invalid")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid timestamp" in str(e)


def test_str2coord_minimal():
    """Test parsing minimal G:A coordinate."""
    result = util.str2coord("org.example:my-artifact")
    assert result["groupId"] == "org.example"
    assert result["artifactId"] == "my-artifact"
    assert result["version"] is None
    assert result["classifier"] is None
    assert result["packaging"] is None
    assert result["scope"] is None
    assert result["optional"] is False


def test_str2coord_with_version():
    """Test parsing G:A:V coordinate."""
    result = util.str2coord("org.example:my-artifact:1.2.3")
    assert result["groupId"] == "org.example"
    assert result["artifactId"] == "my-artifact"
    assert result["version"] == "1.2.3"
    assert result["classifier"] is None
    assert result["packaging"] is None
    assert result["scope"] is None


def test_str2coord_with_version_and_classifier():
    """Test parsing G:A:V:C coordinate."""
    result = util.str2coord("org.example:my-artifact:1.2.3:natives-linux")
    assert result["groupId"] == "org.example"
    assert result["artifactId"] == "my-artifact"
    assert result["version"] == "1.2.3"
    assert result["classifier"] == "natives-linux"
    assert result["packaging"] is None
    assert result["scope"] is None


def test_str2coord_with_packaging_and_version():
    """Test parsing G:A:P:V coordinate (mvn dependency:get format)."""
    result = util.str2coord("sc.fiji:trakem2-transform:jar:1.0.1")
    assert result["groupId"] == "sc.fiji"
    assert result["artifactId"] == "trakem2-transform"
    assert result["version"] == "1.0.1"
    assert result["classifier"] is None
    assert result["packaging"] == "jar"
    assert result["scope"] is None


def test_str2coord_dependency_list_format():
    """Test parsing G:A:P:V:S coordinate (mvn dependency:list format without classifier)."""
    result = util.str2coord("args4j:args4j:jar:2.33:runtime")
    assert result["groupId"] == "args4j"
    assert result["artifactId"] == "args4j"
    assert result["version"] == "2.33"
    assert result["classifier"] is None
    assert result["packaging"] == "jar"
    assert result["scope"] == "runtime"


def test_str2coord_dependency_list_with_classifier():
    """Test parsing G:A:P:C:V:S coordinate (mvn dependency:list format with classifier)."""
    result = util.str2coord(
        "org.jogamp.gluegen:gluegen-rt:jar:natives-macosx-universal:2.5.0:compile"
    )
    assert result["groupId"] == "org.jogamp.gluegen"
    assert result["artifactId"] == "gluegen-rt"
    assert result["version"] == "2.5.0"
    assert result["classifier"] == "natives-macosx-universal"
    assert result["packaging"] == "jar"
    assert result["scope"] == "compile"


def test_str2coord_with_packaging_classifier_version():
    """Test parsing G:A:P:C:V coordinate (user input with packaging and classifier)."""
    result = util.str2coord("org.lwjgl:lwjgl:jar:natives-windows:3.3.1")
    assert result["groupId"] == "org.lwjgl"
    assert result["artifactId"] == "lwjgl"
    assert result["version"] == "3.3.1"
    assert result["classifier"] == "natives-windows"
    assert result["packaging"] == "jar"
    assert result["scope"] is None


def test_str2coord_with_optional():
    """Test parsing coordinate with optional flag."""
    result = util.str2coord("org.example:my-artifact:jar:1.2.3:compile (optional)")
    assert result["groupId"] == "org.example"
    assert result["artifactId"] == "my-artifact"
    assert result["version"] == "1.2.3"
    assert result["packaging"] == "jar"
    assert result["scope"] == "compile"
    assert result["optional"] is True


def test_str2coord_pom_packaging():
    """Test parsing coordinate with pom packaging."""
    result = util.str2coord("org.scijava:pom-scijava:pom:37.0.0")
    assert result["groupId"] == "org.scijava"
    assert result["artifactId"] == "pom-scijava"
    assert result["version"] == "37.0.0"
    assert result["packaging"] == "pom"


def test_str2coord_war_packaging():
    """Test parsing coordinate with war packaging."""
    result = util.str2coord("org.example:my-webapp:war:1.0.0:compile")
    assert result["groupId"] == "org.example"
    assert result["artifactId"] == "my-webapp"
    assert result["version"] == "1.0.0"
    assert result["packaging"] == "war"
    assert result["scope"] == "compile"


def test_str2coord_snapshot_version():
    """Test parsing coordinate with SNAPSHOT version."""
    result = util.str2coord("org.example:my-artifact:1.0-SNAPSHOT")
    assert result["groupId"] == "org.example"
    assert result["artifactId"] == "my-artifact"
    assert result["version"] == "1.0-SNAPSHOT"


def test_str2coord_version_without_digits():
    """Test parsing coordinate with non-numeric version like RELEASE."""
    result = util.str2coord("org.example:my-artifact:RELEASE")
    assert result["groupId"] == "org.example"
    assert result["artifactId"] == "my-artifact"
    assert result["version"] == "RELEASE"


def test_str2coord_test_scope():
    """Test parsing coordinate with test scope."""
    result = util.str2coord("junit:junit:jar:4.13.2:test")
    assert result["groupId"] == "junit"
    assert result["artifactId"] == "junit"
    assert result["version"] == "4.13.2"
    assert result["packaging"] == "jar"
    assert result["scope"] == "test"


def test_str2coord_provided_scope():
    """Test parsing coordinate with provided scope."""
    result = util.str2coord("javax.servlet:servlet-api:jar:2.5:provided")
    assert result["groupId"] == "javax.servlet"
    assert result["artifactId"] == "servlet-api"
    assert result["version"] == "2.5"
    assert result["packaging"] == "jar"
    assert result["scope"] == "provided"


def test_str2coord_invalid_too_few_parts():
    """Test that parsing fails with too few parts."""
    try:
        util.str2coord("org.example")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must have at least groupId and artifactId" in str(e)


def test_str2coord_edge_case_just_packaging():
    """Test parsing G:A:P where P is a known packaging type."""
    result = util.str2coord("org.example:my-artifact:jar")
    assert result["groupId"] == "org.example"
    assert result["artifactId"] == "my-artifact"
    assert result["packaging"] == "jar"
    assert result["version"] is None


def test_str2coord_classifier_only_natives():
    """Test parsing G:A:C with natives classifier."""
    result = util.str2coord("org.lwjgl:lwjgl:natives-linux")
    assert result["groupId"] == "org.lwjgl"
    assert result["artifactId"] == "lwjgl"
    assert result["classifier"] == "natives-linux"
    assert result["version"] is None
    assert result["packaging"] is None


def test_str2coord_classifier_only_sources():
    """Test parsing G:A:C with sources classifier."""
    result = util.str2coord("org.example:my-lib:sources")
    assert result["groupId"] == "org.example"
    assert result["artifactId"] == "my-lib"
    assert result["classifier"] == "sources"
    assert result["version"] is None


def test_str2coord_classifier_only_javadoc():
    """Test parsing G:A:C with javadoc classifier."""
    result = util.str2coord("org.example:my-lib:javadoc")
    assert result["groupId"] == "org.example"
    assert result["artifactId"] == "my-lib"
    assert result["classifier"] == "javadoc"
    assert result["version"] is None


def test_str2coord_classifier_only_tests():
    """Test parsing G:A:C with tests classifier."""
    result = util.str2coord("junit:junit:tests")
    assert result["groupId"] == "junit"
    assert result["artifactId"] == "junit"
    assert result["classifier"] == "tests"
    assert result["version"] is None


def test_str2coord_classifier_architecture():
    """Test parsing G:A:C with architecture in classifier."""
    result = util.str2coord("org.example:native-lib:linux-x86_64")
    assert result["groupId"] == "org.example"
    assert result["artifactId"] == "native-lib"
    assert result["classifier"] == "linux-x86_64"
    assert result["version"] is None


def test_str2coord_classifier_macos():
    """Test parsing G:A:C with macos classifier."""
    result = util.str2coord("org.jogamp:gluegen-rt:natives-macos")
    assert result["groupId"] == "org.jogamp"
    assert result["artifactId"] == "gluegen-rt"
    assert result["classifier"] == "natives-macos"
    assert result["version"] is None


def test_coord2str_minimal():
    """Test coord2str with minimal G:A."""
    result = util.coord2str("org.example", "my-artifact")
    assert result == "org.example:my-artifact"


def test_coord2str_with_version():
    """Test coord2str with G:A:V."""
    result = util.coord2str("org.example", "my-artifact", version="1.2.3")
    assert result == "org.example:my-artifact:1.2.3"


def test_coord2str_with_packaging_and_version():
    """Test coord2str with G:A:P:V."""
    result = util.coord2str(
        "org.example", "my-artifact", version="1.2.3", packaging="jar"
    )
    assert result == "org.example:my-artifact:jar:1.2.3"


def test_coord2str_with_packaging_classifier_version():
    """Test coord2str with G:A:P:C:V."""
    result = util.coord2str(
        "org.example",
        "my-artifact",
        version="1.2.3",
        classifier="natives-linux",
        packaging="jar",
    )
    assert result == "org.example:my-artifact:jar:natives-linux:1.2.3"


def test_coord2str_full():
    """Test coord2str with G:A:P:C:V:S."""
    result = util.coord2str(
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
    result = util.coord2str(
        "org.example",
        "my-artifact",
        version="1.2.3",
        packaging="jar",
        scope="compile",
        optional=True,
    )
    assert result == "org.example:my-artifact:jar:1.2.3:compile (optional)"


def test_text(tmp_path):
    """Test the text function."""
    test_file = tmp_path / "test.txt"
    test_content = "Hello, World!\nThis is a test."
    test_file.write_text(test_content)

    result = util.text(test_file)
    assert result == test_content


def test_binary(tmp_path):
    """Test the binary function."""
    test_file = tmp_path / "test.bin"
    test_content = b"\x00\x01\x02\x03\xff\xfe"
    test_file.write_bytes(test_content)

    result = util.binary(test_file)
    assert result == test_content


def test_parse_endpoint_simple():
    """Test parsing simple endpoint."""
    result = util.parse_endpoint("org.example:my-artifact:1.2.3")
    assert len(result["coordinates"]) == 1
    assert result["coordinates"][0]["groupId"] == "org.example"
    assert result["coordinates"][0]["artifactId"] == "my-artifact"
    assert result["coordinates"][0]["version"] == "1.2.3"
    assert result["main_class"] is None
    assert result["managed"] == [False]
    assert result["deprecated_format"] is False


def test_parse_endpoint_multiple_coords():
    """Test parsing endpoint with multiple coordinates."""
    result = util.parse_endpoint("org.example:foo:1.0+com.example:bar:2.0")
    assert len(result["coordinates"]) == 2
    assert result["coordinates"][0]["groupId"] == "org.example"
    assert result["coordinates"][0]["artifactId"] == "foo"
    assert result["coordinates"][1]["groupId"] == "com.example"
    assert result["coordinates"][1]["artifactId"] == "bar"
    assert result["main_class"] is None
    assert result["managed"] == [False, False]


def test_parse_endpoint_with_main_class():
    """Test parsing endpoint with main class (new @ format)."""
    result = util.parse_endpoint("org.example:foo:1.0@org.example.Main")
    assert len(result["coordinates"]) == 1
    assert result["coordinates"][0]["groupId"] == "org.example"
    assert result["main_class"] == "org.example.Main"
    assert result["deprecated_format"] is False


def test_parse_endpoint_multiple_with_main_class():
    """Test parsing multiple coordinates with main class."""
    result = util.parse_endpoint("g:a:1.0+g2:a2:2.0@org.example.Main")
    assert len(result["coordinates"]) == 2
    assert result["main_class"] == "org.example.Main"
    assert result["managed"] == [False, False]


def test_parse_endpoint_with_managed_flag():
    """Test parsing endpoint with managed dependency flag."""
    result = util.parse_endpoint("org.example:foo:1.0!")
    assert len(result["coordinates"]) == 1
    assert result["coordinates"][0]["groupId"] == "org.example"
    assert result["managed"] == [True]


def test_parse_endpoint_mixed_managed():
    """Test parsing endpoint with mixed managed flags."""
    result = util.parse_endpoint("g:a:1.0!+g2:a2:2.0")
    assert len(result["coordinates"]) == 2
    assert result["managed"] == [True, False]


def test_parse_endpoint_escaped_managed():
    """Test parsing endpoint with escaped managed flag."""
    result = util.parse_endpoint("org.example:foo:1.0\\!")
    assert len(result["coordinates"]) == 1
    assert result["managed"] == [True]


def test_parse_endpoint_complex():
    """Test parsing complex endpoint with multiple features."""
    result = util.parse_endpoint("g:a:1.0!+g2:a2:2.0@org.example.Main")
    assert len(result["coordinates"]) == 2
    assert result["coordinates"][0]["groupId"] == "g"
    assert result["coordinates"][1]["groupId"] == "g2"
    assert result["main_class"] == "org.example.Main"
    assert result["managed"] == [True, False]


def test_parse_endpoint_deprecated_colon_at():
    """Test parsing endpoint with deprecated :@ format."""
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = util.parse_endpoint("org.example:foo:1.0:@Main")
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert ":@mainClass" in str(w[0].message)

    assert result["main_class"] == "@Main"
    assert result["deprecated_format"] is True


def test_parse_endpoint_deprecated_colon_mainclass():
    """Test parsing endpoint with deprecated :MainClass format."""
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = util.parse_endpoint("org.example:foo:1.0:org.example.Main")
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)

    assert result["main_class"] == "org.example.Main"
    assert result["deprecated_format"] is True


def test_parse_endpoint_with_classifier():
    """Test parsing endpoint with classifier."""
    result = util.parse_endpoint("org.lwjgl:lwjgl:jar:natives-linux:3.3.1")
    assert len(result["coordinates"]) == 1
    assert result["coordinates"][0]["classifier"] == "natives-linux"
    assert result["coordinates"][0]["packaging"] == "jar"
    assert result["coordinates"][0]["version"] == "3.3.1"

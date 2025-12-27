"""
Tests for Coordinate placement field (module path control).
"""

from jgo.parse.coordinate import Coordinate, coord2str

# =============================================================================
# Placement parsing tests
# =============================================================================


def test_parse_placement_classpath_short():
    """Test parsing coordinate with (c) placement suffix."""
    result = Coordinate.parse("org.example:artifact:1.0(c)")
    assert result.groupId == "org.example"
    assert result.artifactId == "artifact"
    assert result.version == "1.0"
    assert result.placement == "class-path"


def test_parse_placement_classpath_long():
    """Test parsing coordinate with (cp) placement suffix."""
    result = Coordinate.parse("org.example:artifact:1.0(cp)")
    assert result.groupId == "org.example"
    assert result.artifactId == "artifact"
    assert result.version == "1.0"
    assert result.placement == "class-path"


def test_parse_placement_modulepath_short():
    """Test parsing coordinate with (m) placement suffix."""
    result = Coordinate.parse("org.example:artifact:1.0(m)")
    assert result.groupId == "org.example"
    assert result.artifactId == "artifact"
    assert result.version == "1.0"
    assert result.placement == "module-path"


def test_parse_placement_modulepath_long():
    """Test parsing coordinate with (mp) placement suffix."""
    result = Coordinate.parse("org.example:artifact:1.0(mp)")
    assert result.groupId == "org.example"
    assert result.artifactId == "artifact"
    assert result.version == "1.0"
    assert result.placement == "module-path"


def test_parse_placement_modulepath_p():
    """Test parsing coordinate with (p) placement suffix."""
    result = Coordinate.parse("org.example:artifact:1.0(p)")
    assert result.groupId == "org.example"
    assert result.artifactId == "artifact"
    assert result.version == "1.0"
    assert result.placement == "module-path"


def test_parse_no_placement():
    """Test parsing coordinate without placement suffix (auto mode)."""
    result = Coordinate.parse("org.example:artifact:1.0")
    assert result.groupId == "org.example"
    assert result.artifactId == "artifact"
    assert result.version == "1.0"
    assert result.placement is None


def test_parse_placement_with_raw():
    """Test parsing coordinate with both raw (!) and placement suffix."""
    # Raw flag (!) is checked first in parsing, so it comes LAST in the string
    # Placement (c) comes before raw (!)
    result = Coordinate.parse("org.example:artifact:1.0(c)!")
    assert result.groupId == "org.example"
    assert result.artifactId == "artifact"
    assert result.version == "1.0"
    assert result.raw is True
    assert result.placement == "class-path"


def test_parse_placement_with_minimal_coord():
    """Test parsing minimal G:A coordinate with placement."""
    result = Coordinate.parse("org.example:artifact(m)")
    assert result.groupId == "org.example"
    assert result.artifactId == "artifact"
    assert result.version is None
    assert result.placement == "module-path"


def test_parse_placement_with_packaging():
    """Test parsing G:A:P:V coordinate with placement."""
    result = Coordinate.parse("org.example:artifact:jar:1.0(c)")
    assert result.groupId == "org.example"
    assert result.artifactId == "artifact"
    assert result.packaging == "jar"
    assert result.version == "1.0"
    assert result.placement == "class-path"


# =============================================================================
# Placement stringification tests
# =============================================================================


def test_str_placement_classpath():
    """Test str() with class-path placement."""
    coord = Coordinate(
        groupId="org.example",
        artifactId="artifact",
        version="1.0",
        placement="class-path",
    )
    assert str(coord) == "org.example:artifact:1.0(c)"


def test_str_placement_modulepath():
    """Test str() with module-path placement."""
    coord = Coordinate(
        groupId="org.example",
        artifactId="artifact",
        version="1.0",
        placement="module-path",
    )
    assert str(coord) == "org.example:artifact:1.0(m)"


def test_str_no_placement():
    """Test str() without placement (auto mode)."""
    coord = Coordinate(
        groupId="org.example",
        artifactId="artifact",
        version="1.0",
        placement=None,
    )
    assert str(coord) == "org.example:artifact:1.0"


def test_str_placement_with_raw():
    """Test str() with both raw and placement."""
    coord = Coordinate(
        groupId="org.example",
        artifactId="artifact",
        version="1.0",
        raw=True,
        placement="class-path",
    )
    # Raw (!) comes after placement (c) in the string
    assert str(coord) == "org.example:artifact:1.0(c)!"


def test_coord2str_placement_classpath():
    """Test coord2str with class-path placement."""
    result = coord2str(
        "org.example",
        "artifact",
        version="1.0",
        placement="class-path",
    )
    assert result == "org.example:artifact:1.0(c)"


def test_coord2str_placement_modulepath():
    """Test coord2str with module-path placement."""
    result = coord2str(
        "org.example",
        "artifact",
        version="1.0",
        placement="module-path",
    )
    assert result == "org.example:artifact:1.0(m)"


# =============================================================================
# Round-trip tests
# =============================================================================


def test_roundtrip_placement_classpath():
    """Test parse -> str round-trip with class-path placement."""
    original = "org.example:artifact:1.0(c)"
    coord = Coordinate.parse(original)
    assert str(coord) == original


def test_roundtrip_placement_modulepath():
    """Test parse -> str round-trip with module-path placement."""
    original = "org.example:artifact:1.0(m)"
    coord = Coordinate.parse(original)
    assert str(coord) == original


def test_roundtrip_placement_with_raw():
    """Test parse -> str round-trip with raw and placement."""
    original = "org.example:artifact:1.0(c)!"
    coord = Coordinate.parse(original)
    assert str(coord) == original

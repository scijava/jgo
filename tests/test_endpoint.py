#!/usr/bin/env python3
"""
Tests for Endpoint parsing and stringification.
"""

import warnings

from jgo.parse._endpoint import Endpoint

# =============================================================================
# Endpoint.parse() - Basic parsing tests
# =============================================================================


def test_parse_simple():
    """Test parsing simple endpoint."""
    result = Endpoint.parse("org.example:my-artifact:1.2.3")
    assert len(result.coordinates) == 1
    assert result.coordinates[0].groupId == "org.example"
    assert result.coordinates[0].artifactId == "my-artifact"
    assert result.coordinates[0].version == "1.2.3"
    assert result.main_class is None
    assert result.coordinates[0].raw is None  # No ! flag
    assert result.deprecated_format is False


def test_parse_multiple_coords():
    """Test parsing endpoint with multiple coordinates."""
    result = Endpoint.parse("org.example:foo:1.0+com.example:bar:2.0")
    assert len(result.coordinates) == 2
    assert result.coordinates[0].groupId == "org.example"
    assert result.coordinates[0].artifactId == "foo"
    assert result.coordinates[1].groupId == "com.example"
    assert result.coordinates[1].artifactId == "bar"
    assert result.main_class is None
    assert result.coordinates[0].raw is None  # No ! flag
    assert result.coordinates[1].raw is None  # No ! flag


def test_parse_with_classifier():
    """Test parsing endpoint with classifier."""
    result = Endpoint.parse("org.lwjgl:lwjgl:jar:natives-linux:3.3.1")
    assert len(result.coordinates) == 1
    assert result.coordinates[0].classifier == "natives-linux"
    assert result.coordinates[0].packaging == "jar"
    assert result.coordinates[0].version == "3.3.1"


# =============================================================================
# Endpoint.parse() - Main class specification (new @ format)
# =============================================================================


def test_parse_new_format_simple():
    """Test new @ separator format with simple artifact."""
    result = Endpoint.parse("org.example:artifact@Main")
    assert len(result.coordinates) == 1
    assert result.coordinates[0].groupId == "org.example"
    assert result.coordinates[0].artifactId == "artifact"
    assert result.main_class == "Main"
    assert result.coordinates[0].raw is None  # No ! flag


def test_parse_new_format_with_version():
    """Test new @ separator format with version."""
    result = Endpoint.parse("org.example:artifact:1.0.0@com.example.Main")
    assert len(result.coordinates) == 1
    assert result.coordinates[0].groupId == "org.example"
    assert result.coordinates[0].artifactId == "artifact"
    assert result.coordinates[0].version == "1.0.0"
    assert result.main_class == "com.example.Main"


def test_parse_new_format_multiple_artifacts():
    """Test new @ separator format with multiple artifacts."""
    result = Endpoint.parse("org.example:artifact1+org.example:artifact2@Main")
    assert len(result.coordinates) == 2
    assert result.coordinates[0].groupId == "org.example"
    assert result.coordinates[0].artifactId == "artifact1"
    assert result.coordinates[1].groupId == "org.example"
    assert result.coordinates[1].artifactId == "artifact2"
    assert result.main_class == "Main"


def test_parse_with_main_class():
    """Test parsing endpoint with main class (new @ format)."""
    result = Endpoint.parse("org.example:foo:1.0@org.example.Main")
    assert len(result.coordinates) == 1
    assert result.coordinates[0].groupId == "org.example"
    assert result.main_class == "org.example.Main"
    assert result.deprecated_format is False


def test_parse_multiple_with_main_class():
    """Test parsing multiple coordinates with main class."""
    result = Endpoint.parse("g:a:1.0+g2:a2:2.0@org.example.Main")
    assert len(result.coordinates) == 2
    assert result.main_class == "org.example.Main"
    assert result.coordinates[0].raw is None  # No ! flag
    assert result.coordinates[1].raw is None  # No ! flag


def test_parse_no_main_class():
    """Test parsing without main class."""
    result = Endpoint.parse("org.example:artifact:1.0.0")
    assert len(result.coordinates) == 1
    assert result.main_class is None


def test_parse_only_first_main_class_used():
    """Test that middle @ syntax is deprecated but still works."""
    # Middle @ syntax is deprecated - should trigger warning and normalize to end
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = Endpoint.parse("org.example:artifact1@Main+org.example:artifact2")

        # Should warn about deprecated syntax
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "Deprecated main class syntax" in str(w[0].message)

    assert len(result.coordinates) == 2
    assert result.main_class == "Main"
    assert result.deprecated_format is True


# =============================================================================
# Endpoint.parse() - Raw/unmanaged dependency flags (!)
# =============================================================================


def test_parse_with_raw_flag():
    """Test parsing endpoint with raw/unmanaged flag (!)."""
    result = Endpoint.parse("org.example:foo:1.0!")
    assert len(result.coordinates) == 1
    assert result.coordinates[0].groupId == "org.example"
    assert result.coordinates[0].raw is True  # ! means raw/unmanaged


def test_parse_mixed_raw():
    """Test parsing endpoint with mixed raw flags."""
    result = Endpoint.parse("g:a:1.0!+g2:a2:2.0")
    assert len(result.coordinates) == 2
    assert result.coordinates[0].raw is True  # Has !
    assert result.coordinates[1].raw is None  # No !


def test_parse_escaped_raw():
    """Test parsing endpoint with escaped raw flag (\\!)."""
    result = Endpoint.parse("org.example:foo:1.0\\!")
    assert len(result.coordinates) == 1
    assert result.coordinates[0].raw is True  # \\! means raw/unmanaged


def test_parse_new_format_with_raw():
    """Test new @ separator format with raw dependency."""
    result = Endpoint.parse("org.example:artifact!@Main")
    assert len(result.coordinates) == 1
    assert result.coordinates[0].raw is True  # Has !
    assert result.main_class == "Main"


# =============================================================================
# Endpoint.parse() - Complex combinations
# =============================================================================


def test_parse_complex():
    """Test parsing complex endpoint with multiple features."""
    result = Endpoint.parse("g:a:1.0!+g2:a2:2.0@org.example.Main")
    assert len(result.coordinates) == 2
    assert result.coordinates[0].groupId == "g"
    assert result.coordinates[1].groupId == "g2"
    assert result.main_class == "org.example.Main"
    assert result.coordinates[0].raw is True  # Has !
    assert result.coordinates[1].raw is None  # No !


# =============================================================================
# Endpoint.parse() - Deprecated formats
# =============================================================================


def test_parse_deprecated_colon_at():
    """Test old :@MainClass format triggers deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = Endpoint.parse("org.example:artifact:@Main")

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        # New normalization warning message
        assert "Deprecated main class syntax" in str(w[0].message)
        assert "org.example:artifact@Main" in str(w[0].message)

    assert result.main_class == "Main"  # Normalized format strips the : before @
    assert result.deprecated_format is True


def test_parse_deprecated_colon_at_with_version():
    """Test parsing endpoint with deprecated :@ format."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = Endpoint.parse("org.example:foo:1.0:@Main")
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "Deprecated main class syntax" in str(w[0].message)

    assert result.main_class == "Main"  # Normalized format strips the : before @
    assert result.deprecated_format is True


def test_parse_deprecated_colon_mainclass():
    """Test old :mainClass format triggers deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = Endpoint.parse("org.example:artifact:com.example.Main")

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert ":mainClass" in str(w[0].message)

    assert result.main_class == "com.example.Main"
    assert result.deprecated_format is True


def test_parse_deprecated_colon_mainclass_with_version():
    """Test parsing endpoint with deprecated :MainClass format."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = Endpoint.parse("org.example:foo:1.0:org.example.Main")
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)

    assert result.main_class == "org.example.Main"
    assert result.deprecated_format is True


def test_parse_multiple_at_symbols_error():
    """Test that multiple @ declarations raise an error."""
    import pytest

    with pytest.raises(ValueError) as excinfo:
        Endpoint.parse("org.foo:foo@Main1+org.bar:bar@Main2")

    assert "Multiple main class declarations" in str(excinfo.value)


# =============================================================================
# Endpoint stringification tests
# =============================================================================


def test_str_simple():
    """Test str() on simple endpoint."""
    endpoint = Endpoint.parse("org.example:my-artifact:1.2.3")
    # Should produce the same string (round-trip)
    assert str(endpoint) == "org.example:my-artifact:1.2.3"


def test_str_with_main_class():
    """Test str() on endpoint with main class."""
    endpoint = Endpoint.parse("org.example:foo:1.0@org.example.Main")
    assert str(endpoint) == "org.example:foo:1.0@org.example.Main"


def test_str_with_raw():
    """Test str() on endpoint with raw flag (!)."""
    endpoint = Endpoint.parse("org.example:foo:1.0!")
    assert str(endpoint) == "org.example:foo:1.0!"


def test_str_multiple_coords():
    """Test str() on endpoint with multiple coordinates."""
    endpoint = Endpoint.parse("g:a:1.0+g2:a2:2.0")
    assert str(endpoint) == "g:a:1.0+g2:a2:2.0"


def test_str_complex():
    """Test str() on complex endpoint."""
    endpoint = Endpoint.parse("g:a:1.0!+g2:a2:2.0@org.example.Main")
    assert str(endpoint) == "g:a:1.0!+g2:a2:2.0@org.example.Main"


# =============================================================================
# Round-trip tests
# =============================================================================


def test_roundtrip_simple():
    """Test that parsing and stringifying a simple endpoint is idempotent."""
    original = "org.example:my-artifact:1.2.3"
    endpoint = Endpoint.parse(original)
    assert str(endpoint) == original


def test_roundtrip_with_main_class():
    """Test that parsing and stringifying with main class is idempotent."""
    original = "org.example:foo:1.0@org.example.Main"
    endpoint = Endpoint.parse(original)
    assert str(endpoint) == original


def test_roundtrip_with_raw():
    """Test that parsing and stringifying with raw flag is idempotent."""
    original = "org.example:foo:1.0!"
    endpoint = Endpoint.parse(original)
    assert str(endpoint) == original


def test_roundtrip_complex():
    """Test that parsing and stringifying complex endpoint is idempotent."""
    original = "g:a:1.0!+g2:a2:2.0@org.example.Main"
    endpoint = Endpoint.parse(original)
    assert str(endpoint) == original

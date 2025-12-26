"""Tests for Maven version parsing and comparison."""

import pytest

from jgo.maven.version import (
    JavaVersion,
    parse_java_version,
    parse_version_range,
    version_matches_range,
)


class TestJavaVersion:
    """Test JavaVersion NamedTuple."""

    def test_creation(self):
        v = JavaVersion(11, 0, 1)
        assert v.major == 11
        assert v.minor == 0
        assert v.patch == 1

    def test_string_representation(self):
        assert str(JavaVersion(8, 0, 0)) == "8.0.0"
        assert str(JavaVersion(11, 0, 1)) == "11.0.1"
        assert str(JavaVersion(17, 0, 292)) == "17.0.292"

    def test_comparison(self):
        assert JavaVersion(8, 0, 0) < JavaVersion(11, 0, 0)
        assert JavaVersion(11, 0, 0) < JavaVersion(11, 0, 1)
        assert JavaVersion(11, 0, 1) == JavaVersion(11, 0, 1)
        assert JavaVersion(17, 0, 0) > JavaVersion(11, 0, 1)


class TestParseJavaVersion:
    """Test parse_java_version function."""

    def test_old_format_simple(self):
        assert parse_java_version("1.8") == JavaVersion(8, 0, 0)
        assert parse_java_version("1.7") == JavaVersion(7, 0, 0)
        assert parse_java_version("1.6") == JavaVersion(6, 0, 0)

    def test_old_format_with_minor(self):
        assert parse_java_version("1.8.0") == JavaVersion(8, 0, 0)
        assert parse_java_version("1.7.0") == JavaVersion(7, 0, 0)

    def test_old_format_with_patch(self):
        assert parse_java_version("1.8.0_292") == JavaVersion(8, 0, 292)
        assert parse_java_version("1.8.0_191") == JavaVersion(8, 0, 191)
        assert parse_java_version("1.7.0_80") == JavaVersion(7, 0, 80)

    def test_new_format_simple(self):
        assert parse_java_version("8") == JavaVersion(8, 0, 0)
        assert parse_java_version("11") == JavaVersion(11, 0, 0)
        assert parse_java_version("17") == JavaVersion(17, 0, 0)
        assert parse_java_version("21") == JavaVersion(21, 0, 0)

    def test_new_format_with_minor(self):
        assert parse_java_version("11.0") == JavaVersion(11, 0, 0)
        assert parse_java_version("17.0") == JavaVersion(17, 0, 0)

    def test_new_format_with_patch(self):
        assert parse_java_version("11.0.1") == JavaVersion(11, 0, 1)
        assert parse_java_version("17.0.2") == JavaVersion(17, 0, 2)
        assert parse_java_version("21.0.1") == JavaVersion(21, 0, 1)

    def test_whitespace_handling(self):
        assert parse_java_version("  11  ") == JavaVersion(11, 0, 0)
        assert parse_java_version("\t1.8\n") == JavaVersion(8, 0, 0)

    def test_empty_string(self):
        with pytest.raises(ValueError, match="Empty version string"):
            parse_java_version("")

    def test_whitespace_only(self):
        with pytest.raises(ValueError, match="Empty version string"):
            parse_java_version("   ")

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            parse_java_version("abc")

    def test_invalid_old_format(self):
        with pytest.raises(ValueError):
            parse_java_version("1.")

    def test_invalid_numbers(self):
        with pytest.raises(ValueError):
            parse_java_version("1.x.0")


class TestParseVersionRange:
    """Test parse_version_range function."""

    def test_simple_version(self):
        # Simple version without patch is prefix match
        lower, upper, l_inc, u_inc = parse_version_range("8")
        assert lower == JavaVersion(8, 0, 0)
        assert upper == JavaVersion(9, 0, 0)
        assert l_inc is True
        assert u_inc is False

    def test_simple_version_old_format(self):
        # Simple version without patch is prefix match
        lower, upper, l_inc, u_inc = parse_version_range("1.8")
        assert lower == JavaVersion(8, 0, 0)
        assert upper == JavaVersion(9, 0, 0)
        assert l_inc is True
        assert u_inc is False

    def test_inclusive_range(self):
        lower, upper, l_inc, u_inc = parse_version_range("[1.8,11]")
        assert lower == JavaVersion(8, 0, 0)
        assert upper == JavaVersion(11, 0, 0)
        assert l_inc is True
        assert u_inc is True

    def test_exclusive_range(self):
        lower, upper, l_inc, u_inc = parse_version_range("(1.8,11)")
        assert lower == JavaVersion(8, 0, 0)
        assert upper == JavaVersion(11, 0, 0)
        assert l_inc is False
        assert u_inc is False

    def test_mixed_range_lower_inclusive(self):
        lower, upper, l_inc, u_inc = parse_version_range("[1.8,11)")
        assert lower == JavaVersion(8, 0, 0)
        assert upper == JavaVersion(11, 0, 0)
        assert l_inc is True
        assert u_inc is False

    def test_mixed_range_upper_inclusive(self):
        lower, upper, l_inc, u_inc = parse_version_range("(1.8,11]")
        assert lower == JavaVersion(8, 0, 0)
        assert upper == JavaVersion(11, 0, 0)
        assert l_inc is False
        assert u_inc is True

    def test_unbounded_lower(self):
        lower, upper, l_inc, u_inc = parse_version_range("(,11]")
        assert lower is None
        assert upper == JavaVersion(11, 0, 0)
        assert l_inc is False
        assert u_inc is True

    def test_unbounded_upper(self):
        lower, upper, l_inc, u_inc = parse_version_range("[11,)")
        assert lower == JavaVersion(11, 0, 0)
        assert upper is None
        assert l_inc is True
        assert u_inc is False

    def test_unbounded_both(self):
        lower, upper, l_inc, u_inc = parse_version_range("(,)")
        assert lower is None
        assert upper is None
        assert l_inc is False
        assert u_inc is False

    def test_semantic_versions_in_range(self):
        lower, upper, l_inc, u_inc = parse_version_range("[1.8.0_191,1.8.0_292]")
        assert lower == JavaVersion(8, 0, 191)
        assert upper == JavaVersion(8, 0, 292)
        assert l_inc is True
        assert u_inc is True

    def test_whitespace_handling(self):
        lower, upper, l_inc, u_inc = parse_version_range(" [ 11 , 17 ] ")
        assert lower == JavaVersion(11, 0, 0)
        assert upper == JavaVersion(17, 0, 0)

    def test_empty_string(self):
        with pytest.raises(ValueError, match="Empty range specification"):
            parse_version_range("")

    def test_invalid_lower_greater_than_upper(self):
        with pytest.raises(ValueError, match="Lower bound.*> upper bound"):
            parse_version_range("[17,11]")

    def test_missing_comma(self):
        with pytest.raises(ValueError, match="must contain comma"):
            parse_version_range("[11]")

    def test_invalid_opening_bracket(self):
        # Note: ! prefix for negation is handled at profile activation level,
        # not in range parsing. This should fail as invalid version string.
        with pytest.raises(ValueError):
            parse_version_range("!11,17]")

    def test_invalid_closing_bracket(self):
        with pytest.raises(ValueError, match="Invalid closing bracket"):
            parse_version_range("[11,17!")

    def test_too_short(self):
        with pytest.raises(ValueError, match="Invalid range syntax"):
            parse_version_range("[,")


class TestVersionMatchesRange:
    """Test version_matches_range function."""

    def test_inclusive_bounds_inside(self):
        assert version_matches_range(
            JavaVersion(9, 0, 0),
            JavaVersion(8, 0, 0),
            JavaVersion(11, 0, 0),
            True,
            True,
        )

    def test_inclusive_bounds_at_lower(self):
        assert version_matches_range(
            JavaVersion(8, 0, 0),
            JavaVersion(8, 0, 0),
            JavaVersion(11, 0, 0),
            True,
            True,
        )

    def test_inclusive_bounds_at_upper(self):
        assert version_matches_range(
            JavaVersion(11, 0, 0),
            JavaVersion(8, 0, 0),
            JavaVersion(11, 0, 0),
            True,
            True,
        )

    def test_inclusive_bounds_below(self):
        assert not version_matches_range(
            JavaVersion(7, 0, 0),
            JavaVersion(8, 0, 0),
            JavaVersion(11, 0, 0),
            True,
            True,
        )

    def test_inclusive_bounds_above(self):
        assert not version_matches_range(
            JavaVersion(12, 0, 0),
            JavaVersion(8, 0, 0),
            JavaVersion(11, 0, 0),
            True,
            True,
        )

    def test_exclusive_bounds_inside(self):
        assert version_matches_range(
            JavaVersion(9, 0, 0),
            JavaVersion(8, 0, 0),
            JavaVersion(11, 0, 0),
            False,
            False,
        )

    def test_exclusive_bounds_at_lower(self):
        assert not version_matches_range(
            JavaVersion(8, 0, 0),
            JavaVersion(8, 0, 0),
            JavaVersion(11, 0, 0),
            False,
            False,
        )

    def test_exclusive_bounds_at_upper(self):
        assert not version_matches_range(
            JavaVersion(11, 0, 0),
            JavaVersion(8, 0, 0),
            JavaVersion(11, 0, 0),
            False,
            False,
        )

    def test_mixed_bounds_lower_inclusive(self):
        assert version_matches_range(
            JavaVersion(8, 0, 0),
            JavaVersion(8, 0, 0),
            JavaVersion(11, 0, 0),
            True,
            False,
        )
        assert not version_matches_range(
            JavaVersion(11, 0, 0),
            JavaVersion(8, 0, 0),
            JavaVersion(11, 0, 0),
            True,
            False,
        )

    def test_mixed_bounds_upper_inclusive(self):
        assert not version_matches_range(
            JavaVersion(8, 0, 0),
            JavaVersion(8, 0, 0),
            JavaVersion(11, 0, 0),
            False,
            True,
        )
        assert version_matches_range(
            JavaVersion(11, 0, 0),
            JavaVersion(8, 0, 0),
            JavaVersion(11, 0, 0),
            False,
            True,
        )

    def test_unbounded_lower(self):
        assert version_matches_range(
            JavaVersion(5, 0, 0), None, JavaVersion(11, 0, 0), False, True
        )
        assert version_matches_range(
            JavaVersion(11, 0, 0), None, JavaVersion(11, 0, 0), False, True
        )
        assert not version_matches_range(
            JavaVersion(12, 0, 0), None, JavaVersion(11, 0, 0), False, True
        )

    def test_unbounded_upper(self):
        assert version_matches_range(
            JavaVersion(11, 0, 0), JavaVersion(11, 0, 0), None, True, False
        )
        assert version_matches_range(
            JavaVersion(21, 0, 0), JavaVersion(11, 0, 0), None, True, False
        )
        assert not version_matches_range(
            JavaVersion(10, 0, 0), JavaVersion(11, 0, 0), None, True, False
        )

    def test_unbounded_both(self):
        assert version_matches_range(JavaVersion(1, 0, 0), None, None, False, False)
        assert version_matches_range(JavaVersion(99, 0, 0), None, None, False, False)

    def test_semantic_version_patch_differences(self):
        # 1.8.0_292 should be greater than 1.8.0_191
        assert version_matches_range(
            JavaVersion(8, 0, 250),
            JavaVersion(8, 0, 191),
            JavaVersion(8, 0, 292),
            True,
            True,
        )
        assert not version_matches_range(
            JavaVersion(8, 0, 100),
            JavaVersion(8, 0, 191),
            JavaVersion(8, 0, 292),
            True,
            True,
        )
        assert not version_matches_range(
            JavaVersion(8, 0, 300),
            JavaVersion(8, 0, 191),
            JavaVersion(8, 0, 292),
            True,
            True,
        )

    def test_exact_match_with_patch(self):
        # Version specs with patch are exact matches
        # e.g., "1.8.0_292" matches only JavaVersion(8, 0, 292)
        assert version_matches_range(
            JavaVersion(8, 0, 292),
            JavaVersion(8, 0, 292),
            JavaVersion(8, 0, 292),
            True,
            True,
        )
        assert not version_matches_range(
            JavaVersion(8, 0, 291),
            JavaVersion(8, 0, 292),
            JavaVersion(8, 0, 292),
            True,
            True,
        )

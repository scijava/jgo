# Plan: Maven Version Comparison Logic Refactoring

## Executive Summary

The current `src/jgo/maven/version.py` implements a simplified Java-centric version model that conflates general Maven version comparison with JDK profile activation semantics. This plan outlines a refactoring to:

1. Implement Maven's official version ordering specification
2. Separate concerns between general Maven versions and Java-specific semantics
3. Consolidate duplicate version logic across the codebase
4. Use Maven specification terminology for better code clarity

---

## Design Decisions (Approved)

1. **Location**: All version logic stays in `src/jgo/maven/version.py`
2. **SemVer Library**: Use `semver` package from PyPI (no dependencies) for SemVer parsing
3. **SemVer 1.x vs 2.x**: The `semver` library implements 2.x; we must check parsed versions comply with Maven's 1.x subset before using SemVer comparison
4. **Four Components**:
   - SemVer parsing/comparison (via `semver` library)
   - Non-SemVer Maven version parsing/comparison (per Maven spec)
   - Maven version range parsing (using above for bounds checking)
   - Java-specific handling (old-style `1.x` prefix special casing)

---

## Current State Analysis

### Existing Files

| File | Purpose | Issues |
|------|---------|--------|
| `src/jgo/maven/version.py` | Version parsing for profile activation | Uses simplified 3-tuple model; conflates Maven version semantics with Java version semantics |
| `src/jgo/exec/java_source.py` | Java executable location | Contains duplicate Java version parsing logic (lines 181-225) |
| `tests/test_maven_version.py` | Unit tests | Tests are Java-version-centric, not general Maven versions |

### Key Deficiencies

1. **Simplified Version Model**: `JavaVersion(major, minor, patch)` cannot represent Maven versions like:
   - `1.0.0-alpha-1`
   - `2.0-SNAPSHOT`
   - `3.1.0-M2`
   - `4.0.0.Final`

2. **Missing Maven Specification Features**:
   - Token splitting on transitions (e.g., `foo1bar` → `foo-1-bar`)
   - Trailing null value trimming (`1.0.0` → `1`)
   - Qualifier ordering (`alpha < beta < milestone < rc < snapshot < "" < sp`)
   - Case-insensitive comparison
   - Padding rules for different separators (`.` vs `-`)

3. **Conflated Semantics**: The "prefix match" logic (e.g., `"11"` matches `[11.0.0, 12.0.0)`) is specific to JDK profile activation, not general Maven version ranges.

4. **Duplicate Code**: `java_source.py:_get_java_version()` duplicates Java version parsing logic.

---

## Maven Version Order Specification (Reference)

From https://maven.apache.org/pom.html#version-order-specification:

### Two Comparison Modes

1. **SemVer Mode**: If both versions match Semantic Versioning 1.0.0 grammar with lowercase letters only, use SemVer precedence rules
2. **Maven Mode**: Otherwise, use Maven's complex token-based algorithm

### Maven Algorithm Steps

1. **Token Splitting**: Split on `.`, `-`, `_`, and digit-to-character transitions
2. **Token Replacement**: Empty tokens become `0`
3. **Trimming**: Remove trailing null values (`0`, `""`, `final`, `ga`)
4. **Padding**: Pad shorter sequence to match longer
5. **Comparison**: Compare token-by-token

### Qualifier Ordering

```
alpha < beta < milestone < rc = cr < snapshot < "" = final = ga = release < sp
```

- `a` = `alpha`, `b` = `beta`, `m` = `milestone` (when followed by number)
- Case-insensitive comparison

### Separator Influence

```
.qualifier = -qualifier < -number < .number
```

---

## Proposed Architecture

### File Structure

```
src/jgo/
├── maven/
│   └── version.py          # REFACTOR: All version logic consolidated here
└── exec/
    └── java_source.py      # REFACTOR: Use shared utilities from maven.version
```

### Module Structure: `src/jgo/maven/version.py`

```python
"""
Maven version parsing, comparison, and range utilities.

This module provides four levels of version handling:

1. SemVer Comparison (via semver library)
   - is_semver_1x() - Check if version string is valid SemVer 1.x
   - compare_semver() - Compare two SemVer strings

2. Maven Version Comparison (non-SemVer)
   - MavenVersion class - Parsed version with comparison operators
   - tokenize() - Split version into tokens per Maven spec
   - trim_nulls() - Remove trailing null values
   - compare_versions() - Compare two version strings

3. Maven Version Ranges
   - VersionRange class - Parsed range with bounds
   - parse_version_range() - Parse "[1.0,2.0)" style ranges
   - version_in_range() - Check if version satisfies range

4. Java Version Handling
   - JavaVersion - NamedTuple for JVM versions
   - parse_java_version() - Handle old-style "1.8" format
   - parse_jdk_activation_range() - JDK profile activation ranges
   - version_matches_jdk_range() - Check JDK activation
"""

import semver
from typing import NamedTuple
from functools import total_ordering

# ============================================================
# SECTION 1: SEMVER COMPARISON
# ============================================================

def is_semver_1x(version: str) -> bool:
    """
    Check if version string is valid Semantic Versioning 1.x.

    SemVer 1.x differences from 2.x:
    - No build metadata (+ suffix)
    - Prerelease identifiers are dot-separated alphanumerics

    Maven uses SemVer 1.x rules when both versions match this grammar.
    """

def compare_semver(v1: str, v2: str) -> int:
    """Compare two SemVer strings. Returns -1, 0, or 1."""

# ============================================================
# SECTION 2: MAVEN VERSION COMPARISON (NON-SEMVER)
# ============================================================

@total_ordering
class MavenVersion:
    """
    A Maven version parsed into tokens for comparison.

    Implements the full Maven version ordering specification from:
    https://maven.apache.org/pom.html#version-order-specification
    """

    def __init__(self, version_string: str): ...
    def __lt__(self, other): ...
    def __eq__(self, other): ...
    def __str__(self): ...

class Token(NamedTuple):
    """A single version token."""
    value: int | str  # numeric or string
    separator: str    # '.', '-', '_', or '' for transitions

# Qualifier ordering per Maven spec
QUALIFIER_ORDER = {
    "alpha": -5, "a": -5,
    "beta": -4, "b": -4,
    "milestone": -3, "m": -3,
    "rc": -2, "cr": -2,
    "snapshot": -1,
    "": 0, "final": 0, "ga": 0, "release": 0,
    "sp": 1,
}

def tokenize(version: str) -> list[Token]:
    """Split version string into tokens per Maven spec."""

def trim_nulls(tokens: list[Token]) -> list[Token]:
    """Remove trailing null values (0, '', final, ga)."""

def compare_tokens(a: Token, b: Token, sep_a: str, sep_b: str) -> int:
    """Compare two tokens with separator context."""

def compare_versions(v1: str, v2: str) -> int:
    """
    Compare two Maven version strings.

    Uses SemVer comparison if both versions are valid SemVer 1.x,
    otherwise falls back to Maven's complex algorithm.

    Returns:
        -1 if v1 < v2
         0 if v1 == v2
         1 if v1 > v2
    """

# ============================================================
# SECTION 3: MAVEN VERSION RANGES
# ============================================================

class VersionRange(NamedTuple):
    """A Maven version range specification."""
    lower: str | None       # Lower bound version or None
    upper: str | None       # Upper bound version or None
    lower_inclusive: bool   # True for '[', False for '('
    upper_inclusive: bool   # True for ']', False for ')'

def parse_version_range(range_spec: str) -> VersionRange:
    """
    Parse Maven version range specification.

    Supports:
        - Inclusive range: "[1.0,2.0]"
        - Exclusive range: "(1.0,2.0)"
        - Mixed: "[1.0,2.0)"
        - Unbounded lower: "(,2.0]"
        - Unbounded upper: "[1.0,)"
        - Exact version: "[1.0]" (equivalent to "[1.0,1.0]")
        - Soft requirement: "1.0" (any version, prefer 1.0)

    Returns:
        VersionRange with parsed bounds and inclusivity
    """

def version_in_range(version: str, range_spec: str | VersionRange) -> bool:
    """Check if version satisfies the given range."""

# ============================================================
# SECTION 4: JAVA VERSION HANDLING
#
# Special handling for Java/JVM version strings and JDK profile
# activation ranges. These differ from general Maven versions:
# - Old-style "1.8" format maps to Java 8
# - JDK activation uses PREFIX matching for simple versions
# ============================================================

class JavaVersion(NamedTuple):
    """
    Semantic representation for Java runtime versions.

    This is specifically for JVM version detection, NOT for
    Maven artifact versions.
    """
    major: int
    minor: int = 0
    patch: int = 0

def parse_java_version(version: str) -> JavaVersion:
    """
    Parse Java runtime version string.

    Handles JVM-specific formats:
    - Old: "1.8.0_292" → JavaVersion(8, 0, 292)
    - New: "17.0.2" → JavaVersion(17, 0, 2)
    """

def parse_jdk_activation_range(range_spec: str) -> tuple[
    JavaVersion | None,  # lower bound
    JavaVersion | None,  # upper bound
    bool,                # lower inclusive
    bool,                # upper inclusive
]:
    """
    Parse JDK profile activation range specification.

    This implements Maven's JDK profile activation semantics, which
    differ from general version ranges:

    - Simple versions use PREFIX MATCHING: "11" matches 11.x.x
    - Range syntax follows Maven conventions: "[1.8,11)"

    NOTE: This is NOT the same as dependency version ranges.
    """

def version_matches_jdk_range(
    version: JavaVersion,
    lower: JavaVersion | None,
    upper: JavaVersion | None,
    lower_inclusive: bool,
    upper_inclusive: bool,
) -> bool:
    """Check if Java version matches JDK activation range."""
```

---

## Implementation Tasks

### Phase 1: Add `semver` dependency

- [ ] **1.1** Add `semver` to project dependencies in `pyproject.toml`
- [ ] **1.2** Run `uv sync` to update lock file

### Phase 2: Implement SemVer utilities

- [ ] **2.1** Implement `is_semver_1x()` to detect SemVer 1.x compliance:
  - Must not have build metadata (`+` suffix)
  - Must parse successfully with `semver` library
  - All letters must be lowercase (Maven requirement)
- [ ] **2.2** Implement `compare_semver()` wrapper around `semver.compare()`

### Phase 3: Implement Maven version comparison

- [ ] **3.1** Implement `Token` NamedTuple with value and separator
- [ ] **3.2** Implement `tokenize()` following Maven spec:
  - Split on `.`, `-`, `_` delimiters
  - Split on digit↔character transitions (record as `-` separator)
  - Replace empty tokens with `0`
- [ ] **3.3** Implement `trim_nulls()` to remove trailing null values
- [ ] **3.4** Implement `QUALIFIER_ORDER` constant
- [ ] **3.5** Implement `compare_tokens()` with separator-aware logic
- [ ] **3.6** Implement `MavenVersion` class with `@total_ordering`
- [ ] **3.7** Implement `compare_versions()` with SemVer fast-path

### Phase 4: Implement version ranges

- [ ] **4.1** Implement `VersionRange` NamedTuple
- [ ] **4.2** Implement `parse_version_range()` for Maven range syntax
- [ ] **4.3** Implement `version_in_range()` using `compare_versions()`

### Phase 5: Refactor Java version handling

- [ ] **5.1** Keep existing `JavaVersion` and `parse_java_version()`
- [ ] **5.2** Rename `parse_version_range` → `parse_jdk_activation_range`
- [ ] **5.3** Rename `version_matches_range` → `version_matches_jdk_range`
- [ ] **5.4** Add clear section comments and docstrings

### Phase 6: Refactor `java_source.py`

- [ ] **6.1** Import `parse_java_version` from `jgo.maven.version`
- [ ] **6.2** Replace duplicate parsing logic in `_get_java_version()`
- [ ] **6.3** Extract version string extraction to helper if needed

### Phase 7: Update tests

- [ ] **7.1** Create `tests/test_maven_version.py` with comprehensive tests:
  - SemVer detection and comparison
  - Maven tokenization
  - Null trimming
  - Qualifier ordering
  - Complete ordering examples from spec
  - Version range parsing
  - Version-in-range checks
- [ ] **7.2** Keep Java/JDK-specific tests (can rename file if desired)
- [ ] **7.3** Update imports in `model.py` to use new function names

### Phase 8: Verify and clean up

- [ ] **8.1** Run full test suite
- [ ] **8.2** Update `model.py` imports if needed
- [ ] **8.3** Run linter

---

## Test Cases from Maven Specification

These test cases must pass after implementation:

```python
# SemVer detection
assert is_semver_1x("1.0.0") == True
assert is_semver_1x("1.0.0-alpha") == True
assert is_semver_1x("1.0.0-alpha.1") == True
assert is_semver_1x("1.0.0+build") == False  # build metadata = SemVer 2.x
assert is_semver_1x("1.0.0-ALPHA") == False  # uppercase = not Maven SemVer

# Numeric padding
assert compare_versions("1", "1.1") < 0

# Qualifier padding
assert compare_versions("1-snapshot", "1") < 0
assert compare_versions("1", "1-sp") < 0

# Automatic numeric ordering within strings
assert compare_versions("1-foo2", "1-foo10") < 0

# Separator equivalence
assert compare_versions("1.foo", "1-foo") == 0
assert compare_versions("1-foo", "1-1") < 0
assert compare_versions("1-1", "1.1") < 0

# Null value trimming equivalence
assert compare_versions("1.ga", "1-ga") == 0
assert compare_versions("1-ga", "1-0") == 0
assert compare_versions("1-0", "1_0") == 0
assert compare_versions("1_0", "1.0") == 0
assert compare_versions("1.0", "1") == 0

# Service pack ordering
assert compare_versions("1-sp", "1-ga") > 0
assert compare_versions("1-sp.1", "1-ga.1") > 0
assert compare_versions("1-sp-1", "1-ga-1") < 0  # Note: different due to separator!

# Alpha shorthand
assert compare_versions("1-a1", "1-alpha-1") == 0

# Case insensitivity
assert compare_versions("1.0-alpha1", "1.0-ALPHA1") == 0

# Alphabetic ordering
assert compare_versions("1.7", "1.K") > 0  # numeric > alphabetic
assert compare_versions("5.zebra", "5.aardvark") > 0  # alphabetic order

# Version ranges
assert version_in_range("1.5", "[1.0,2.0]") == True
assert version_in_range("2.0", "[1.0,2.0)") == False
assert version_in_range("0.5", "[1.0,)") == False
assert version_in_range("3.0", "[1.0,)") == True
```

---

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| Breaking existing JDK activation | Keep JavaVersion semantics; rename but preserve behavior |
| SemVer 2.x vs 1.x mismatch | Explicit `is_semver_1x()` check before using SemVer path |
| API compatibility | Rename functions clearly; update all call sites |
| Edge cases in version parsing | Use Maven spec test cases extensively |

---

## Estimated Complexity

- **Phase 1-2**: Dependencies + SemVer (~30 lines)
- **Phase 3**: Maven comparison (~150 lines)
- **Phase 4**: Version ranges (~50 lines)
- **Phase 5**: Java refactor (~30 lines changed)
- **Phase 6**: java_source.py (~20 lines changed)
- **Phase 7**: Tests (~200 lines)
- **Phase 8**: Cleanup (~10 lines)

**Total**: ~350-400 lines of new code, ~60 lines refactored

---

## Approval

✅ Architecture approach approved
✅ File location approved (`src/jgo/maven/version.py`)
✅ API structure approved (4 sections)
✅ `semver` library dependency approved

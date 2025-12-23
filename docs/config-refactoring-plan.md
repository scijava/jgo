# Config Subsystem Refactoring Plan

## Overview

Refactor jgo config subsystem to:
1. Replace hardcoded `~/.jgorc` references with proper terminology (see Terminology section)
2. Eliminate duplication between JgoConfig/GlobalSettings (OO, read-focused) and ConfigParser helpers (procedural, read-write)
3. Maintain backward compatibility with `--ignore-jgorc` flag and legacy paths

## Terminology

This refactoring establishes clear terminology to distinguish different configuration concepts:

- **Config subsystem**: Umbrella term for the entire `src/jgo/config/` module
- **Global settings**: User preferences stored in INI format (`~/.config/jgo/config` or `~/.jgorc`)
  - Use "settings" consistently when referring to global configuration
  - File: `src/jgo/config/settings.py`
  - Class: `GlobalSettings`
- **Project config**: Project-specific configuration in TOML format (`jgo.toml` in project directory)
  - Always use both words together: "project config"
  - Future feature, not yet implemented
- **"Config" alone**: Only use for general/umbrella contexts (e.g., "config subsystem", "config manager")

**Rationale:**
- Semantic accuracy: "settings" = global user preferences, "config" = project-specific
- Greppability: Search for one without getting false matches from the other
- Industry precedent: Matches patterns used by VSCode, Git, and other tools

## Architectural Approach

**Hybrid Strategy**: Extend GlobalSettings with write capabilities while centralizing settings path logic in a new manager module.

### Why This Approach?
- GlobalSettings (formerly JgoConfig) is already the authoritative read interface (used in 15+ files)
- Minimal disruption - extends existing patterns rather than replacing them
- Clean separation between global settings (.jgorc) and project config (jgo.toml)
- Future-proof for potential config format migration

## Implementation Phases

### Phase 1: Create Config Manager Module

**New File**: `src/jgo/config/manager.py`

Centralizes settings file path resolution and terminology:
```python
# Constants
SETTINGS_FILE_DISPLAY_NAME = "jgo settings file"
LEGACY_SETTINGS_NAME = "~/.jgorc"

# Functions
def get_settings_path(prefer_legacy: bool = False) -> Path
def get_settings_display_name(path: Path) -> str
def format_settings_message(path: Path, action: str) -> str
```

**Benefits**: Single source of truth for terminology, easy to update all references.

### Phase 2: Extend GlobalSettings with Write Operations

**File**: `src/jgo/config/settings.py` (renamed from `file.py`)

Add write methods to GlobalSettings class (renamed from JgoConfig):
```python
class GlobalSettings:
    # New methods
    def save(self, settings_file: Path | None = None) -> None
    def set_setting(self, key: str, value: str) -> None
    def set_repository(self, name: str, url: str) -> None
    def set_shortcut(self, name: str, replacement: str) -> None
    def unset_setting(self, key: str) -> None
    def unset_repository(self, name: str) -> None
    def unset_shortcut(self, name: str) -> None
```

**Implementation**: Use ConfigParser internally for writing (maintains INI format), handle both XDG and legacy paths, support old names (cacheDir) and new names (cache_dir).

**File Rename**: `src/jgo/config/file.py` → `src/jgo/config/settings.py`
**Class Rename**: `JgoConfig` → `GlobalSettings`

### Phase 3: Refactor CLI Config Commands

**Files**:
- `src/jgo/cli/commands/config.py`
- `src/jgo/cli/helpers.py`

**Changes in config.py**:
- Replace `_list_jgorc()` - use `GlobalSettings.load()` instead of `load_config_parser()`
- Replace `_get_jgorc()` - use GlobalSettings methods
- Replace `_set_jgorc()` - use `settings.set_setting/repository/shortcut()` + `save()`
- Replace `_unset_jgorc()` - use `settings.unset_*()` + `save()`

**Changes in helpers.py**:
- Remove `load_config_parser()` - no longer needed after config.py refactor
- Remove `validate_config_section()` and `validate_config_key()` - move into GlobalSettings if needed

### Phase 4: Update Terminology in Documentation

**Files** (8 documentation files):
- README.md
- docs/user-guide.md
- docs/MIGRATION.md
- docs/MIGRATION_EXAMPLE.md
- docs/FLAG-MIGRATION.md
- docs/architecture.md
- docs/CLI-REDESIGN.md
- CHANGELOG.md

**Pattern**:
```
Before: "settings from ~/.jgorc"
After:  "settings from jgo settings file (~/.config/jgo/config or ~/.jgorc)"

Before: "Create ~/.jgorc with [settings]..."
After:  "Create jgo settings file with [settings]..."
        Note: "Settings file location: ~/.config/jgo/config (or ~/.jgorc for legacy)"
```

**Keep Legacy References In**:
- MIGRATION.md - comparing old vs new
- CHANGELOG.md - historical entries
- Legacy jgo.py module
- `--ignore-jgorc` flag help

### Phase 5: Update Terminology in Code

**Files** (15 code files with comments/docstrings):
- `src/jgo/config/settings.py` - Docstrings
- `src/jgo/cli/commands/*.py` - All command files
- `src/jgo/cli/context.py`
- `src/jgo/cli/parser.py`
- `src/jgo/jgo.py` (error messages only, it's deprecated)

**Pattern**:
```python
Before: """Load configuration from ~/.jgorc"""
After:  """Load global settings from jgo settings file"""

Before: print(f"Error: {config_file} not found")
After:  print(f"Error: {get_settings_display_name(settings_file)} not found")
```

**Error Messages**: Use `manager.get_settings_display_name()` for dynamic paths.

### Phase 6: Update Constants

**File**: `src/jgo/constants.py`

Add:
```python
SETTINGS_FILE_DISPLAY_NAME = "jgo settings file"
SETTINGS_FILE_LEGACY_NAME = "~/.jgorc"
```

Update imports across codebase to use these constants.

### Phase 7: Update Tests

**Files**:
- `tests/test_config.py`
- `tests/test_phase4_commands.py`
- `tests/test_run.py`

**New Test Coverage**:
1. Settings write operations - Test `GlobalSettings.save()`, `set_*()`, `unset_*()`
2. Settings path resolution - Test XDG preference, legacy fallback
3. Terminology display - Test `get_settings_display_name()`
4. Backward compatibility - Test reading old format, `--ignore-jgorc` flag

### Phase 8: Handle Legacy Code

**File**: `src/jgo/jgo.py`

**Approach**: Keep deprecated code as-is (will be removed in 3.0). Add comment pointing to new implementation:
```python
# DEPRECATED: Use GlobalSettings.expand_shortcuts() instead (see src/jgo/config/settings.py)
def expand_coordinate(coordinate, shortcuts={}):
    ...
```

## Critical Files (in order of modification)

1. `src/jgo/config/manager.py` - NEW (Phase 1)
2. `src/jgo/config/file.py` → `src/jgo/config/settings.py` - Rename file, rename JgoConfig → GlobalSettings, extend with write operations (Phase 2)
3. `src/jgo/cli/commands/config.py` - Refactor config commands to use GlobalSettings (Phase 3)
4. `src/jgo/cli/helpers.py` - Remove helpers (Phase 3)
5. `src/jgo/constants.py` - Add terminology constants (Phase 6)
6. Documentation files - 8 files (Phase 4)
7. CLI command files - 15 files (Phase 5)
8. Test files - 3 files (Phase 7)
9. `src/jgo/jgo.py` - Add deprecation comments (Phase 8)

## Execution Order

**Must be sequential**:
1. Phase 1 → Phase 2 → Phase 3 (foundation first)
2. Then Phase 4-6 in any order (terminology updates)
3. Phase 7 last (verify everything works)
4. Phase 8 anytime (low risk, comments only)

**Reasoning**: Build infrastructure before using it, update terminology after new infrastructure exists, test at the end.

## Backward Compatibility

**Guaranteed to work**:
- Existing .jgorc files (read correctly)
- `--ignore-jgorc` flag
- Old setting names (cacheDir, m2Repo)
- Legacy Python API

**User-visible changes**:
- Help messages say "jgo settings file" instead of "~/.jgorc"
- Error messages show actual settings file path

**Unchanged**:
- File location priority (XDG first, then ~/.jgorc)
- INI file format
- Settings sections (settings, repositories, shortcuts)

## Success Criteria

- ✅ GlobalSettings can read and write settings files
- ✅ CLI commands use GlobalSettings (not raw ConfigParser)
- ✅ No hardcoded `~/.jgorc` in user-facing messages (except backward compat)
- ✅ Help messages show "jgo settings file"
- ✅ Consistent terminology: "global settings" vs "project config"
- ✅ All tests pass
- ✅ Test coverage for new write operations

## Risk Mitigation

**Potential Issues**:
1. Settings file format changes → Mitigation: Continue reading both formats
2. CLI behavior changes → Mitigation: Keep output structure, only update terminology
3. API changes → Mitigation: All new methods are additions, not changes
4. Import breakage from renames → Mitigation: Update all imports in same commit as rename

**Testing Strategy**:
- Run tests after each phase
- Manual test config operations
- Final integration test: init → config set → run

## Progress Tracking

- [x] Phase 1: Create Config Manager Module
- [x] Phase 2: Extend GlobalSettings with Write Operations
- [x] Phase 3: Refactor CLI Config Commands
- [x] Phase 4: Update Terminology in Documentation
- [x] Phase 5: Update Terminology in Code
- [x] Phase 6: Update Constants
- [x] Phase 7: Update Tests
- [x] Phase 8: Handle Legacy Code

**Status: ✅ COMPLETE** - All 8 phases finished successfully. All 250 tests passing.

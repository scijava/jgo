# Output Subsystem Design

This document describes jgo's output subsystem, covering both **logging** (progress reporting on operations) and **non-logging** (information produced by commands) output, the role of Rich and rich-click, and usage guidelines for output-related functions.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Output Categories](#output-categories)
- [Console Management](#console-management)
- [Logging Infrastructure](#logging-infrastructure)
- [Output Functions](#output-functions)
- [Rich Integration](#rich-integration)
- [Usage Guidelines](#usage-guidelines)
- [Progress Bars](#progress-bars)

## Overview

jgo's output subsystem is designed around a clear separation between two types of output:

1. **Logging output** (stderr): Progress reporting, status updates, warnings, errors
2. **Data output** (stdout): Information produced by commands (classpaths, dependencies, etc.)

This separation allows users to:
- Pipe command data to other tools while still seeing progress on stderr
- Control verbosity independently from data output
- Suppress logging while preserving data output with `--quiet`
- Use colored/styled output or plain text for both channels independently

The subsystem is built on:
- **Rich**: Terminal formatting library providing colors, tables, trees, panels
- **rich-click**: Click wrapper for styled help text
- **Python logging**: Standard logging infrastructure with Rich handler

## Architecture

### Key Modules

```
src/jgo/
├── util/
│   ├── console.py       # Console management (stdout/stderr Rich Consoles)
│   ├── logging.py       # Logging setup and log_exception_if_verbose
│   ├── rich_utils.py    # Custom Rich components (NoWrapTree, NoWrapTable)
│   └── toml.py          # TOML utilities (tomllib + load_toml_file)
├── cli/
│   ├── colors.py        # Early color mode detection for rich-click
│   ├── output.py        # Output functions (print_dry_run, handle_dry_run, print_*)
│   └── helpers.py       # DEPRECATED: backward compatibility shims
├── config/
│   └── settings.py      # GlobalSettings + parse_config_key
├── env/
│   └── spec.py          # EnvironmentSpec + load_or_error classmethod
└── maven/
    └── dependency_printer.py  # Dependency formatting (trees and lists)
```

### Initialization Flow

1. **`__main__.py`**: Imports `cli.colors` first to configure rich-click
2. **`cli.colors`**: Parses `--color` from `sys.argv`, configures rich-click globally
3. **`cli.parser.cli()`**: Main Click group callback runs before any command:
   - Calls `setup_consoles(color, quiet, no_wrap)` → configures stdout/stderr consoles
   - Calls `setup_logging(verbose)` → configures Python logging with RichHandler
4. **Commands**: Use configured consoles and loggers via getters

## Output Categories

### 1. Logging Output (stderr)

**Purpose**: Report progress, status, warnings, and errors to the user

**Channel**: stderr (via `_err_console` or Python logging)

**Control**: 
- Verbosity level: `-v` (INFO), `-vv` (DEBUG)
- Suppression: `--quiet` (suppresses all logging)
- Color/style: `--color` flag

**Examples**:
```python
import logging
_log = logging.getLogger(__name__)

# Levels controlled by -v flags
_log.debug("Loaded spec file from jgo.toml")       # -vv
_log.info("Added 3 dependencies to jgo.toml")      # -v
_log.warning("No new dependencies added")          # default
_log.error("Failed to load jgo.toml")              # always (unless --quiet)
```

**When to use**: Operations that take time, status changes, problems encountered, debugging information.

### 2. Data Output (stdout)

**Purpose**: Produce structured information for consumption by users or other tools

**Channel**: stdout (via `print()` or `_console.print()`)

**Control**:
- Suppression: `--quiet` (suppresses all output including data)
- Color/style: `--color` flag
- Wrapping: `--no-wrap` flag (for long lines in tables/trees)

**Examples**:
```python
# Raw data (machine-parseable) - use print()
for jar_path in environment.class_path_jars:
    print(jar_path)

# Formatted data (human-friendly) - use _console.print()
from ..util.console import get_console
_console = get_console()

_console.print("[cyan]Dependencies:[/]")
_console.print(f"  {dependency_count} resolved")
```

**When to use**: Outputting requested information (classpaths, dependency lists, version info, search results).

## Console Management

### Module: `util/console.py`

Provides centralized Rich Console instances configured once at startup.

#### Functions

**`setup_consoles(color, quiet, no_wrap)`**
- Called once at CLI startup (in `cli.parser.cli()`)
- Configures global console instances based on flags
- Color modes:
  - `"auto"`: Rich's default TTY detection
  - `"rich"` (alias `"always"`): Force full color + style even if not TTY
  - `"styled"`: Bold/italic only, no color (NO_COLOR compliant)
  - `"plain"` (alias `"never"`): No ANSI codes at all
- Quiet mode: Suppresses all output (both data and logging)
- No-wrap mode: Disables text wrapping in Rich output

**`get_console() -> Console`**
- Returns the stdout console instance
- Use for **data output** with Rich formatting

**`get_err_console() -> Console`**
- Returns the stderr console instance
- Use for **logging-like messages** that aren't part of Python logging

**`get_color_mode() -> str`**
- Returns current color mode: `"auto"`, `"rich"`, `"styled"`, or `"plain"`

**`get_no_wrap() -> bool`**
- Returns whether no-wrap mode is enabled
- Used by functions that create trees/tables to decide which variant to use

**`console_print(*objects, stderr=False, highlight=None, **kwargs)`**
- Convenience wrapper around Console.print()
- Automatically applies `soft_wrap=True` in no-wrap mode
- Disables highlighting in no-wrap mode (cleaner grep output)

#### Global State

```python
_console: Console        # Stdout console (for data)
_err_console: Console    # Stderr console (for logging-like messages)
_color_mode: str         # Current color mode
_no_wrap: bool           # Whether no-wrap mode is enabled
```

## Logging Infrastructure

### Module: `util/logging.py`

Provides structured logging with Rich formatting.

#### Functions

**`setup_logging(verbose)`**
- Called once at CLI startup (after `setup_consoles()`)
- Configures root `"jgo"` logger with RichHandler
- Verbosity levels:
  - `0`: WARNING (default)
  - `1`: INFO (with `-v`)
  - `2+`: DEBUG (with `-vv` or more)
- Uses stderr console from `get_err_console()`

**`get_log(name="jgo") -> logging.Logger`**
- Get a logger instance for a module
- All module loggers should be children of "jgo" root logger

**`get_log_level() -> int`**
- Returns current log level (logging.DEBUG, logging.INFO, etc.)

**`is_debug_enabled() -> bool`**
- Check if DEBUG logging is enabled (verbose >= 2)

**`is_info_enabled() -> bool`**
- Check if INFO logging is enabled (verbose >= 1)

#### Logger Pattern

Every module creates its logger at module level:

```python
import logging
_log = logging.getLogger(__name__)

# Later in functions:
_log.debug("Detailed information")
_log.info("Status update")
_log.warning("Potential issue")
_log.error("Problem occurred")
```

## Output Functions

### Module: `cli/output.py`

High-level output functions for CLI commands that produce data.

#### Message Output

**`print_dry_run(message: str)`**
- Prints a cyan `[DRY-RUN]` prefixed message
- Uses `_console.print()` → stdout
- Example: `[DRY-RUN] Would add 5 dependencies`

#### Data Output Functions

All data output functions use a consistent pattern:
- Print actual data with `print()` (raw, no Rich formatting) for machine-parseability
- Print headers/messages with `_console.print()` or `_err_console.print()` (Rich formatted)
- Send errors to `_err_console` (stderr)

**`print_classpath(environment)`**
- Prints classpath JARs, one per line
- Uses `print()` for actual paths → stdout (pipeable!)
- Uses `_err_console.print()` for errors → stderr

**`print_modulepath(environment)`**
- Prints module-path JARs, one per line
- Same pattern: `print()` for data, `_err_console` for errors

**`print_jars(environment)`**
- Prints both classpath and module-path JARs with headers
- Headers use `_console.print()` with Rich markup
- JARs use `print()` for machine-parseability

**`print_main_classes(environment)`**
- Scans JARs for classes with main methods
- Groups by JAR name, pretty-printed with Rich

**`print_dependencies(components, context, boms, list_mode, direct_only)`**
- Prints dependency list (flat) or tree
- List mode: Uses `format_dependency_list_rich()` → colored lines
- Tree mode: Uses `format_dependency_tree_rich()` → Rich Tree
- Respects `--no-wrap` via `get_no_wrap()`

**`print_java_info(environment)`**
- Analyzes bytecode to determine Java requirements
- Uses Rich Panel, Table, and formatted output
- Respects `--no-wrap` for table column widths

**`handle_dry_run(args, message) -> bool`**
- Checks for dry-run mode and prints message if active
- Returns True if dry run (caller should return 0), False otherwise
- Uses `print_dry_run()` internally

### Module: `cli/helpers.py` ⚠️ **DEPRECATED**

This module now only contains backward compatibility shims. All functions have been moved to more appropriate locations:

**Moved Functions:**
- `handle_dry_run` → `cli/output.py` 
- `load_spec_file` → `env/spec.py` as `EnvironmentSpec.load_or_error()`
- `parse_config_key` → `config/settings.py`
- `load_toml_file` → `util/toml.py`
- `print_exception_if_verbose` → `util/logging.py` as `log_exception_if_verbose()`

**Removed Functions:**
- `verbose_print()` - REMOVED: Use `_log.debug()` instead
- `verbose_multiline()` - REMOVED: Use logging instead

The module will be removed entirely in jgo 3.0.

### Module: `util/logging.py`

**`log_exception_if_verbose(verbose, level=1)`**
- Prints full traceback if verbose level is high enough
- Args: verbose (int), level (int, default 1)
- Example:
  ```python
  try:
      risky_operation()
  except Exception as e:
      _log.error(f"Operation failed: {e}")
      log_exception_if_verbose(args.verbose)
  ```

### Module: `util/toml.py`

**`load_toml_file(path) -> dict | None`**
- Loads TOML file and returns parsed dict
- Returns None if file doesn't exist
- Handles Python 3.11+ tomllib vs older tomli
- Used by config commands

### Module: `config/settings.py`

**`parse_config_key(key, default_section="settings") -> tuple[str, str]`**
- Parses config key into (section, key_name)
- Examples:
  - `"cache_dir"` → `("settings", "cache_dir")`
  - `"repositories.central"` → `("repositories", "central")`

### Module: `env/spec.py`

**`EnvironmentSpec.load_or_error(path) -> EnvironmentSpec`** (classmethod)
- Loads spec file with user-friendly error handling
- Logs helpful messages if file doesn't exist or is invalid
- Raises FileNotFoundError or ValueError with context
- Replaces the old `load_spec_file(args)` helper

### Module: `maven/dependency_printer.py`

Formats dependency data as trees and lists with Rich markup.

**`format_dependency_list(root, dependencies) -> str`**
- Plain text formatting (no colors)
- Returns string with dependency coordinates

**`format_dependency_list_rich(root, dependencies) -> list[str]`**
- Rich markup formatting with colors:
  - Cyan: groupId
  - Bold: artifactId  
  - Green: version
- Returns list of formatted lines

**`format_dependency_tree(root) -> str`**
- Plain text tree with Unicode box characters
- Returns formatted string

**`format_dependency_tree_rich(root, no_wrap=False) -> Tree`**
- Rich Tree object with colored nodes
- Uses `NoWrapTree` if `no_wrap=True`
- Returns Rich Tree for printing with `_console.print()`

## Rich Integration

### Rich-Click (Help Text)

**Module**: `cli/colors.py`

- Configures `rich_click` globally for styled help text
- Parses `--color` early from `sys.argv` before Click validation
- Sets `rich_click.USE_RICH_MARKUP = True` for `[cyan]colored[/]` markup in help strings
- Configures color system based on detected mode

### Rich Consoles (Runtime Output)

**Module**: `util/console.py`

- Provides two Console instances: stdout and stderr
- Configured at startup based on `--color`, `--quiet`, `--no-wrap`
- Both consoles respect the same color settings

### Custom Rich Components

**Module**: `util/rich_utils.py`

**`NoWrapTree(Tree)`**
- Tree that renders with unlimited width when printed with `soft_wrap=True`
- Prevents Rich from wrapping long dependency names
- Used when `--no-wrap` flag is set

**`NoWrapTable(Table)`**
- Table that renders with unlimited width when printed with `soft_wrap=True`
- Prevents Rich from truncating column content
- Used when `--no-wrap` flag is set

**`create_tree(label, no_wrap=False) -> Tree | NoWrapTree`**
- Factory function: returns NoWrapTree if `no_wrap=True`, else Tree

**`create_table(no_wrap=False, **kwargs) -> Table | NoWrapTable`**
- Factory function: returns NoWrapTable if `no_wrap=True`, else Table

## Usage Guidelines

### Current State Analysis (Post-Refactoring)

#### ✅ Good Patterns

1. **Logging in resolvers/builders**: `maven/resolver.py`, `env/builder.py` properly use `_log.debug()`, `_log.info()`, `_log.warning()`, `_log.error()` for progress reporting

2. **Data output in CLI commands**: Commands like `print_classpath()` use `print()` for actual data (machine-parseable) and `_console.print()` for headers/messages

3. **Separation of channels**: All code correctly sends logging to stderr and data to stdout

4. **Module-level loggers**: All modules create loggers as `_log = logging.getLogger(__name__)`

5. **Helper functions organized**: Functions moved to appropriate modules (config, logging, util, env)

6. **Config command fixed**: Now uses `_console.print()` for formatted output and `_log.debug()` for verbose messages

#### ⚠️ Remaining Issues

1. **Missing logging for progress-reporting operations**:
   - `maven/resolver.py`: Downloads use `_log.debug()` for normal artifacts, `_log.info()` for snapshots
     - **Issue**: Regular downloads are silent at default verbosity, user doesn't see progress
   - `env/builder.py`: No logging for JAR linking operations
   - `cli/commands/sync.py`: Minimal progress reporting during sync

2. **Some commands still use plain `print()` for messages**:
   - `cli/commands/search.py`: Uses `print()` for result display (should arguably use `_console.print()` with highlight=False)
   - Some config error messages could benefit from Rich formatting

3. **No progress bars**: Long operations (downloads, linking) have no visual feedback

### Best Practices

#### When to Use `print()` vs `_console.print()` vs Logging

After refactoring and testing, here's the **verified clean output approach**:

**Use `print()`** for:
- ✅ Machine-parseable data (classpaths, coordinates)
- ✅ Data intended for piping to other tools
- ✅ Simple, unformatted output where styling adds no value

**Use `_console.print()`** for:
- ✅ Headers, labels, section dividers
- ✅ Formatted/styled output (colors, bold, etc.)
- ✅ Messages to the user (but not progress → use logging!)
- ✅ Dry-run messages
- ⚠️ **Important**: Use `rich.markup.escape()` for text containing `[...]` that should be printed literally (e.g., `[settings]` section headers)

**Use `_err_console.print()`** for:
- ✅ Error messages that aren't Python exceptions
- ✅ Warnings that aren't part of logging
- ✅ Tips/hints to the user about errors

**Use logging (`_log.*`)** for:
- ✅ Progress reporting ("Resolving dependencies...")
- ✅ Status updates ("Added 3 dependencies")
- ✅ Warnings about potential issues
- ✅ Errors with context
- ✅ Debug information

#### Systematic Approach

```python
# === Data Output Pattern ===
from ..util.console import get_console
_console = get_console()

def print_some_data(data):
    """Print data for consumption."""
    # Headers and labels: Rich formatted
    _console.print("[cyan]Results:[/]")
    
    # Actual data: Plain print for machine-parseability
    for item in data:
        print(item)

# === Text with Square Brackets Pattern ===
from rich.markup import escape

def print_config_section():
    """Print configuration with section headers like [settings]."""
    # Use escape() to prevent Rich from interpreting [...] as markup
    _console.print(escape("[settings]"))
    _console.print(f"  cache_dir = {cache_dir}")

# === Progress Reporting Pattern ===
import logging
_log = logging.getLogger(__name__)

def do_operation(args):
    """Perform an operation with progress reporting."""
    _log.info("Starting operation...")
    
    for item in items:
        _log.debug(f"Processing {item}")
        # do work
    
    _log.info(f"Completed: processed {len(items)} items")

# === Error Handling Pattern ===
from jgo.util.logging import log_exception_if_verbose

def command_with_errors(args):
    """Handle errors properly."""
    try:
        result = do_something()
    except ValueError as e:
        _log.error(f"Invalid input: {e}")
        return 1
    except Exception as e:
        _log.error(f"Operation failed: {e}")
        log_exception_if_verbose(args.verbose)
        return 1
    
    return 0
```

### Completed Improvements

1. **✅ Refactored helper functions**: Moved to appropriate modules
   - `handle_dry_run` → `cli/output.py`
   - `load_spec_file` → `env/spec.py` as `EnvironmentSpec.load_or_error()`
   - `parse_config_key` → `config/settings.py`
   - `load_toml_file` → `util/toml.py`
   - `print_exception_if_verbose` → `util/logging.py` as `log_exception_if_verbose()`

2. **✅ Fixed config command**: Converted to use `_console.print()` for formatted output and proper logging

3. **✅ Removed deprecated functions**: `verbose_print()` and `verbose_multiline()` removed

4. **✅ Verified clean output**: Tested that `_console.print()` with `--color=plain` produces no ANSI codes

### Recommendations for Future Work

1. **Convert search command output**: Change `cli/commands/search.py` to use `_console.print()` for formatted output

2. **Add progress logging**: 
   - `maven/resolver.py`: Use `_log.info()` for all downloads (not just snapshots)
   - `env/builder.py`: Add `_log.info()` for JAR linking progress
   - `cli/commands/sync.py`: Add `_log.info()` for resolution steps

3. **Add Rich Progress bars** (see Progress Bars section below)

4. **Standardize on `_console.print()` everywhere**: Consider using `_console.print()` with `highlight=False` even for data output, with documentation that scripts should use `--color=plain`

## Progress Bars

### Current State

jgo does **not** currently use progress bars for long-running operations like:
- Maven dependency resolution
- JAR file downloads
- Environment building/linking

### Available Libraries

**cjdk** (already a dependency) uses **`progressbar2`**:
- Already in dependency tree via cjdk
- No additional dependency needed
- API: `progressbar.ProgressBar(max_value=n)` with `.update(i)` calls

**tqdm** (not currently a dependency):
- More popular and modern
- Better terminal detection
- Richer features (nested bars, pandas integration)
- Would require adding as a dependency

### Recommendation

**Use progressbar2** since it's already in the dependency tree via cjdk.

#### Implementation Strategy

1. **File Downloads** (`maven/resolver.py`):
   ```python
   import progressbar
   
   def download(self, artifact: Artifact) -> Path | None:
       # ... URL construction ...
       
       response = requests.get(url, stream=True)
       total_size = int(response.headers.get('content-length', 0))
       
       if total_size > 0 and is_info_enabled():
           bar = progressbar.ProgressBar(max_value=total_size)
           downloaded = 0
       
       with open(cached_file, 'wb') as f:
           for chunk in response.iter_content(chunk_size=8192):
               f.write(chunk)
               if total_size > 0 and is_info_enabled():
                   downloaded += len(chunk)
                   bar.update(downloaded)
   ```

2. **Multi-JAR Operations** (`env/builder.py`):
   ```python
   import progressbar
   
   def _link_jars(self, artifacts: list[Artifact]):
       if is_info_enabled():
           widgets = [
               'Linking JARs: ',
               progressbar.Counter(), f'/{len(artifacts)} ',
               progressbar.Bar(), ' ',
               progressbar.ETA()
           ]
           bar = progressbar.ProgressBar(max_value=len(artifacts), widgets=widgets)
       
       for i, artifact in enumerate(artifacts):
           link_file(source, dest)
           if is_info_enabled():
               bar.update(i + 1)
   ```

3. **Conditional Display**:
   - Only show progress bars when `is_info_enabled()` (i.e., `-v` flag)
   - Don't show in quiet mode or at default verbosity
   - Ensures progress bars don't interfere with data output
   - Falls back to simple logging at default verbosity

4. **Integration with Rich**:
   - progressbar2 outputs to stderr by default ✅
   - Won't interfere with stdout data output ✅
   - Rich logging will properly handle interleaving
   - Consider using Rich's `Progress` instead for better integration:
     ```python
     from rich.progress import Progress
     
     with Progress(console=get_err_console()) as progress:
         task = progress.add_task("Downloading...", total=total_size)
         for chunk in response.iter_content():
             progress.update(task, advance=len(chunk))
     ```

### Rich Progress vs progressbar2

**Rich Progress advantages**:
- ✅ Better integration with Rich console system
- ✅ Respects `--color` and `--quiet` flags automatically
- ✅ Can show multiple progress bars simultaneously
- ✅ More modern, actively maintained
- ✅ Consistent styling with rest of jgo output

**Rich Progress is recommended** over progressbar2:
- Already have Rich as a dependency
- Better integration with console system
- More features and flexibility
- Single dependency for all terminal formatting

### Example Implementation with Rich Progress

```python
# In maven/resolver.py
from rich.progress import Progress, DownloadColumn, TransferSpeedColumn
from ..util.console import get_err_console
from ..util.logging import is_info_enabled

def download(self, artifact: Artifact) -> Path | None:
    # ... URL setup ...
    
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    if is_info_enabled() and total_size > 0:
        # Show progress bar at info level (-v)
        with Progress(
            *Progress.get_default_columns(),
            DownloadColumn(),
            TransferSpeedColumn(),
            console=get_err_console()
        ) as progress:
            task = progress.add_task(f"Downloading {artifact.artifactId}", total=total_size)
            
            with open(cached_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    progress.update(task, advance=len(chunk))
    else:
        # No progress bar - download without display
        with open(cached_file, 'wb') as f:
            f.write(response.content)
    
    _log.debug(f"Downloaded {artifact} to {cached_file}")
    return cached_file
```

## Summary

jgo's output subsystem provides:
- ✅ Clear separation between logging (stderr) and data (stdout)
- ✅ Flexible color/style control via `--color` flag
- ✅ Consistent verbosity control via `-v` flags
- ✅ Rich formatting for beautiful terminal output
- ✅ Machine-parseable data output via plain `print()` or `_console.print()` with `--color=plain`
- ✅ Well-organized helper functions in appropriate modules
- ✅ Config command using proper output methods
- ✅ Deprecated functions removed
- ⚠️ Could benefit from progress bars for long operations
- ⚠️ Could benefit from more INFO-level logging for user feedback

**Completed in this refactoring**:
1. ✅ Moved helper functions to appropriate modules
2. ✅ Fixed config command output to use `_console.print()` and logging
3. ✅ Removed `verbose_print()` and `verbose_multiline()`
4. ✅ Added `log_exception_if_verbose()` to util/logging.py
5. ✅ Verified `_console.print()` produces clean output with `--color=plain`
6. ✅ All 502 tests passing

**Next steps**:
1. Add Rich Progress bars for downloads and linking operations
2. Increase INFO-level logging for better user feedback
3. Consider standardizing on `_console.print()` everywhere for consistency

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
├── cli/
│   ├── colors.py        # Early color mode detection for rich-click
│   ├── console.py       # Console management (stdout/stderr Rich Consoles)
│   ├── output.py        # Output functions (print_dry_run, handle_dry_run, print_*)
│   └── rich/
│       ├── formatters.py  # Dependency formatting (trees and lists)
│       └── widgets.py     # Custom Rich components (NoWrapTree, NoWrapTable)
├── config/
│   └── settings.py      # GlobalSettings + parse_config_key
├── env/
│   └── spec.py          # EnvironmentSpec + load_or_error classmethod
└── util/
    ├── logging.py       # Logging setup and log_exception_if_verbose
    └── toml.py          # TOML utilities (tomllib + load_toml_file)
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

**Channel**: stdout (via `console_print()`)

**Control**:
- Suppression: `--quiet` (suppresses all output including data)
- Color/style: `--color` flag (automatically respected)
- Wrapping: `--wrap` flag (automatically handled) - `auto` for TTY detection, `smart` for word-boundary wrapping, `raw` for natural terminal wrapping

**Both raw and formatted data use the same function**:
```python
from ..console import console_print

# Raw data (machine-parseable) - use console_print()
for jar_path in environment.class_path_jars:
    console_print(jar_path)

# Formatted data (human-friendly) - use console_print() with Rich markup
console_print("[cyan]Dependencies:[/]")
console_print(f"  {dependency_count} resolved")

# Works correctly for piping:
# - With --color=plain: outputs plain text, no ANSI codes
# - With --color=rich: outputs colored text for TTY
# - Works with pipes and file redirection automatically
```

**When to use**: Outputting requested information (classpaths, dependency lists, version info, search results). The `console_print()` function automatically respects all color and wrap settings, so it works correctly for both interactive terminal use and scripting via pipes.

## Console Management

### Module: `cli/console.py`

Provides centralized Rich Console instances configured once at startup.

#### Functions

**`setup_consoles(color, quiet, wrap)`**
- Called once at CLI startup (in `cli.parser.cli()`)
- Configures global console instances based on flags
- Color modes:
  - `"auto"`: Rich's default TTY detection
  - `"rich"` (alias `"always"`): Force full color + style even if not TTY
  - `"styled"`: Bold/italic only, no color (NO_COLOR compliant)
  - `"plain"` (alias `"never"`): No ANSI codes at all
- Quiet mode: Suppresses all output (both data and logging)
- Wrap modes:
  - `"auto"` (default): Smart for TTY, raw for pipes/files
  - `"smart"`: Rich's intelligent wrapping at word boundaries
  - `"raw"`: Natural terminal wrapping without constraints

**`get_console() -> Console`**
- Returns the stdout console instance
- Use for **data output** with Rich formatting

**`get_err_console() -> Console`**
- Returns the stderr console instance
- Use for **logging-like messages** that aren't part of Python logging

**`get_color_mode() -> str`**
- Returns current color mode: `"auto"`, `"rich"`, `"styled"`, or `"plain"`

**`get_wrap_mode() -> str`**
- Returns current wrap mode: `"smart"` or `"raw"`
- The `"auto"` mode is resolved to `"smart"` or `"raw"` in `setup_consoles()` using `console.is_terminal`
- This ensures consistency with Rich's TTY detection

#### Global State

```python
_console: Console        # Stdout console (for data)
_err_console: Console    # Stderr console (for logging-like messages)
_color_mode: str         # Current color mode ("auto", "rich", "styled", "plain")
_wrap_mode: str          # Current wrap mode ("smart" or "raw", auto is resolved in setup_consoles)
_quiet: bool             # Whether quiet mode is enabled
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

#### Rich Markup in Log Messages

**RichHandler is configured with `markup=False`**, which has important implications:

**✅ What IS enabled** (built-in RichHandler features):
- Log level colors (DEBUG=blue, INFO=green, WARNING=yellow, ERROR=red)
- Module:line formatting when verbose >= 2 (`show_path=True`)
- Rich tracebacks for better exception formatting
- Nice layout and styling

**❌ What is NOT enabled** (markup processing in message content):
- Rich markup tags like `[red]text[/]`, `[bold]text[/]` - will be shown literally
- Emoji substitution like `:emoji_name:` (e.g., `:fire:`, `:fiji:`) - will be shown literally

**Rationale:**
1. **Prevents collisions with user data**: Maven coordinates like `sc.fiji:fiji:2.17.0` contain the pattern `:fiji:` which Rich would interpret as the Fiji flag emoji 🇫🇯 if markup were enabled
2. **Keeps logs simple**: Log messages should be plain text for debugging and grepping
3. **No need for markup in logs**: RichHandler already provides sufficient styling via log levels

**Example:**
```python
import logging
_log = logging.getLogger(__name__)

# ✅ Good: Plain text logging
_log.debug("Processing sc.fiji:fiji:2.17.0")
_log.info("Added 3 dependencies")

# ❌ Don't use markup in log messages (won't work)
_log.debug("[cyan]Processing[/] sc.fiji:fiji:2.17.0")  # Tags shown literally

# ✅ For styled user messages, use console_print() instead
from ..console import console_print
console_print("[cyan]Processing:[/] sc.fiji:fiji:2.17.0")
```

**Note:** If you need to include text with literal square brackets (e.g., `[settings]` section names) in console output, use `rich.markup.escape()` to prevent misinterpretation as markup tags.

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
- Uses `console_print()` → stdout
- Example: `[DRY-RUN] Would add 5 dependencies`

#### Data Output Functions

All data output functions use a consistent pattern:
- Print all data (raw and formatted) with `console_print()`
- Print headers/messages with `console_print()` (Rich markup is supported)
- Send errors to `_err_console` or `console_print(..., stderr=True)` (stderr)

The `console_print()` function automatically respects `--color` and `--wrap` flags, so the same code works for both interactive terminal use and piping.

**`print_classpath(environment)`**
- Prints classpath JARs, one per line
- Uses `console_print()` for actual paths → stdout
- With `--color=plain`: outputs paths without ANSI codes (perfect for piping)
- With `--color=rich`: outputs colored paths for TTY
- Errors go to stderr

**`print_modulepath(environment)`**
- Prints module-path JARs, one per line
- Same pattern: all output uses `console_print()`

**`print_jars(environment)`**
- Prints both classpath and module-path JARs with headers
- Headers use `console_print()` with Rich markup
- JARs use `console_print()`
- All output respects color and wrap settings

**`print_main_classes(environment)`**
- Scans JARs for classes with main methods
- Groups by JAR name, pretty-printed with Rich
- Uses `console_print()` for formatted output

**`pom` command (in `cli/commands/info.py`)**
- Shows POM content with syntax highlighting
- Uses `console_print()` with XML string directly (not a Rich Syntax object)
- Behavior by color mode:
  - `plain` or `auto` (non-TTY): Plain XML without ANSI codes
  - `rich` or `auto` (TTY): Colored XML with basic highlighting (tags, slashes)
  - `styled`: Plain XML (Rich's no_color mode limitation - no syntax highlighting)
- Respects `--wrap` mode via automatic `soft_wrap` handling in `console_print()`

**`print_dependencies(components, context, boms, list_mode, direct_only)`**
- Prints dependency list (flat) or tree
- List mode: Uses `format_dependency_list()` → colored lines via `console_print()`
- Tree mode: Uses `format_dependency_tree()` → Rich Tree (NoWrapTree variant for raw mode)
- Respects `--wrap` mode via automatic `soft_wrap` handling in `console_print()`

**`print_java_info(environment)`**
- Analyzes bytecode to determine Java requirements
- Uses Rich Panel, Table (NoWrapTable variant for raw mode), and formatted output
- Uses `console_print()` for all output
- Respects `--wrap` mode automatically

**`handle_dry_run(args, message) -> bool`**
- Checks for dry-run mode and prints message if active
- Returns True if dry run (caller should return 0), False otherwise
- Uses `print_dry_run()` internally

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

### Module: `cli/rich/formatters.py`

Formats dependency data as trees and lists with Rich markup.

**`format_dependency_list(root, dependencies) -> list[str]`**
- Rich markup formatting with colors:
  - Cyan: groupId
  - Bold: artifactId
  - Green: version
- Returns list of formatted lines

**`format_dependency_tree(root, no_wrap=False) -> Tree`**
- Rich Tree object with colored nodes
- Uses `NoWrapTree` if `no_wrap=True`
- Returns Rich Tree for printing with `console_print(tree)`

## Rich Integration

### Rich-Click (Help Text)

**Module**: `cli/colors.py`

- Configures `rich_click` globally for styled help text
- Parses `--color` early from `sys.argv` before Click validation
- Sets `rich_click.USE_RICH_MARKUP = True` for `[cyan]colored[/]` markup in help strings
- Configures color system based on detected mode

### Rich Consoles (Runtime Output)

**Module**: `cli/console.py`

- Provides two Console instances: stdout and stderr
- Configured at startup based on `--color`, `--quiet`, `--wrap`
- Both consoles respect the same color settings
- Wrap mode is applied per-call via `soft_wrap` parameter to `console_print()`

### Custom Rich Components

**Module**: `cli/rich/widgets.py`

**`NoWrapTree(Tree)`**
- Tree that renders with unlimited width when printed with `soft_wrap=True`
- Allows full dependency names to wrap naturally at terminal edge
- Used when `--wrap=raw` flag is set
- Combined with `console_print(tree)` for natural wrapping

**`NoWrapTable(Table)`**
- Table that renders with unlimited width when printed with `soft_wrap=True`
- Allows full column content without truncation, wrapping naturally
- Used when `--wrap=raw` flag is set
- Combined with `console_print(table)` for natural wrapping

**`create_tree(label, no_wrap=False, **kwargs) -> Tree | NoWrapTree`**
- Factory function: returns NoWrapTree if `no_wrap=True`, else Tree

**`create_table(no_wrap=False, **kwargs) -> Table | NoWrapTable`**
- Factory function: returns NoWrapTable if `no_wrap=True`, else Table

### Wrap Mode Implementation

Wrap modes are implemented in `console_print()` by passing the `soft_wrap` parameter to `console.print()`:

**Auto mode** (`--wrap=auto`, default):
- Resolved at startup in `setup_consoles()` using `console.is_terminal`
- Uses `smart` for TTY (terminal display)
- Uses `raw` for non-TTY (pipes, file redirection)
- Mirrors the philosophy of `--color=auto`
- Ensures consistency with Rich's TTY detection

**Smart mode** (`--wrap=smart`):
- Uses `console.print(content, soft_wrap=False)`
- Rich applies intelligent word-boundary wrapping
- Tables and trees are constrained to terminal width
- Long lines wrap at word boundaries

**Raw mode** (`--wrap=raw`):
- Uses `console.print(content, soft_wrap=True)`
- Natural terminal wrapping without Rich constraints
- NoWrapTree/NoWrapTable variants render with unlimited width
- Content wraps naturally at terminal edge, mid-word if needed

**Example usage:**
```python
from ..console import get_wrap_mode

# Get resolved wrap mode (auto is already resolved in setup_consoles)
wrap_mode = get_wrap_mode()  # Returns "smart" or "raw"
no_wrap = wrap_mode == "raw"

# For trees
rich_tree = format_dependency_tree(tree, no_wrap=no_wrap)
console.print(rich_tree, soft_wrap=no_wrap)

# For tables
table = create_table(no_wrap=no_wrap)
# ... add rows ...
console.print(table, soft_wrap=no_wrap)

# For simple text (like info pom XML output)
wrap_mode = get_wrap_mode()
console.print(xml_output, soft_wrap=(wrap_mode == "raw"))
```

## Usage Guidelines

### Current State Analysis (Post-Refactoring)

#### ✅ Good Patterns

1. **Logging in resolvers/builders**: `maven/resolver.py`, `env/builder.py` properly use `_log.debug()`, `_log.info()`, `_log.warning()`, `_log.error()` for progress reporting

2. **Unified data output**: All CLI commands use `console_print()` for data output (both raw and formatted)
   - Example: `print_classpath()` uses `console_print()` for paths
   - Works correctly for piping with `--color=plain` and interactive use with colors

3. **Separation of channels**: All code correctly sends logging to stderr and data to stdout
   - Use `console_print(..., stderr=True)` or `_err_console.print()` for stderr output

4. **Module-level loggers**: All modules create loggers as `_log = logging.getLogger(__name__)`

5. **Helper functions organized**: Functions moved to appropriate modules (config, logging, util, env)

6. **Output consistency**: All commands use `console_print()` for formatted output

#### ⚠️ Remaining Issues

1. **Missing logging for progress-reporting operations**:
   - `maven/resolver.py`: Downloads use `_log.debug()` for normal artifacts, `_log.info()` for snapshots
     - **Issue**: Regular downloads are silent at default verbosity, user doesn't see progress
   - `env/builder.py`: No logging for JAR linking operations
   - `cli/commands/sync.py`: Minimal progress reporting during sync

2. **No progress bars**: Long-running operations don't have visual progress indicators
   - Recommendation: Add Rich Progress bars shown at `-v` verbosity level

### Best Practices

#### When to Use `console_print()` vs `_err_console.print()` vs Logging

After refactoring and testing, here's the **verified unified output approach**:

**Use `console_print()`** for:
- ✅ All stdout data output (machine-parseable classpaths, coordinates)
- ✅ Data intended for piping to other tools
- ✅ Headers, labels, section dividers
- ✅ Formatted/styled output (colors, bold, etc.)
- ✅ Messages to the user (but not progress → use logging!)
- ✅ Dry-run messages
- ✅ Both raw and formatted data - `console_print()` handles all cases
- ⚠️ **Important**: Use `rich.markup.escape()` for text containing `[...]` that should be printed literally (e.g., `[settings]` section headers)
- **How it works**: Automatically respects `--color` and `--wrap` flags, making it safe for piping to other tools

**Use `console_print(..., stderr=True)` or `_err_console.print()`** for:
- ✅ Error messages that aren't Python exceptions
- ✅ Warnings that aren't part of logging
- ✅ Tips/hints to the user about errors
- ✅ Output that should go to stderr instead of stdout

**Use logging (`_log.*`)** for:
- ✅ Progress reporting ("Resolving dependencies...")
- ✅ Status updates ("Added 3 dependencies")
- ✅ Warnings about potential issues
- ✅ Errors with context
- ✅ Debug information
- ⚠️ **Note**: Log messages do NOT support Rich markup (see [Rich Markup in Log Messages](#rich-markup-in-log-messages))

#### Systematic Approach

```python
# === Data Output Pattern (unified approach) ===
from ..console import console_print

def print_some_data(data):
    """Print data for consumption (works for both raw and formatted output)."""
    # Headers and labels: Rich formatted with console_print()
    console_print("[cyan]Results:[/]")

    # Actual data: Also use console_print() - it automatically handles color modes
    # With --color=plain: outputs plain text, no ANSI codes (perfect for piping)
    # With --color=rich: outputs colored text for TTY
    for item in data:
        console_print(item)

# === Text with Square Brackets Pattern ===
from rich.markup import escape

def print_config_section():
    """Print configuration with section headers like [settings]."""
    # Use escape() to prevent Rich from interpreting [...] as markup
    console_print(escape("[settings]"))
    console_print(f"  cache_dir = {cache_dir}")

# === Data to stderr Pattern ===
def print_error_info():
    """Print diagnostic info to stderr."""
    console_print("Diagnostic information:", stderr=True)
    console_print(f"  Error code: 42", stderr=True)

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

2. **✅ Fixed config command**: Converted to use `console_print()` for formatted output and proper logging

3. **✅ Removed deprecated functions**: `verbose_print()` and `verbose_multiline()` removed

4. **✅ Verified clean output**: Tested that `console_print()` with `--color=plain` produces no ANSI codes

5. **✅ Unified output approach**: All data output now uses `console_print()` instead of plain `print()`
   - `console_print()` function in `cli/console.py` automatically handles `--color` and `--wrap` flags
   - Both raw and formatted data use the same function
   - Piping works correctly: `--color=plain` produces machine-parseable output, `--color=rich` adds colors for TTY
   - No distinction between "pure data" and "formatted data" - one unified approach

### Recommendations for Future Work

1. **Add progress logging**:
   - `maven/resolver.py`: Use `_log.info()` for all downloads (not just snapshots)
   - `env/builder.py`: Add `_log.info()` for JAR linking progress
   - `cli/commands/sync.py`: Add `_log.info()` for resolution steps

2. **Add Rich Progress bars** (see Progress Bars section below)
   - Complements logging with visual progress indicators
   - Shown at `-v` verbosity level

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
- ✅ **Unified output via `console_print()`**: Machine-parseable data and formatted output use the same function
  - With `--color=plain --wrap=raw`: outputs clean, pipeable data
  - With `--color=rich --wrap=smart`: outputs colored text for interactive use
- ✅ Well-organized helper functions in appropriate modules
- ✅ All commands using proper output methods
- ✅ Deprecated functions removed
- ⚠️ Could benefit from progress bars for long operations
- ⚠️ Could benefit from more INFO-level logging for user feedback

**Completed in this refactoring**:
1. ✅ Moved helper functions to appropriate modules
2. ✅ Fixed config command output to use `console_print()` and logging
3. ✅ Removed `verbose_print()` and `verbose_multiline()`
4. ✅ Added `log_exception_if_verbose()` to util/logging.py
5. ✅ Verified `console_print()` produces clean output with `--color=plain`
6. ✅ Unified all data output to use `console_print()` instead of `print()` or `_console.print()`
7. ✅ All tests passing

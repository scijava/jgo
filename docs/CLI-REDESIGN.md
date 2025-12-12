# jgo CLI Redesign: Command-Based Interface

## Status

✅ **Phase 1 Complete** - Subcommand infrastructure with `jgo run`  
✅ **Phase 2 Complete** - Core information commands (`info`, `list`, `tree`, `versions`, `init`)  
✅ **Migration to Click** - Replaced argparse with Click for cleaner, more maintainable code  
✅ **Phase 3 Complete** - Project management commands (`add`, `remove`, `sync`, `lock`)  

## Overview

This document outlines the plan to restructure jgo's CLI from a flat flag-based interface to a modern command-based interface, following the patterns established by `uv`, `pixi`, `npm`, `cargo`, and other contemporary package managers.

**Update**: We switched from argparse to Click (which is already a transitive dependency via cjdk) for much cleaner implementation of the command-based interface.

## Goals

1. **Modern conventions** - Follow established patterns from contemporary tooling
2. **Better discoverability** - Commands are easier to explore than flags
3. **Room for growth** - Namespaced commands scale better than flat flags
4. **Backwards compatibility** - Existing `jgo <endpoint>` usage continues to work
5. **Cleaner architecture** - Each command gets focused parsing and logic

## Implementation Notes

### Why Click?

We migrated from argparse to Click because:
- Click is designed specifically for command-based CLIs
- Already a dependency (via cjdk → click)
- Much simpler to implement global options that work across commands
- Better help formatting out of the box
- Environment variable support is trivial
- Easier to maintain and extend

### Option Ordering

Modern convention: **options must come BEFORE the command/endpoint**

```bash
# Correct
jgo --dry-run org.python:jython-standalone
jgo --dry-run run org.python:jython-standalone

# Incorrect (not supported)
jgo org.python:jython-standalone --dry-run
```

This follows the pattern of modern tools like `uv`, `cargo`, `npm`, etc.

## Command Structure

### Core Workflow

```bash
jgo run [OPTIONS] [endpoint]
```
- Default command for running Java applications
- If `endpoint` provided: resolve and run from Maven coordinates
- If no `endpoint` and `jgo.toml` exists: run default entrypoint
- If no `endpoint` and no `jgo.toml`: error with helpful message
- Replaces: current `jgo <endpoint>` behavior

```bash
jgo init [OPTIONS] [endpoint]
```
- Create a new `jgo.toml` environment file
- If `endpoint` provided: initialize with that dependency
- If no `endpoint`: create minimal template
- Interactive mode could prompt for common settings
- Replaces: `--init` flag

### Project Management

```bash
jgo add [OPTIONS] <coordinate> [<coordinate> ...]
```
- Add dependencies to `jgo.toml`
- Automatically runs `jgo sync` unless `--no-sync` provided
- Options:
  - `--entrypoint NAME` - add to specific entrypoint
  - `--no-sync` - don't resolve/sync after adding
- Example: `jgo add org.python:jython-standalone:2.7.3`

```bash
jgo remove [OPTIONS] <coordinate> [<coordinate> ...]
```
- Remove dependencies from `jgo.toml`
- Automatically runs `jgo sync` unless `--no-sync` provided
- Options:
  - `--entrypoint NAME` - remove from specific entrypoint
  - `--no-sync` - don't resolve/sync after removing
- Example: `jgo remove org.python:jython-standalone`

```bash
jgo sync [OPTIONS]
```
- Resolve dependencies and build environment in `.jgo/` directory
- Updates `jgo.lock.toml` if dependencies changed
- Like `npm install` or `pip install` after editing package.json/requirements.txt
- Options:
  - `--update` - update dependency versions within constraints
  - `--offline` - work offline
  - `--force` - force rebuild even if cached

```bash
jgo lock [OPTIONS]
```
- Update `jgo.lock.toml` without building environment
- Useful for updating lock file when RELEASE versions involved
- Options:
  - `--update` - update versions within constraints
  - `--check` - verify lock file is up to date

### Information Commands

```bash
jgo list [OPTIONS]
```
- List resolved dependencies (flat list)
- Replaces: `--print-dependency-list`
- Options:
  - `--format {simple,json,table}` - output format

```bash
jgo tree [OPTIONS]
```
- Show dependency tree
- Replaces: `--print-dependency-tree`
- Options:
  - `--depth N` - limit tree depth
  - `--format {simple,json}` - output format

```bash
jgo info [OPTIONS] [coordinate]
```
- Show information about environment or specific coordinate
- If no `coordinate`: show info about current project environment
- If `coordinate`: show info about that artifact
- Replaces: `--print-java-info`, `--print-classpath`
- Options:
  - `--classpath` - show classpath
  - `--java-version` - show Java version requirements
  - `--all` - show all information

```bash
jgo versions [OPTIONS] <coordinate>
```
- List available versions of an artifact
- Replaces: `--list-versions`
- Options:
  - `--limit N` - limit results
  - `--filter PATTERN` - filter versions by pattern

```bash
jgo search [OPTIONS] <query>
```
- Search for artifacts in configured Maven repositories
- New functionality
- Options:
  - `--limit N` - limit results
  - `--repository NAME` - search specific repository
- Examples:
  - `jgo search apache commons`
  - `jgo search --repository central junit`

### Configuration

```bash
jgo config [OPTIONS] [key] [value]
```
- Manage jgo configuration
- Without args: show current config
- With key only: show value for key
- With key and value: set value
- Could subsume `~/.jgorc` functionality long-term
- Options:
  - `--global` - modify global config (~/.jgorc)
  - `--local` - modify project config (jgo.toml)
  - `--list` - list all config values
  - `--unset KEY` - remove config value
- Examples:
  - `jgo config` - show all config
  - `jgo config cache_dir` - show cache directory
  - `jgo config cache_dir ~/.local/share/jgo` - set cache directory
  - `jgo config --global repositories.central https://repo.maven.apache.org/maven2`

```bash
jgo alias [OPTIONS] <name> [main-class]
```
- Manage main class aliases (shortcuts for entry points)
- Without args: list all aliases
- With name only: show the main class for that alias
- With name and main-class: register or update an alias
- Replaces/enhances: `~/.jgorc` shortcuts functionality
- Options:
  - `--global` - modify global aliases (~/.jgorc)
  - `--local` - modify project aliases (jgo.toml)
  - `--remove NAME` - remove an alias
- Examples:
  - `jgo alias` - list all aliases
  - `jgo alias repl` - show what 'repl' maps to
  - `jgo alias repl org.scijava.script.ScriptREPL` - register alias
  - `jgo alias --remove repl` - remove alias
- Usage with run:
  - `jgo run org.scijava:scijava-common@repl` - use alias

### Utility Commands

```bash
jgo help [command]
```
- Show help information
- Without args: same as `jgo --help`
- With command: same as `jgo <command> --help`

```bash
jgo version
```
- Show jgo version
- Replaces: `--version` flag

```bash
jgo update [OPTIONS]
```
- Update dependencies to latest versions within constraints
- Alias for `jgo sync --update`
- Replaces: `-u, --update` flag behavior

## Backwards Compatibility

### Endpoint Detection

The key insight: **commands never contain colons, endpoints always do**.

```bash
jgo org.python:jython-standalone           # endpoint (has colon)
jgo run org.python:jython-standalone       # explicit command
jgo org.python:jython-standalone:2.7.3     # endpoint with version
jgo info                                    # command (no colon)
```

Implementation:
```python
def parse_args():
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        if ':' in first_arg:
            # Legacy endpoint syntax - inject 'run' command
            sys.argv.insert(1, 'run')
    # ... continue with normal argparse subcommand parsing
```

### Flag Migration

Most existing flags work naturally within the command structure:

| Old Flag | New Command/Flag |
|----------|------------------|
| `jgo <endpoint>` | `jgo run <endpoint>` (auto-detected) |
| `jgo --init` | `jgo init` |
| `jgo --list-entrypoints` | `jgo info --entrypoints` |
| `jgo --list-versions` | `jgo versions <coordinate>` |
| `jgo --print-classpath` | `jgo info --classpath` |
| `jgo --print-dependency-tree` | `jgo tree` |
| `jgo --print-dependency-list` | `jgo list` |
| `jgo --print-java-info` | `jgo info --java-version` |
| `jgo -u` | `jgo update` or `jgo sync --update` |
| `jgo --dry-run` | Applies to any command as global flag |
| `jgo -v` | Applies to any command as global flag |
| `jgo -f FILE` | `jgo -f FILE <command>` (global flag) |

### Global Flags

Some flags make sense across all commands and remain as global options:

```bash
jgo [GLOBAL_OPTIONS] <command> [COMMAND_OPTIONS] [args]

Global Options:
  -v, --verbose         Verbose output
  -q, --quiet           Suppress output
  -f, --file FILE       Use specific environment file
  --cache-dir PATH      Override cache directory
  --repo-cache PATH     Override Maven repo cache
  --offline             Work offline
  --dry-run             Show what would be done
  -h, --help            Show help
```

## Implementation Plan

### Phase 1: Subcommand Infrastructure

1. **Create subcommand framework**
   - New file: `src/jgo/cli/subcommands.py` or package `src/jgo/cli/subcommands/`
   - Update `parser.py` to use `argparse.ArgumentParser.add_subparsers()`
   - Detect legacy endpoint syntax and inject `run` command

2. **Implement `run` command**
   - Move existing endpoint execution logic into `run` subcommand
   - Keep all existing functionality
   - Ensure backwards compat with endpoint detection

3. **Update `__main__.py`**
   - Handle command dispatch
   - Preserve behavior when no args given (show help)

4. **Test backwards compatibility**
   - All existing tests should pass
   - `jgo <endpoint>` works identically
   - `jgo run <endpoint>` works identically

### Phase 2: Core Commands

Implement new commands one at a time:

1. **`jgo init`** - Move from `--init` flag
2. **`jgo info`** - Consolidate `--print-*` flags
3. **`jgo list`** - From `--print-dependency-list`
4. **`jgo tree`** - From `--print-dependency-tree`
5. **`jgo versions`** - From `--list-versions`

Each should:
- Have its own subparser with focused options
- Have its own command class/function
- Include tests
- Update documentation

### Phase 3: Project Management Commands

1. **`jgo add`** - New functionality for adding deps to jgo.toml
2. **`jgo remove`** - New functionality for removing deps
3. **`jgo sync`** - Explicit environment sync operation
4. **`jgo lock`** - Lock file management

### Phase 4: Advanced Commands

1. **`jgo search`** - Search Maven repositories
2. **`jgo config`** - Configuration management
3. **`jgo update`** - Convenience alias

### Phase 5: Polish

1. Address TODO comments in cli subpackage
2. Update all documentation
3. Add comprehensive examples
4. Consider shell completions
5. Migration guide (though should be seamless)

## Code Architecture

### Proposed Structure

```
src/jgo/cli/
├── __init__.py
├── parser.py              # Main parser, subcommand setup, global flags
├── commands.py            # Command dispatch and shared utilities (kept but refactored)
└── subcommands/
    ├── __init__.py
    ├── run.py             # jgo run
    ├── init.py            # jgo init
    ├── add.py             # jgo add
    ├── remove.py          # jgo remove
    ├── sync.py            # jgo sync
    ├── lock.py            # jgo lock
    ├── info.py            # jgo info
    ├── list.py            # jgo list
    ├── tree.py            # jgo tree
    ├── versions.py        # jgo versions
    ├── search.py          # jgo search
    ├── config.py          # jgo config
    ├── update.py          # jgo update
    └── version.py         # jgo version
```

### Subcommand Pattern

Each subcommand module should follow this pattern:

```python
"""jgo <command> - description"""

from __future__ import annotations
import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..parser import ParsedArgs

def add_parser(subparsers) -> argparse.ArgumentParser:
    """Add this command's parser to the subparsers."""
    parser = subparsers.add_parser(
        'command',
        help='Short description',
        description='Longer description',
    )
    # Add command-specific arguments
    parser.add_argument('--option', help='...')
    return parser

def execute(args: ParsedArgs, config: dict) -> int:
    """Execute the command. Returns exit code."""
    # Implementation
    return 0
```

### Parser Changes

```python
# parser.py
class JgoArgumentParser:
    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(...)
        
        # Global flags (before subcommands)
        parser.add_argument('-v', '--verbose', ...)
        parser.add_argument('-q', '--quiet', ...)
        parser.add_argument('-f', '--file', ...)
        # ... other global flags
        
        # Subcommands
        subparsers = parser.add_subparsers(
            dest='command',
            title='commands',
            description='Available commands',
        )
        
        # Import and register each subcommand
        from .subcommands import run, init, add, remove, ...
        run.add_parser(subparsers)
        init.add_parser(subparsers)
        add.add_parser(subparsers)
        # ...
        
        return parser
    
    def parse_args(self, args=None):
        # Detect legacy endpoint syntax
        if args is None:
            args = sys.argv[1:]
        
        if args and ':' in args[0] and not args[0].startswith('-'):
            # Legacy endpoint - inject 'run' command
            args.insert(0, 'run')
        
        parsed = self.parser.parse_args(args)
        
        # If no command specified, show help
        if not parsed.command:
            self.parser.print_help()
            sys.exit(0)
        
        return parsed
```

## Examples

### Before and After

```bash
# Before (still works!)
jgo org.python:jython-standalone
jgo org.python:jython-standalone:2.7.3 -- -Xmx2G

# After (explicit)
jgo run org.python:jython-standalone
jgo run org.python:jython-standalone:2.7.3 -- -Xmx2G

# New project workflow
jgo init org.python:jython-standalone:2.7.3
jgo add org.scijava:parsington
jgo run

# Information commands
jgo list
jgo tree
jgo info --classpath
jgo versions org.python:jython-standalone

# Search and explore
jgo search apache commons
jgo versions commons-io:commons-io

# Configuration
jgo config --list
jgo config cache_dir ~/.local/share/jgo
```

## Testing Strategy

1. **Backwards compatibility tests** - Ensure all old syntax still works
2. **New command tests** - Unit tests for each command
3. **Integration tests** - End-to-end workflows
4. **Documentation tests** - Examples in docs are tested

## Documentation Updates

1. **README.md** - Update with new command examples
2. **CLI reference** - Complete command documentation
3. **Migration guide** - Though should be mostly transparent
4. **Tutorial** - Step-by-step using new commands

## Open Questions

1. **Should `jgo config` eventually replace `~/.jgorc`?**
   - Could support both for backwards compat
   - `jgo config --global` writes to ~/.jgorc
   - Eventually could migrate to XDG config dirs

2. **Should there be a `jgo clean` command?**
   - Clear cache directories
   - Clean project `.jgo/` directory
   - Like `cargo clean`, `npm clean-install`

3. **Should `jgo exec` exist for running arbitrary commands in environment?**
   - Like `uv run` or `pixi run`
   - Example: `jgo exec -- javac MyClass.java`
   - Access to resolved classpath

4. **Shell completion?**
   - Generate bash/zsh/fish completion scripts
   - Would be much easier with command structure

## Benefits Summary

1. **User Experience**
   - Intuitive for users of modern tooling
   - Better help and discoverability
   - Shorter commands for common operations

2. **Maintainability**
   - Cleaner separation of concerns
   - Easier to add new commands
   - Less flag soup in parser

3. **Extensibility**
   - Easy to add subcommands
   - Natural place for new features
   - Plugin architecture possible later

4. **Backwards Compatibility**
   - Existing usage keeps working
   - No breaking changes for users
   - Smooth migration path

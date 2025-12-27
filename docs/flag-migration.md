# Flag Categorization for CLI Redesign

This document categorizes existing jgo flags for the command-based CLI redesign.

## Legend
- **Keep** = Retain as global flag (applies to all commands)
- **Command** = Remove flag, becomes a subcommand
- **Move** = Move from global to specific subcommand(s)
- **Retire** = Can be removed (deprecated, replaced, or jgo2-only)

---

## Flags from jgo 1.x (MUST keep for backwards compatibility)

| Flag | Category | Notes |
|------|----------|-------|
| `-v, --verbose` | **Keep** | Global flag - applies to all commands |
| `-q, --quiet` | **Keep** | Global flag - applies to all commands |
| `-u, --update-cache` | **Keep** → Rename to `--update` | Also becomes `jgo update` command for discoverability |
| `-U, --force-update` | **Retire** | Merged into `-u, --update` in jgo2 |
| `-m, --manage-dependencies` | **Keep** | Already default in jgo2, but keep for explicit control |
| `-r, --repository` | **Keep** | Global flag - can add repos for any command |
| `-a, --additional-jars` | **Keep** → Rename | Already renamed to `--add-classpath` in jgo2 |
| `--additional-endpoints` | **Keep** | Deprecated but keep for backwards compat |
| `--ignore-jgorc` | **Keep** | Global flag - applies to configuration loading - deprecate in favor of `--ignore-config` |
| `--link-type` | **Keep** → Rename | Already renamed to `--link` in jgo2 |
| `--log-level` | **Retire** | Replaced by `-v/-vv/-vvv` in jgo2 |

---

## New jgo 2.0 Flags

### Environment & Caching
| Flag | Category | Notes |
|------|----------|-------|
| `--offline` | **Keep** | Global flag - work offline for any command |
| `--no-cache` | **Keep** | Global flag - skip cache for any command |
| `--cache-dir PATH` | **Keep** | Global flag - override cache location |
| `--repo-cache PATH` | **Keep** | Global flag - override Maven repo location |
| `--dry-run` | **Keep** | Global flag - useful for any command |

### Resolution & Dependencies
| Flag | Category | Notes |
|------|----------|-------|
| `--resolver {auto,python,mvn}` | **Keep** | Global flag - affects all dependency resolution |
| `--link {hard,soft,copy,auto}` | **Keep** | Global flag - affects environment building |
| `--no-managed` | **Keep** | Global flag - inverse of `-m`, affects resolution |
| `--main-class CLASS` | **Move** | ✅ Moved to `jgo run` only |
| `--add-classpath PATH` | **Move** | ✅ Moved to `jgo run` only |

### Information Commands (become subcommands)
| Flag | Category | New Command | Notes |
|------|----------|-------------|-------|
| `--list-versions` | **Command** | `jgo versions <coordinate>` | Query versions of artifact |
| `--print-classpath` | **Command** | `jgo info --classpath` | Show classpath info |
| `--print-java-info` | **Command** | `jgo info --java-version` | Show Java requirements |
| `--print-dependency-tree` | **Command** | `jgo tree` | Show dependency tree |
| `--print-dependency-list` | **Command** | `jgo list` | List dependencies flat |

### Project/Spec File Commands (become subcommands)
| Flag | Category | New Command | Notes |
|------|----------|-------------|-------|
| `--init ENDPOINT` | **Command** | `jgo init [endpoint]` | Create jgo.toml |
| `--list-entrypoints` | **Command** | `jgo info --entrypoints` | Show entrypoints in jgo.toml |
| `-f, --file FILE` | **Keep** | | Global flag - specify jgo.toml path |
| `--entrypoint NAME` | **Move** | Move to `jgo run` only | Run specific entrypoint |

### Java Version Management
| Flag | Category | Notes |
|------|----------|-------|
| `--java-version VERSION` | **Keep** | Global flag - affects Java selection for all commands |
| `--java-vendor VENDOR` | **Keep** | Global flag - affects Java selection |
| `--system-java` | **Keep** | Global flag - use system Java instead of auto mode (default) |

---

## Migration Strategy

### Phase 1: Add Subcommands (Keep All Flags)
- Add `run`, `init`, `info`, `list`, `tree`, `versions` commands
- All existing flags still work at global level
- Commands are additive, nothing breaks
- **Status**: In progress

### Phase 2: Move Command-Specific Flags
Move these flags from global to specific subcommands:
- ✅ `--main-class` → `jgo run --main-class` (COMPLETED)
- ✅ `--add-classpath` → `jgo run --add-classpath` (COMPLETED)
- ✅ `--entrypoint` → `jgo run --entrypoint` (COMPLETED)
- **Target**: Before 2.0.0 release

### Phase 3: Deprecation Warnings (Post 2.0.0)
Add warnings for:
- Using information flags instead of commands:
  - `--print-classpath` → "Use 'jgo info --classpath' instead"
  - `--list-versions` → "Use 'jgo versions <coordinate>' instead"
  - etc.
- Keep flags working, just warn
- **Target**: 2.1.0

### Phase 4: Remove Deprecated Flags (Far Future)
After sufficient deprecation period (6-12 months):
- Remove information flags (replaced by commands)
- Remove `--additional-endpoints` (use `+` syntax)
- Remove `--log-level` (use `-v/-vv/-vvv`)
- **Target**: 3.0.0 or later

---

## Command Structure Summary

### Global Flags (Apply to all commands)
```bash
jgo [GLOBAL_OPTIONS] <command> [COMMAND_OPTIONS] [args]

Global Options:
  -v, --verbose           Verbose output (can be repeated)
  -q, --quiet            Suppress output
  -u, --update           Update cached environment
  -m, --managed          Use dependency management (default)
  --no-managed           Disable dependency management
  -r, --repository       Add Maven repository
  --ignore-jgorc         Ignore ~/.jgorc config
  --link {hard,soft,copy,auto}  Link strategy
  --resolver {auto,python,mvn}  Resolver to use
  --offline              Work offline
  --no-cache             Skip cache entirely
  --cache-dir PATH       Override cache directory
  --repo-cache PATH      Override Maven repository
  --dry-run              Show what would be done
  -f, --file FILE        Use specific jgo.toml
  --java-version VERSION Force Java version
  --java-vendor VENDOR   Prefer Java vendor
  --system-java          Use system Java (default: auto mode)
  
  # Deprecated but kept for backwards compat
  --additional-endpoints Add endpoints (use + syntax instead)
  -a, --additional-jars  Add JARs (use --add-classpath instead)
  --link-type            Old name for --link
```

### Commands with Specific Options

```bash
jgo run [OPTIONS] [endpoint] [-- JVM_ARGS] [-- APP_ARGS]
  Options:
    --main-class CLASS     Override main class
    --entrypoint NAME      Run specific entrypoint from jgo.toml
    --add-classpath PATH   Append to classpath

jgo init [OPTIONS] [endpoint]
  Options:
    --name NAME           Project name
    --interactive         Interactive mode

jgo add [OPTIONS] <coordinate> [<coordinate> ...]
  Options:
    --entrypoint NAME     Add to specific entrypoint
    --no-sync            Don't sync after adding

jgo remove [OPTIONS] <coordinate> [<coordinate> ...]
  Options:
    --entrypoint NAME     Remove from specific entrypoint
    --no-sync            Don't sync after removing

jgo sync [OPTIONS]
  Options:
    --update             Update versions
    --force              Force rebuild

jgo lock [OPTIONS]
  Options:
    --update             Update lock file
    --check              Verify lock file is current

jgo list [OPTIONS]
  Options:
    --tree               Show as tree (alias for 'jgo tree')
    --format {simple,json,table}

jgo tree [OPTIONS]
  Options:
    --depth N            Limit tree depth
    --format {simple,json}

jgo info [OPTIONS] [coordinate]
  Options:
    --classpath          Show classpath
    --java-version       Show Java requirements
    --entrypoints        Show available entrypoints
    --all                Show all information

jgo versions [OPTIONS] <coordinate>
  Options:
    --limit N            Limit results
    --filter PATTERN     Filter versions

jgo search [OPTIONS] <query>
  Options:
    --limit N            Limit results
    --repository NAME    Search specific repository

jgo config [OPTIONS] [key] [value]
  Options:
    --global             Modify global config
    --local              Modify project config
    --list               List all values
    --unset KEY          Remove value

jgo update [OPTIONS]
  (Alias for: jgo sync --update)

jgo version
jgo help [command]
```

---

## Backwards Compatibility Examples

All of these will continue to work:

```bash
# jgo 1.x style
jgo -v -u org.python:jython-standalone
jgo -m org.scijava:scijava-common:2.96.0
jgo --additional-jars mylib.jar org.example:myapp

# jgo 2.0 current style (no commands)
jgo --print-classpath org.python:jython-standalone
jgo --list-versions org.scijava:scijava-common
jgo --init org.python:jython-standalone

# jgo 2.0 with commands (new style)
jgo info --classpath org.python:jython-standalone
jgo versions org.scijava:scijava-common
jgo init org.python:jython-standalone

# Auto-detection of endpoints (always works)
jgo org.python:jython-standalone    # Auto-injects 'run'
jgo run org.python:jython-standalone # Explicit command
```

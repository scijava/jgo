# jgo 1.x → 2.0 Migration Guide

This document helps users migrate from jgo 1.x to jgo 2.0.

## Backward Compatibility

jgo 2.0 maintains backward compatibility with jgo 1.x through:

1. **Deprecated Python API** - All old functions still work but show deprecation warnings
2. **Deprecated CLI flags** - Old flags are aliased to new ones with deprecation warnings
3. **Exported classes/exceptions** - Old classes like `Endpoint` are still available

## Python API Changes

### Old API (Deprecated but Still Works)

```python
import jgo

# Old approach - shows deprecation warning
jgo.main(['org.scijava:parsington'])
jgo.resolve_dependencies('org.scijava:parsington', cache_dir='/tmp')
jgo.main_from_endpoint('org.scijava:parsington')

# Old classes still available
from jgo import Endpoint, NoMainClassInManifest
```

### New API (Recommended)

```python
import jgo

# New approach - clean API
jgo.run('org.scijava:parsington', app_args=['--help'])
env = jgo.build('org.scijava:parsington')
components = jgo.resolve('org.scijava:parsington')
```

## CLI Flag Changes

### Non-Deprecated Aliases (Keep Using These!)

These short flags are **permanent aliases** and will not be removed:

| Short | Long | Description |
|-------|------|-------------|
| `-v` | `--verbose` | Verbose output |
| `-q` | `--quiet` | Quiet mode |
| `-u` | `--update` | Update cache |
| `-m` | `--managed` | Managed dependencies |
| `-r` | `--repository` | Add repository |

**Note:** In jgo 1.x, `-u` and `-U` were different. In jgo 2.0, both map to `--update` which checks remote repositories (the old `-U` behavior). For the old `-u` behavior (rebuild without checking remote), use `--update --offline`.

### Deprecated Flags (Migrate Away From These)

| Old Flag | New Replacement | Notes |
|----------|-----------------|-------|
| `-U`, `--force-update` | `-u`, `--update` | Both now check remote repos |
| `-a JAR`, `--additional-jars JAR` | `--classpath-append PATH` | New name is more general (handles directories too) |
| `--additional-endpoints EP` | Use `+` syntax | See examples below |
| `--link-type TYPE` | `--link TYPE` | Just renamed |
| `--log-level LEVEL` | `-v`, `-vv`, `-vvv` | Use verbose flags instead |

### New Features

| Flag | Description |
|------|-------------|
| `--classpath-append PATH` | Append JARs, directories, or other classpath elements |
| `--ignore-jgorc` | Ignore ~/.jgorc configuration file |
| `--offline` | Work offline (don't download) |
| `--no-cache` | Skip cache entirely |
| `--resolver {auto,pure,maven}` | Choose dependency resolver |
| `--java-version VERSION` | Force specific Java version |
| `--java-vendor VENDOR` | Prefer specific Java vendor |
| `--print-classpath` | Print classpath and exit |
| `-f FILE` | Use specific jgo.toml file |

## Common Migration Patterns

### Multiple Dependencies

**Old:**
```bash
jgo --additional-endpoints org.slf4j:slf4j-simple org.scijava:parsington
```

**New:**
```bash
jgo org.scijava:parsington+org.slf4j:slf4j-simple
```

### Additional JARs

**Old:**
```bash
jgo -a /path/to/lib.jar -a /path/to/other.jar org.scijava:parsington
```

**New:**
```bash
jgo --classpath-append /path/to/lib.jar --classpath-append /path/to/other.jar org.scijava:parsington
```

### Update Cache

**Old:**
```bash
jgo -u org.scijava:parsington   # Rebuild from local
jgo -U org.scijava:parsington   # Check remote and rebuild
```

**New:**
```bash
jgo -u --offline org.scijava:parsington   # Rebuild from local (old -u)
jgo -u org.scijava:parsington              # Check remote and rebuild (old -U)
```

### Verbose Output

**Old:**
```bash
jgo --log-level DEBUG org.scijava:parsington
```

**New:**
```bash
jgo -vv org.scijava:parsington   # -v (INFO), -vv (DEBUG), -vvv (TRACE)
```

## Configuration Changes

### Cache Directory

**Old behavior:**
- Default: `~/.jgo`
- Override: `JGO_CACHE_DIR` environment variable

**New behavior:**
- Default: `~/.cache/jgo` (Linux/Mac), `%LOCALAPPDATA%\jgo` (Windows)
- Override: `--cache-dir PATH` flag or `JGO_CACHE_DIR` environment variable

**Note:** Old cache directories are not migrated automatically. jgo 2.0 will create a new cache.

### ~/.jgorc

The `~/.jgorc` configuration file format remains the same. To ignore it, use `--ignore-jgorc`.

## Breaking Changes (Minimal)

1. **Cache location changed** - Old cache at `~/.jgo` is not migrated
2. **`-u` now checks remote** - Old `-u` behavior now requires `--update --offline`
3. **Argument order for `--additional-endpoints`** - Use `+` syntax instead

## Deprecation Timeline

- **jgo 2.0**: Deprecated APIs work with warnings
- **jgo 3.0** (future): Deprecated APIs will be removed

To see deprecation warnings:
```bash
python -W default::DeprecationWarning -m jgo ...
```

## Questions?

For issues or questions, see: https://github.com/scijava/jgo/issues

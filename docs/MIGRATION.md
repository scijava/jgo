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
| `-a JAR`, `--additional-jars JAR` | `--add-classpath PATH` | New name is more general (handles directories too) |
| `--additional-endpoints EP` | Use `+` syntax | See examples below |
| `--link-type TYPE` | `--link TYPE` | Just renamed |
| `--log-level LEVEL` | `-v`, `-vv`, `-vvv` | Use verbose flags instead |

### New Features

| Flag | Description |
|------|-------------|
| `--add-classpath PATH` | Append JARs, directories, or other classpath elements |
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
jgo --add-classpath /path/to/lib.jar --add-classpath /path/to/other.jar org.scijava:parsington
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

### Config File

The configuration file format remains the same (INI format with `[settings]`, `[repositories]`, and `[shortcuts]` sections).

**New in jgo 2.0:** Config files can now be placed at:
1. `~/.config/jgo/config` (XDG Base Directory standard - recommended)
2. `~/.jgorc` (legacy location, still supported for backward compatibility)

jgo will check both locations, preferring the XDG location if it exists. Your existing `~/.jgorc` file will continue to work without any changes. To ignore config files, use `--ignore-jgorc`.

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

## New Features in 2.0

### jgo.toml Project Files

jgo 2.0 introduces reproducible project environments:

```toml
# jgo.toml
[environment]
name = "my-project"

[dependencies]
coordinates = ["net.imagej:imagej:2.15.0"]

[entrypoints]
main = "net.imagej.Main"
default = "main"

[settings]
cache_dir = ".jgo"  # Local environment
```

```bash
# Run from current directory
jgo

# Creates .jgo/ directory (like .venv for Python)
# Generates jgo.lock.toml with locked versions
```

**Benefits:**
- Reproducible environments (lock files)
- Version control friendly (commit jgo.toml + jgo.lock.toml)
- Multiple entry points per project
- Project-local or centralized cache

### Automatic Java Management

```bash
# Automatically downloads Java if needed!
jgo net.imagej:imagej
```

No need to pre-install Java - jgo detects requirements from bytecode and downloads the right version using [cjdk](https://github.com/cachedjdk/cjdk).

### Three-Layer Architecture

For power users, jgo 2.0 provides three independently useful layers:

```python
from jgo.maven import MavenContext, SimpleResolver
from jgo.env import EnvironmentBuilder
from jgo.exec import JavaRunner

# Layer 1: Maven resolution (no Maven required!)
maven = MavenContext(resolver=SimpleResolver())
component = maven.project("org.python", "jython-standalone").at_version("2.7.3")

# Layer 2: Environment materialization
builder = EnvironmentBuilder(context=maven)
env = builder.from_components([component])

# Layer 3: Execution
runner = JavaRunner()
runner.run(env)
```

Each layer is independently useful:
- Use Maven layer for dependency analysis
- Use Environment layer for IDE classpath generation
- Use Execution layer for custom Java launching

See [architecture.md](architecture.md) for details.

### Pure Python Resolver

jgo 2.0 includes a pure-Python Maven resolver:

```bash
# No Maven installation required!
jgo --resolver pure org.python:jython-standalone
```

Falls back to system `mvn` command only when needed for edge cases.

## Practical Migration Example

### Before (jgo 1.x)

```bash
# Old script
jgo -v -u \
  --additional-endpoints org.slf4j:slf4j-simple \
  -a /path/to/custom.jar \
  org.example:myapp:1.0.0 \
  --app-flag value
```

### After (jgo 2.0)

**Option 1: Direct CLI migration**
```bash
jgo -v -u \
  --add-classpath /path/to/custom.jar \
  org.example:myapp:1.0.0+org.slf4j:slf4j-simple \
  -- -- --app-flag value
```

**Option 2: Use jgo.toml (recommended)**
```toml
# jgo.toml
[environment]
name = "myapp"

[dependencies]
coordinates = [
    "org.example:myapp:1.0.0",
    "org.slf4j:slf4j-simple",
]

[entrypoints]
default = "org.example.Main"

[settings]
classpath_append = ["/path/to/custom.jar"]
```

```bash
# Much simpler!
jgo -v -- -- --app-flag value
```

## Testing Your Migration

1. **Run with deprecation warnings visible:**
   ```bash
   python -W default::DeprecationWarning -m jgo your-endpoint
   ```

2. **Test backward compatibility:**
   ```python
   # Your old code should still work
   import jgo
   jgo.main(['org.python:jython-standalone'])  # Shows warning but works
   ```

3. **Gradually migrate to new API:**
   ```python
   import jgo

   # New style
   jgo.run('org.python:jython-standalone')  # Recommended
   ```

## Getting Help

- **User Guide**: See [user-guide.md](user-guide.md) for comprehensive documentation
- **Architecture**: See [architecture.md](architecture.md) to understand the new design
- **GitHub Issues**: https://github.com/apposed/jgo/issues
- **API Reference**: Use `help(jgo)` in Python for detailed documentation

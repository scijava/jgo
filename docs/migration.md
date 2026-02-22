# Migrating from jgo 1.x

This guide covers upgrading from jgo 1.x to 2.0. jgo 2.0 maintains backward compatibility -- your existing scripts and code will continue to work, with deprecation warnings guiding you toward the new APIs.

## Backward compatibility

jgo 2.0 preserves backward compatibility through:

1. **Deprecated Python API** -- All old functions still work but emit deprecation warnings.
2. **Deprecated CLI flags** -- Old flags are aliased to new ones with warnings.
3. **Exported classes/exceptions** -- Old classes like `Endpoint` remain importable.

Deprecated APIs will be removed in jgo 3.0.

## Python API changes

### Old API (deprecated)

```python
import jgo

# These still work but show deprecation warnings
jgo.main(["org.scijava:parsington"])
jgo.resolve_dependencies("org.scijava:parsington", cache_dir="/tmp")
jgo.main_from_endpoint("org.scijava:parsington")
```

### New API

```python
import jgo

# Simple high-level functions
jgo.run("org.scijava:parsington", app_args=["--help"])
env = jgo.build("org.scijava:parsington")
components = jgo.resolve("org.scijava:parsington")
```

### Migration table

| Old (1.x) | New (2.0) |
|:-----------|:----------|
| `jgo.main(argv)` | `jgo.run(endpoint, app_args=...)` |
| `jgo.main_from_endpoint(ep, ...)` | `jgo.run(endpoint, ...)` |
| `jgo.resolve_dependencies(ep, ...)` | `jgo.resolve(endpoint, ...)` |
| `from jgo.jgo import resolve_dependencies` | `import jgo; jgo.resolve(...)` |
| `from jgo.util import main_from_endpoint` | `import jgo; jgo.run(...)` |

### Advanced: layered API

jgo 1.x had a single monolithic module. jgo 2.0 provides three independently useful layers:

```python
from jgo.maven import MavenContext, PythonResolver
from jgo.env import EnvironmentBuilder
from jgo.exec import JavaRunner

# Layer 1: Maven resolution (no Maven installation needed!)
maven = MavenContext(resolver=PythonResolver())
component = maven.project("org.python", "jython-standalone").at_version("2.7.3")

# Layer 2: Environment materialization
builder = EnvironmentBuilder(context=maven)
env = builder.from_endpoint("org.python:jython-standalone:2.7.3")

# Layer 3: Execution
runner = JavaRunner()
runner.run(env)
```

See {doc}`python-api` for full details.

## CLI changes

### Commands replace flags

jgo 2.0 uses a command-based CLI. The old endpoint-first syntax still works:

```bash
# Both work -- the first auto-detects the 'run' command
jgo org.python:jython-standalone
jgo run org.python:jython-standalone
```

New commands for project management and inspection:

```bash
jgo init org.python:jython-standalone    # Create jgo.toml
jgo add org.slf4j:slf4j-simple           # Add dependency
jgo remove org.slf4j:slf4j-simple        # Remove dependency
jgo list                                  # List dependencies
jgo tree                                  # Show dependency tree
jgo info classpath ENDPOINT              # Show classpath
jgo search apache commons                # Search Maven Central
jgo config shortcut imagej net.imagej:imagej  # Manage shortcuts
```

### Permanent short flags

These short flags are permanent aliases and will not be removed:

| Short | Long | Description |
|:------|:-----|:------------|
| `-v` | `--verbose` | Verbose output |
| `-q` | `--quiet` | Quiet mode |
| `-u` | `--update` | Update cache |
| `-r` | `--repository` | Add repository |
| `-f` | `--file` | Use specific jgo.toml |

### Deprecated flags

| Old flag | New replacement | Notes |
|:---------|:----------------|:------|
| `-U`, `--force-update` | `-u`, `--update` | Both now check remote repos |
| `-a`, `--additional-jars` | `--add-classpath` | Handles JARs and directories |
| `--additional-endpoints` | `+` syntax | e.g., `g:a+g2:a2` |
| `--link-type` | `--links` | Matches config field name |
| `--log-level` | `-v`/`-vv`/`-vvv` | Use verbose flags |
| `--print-classpath` | `jgo info classpath` | Now a subcommand |
| `--print-dependency-tree` | `jgo tree` | Now a subcommand |
| `--print-dependency-list` | `jgo list` | Now a subcommand |
| `--list-versions` | `jgo info versions` | Now a subcommand |

### Update behavior change

In jgo 1.x, `-u` and `-U` were different. In jgo 2.0:

```bash
# jgo 1.x
jgo -u endpoint    # Rebuild from local cache
jgo -U endpoint    # Check remote repositories and rebuild

# jgo 2.0
jgo -u --offline endpoint   # Rebuild from local (old -u behavior)
jgo -u endpoint              # Check remote and rebuild (old -U behavior)
```

## Configuration changes

### Cache directory

| | Location |
|:--|:---------|
| **jgo 1.x** | `~/.jgo` |
| **jgo 2.0** | `~/.cache/jgo` (Linux/macOS), `%LOCALAPPDATA%\jgo` (Windows) |

Old cache directories are not migrated automatically. jgo 2.0 creates a fresh cache.

### Settings file

The INI format is unchanged. jgo 2.0 adds a new preferred location:

1. `~/.config/jgo.conf` (XDG standard -- new, recommended)
2. `~/.jgorc` (legacy -- still works)

Your existing `~/.jgorc` will continue to work. Use `--ignore-config` to skip the settings file.

## Breaking changes

These are the only behaviors that differ from 1.x in a non-backward-compatible way:

1. **Cache location** -- `~/.jgo` is no longer used by default. Override with `--cache-dir ~/.jgo` or `JGO_CACHE_DIR=~/.jgo` if needed.
2. **`-u` checks remote** -- The old `-u` (local-only rebuild) now requires `--update --offline`.

## New features in 2.0

### jgo.toml project files

Reproducible environments with lock files:

```toml
[environment]
name = "my-project"

[dependencies]
coordinates = ["net.imagej:imagej:2.15.0"]

[entrypoints]
default = "net.imagej.Main"
```

```bash
jgo           # Run from jgo.toml
jgo sync      # Rebuild environment
jgo update    # Update dependencies
```

See {doc}`project-mode` for details.

### Automatic Java management

No need to pre-install Java. jgo detects bytecode requirements and downloads the correct version:

```bash
jgo net.imagej:imagej    # Downloads Java 17 automatically
```

### Pure Python resolver

Resolve Maven dependencies without a Maven installation:

```bash
jgo --resolver python org.python:jython-standalone
```

### Three-layer architecture

Each layer is independently useful for dependency analysis, IDE integration, or custom launchers. See {doc}`architecture` for details.

## Testing your migration

Run with deprecation warnings visible:

```bash
python -W default::DeprecationWarning -m jgo org.python:jython-standalone
```

Gradually replace deprecated calls:

```python
# Before
jgo.main_from_endpoint("org.python:jython-standalone")

# After
jgo.run("org.python:jython-standalone")
```

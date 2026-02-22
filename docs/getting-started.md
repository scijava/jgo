# Getting Started

## Installation

::::{tab-set}

:::{tab-item} uv
```bash
uv tool install jgo
```
:::

:::{tab-item} pip
```bash
pip install jgo
```
:::

:::{tab-item} conda
```bash
conda install -c conda-forge jgo
```
:::

:::{tab-item} From source
```bash
git clone https://github.com/apposed/jgo
uv tool install --with-editable jgo jgo
```
Changes to the source will be immediately reflected when running `jgo`.
:::

::::

### Prerequisites

- **Python 3.9** or later
- **No Java required!** jgo downloads it on demand via [cjdk](https://github.com/cachedjdk/cjdk).

### As a library dependency

If you want to use jgo from your own Python code:

```bash
uv add jgo
```
or:
```bash
pip install jgo
```

## Quick Start

### Run a Java program

Launch Java programs directly from Maven coordinates:

```bash
# Run Jython REPL (latest release version)
jgo org.python:jython-standalone

# Run a specific version
jgo org.python:jython-standalone:2.7.3

# Pass arguments to the Java program
jgo org.python:jython-standalone -- -- script.py --verbose
```

The `--` separators split arguments into three groups: jgo options, JVM arguments, and application arguments. See {doc}`cli` for details.

### Inspect dependencies

```bash
# Show dependency tree
jgo tree org.python:jython-standalone

# Show flat dependency list
jgo list org.python:jython-standalone

# Print the classpath
jgo info classpath org.python:jython-standalone
```

### Create a project environment

For reproducible environments, use `jgo.toml`:

```bash
# Initialize a project with a dependency
jgo init org.python:jython-standalone:2.7.3

# Add more dependencies
jgo add org.slf4j:slf4j-simple

# Run the default entrypoint
jgo
```

This creates a `jgo.toml` file and a `.jgo/` directory (like Python's `.venv/`). See {doc}`project-mode` for details.

### Use from Python

```python
import jgo

# Run a Java application
jgo.run("org.python:jython-standalone:2.7.3", app_args=["script.py"])

# Build an environment without running
env = jgo.build("org.python:jython-standalone")
print(env.classpath)  # List of JAR paths

# Resolve dependencies
components = jgo.resolve("org.python:jython-standalone")
for comp in components:
    print(f"{comp.groupId}:{comp.artifactId}:{comp.version}")
```

See {doc}`python-api` for the full API.

## Endpoint format

Endpoints specify what to run. The general format is:

```
groupId:artifactId[:version][:classifier][@mainClass]
```

**Examples:**

| Endpoint | Meaning |
|:---------|:--------|
| `org.python:jython-standalone` | Latest release, auto-detect main class |
| `org.python:jython-standalone:2.7.3` | Specific version |
| `org.scijava:parsington@Parser` | Auto-complete main class name |
| `g:a+g2:a2` | Multiple artifacts on the classpath |
| `g:a+g2:a2@com.example.Main` | Multiple artifacts with explicit main class |

The `@` separator specifies the main class. Simple names (without dots) are auto-completed by scanning JAR manifests and class files. Fully qualified names are used as-is.

Use `+` to combine multiple artifacts on the classpath:

```bash
jgo org.scijava:scijava-common+org.scijava:scripting-jython@ScriptREPL
```

### Coordinate modifiers

Coordinates support optional suffixes for advanced control:

| Suffix | Meaning |
|:-------|:--------|
| `(c)` | Force this artifact onto the classpath |
| `(m)` | Force this artifact onto the module-path |
| `!` | Disable dependency management (BOM import) for this coordinate |

```bash
# Force a JAR onto the module-path
jgo org.lwjgl:lwjgl:3.3.1(m)

# Disable managed dependency resolution for one coordinate
jgo org.scijava:scijava-common!
```

These are rarely needed -- jgo's defaults handle most cases correctly. See {doc}`dependency-management` for details on the `!` flag.

:::{tip}
Use `jgo --dry-run run <endpoint>` to see what command would be executed without actually running it.
:::

## Next steps

- {doc}`cli` -- Full CLI command reference
- {doc}`project-mode` -- Working with `jgo.toml` environments
- {doc}`python-api` -- Using jgo from Python code
- {doc}`configuration` -- Configuring repositories, shortcuts, and settings

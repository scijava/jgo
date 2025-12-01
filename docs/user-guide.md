# jgo 2.0 User Guide

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Reference](#cli-reference)
- [Project Mode with jgo.toml](#project-mode-with-jgotoml)
- [Python API](#python-api)
- [Configuration](#configuration)
- [Common Recipes](#common-recipes)

## Installation

### Basic Installation

Install jgo using pip or conda:

```bash
# Using pip
pip install jgo

# Using conda
conda install -c conda-forge jgo
```

This provides core jgo functionality and requires Java to be pre-installed on your system.

### Full Installation with Automatic Java Management

For zero-configuration execution with automatic Java download:

```bash
pip install jgo[cjdk]
```

This adds [cjdk](https://github.com/cachedjdk/cjdk) integration, allowing jgo to automatically download the correct Java version for each program.

### Prerequisites

**Minimal installation:**
- Python 3.9 or later
- Java 8 or later (pre-installed)
- Maven (optional, for `--resolver maven` mode)

**Full installation:**
- Python 3.9 or later
- No Java required! (cjdk downloads it automatically)

## Quick Start

### Running Java Programs

Launch Java programs directly from Maven coordinates:

```bash
# Run Jython REPL (latest version)
jgo org.python:jython-standalone

# Run specific version
jgo org.python:jython-standalone:2.7.3

# Run with arguments
jgo org.python:jython-standalone -- -- script.py --verbose
```

### Endpoint Format

Endpoints specify what to run:

```
groupId:artifactId[:version][:classifier][:mainClass]
```

**Examples:**
- `org.python:jython-standalone` - Auto-detect version and main class
- `org.python:jython-standalone:2.7.3` - Specific version
- `org.scijava:parsington:@Parser` - Auto-complete main class
- `net.imagej:imagej+org.scijava:scripting-jython` - Multiple artifacts (use `+`)

### Main Class Auto-Completion

Use `@` prefix for partial main class matching:

```bash
# Finds org.scijava.script.ScriptREPL
jgo org.scijava:scijava-common:@ScriptREPL
```

## CLI Reference

### Basic Usage

```
jgo [OPTIONS] <endpoint> [-- JVM_ARGS] [-- APP_ARGS]
```

### Common Flags

**Execution Control:**
- `-v, --verbose` - Verbose output (use `-vv` for debug, `-vvv` for trace)
- `-q, --quiet` - Suppress all output
- `-u, --update` - Update cached environment (checks remote repositories)
- `--offline` - Work offline (don't download)
- `--no-cache` - Skip cache entirely, always rebuild

**Environment Configuration:**
- `--cache-dir PATH` - Override cache directory (default: `~/.cache/jgo`)
- `--link {hard,soft,copy,auto}` - How to link JARs (default: auto)
- `--resolver {auto,pure,maven}` - Dependency resolver (default: auto)
  - `pure` - Pure Python, no Maven required
  - `maven` - Shell out to `mvn` command
  - `auto` - Use pure, fallback to maven if needed

**Maven Configuration:**
- `-r NAME=URL, --repository NAME=URL` - Add Maven repository
- `-m, --managed` - Use dependency management (import scope)
- `--ignore-jgorc` - Ignore `~/.jgorc` configuration

**Java Version Control:**
- `--java-version VERSION` - Force specific Java version
- `--java-vendor VENDOR` - Prefer specific vendor (adoptium, zulu, etc.)
- `--java-source {cjdk,system}` - Java selection strategy

**Output Options:**
- `--print-classpath` - Print classpath and exit
- `--print-dependency-tree` - Print dependency tree and exit
- `--print-java-info` - Print detected Java version requirements and exit
- `--main-class CLASS` - Override main class detection

**Project Mode:**
- `-f FILE, --file FILE` - Use specific jgo.toml file
- `--entrypoint NAME` - Run specific entry point from jgo.toml

### Examples

```bash
# Run with verbose output
jgo -v org.python:jython-standalone

# Force update from remote repos
jgo -u org.python:jython-standalone

# Use specific Java version
jgo --java-version 17 net.imagej:imagej

# Pass JVM arguments
jgo org.python:jython-standalone -- -Xmx4G -- script.py

# Print classpath without running
jgo --print-classpath org.python:jython-standalone

# Add custom repository
jgo -r scijava=https://maven.scijava.org/content/groups/public org.scijava:parsington

# Work offline with cached dependencies
jgo --offline org.python:jython-standalone

# Append additional JARs to classpath
jgo --add-classpath /path/to/lib.jar org.scijava:parsington
```

## Project Mode with jgo.toml

jgo 2.0 supports reproducible project environments using `jgo.toml` files (similar to `package.json` or `pyproject.toml`).

### Creating a jgo.toml

Create a `jgo.toml` file in your project directory:

```toml
# jgo.toml - Define a reproducible Java environment

[environment]
name = "my-java-app"
description = "My Java application with dependencies"

[java]
version = "17"           # Or ">=11", "11-17", or "auto" (default)
vendor = "adoptium"      # Optional: adoptium, zulu, etc.

[repositories]
scijava = "https://maven.scijava.org/content/groups/public"

[dependencies]
coordinates = [
    "net.imagej:imagej:2.15.0",
    "org.scijava:scripting-jython:1.0.0",
]

# Maven-style exclusions (groupId:artifactId only)
[dependencies.exclusions]
"net.imagej:imagej" = ["org.scijava:scijava-common"]

[entrypoints]
imagej = "net.imagej.Main"
repl = "org.scijava.script.ScriptREPL"
default = "imagej"

[settings]
links = "hard"
cache_dir = ".jgo"  # Local environment (like .venv)
```

### Using jgo.toml

```bash
# Run from current directory (uses default entrypoint)
jgo

# Run specific entrypoint
jgo --entrypoint repl

# Use specific file
jgo -f path/to/environment.toml

# Initial run creates .jgo/ directory with:
# - jgo.toml (your spec, copied)
# - jgo.lock.toml (locked versions)
# - jars/ (materialized JARs)
# - manifest.json (metadata)
```

### Lock Files

jgo automatically generates `jgo.lock.toml` with exact versions:

```toml
# jgo.lock.toml - Auto-generated, do not edit

[metadata]
generated = "2025-01-15T10:30:00Z"
jgo_version = "2.0.0"

[environment]
name = "my-java-app"
min_java_version = 17

[[dependencies]]
groupId = "net.imagej"
artifactId = "imagej"
version = "2.15.0"
packaging = "jar"
sha256 = "abc123..."
```

### Version Control

```bash
# Add to git
git add jgo.toml jgo.lock.toml

# Ignore build environment
echo ".jgo/" >> .gitignore
```

## Python API

### High-Level API

```python
import jgo

# Run a Java program
jgo.run("org.python:jython-standalone:2.7.3", app_args=["script.py"])

# Build environment without running
env = jgo.build("org.python:jython-standalone:2.7.3")
print(env.classpath)  # List of JAR paths
print(env.main_class)  # Detected main class

# Resolve dependencies
components = jgo.resolve("org.python:jython-standalone:2.7.3")
for comp in components:
    print(f"{comp.groupId}:{comp.artifactId}:{comp.version}")
```

### Layered API

For fine-grained control, use the three-layer architecture:

```python
from jgo.maven import MavenContext, SimpleResolver
from jgo.env import EnvironmentBuilder, LinkStrategy
from jgo.exec import JavaRunner, JVMConfig

# Layer 1: Maven - Dependency resolution
maven = MavenContext(
    resolver=SimpleResolver(),  # Pure Python, no mvn needed
    remote_repos={
        "central": "https://repo.maven.apache.org/maven2",
        "scijava": "https://maven.scijava.org/content/groups/public"
    }
)

# Resolve a component
project = maven.project("org.python", "jython-standalone")
component = project.at_version("2.7.3")
model = component.model()

# Layer 2: Environment - Materialize JARs
builder = EnvironmentBuilder(
    maven_context=maven,
    link_strategy=LinkStrategy.HARD
)
environment = builder.from_endpoint("org.python:jython-standalone:2.7.3")

# Layer 3: Execution - Run Java
jvm_config = JVMConfig(max_heap="2G")
runner = JavaRunner(jvm_config=jvm_config)
result = runner.run(environment, app_args=["script.py"])
```

### Using jgo.toml from Python

```python
from jgo.env import EnvironmentBuilder, EnvironmentSpec
from jgo.maven import MavenContext

# Load spec from file
spec = EnvironmentSpec.load("jgo.toml")

# Build environment
maven = MavenContext()
builder = EnvironmentBuilder(maven_context=maven)
environment = builder.from_spec(spec)

# Run specific entrypoint
from jgo.exec import JavaRunner
runner = JavaRunner()
main_class = spec.get_main_class("repl")  # Get 'repl' entrypoint
runner.run(environment, main_class=main_class)
```

## Configuration

### ~/.jgorc

Global configuration file in INI format:

```ini
[settings]
# Cache directory (overridden by --cache-dir or JGO_CACHE_DIR)
cacheDir = /custom/path/.jgo

# Maven repository cache
m2Repo = ~/.m2/repository

# Link strategy: hard, soft, copy, or auto
links = hard

[repositories]
# Additional Maven repositories
scijava.public = https://maven.scijava.org/content/groups/public
myrepo = https://repo.example.com/maven2

[shortcuts]
# Command shortcuts
imagej = net.imagej:imagej
fiji = sc.fiji:fiji:LATEST
jython = org.python:jython-standalone
```

### Environment Variables

- `JGO_CACHE_DIR` - Override cache directory
- `M2_REPO` - Override Maven repository location
- `JAVA_HOME` - Java installation (when using system Java)

### Precedence

Configuration is merged with this precedence (highest to lowest):

1. Command-line flags (`--cache-dir`, etc.)
2. Environment variables (`JGO_CACHE_DIR`)
3. jgo.toml settings (in project mode)
4. ~/.jgorc configuration
5. Built-in defaults

## Common Recipes

### Running ImageJ with Fiji Plugins

```bash
# Add scijava repo to ~/.jgorc first
jgo sc.fiji:fiji
```

### Running with Custom JVM Options

```bash
# Increase heap, enable assertions
jgo org.example:myapp -- -Xmx8G -ea -- --app-flag
```

### Building Environment for IDE

```bash
# Print classpath for IntelliJ/Eclipse
jgo --print-classpath org.python:jython-standalone > classpath.txt
```

### Combining Multiple Artifacts

```bash
# Run with both ImageJ and Python scripting
jgo net.imagej:imagej+org.scijava:scripting-jython
```

### Testing SNAPSHOT Versions

```bash
# Force update to get latest SNAPSHOT
jgo -u org.example:mylib:1.0-SNAPSHOT
```

### Using in CI/CD

```bash
# Work offline with cached dependencies
jgo --offline --cache-dir /build/cache org.example:myapp
```

### Local Development with jgo.toml

```toml
# jgo.toml for your project
[environment]
name = "my-dev-env"

[dependencies]
coordinates = [
    "org.junit.jupiter:junit-jupiter:5.9.0",
    "org.mockito:mockito-core:5.0.0",
]

[entrypoints]
test = "org.junit.platform.console.ConsoleLauncher"
default = "test"

[settings]
cache_dir = ".jgo"  # Local to project
```

```bash
# Run tests
jgo -- -- --scan-classpath
```

### Zero-Configuration Execution

With cjdk installed:

```bash
# Java automatically downloaded if needed
pip install jgo[cjdk]
jgo net.imagej:imagej  # Downloads Java 17 automatically!
```

## Next Steps

- **Migration**: See [migration-guide.md](migration-guide.md) for upgrading from jgo 1.x
- **Architecture**: See [architecture.md](architecture.md) for understanding the three-layer design
- **API Reference**: Use `help(jgo)` in Python for detailed API documentation
- **Examples**: See `examples/` directory for sample code

## Getting Help

- **GitHub Issues**: https://github.com/scijava/jgo/issues
- **Documentation**: https://github.com/scijava/jgo
- **SciJava Forum**: https://forum.image.sc/tag/jgo

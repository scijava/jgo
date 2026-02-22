# Project Mode with jgo.toml

jgo supports reproducible project environments using `jgo.toml` files, similar to `package.json` (npm) or `pyproject.toml` (Python).

## Creating a project

### From an endpoint

```bash
jgo init org.python:jython-standalone:2.7.3
```

This creates a `jgo.toml` file with the dependency pre-filled.

### From scratch

```bash
jgo init
```

This creates a bare `jgo.toml` that you can edit manually.

### From a requirements file

```bash
jgo init -r requirements.txt
```

Where `requirements.txt` contains one coordinate per line (`#` for comments).

## jgo.toml specification

A complete `jgo.toml` example:

```toml
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

[entrypoints]
imagej = "net.imagej.Main"
repl = "org.scijava.script.ScriptREPL"
default = "imagej"

[settings]
links = "hard"
cache_dir = ".jgo"  # Local environment directory (like .venv)
```

### Sections

`[environment]`
: Project metadata. `name` is used in output and logging.

`[java]`
: Java version constraints. If omitted, jgo detects the minimum version from JAR bytecode.

`[repositories]`
: Additional Maven repositories beyond Maven Central.

`[dependencies]`
: Maven coordinates for the project. Each coordinate follows the standard `groupId:artifactId[:version[:classifier]]` format.

`[entrypoints]`
: Named main classes. The `default` key specifies which entrypoint `jgo run` uses when no `--entrypoint` is given.

`[settings]`
: Project-level settings. `cache_dir` controls where the environment is materialized.

## Managing dependencies

### Adding dependencies

```bash
# Add one or more coordinates
jgo add org.slf4j:slf4j-simple:2.0.9
jgo add org.scijava:scijava-common org.scijava:scripting-jython

# Add from a file
jgo add -r requirements.txt

# Add without syncing the environment
jgo add --no-sync org.example:mylib
```

By default, `jgo add` automatically runs `jgo sync` to rebuild the environment.

### Removing dependencies

```bash
jgo remove org.slf4j:slf4j-simple
```

### Updating dependencies

```bash
# Update all dependencies to latest versions within constraints
jgo update

# Rebuild even if cached
jgo update --force
```

## Running

```bash
# Run the default entrypoint
jgo

# Run a named entrypoint
jgo run --entrypoint repl

# Pass arguments
jgo run -- -- --app-flag value

# Use a different jgo.toml
jgo -f path/to/other.toml run
```

When jgo finds a `jgo.toml` in the current directory (or specified via `-f`), it uses that file's configuration for dependency resolution, Java version selection, and entrypoint detection.

## Lock files

jgo automatically generates `jgo.lock.toml` with exact resolved versions:

```toml
# jgo.lock.toml -- Auto-generated, do not edit

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

### Lock file commands

```bash
# Update the lock file (resolve versions) without building
jgo lock

# Check if the lock file is current
jgo lock --check
```

## Environment directory

The environment is materialized in the `cache_dir` (default: `.jgo/`):

```
.jgo/
├── jars/               # Linked or copied JAR files
├── jgo.toml            # Copy of the spec
└── jgo.lock.toml       # Locked dependency versions
```

### Syncing

```bash
# Resolve and build the environment
jgo sync

# Force rebuild
jgo sync --force
```

## Version control

Commit your spec and lock file. Ignore the environment directory:

```bash
# Track these
git add jgo.toml jgo.lock.toml

# Ignore the built environment
echo ".jgo/" >> .gitignore
```

When a collaborator clones the repo, `jgo sync` (or simply `jgo`) rebuilds the environment from the lock file.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

jgo is a Python tool for launching Java applications directly from Maven coordinates without manual installation. It resolves dependencies using Maven, caches them locally in `~/.jgo`, and executes Java code using the `java` and `mvn` command-line tools.

The tool serves two purposes:
1. A CLI tool (`jgo`) for running Java applications from the command line
2. A Python library for programmatically launching Java applications from Python code

## Development Commands

### Testing
```bash
# Run all tests
make test
# or
bin/test.sh

# Run specific test file
bin/test.sh tests/test_run.py

# Run specific test
bin/test.sh tests/test_run.py::test_name
```

### Linting and Formatting
```bash
# Run linters and auto-format code
make lint
# or
bin/lint.sh
```

This project uses:
- `ruff` for linting and formatting (configured in pyproject.toml)
- `validate-pyproject` for validating pyproject.toml

### Building Distribution
```bash
# Build distribution archives
make dist
# or
bin/dist.sh
```

### Cleaning
```bash
# Remove build artifacts
make clean
# or
bin/clean.sh
```

## Code Architecture

### Core Components

**src/jgo/jgo.py** - Main implementation containing:
- `Endpoint` class: Represents Maven coordinates (groupId:artifactId:version:classifier:mainClass)
- `resolve_dependencies()`: Generates a temporary Maven POM, resolves dependencies via `mvn`, and creates hard/soft links from `~/.m2/repository` to the jgo cache directory
- `run()`: Main entry point that parses arguments, reads `~/.jgorc` config, resolves dependencies, and launches Java
- `launch_java()`: Constructs and executes the java command with appropriate classpath

**src/jgo/util.py** - Utility functions:
- `add_jvm_args_as_necessary()`: Adds default JVM args like max heap size based on system memory
- `main_from_endpoint()`: Convenience wrapper for launching Java programs from Python code

**src/jgo/__init__.py** - Public API exports

**src/jgo/__main__.py** - CLI entry point

### Key Workflows

**Dependency Resolution Flow:**
1. Parse endpoint string (e.g., "org.python:jython-standalone" or "groupId:artifactId:version:mainClass")
2. Expand shortcuts from `~/.jgorc` config file
3. Generate workspace directory path: `~/.jgo/<groupId>/<artifactId>/<hash>/`
4. Check if workspace exists and is valid (has `buildSuccess` file)
5. If cache miss or force update: generate temporary POM, run `mvn dependency:resolve`, link JARs into workspace
6. Auto-detect main class from JAR manifest if not specified
7. Launch Java with constructed classpath

**Endpoint String Format:**
- Endpoints use `+` to concatenate multiple artifacts (adds all to classpath)
- Main class auto-completion: prefix with `@` for partial match (e.g., `@ScriptREPL`)
- Only the first endpoint should specify a main class

**Configuration:**
- `~/.jgorc`: INI file with `[settings]`, `[repositories]`, and `[shortcuts]` sections
- `JGO_CACHE_DIR` environment variable overrides cache directory
- `M2_REPO` environment variable overrides Maven repository location

### Important Implementation Details

**Deprecated Functions:**
- `m2_path()` is deprecated in favor of `m2_home()` and `m2_repo()`

**Link Types:**
- Supports hard links (default), soft links, or copy for linking JARs from Maven repo to jgo cache
- Configured via `links` setting in `~/.jgorc` or `--link-type` flag
- "auto" mode tries hard link, falls back to soft link, then copy

**Dependency Management Mode (`-m` flag):**
- When enabled, adds endpoints to POM's `<dependencyManagement>` section using import scope
- Ensures transitive dependency versions match those of the endpoint itself
- See README.md "Pitfalls" section for details on Maven dependency management

## Testing

Tests are in the `tests/` directory:
- `test_run.py`: Integration tests for running jgo
- `test_managed.py`: Tests for dependency management mode
- `test_parsington.py`: Tests for parsing endpoint strings

Tests use pytest. The project uses `uv` for dependency management.

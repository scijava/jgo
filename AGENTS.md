# AGENTS.md

This file provides guidance to AI coding assistants when working with code in this repository.

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
- `validate-pyproject` for validating pyproject.toml
- `ruff` for linting and formatting
- `mypy` for static type analysis checks

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

See `docs/architecture.md`.

### Key Workflows

**Dependency Resolution Flow:**
1. Parse the endpoint string (e.g., `org.python:jython-standalone` or `g:a:v@MainClass`) or load an entrypoint from `jgo.toml` if present
2. Expand shortcuts from `~/.config/jgo.conf` and resolve configuration via 4-tier precedence: CLI flags > `jgo.toml` > `~/.config/jgo.conf` > smart defaults
3. Determine workspace path:
   - **Project mode** (jgo.toml present): `.jgo/` in the project root
   - **Ad-hoc mode**: `~/.cache/jgo/envs/<groupId>/<artifactId>/<hash>/` where the 16-char hash is derived from coordinates + flags
4. On cache miss or forced refresh: resolve dependencies via Maven (downloading JARs to `~/.m2/repository/`), then link/copy JARs into the workspace
5. Classify each JAR as modular (EXPLICIT/AUTOMATIC) or non-modular (PLAIN), using a baseline `jar` tool fetched via `cjdk` (Java 11) for consistency; cache classification results in `~/.cache/jgo/info/...`
6. Separate JARs into `jars/` (classpath) and `modules/` (module-path) subdirectories in the workspace
7. Scan JAR bytecode to detect the minimum required Java version, rounded up to the nearest LTS (8, 11, 17, 21, …); record this in `jgo.lock.toml` alongside resolved coordinates and SHA-256 checksums
8. Locate an appropriate JVM: in AUTO mode (default), use `cjdk` to download/cache a matching JDK if no suitable system Java is found; in SYSTEM mode, use Java from `JAVA_HOME`/`PATH`
9. Launch Java, passing non-modular JARs via `-cp` and modular JARs via `--module-path` (when Java 9+ is available)

**Endpoint String Format:**
- Endpoints use `+` to concatenate multiple artifacts (adds all to classpath)
- Main class specification: use `@` separator after coordinates (e.g., `coord1+coord2@MainClass`)
- Auto-completion: Simple class names without dots are auto-completed (e.g., `ScriptREPL` → `org.scijava.script.ScriptREPL`)
- Fully qualified names (with dots) are used as-is (e.g., `org.example.Main`)
- Old format (`coord:@MainClass` or `coord:MainClass`) is deprecated but still supported

**Configuration:**
- `~/.config/jgo.conf`: INI file with `[settings]`, `[repositories]`, and `[shortcuts]` sections
- `JGO_CACHE_DIR` environment variable overrides cache directory
- `M2_REPO` environment variable overrides Maven repository location

**Dependency Management Mode (enabled by default):**
- By default, jgo adds endpoints to POM's `<dependencyManagement>` section using import scope
- This ensures transitive dependency versions match those of the endpoint itself
- Use `--no-managed` flag to disable this behavior (rare)
- See `docs/dependency-management.md` for details on Maven dependency management
- The `-m`/`--managed` flags still work for backward compatibility but are now the default

## Testing

- Unit tests in `tests/test_*.py` use `pytest` via `uv`.
- Integration tests in `tests/cli/*.t` use `prysk` via `uv`.
- The `bin/test.sh` script runs both kinds of tests, and can be given arguments to limit what runs.

### Thicket Test Fixture

The "thicket" is a complex generated hierarchy of Maven POMs used to test jgo's Maven model building:

**Location:** `tests/fixtures/thicket/`
- `generator.py`: Generates complex POM hierarchies with configurable random seed
- `__init__.py`: Exports `generate_thicket()` function

**What it tests:**
- Multi-level parent POM inheritance (up to 4 levels)
- BOM imports and transitive BOM imports (up to 3 per POM)
- Property-based versioning and interpolation
- Complex dependency management merging

**How it works:**
- POMs are automatically generated during test runs via a pytest session-scoped fixture in `tests/conftest.py`
- Uses a fixed random seed (42) for reproducible test results
- No manual setup required - just run `bin/test.sh`
- POMs are generated in a temporary directory and cleaned up automatically

**Regenerating with different seeds:**
```bash
# From project root
python -m tests.fixtures.thicket.generator 123 /tmp/thicket-test
```

This ensures tests are fully integrated with the test suite and require no manual intervention.

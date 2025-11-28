# jgo 2.0.0 Implementation Plan

## Overview

jgo 2.0 redesigns the architecture around three clean layers:

1. **Maven Layer** - Pure dependency resolution (from db-xml-maven/maven.py)
2. **Environment Layer** - Environment materialization (JAR linking/copying)
3. **Execution Layer** - Java program launching

This design makes each layer independently useful while eliminating the current monolithic approach.

## Architecture

### Layer 1: Maven Resolution (`jgo.maven`)

Port the pure-Python Maven resolution code from `db-xml-maven/maven.py`.

**Key Classes:**
- `MavenContext` - Maven configuration (repos, cache, resolver)
- `Resolver` - Abstract resolver interface
  - `SimpleResolver` - Pure Python (no mvn required)
  - `MavenResolver` - Shells out to mvn (renamed from SysCallResolver)
- `Project` - G:A (groupId:artifactId)
- `Component` - G:A:V (with version)
- `Artifact` - G:A:P:C:V (with packaging and classifier)
- `Dependency` - Artifact + scope + optional + exclusions
- `POM` - POM file parser
- `Metadata` - maven-metadata.xml parser
- `Model` - Dependency resolution engine

**API Example:**
```python
from jgo.maven import MavenContext, SimpleResolver

# Create Maven context
maven = MavenContext(
    repo_cache=Path("~/.m2/repository"),
    remote_repos={"central": "https://repo.maven.apache.org/maven2"},
    resolver=SimpleResolver()
)

# Resolve dependencies
component = maven.project("org.python", "jython-standalone").at_version("2.7.3")
model = component.model()
deps = model.dependencies()  # Returns List[Dependency]

for dep in deps:
    print(f"{dep.groupId}:{dep.artifactId}:{dep.version}")
    artifact = dep.artifact
    path = artifact.resolve()  # Downloads if needed
    print(f"  -> {path}")
```

### Layer 2: Environment Materialization (`jgo.env`)

Creates and manages environment directories with materialized JAR files.

**Key Classes:**
- `Environment` - A directory containing an environment
- `EnvironmentBuilder` - Builds environments from endpoints
- `LinkStrategy` - How to materialize artifacts (hard/soft/copy)

**Environment Structure (Hybrid Approach):**

jgo 2.0 supports both project-local and centralized environments:

**Project Mode** (when jgo.toml exists):
```
.jgo/                      # Local environment (like node_modules, .venv, .pixi)
  jgo.toml                 # Copy of spec that created this environment
  jgo.lock.toml            # Locked versions (SNAPSHOTs → timestamps)
  jars/                    # Materialized JAR files
    artifact1.jar
    artifact2.jar
  manifest.json            # Metadata (min_java_version, created, etc.)
```

**Ad-hoc Mode** (one-off CLI execution):
```
~/.cache/jgo/              # Centralized cache (like conda envs)
  <groupId>/
    <artifactId>/
      <hash>/
        jgo.toml           # Auto-generated spec
        jgo.lock.toml      # Locked versions
        jars/              # JAR files
        manifest.json      # Metadata
```

**Behavior:**
- `jgo` in directory with jgo.toml → Creates `.jgo/` locally
- `jgo G:A:V` without jgo.toml → Uses `~/.cache/jgo/`
- Override via `cache_dir` setting or `--cache-dir` flag

**File Purposes:**
- `jgo.toml` - Environment specification (reproducible, version-controlled)
- `jgo.lock.toml` - Locked dependency versions (like package-lock.json)
- `manifest.json` - Runtime metadata (min_java_version, link_strategy, timestamps)

**API Example:**
```python
from jgo.env import EnvironmentBuilder, LinkStrategy
from jgo.maven import MavenContext

# Option 1: Auto-detect mode (project-local if jgo.toml exists)
builder = EnvironmentBuilder(
    maven_context=MavenContext(),
    link_strategy=LinkStrategy.HARD
    # cache_dir auto-selected: .jgo/ if jgo.toml exists, else ~/.cache/jgo/
)

# Option 2: Explicit project-local mode
builder = EnvironmentBuilder(
    maven_context=MavenContext(),
    cache_dir=Path(".jgo"),
    link_strategy=LinkStrategy.HARD
)

# Option 3: Explicit centralized mode
builder = EnvironmentBuilder(
    maven_context=MavenContext(),
    cache_dir=Path.home() / ".cache" / "jgo",
    link_strategy=LinkStrategy.HARD
)

# Build from endpoint string
environment = builder.from_endpoint(
    "org.python:jython-standalone:2.7.3",
    update=False
)

# Build from jgo.toml specification
from jgo.env import EnvironmentSpec
spec = EnvironmentSpec.load("jgo.toml")
environment = builder.from_spec(spec)

# Or from components directly
environment = builder.from_components(
    included=[component1, component2],
    excluded=[component3],
    main_class="org.python.util.jython"
)

# Access environment properties
print(environment.path)              # Path to environment dir
print(environment.classpath)         # List of JAR paths
print(environment.main_class)        # Detected main class
print(environment.min_java_version)  # Detected from bytecode
```

#### Environment Specification Files (`jgo.toml`)

Environments can be defined in `jgo.toml` files for reproducibility:

```toml
# jgo.toml - Define a reproducible Java environment

[environment]
name = "imagej-analysis"
description = "ImageJ with Python scripting"

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

# Maven-style exclusions (G:A only, not G:A:V)
[dependencies.exclusions]
"net.imagej:imagej" = ["org.scijava:scijava-common"]

[entrypoints]
imagej = "net.imagej.Main"
repl = "org.scijava.script.ScriptREPL"
default = "imagej"

[settings]
links = "hard"
cache_dir = ".jgo"
```

**CLI Usage:**
```bash
# Project mode (creates .jgo/ locally)
cd my-project/
jgo                              # Run from jgo.toml in current dir
jgo --entrypoint repl            # Run specific entry point
jgo --init "endpoint"            # Generate jgo.toml from endpoint
jgo -f environment.toml          # Run from specific file

# Add .jgo/ to .gitignore
echo ".jgo/" >> .gitignore
git add jgo.toml jgo.lock.toml   # Commit specs, not environment

# Ad-hoc mode (uses ~/.cache/jgo/)
jgo org.python:jython-standalone              # One-off execution
jgo org.python:jython-standalone:2.7.3        # Specific version

# Custom cache location
jgo --cache-dir /tmp/test G:A:V  # Override cache directory
```

**Comparison to Other Tools:**
| Tool | Project Config | Lock File | Environment | Default Location |
|------|---------------|-----------|-------------|------------------|
| npm | package.json | package-lock.json | node_modules/ | Local |
| Python | requirements.txt | - | .venv/ | Local |
| pixi | pixi.toml | pixi.lock | .pixi/ | Local |
| **jgo** | **jgo.toml** | **jgo.lock.toml** | **.jgo/** | **Hybrid** |

**Configuration Hierarchy:**
- `.jgorc` = Global user configuration (`~/.jgorc`)
- `jgo.toml` = Project environment spec (version-controlled)
- `jgo.lock.toml` = Locked versions (version-controlled)
- `.jgo/` = Built environment (gitignored, rebuilt from specs)

#### Lock File Format (`jgo.lock.toml`)

The lock file records exact resolved versions for reproducibility:

```toml
# jgo.lock.toml - Auto-generated, do not edit manually

[metadata]
generated = "2025-01-15T10:30:00Z"
jgo_version = "2.0.0"

[environment]
name = "imagej-analysis"
min_java_version = 17

# All dependencies with resolved versions
[[dependencies]]
groupId = "net.imagej"
artifactId = "imagej"
version = "2.15.0"                    # Exact version
sha256 = "abc123..."                  # Checksum

[[dependencies]]
groupId = "org.scijava"
artifactId = "scijava-common"
version = "2.97.0"                    # Transitive dep, resolved
sha256 = "def456..."

[[dependencies]]
groupId = "some.snapshot"
artifactId = "library"
version = "1.0-20250115.103000-5"     # SNAPSHOT locked to timestamp
sha256 = "ghi789..."

[entrypoints]
imagej = "net.imagej.Main"
default = "imagej"
```

**Lock file behavior:**
- Generated on `jgo` first run or when jgo.toml changes
- Locks SNAPSHOT versions to exact timestamps
- Records SHA256 checksums for verification
- Committed to version control for reproducible builds
- Updated with `jgo --update` or when dependencies change

#### Automatic Java Version Detection

Environments automatically detect the minimum required Java version by analyzing bytecode:

```python
environment = builder.from_endpoint("net.imagej:imagej:2.15.0")

# Scans .class files in JARs, detects bytecode version
print(environment.min_java_version)  # 17

# Cached in manifest.json to avoid re-scanning
```

This enables zero-configuration execution with cjdk (see Layer 3 below).

### Layer 3: Execution (`jgo.exec`)

Launches Java programs with constructed environments.

**Key Classes:**
- `JavaRunner` - Executes Java programs
- `JVMConfig` - JVM configuration (heap, GC, etc.)
- `JavaSource` - Strategy for locating Java (SYSTEM, CJDK, AUTO)
- `JavaLocator` - Finds or downloads Java executable

**API Example:**
```python
from jgo.exec import JavaRunner, JVMConfig, JavaSource

# Configure JVM
jvm_config = JVMConfig(
    max_heap="2G",
    gc_options=["-XX:+UseG1GC"],
    extra_args=["-Dfoo=bar"]
)

# Run with auto Java selection (uses cjdk if available)
runner = JavaRunner(
    jvm_config=jvm_config,
    java_source=JavaSource.AUTO  # Default behavior
)
result = runner.run(
    environment=environment,
    main_class="org.python.util.jython",
    app_args=["script.py", "--verbose"]
)
```

#### Automatic Java Management with cjdk (Optional)

jgo integrates with [cjdk](https://github.com/scijava/cjdk) for automatic Java version management:

```python
from jgo.exec import JavaRunner, JavaSource

# Option 1: Use system Java (lightweight, no cjdk needed)
runner = JavaRunner(java_source=JavaSource.SYSTEM)

# Option 2: Use specific Java version via cjdk
runner = JavaRunner(
    java_source=JavaSource.CJDK,
    java_version="17",
    java_vendor="adoptium"
)

# Option 3: AUTO - Uses environment's detected version (DEFAULT)
runner = JavaRunner(java_source=JavaSource.AUTO)
# If cjdk available: auto-downloads Java based on environment.min_java_version
# If cjdk not available: uses system Java (with compatibility warning)

environment = builder.from_endpoint("net.imagej:imagej:2.15.0")
# Bytecode scan detects Java 17 requirement

runner.run(environment)
# Automatically uses Java 17 via cjdk!
```

**Installation:**
```bash
pip install jgo           # Minimal - uses system Java
pip install jgo[cjdk]     # Full-featured - automatic Java management
```

**Zero-Configuration Execution:**
```python
import jgo

# User doesn't need Java pre-installed!
# Automatically detects requirement and downloads Java 17
jgo.run("net.imagej:imagej:2.15.0")

# Output:
# INFO: Detected minimum Java version: 17
# INFO: Obtaining Java 17 via cjdk...
# INFO: Using Java 17.0.9 (Adoptium)
# [ImageJ launches successfully]
```

**CLI Support:**
```bash
jgo net.imagej:imagej                    # Auto-detect and use correct Java
jgo --java-version 11 endpoint           # Force Java 11
jgo --java-vendor zulu endpoint          # Prefer Zulu vendor
jgo --java-source system endpoint        # Force system Java
```

### High-Level Convenience API (`jgo`)

The top-level `jgo` module provides convenience functions that chain the layers:

```python
import jgo

# Simple one-liner
jgo.run("org.python:jython-standalone:2.7.3", ["script.py"])

# With configuration
result = jgo.run(
    endpoint="org.python:jython-standalone:2.7.3",
    app_args=["script.py"],
    jvm_args=["-Xmx2G"],
    update=False,
    verbose=True
)

# Just build environment (don't run)
environment = jgo.build("org.python:jython-standalone:2.7.3")
print(environment.classpath)
```

## Terminology

### Endpoint

**Definition:** An endpoint is a complete specification for running a Java program via jgo.

**Syntax:**
```
endpoint = coordinate-set [':' entry-point]
coordinate-set = coordinate ('+' coordinate)*
coordinate = groupId ':' artifactId [':' version] [':' classifier]
entry-point = main-class | '@' main-class-fragment
```

**Examples:**
- `org.python:jython-standalone` - Single coordinate, auto-detect entry point
- `org.python:jython-standalone:2.7.3` - With explicit version
- `org.python:jython-standalone:@Main` - With entry point auto-completion
- `net.imagej:imagej+org.scijava:scripting-jython` - Two coordinates (single endpoint)
- `G:A:V+G2:A2:V2:org.example.Main` - Two coordinates with explicit entry point

**Key Point:** Multiple coordinates concatenated with `+` form a **single endpoint**, not multiple endpoints.

**Terminology Hierarchy:**
- **Coordinate** = `G:A:V` - A single Maven artifact identifier
- **Coordinate Set** = `coord1+coord2+...` - Multiple coordinates
- **Entry Point** = Main class specification
- **Endpoint** = Coordinate set + optional entry point (the complete runnable specification)

## CLI Redesign

### Current Issues

The current CLI has some confusing aspects:
- `-u` vs `-U` is unclear (update cache vs force update)
- `-m` (manage dependencies) is obscure
- Mixing JVM args with jgo flags is fragile
- No clear separation between jgo options and Java/app options

### New CLI Design

```
jgo [JGO_OPTIONS] <endpoint> [-- JVM_OPTIONS] [-- APP_ARGS]

JGO Options:
  -h, --help              Show this help message
  -v, --verbose           Verbose output (can be repeated: -vv, -vvv)
  -q, --quiet             Suppress all output

  --update                Update cached environment
  --offline               Work offline (don't download)
  --no-cache              Skip cache entirely, always rebuild

  --resolver {auto,pure,maven}
                          Dependency resolver to use (default: auto)
                          - auto: use pure, fall back to maven if needed
                          - pure: pure Python (no mvn required)
                          - maven: shell out to mvn command

  --link {hard,soft,copy,auto}
                          How to link JARs into environment (default: auto)

  --cache-dir PATH        Override cache directory (default: ~/.jgo)
  --repo-cache PATH       Override Maven repo cache (default: ~/.m2/repository)
  -r, --repository NAME=URL
                          Add remote Maven repository

  --managed               Use dependency management (import scope)
  --main-class CLASS      Specify main class explicitly
  --list-versions         List available versions and exit
  --print-classpath       Print classpath and exit (don't run)
  --dry-run              Show what would be done, but don't do it

Endpoint Format:
  groupId:artifactId[:version][:classifier][:mainClass]

  Multiple Maven coordinates can be combined with '+':
    org.scijava:scijava-common:2.96.0+org.scijava:parsington:3.1.0

  Use '@' for main class auto-completion:
    org.scijava:scijava-common:@ScriptREPL

Examples:
  # Run Jython REPL
  jgo org.python:jython-standalone

  # Run with specific version and JVM options
  jgo org.python:jython-standalone:2.7.3 -- -Xmx2G -- script.py --verbose

  # Build environment without running
  jgo --print-classpath org.python:jython-standalone

  # Force update and use pure Python resolver
  jgo --update --resolver=pure org.python:jython-standalone

  # List available versions
  jgo --list-versions org.scijava:scijava-common
```

## Module Structure

```
jgo/
  __init__.py           # High-level convenience API
  __main__.py           # CLI entry point

  maven/                # Layer 1: Maven resolution
    __init__.py         # Exports: MavenContext, Resolver, etc.
    core.py             # Main classes (MavenContext, Project, Component, Artifact)
    resolver.py         # SimpleResolver, MavenResolver
    model.py            # Model, dependency resolution logic
    pom.py              # POM, XML parsing
    metadata.py         # Metadata, maven-metadata.xml
    util.py             # Helper functions

  env/                  # Layer 2: Environment materialization
    __init__.py         # Exports: Environment, EnvironmentBuilder, EnvironmentSpec
    environment.py      # Environment class with bytecode detection
    builder.py          # EnvironmentBuilder
    linking.py          # LinkStrategy, linking logic
    spec.py             # EnvironmentSpec (jgo.toml parser)

  exec/                 # Layer 3: Execution
    __init__.py         # Exports: JavaRunner, JVMConfig, JavaSource
    runner.py           # JavaRunner
    config.py           # JVMConfig
    java_source.py      # JavaSource enum, JavaLocator (cjdk integration)

  cli/                  # CLI interface
    __init__.py
    parser.py           # Argument parsing
    commands.py         # CLI commands (run, build, list-versions, etc.)

  config/               # Configuration
    __init__.py
    jgorc.py            # ~/.jgorc parsing and defaults

  compat/               # Backward compatibility
    __init__.py
    v1.py               # jgo 1.x compatibility shims

  util/                 # Shared utilities
    __init__.py
    logging.py          # Logging setup
    cache.py            # Cache key generation
```

## Dependencies and Installation

### Core Dependencies (Minimal)

```toml
# pyproject.toml
[project]
dependencies = [
    "psutil",  # For system memory detection
]
```

### Optional Dependencies

```toml
[project.optional-dependencies]
cjdk = ["cjdk>=0.5.0"]   # Automatic Java version management
all = ["cjdk>=0.5.0"]    # All optional features
```

### Installation Options

```bash
# Minimal installation (uses system Java)
pip install jgo

# Full-featured (automatic Java management)
pip install jgo[cjdk]

# All features
pip install jgo[all]
```

## Implementation Tasks

### Phase 1: Maven Layer (Week 1)

**1.1: Port maven.py** ✓ High Priority
- Copy `maven.py` from db-xml-maven to `jgo/maven/`
- Split into logical modules (core, resolver, model, pom, metadata)
- Rename `SysCallResolver` → `MavenResolver`
- Add `jgo/maven/__init__.py` with clean exports

**1.2: Fix property interpolation in G/A/C** ✓ Critical
- Fix the "CTR START HERE" issue at line 1022-1032
- Interpolate properties in `Environment.dependency()` before creating GACT key
- Add tests for dependencies using `${project.groupId}`, etc.

**1.3: Implement SNAPSHOT support** ⚠️ Medium Priority
- Add SNAPSHOT download in `SimpleResolver`
- Fetch version-specific maven-metadata.xml
- Parse `<snapshotVersion>` to get timestamped filenames
- Handle SNAPSHOT resolution in local repos

**1.4: Add remote metadata fetching** ⚠️ Medium Priority
- Implement `Project.update()` to fetch maven-metadata.xml from remotes
- Support RELEASE/LATEST version resolution without local cache
- Cache fetched metadata appropriately

**1.5: Tests for Maven layer** ✓ High Priority
- Port tests from db-xml-maven
- Add tests for common projects (jython, scijava-common, imagej)
- Test both SimpleResolver and MavenResolver
- Test BOM imports, exclusions, scope transitivity

### Phase 2: Environment Layer (Week 2)

**2.1: Implement Environment class** ✓ High Priority
- Track environment path, coordinates, classpath
- Load/save manifest.json with metadata
- Detect/cache main class

**2.2: Implement EnvironmentBuilder** ✓ High Priority
- Build from endpoint strings (parse + and : syntax)
- Build from Component objects
- Handle main class auto-detection and @completion
- Implement linking strategies (hard/soft/copy/auto)

**2.3: Cache key generation** ✓ High Priority
- Generate stable hashes for coordinate combinations
- Handle managed vs unmanaged dependency modes
- Ensure cache hits for identical environments

**2.4: Migration from old environment format** ⚠️ Medium Priority
- Detect old-style environment dirs (lacking manifest.json)
- Either migrate them or rebuild them
- Handle gracefully during transition period

**2.5: Tests for Environment layer** ✓ High Priority
- Test environment building with various endpoints
- Test linking strategies on different filesystems
- Test cache key generation and collision avoidance
- Test main class detection

**2.6: Bytecode Version Detection** ✓ High Priority [2 days]
- Add `min_java_version` property to Environment class
- Implement bytecode scanning of JAR files (.class file major version)
- Map bytecode version to Java version (round up to LTS: 8, 11, 17, 21)
- Cache result in manifest.json to avoid re-scanning
- Handle edge cases (no class files, corrupt JARs, multiple versions)
- Add tests for version detection with various JARs

**2.7: Environment Specification Files (jgo.toml + jgo.lock.toml)** ✓ High Priority [3 days]
- Define `jgo.toml` schema (TOML format)
- Implement `EnvironmentSpec` class to parse/validate TOML
- Support loading from file: `EnvironmentSpec.load(path)`
- Support saving to file: `spec.save(path)`
- Support multiple entry points in `[entrypoints]` table
- Support Maven-style exclusions (G:A only, per Maven spec)
- Implement `EnvironmentBuilder.from_spec(spec)`
- Implement jgo.lock.toml generation with locked versions
- Lock SNAPSHOT versions to exact timestamps
- Record SHA256 checksums for verification
- Write both jgo.toml and jgo.lock.toml to environment directory
- Implement hybrid cache_dir behavior (`.jgo/` vs `~/.cache/jgo/`)
- Auto-detect project mode when jgo.toml exists
- Add validation with helpful error messages
- Document schema with examples

### Phase 3: Execution Layer (Week 3)

**3.1: Implement JVMConfig** ✓ High Priority
- Heap size configuration
- GC options
- System properties (-Dfoo=bar)
- Auto-detection of system memory (port from util.py)

**3.2: Implement JavaRunner** ✓ High Priority
- Construct java command with classpath
- Handle stdout/stderr
- Return CompletedProcess
- Proper error handling

**3.3: Tests for Execution layer** ✓ High Priority
- Test running simple Java programs
- Test JVM option passing
- Test app argument passing
- Test error conditions (missing java, missing main class)

**3.4: cjdk Integration** ✓ High Priority [3 days]
- Add `JavaSource` enum (SYSTEM, CJDK, AUTO)
- Implement `JavaLocator` class to find/download Java
- Integrate `Environment.min_java_version` with JavaRunner
- Make `JavaSource.AUTO` the default behavior
- Download Java via cjdk when available and needed
- Fall back to system Java with compatibility warning
- Verify system Java version and warn if too old
- Add CLI flags: `--java-version`, `--java-vendor`, `--java-source`
- Make cjdk an optional dependency: `pip install jgo[cjdk]`
- Add tests for all three JavaSource modes
- Test on multiple platforms (Linux, macOS, Windows)
- Document zero-configuration workflow

### Phase 4: CLI and High-Level API (Week 4)

**4.1: Implement new CLI parser** ✓ High Priority
- Parse new flag syntax
- Handle -- separators for JVM and app args
- Validate endpoint format
- Load ~/.jgorc configuration

**4.2: Implement CLI commands** ✓ High Priority
- `run` - The default command (runs endpoint or jgo.toml)
- `build` - Build environment without running
- `list-versions` - Show available versions
- `update` - Update cache for endpoint
- `clean` - Clean cache
- Support for jgo.toml files:
  - `jgo` (no args) - Run from jgo.toml in current directory
  - `jgo -f FILE` - Run from specific environment file
  - `jgo --entrypoint NAME` - Run specific entry point from jgo.toml
  - `jgo --init ENDPOINT` - Generate jgo.toml from endpoint
  - `jgo --list-entrypoints` - Show available entry points in jgo.toml

**4.3: High-level convenience API** ✓ High Priority
- `jgo.run()` - One-liner to run an endpoint
- `jgo.build()` - Build environment
- `jgo.resolve()` - Just resolve dependencies
- Integration with all three layers

**4.4: Configuration system** ⚠️ Medium Priority
- Parse ~/.jgorc with backward compatibility
- Support environment variables (JGO_CACHE_DIR, etc.)
- Merge config sources with proper precedence

**4.5: Logging and verbosity** ⚠️ Medium Priority
- Structured logging at each layer
- Verbose levels (-v, -vv, -vvv)
- Quiet mode suppression

### Phase 5: Backward Compatibility (Week 5)

**5.1: v1 compatibility shims** ✓ High Priority
- `jgo.compat.v1` module with old API
- Old function signatures call new implementation
- Deprecation warnings

**5.2: Endpoint format compatibility** ✓ High Priority
- Support all old endpoint formats
- Maintain + for concatenation
- Maintain @ for main class completion

**5.3: Configuration compatibility** ✓ High Priority
- Old ~/.jgorc format still works
- Old settings map to new structure
- No breaking changes for existing users

### Phase 6: Documentation and Release (Week 6)

**6.1: API documentation** ✓ High Priority
- Docstrings for all public classes/functions
- Type hints throughout
- Sphinx or MkDocs setup

**6.2: User guide** ✓ High Priority
- Migration guide from 1.x to 2.x
- Tutorial for each layer
- CLI reference
- Common recipes

**6.3: Update README.md** ✓ High Priority
- New architecture overview
- Updated examples
- Link to full documentation

**6.4: CHANGELOG.md** ✓ High Priority
- Document breaking changes
- Document new features
- Migration instructions

**6.5: Release preparation** ✓ High Priority
- Update version to 2.0.0
- Update pyproject.toml dependencies
- CI/CD updates for new structure
- Release notes

## Breaking Changes and Migration

### Breaking Changes

1. **Moved modules**: `jgo.jgo` internals are now split across `jgo.maven`, `jgo.env`, `jgo.exec`
2. **Renamed functions**: Some internal functions have better names
3. **CLI flags**: New flag syntax
4. **Python API**: Old functional API replaced with OOP API (but compat shims provided)

### Migration for Python API Users

**Before (jgo 1.x):**
```python
from jgo import jgo
import sys

# Old API
jgo.main_from_endpoint(
    'org.python:jython-standalone',
    primary_endpoint_version='2.7.3',
    argv=sys.argv[1:]
)
```

**After (jgo 2.x):**
```python
import jgo

# New API
jgo.run(
    endpoint='org.python:jython-standalone:2.7.3',
    app_args=sys.argv[1:]
)

# Or use compatibility layer
from jgo.compat.v1 import main_from_endpoint
main_from_endpoint(
    'org.python:jython-standalone',
    primary_endpoint_version='2.7.3',
    argv=sys.argv[1:]
)
```

**Using the new layered API:**
```python
from jgo.maven import MavenContext
from jgo.env import EnvironmentBuilder
from jgo.exec import JavaRunner

# Full control over each layer
maven = MavenContext()
component = maven.project("org.python", "jython-standalone").at_version("2.7.3")

builder = EnvironmentBuilder(maven_env=env)
environment = builder.from_components([component])

runner = JavaRunner()
runner.run(environment, app_args=["script.py"])
```

### Migration for CLI Users

**Before (jgo 1.x):**
```bash
jgo -v -u org.python:jython-standalone:2.7.3 script.py
```

**After (jgo 2.x):**
```bash
# New syntax (recommended)
jgo --verbose --update org.python:jython-standalone:2.7.3 -- -- script.py
```

## Success Criteria

Before releasing jgo 2.0.0:

- [ ] All tests pass (aiming for >90% coverage)
- [ ] Maven layer resolves dependencies correctly for major projects (imagej, fiji, scijava)
- [ ] SNAPSHOT support works
- [ ] Property interpolation in G/A/C fields works
- [ ] CLI works with new syntax
- [ ] Backward compatibility layer works with old code
- [ ] Documentation is complete
- [ ] Migration guide is clear
- [ ] No performance regressions vs 1.x
- [ ] Successfully tested on Windows, macOS, Linux
- [ ] Memory usage is reasonable for large dependency trees

## Timeline

**Total estimated time: 7-8 weeks**

- Week 1: Maven Layer (Tasks 1.1-1.3)
- Week 2-3: Environment Layer (Tasks 2.1-2.7, includes bytecode detection and jgo.toml)
- Week 3-4: Execution Layer (Tasks 3.1-3.4, includes cjdk integration)
- Week 4-5: CLI and High-Level API (Tasks 4.1-4.3)
- Week 5-6: Backward Compatibility (Task 5.1)
- Week 6-7: Documentation and Release (Task 6.1)

**Timeline notes:**
- Added ~1.5 weeks for new features (bytecode detection, jgo.toml, jgo.lock.toml, cjdk)
- Time investment justified by zero-configuration user experience
- Assumes one developer working full-time
- Can be parallelized with multiple developers

## Benefits of This Design

1. **Modularity**: Each layer is independently useful
2. **Testability**: Each layer can be tested in isolation
3. **Flexibility**: Users can use just what they need
4. **Maintainability**: Clean separation of concerns
5. **Extensibility**: Easy to add new resolvers, link strategies, etc.
6. **No mvn dependency**: Pure Python resolver works without Maven installed
7. **Better performance**: Can cache at multiple levels
8. **Better error messages**: Each layer has clear failure points
9. **Future-proof**: Easy to add features like conda integration, docker support, etc.

## Future Enhancements (Post 2.0)

- **Conda integration**: Resolve from conda channels in addition to Maven
- **Docker support**: Build Docker images from endpoints and jgo.toml
- **Version ranges**: Support semantic versioning ranges (e.g., `">=1.0,<2.0"`)
- **Dependency graph visualization**: Generate visual dependency trees
- **Reproducibility verification**: Verify checksums match jgo.lock.toml
- **Multi-platform environments**: Build environments for multiple platforms simultaneously
- **Parallel downloads**: Speed up initial cache population
- **Progress bars**: Show download progress
- **Shell completion**: Bash/zsh completion for endpoints
- **Plugin system**: Allow custom resolvers, link strategies
- **Web UI**: Optional local web interface for exploring environments

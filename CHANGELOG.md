# Changelog

All notable changes to jgo will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - TBD

jgo 2.0 is a complete architectural redesign around three clean, independently useful layers: Maven resolution, environment materialization, and execution. This release maintains backward compatibility with jgo 1.x while adding powerful new features.

### Added

#### Zero-Configuration Execution
- **Automatic Java management**: Integration with [cjdk](https://github.com/cachedjdk/cjdk) to automatically download and manage Java versions
- **Bytecode detection**: Automatically detect minimum Java version from JAR files
- **Auto-download Java**: Install `jgo[cjdk]` to automatically download the correct Java version (no pre-installed Java required!)

#### Reproducible Environments
- **jgo.toml files**: Project-level environment specifications (like `package.json` for Node.js)
- **jgo.lock.toml files**: Lock files with exact dependency versions and SHA256 checksums (like `package-lock.json`)
- **Hybrid cache mode**: Support both project-local (`.jgo/`) and centralized (`~/.cache/jgo/`) environments
- **Multiple entry points**: Define multiple entry points per project

#### Three-Layer Architecture
- **Layer 1 - Maven resolution** (`jgo.maven`): Pure Python dependency resolution, POM parsing, and artifact downloading
  - `MavenContext`: Maven configuration and repository management
  - `SimpleResolver`: Pure Python resolver (no Maven installation required!)
  - `MavenResolver`: Shell out to `mvn` command for edge cases
  - Full support for: transitive dependencies, scopes, exclusions, dependency management (BOMs), property interpolation

- **Layer 2 - Environment materialization** (`jgo.env`): Build executable environments (directories of JARs)
  - `Environment`: Materialized directory of JARs with classpath
  - `EnvironmentBuilder`: Build environments from endpoints or specs
  - `EnvironmentSpec`: Parse and generate jgo.toml files
  - `LockFile`: Generate and verify jgo.lock.toml files
  - Link strategies: hard links (default), soft links, copy, or auto

- **Layer 3 - Execution** (`jgo.exec`): Launch Java programs
  - `JavaRunner`: Execute Java programs from environments
  - `JVMConfig`: Configure JVM settings (heap, GC, system properties)
  - `JavaSource`: Java selection strategy (SYSTEM, CJDK)
  - Cross-platform classpath handling

#### Python API
- **High-level API**: Simple functions for common use cases
  - `jgo.run()`: Run a Java application from an endpoint
  - `jgo.build()`: Build an environment without running
  - `jgo.resolve()`: Resolve dependencies to Component objects

- **Layered API**: Fine-grained control over each layer
  ```python
  from jgo.maven import MavenContext
  from jgo.env import EnvironmentBuilder
  from jgo.exec import JavaRunner
  # Full control over resolution, building, and execution
  ```

#### CLI Improvements
- **New flags**:
  - `--java-version VERSION`: Force specific Java version
  - `--java-vendor VENDOR`: Prefer specific Java vendor (adoptium, zulu, etc.)
  - `--resolver {auto,pure,maven}`: Choose dependency resolver
  - `--print-dependency-tree`: Print dependency tree
  - `--print-java-info`: Print detected Java version requirements
  - `--offline`: Work offline (don't download)
  - `--no-cache`: Skip cache entirely
  - `--ignore-jgorc`: Ignore ~/.jgorc configuration
  - `-f FILE, --file FILE`: Use specific jgo.toml file
  - `--entrypoint NAME`: Run specific entry point from jgo.toml
  - `--add-classpath PATH`: Append to classpath (replaces `--additional-jars`)

- **Improved verbosity**: `-v` (INFO), `-vv` (DEBUG), `-vvv` (TRACE)

### Changed

#### Breaking Changes (Minimal)
- **Cache location**: Default changed from `~/.jgo` to `~/.cache/jgo` (Linux/Mac) or `%LOCALAPPDATA%\jgo` (Windows)
  - Old caches not migrated automatically
  - Override with `--cache-dir` or `JGO_CACHE_DIR` environment variable

- **`-u` flag behavior**: Now checks remote repositories by default (old `-U` behavior)
  - For old `-u` behavior (rebuild without checking remote): use `--update --offline`

- **Module reorganization**: Internal code split into `jgo.maven`, `jgo.env`, `jgo.exec` modules
  - Public API unchanged for backward compatibility
  - Old imports still work with deprecation warnings

#### Improved
- **Performance**: Faster dependency resolution with pure Python resolver
- **Error messages**: Clearer error messages with better context
- **Testing**: Comprehensive test suite with 108 tests covering all layers
- **Cross-platform**: Better Windows support with improved path handling

### Deprecated

All deprecated APIs still work but show deprecation warnings. They will be removed in jgo 3.0.

#### Python API
- `jgo.main()` → Use `jgo.run()` instead
- `jgo.main_from_endpoint()` → Use `jgo.run()` instead
- `jgo.resolve_dependencies()` → Use `jgo.resolve()` or `jgo.build()` instead

#### CLI Flags
- `-U, --force-update` → Use `-u, --update` (now checks remote by default)
- `--additional-jars JAR` → Use `--add-classpath PATH`
- `--additional-endpoints EP` → Use `+` syntax in endpoint (e.g., `G1:A1+G2:A2`)
- `--link-type TYPE` → Use `--link TYPE`
- `--log-level LEVEL` → Use `-v`, `-vv`, `-vvv` instead

### Removed

Nothing removed in 2.0 - full backward compatibility maintained.

### Fixed

- **Property interpolation**: Fixed interpolation of properties in groupId/artifactId/classifier fields
- **Scope handling**: Improved compile/runtime/provided scope matching
- **Main class detection**: More robust main class auto-detection from JAR manifests
- **Endpoint parsing**: Better parsing of complex endpoint strings
- **Windows support**: Fixed path handling and link creation on Windows

### Security

- **Checksum support**: jgo.lock.toml includes SHA256 checksums for all dependencies
- **Verification**: Can verify downloaded artifacts against lock file checksums

### Documentation

- **User Guide**: Comprehensive guide covering all features
- **Migration Guide**: Detailed guide for upgrading from jgo 1.x
- **Architecture Guide**: Explanation of three-layer design
- **API Reference**: Enhanced docstrings for `help(jgo)` command
- **Examples**: Sample jgo.toml files and Python scripts

### Internal

- **Code quality**:
  - Formatted with `black` and `ruff`
  - Type hints throughout
  - Comprehensive docstrings
  - 108 tests, all passing

- **Dependencies**:
  - `cjdk` for automatic Java management
  - `psutil` for max heap auto-detection
  - `requests` for dependency fetching
  - `tomli`/`tomli-w` for jgo.toml

## [1.1.0] - Previous Release

See git history for changes in jgo 1.x series.

---

## Migration from 1.x to 2.0

See [docs/MIGRATION.md](docs/MIGRATION.md) for detailed migration instructions.

### Quick Migration Checklist

- [ ] Update import statements if using internal APIs (public API unchanged)
- [ ] Replace deprecated CLI flags with new equivalents
- [ ] Test scripts with deprecation warnings enabled: `python -W default::DeprecationWarning -m jgo ...`
- [ ] Consider using new features: jgo.toml, cjdk integration, layered API
- [ ] Update cache directory path if using `JGO_CACHE_DIR` (new default location)

### Backward Compatibility

jgo 2.0 maintains **full backward compatibility** with jgo 1.x:
- All jgo 1.x Python APIs work (with deprecation warnings)
- All jgo 1.x CLI commands work (with deprecation warnings for renamed flags)
- All jgo 1.x scripts should run without modification
- Deprecation warnings can be enabled to see what needs updating

Plan to migrate away from deprecated APIs before jgo 3.0 (which will remove them).

---

[Unreleased]: https://github.com/scijava/jgo/compare/v1.1.0...HEAD
[2.0.0]: https://github.com/scijava/jgo/compare/v1.1.0...v2.0.0
[1.1.0]: https://github.com/scijava/jgo/releases/tag/v1.1.0

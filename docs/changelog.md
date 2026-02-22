# Changelog

## 2.0.0 (unreleased)

jgo 2.0 is a major rewrite with a new architecture, new CLI, and new Python API. It maintains backward compatibility with jgo 1.x -- existing scripts and code continue to work with deprecation warnings.

### New features

- **Command-based CLI** -- Modern subcommand interface (`jgo run`, `jgo init`, `jgo add`, `jgo list`, `jgo tree`, `jgo info`, `jgo search`, `jgo config`, etc.) following conventions from tools like `uv`, `cargo`, and `npm`. The old `jgo <endpoint>` syntax still works.

- **jgo.toml project files** -- Reproducible environments with lock files, similar to `package.json` + `package-lock.json`. Create with `jgo init`, manage with `jgo add`/`jgo remove`, sync with `jgo sync`.

- **Pure Python resolver** -- Resolve Maven dependencies without a Maven installation. Handles transitive dependencies, property interpolation, dependency management (BOMs), exclusions, and scopes.

- **Automatic Java management** -- Zero-configuration execution: jgo detects the minimum Java version from bytecode and downloads it on demand via [cjdk](https://github.com/cachedjdk/cjdk).

- **Three-layer architecture** -- Independently useful layers for Maven resolution (`jgo.maven`), environment materialization (`jgo.env`), and Java execution (`jgo.exec`).

- **High-level Python API** -- `jgo.run()`, `jgo.build()`, `jgo.resolve()` for simple programmatic usage.

- **Artifact search** -- `jgo search` queries Maven Central (and configured repositories) for artifacts.

- **Rich terminal output** -- Color, progress bars, and formatted tables via [Rich](https://github.com/Textualize/rich).

- **JVM tuning flags** -- `--max-heap`, `--min-heap`, `--gc` for convenient JVM configuration.

- **Platform-aware profile activation** -- `--platform`, `--os-name`, `--os-arch` flags for Maven profile activation.

- **XDG config support** -- Settings file at `~/.config/jgo.conf` (XDG standard), with `~/.jgorc` still supported.

### Breaking changes

- **Default cache directory** changed from `~/.jgo` to `~/.cache/jgo`. Override with `--cache-dir` or `JGO_CACHE_DIR`.
- **`-u` flag behavior** -- Now checks remote repositories (the old `-U` behavior). For the old `-u` behavior (local rebuild only), use `-u --offline`.

### Deprecated

- `jgo.main()`, `jgo.main_from_endpoint()`, `jgo.resolve_dependencies()` -- use `jgo.run()`, `jgo.build()`, `jgo.resolve()` instead.
- `-U`/`--force-update`, `-a`/`--additional-jars`, `--additional-endpoints`, `--link-type`, `--log-level` flags -- see {doc}`migration` for replacements.

Deprecated APIs will be removed in jgo 3.0.

## 1.x

See the [GitHub releases page](https://github.com/apposed/jgo/releases) for the jgo 1.x changelog.

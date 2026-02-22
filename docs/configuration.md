# Configuration

jgo is configured through a combination of settings files, environment variables, command-line flags, and `jgo.toml` project files.

## Settings file

The global settings file uses INI format. jgo checks these locations in order:

1. `~/.config/jgo.conf` (XDG Base Directory standard -- recommended)
2. `~/.jgorc` (legacy location, still supported)

If both exist, the XDG location takes precedence.

### Format

```ini
[settings]
cacheDir = ~/.cache/jgo
m2Repo = ~/.m2/repository
links = hard

[repositories]
scijava.public = https://maven.scijava.org/content/groups/public

[shortcuts]
imagej = net.imagej:imagej
fiji = sc.fiji:fiji:LATEST
jython = org.python:jython-standalone
repl = imagej:org.scijava.script.ScriptREPL
```

### `[settings]` section

`cacheDir`
: Root directory for cached environments. Default: `~/.cache/jgo`.

`m2Repo`
: Local Maven repository cache. Default: `~/.m2/repository`.

`links`
: Link strategy for JARs: `hard`, `soft`, `copy`, or `auto`. Default: `hard`.

### `[repositories]` section

Additional remote Maven repositories. Maven Central is always included. Each entry is `name = URL`:

```ini
[repositories]
scijava.public = https://maven.scijava.org/content/groups/public
myrepo = https://repo.example.com/maven2
```

You can also pass repositories on the command line with `-r`:

```bash
jgo -r scijava=https://maven.scijava.org/content/groups/public org.scijava:parsington
```

:::{tip}
For more control over Maven repository configuration (mirrors, authentication), use Maven's `~/.m2/settings.xml`. See [Using Mirrors for Repositories](https://maven.apache.org/guides/mini/guide-mirror-settings.html).
:::

### `[shortcuts]` section

Shortcuts are aliases that expand to Maven coordinates. They replace the matched prefix at the beginning of an endpoint string:

```ini
[shortcuts]
imagej = net.imagej:imagej
fiji = sc.fiji:fiji:LATEST
repl = imagej:org.scijava.script.ScriptREPL
```

**Usage:**

```bash
jgo imagej              # Expands to: net.imagej:imagej
jgo imagej:2.15.0       # Expands to: net.imagej:imagej:2.15.0
jgo repl                # Expands to: net.imagej:imagej with main class
jgo repl+groovy         # Combines multiple shortcuts
```

**Shortcut rules:**

- Shortcuts match at the start of a coordinate (or each `+`-separated part).
- Anything after the matched name is preserved (e.g., `imagej:2.0.0` keeps `:2.0.0`).
- Shortcuts can reference other shortcuts and are expanded recursively.
- Composition with `+` treats each part independently.

**Managing shortcuts from the CLI:**

```bash
jgo config shortcut                          # List all shortcuts
jgo config shortcut imagej                   # Show expansion
jgo config shortcut imagej net.imagej:imagej # Add/update
jgo config shortcut --remove imagej          # Remove
```

## Environment variables

| Variable | Description | Equivalent flag |
|:---------|:------------|:----------------|
| `JGO_CACHE_DIR` | Override cache directory | `--cache-dir` |
| `M2_REPO` | Override Maven repository location | `--repo-cache` |
| `JAVA_HOME` | Java installation (when using system Java) | `--system-java` |
| `JAVA_VERSION` | Force specific Java version | `--java-version` |
| `JGO_OFFLINE` | Work offline | `--offline` |
| `JGO_UPDATE` | Update cached environment | `--update` |
| `JGO_NO_CACHE` | Skip cache | `--no-cache` |
| `JGO_LENIENT` | Warn instead of fail on unresolved deps | `--lenient` |
| `JGO_INCLUDE_OPTIONAL` | Include optional dependencies | `--include-optional` |
| `COLOR` | Output color mode | `--color` |

## Precedence

Configuration is merged with this precedence (highest to lowest):

1. Command-line flags (`--cache-dir`, `-r`, etc.)
2. Environment variables (`JGO_CACHE_DIR`, etc.)
3. `jgo.toml` settings (in project mode)
4. Settings file (`~/.config/jgo.conf` or `~/.jgorc`)
5. Built-in defaults

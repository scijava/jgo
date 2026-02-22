# CLI Reference

## Usage

```
jgo [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGS]
```

If the first argument contains a colon (`:`), jgo treats it as an endpoint and implicitly runs `jgo run`:

```bash
# These are equivalent:
jgo org.python:jython-standalone
jgo run org.python:jython-standalone
```

## Global Options

These options apply to all commands and must appear **before** the command name:

### Output control

| Option | Description |
|:-------|:-----------|
| `-v`, `--verbose` | Verbose output. Repeat for more detail: `-vv` (debug), `-vvv` (trace). |
| `-q`, `--quiet` | Suppress all output. |
| `--color {auto,rich,styled,plain}` | Control output formatting. `auto` detects TTY. Aliases: `always`=`rich`, `never`=`plain`. Env: `COLOR`. |
| `--wrap {auto,smart,raw}` | Control line wrapping. `auto` uses smart wrapping for TTYs, raw for pipes. |
| `--dry-run` | Show what would be done without doing it. Dependencies may still be downloaded to report accurate information. |

### Environment and cache

| Option | Description |
|:-------|:-----------|
| `-f`, `--file FILE` | Use a specific `jgo.toml` file (default: `jgo.toml` in current directory). |
| `--cache-dir PATH` | Override cache directory. Env: `JGO_CACHE_DIR`. |
| `--repo-cache PATH` | Override Maven repository cache. Env: `M2_REPO`. |
| `--no-cache` | Skip cache entirely, always rebuild. Env: `JGO_NO_CACHE`. |
| `-u`, `--update` | Update cached environment (checks remote repositories). Env: `JGO_UPDATE`. |
| `--offline` | Work offline -- don't download anything. Env: `JGO_OFFLINE`. |

### Resolver and dependencies

| Option | Description |
|:-------|:-----------|
| `--resolver {auto,python,mvn}` | Dependency resolver. `auto` (default) tries pure Python first, falls back to Maven. |
| `-r`, `--repository NAME:URL` | Add a remote Maven repository. Can be repeated. |
| `--links {hard,soft,copy,auto}` | How to link JARs from Maven cache to environment. Default: from config or `auto`. |
| `--include-optional` | Include optional dependencies. Env: `JGO_INCLUDE_OPTIONAL`. |
| `--lenient` | Warn instead of failing on unresolved dependencies. Env: `JGO_LENIENT`. |
| `--full-coordinates` | Include default coordinate components (jar packaging, compile scope) in output. |

### Java

| Option | Description |
|:-------|:-----------|
| `--java-version VERSION` | Force a specific Java version (e.g., `17`). Env: `JAVA_VERSION`. |
| `--java-vendor VENDOR` | Prefer a specific Java vendor (e.g., `adoptium`, `zulu`). |
| `--system-java` | Use system Java instead of downloading on demand. |
| `--min-heap SIZE` | Minimum/initial heap size (e.g., `512M`, `1G`). |
| `--max-heap SIZE` | Maximum heap size (e.g., `4G`). Overrides auto-detection. |
| `--gc FLAG` | GC options. Shorthand: `--gc=G1`, `--gc=Z`. Special: `auto`, `none`. Can be repeated. |

### Advanced

| Option | Description |
|:-------|:-----------|
| `-D KEY=VALUE`, `--property KEY=VALUE` | Set property for Maven profile activation. |
| `--platform PLATFORM` | Target platform for profile activation. Sets os-name, os-family, and os-arch. |
| `--os-name NAME` | OS name for profile activation (e.g., `Linux`, `Windows`). |
| `--os-family FAMILY` | OS family for profile activation (e.g., `unix`, `windows`). |
| `--os-arch ARCH` | OS architecture for profile activation (e.g., `amd64`, `aarch64`). |
| `--os-version VERSION` | OS version for profile activation. |
| `--module-path-only` | Force all JARs to module-path (treat as modular). |
| `--class-path-only` | Force all JARs to classpath (disable module detection). |
| `--ignore-config` | Ignore the `~/.config/jgo.conf` settings file. |

## Commands

### `jgo run`

Run a Java application from Maven coordinates or `jgo.toml`.

```
jgo run [OPTIONS] [ENDPOINT] [-- JVM_ARGS] [-- APP_ARGS]
```

| Option | Description |
|:-------|:-----------|
| `--main-class CLASS` | Main class to run. Supports auto-completion for simple names. |
| `--entrypoint NAME` | Run a specific entrypoint from `jgo.toml`. |
| `--add-classpath PATH` | Append JARs, directories, or other paths to the classpath. Can be repeated. |

**Argument separators:** Use `--` to separate JVM arguments and application arguments:

```bash
# No extra args
jgo run org.python:jython-standalone

# JVM args only
jgo run org.python:jython-standalone -- -Xmx4G

# JVM args and app args
jgo run org.python:jython-standalone -- -Xmx4G -- script.py --verbose

# App args only (empty JVM section)
jgo run org.python:jython-standalone -- -- script.py
```

If no endpoint is given and a `jgo.toml` exists in the current directory, jgo runs its default entrypoint.

### `jgo init`

Create a new `jgo.toml` environment file.

```
jgo init [OPTIONS] [ENDPOINT]
```

| Option | Description |
|:-------|:-----------|
| `-r`, `--requirements FILE` | Add coordinates from a requirements file (one per line, `#` for comments). |

```bash
# Create empty jgo.toml
jgo init

# Initialize with a dependency
jgo init org.python:jython-standalone:2.7.3

# Initialize with multiple dependencies from a file
jgo init -r requirements.txt
```

### `jgo add`

Add dependencies to `jgo.toml`.

```
jgo add [OPTIONS] [COORDINATES...]
```

| Option | Description |
|:-------|:-----------|
| `-r`, `--requirements FILE` | Read coordinates from a requirements file. |
| `--no-sync` | Don't automatically sync after adding. |

```bash
jgo add org.slf4j:slf4j-simple:2.0.9
jgo add org.scijava:scijava-common org.scijava:scripting-jython
```

### `jgo remove`

Remove dependencies from `jgo.toml`.

```
jgo remove [OPTIONS] COORDINATES...
```

| Option | Description |
|:-------|:-----------|
| `--no-sync` | Don't automatically sync after removing. |

```bash
jgo remove org.slf4j:slf4j-simple
```

### `jgo sync`

Resolve dependencies and build the environment in `.jgo/`.

```
jgo sync [OPTIONS]
```

| Option | Description |
|:-------|:-----------|
| `--force` | Force rebuild even if cached. |

### `jgo update`

Update dependencies to latest versions within constraints. Equivalent to `jgo sync --update`.

```
jgo update [OPTIONS]
```

| Option | Description |
|:-------|:-----------|
| `--force` | Force rebuild even if cached. |

### `jgo lock`

Update `jgo.lock.toml` without building the environment.

```
jgo lock [OPTIONS]
```

| Option | Description |
|:-------|:-----------|
| `--check` | Check if lock file is up to date (exits non-zero if stale). |

### `jgo list`

List resolved dependencies as a flat list.

```
jgo list [OPTIONS] [ENDPOINT]
```

| Option | Description |
|:-------|:-----------|
| `--direct` | Show only direct (non-transitive) dependencies. |

Without an endpoint, operates on the `jgo.toml` in the current directory.

### `jgo tree`

Show the dependency tree.

```
jgo tree [OPTIONS] [ENDPOINT]
```

Without an endpoint, operates on the `jgo.toml` in the current directory.

### `jgo info`

Show information about an environment or artifact. This is a command group with subcommands:

```bash
jgo info classpath [ENDPOINT]       # Show classpath
jgo info modulepath [ENDPOINT]      # Show module-path
jgo info jars [ENDPOINT]            # Show all JAR paths (classpath + module-path)
jgo info deptree [ENDPOINT]         # Show dependency tree
jgo info deplist [ENDPOINT]         # Show flat dependency list
jgo info javainfo [ENDPOINT]        # Show Java version requirements
jgo info entrypoints                # Show entrypoints from jgo.toml
jgo info versions COORDINATE       # List available versions of an artifact
jgo info mains [ENDPOINT]           # Show classes with public main methods
jgo info manifest [ENDPOINT]        # Show JAR manifest
jgo info pom [ENDPOINT]             # Show POM content
jgo info envdir [ENDPOINT]          # Show environment directory path
```

### `jgo search`

Search for artifacts in Maven repositories.

```
jgo search [OPTIONS] QUERY...
```

| Option | Description |
|:-------|:-----------|
| `--limit N` | Limit number of results (default: 20). |
| `--repository NAME` | Search a specific repository (default: `central`). |
| `--detailed` | Show detailed metadata for each result. |

Supports plain text, coordinates (`g:a:v`), and SOLR syntax (`g:groupId a:artifactId`):

```bash
jgo search apache commons
jgo search g:org.python a:jython*
jgo search org.scijava:parsington
```

### `jgo config`

Manage jgo configuration.

```bash
jgo config list                          # List all configuration values
jgo config get KEY                       # Get a configuration value
jgo config set KEY VALUE                 # Set a configuration value
jgo config unset KEY                     # Remove a configuration value
jgo config shortcut                      # List all shortcuts
jgo config shortcut NAME                 # Show what a shortcut expands to
jgo config shortcut NAME ENDPOINT        # Add or update a shortcut
jgo config shortcut --remove NAME        # Remove a shortcut
```

### `jgo version`

Display jgo's version.

```bash
jgo version
jgo --version   # Also works as a global flag
```

## Examples

### Basic usage

```bash
# Run Jython REPL
jgo org.python:jython-standalone

# Run JRuby
echo "puts 'Hello Ruby'" | jgo org.jruby:jruby-complete@jruby.Main

# Run Groovy shell
jgo org.codehaus.groovy:groovy-groovysh+commons-cli:commons-cli:1.3.1@shell.Main
```

### With the SciJava repository

Add the SciJava repository to your [configuration](configuration.md):

```ini
[repositories]
scijava.public = https://maven.scijava.org/content/groups/public
```

Then run SciJava tools:

```bash
# SciJava REPL with different scripting languages
jgo org.scijava:scijava-common+org.scijava:scripting-jython@ScriptREPL
jgo org.scijava:scijava-common+org.scijava:scripting-groovy@ScriptREPL
```

### Inspecting artifacts

```bash
# Preview the java command without running
jgo --dry-run run org.scijava:parsington

# Preview what jgo init would create
jgo --dry-run init org.python:jython-standalone

# Check available versions
jgo info versions org.python:jython-standalone

# Show main classes in a JAR
jgo info mains org.scijava:parsington
```

### Working with Java versions

```bash
# Use a specific Java version
jgo --java-version 17 net.imagej:imagej

# Use system Java instead of downloading
jgo --system-java org.python:jython-standalone

# Check what Java version is needed
jgo info javainfo net.imagej:imagej
```

[![build status](https://github.com/apposed/jgo/actions/workflows/build.yml/badge.svg)](https://github.com/apposed/jgo/actions/workflows/build.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# jgo: painless Java component execution

![](https://raw.githubusercontent.com/apposed/jgo/main/jgo.png)

## Summary

`jgo` launches Java applications directly from Maven coordinates—no installation required. Just specify a Maven artifact identifier and an optional main class, and `jgo` resolves dependencies, materializes the environment, and runs your program.

```bash
# Run Jython REPL (latest version)
jgo org.python:jython-standalone

# Run with specific version
jgo org.python:jython-standalone:2.7.3

# With cjdk: automatically downloads Java if needed!
pip install jgo[cjdk]
jgo net.imagej:imagej  # Downloads Java 17 automatically
```

### What's New in 2.0

- **🎯 Zero-configuration execution**: Automatic Java download and version management thanks to `cjdk` integration
- **📦 Reproducible environments**: `jgo.toml` project files with lock files (like `package.json` + `package-lock.json`)
- **🏗️ Three-layer architecture**: Independently useful layers for Maven resolution, environment building, and execution
- **🐍 Pure Python resolver**: No Maven installation required for basic operations
- **🔧 Powerful Python API**: Fine-grained control over dependency resolution and execution

See [docs/MIGRATION.md](docs/MIGRATION.md) for migration from jgo 1.x.

## Quick Start

### CLI Usage

```bash
# Run Jython REPL
jgo org.python:jython-standalone

# Run with arguments
jgo org.python:jython-standalone -- -- script.py --verbose

# Multiple artifacts with main class (use @ separator)
jgo org.scijava:scijava-common+org.scijava:scripting-jython@ScriptREPL

# Force update from remote repos
jgo -u org.python:jython-standalone

# Use specific Java version
jgo --java-version 17 net.imagej:imagej

# Print classpath without running
jgo info classpath org.python:jython-standalone
```

### Python API

```python
import jgo

# Simple one-liner
jgo.run("org.python:jython-standalone:2.7.3", app_args=["script.py"])

# Build environment without running
env = jgo.build("org.python:jython-standalone")
print(env.classpath)  # List of JAR paths

# Resolve dependencies
components = jgo.resolve("org.python:jython-standalone")
for comp in components:
    print(f"{comp.groupId}:{comp.artifactId}:{comp.version}")
```

### Project Mode with jgo.toml

Create reproducible environments:

```toml
# jgo.toml
[environment]
name = "my-java-app"

[dependencies]
coordinates = ["net.imagej:imagej:2.15.0"]

[entrypoints]
default = "net.imagej.Main"

[settings]
cache_dir = ".jgo"  # Local environment like .venv
```

```bash
# Run from current directory
jgo

# Creates .jgo/ with jars/ and jgo.lock.toml
# Add to git: jgo.toml, jgo.lock.toml
# Ignore: .jgo/
```

## Installation

The `jgo` project began life as a shell script, but was later translated into
Python, so that tools such as [scyjava](https://github.com/scijava/scyjava)
could leverage its environment-building capabilities.

<details><summary><strong>Installing jgo with uv</strong></summary>

```shell
uv tool install jgo
```

</details>
<details><summary><strong>Installing jgo with pip</strong></summary>

```shell
pip install jgo
```

</details>
<details><summary><strong>Installing jgo with conda</strong></summary>

```shell
conda install -c conda-forge jgo
```

</details>
<details><summary><strong>Installing jgo from source</strong></summary>

```shell
git clone https://github.com/apposed/jgo
uv tool install --with-editable jgo jgo
```

When installed in this fashion, changes to the jgo source code will be immediately reflected when running `jgo` from the command line.

</details>
<details><summary><strong>Using jgo as a dependency</strong></summary>

```shell
uv add jgo
```
or
```shell
pixi add jgo
```
Not sure which to use? [Read this](https://jacobtomlinson.dev/posts/2025/python-package-managers-uv-vs-pixi/#so-what-do-i-use).

</details>

## CLI Reference

```
Usage: jgo [OPTIONS] <endpoint> [-- JVM_ARGS] [-- APP_ARGS]

Common Options:
  -v, --verbose           Verbose output (-vv for debug, -vvv for trace)
  -u, --update            Update cached environment
  --offline               Work offline (don't download)
  --cache-dir PATH        Override cache directory
  --java-version VERSION  Force specific Java version
  -f FILE                 Use jgo.toml file

Commands:
  run                     Run a Java application (default)
  info classpath          Show classpath
  info deptree            Show dependency tree  
  info deplist            Show flat dependency list
  info javainfo           Show Java version requirements
  info entrypoints        Show entrypoints from jgo.toml
  info versions           List available artifact versions
  init                    Create new jgo.toml file
  version                 Display jgo version

Endpoint Format:
  groupId:artifactId[:version][:classifier][@mainClass]

  Multiple artifacts: org.python:jython-standalone+org.slf4j:slf4j-simple
  Specify main class: org.scijava:scijava-common@ScriptREPL
  Auto-completion: Use simple class name (e.g., @ScriptREPL) and it will be auto-completed

Full documentation: jgo --help
```

### Examples

| Program                      | Command                                                                             |
|-----------------------------:|:------------------------------------------------------------------------------------|
| Jython REPL                  | `jgo org.python:jython-standalone`                                                  |
| JRuby eval                   | `echo "puts 'Hello Ruby'" \| jgo org.jruby:jruby-complete@jruby.Main`              |
| Groovy REPL                  | `jgo org.codehaus.groovy:groovy-groovysh+commons-cli:commons-cli:1.3.1@shell.Main` |

Note the usage of the `+` syntax as needed to append elements to the classpath.

If you add
`scijava.public = https://maven.scijava.org/content/groups/public`
to the
`[repositories]` section of your [config file](#configuration)
(see [Repositories](#repositories) below),
you can also try:

| Program                      | Command                                                                             |
|-----------------------------:|:------------------------------------------------------------------------------------|
| SciJava REPL with JRuby      | `jgo org.scijava:scijava-common+org.scijava:scripting-jruby@ScriptREPL`            |
| SciJava REPL with Jython     | `jgo org.scijava:scijava-common+org.scijava:scripting-jython@ScriptREPL`           |
| SciJava REPL with Groovy     | `jgo org.scijava:scijava-common+org.scijava:scripting-groovy@ScriptREPL`           |
| SciJava REPL with Clojure    | `jgo org.scijava:scijava-common+org.scijava:scripting-clojure@ScriptREPL`          |
| SciJava REPL with JavaScript | `jgo org.scijava:scijava-common+org.scijava:scripting-javascript@ScriptREPL`       |

### FAQ

* __Is it fast?__
  Endpoints are synthesized in a local cache under `~/.jgo`.
  So invoking the same endpoint a second time is really quick.
* __What does "no installation" mean?__
  Classpath elements are [hard-linked](https://en.wikipedia.org/wiki/Hard_link)
  into `~/.jgo` from `~/.m2/repository` rather than copied, so the `~/.jgo`
  folder has a tiny footprint even if you execute lots of different endpoints.
* __What if an endpoint has a new version?__
  Pass the `-U` flag to `jgo` to rebuild the endpoint.
  Note that unlike `mvn`, though, `jgo` does not check for updates otherwise.

### Configuration

You can configure the behavior of `jgo` using a configuration file. The config file is searched in the following locations (in order of precedence):

1. `~/.config/jgo/config` (XDG Base Directory standard - recommended)
2. `~/.jgorc` (legacy location for backward compatibility)

#### Repositories

You can define additional remote Maven repositories,
from which artifacts will be retrieved. E.g.:

```ini
[repositories]
scijava.public = https://maven.scijava.org/content/groups/public
```

If you need more control over where artifacts come from—for example, if you
want to use your own remote Maven repository as a mirror of Maven Central—you
can do it using Maven's usual `~/.m2/settings.xml`; see [Using Mirrors for
Repositories](https://maven.apache.org/guides/mini/guide-mirror-settings.html).

You can also use the `-r` flag to pass additional repositories to individual
invocations of jgo.

#### Shortcuts

You can define shortcuts for launching commonly used programs:

```ini
[shortcuts]
repl = imagej:org.scijava.script.ScriptREPL
imagej = net.imagej:imagej
fiji = sc.fiji:fiji:LATEST
scifio = io.scif:scifio-cli
```

Shortcuts are substituted verbatim from the beginning of the endpoint,
single-pass in the order they are defined. So e.g. now you can run:
```shell
jgo repl
```
Note that with the `repl` shortcut above, the main class
(`org.scijava.script.ScriptREPL`) comes from a _different_ artifact than
the toplevel artifact (`net.imagej:imagej`). This is intentional, so that
all of [ImageJ](https://imagej.net/), including all of the various SciJava
`scripting-<foo>` plugins, is included in the classpath of the REPL.

#### Settings

There are a few configurable settings:

```ini
[settings]
m2Repo = /path/to/.m2Repo (default ~/.m2/repository)
cacheDir = /path/to/.jgo (default ~/.jgo)
links = soft (options: hard, soft, none; default hard)
```
The `jgo` cache dir can also be set via the `JGO_CACHE_DIR` environment
variable. The precedence of reading the cache dir, from highest to lowest:
  - `JGO_CACHE_DIR` environment variable
  - `cacheDir` in `settings` section in [config file](#configuration)
  - default to `~/.cache/jgo`

### Dependency management

#### How jgo handles dependency versions (important!)

Maven has a feature whereby a project can override the versions of transitive
(a.k.a. inherited) dependencies, via a `<dependencyManagement>` configuration.
The problem is: a library may believe it depends on components at particular
versions as defined by its `<dependencyManagement>`, but downstream projects
which depend on that library will resolve to **different versions**. This means
the library's actual dependencies differ from what it was built against!
See [this SO thread](https://stackoverflow.com/q/45041888/1207769) and
[this gist](https://gist.github.com/ctrueden/d058330c8a3687317806ce8cc18332c3)
for full details.

**By default, jgo works around this Maven limitation** by adding all endpoints to
the synthesized POM's `<dependencyManagement>` section using
[import scope](https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html#Importing_Dependencies).
This ensures that the versions of transitive dependencies match those that each
endpoint was actually built with, giving you the behavior you'd expect. In cases
where multiple endpoints are concatenated via the `+` operator with conflicting
dependency management, the earlier endpoints will win because they are declared
earlier in the POM.

If you need to disable this behavior (rare), you can use `--no-managed` to get
raw Maven transitive dependency resolution without the dependencyManagement
workaround. The `-m`/`--managed` flags are still supported for compatibility,
but managed mode is now the default.

See also [issue #9](https://github.com/apposed/jgo/issues/9) in the jgo issue
tracker for more discussion of this issue.

## Documentation

- **[User Guide](docs/user-guide.md)** - Comprehensive guide covering installation, CLI reference, Python API, and common recipes
- **[Migration Guide](docs/MIGRATION.md)** - Upgrading from jgo 1.x to 2.0
- **[Architecture](docs/architecture.md)** - Understanding the three-layer design
- **[API Reference](docs/)** - Use `help(jgo)` in Python for detailed API documentation
- **[TODO](TODO.md)** - Current development status and roadmap

## Development

### Code style

`jgo` uses [`black`](https://github.com/psf/black) for its code style.

After `pip install tox`, you can lint the code with:

```shell
tox -e lint
```

### Testing

```shell
# Run all tests
bin/test.sh

# Run specific test file
bin/test.sh tests/test_maven_basic.py

# Run with coverage
uv run pytest --cov=src/jgo tests/
```

## Alternatives

* [JBang](https://github.com/jbangdev/jbang)
* [mvnx](https://github.com/mvnx/mvnx)
* [JPM4J](https://github.com/jpm4j) (discontinued)
* [Mop](https://github.com/chirino/mop) (unmaintained)
* [marun](https://github.com/nishemon/marun) (unmaintained, Python 2 only)

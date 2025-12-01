[![build status](https://github.com/scijava/jgo/actions/workflows/build.yml/badge.svg)](https://github.com/scijava/jgo/actions/workflows/build.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# jgo: painless Java component execution

![](https://raw.githubusercontent.com/scijava/jgo/main/jgo.png)

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
jgo --print-classpath org.python:jython-standalone
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

### Prerequisites

`jgo` uses `mvn` and `java` for the heavy lifting.

There is a `jgo` console script, as well as a `jgo` module
for programmatically creating endpoints.

<details><summary><strong>Installing with pip</strong></summary>

```shell
pip install jgo
```

</details>
<details><summary><strong>Installing with conda</strong></summary>

```shell
conda install -c conda-forge jgo
```

</details>
<details><summary><strong>Installing from source</strong></summary>

```shell
git clone https://github.com/scijava/jgo
cd jgo

# install globally (not recommended unless using a virtual environment)
pip install .

# install into ~/.local (see pip install --help for details)
pip install --user .

# install into $PREFIX
pip install --prefix=$PREFIX .

# install globally in developer mode (hot linked to working copy folder)
pip install -e .
```

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
  --print-classpath       Print classpath and exit
  -f FILE                 Use jgo.toml file

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
`[repositories]` section of your `.jgorc`
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

You can configure the behavior of `jgo` using the `~/.jgorc` file.

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
  - `cacheDir` in `settings` sections in `~/.jgorc`
  - default to `~/.jgo`

### Pitfalls

#### Dependency management

Maven has a feature whereby a project can override the versions of transitive
(a.k.a. inherited) dependencies, via a `<dependencyManagement>` configuration.
The problem is: a library may then believe it depends on components at
particular versions as defined by its `<dependencyManagement>`, but downstream
projects which depend on that library will resolve to different versions.
See [this SO thread](https://stackoverflow.com/q/45041888/1207769) and
[this gist](https://gist.github.com/ctrueden/d058330c8a3687317806ce8cc18332c3)
for full details.

To work around this issue, you can pass `-m` to jgo, which
causes it to add all endpoints to the synthesized POM's
`<dependencyManagement>` section using
[import scope](https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html#Importing_Dependencies).
By doing this, the versions of transitive dependencies used in the synthesized
project should more precisely match those of each endpoint itself—although in
the case of multiple endpoints concatenated via the `+` operator with
conflicting dependency management, the earlier endpoints will win because they
will be declared earlier in the POM. See also
[issue #9](https://github.com/scijava/jgo/issues/9) in the jgo issue tracker.

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

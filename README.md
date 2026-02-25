[![build status](https://github.com/apposed/jgo/actions/workflows/build.yml/badge.svg)](https://github.com/apposed/jgo/actions/workflows/build.yml)
[![Documentation](https://readthedocs.org/projects/jgo/badge/?version=latest)](https://jgo.apposed.org/)

# jgo: painless Java environments and execution

![](https://raw.githubusercontent.com/apposed/jgo/main/jgo.png)

## Summary

`jgo` launches Java applications directly from Maven coordinates—no installation required. Specify a Maven artifact identifier and an optional main class, and `jgo` resolves dependencies, materializes the environment including the version of Java needed, and runs your program.

```bash
# Run Jython REPL (latest version)
jgo org.python:jython-standalone

# Run with specific version
jgo org.python:jython-standalone:2.7.3
```

### Features

- **Zero-configuration execution**: Automatic Java download and version management thanks to `cjdk` integration
- **Pure Python dependency resolver**: No Maven installation required to resolve dependency graphs
- **Reproducible environments**: `jgo.toml` project files with lock files (like `package.json` + `package-lock.json`)
- **Three-layer architecture**: Independently useful layers for Maven resolution, environment building, and execution
- **Powerful Python API**: Fine-grained control over dependency resolution and execution
- **Intelligent module handling**: Full support of the Java module system (JPMS), including
  intelligent classification of dependencies on module-path or class-path as appropriate

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

# Preview commands without executing (--dry-run)
jgo --dry-run run org.scijava:parsington         # See java command
jgo --dry-run init org.python:jython-standalone  # Preview jgo.toml
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

[repositories]
scijava.public = "https://maven.scijava.org/content/groups/public"

[dependencies]
coordinates = ["net.imagej:imagej:2.15.0"]

[entrypoints]
default = "main"
main = "net.imagej.Main"

[settings]
cache_dir = ".jgo"  # Local environment like .venv
```

```bash
# Run from current directory
jgo sync

# Creates .jgo/ with jars/ and jgo.lock.toml
```

## Installation

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

## Examples

| Program                      | Command                                                                             |
|-----------------------------:|:------------------------------------------------------------------------------------|
| Jython REPL                  | `jgo org.python:jython-standalone`                                                  |
| JRuby eval                   | `echo "puts 'Hello Ruby'" \| jgo org.jruby:jruby-complete@jruby.Main`              |
| Groovy REPL                  | `jgo org.codehaus.groovy:groovy-groovysh+commons-cli:commons-cli:1.3.1@shell.Main` |

Note the usage of the `+` syntax as needed to append elements to the classpath.

If you add
`scijava.public = https://maven.scijava.org/content/groups/public`
to the
`[repositories]` section of your settings file
(see the [configuration docs](https://jgo.apposed.org/en/latest/configuration.html)),
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
  Endpoints are synthesized in a local cache under `~/.cache/jgo`.
  So invoking the same endpoint a second time is really quick.
* __What does "no installation" mean?__
  Classpath elements are [hard-linked](https://en.wikipedia.org/wiki/Hard_link)
  into `~/.cache/jgo` from `~/.m2/repository` rather than copied, so the cache
  folder has a tiny footprint even if you execute lots of different endpoints.
* __What if an endpoint has a new version?__
  Pass the `-u` flag to `jgo` to rebuild the endpoint.
  Note that unlike `mvn`, `jgo` does not check for updates otherwise.

## Documentation

Full documentation is available at **[jgo.apposed.org](https://jgo.apposed.org/)**:

- **[Getting Started](https://jgo.apposed.org/en/latest/getting-started.html)** — Installation and quick start
- **[CLI Reference](https://jgo.apposed.org/en/latest/cli.html)** — All commands and options
- **[Project Mode](https://jgo.apposed.org/en/latest/project-mode.html)** — Working with `jgo.toml`
- **[Python API](https://jgo.apposed.org/en/latest/python-api.html)** — Using jgo from Python code
- **[Configuration](https://jgo.apposed.org/en/latest/configuration.html)** — Repositories, shortcuts, and settings
- **[Migration Guide](https://jgo.apposed.org/en/latest/migration.html)** — Upgrading from jgo 1.x
- **[Architecture](https://jgo.apposed.org/en/latest/architecture.html)** — The three-layer design

Use `help(jgo)` in Python for detailed API documentation.

## Development

### Code style

`jgo` uses [`ruff`](https://github.com/astral-sh/ruff) for linting and formatting:

```shell
make lint
```

### Testing

```shell
# Run all tests
make test

# Run specific test file
bin/test.sh tests/test_maven_basic.py

# Run with coverage
uv run pytest --cov=src/jgo tests/
```

## Alternatives

* [JBang](https://github.com/jbangdev/jbang)
* [mvnx](https://github.com/mvnx/mvnx) (unmaintained)
* [JPM4J](https://github.com/jpm4j) (discontinued)
* [Mop](https://github.com/chirino/mop) (unmaintained)
* [marun](https://github.com/nishemon/marun) (unmaintained, Python 2 only)

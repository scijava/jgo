# jgo: painless Java component execution

```{image} ../jgo.png
:alt: jgo logo
:width: 200px
:align: center
```

**jgo** launches Java applications directly from [Maven](https://maven.apache.org/) coordinates -- no installation required. Specify an artifact and an optional main class, and jgo resolves dependencies, downloads the right version of Java, and runs your program.

```bash
# Run Jython REPL -- no Java or Maven installation needed
jgo org.python:jython-standalone

# Run a specific version
jgo org.python:jython-standalone:2.7.3
```

## What's New in 2.0

- **Zero-configuration execution** -- Automatic Java download and version management via [cjdk](https://github.com/cachedjdk/cjdk) integration
- **Reproducible environments** -- `jgo.toml` project files with lock files (like `package.json` + `package-lock.json`)
- **Three-layer architecture** -- Independently useful layers for Maven resolution, environment building, and execution
- **Pure Python resolver** -- No Maven installation required for basic operations
- **Powerful Python API** -- Fine-grained control over dependency resolution and execution

## Documentation

```{toctree}
:maxdepth: 2
:caption: User Guide

getting-started
cli
project-mode
python-api
configuration
```

```{toctree}
:maxdepth: 2
:caption: Topics

dependency-management
recipes
```

```{toctree}
:maxdepth: 2
:caption: Reference

migration
architecture
changelog
```

```{toctree}
:maxdepth: 1
:caption: Development
:hidden:

design/index
future
GitHub <https://github.com/apposed/jgo>
Issue Tracker <https://github.com/apposed/jgo/issues>
```

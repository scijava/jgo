# jgo: painless Java environments and execution

```{image} ../jgo.png
:alt: jgo in action
```

**jgo** launches Java applications directly from [Maven](https://maven.apache.org/) coordinates—no installation required. Specify an artifact identifier and an optional main class, and `jgo` resolves dependencies, materializes the environment including the version of Java needed, and runs your program.

```bash
# Run Jython REPL -- no Java or Maven installation needed
jgo org.python:jython-standalone

# Run a specific version
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

future
GitHub <https://github.com/apposed/jgo>
Issue Tracker <https://github.com/apposed/jgo/issues>
```

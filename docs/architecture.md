# Architecture

jgo 2.0 is built around a three-layer architecture. Each layer is independently useful and can be used separately or combined.

```
┌──────────────────────────────────────┐
│  High-Level API (jgo.run())          │
└──────────────────────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
┌─────────────┐ ┌─────────────────┐
│ Maven       │ │ Environment     │
│ Resolution  │→│ Materialization │
└─────────────┘ └─────────────────┘
                        │
                        ▼
                ┌───────────────┐
                │  Execution    │
                └───────────────┘
```

## Layer 1: Maven (`jgo.maven`)

**Purpose:** Resolve Maven dependencies using pure Python -- no Maven installation required.

### Concepts

```
Project (groupId:artifactId)
  └─> Component (groupId:artifactId:version)
        └─> Artifact (groupId:artifactId:packaging:classifier:version)
              └─> Dependency (Artifact + scope + exclusions)
```

- **Project** -- a Maven project identified by groupId and artifactId (e.g., `org.python:jython-standalone`).
- **Component** -- a project at a specific version (e.g., `org.python:jython-standalone:2.7.3`).
- **Artifact** -- a component with packaging and classifier (e.g., `jar`, `natives-linux`).
- **Dependency** -- an artifact with metadata: scope, optional flag, exclusions.

### Resolvers

| Resolver | Requires | Use case |
|:---------|:---------|:---------|
| `PythonResolver` | Nothing | Default. Parses POMs, resolves transitive dependencies, handles BOMs and exclusions. |
| `MvnResolver` | `mvn` on PATH | Fallback for edge cases. Handles all Maven features including plugins. |
| Auto (default) | Nothing | Tries `PythonResolver` first, falls back to `MvnResolver`. |

### Standalone use

Use `jgo.maven` on its own for dependency analysis, POM parsing, or version resolution:

```python
from jgo.maven import MavenContext

maven = MavenContext()
component = maven.project("org.example", "mylib").at_version("1.0.0")
model = component.model()
deps, root = model.dependencies()

for dep in deps:
    print(f"{dep.groupId}:{dep.artifactId}:{dep.version} ({dep.scope})")
```

## Layer 2: Environment (`jgo.env`)

**Purpose:** Materialize Maven dependencies into directories of JARs, analogous to Python virtualenvs.

### Environment structure

```
~/.cache/jgo/org/python/jython-standalone/<hash>/
├── jars/                      # Materialized JAR files
│   ├── jython-standalone-2.7.3.jar
│   └── ...
├── jgo.toml                   # Environment spec
└── jgo.lock.toml              # Locked versions
```

### Link strategies

| Strategy | Disk overhead | Cross-filesystem |
|:---------|:--------------|:-----------------|
| Hard (default) | None | No |
| Soft | None | Yes |
| Copy | Full | Yes |
| Auto | None | Yes (tries hard → soft → copy) |

### Cache modes

**Ad-hoc mode** (default): Environments cached in `~/.cache/jgo/<hash>/` for one-off executions.

**Project mode** (with `jgo.toml`): Environment built in `.jgo/` in the project directory, with a lock file for reproducibility.

### Bytecode detection

Environments automatically detect the minimum Java version from `.class` file bytecode. This enables zero-configuration execution: jgo knows which Java version to download without any user input.

### Standalone use

Use `jgo.env` for IDE classpath generation, Docker image building, or dependency auditing:

```python
import jgo

env = jgo.build("org.example:myapp")
classpath = ":".join(str(p) for p in env.classpath)
```

## Layer 3: Execution (`jgo.exec`)

**Purpose:** Launch Java programs with configured JVM settings and automatic Java version management.

### Java source strategies

| Strategy | Description |
|:---------|:------------|
| `AUTO` (default) | Detects the environment's minimum Java version and downloads the right version via [cjdk](https://github.com/cachedjdk/cjdk). |
| `SYSTEM` | Uses Java from `PATH` or `JAVA_HOME`. Requires pre-installed Java. |

### Standalone use

Use `jgo.exec` with your own classpath or environment for custom JVM tuning:

```python
from jgo.exec import JavaRunner, JVMConfig, JavaSource

runner = JavaRunner(
    jvm_config=JVMConfig(max_heap="16G", gc_options=["-XX:+UseZGC"]),
    java_source=JavaSource.AUTO,
    java_version=17,
)
runner.run(environment, main_class="org.example.Main")
```

## Module structure

```
jgo/
├── __init__.py           # High-level API: run(), build(), resolve()
├── maven/                # Layer 1: Maven resolution
│   ├── _core.py          #   MavenContext, Project, Component, Artifact
│   ├── _resolver.py      #   PythonResolver, MvnResolver
│   ├── _model.py         #   Dependency resolution logic
│   ├── _pom.py           #   POM parsing
│   ├── _metadata.py      #   maven-metadata.xml parsing
│   └── _version.py       #   Version comparison utilities
├── env/                  # Layer 2: Environment materialization
│   ├── _environment.py   #   Environment class
│   ├── _builder.py       #   EnvironmentBuilder
│   ├── _linking.py       #   Link strategies
│   ├── _spec.py          #   jgo.toml parser
│   ├── _lockfile.py      #   jgo.lock.toml generator
│   └── _bytecode.py      #   Java version detection from bytecode
├── exec/                 # Layer 3: Execution
│   ├── _runner.py        #   JavaRunner
│   └── _config.py        #   JVMConfig
├── cli/                  # Command-line interface
│   ├── _commands/        #   One module per CLI command
│   └── rich/             #   Rich formatting, logging, progress
├── config/               # Configuration management
├── parse/                # Coordinate and endpoint parsing
└── util/                 # Shared utilities
```

## Design principles

**Modularity**
: Each layer is independently useful. Use the Maven layer for dependency analysis without execution, the Environment layer for IDE integration without running, or the Execution layer for custom Java launching.

**No external dependencies (core)**
: The Maven layer is pure Python. No Maven, Gradle, or Java installation is required for dependency resolution. This makes jgo suitable for CI/CD pipelines and restricted environments.

**Testability**
: Each layer is tested in isolation: POM parsing, JAR linking, JVM configuration.

**Flexibility**
: Mix and match components: choose your resolver, link strategy, and Java source strategy independently.

## Comparison to jgo 1.x

jgo 1.x was a single monolithic module (`jgo.jgo`) that handled dependency resolution, JAR linking, and Java execution in one tightly coupled file. jgo 2.0 separates these concerns into distinct layers with clean interfaces, making the codebase more maintainable, testable, and extensible.

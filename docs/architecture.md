# jgo 2.0 Architecture

## Overview

jgo 2.0 is built around a clean three-layer architecture, where each layer is independently useful and can be used separately or combined:

1. **Maven Layer** (`jgo.maven`) - Pure dependency resolution
2. **Environment Layer** (`jgo.env`) - Environment materialization
3. **Execution Layer** (`jgo.exec`) - Java program launching

This design makes jgo modular, testable, and extensible while eliminating the monolithic approach of jgo 1.x.

## Layer 1: Maven Layer (`jgo.maven`)

**Purpose**: Resolve Maven dependencies without running Java or Maven.

### Key Classes

```python
from jgo.maven import MavenContext, PythonResolver, MvnResolver

# Maven configuration
maven = MavenContext(
    repo_cache=Path("~/.m2/repository"),
    remote_repos={"central": "https://repo.maven.apache.org/maven2"},
    resolver=PythonResolver()  # Pure Python, no mvn needed
)

# Access projects
project = maven.project("org.python", "jython-standalone")
component = project.at_version("2.7.3")
```

### Maven Concepts Hierarchy

```
Project (G:A)
  └─> Component (G:A:V)
        └─> Artifact (G:A:P:C:V)
              └─> Dependency (Artifact + scope + exclusions)
```

- **Project**: groupId + artifactId (e.g., `org.python:jython-standalone`)
- **Component**: Project at a specific version (e.g., `org.python:jython-standalone:2.7.3`)
- **Artifact**: Component with packaging and classifier (e.g., `jar`, `natives-linux`)
- **Dependency**: Artifact with metadata (scope, optional, exclusions)

### Resolvers

**PythonResolver** (Pure Python):
- No external dependencies
- Parses POM files directly
- Handles transitive dependencies
- Property interpolation
- Dependency management (BOMs)
- Exclusions and scopes
- Downloads from Maven repositories

**MvnResolver** (Shells out to mvn):
- Falls back when pure Python resolver can't handle edge cases
- Uses system Maven installation
- Handles all Maven features

**Auto Resolver**:
- Tries PythonResolver first
- Falls back to MvnResolver if needed

### Use Cases

**Standalone Maven resolution**:

```python
from jgo.maven import MavenContext

maven = MavenContext()
component = maven.project("org.example", "mylib").at_version("1.0.0")
model = component.model()
deps, root = model.dependencies()

for dep in deps:
    print(f"{dep.groupId}:{dep.artifactId}:{dep.version} ({dep.scope})")
```

**Other tools** can use `jgo.maven` for:
- Dependency analysis
- POM parsing
- Version resolution
- Artifact downloading

## Layer 2: Environment Layer (`jgo.env`)

**Purpose**: Materialize Maven dependencies into executable environments (directories of JARs).

### Key Classes

```python
from jgo.env import Environment, EnvironmentBuilder, LinkStrategy

# Build environment
builder = EnvironmentBuilder(
    context=maven,
    link_strategy=LinkStrategy.HARD
)

environment = builder.from_endpoint("org.python:jython-standalone:2.7.3")
```

### Environment Structure

An environment is a directory containing:

```
~/.cache/jgo/org/python/jython-standalone/<hash>/
  ├─ jars/                      # Materialized JAR files
  │   ├─ jython-standalone-2.7.3.jar
  │   └─ ...
  ├─ jgo.toml                   # Environment spec
  └─ jgo.lock.toml              # Metadata with locked versions
```

### Link Strategies

**Hard Links** (default on Unix):
- Creates hard links from `~/.m2/repository` to environment
- Zero disk space overhead
- Fast
- Requires same filesystem

**Soft Links**:
- Creates symbolic links
- Works across filesystems
- Requires symlink support

**Copy**:
- Copies JAR files
- Works everywhere
- Uses disk space

**Auto**:
- Tries hard → soft → copy

### Cache Modes

**Ad-hoc Mode** (default):
```python
# Uses ~/.cache/jgo/<hash>/ for one-off executions
builder = EnvironmentBuilder(context=maven)
env = builder.from_endpoint("org.python:jython-standalone")
```

**Project Mode** (with jgo.toml):
```python
# Uses .jgo/ in current directory
spec = EnvironmentSpec.load("jgo.toml")
builder = EnvironmentBuilder(context=maven, cache_dir=Path(".jgo"))
env = builder.from_spec(spec)
```

### Bytecode Detection

Environments automatically detect minimum Java version:

```python
environment = builder.from_endpoint("net.imagej:imagej")
print(environment.min_java_version)  # 17 (detected from .class files)
```

This enables zero-configuration execution with the Execution Layer.

### Use Cases

**IDE classpath generation**:
```python
env = jgo.build("org.example:myapp")
classpath = ":".join(str(p) for p in env.classpath)
# Use in IDE configuration
```

**Docker image building**:
```python
spec = EnvironmentSpec.load("jgo.toml")
env = builder.from_spec(spec)
# Copy env.classpath JARs into Docker image
```

**Dependency auditing**:
```python
env = jgo.build("org.example:myapp")
for jar in env.classpath:
    print(f"Checking {jar.name} for vulnerabilities...")
```

## Layer 3: Execution Layer (`jgo.exec`)

**Purpose**: Launch Java programs with configured JVM settings.

### Key Classes

```python
from jgo.exec import JavaRunner, JVMConfig, JavaSource

# Configure JVM
jvm_config = JVMConfig(
    max_heap="4G",
    gc_options=["-XX:+UseG1GC"],
    system_properties={"foo": "bar"}
)

# Run program
runner = JavaRunner(
    jvm_config=jvm_config,
    java_source=JavaSource.AUTO  # Auto-download Java if needed
)

result = runner.run(
    environment=environment,
    main_class="org.example.Main",
    app_args=["--help"]
)
```

### Java Source Strategies

**SYSTEM**:
- Uses Java from `PATH` or `JAVA_HOME`
- Lightweight, no extra dependencies
- Requires pre-installed Java

**AUTO**:
- Detects environment's `min_java_version`
- Automatically fetches/downloads Java if needed
- Supports version and vendor selection

### Zero-Configuration Execution

```python
import jgo

# User doesn't need Java installed!
# Detects requirement → downloads correct Java version → runs
jgo.run("net.imagej:imagej")

# Output:
# INFO: Detected minimum Java version: 17
# INFO: Locating Java 17...
# INFO: Using Java 17.0.9 (Adoptium)
# [ImageJ launches]
```

### Use Cases

**Testing different Java versions**:
```python
from jgo.exec import JavaRunner, JavaSource

runner = JavaRunner(
    java_source=JavaSource.AUTO,
    java_version="11"
)
runner.run(env)  # Test with Java 11

runner = JavaRunner(java_version="17")
runner.run(env)  # Test with Java 17
```

**Custom JVM tuning**:
```python
from jgo.exec import JVMConfig

config = JVMConfig(
    max_heap="16G",
    gc_options=[
        "-XX:+UseZGC",
        "-XX:ConcGCThreads=4"
    ],
    system_properties={
        "java.awt.headless": "true",
        "user.timezone": "UTC"
    }
)
```

## Integration: The Three Layers Working Together

### High-Level API

The `jgo` module provides convenience functions that chain all three layers:

```python
import jgo

# One-liner that uses all three layers
jgo.run("org.python:jython-standalone:2.7.3", app_args=["script.py"])

# Internally:
# 1. Maven Layer: Resolve dependencies
# 2. Environment Layer: Materialize JARs
# 3. Execution Layer: Launch Java
```

### Manual Integration

For fine-grained control:

```python
from jgo.maven import MavenContext, PythonResolver
from jgo.env import EnvironmentBuilder, LinkStrategy
from jgo.exec import JavaRunner, JVMConfig, JavaSource

# Layer 1: Configure Maven
maven = MavenContext(
    resolver=PythonResolver(),
    remote_repos={
        "central": "https://repo.maven.apache.org/maven2",
        "scijava": "https://maven.scijava.org/content/groups/public"
    }
)

# Layer 2: Build environment
builder = EnvironmentBuilder(
    context=maven,
    link_strategy=LinkStrategy.HARD,
    cache_dir=Path(".jgo")  # Project-local
)

spec = EnvironmentSpec.load("jgo.toml")
environment = builder.from_spec(spec)

# Layer 3: Execute with custom configuration
jvm_config = JVMConfig(
    max_heap="8G",
    gc_options=["-XX:+UseG1GC"],
    system_properties={"app.mode": "production"}
)

runner = JavaRunner(
    jvm_config=jvm_config,
    java_source=JavaSource.AUTO,
    java_version="17",
    java_vendor="adoptium"
)

result = runner.run(
    environment=environment,
    main_class=spec.get_main_class("default"),
    app_args=["--config", "prod.yml"]
)
```

## Design Principles

### 1. Modularity

Each layer is independently useful:
- Use Maven layer for dependency analysis without execution
- Use Environment layer for IDE integration without running
- Use Execution layer for custom Java launching

### 2. Testability

Each layer can be tested in isolation:
- Maven layer: Test POM parsing, dependency resolution
- Environment layer: Test JAR linking, caching
- Execution layer: Test JVM configuration, Java detection

### 3. Flexibility

Mix and match components:
- Use PythonResolver or MvnResolver
- Use hard links or copies
- Use auto or system Java

### 4. No External Dependencies (Core)

The Maven layer is pure Python with no external tools required. This makes jgo suitable for:
- Embedded systems
- Restricted environments
- CI/CD pipelines (no Maven installation needed)

### 5. Extensibility

Easy to add new features:
- New resolvers (conda, Gradle)
- New link strategies
- New Java sources (GraalVM, custom distributions)

## Comparison to jgo 1.x

### jgo 1.x (Monolithic)

```
┌─────────────────────────────┐
│                             │
│      jgo.jgo (big file)     │
│                             │
│  - Dependency resolution    │
│  - JAR linking              │
│  - Java execution           │
│  - All tightly coupled      │
│                             │
└─────────────────────────────┘
```

### jgo 2.0 (Layered)

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

**Benefits of layered design**:
- Each layer independently testable
- Can use layers separately
- Clear separation of concerns
- Easy to extend each layer
- Better error messages (clear which layer failed)

## Module Structure

```
jgo/
  ├─ __init__.py           # High-level API: run(), build(), resolve()
  ├─ maven/                # Layer 1: Maven resolution
  │   ├─ core.py           # MavenContext, Project, Component, Artifact
  │   ├─ resolver.py       # PythonResolver, MvnResolver
  │   ├─ model.py          # Dependency resolution logic
  │   ├─ pom.py            # POM parsing
  │   └─ metadata.py       # maven-metadata.xml parsing
  ├─ env/                  # Layer 2: Environment materialization
  │   ├─ environment.py    # Environment class
  │   ├─ builder.py        # EnvironmentBuilder
  │   ├─ linking.py        # Link strategies
  │   ├─ spec.py           # jgo.toml parser
  │   ├─ lockfile.py       # jgo.lock.toml generator
  │   └─ bytecode.py       # Java version detection
  ├─ exec/                 # Layer 3: Execution
  │   ├─ runner.py         # JavaRunner
  │   ├─ config.py         # JVMConfig
  │   └─ java_source.py    # JavaLocator, auto Java management
  ├─ cli/                  # Command-line interface
  │   ├─ parser.py         # Argument parsing
  │   └─ commands.py       # CLI commands
  ├─ config/               # Configuration
  │   └─ settings.py       # Global settings parsing
  └─ compat/               # Backward compatibility
      └─ v1.py             # jgo 1.x compatibility layer
```

## Future Architecture Extensions

Possible future additions (post-2.0.0):

### Conda Integration
```python
from jgo.maven import CondaResolver  # New resolver

maven = MavenContext(resolver=CondaResolver())
# Resolves from conda-forge in addition to Maven Central
```

### Docker Support
```python
from jgo.env import DockerBuilder  # New builder

builder = DockerBuilder(context=maven)
docker_image = builder.from_spec(spec)
# Generates Dockerfile and builds image
```

### Plugin System
```python
from jgo.maven import CustomResolver

class MyResolver(CustomResolver):
    def resolve(self, component):
        # Custom resolution logic
        pass
```

## Summary

The three-layer architecture makes jgo 2.0:
- **Modular**: Each layer independently useful
- **Testable**: Each layer tested in isolation
- **Flexible**: Mix and match components
- **Extensible**: Easy to add new features
- **Clean**: Clear separation of concerns

For most users, the high-level API (`jgo.run()`) is sufficient. Power users can leverage individual layers for custom workflows.

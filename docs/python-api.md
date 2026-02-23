# Python API

jgo provides a Python API at two levels: a simple high-level API for common tasks, and a layered API for fine-grained control.

## High-level API

The `jgo` module exports three main functions:

### `jgo.run()`

Run a Java application from a Maven endpoint.

```python
import jgo

result = jgo.run(
    "org.python:jython-standalone:2.7.3",
    app_args=["script.py"],
    jvm_args=["-Xmx2G"],
)
print(result.returncode)
```

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `endpoint` | `str` | Maven endpoint (e.g., `"org.python:jython-standalone:2.7.3"`) |
| `app_args` | `list[str]` | Arguments passed to the Java application |
| `jvm_args` | `list[str]` | JVM arguments (e.g., `["-Xmx2G"]`) |
| `main_class` | `str` | Main class to run (auto-detected if omitted) |
| `update` | `bool` | Force update of cached environment |
| `verbose` | `bool` | Enable verbose output |
| `cache_dir` | `Path` | Override cache directory |
| `repositories` | `dict[str, str]` | Additional Maven repositories (`name` -> `URL`) |
| `java_version` | `int` | Force specific Java version |
| `java_vendor` | `str` | Prefer specific Java vendor |
| `java_source` | `str` | `"auto"` (download if needed) or `"system"` (use installed Java) |

**Returns:** `subprocess.CompletedProcess`

### `jgo.build()`

Build an environment without running it. Useful for getting the classpath or inspecting resolved dependencies.

```python
import jgo

env = jgo.build("org.python:jython-standalone:2.7.3")
print(env.classpath)    # List of Path objects
print(env.main_class)   # Detected main class
print(env.path)         # Environment directory
```

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `endpoint` | `str` | Maven endpoint |
| `update` | `bool` | Force update of cached environment |
| `cache_dir` | `Path` | Override cache directory |
| `repositories` | `dict[str, str]` | Additional Maven repositories |

**Returns:** `Environment`

### `jgo.resolve()`

Resolve dependencies to a list of Maven components without materializing JARs.

```python
import jgo

components = jgo.resolve("org.python:jython-standalone:2.7.3")
for comp in components:
    print(f"{comp.groupId}:{comp.artifactId}:{comp.version}")
```

**Parameters:**

| Parameter | Type | Description |
|:----------|:-----|:------------|
| `endpoint` | `str` | Maven endpoint |
| `repositories` | `dict[str, str]` | Additional Maven repositories |

**Returns:** `list[Artifact]`

## Layered API

For fine-grained control, use the three-layer architecture directly. Each layer is independently useful.

### Layer 1: Maven resolution (`jgo.maven`)

Resolve Maven dependencies using pure Python -- no Maven installation required.

```python
from jgo.maven import MavenContext, PythonResolver

# Configure Maven access
maven = MavenContext(
    resolver=PythonResolver(),
    remote_repos={
        "central": "https://repo.maven.apache.org/maven2",
        "scijava": "https://maven.scijava.org/content/groups/public",
    },
)

# Access a project
project = maven.project("org.python", "jython-standalone")
component = project.at_version("2.7.3")

# Get the dependency model
model = component.model()
deps, root = model.dependencies()

for dep in deps:
    print(f"{dep.groupId}:{dep.artifactId}:{dep.version} ({dep.scope})")
```

**Key classes:**

`MavenContext`
: Maven configuration: repository locations, resolver strategy, remote repositories.

`PythonResolver`
: Pure Python resolver. Parses POM files directly, handles transitive dependencies, property interpolation, dependency management (BOMs), exclusions, and scopes.

`MvnResolver`
: Shells out to the system `mvn` command. Use as a fallback for edge cases.

`Project`
: A Maven project identified by `groupId:artifactId`.

`Component`
: A project at a specific version (`groupId:artifactId:version`).

`Dependency`
: An artifact with scope, optional flag, and exclusions.

### Layer 2: Environment materialization (`jgo.env`)

Materialize Maven dependencies into a directory of JARs.

```python
from jgo.maven import MavenContext
from jgo.env import EnvironmentBuilder, LinkStrategy

maven = MavenContext()
builder = EnvironmentBuilder(
    context=maven,
    link_strategy=LinkStrategy.HARD,
)

env = builder.from_endpoint("org.python:jython-standalone:2.7.3")
print(env.path)         # Environment directory
print(env.classpath)    # List of JAR paths
print(env.main_class)   # Detected main class
```

**Key classes:**

`EnvironmentBuilder`
: Builds environments from endpoint strings or `jgo.toml` specs.
  - `from_endpoint(endpoint, update=False, main_class=None)` -- build from a Maven coordinate string.
  - `from_spec(spec)` -- build from an `EnvironmentSpec` (parsed `jgo.toml`).

`Environment`
: A materialized directory of JARs, analogous to a Python virtualenv.

`EnvironmentSpec`
: Parsed `jgo.toml` file.
  - `EnvironmentSpec.load("jgo.toml")` -- load from file.

`LinkStrategy`
: How JARs are placed in the environment directory.
  - `HARD` -- hard links (zero disk overhead, default on Unix).
  - `SOFT` -- symbolic links.
  - `COPY` -- file copies.
  - `AUTO` -- try hard, then soft, then copy.

### Layer 3: Execution (`jgo.exec`)

Launch Java programs with configured JVM settings.

```python
from jgo.exec import JavaRunner, JVMConfig, JavaSource

jvm_config = JVMConfig(
    max_heap="4G",
    gc_options=["-XX:+UseG1GC"],
    system_properties={"foo": "bar"},
)

runner = JavaRunner(
    jvm_config=jvm_config,
    java_source=JavaSource.AUTO,  # Download Java if needed
    java_version=17,
)

result = runner.run(
    environment=env,
    main_class="org.example.Main",
    app_args=["--help"],
)
```

**Key classes:**

`JavaRunner`
: Executes Java programs from an `Environment`.

`JVMConfig`
: JVM settings: heap sizes, GC options, system properties.

`JavaSource`
: How to find Java.
  - `AUTO` -- detect version from bytecode, download if needed.
  - `SYSTEM` -- use Java from `PATH` or `JAVA_HOME`.

### Combining layers

A complete example using all three layers:

```python
from pathlib import Path
from jgo.maven import MavenContext, PythonResolver
from jgo.env import EnvironmentBuilder, EnvironmentSpec, LinkStrategy
from jgo.exec import JavaRunner, JVMConfig, JavaSource

# Layer 1: Configure Maven
maven = MavenContext(
    resolver=PythonResolver(),
    remote_repos={
        "central": "https://repo.maven.apache.org/maven2",
        "scijava": "https://maven.scijava.org/content/groups/public",
    },
)

# Layer 2: Build environment from jgo.toml
spec = EnvironmentSpec.load("jgo.toml")
builder = EnvironmentBuilder(
    context=maven,
    link_strategy=LinkStrategy.HARD,
    cache_dir=Path(".jgo"),
)
environment = builder.from_spec(spec)

# Layer 3: Run with custom JVM settings
runner = JavaRunner(
    jvm_config=JVMConfig(max_heap="8G"),
    java_source=JavaSource.AUTO,
    java_version=17,
)
result = runner.run(
    environment=environment,
    main_class=spec.get_main_class("default"),
    app_args=["--config", "prod.yml"],
)
```

## Backward compatibility

jgo 1.x APIs still work but emit deprecation warnings:

| Old API | New API |
|:--------|:--------|
| `jgo.main(argv)` | `jgo.run(endpoint, ...)` |
| `jgo.main_from_endpoint(ep, ...)` | `jgo.run(endpoint, ...)` |
| `jgo.resolve_dependencies(ep, ...)` | `jgo.resolve(endpoint, ...)` |

These deprecated functions will be removed in jgo 3.0. See {doc}`migration` for details.

# jgo 2.0 Terminology Guide

## Official Terminology

This document defines the official terminology for jgo 2.0 to ensure consistency across code, documentation, and discussions.

## Core Concepts

### MavenContext
**What it is:** Maven configuration object containing repository settings, cache locations, and resolution strategy.

**Module:** `jgo.maven.MavenContext`

**Attributes:**
- `repo_cache` - Path to local Maven repository cache (~/.m2/repository)
- `local_repos` - List of local Maven repository storage directories
- `remote_repos` - Dict of remote repository name:URL pairs
- `resolver` - Resolver instance (SimpleResolver or MavenResolver)

**Usage:**
```python
from jgo.maven import MavenContext, SimpleResolver

maven = MavenContext(
    repo_cache=Path("~/.m2/repository"),
    remote_repos={"central": "https://repo.maven.apache.org/maven2"},
    resolver=SimpleResolver()
)

# Use it to access Maven projects
project = maven.project("org.python", "jython-standalone")
```

**Avoid:** Calling this "Environment" (reserved for materialized directories)

---

### Environment
**What it is:** A materialized directory containing JAR files ready for execution—analogous to Python's virtualenv or conda environment.

**Module:** `jgo.env.Environment`

**Attributes:**
- `path` - Path to the environment directory
- `classpath` - List of JAR file paths in the environment
- `main_class` - Detected or specified main class
- `manifest` - Metadata about this environment

**Usage:**
```python
from jgo.env import EnvironmentBuilder

builder = EnvironmentBuilder(context=maven)
env = builder.from_endpoint("org.python:jython-standalone:2.7.3")

print(env.path)       # /home/user/.jgo/org/python/jython-standalone/abc123
print(env.classpath)  # [Path('/home/user/.jgo/.../jython-standalone-2.7.3.jar')]
print(env.main_class) # org.python.util.jython
```

**Avoid:** Calling this "Workspace" (deprecated term)

---

### EnvironmentBuilder
**What it is:** Builds Environment instances from Maven components or endpoint strings.

**Module:** `jgo.env.EnvironmentBuilder`

**Methods:**
- `from_endpoint(endpoint: str)` - Build from endpoint string (e.g., "G:A:V")
- `from_components(components: list[Component])` - Build from Component objects

**Usage:**
```python
from jgo.env import EnvironmentBuilder, LinkStrategy

builder = EnvironmentBuilder(
    context=maven,
    cache_dir=Path("~/.jgo"),
    link_strategy=LinkStrategy.HARD
)

env = builder.from_endpoint("org.python:jython-standalone:2.7.3")
```

**Avoid:** Calling this "WorkspaceBuilder" (deprecated term)

---

## Maven Layer Concepts

### Project
**What it is:** A Maven project identified by groupId:artifactId (G:A)

**Example:** `org.python:jython-standalone`

### Component
**What it is:** A Project at a specific version (G:A:V)

**Example:** `org.python:jython-standalone:2.7.3`

### Artifact
**What it is:** A Component with specific packaging and classifier (G:A:P:C:V)

**Example:** `org.python:jython-standalone:jar::2.7.3` (main JAR)
**Example:** `org.lwjgl:lwjgl:jar:natives-linux:3.3.1` (native JAR)

### Dependency
**What it is:** An Artifact with scope, optional flag, and exclusions

**Scopes:** compile, runtime, test, provided, system, import

---

## Deprecated Terms

These terms should **NOT** be used in jgo 2.0:

### ❌ "Workspace"
**Why deprecated:** Ambiguous—could mean IDE workspace, build workspace, etc.

**Use instead:** "Environment" for materialized JAR directories

### ❌ "Environment" (for Maven config)
**Why deprecated:** Creates confusion with materialized environments

**Use instead:** "MavenContext" for Maven configuration

### ❌ "WorkspaceBuilder"
**Why deprecated:** Builds environments, not workspaces

**Use instead:** "EnvironmentBuilder"

---

## Consistent Usage Patterns

### Talking About the Three Layers

✅ **Correct:**
- "Layer 1: Maven Layer - dependency resolution using MavenContext"
- "Layer 2: Environment Layer - materializing JARs into environments"
- "Layer 3: Execution Layer - running Java programs"

❌ **Incorrect:**
- "Layer 2: Workspace Layer"
- "Using Environment to configure Maven"

### Code Examples

✅ **Correct:**
```python
# Layer 1: Create Maven context
maven = MavenContext()

# Layer 2: Build environment
builder = EnvironmentBuilder(context=maven)
env = builder.from_endpoint("G:A:V")

# Layer 3: Run program
runner = JavaRunner()
runner.run(env)
```

❌ **Incorrect:**
```python
# Don't mix terminology
maven_env = Environment()  # Wrong! Use MavenContext
workspace = builder.build()  # Wrong! Returns Environment
```

### CLI/Documentation

✅ **Correct:**
- "jgo builds environments in ~/.jgo"
- "Configure Maven repositories in your MavenContext"
- "The environment contains all dependencies"

❌ **Incorrect:**
- "jgo builds workspaces"
- "The Maven environment configuration"

---

## Quick Reference

| Concept | Class | Module | Purpose |
|---------|-------|--------|---------|
| Maven configuration | `MavenContext` | `jgo.maven` | Repos, cache, resolver |
| Materialized JARs | `Environment` | `jgo.env` | Directory with classpath |
| Build environments | `EnvironmentBuilder` | `jgo.env` | Create environments |
| Maven project | `Project` | `jgo.maven` | G:A |
| Versioned component | `Component` | `jgo.maven` | G:A:V |
| Packaged artifact | `Artifact` | `jgo.maven` | G:A:P:C:V |
| With metadata | `Dependency` | `jgo.maven` | Artifact + scope + ... |

---

## Analogy to Help Remember

Think of it like Python package management:

| Python Concept | jgo 2.0 Equivalent |
|----------------|-------------------|
| pip configuration (~/.pip/pip.conf) | MavenContext |
| virtualenv directory | Environment |
| `python -m venv` | EnvironmentBuilder |
| PyPI | Maven Central |
| package name | Project (G:A) |
| package==1.0.0 | Component (G:A:V) |

---

## Summary

- **MavenContext** = Maven configuration and settings
- **Environment** = Materialized directory of JARs (like virtualenv)
- **EnvironmentBuilder** = Tool to create environments

Use these terms consistently in:
- Code (class names, variable names)
- Documentation (user guides, API docs)
- Discussions (issues, PRs, planning)
- Comments (inline code comments)

When in doubt: If it's about configuration → **MavenContext**. If it's about materialized JARs → **Environment**.

# jgo 2.0 Migration Examples

This document shows concrete before/after examples for migrating from jgo 1.x to 2.0.

## Python API Migration

### Example 1: Simple Program Execution

**jgo 1.x:**
```python
from jgo import jgo

# Run with defaults
jgo._jgo_main(['org.python:jython-standalone'])
```

**jgo 2.x (Simple):**
```python
import jgo

# High-level API - simple and clear
jgo.run('org.python:jython-standalone')
```

**jgo 2.x (Layered):**
```python
from jgo.maven import MavenContext
from jgo.env import EnvironmentBuilder
from jgo.exec import JavaRunner

# Full control over each step
maven = MavenContext()
component = maven.project('org.python', 'jython-standalone').at_version('RELEASE')

builder = EnvironmentBuilder(context=maven)
environment = builder.from_components([component])

runner = JavaRunner()
result = runner.run(environment)
```

### Example 2: Custom Configuration

**jgo 1.x:**
```python
from jgo.util import main_from_endpoint

main_from_endpoint(
    'org.scijava:scijava-common',
    primary_endpoint_version='2.96.0',
    primary_endpoint_main_class='org.scijava.script.ScriptREPL',
    secondary_endpoints=('org.scijava:scripting-jython',),
    repositories={'scijava.public': 'https://maven.scijava.org/content/groups/public'},
    argv=['--verbose']
)
```

**jgo 2.x:**
```python
import jgo

result = jgo.run(
    endpoint='org.scijava:scijava-common:2.96.0:org.scijava.script.ScriptREPL+org.scijava:scripting-jython',
    app_args=['--verbose'],
    repositories={'scijava.public': 'https://maven.scijava.org/content/groups/public'}
)
```

### Example 3: Building Environment Without Running

**jgo 1.x:**
```python
from jgo.jgo import resolve_dependencies

endpoint, environment = resolve_dependencies(
    'org.python:jython-standalone:2.7.3',
    cache_dir='~/.jgo',
    m2_repo='~/.m2/repository',
    update_cache=False,
    force_update=False,
    manage_dependencies=False,
    repositories={},
    shortcuts={},
    verbose=0,
    link_type='auto'
)

# Now you have the environment path, but classpath construction is manual
```

**jgo 2.x:**
```python
import jgo

# Simple way
environment = jgo.build('org.python:jython-standalone:2.7.3')
print(environment.path)
print(environment.classpath)  # List of Path objects
print(environment.main_class)

# Or with more control
from jgo.env import EnvironmentBuilder
from jgo.maven import MavenContext

builder = EnvironmentBuilder(
    context=MavenContext(),
    cache_dir=Path('~/.jgo'),
    link_strategy='auto'
)
environment = builder.from_endpoint(
    'org.python:jython-standalone:2.7.3',
    update=False
)
```

### Example 4: Just Resolving Dependencies

**jgo 1.x:**
```python
# Not directly supported - had to go through full environment resolution
```

**jgo 2.x:**
```python
from jgo.maven import MavenContext, Model

env = Environment()
component = maven.project('org.scijava', 'scijava-common').at_version('2.96.0')
model = Model(component.pom())
deps = model.dependencies()

for dep in deps:
    print(f"{dep.groupId}:{dep.artifactId}:{dep.version}:{dep.scope}")
```

### Example 5: Custom Resolver

**jgo 1.x:**
```python
# Not supported - always used mvn
```

**jgo 2.x:**
```python
from jgo.maven import MavenContext, PythonResolver, MvnResolver

# Pure Python (no mvn needed)
env_pure = Environment(resolver=PythonResolver())

# Using mvn
env_mvn = Environment(resolver=MvnResolver(mvn_command='mvn'))

# Auto (tries pure, falls back to mvn)
env_auto = Environment()  # Default is auto-selection
```

## CLI Migration

### Example 1: Basic Execution

**jgo 1.x:**
```bash
jgo org.python:jython-standalone
```

**jgo 2.x:**
```bash
# Same! Backward compatible for simple cases
jgo org.python:jython-standalone
```

### Example 2: With JVM Arguments

**jgo 1.x:**
```bash
# JVM args are positional, fragile parsing
jgo -Xmx2G -Dfoo=bar org.python:jython-standalone script.py
```

**jgo 2.x:**
```bash
# Explicit separator makes it unambiguous
jgo org.python:jython-standalone -- -Xmx2G -Dfoo=bar -- script.py

# Or use new flags for common JVM options
jgo --max-heap 2G org.python:jython-standalone -- -- script.py
```

### Example 3: Update Cache

**jgo 1.x:**
```bash
jgo -u org.python:jython-standalone    # Update if stale
jgo -U org.python:jython-standalone    # Force update from remote
```

**jgo 2.x:**
```bash
jgo --update org.python:jython-standalone   # Clearer flag name
jgo --update --force org.python:jython-standalone  # Explicit force
```

### Example 4: Verbose Output

**jgo 1.x:**
```bash
jgo -v org.python:jython-standalone
```

**jgo 2.x:**
```bash
jgo --verbose org.python:jython-standalone
# Or use short form
jgo -v org.python:jython-standalone
# Multiple levels
jgo -vv org.python:jython-standalone   # Very verbose
jgo -vvv org.python:jython-standalone  # Debug level
```

### Example 5: Custom Repository

**jgo 1.x:**
```bash
jgo -r scijava.public=https://maven.scijava.org/content/groups/public org.scijava:scijava-common
```

**jgo 2.x:**
```bash
# Same syntax
jgo --repository scijava.public=https://maven.scijava.org/content/groups/public org.scijava:scijava-common
```

### Example 6: List Available Versions

**jgo 1.x:**
```bash
# Not supported
```

**jgo 2.x:**
```bash
jgo --list-versions org.scijava:scijava-common
# Output:
# Available versions for org.scijava:scijava-common:
# Releases (426):
#   2.99.2 (latest)
#   2.99.1
#   2.99.0
#   ...
# Snapshots (113):
#   2.95.0-SNAPSHOT
#   ...
```

### Example 7: Print Classpath

**jgo 1.x:**
```bash
# Not directly supported
```

**jgo 2.x:**
```bash
jgo --print-classpath org.python:jython-standalone
# Output:
# /home/user/.jgo/org/python/jython-standalone/abc123/jars/jython-standalone-2.7.3.jar
```

### Example 8: Dry Run

**jgo 1.x:**
```bash
# Not supported
```

**jgo 2.x:**
```bash
jgo --dry-run org.python:jython-standalone -- -Xmx2G -- script.py
# Output:
# Would resolve dependencies for: org.python:jython-standalone:RELEASE
# Would build environment at: ~/.jgo/org/python/jython-standalone/abc123
# Would execute: java -Xmx2G -cp ... org.python.util.jython script.py
```

## Configuration Migration

### ~/.jgorc Format

**jgo 1.x format:**
```ini
[settings]
m2Repo = /path/to/.m2/repository
cacheDir = /path/to/.jgo
links = auto

[repositories]
scijava.public = https://maven.scijava.org/content/groups/public

[shortcuts]
imagej = net.imagej:imagej
```

**jgo 2.x format (backward compatible):**
```ini
[settings]
# Old names still work
m2Repo = /path/to/.m2/repository
cacheDir = /path/to/.jgo
links = auto

# New names (preferred)
maven.repo_cache = /path/to/.m2/repository
jgo.cache_dir = /path/to/.jgo
jgo.link_strategy = auto
jgo.resolver = auto  # New: auto, python, or mvn

[repositories]
scijava.public = https://maven.scijava.org/content/groups/public

[shortcuts]
imagej = net.imagej:imagej
```

## Common Patterns

### Pattern 1: Using jgo as a Library Dependency

**Your project (using jgo 2.x):**

```python
# pyproject.toml
[project]
dependencies = ["jgo>=2.0.0"]

# your_code.py
import jgo

def run_imagej_macro(macro_file):
    """Run an ImageJ macro using jgo."""
    return jgo.run(
        endpoint='net.imagej:imagej:RELEASE',
        app_args=['--headless', '--run', macro_file]
    )

def get_imagej_classpath():
    """Get the ImageJ classpath without running."""
    environment = jgo.build('net.imagej:imagej:RELEASE')
    return environment.classpath
```

### Pattern 2: Building Custom Java Environments

```python
from jgo.maven import MavenContext
from jgo.env import EnvironmentBuilder, LinkStrategy
from pathlib import Path

def build_analysis_environment():
    """Build a custom environment with specific scientific libraries."""

    env = Environment(
        remote_repos={
            'central': 'https://repo.maven.apache.org/maven2',
            'scijava': 'https://maven.scijava.org/content/groups/public'
        }
    )

    # Define the components we want
    components = [
        maven.project('org.scijava', 'scijava-common').at_version('2.96.0'),
        maven.project('net.imagej', 'imagej-common').at_version('0.32.0'),
        maven.project('net.imglib2', 'imglib2').at_version('6.0.0'),
    ]

    # Build the environment
    builder = EnvironmentBuilder(
        maven_env=env,
        cache_dir=Path('~/.myapp/java-env'),
        link_strategy=LinkStrategy.HARD
    )

    environment = builder.from_components(components)

    return environment

# Use it
environment = build_analysis_environment()
print(f"Environment ready at: {environment.path}")
print(f"Classpath has {len(environment.classpath)} JARs")
```

### Pattern 3: Programmatic Dependency Analysis

```python
from jgo.maven import MavenContext, Model

def analyze_dependencies(gav: str):
    """Analyze the dependency tree of a Maven artifact."""

    g, a, v = gav.split(':')

    env = Environment()
    component = maven.project(g, a).at_version(v)
    model = Model(component.pom())
    deps = model.dependencies()

    # Group by scope
    by_scope = {}
    for dep in deps:
        scope = dep.scope
        if scope not in by_scope:
            by_scope[scope] = []
        by_scope[scope].append(dep)

    # Report
    print(f"Dependency analysis for {gav}:")
    print(f"Total dependencies: {len(deps)}")
    for scope, scope_deps in by_scope.items():
        print(f"  {scope}: {len(scope_deps)}")
        for dep in scope_deps[:5]:  # Show first 5
            print(f"    - {dep.groupId}:{dep.artifactId}:{dep.version}")
        if len(scope_deps) > 5:
            print(f"    ... and {len(scope_deps) - 5} more")

# Use it
analyze_dependencies('org.scijava:scijava-common:2.96.0')
```

## Troubleshooting Migration Issues

### Issue 1: Import Errors

**Problem:**
```python
from jgo.jgo import resolve_dependencies  # ImportError in 2.x
```

**Solution:**
```python
# Use compatibility layer
from jgo.compat.v1 import resolve_dependencies

# Or use new API
from jgo.env import EnvironmentBuilder
```

### Issue 2: Old CLI Flags Don't Work

**Problem:**
```bash
jgo -u -U -m org.python:jython-standalone  # Confusing in 2.x
```

**Solution:**
```bash
# Use new flags
jgo --update --force --managed org.python:jython-standalone

# Or use jgo1 command for exact old behavior
jgo1 -u -U -m org.python:jython-standalone
```

### Issue 3: Missing m2_path() Function

**Problem:**
```python
from jgo.jgo import m2_path  # Deprecated in 1.x, removed in 2.x
```

**Solution:**
```python
from jgo.maven import MavenContext

env = Environment()
repo_cache = env.repo_cache  # Path to ~/.m2/repository
```

## Summary of Benefits

### For Users:
- ✅ Clearer, more intuitive API
- ✅ Better error messages
- ✅ Can use pure Python (no Maven required)
- ✅ Can use just the parts they need
- ✅ Better documentation and examples

### For Developers:
- ✅ Modular, testable architecture
- ✅ Each layer has clear responsibilities
- ✅ Easy to extend with new features
- ✅ Better separation of concerns
- ✅ Type hints throughout

### For the Ecosystem:
- ✅ jgo becomes the standard Maven resolution library for Python
- ✅ Other tools (javadoc.scijava.org, status.scijava.org, updater) can depend on it
- ✅ Maintains backward compatibility for smooth migration
- ✅ Future-proof architecture for new features

"""
jgo: Launch Java applications from Maven coordinates.

jgo is a tool for running Java applications directly from Maven coordinates
without manual installation. It resolves dependencies, materializes JARs, and
executes programs with automatic Java version management.

Quick Start
-----------
>>> import jgo
>>> # Run a Java application
>>> jgo.run("org.python:jython-standalone:2.7.3", app_args=["script.py"])
>>>
>>> # Build environment without running
>>> env = jgo.build("org.python:jython-standalone")
>>> print(env.classpath)  # List of JAR paths
>>>
>>> # Resolve dependencies
>>> components = jgo.resolve("org.python:jython-standalone")

High-Level API (Recommended)
-----------------------------
run(endpoint, app_args=None, jvm_args=None, **kwargs)
    Run a Java application from a Maven endpoint.

build(endpoint, update=False, cache_dir=None, **kwargs) -> Environment
    Build an environment from an endpoint without running it.

resolve(endpoint, repositories=None) -> list[Component]
    Resolve dependencies for a Maven endpoint to Component objects.

Layered API (Advanced)
----------------------
For fine-grained control, use the three-layer architecture:

Layer 1 - Maven resolution (jgo.maven):
    MavenContext - Maven configuration and repository access
    SimpleResolver - Pure Python dependency resolution (no Maven required)
    Component - Versioned Maven artifact (groupId:artifactId:version)

Layer 2 - Environment materialization (jgo.env):
    EnvironmentBuilder - Build environments from endpoints or specs
    Environment - Materialized directory of JARs (like Python's virtualenv)
    EnvironmentSpec - Parse/generate jgo.toml project files

Layer 3 - Execution (jgo.exec):
    JavaRunner - Execute Java programs from environments
    JVMConfig - Configure JVM settings (heap, GC, system properties)
    JavaSource - Java selection strategy (SYSTEM, CJDK)

Example - Full Control
----------------------
>>> from jgo.maven import MavenContext, SimpleResolver
>>> from jgo.env import EnvironmentBuilder, LinkStrategy
>>> from jgo.exec import JavaRunner, JVMConfig
>>>
>>> # Layer 1: Maven resolution
>>> maven = MavenContext(resolver=SimpleResolver())
>>> component = maven.project("org.python", "jython-standalone").at_version("2.7.3")
>>>
>>> # Layer 2: Environment materialization
>>> builder = EnvironmentBuilder(context=maven, link_strategy=LinkStrategy.HARD)
>>> environment = builder.from_components([component])
>>>
>>> # Layer 3: Execution
>>> runner = JavaRunner(jvm_config=JVMConfig(max_heap="2G"))
>>> runner.run(environment, app_args=["script.py"])

jgo.toml Project Files
-----------------------
Create reproducible environments with jgo.toml files:

    [environment]
    name = "my-project"

    [dependencies]
    coordinates = ["org.python:jython-standalone:2.7.3"]

    [entrypoints]
    default = "org.python.util.jython"

Then run with: jgo (uses jgo.toml in current directory)

Backward Compatibility (jgo 1.x)
---------------------------------
Old jgo 1.x APIs still work but show deprecation warnings:
    main(argv) - Old CLI entry point (use jgo.run() instead)
    main_from_endpoint(endpoint, **kwargs) - Old API (use jgo.run() instead)
    resolve_dependencies(endpoint, **kwargs) - Old resolver (use jgo.resolve() instead)

Installation
------------
Basic: pip install jgo  (requires Java pre-installed)
Full:  pip install jgo[cjdk]  (automatic Java download/management)

See Also
--------
- User Guide: docs/user-guide.md
- Architecture: docs/architecture.md
- Migration Guide: docs/MIGRATION.md (for upgrading from jgo 1.x)
- GitHub: https://github.com/apposed/jgo
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from .config.jgorc import JgoConfig
from .env import Environment, EnvironmentBuilder, LinkStrategy
from .exec import JavaRunner, JavaSource, JVMConfig
from .jgo import (
    Endpoint,
    ExecutableNotFound,
    HelpRequested,
    InvalidEndpoint,
    NoEndpointProvided,
    NoMainClassInManifest,
    UnableToAutoComplete,
    resolve_dependencies,
)
from .jgo import _jgo_main as main
from .maven import Component, MavenContext, SimpleResolver
from .util import (
    add_jvm_args_as_necessary,
    main_from_endpoint,
    maven_scijava_repository,
)


def run(
    endpoint: str,
    app_args: list[str] | None = None,
    jvm_args: list[str] | None = None,
    main_class: str | None = None,
    update: bool = False,
    verbose: bool = False,
    cache_dir: Path | None = None,
    repositories: dict[str, str] | None = None,
    java_version: int | None = None,
    java_vendor: str | None = None,
    java_source: str = "cjdk",
) -> subprocess.CompletedProcess:
    """
    Run a Java application from a Maven endpoint.

    This is the main high-level API for running Java applications with jgo.

    Args:
        endpoint: Maven endpoint (e.g., "org.python:jython-standalone:2.7.3")
        app_args: Arguments to pass to the application
        jvm_args: JVM arguments (e.g., ["-Xmx2G"])
        main_class: Main class to run (auto-detected if not specified)
        update: Force update of cached environment
        verbose: Enable verbose output
        cache_dir: Override cache directory
        repositories: Additional Maven repositories (name -> URL)
        java_version: Force specific Java version
        java_vendor: Prefer specific Java vendor
        java_source: Java source strategy ("cjdk", "system")

    Returns:
        CompletedProcess from subprocess.run

    Example:
        >>> import jgo
        >>> jgo.run("org.python:jython-standalone:2.7.3", app_args=["script.py"])
    """
    # Load configuration
    config = JgoConfig.load()

    # Create Maven context
    remote_repos = {"central": "https://repo.maven.apache.org/maven2"}
    if repositories:
        remote_repos.update(repositories)

    context = MavenContext(
        repo_cache=config.repo_cache,
        remote_repos=remote_repos,
        resolver=SimpleResolver(),
    )

    # Create environment builder
    builder = EnvironmentBuilder(
        context=context,
        cache_dir=cache_dir or config.cache_dir,
        link_strategy=LinkStrategy.AUTO,
    )

    # Build environment
    environment = builder.from_endpoint(
        endpoint=endpoint,
        update=update,
        main_class=main_class,
    )

    # Create Java runner
    java_source_map = {
        "system": JavaSource.SYSTEM,
        "cjdk": JavaSource.CJDK,
    }

    runner = JavaRunner(
        jvm_config=JVMConfig(),
        java_source=java_source_map.get(java_source, JavaSource.CJDK),
        java_version=java_version,
        java_vendor=java_vendor,
        verbose=verbose,
    )

    # Run
    result = runner.run(
        environment=environment,
        main_class=main_class,
        app_args=app_args or [],
        additional_jvm_args=jvm_args or [],
        print_command=verbose,
    )

    return result


def build(
    endpoint: str,
    update: bool = False,
    cache_dir: Path | None = None,
    repositories: dict[str, str] | None = None,
) -> Environment:
    """
    Build an environment from a Maven endpoint without running it.

    Args:
        endpoint: Maven endpoint (e.g., "org.python:jython-standalone:2.7.3")
        update: Force update of cached environment
        cache_dir: Override cache directory
        repositories: Additional Maven repositories (name -> URL)

    Returns:
        Environment instance

    Example:
        >>> import jgo
        >>> env = jgo.build("org.python:jython-standalone:2.7.3")
        >>> print(env.classpath)
    """
    # Load configuration
    config = JgoConfig.load()

    # Create Maven context
    remote_repos = {"central": "https://repo.maven.apache.org/maven2"}
    if repositories:
        remote_repos.update(repositories)

    context = MavenContext(
        repo_cache=config.repo_cache,
        remote_repos=remote_repos,
        resolver=SimpleResolver(),
    )

    # Create environment builder
    builder = EnvironmentBuilder(
        context=context,
        cache_dir=cache_dir or config.cache_dir,
        link_strategy=LinkStrategy.AUTO,
    )

    # Build and return environment
    return builder.from_endpoint(endpoint=endpoint, update=update)


def resolve(
    endpoint: str,
    repositories: dict[str, str] | None = None,
) -> list[Component]:
    """
    Resolve dependencies for a Maven endpoint.

    Args:
        endpoint: Maven endpoint (e.g., "org.python:jython-standalone:2.7.3")
        repositories: Additional Maven repositories (name -> URL)

    Returns:
        List of resolved Component objects

    Example:
        >>> import jgo
        >>> components = jgo.resolve("org.python:jython-standalone:2.7.3")
        >>> for comp in components:
        ...     print(f"{comp.groupId}:{comp.artifactId}:{comp.version}")
    """
    # Load configuration
    config = JgoConfig.load()

    # Create Maven context
    remote_repos = {"central": "https://repo.maven.apache.org/maven2"}
    if repositories:
        remote_repos.update(repositories)

    context = MavenContext(
        repo_cache=config.repo_cache,
        remote_repos=remote_repos,
        resolver=SimpleResolver(),
    )

    # Parse endpoint to get components
    parts = endpoint.split("+")
    components = []

    for part in parts:
        from .parse.coordinate import Coordinate

        coord = Coordinate.parse(part)
        version = coord.version or "RELEASE"

        component = context.project(coord.groupId, coord.artifactId).at_version(version)
        components.append(component)

    return components


__all__ = (
    # New 2.0 API
    "run",
    "build",
    "resolve",
    # Old 1.x compatibility API - Functions
    "main",
    "main_from_endpoint",
    "resolve_dependencies",
    "add_jvm_args_as_necessary",
    "maven_scijava_repository",
    # Old 1.x compatibility API - Classes and Exceptions
    "Endpoint",
    "NoMainClassInManifest",
    "ExecutableNotFound",
    "InvalidEndpoint",
    "UnableToAutoComplete",
    "HelpRequested",
    "NoEndpointProvided",
)

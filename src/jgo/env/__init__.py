"""
Environment materialization layer for jgo.

An *environment* is a directory that holds the resolved JAR files for a set
of Maven coordinates, laid out so that Java can consume them directly:

    <env-dir>/
        jars/           — class-path JARs  (non-modular)
        modules/        — module-path JARs (explicit- or automatic-module JARs)
        jgo.lock.toml   — pinned dependency graph + checksums + entrypoints

This module provides the classes needed to create, inspect, and reuse
environments.

Key Classes
-----------
EnvironmentBuilder
    Resolves Maven coordinates, downloads JARs (via ``jgo.maven``), classifies
    each JAR as modular/non-modular, links them into the right sub-directory,
    and writes ``jgo.lock.toml``.

    Two construction modes:

    * ``from_endpoint(endpoint)`` — ad-hoc resolution from a coordinate string
      (e.g. ``"org.python:jython-standalone:2.7.3"``).
    * ``from_spec(spec)`` — project-mode resolution from a parsed ``jgo.toml``
      file (see ``EnvironmentSpec``).

    Cache paths:

    * **Project mode** (``jgo.toml`` present in CWD): cache stored in ``.jgo/``
      relative to the project root.
    * **Ad-hoc mode**: cache stored under
      ``~/.cache/jgo/envs/<groupId>/<artifactId>/<16-char-hash>/``.

    >>> from jgo.maven import MavenContext
    >>> from jgo.env import EnvironmentBuilder, LinkStrategy
    >>> builder = EnvironmentBuilder(
    ...     context=MavenContext(),
    ...     link_strategy=LinkStrategy.HARD,
    ... )
    >>> env = builder.from_endpoint("org.python:jython-standalone:2.7.3")
    >>> env.classpath           # List[Path] of class-path JARs
    >>> env.module_path_jars    # List[Path] of module-path JARs
    >>> env.main_class          # Auto-detected from JAR manifest

Environment
    A read-only handle on a materialized environment directory.  Provides
    convenient access to classpath/module-path JAR lists, the detected main
    class, minimum required Java version, and the lock file.

    >>> env.path                # Root directory of the environment
    >>> env.jars_dir            # env.path / "jars"
    >>> env.modules_dir         # env.path / "modules"
    >>> env.all_jars            # All JARs (both directories)
    >>> env.min_java_version    # e.g. 11
    >>> env.lockfile            # LockFile | None
    >>> env.main_class          # e.g. "org.python.util.jython"

LinkStrategy
    Controls how JARs are placed into the environment directory.

    * ``AUTO``   — hard-link when possible, copy otherwise (default)
    * ``HARD``   — always hard-link (error if cross-device)
    * ``COPY``   — always copy
    * ``SYMLINK``— symbolic link

EnvironmentSpec
    In-memory representation of a ``jgo.toml`` project file.  Use
    ``EnvironmentSpec.load(path)`` to parse an existing file, or construct
    one programmatically and call ``spec.save(path)``.

    >>> from jgo.env import EnvironmentSpec
    >>> spec = EnvironmentSpec.load("jgo.toml")
    >>> spec.coordinates        # List of Maven coordinate strings
    >>> spec.entrypoints        # Dict of name → class or coordinate

LockFile / LockedDependency
    ``jgo.lock.toml`` data — resolved G:A:V coordinates with SHA-256
    checksums, module names, and minimum Java version.  Written by
    ``EnvironmentBuilder`` and read by ``Environment``.

JAR Utility Functions
---------------------
analyze_jar_bytecode(jar_path)
    Return bytecode version information for all ``.class`` files in a JAR.

bytecode_to_java_version(bytecode_version)
    Convert a raw class-file major version number to a Java release number.

round_to_lts(java_version)
    Round up a Java version to the nearest LTS release (8, 11, 17, 21, …).

find_main_classes(jar_path)
    List all classes that declare a ``public static void main(String[])``
    method inside a JAR.

parse_manifest(jar_path) / read_raw_manifest(jar_path)
    Read ``META-INF/MANIFEST.MF`` from a JAR.

compute_spec_hash(spec_path)
    Compute a deterministic hash of a ``jgo.toml`` file for staleness
    detection.

Example — Build and Inspect an Environment
-------------------------------------------
>>> from jgo.maven import MavenContext
>>> from jgo.env import EnvironmentBuilder
>>> builder = EnvironmentBuilder(context=MavenContext())
>>> env = builder.from_endpoint("net.imagej:imagej:2.14.0")
>>> print("Main class:", env.main_class)
>>> print("Min Java:", env.min_java_version)
>>> print("JARs on classpath:", len(env.classpath))
>>> print("JARs on module-path:", len(env.module_path_jars))
"""

from ._builder import EnvironmentBuilder
from ._bytecode import analyze_jar_bytecode, bytecode_to_java_version, round_to_lts
from ._environment import Environment
from ._jar import find_main_classes, parse_manifest, read_raw_manifest
from ._linking import LinkStrategy
from ._lockfile import LockedDependency, LockFile, compute_spec_hash
from ._spec import EnvironmentSpec

__all__ = [
    # builder
    "EnvironmentBuilder",
    # bytecode
    "analyze_jar_bytecode",
    "bytecode_to_java_version",
    "round_to_lts",
    # environment
    "Environment",
    # jar
    "find_main_classes",
    "parse_manifest",
    "read_raw_manifest",
    # linking
    "LinkStrategy",
    # lockfile
    "LockedDependency",
    "LockFile",
    "compute_spec_hash",
    # spec
    "EnvironmentSpec",
]

"""
Java execution layer for jgo.

This module is responsible for everything that happens *after* the environment
has been materialized: locating a suitable JVM, building the ``java`` command
line, and launching the process.

Key Classes
-----------
JavaRunner
    Executes a Java program from a materialized ``jgo.env.Environment``.
    Handles:

    * Locating a JVM via ``JavaLocator`` (honouring ``java_version`` /
      ``java_vendor`` preferences).
    * Building the command line — class-path (``-cp``), module-path
      (``--module-path``), and JVM arguments from ``JVMConfig``.
    * Switching between class-path and module-path based on whether the
      environment contains modular JARs.

    >>> from jgo.exec import JavaRunner, JVMConfig
    >>> runner = JavaRunner(jvm_config=JVMConfig(max_heap="2G"))
    >>> result = runner.run(env, app_args=["--help"])

    Methods:

    * ``run(environment, ...)`` — stream stdout/stderr to terminal, return
      ``subprocess.CompletedProcess``.
    * ``run_and_capture(environment, ...)`` — capture stdout/stderr into
      ``result.stdout`` / ``result.stderr``.

JVMConfig
    Encapsulates JVM tuning knobs passed as arguments to ``java``.

    Parameters:

    * ``max_heap`` / ``min_heap`` — ``-Xmx`` / ``-Xms`` values (e.g. ``"2G"``).
      When ``max_heap`` is ``None`` and ``auto_heap=True`` (the default),
      the heap is set to half of available system RAM.
    * ``gc_options`` — explicit GC flags (e.g. ``["-XX:+UseZGC"]``).  When
      ``None``, smart version-aware defaults are chosen (G1GC for Java 8–20,
      ZGC for Java 21+).
    * ``system_properties`` — dict of ``-D`` properties; nested dicts are
      flattened with dot notation (TOML-friendly).
    * ``extra_args`` — arbitrary additional JVM arguments.

    Instances are immutable-by-convention; use the builder helpers to derive
    modified copies:

    >>> cfg = JVMConfig(max_heap="4G", gc_options=["-XX:+UseZGC"])
    >>> cfg2 = cfg.with_system_property("java.awt.headless", "true")
    >>> cfg3 = cfg2.with_extra_arg("--enable-preview")
    >>> cfg.to_jvm_args(java_version=21)
    ['-XX:+UseZGC', '-Xmx4G']

JavaSource
    Enum controlling how the Java executable is located.

    * ``AUTO``   — use ``cjdk`` to download/cache a matching JDK if no
      suitable system Java is found.  This is the default and ensures the
      requested ``java_version`` / ``java_vendor`` are always satisfied.
    * ``SYSTEM`` — use the Java binary found via ``JAVA_HOME`` or ``PATH``.
      Raises an error if the system Java does not satisfy version constraints.

JavaLocator
    Low-level helper that implements the JVM discovery strategy described by
    ``JavaSource``.  Used internally by ``JavaRunner`` but also useful on its
    own when you need a ``java`` path without running anything.

    >>> from jgo.exec import JavaLocator, JavaSource
    >>> locator = JavaLocator(java_source=JavaSource.AUTO, java_version=21)
    >>> java_path = locator.locate()   # Path to java executable

GC Utilities
------------
is_gc_flag(arg)
    Return True if a JVM argument string is a garbage-collector flag
    (e.g. ``"-XX:+UseG1GC"``).

normalize_gc_flag(arg)
    Normalise a GC flag to its canonical ``-XX:+UseXxxGC`` form.

Example — Full Execution Pipeline
-----------------------------------
>>> from jgo.maven import MavenContext
>>> from jgo.env import EnvironmentBuilder
>>> from jgo.exec import JavaRunner, JVMConfig, JavaSource
>>>
>>> env = EnvironmentBuilder(context=MavenContext()).from_endpoint(
...     "org.python:jython-standalone:2.7.3"
... )
>>> runner = JavaRunner(
...     jvm_config=JVMConfig(max_heap="1G", system_properties={"python.home": "/tmp"}),
...     java_source=JavaSource.AUTO,
...     java_version=11,
... )
>>> result = runner.run(env, app_args=["-c", "print('hello')"])
>>> result.returncode
0
"""

from ..util.java import JavaLocator, JavaSource
from ._config import JVMConfig
from ._gc import is_gc_flag, normalize_gc_flag
from ._runner import JavaRunner

__all__ = [
    "JVMConfig",
    "is_gc_flag",
    "JavaSource",
    "JavaLocator",
    "JavaRunner",
    "normalize_gc_flag",
]

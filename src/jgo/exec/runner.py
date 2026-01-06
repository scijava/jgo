"""
Java runner for jgo.

Executes Java programs with constructed environments.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

from .config import JVMConfig
from .java_source import JavaLocator, JavaSource

_log = logging.getLogger(__name__)


class JavaRunner:
    """
    Executes Java programs with configured JVM and classpath.
    """

    def __init__(
        self,
        jvm_config: JVMConfig | None = None,
        java_source: JavaSource = JavaSource.AUTO,
        java_version: int | None = None,
        java_vendor: str | None = None,
        verbose: bool = False,
    ):
        """
        Initialize Java runner.

        Args:
            jvm_config: JVM configuration (heap, GC, etc.)
            java_source: Strategy for locating Java executable
            java_version: Desired Java version (overrides environment detection)
            java_vendor: Desired Java vendor (e.g., "adoptium", "zulu")
            verbose: Enable verbose output
        """
        self.jvm_config = jvm_config or JVMConfig()
        self.java_source = java_source
        self.java_version = java_version
        self.java_vendor = java_vendor
        self.verbose = verbose

    def run(
        self,
        environment,  # Type hint would be circular: jgo.env.Environment
        main_class: str | None = None,
        app_args: list[str] | None = None,
        additional_jvm_args: list[str] | None = None,
        additional_classpath: list[str] | None = None,
        print_command: bool = False,
        dry_run: bool = False,
        module_mode: str = "auto",
    ) -> subprocess.CompletedProcess:
        """
        Run a Java program from an environment.

        Args:
            environment: Environment containing classpath and metadata
            main_class: Main class to execute (uses environment.main_class
                if not specified)
            app_args: Arguments to pass to the application
            additional_jvm_args: Additional JVM arguments (beyond jvm_config)
            additional_classpath: Additional classpath elements (JARs,
                directories, etc.)
            print_command: If True, print the java command being executed
            dry_run: If True, print the command but don't execute it
            module_mode: Module mode - "auto", "class-path-only", or "module-path-only"

        Returns:
            CompletedProcess from subprocess.run

        Raises:
            RuntimeError: If main class cannot be determined or Java execution fails
        """
        # Determine main class
        effective_main_class = main_class or environment.main_class
        if not effective_main_class:
            raise RuntimeError(
                "No main class specified. Either provide main_class argument or "
                "ensure environment has a detected main class."
            )

        # Determine module/classpath usage based on mode
        modules_dir = environment.modules_dir
        jars_dir = environment.jars_dir
        has_classpath = environment.has_classpath
        has_modules = environment.has_modules

        if module_mode == "class-path-only":
            # Force all JARs to classpath (both jars/ and modules/ directories)
            use_modules = False
            use_classpath = True
            classpath_dirs = (
                [jars_dir, modules_dir] if modules_dir.exists() else [jars_dir]
            )
        else:  # "auto" (module-path-only is now same as auto)
            # Smart mode: Use modules if available, but also include jars/ for non-modularizable JARs
            use_modules = has_modules

            # When using modules, we may still need classpath for non-modularizable JARs
            # Always include jars/ if it exists, even when using modules
            if has_modules and has_classpath:
                # Modular app with some non-modularizable JARs
                use_classpath = True
                classpath_dirs = [jars_dir]
            elif has_classpath:
                # Non-modular app - everything on classpath
                use_classpath = True
                classpath_dirs = (
                    [jars_dir, modules_dir] if modules_dir.exists() else [jars_dir]
                )
            else:
                # Pure modular app (no non-modularizable JARs)
                use_classpath = False
                classpath_dirs = []

        if use_classpath and module_mode == "module-path-only":
            raise RuntimeError(
                f"Cannot use module-path-only due to non-modularizable JARs in {jars_dir}"
            )

        if not use_modules and not use_classpath:
            raise RuntimeError(f"No JARs found in environment: {environment.path}")

        # Locate Java executable
        locator = JavaLocator(
            java_source=self.java_source,
            java_version=self.java_version,
            java_vendor=self.java_vendor,
            verbose=self.verbose,
        )

        # Use environment's min_java_version if no explicit version specified
        min_version = (
            environment.min_java_version if self.java_version is None else None
        )
        java_path = locator.locate(min_version=min_version)

        # Check Java version to determine if module-path is supported
        actual_java_version = locator._get_java_version(java_path)
        supports_modules = actual_java_version >= 9

        # Build command
        cmd = [str(java_path)]

        # Add JVM arguments (pass java_version for smart GC defaults)
        jvm_args = self.jvm_config.to_jvm_args(java_version=actual_java_version)
        cmd.extend(jvm_args)

        # Add additional JVM arguments
        if additional_jvm_args:
            cmd.extend(additional_jvm_args)

        # Add module-path (directory, not enumerated JARs)
        # Only use module-path if Java 9+ and modules are present
        if use_modules and modules_dir.exists() and supports_modules:
            cmd.extend(["--module-path", str(modules_dir)])
            # Add all modules from the module-path
            cmd.extend(["--add-modules", "ALL-MODULE-PATH"])
        elif use_modules and not supports_modules:
            # Java 8 or earlier - fall back to classpath for modular JARs
            use_modules = False
            use_classpath = True
            classpath_dirs = (
                [jars_dir, modules_dir] if modules_dir.exists() else [jars_dir]
            )

        # Add classpath
        if use_classpath or classpath_dirs:
            # Start with environment directories, then add user-specified paths
            all_classpath = list(classpath_dirs)
            if additional_classpath:
                all_classpath.extend(Path(p) for p in additional_classpath)
            if all_classpath:
                classpath_str = self._build_classpath(all_classpath)
                cmd.extend(["-cp", classpath_str])

        # Determine if main class is in modular JAR
        module_name = None
        is_modular_main = False
        if use_modules:
            module_name, is_modular_main = environment.get_module_for_main_class(
                effective_main_class
            )

        if is_modular_main and module_name:
            # Use --module for modular main class
            cmd.extend(["--module", f"{module_name}/{effective_main_class}"])
        else:
            # Traditional main class on command line
            cmd.append(effective_main_class)

        # Add application arguments
        if app_args:
            cmd.extend(app_args)

        # Print command if requested or in dry-run/verbose mode
        # Print directly to stderr for clean, unwrapped output
        if print_command or self.verbose or dry_run:
            print(" ".join(cmd), file=sys.stderr)

        # In dry-run mode, don't execute - just return a mock result
        if dry_run:
            return subprocess.CompletedProcess(args=cmd, returncode=0)

        # Execute
        try:
            result = subprocess.run(cmd, check=False)
            return result
        except FileNotFoundError:
            raise RuntimeError(f"Java executable not found: {java_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to execute Java program: {e}")

    def run_and_capture(
        self,
        environment,  # Type hint would be circular: jgo.env.Environment
        main_class: str | None = None,
        app_args: list[str] | None = None,
        additional_jvm_args: list[str] | None = None,
        print_command: bool = False,
    ) -> subprocess.CompletedProcess:
        """
        Run a Java program and capture stdout/stderr.

        Like run(), but captures output instead of streaming it.

        Args:
            environment: Environment containing classpath and metadata
            main_class: Main class to execute
            app_args: Arguments to pass to the application
            additional_jvm_args: Additional JVM arguments
            print_command: If True, print the java command being executed

        Returns:
            CompletedProcess with stdout and stderr captured
        """
        # Build command (same as run())
        effective_main_class = main_class or environment.main_class
        if not effective_main_class:
            raise RuntimeError("No main class specified")

        classpath = environment.classpath
        if not classpath:
            raise RuntimeError(f"No JARs found in environment: {environment.path}")

        locator = JavaLocator(
            java_source=self.java_source,
            java_version=self.java_version,
            java_vendor=self.java_vendor,
            verbose=self.verbose,
        )

        min_version = (
            environment.min_java_version if self.java_version is None else None
        )
        java_path = locator.locate(min_version=min_version)

        cmd = [str(java_path)]
        jvm_args = self.jvm_config.to_jvm_args()
        cmd.extend(jvm_args)

        if additional_jvm_args:
            cmd.extend(additional_jvm_args)

        classpath_str = self._build_classpath(classpath)
        cmd.extend(["-cp", classpath_str])
        cmd.append(effective_main_class)

        if app_args:
            cmd.extend(app_args)

        # Print command if verbose or explicitly requested
        # Print directly to stderr for clean output
        if print_command or self.verbose:
            print(" ".join(cmd), file=sys.stderr)

        # Execute and capture output
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return result
        except FileNotFoundError:
            raise RuntimeError(f"Java executable not found: {java_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to execute Java program: {e}")

    def _build_classpath(self, paths: list[Path]) -> str:
        """
        Build classpath string from paths.

        For directories, appends '/*' to include all JARs (Java classpath wildcard).
        For files, includes them as-is. Preserves order of paths.

        Args:
            paths: List of directories (to be wildcarded) or file paths

        Returns:
            Classpath string with platform-appropriate separator
        """
        separator = ";" if sys.platform == "win32" else ":"

        def format_path(path: Path) -> str:
            return str(path / "*") if path.is_dir() else str(path)

        return separator.join(format_path(path) for path in paths)

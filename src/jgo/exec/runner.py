"""
Java runner for jgo 2.0.

Executes Java programs with constructed environments.
"""

from pathlib import Path
from typing import List, Optional
import subprocess
import sys

from .config import JVMConfig
from .java_source import JavaSource, JavaLocator


class JavaRunner:
    """
    Executes Java programs with configured JVM and classpath.
    """

    def __init__(
        self,
        jvm_config: Optional[JVMConfig] = None,
        java_source: JavaSource = JavaSource.AUTO,
        java_version: Optional[int] = None,
        java_vendor: Optional[str] = None,
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
        main_class: Optional[str] = None,
        app_args: Optional[List[str]] = None,
        additional_jvm_args: Optional[List[str]] = None,
        additional_classpath: Optional[List[str]] = None,
        print_command: bool = False,
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

        # Get classpath
        classpath = environment.classpath
        if not classpath:
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

        # Build command
        cmd = [str(java_path)]

        # Add JVM arguments
        jvm_args = self.jvm_config.to_jvm_args()
        cmd.extend(jvm_args)

        # Add additional JVM arguments
        if additional_jvm_args:
            cmd.extend(additional_jvm_args)

        # Add classpath (include additional classpath if provided)
        all_classpath = list(classpath)
        if additional_classpath:
            all_classpath.extend(Path(p) for p in additional_classpath)
        classpath_str = self._build_classpath(all_classpath)
        cmd.extend(["-cp", classpath_str])

        # Add main class
        cmd.append(effective_main_class)

        # Add application arguments
        if app_args:
            cmd.extend(app_args)

        # Print command if requested
        if print_command or self.verbose:
            print(" ".join(cmd), file=sys.stderr)

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
        main_class: Optional[str] = None,
        app_args: Optional[List[str]] = None,
        additional_jvm_args: Optional[List[str]] = None,
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

    def _build_classpath(self, jar_paths: List[Path]) -> str:
        """
        Build classpath string from JAR paths.

        Args:
            jar_paths: List of JAR file paths

        Returns:
            Classpath string with platform-appropriate separator
        """
        separator = ";" if sys.platform == "win32" else ":"
        return separator.join(str(p) for p in jar_paths)

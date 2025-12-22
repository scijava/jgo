"""
CLI command implementations for jgo.
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import TYPE_CHECKING

from ..constants import DEFAULT_MAVEN_REPO, MAVEN_CENTRAL_URL
from ..env import EnvironmentBuilder, EnvironmentSpec, LinkStrategy
from ..env.builder import filter_managed_components
from ..exec import JavaRunner, JavaSource, JVMConfig
from ..maven import MavenContext, MvnResolver, PythonResolver
from .parser import ParsedArgs

if TYPE_CHECKING:
    from ..maven.core import Component


class JgoCommands:
    """
    Implementation of jgo CLI commands.
    """

    def __init__(self, args: ParsedArgs, config: dict | None = None):
        """
        Initialize commands with parsed arguments and configuration.

        Args:
            args: Parsed command line arguments
            config: Configuration from ~/.jgorc (optional)
        """
        self.args = args
        self.config = config or {}
        self.verbose = args.verbose > 0 and not args.quiet
        self.debug = args.verbose >= 2

    def execute(self) -> int:
        """
        Execute the appropriate command based on parsed arguments (legacy path).

        This method handles the old flag-based interface for backwards compatibility.
        New command-based interface is dispatched from __main__.py.

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        # Show deprecation warnings for old jgo 1.x flags
        self._check_deprecated_flags()

        try:
            # Handle legacy --init flag
            if self.args.init:
                from .subcommands import init

                # Create a copy of args with endpoint set to init value
                self.args.endpoint = self.args.init
                return init.execute(self.args, self.config)

            # Handle legacy --list-entrypoints flag
            if self.args.list_entrypoints:
                from .subcommands import info

                return info.execute(self.args, self.config)

            # Handle legacy --list-versions flag
            if self.args.list_versions:
                from .subcommands import versions

                return versions.execute(self.args, self.config)

            # Handle spec file mode vs endpoint mode
            if self.args.is_spec_mode():
                return self._cmd_run_spec()
            else:
                return self._cmd_run_endpoint()

        except KeyboardInterrupt:
            if self.verbose:
                print("\nInterrupted by user", file=sys.stderr)
            return 130  # Standard exit code for SIGINT
        except Exception as e:
            if self.debug:
                raise  # Show full traceback in debug mode
            print(f"Error: {e}", file=sys.stderr)
            return 1

    def _check_deprecated_flags(self):
        """
        Check for deprecated jgo 1.x flags and show warnings.
        """
        # Check for --additional-endpoints
        if self.args.additional_endpoints:
            warnings.warn(
                "--additional-endpoints is deprecated. Use '+' syntax instead:\n"
                "  Old: jgo --additional-endpoints org.dep:lib org.main:app\n"
                "  New: jgo org.main:app+org.dep:lib",
                DeprecationWarning,
                stacklevel=3,
            )

        # Check for --log-level
        if self.args.log_level:
            warnings.warn(
                "--log-level is deprecated. Use -v/-vv/-vvv for verbose output instead",
                DeprecationWarning,
                stacklevel=3,
            )

    def _cmd_run_spec(self) -> int:
        """
        Run from jgo.toml spec file.
        """
        spec_file = self.args.get_spec_file()

        if not spec_file.exists():
            print(f"Error: {spec_file} not found", file=sys.stderr)
            return 1

        # Load spec
        spec = EnvironmentSpec.load(spec_file)

        # Create Maven context and environment builder
        context = self._create_maven_context()
        builder = self._create_environment_builder(context)

        # If --print-dependency-tree or --print-dependency-list, parse coordinates and print without building
        if self.args.print_dependency_tree or self.args.print_dependency_list:
            # Parse coordinates into components
            components = []
            for coord_str in spec.coordinates:
                from ..parse.coordinate import Coordinate

                coord = Coordinate.parse(coord_str)
                version = coord.version or "RELEASE"
                component = context.project(coord.groupId, coord.artifactId).at_version(
                    version
                )
                components.append(component)
            self._print_dependencies(
                components, context, list_mode=self.args.print_dependency_list
            )
            return 0

        # Build environment
        if self.verbose:
            print(f"Building environment from {spec_file}...")

        environment = builder.from_spec(
            spec, update=self.args.update, entrypoint=self.args.entrypoint
        )

        # If --print-classpath, just print and exit
        if self.args.print_classpath:
            self._print_classpath(environment)
            return 0

        # If --print-java-info, just print and exit
        if self.args.print_java_info:
            self._print_java_info(environment)
            return 0

        # Create runner and execute
        if self.verbose:
            print(f"Running {spec.name}...")

        runner = self._create_java_runner()
        # Use environment's main class if set, otherwise fall back to args.main_class
        main_class_to_use = environment.main_class or self.args.main_class
        result = runner.run(
            environment=environment,
            main_class=main_class_to_use,
            app_args=self.args.app_args,
            additional_jvm_args=self.args.jvm_args,
            additional_classpath=self.args.classpath_append,
            print_command=self.debug,
        )

        return result.returncode

    def _cmd_run_endpoint(self) -> int:
        """
        Run from endpoint string.
        """
        if not self.args.endpoint:
            print("Error: No endpoint specified", file=sys.stderr)
            print("Use 'jgo --help' for usage information", file=sys.stderr)
            return 1

        # Create Maven context and environment builder
        context = self._create_maven_context()
        builder = self._create_environment_builder(context)

        # If --print-dependency-tree or --print-dependency-list, parse endpoint and print without building
        if self.args.print_dependency_tree or self.args.print_dependency_list:
            components, coordinates, _ = builder._parse_endpoint(self.args.endpoint)
            # Determine which components should be managed
            boms = filter_managed_components(components, coordinates)
            self._print_dependencies(
                components,
                context,
                boms=boms,
                list_mode=self.args.print_dependency_list,
            )
            return 0

        # Build environment
        if self.verbose:
            print(f"Building environment for {self.args.endpoint}...")

        environment = builder.from_endpoint(
            self.args.endpoint,
            update=self.args.update,
            main_class=self.args.main_class,
        )

        # If --print-classpath, just print and exit
        if self.args.print_classpath:
            self._print_classpath(environment)
            return 0

        # If --print-java-info, just print and exit
        if self.args.print_java_info:
            self._print_java_info(environment)
            return 0

        # Create runner and execute
        if self.verbose:
            print("Running Java application...")

        runner = self._create_java_runner()
        # Use environment's main class if set (it's been auto-completed),
        # otherwise fall back to args.main_class
        main_class_to_use = environment.main_class or self.args.main_class
        result = runner.run(
            environment=environment,
            main_class=main_class_to_use,
            app_args=self.args.app_args,
            additional_jvm_args=self.args.jvm_args,
            additional_classpath=self.args.classpath_append,
            print_command=self.debug,
        )

        return result.returncode

    def _create_maven_context(self) -> MavenContext:
        """
        Create Maven context from arguments and configuration.
        """
        # Determine resolver
        if self.args.resolver == "python":
            resolver = PythonResolver()
        elif self.args.resolver == "mvn":
            from jgo.util import ensure_maven_available

            mvn_command = ensure_maven_available()
            resolver = MvnResolver(
                mvn_command, update=self.args.update, debug=self.args.verbose >= 2
            )
        else:  # auto
            resolver = PythonResolver()  # Default to pure Python

        # Get repo cache path
        repo_cache = self.args.repo_cache
        if repo_cache is None:
            # Check config, then default
            repo_cache = self.config.get("repo_cache", DEFAULT_MAVEN_REPO)
        repo_cache = Path(repo_cache).expanduser()

        # Get remote repositories
        remote_repos = {}

        # Start with Maven Central
        remote_repos["central"] = MAVEN_CENTRAL_URL

        # Add from config
        if "repositories" in self.config:
            remote_repos.update(self.config["repositories"])

        # Add from command line (overrides config)
        if self.args.repositories:
            remote_repos.update(self.args.repositories)

        # Create context
        return MavenContext(
            repo_cache=repo_cache,
            remote_repos=remote_repos,
            resolver=resolver,
        )

    def _create_environment_builder(self, context: MavenContext) -> EnvironmentBuilder:
        """
        Create environment builder from arguments and configuration.
        """
        # Determine link strategy
        link_strategy_map = {
            "hard": LinkStrategy.HARD,
            "soft": LinkStrategy.SOFT,
            "copy": LinkStrategy.COPY,
            "auto": LinkStrategy.AUTO,
        }
        link_strategy = link_strategy_map[self.args.link]

        # Get cache directory
        cache_dir = self.args.cache_dir
        if cache_dir is None:
            # Check config
            cache_dir = self.config.get("cache_dir")
        # If still None, EnvironmentBuilder will auto-detect

        return EnvironmentBuilder(
            context=context,
            cache_dir=cache_dir,
            link_strategy=link_strategy,
        )

    def _create_java_runner(self) -> JavaRunner:
        """
        Create Java runner from arguments and configuration.
        """
        # Map string to JavaSource enum
        java_source_map = {
            "system": JavaSource.SYSTEM,
            "cjdk": JavaSource.CJDK,
        }
        java_source = java_source_map[self.args.java_source]

        # Create JVM config
        jvm_config = JVMConfig()

        # TODO: Load JVM options from config file

        return JavaRunner(
            jvm_config=jvm_config,
            java_source=java_source,
            java_version=self.args.java_version,
            java_vendor=self.args.java_vendor,
            verbose=self.verbose,
        )

    def _print_classpath(self, environment) -> None:
        """
        Print environment classpath.
        """
        classpath = environment.classpath
        if not classpath:
            print("No JARs in classpath", file=sys.stderr)
            return

        separator = ";" if sys.platform == "win32" else ":"
        classpath_str = separator.join(str(p) for p in classpath)
        print(classpath_str)

    def _print_dependencies(
        self,
        components: list[Component],
        context: MavenContext,
        boms: list[Component] | None = None,
        list_mode: bool = False,
    ) -> None:
        """
        Print dependencies for the given components.

        Args:
            components: List of components to print dependencies for
            context: Maven context containing the resolver
            boms: List of components to use as managed BOMs (None = none managed)
            list_mode: If True, print flat list (like mvn dependency:list).
                      If False, print tree (like mvn dependency:tree).
        """
        # Print dependencies for the components
        if list_mode:
            output = context.resolver.print_dependency_list(
                components,
                managed=bool(boms),
                boms=boms,
                transitive=not self.args.direct_only,
            )
        else:
            output = context.resolver.print_dependency_tree(
                components,
                managed=bool(boms),
                boms=boms,
            )
        print(output)

    def _print_java_info(self, environment) -> None:
        """
        Print detailed Java version requirements for the environment.
        """
        from jgo.env.bytecode import (
            analyze_jar_bytecode,
            bytecode_to_java_version,
            round_to_lts,
        )

        jars_dir = environment.path / "jars"
        if not jars_dir.exists():
            print("No JARs directory found", file=sys.stderr)
            return

        jar_files = sorted(jars_dir.glob("*.jar"))
        if not jar_files:
            print("No JARs in environment", file=sys.stderr)
            return

        print(f"Environment: {environment.path}")
        print(f"JARs directory: {jars_dir}")
        print(f"Total JARs: {len(jar_files)}\n")

        # Analyze each JAR
        jar_analyses = []
        overall_max_java = None

        for jar_path in jar_files:
            analysis = analyze_jar_bytecode(jar_path)
            if analysis and analysis.get("java_version"):
                jar_analyses.append((jar_path.name, analysis))
                java_ver = analysis["java_version"]
                if overall_max_java is None or java_ver > overall_max_java:
                    overall_max_java = java_ver

        # Sort by Java version (highest first)
        jar_analyses.sort(key=lambda x: x[1]["java_version"], reverse=True)

        # Print summary
        lts_version = round_to_lts(overall_max_java) if overall_max_java else None
        print("=" * 70)
        print("JAVA VERSION REQUIREMENTS")
        print("=" * 70)
        print(f"Detected minimum Java version: {overall_max_java}")
        if lts_version != overall_max_java:
            print(f"Rounded to LTS: {lts_version}")
        else:
            print("(already an LTS version)")
        print()

        # Print per-JAR analysis
        print("=" * 70)
        print("PER-JAR ANALYSIS")
        print("=" * 70)
        for jar_name, analysis in jar_analyses:
            java_ver = analysis["java_version"]
            max_bytecode = analysis["max_version"]
            version_counts = analysis["version_counts"]

            print(f"\n{jar_name}")
            print(f"  Required Java version: {java_ver} (bytecode {max_bytecode})")

            # Show distribution
            print("  Bytecode version distribution:")
            for bytecode_ver in sorted(version_counts.keys(), reverse=True):
                count = version_counts[bytecode_ver]
                java_v = bytecode_to_java_version(bytecode_ver)
                print(
                    f"    Java {java_v:2d} (bytecode {bytecode_ver}): {count:5d} classes"
                )

            # Show high-version classes if not all the same
            if len(version_counts) > 1:
                high_classes = analysis["high_version_classes"]
                max_ver = high_classes[0][1] if high_classes else None
                high_ver_only = [
                    (name, ver) for name, ver in high_classes if ver == max_ver
                ]
                if high_ver_only and len(high_ver_only) <= 5:
                    print(f"  Classes requiring Java {java_ver}:")
                    for class_name, _ in high_ver_only:
                        print(f"    - {class_name}")

            # Show skipped files if any
            skipped = analysis.get("skipped", [])
            if skipped:
                print(f"  Skipped files (sample): {len(skipped)} files")
                for s in skipped[:3]:
                    print(f"    - {s}")

        print("\n" + "=" * 70)

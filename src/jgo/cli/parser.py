"""
CLI argument parser for jgo 2.0.
"""

import argparse
from pathlib import Path
from typing import List, Optional, Tuple


class JgoArgumentParser:
    """
    Parser for jgo CLI arguments.

    Supports the format:
        jgo [JGO_OPTIONS] [endpoint] [-- JVM_OPTIONS] [-- APP_ARGS]

    Or spec file mode:
        jgo [JGO_OPTIONS] [-f FILE] [--entrypoint NAME]
    """

    def __init__(self):
        self.parser = self._build_parser()

    def _build_parser(self) -> argparse.ArgumentParser:
        """Build the argument parser."""
        parser = argparse.ArgumentParser(
            prog="jgo",
            description="Launch Java applications from Maven coordinates",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Endpoint Format:
  groupId:artifactId[:version][:classifier][:mainClass]

  Multiple Maven coordinates can be combined with '+':
    org.scijava:scijava-common:2.96.0+org.scijava:parsington:3.1.0

  Use '@' for main class auto-completion:
    org.scijava:scijava-common:@ScriptREPL

Examples:
  # Run Jython REPL
  jgo org.python:jython-standalone

  # Run with specific version and JVM options
  jgo org.python:jython-standalone:2.7.3 -- -Xmx2G -- script.py --verbose

  # Build environment without running
  jgo --print-classpath org.python:jython-standalone

  # Show Java version requirements
  jgo --print-java-info org.python:jython-standalone

  # Force update and use pure Python resolver
  jgo --update --resolver=pure org.python:jython-standalone

  # List available versions
  jgo --list-versions org.scijava:scijava-common

  # Run from jgo.toml in current directory
  jgo

  # Run specific entrypoint from jgo.toml
  jgo --entrypoint repl
""",
        )

        # General options
        parser.add_argument(
            "-v",
            "--verbose",
            action="count",
            default=0,
            help="Verbose output (can be repeated: -vv, -vvv)",
        )
        parser.add_argument(
            "-q", "--quiet", action="store_true", help="Suppress all output"
        )

        # Cache and update options
        parser.add_argument(
            "-u",
            "--update",
            action="store_true",
            help="Update cached environment",
        )
        parser.add_argument(
            "--offline",
            action="store_true",
            help="Work offline (don't download)",
        )
        parser.add_argument(
            "--no-cache",
            action="store_true",
            help="Skip cache entirely, always rebuild",
        )

        # Resolver and linking options
        parser.add_argument(
            "--resolver",
            choices=["auto", "pure", "maven"],
            default="auto",
            help="Dependency resolver to use (default: auto)",
        )
        parser.add_argument(
            "--link",
            choices=["hard", "soft", "copy", "auto"],
            default="auto",
            help="How to link JARs into environment (default: auto)",
        )

        # Path options
        parser.add_argument(
            "--cache-dir",
            type=Path,
            metavar="PATH",
            help="Override cache directory (default: ~/.cache/jgo)",
        )
        parser.add_argument(
            "--repo-cache",
            type=Path,
            metavar="PATH",
            help="Override Maven repo cache (default: ~/.m2/repository)",
        )
        parser.add_argument(
            "-r",
            "--repository",
            action="append",
            metavar="NAME=URL",
            dest="repositories",
            help="Add remote Maven repository",
        )

        # Dependency management
        parser.add_argument(
            "-m",
            "--managed",
            action="store_true",
            help="Use dependency management (import scope)",
        )
        parser.add_argument(
            "--main-class",
            metavar="CLASS",
            help="Specify main class explicitly",
        )

        # Classpath options
        parser.add_argument(
            "--classpath-append",
            action="append",
            metavar="PATH",
            dest="classpath_append",
            help="Append to classpath (JARs, directories, etc.)",
        )

        # Backward compatibility options
        parser.add_argument(
            "--ignore-jgorc",
            action="store_true",
            help="Ignore ~/.jgorc configuration file",
        )

        # Deprecated aliases (jgo 1.x compatibility)
        parser.add_argument(
            "-U",
            "--force-update",
            dest="update",
            action="store_true",
            help="(Deprecated: use -u/--update) Force update from remote",
        )
        parser.add_argument(
            "-a",
            "--additional-jars",
            action="append",
            metavar="JAR",
            dest="classpath_append",
            help="(Deprecated: use --classpath-append) Add JARs to classpath",
        )
        parser.add_argument(
            "--additional-endpoints",
            nargs="+",
            metavar="ENDPOINT",
            dest="additional_endpoints",
            help="(Deprecated: use '+' syntax) Add additional endpoints",
        )
        parser.add_argument(
            "--link-type",
            dest="link",
            choices=["hard", "soft", "copy", "auto"],
            help="(Deprecated: use --link) How to link JARs",
        )
        parser.add_argument(
            "--log-level",
            help="(Deprecated: use -v/-vv/-vvv) Set log level",
        )

        # Information commands
        parser.add_argument(
            "--list-versions",
            action="store_true",
            help="List available versions and exit",
        )
        parser.add_argument(
            "--print-classpath",
            action="store_true",
            help="Print classpath and exit (don't run)",
        )
        parser.add_argument(
            "--print-java-info",
            action="store_true",
            help="Print Java version requirements and exit",
        )
        parser.add_argument(
            "--print-dependencies",
            action="store_true",
            help="Print dependency tree and exit",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done, but don't do it",
        )

        # Spec file options (jgo.toml)
        parser.add_argument(
            "-f",
            "--file",
            type=Path,
            metavar="FILE",
            help="Run from specific environment file (default: jgo.toml)",
        )
        parser.add_argument(
            "--entrypoint",
            metavar="NAME",
            help="Run specific entry point from jgo.toml",
        )
        parser.add_argument(
            "--init",
            metavar="ENDPOINT",
            help="Generate jgo.toml from endpoint",
        )
        parser.add_argument(
            "--list-entrypoints",
            action="store_true",
            help="Show available entry points in jgo.toml",
        )

        # Java options
        parser.add_argument(
            "--java-version",
            type=int,
            metavar="VERSION",
            help="Force specific Java version (e.g., 17)",
        )
        parser.add_argument(
            "--java-vendor",
            metavar="VENDOR",
            help="Prefer specific Java vendor (e.g., 'adoptium', 'zulu')",
        )
        parser.add_argument(
            "--java-source",
            choices=["auto", "system", "cjdk"],
            default="auto",
            help="Java source strategy (default: auto)",
        )

        # Positional: endpoint (optional - can be from jgo.toml)
        parser.add_argument(
            "endpoint",
            nargs="?",
            help=(
                "Maven endpoint (groupId:artifactId[:version][:classifier][:mainClass])"
            ),
        )

        # Remaining arguments after -- separators
        parser.add_argument(
            "remaining",
            nargs=argparse.REMAINDER,
            help="JVM options and app arguments (use -- to separate)",
        )

        return parser

    def parse_args(self, args: Optional[List[str]] = None) -> "ParsedArgs":
        """
        Parse command line arguments.

        Args:
            args: Arguments to parse (defaults to sys.argv[1:])

        Returns:
            ParsedArgs object with parsed arguments
        """
        parsed = self.parser.parse_args(args)

        # Split remaining args on --
        jvm_args, app_args = self._split_remaining_args(parsed.remaining)

        # Handle additional-endpoints by merging into endpoint with + syntax
        # Note: additional_endpoints is a list if specified, None otherwise
        endpoint = parsed.endpoint
        if parsed.additional_endpoints:
            additional_eps = (
                parsed.additional_endpoints
                if isinstance(parsed.additional_endpoints, list)
                else [parsed.additional_endpoints]
            )
            if endpoint:
                endpoint = "+".join([endpoint] + additional_eps)
            else:
                endpoint = "+".join(additional_eps)

        return ParsedArgs(
            # General
            verbose=parsed.verbose,
            quiet=parsed.quiet,
            # Cache and update
            update=parsed.update,
            offline=parsed.offline,
            no_cache=parsed.no_cache,
            # Resolver and linking
            resolver=parsed.resolver,
            link=parsed.link,
            # Paths
            cache_dir=parsed.cache_dir,
            repo_cache=parsed.repo_cache,
            repositories=self._parse_repositories(parsed.repositories),
            # Dependency management
            managed=parsed.managed,
            main_class=parsed.main_class,
            # Classpath
            classpath_append=parsed.classpath_append,
            # Backward compatibility
            ignore_jgorc=parsed.ignore_jgorc,
            additional_endpoints=parsed.additional_endpoints,
            log_level=parsed.log_level,
            # Information commands
            list_versions=parsed.list_versions,
            print_classpath=parsed.print_classpath,
            print_java_info=parsed.print_java_info,
            print_dependencies=parsed.print_dependencies,
            dry_run=parsed.dry_run,
            # Spec file
            file=parsed.file,
            entrypoint=parsed.entrypoint,
            init=parsed.init,
            list_entrypoints=parsed.list_entrypoints,
            # Java
            java_version=parsed.java_version,
            java_vendor=parsed.java_vendor,
            java_source=parsed.java_source,
            # Endpoint and args
            endpoint=endpoint,
            jvm_args=jvm_args,
            app_args=app_args,
        )

    def _split_remaining_args(
        self, remaining: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Split remaining args on -- separators.

        Format: [-- JVM_ARGS] [-- APP_ARGS]

        Returns:
            Tuple of (jvm_args, app_args)
        """
        if not remaining:
            return [], []

        # Find -- separators
        separators = [i for i, arg in enumerate(remaining) if arg == "--"]

        if not separators:
            # No separators - everything is app args
            return [], remaining

        if len(separators) == 1:
            # One separator - everything before is JVM args, after is app args
            sep_idx = separators[0]
            jvm_args = remaining[:sep_idx]
            app_args = remaining[sep_idx + 1 :]
            return jvm_args, app_args

        # Two or more separators
        first_sep = separators[0]
        second_sep = separators[1]
        jvm_args = remaining[:first_sep]
        app_args = remaining[second_sep + 1 :]
        return jvm_args, app_args

    def _parse_repositories(self, repositories: Optional[List[str]]) -> Optional[dict]:
        """
        Parse repository arguments in NAME=URL format.

        Args:
            repositories: List of "NAME=URL" strings

        Returns:
            Dictionary mapping names to URLs, or None if no repositories
        """
        if not repositories:
            return None

        result = {}
        for repo in repositories:
            if "=" not in repo:
                raise ValueError(
                    f"Invalid repository format '{repo}': expected NAME=URL"
                )
            name, url = repo.split("=", 1)
            result[name] = url

        return result


class ParsedArgs:
    """
    Container for parsed CLI arguments.
    """

    def __init__(
        self,
        # General
        verbose: int = 0,
        quiet: bool = False,
        # Cache and update
        update: bool = False,
        offline: bool = False,
        no_cache: bool = False,
        # Resolver and linking
        resolver: str = "auto",
        link: str = "auto",
        # Paths
        cache_dir: Optional[Path] = None,
        repo_cache: Optional[Path] = None,
        repositories: Optional[dict] = None,
        # Dependency management
        managed: bool = False,
        main_class: Optional[str] = None,
        # Classpath
        classpath_append: Optional[List[str]] = None,
        # Backward compatibility
        ignore_jgorc: bool = False,
        additional_endpoints: Optional[List[str]] = None,
        log_level: Optional[str] = None,
        # Information commands
        list_versions: bool = False,
        print_classpath: bool = False,
        print_java_info: bool = False,
        print_dependencies: bool = False,
        dry_run: bool = False,
        # Spec file
        file: Optional[Path] = None,
        entrypoint: Optional[str] = None,
        init: Optional[str] = None,
        list_entrypoints: bool = False,
        # Java
        java_version: Optional[int] = None,
        java_vendor: Optional[str] = None,
        java_source: str = "auto",
        # Endpoint and args
        endpoint: Optional[str] = None,
        jvm_args: Optional[List[str]] = None,
        app_args: Optional[List[str]] = None,
    ):
        # General
        self.verbose = verbose
        self.quiet = quiet
        # Cache and update
        self.update = update
        self.offline = offline
        self.no_cache = no_cache
        # Resolver and linking
        self.resolver = resolver
        self.link = link
        # Paths
        self.cache_dir = cache_dir
        self.repo_cache = repo_cache
        self.repositories = repositories or {}
        # Dependency management
        self.managed = managed
        self.main_class = main_class
        # Classpath
        self.classpath_append = classpath_append or []
        # Backward compatibility
        self.ignore_jgorc = ignore_jgorc
        self.additional_endpoints = additional_endpoints
        self.log_level = log_level
        # Information commands
        self.list_versions = list_versions
        self.print_classpath = print_classpath
        self.print_java_info = print_java_info
        self.print_dependencies = print_dependencies
        self.dry_run = dry_run
        # Spec file
        self.file = file
        self.entrypoint = entrypoint
        self.init = init
        self.list_entrypoints = list_entrypoints
        # Java
        self.java_version = java_version
        self.java_vendor = java_vendor
        self.java_source = java_source
        # Endpoint and args
        self.endpoint = endpoint
        self.jvm_args = jvm_args or []
        self.app_args = app_args or []

    def is_spec_mode(self) -> bool:
        """Check if running in spec file mode (jgo.toml)."""
        return bool(
            self.file
            or self.entrypoint
            or self.init
            or self.list_entrypoints
            or (not self.endpoint and Path("jgo.toml").exists())
        )

    def get_spec_file(self) -> Path:
        """Get the spec file path (defaults to jgo.toml)."""
        return self.file or Path("jgo.toml")

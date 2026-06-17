"""
Utilities for building parsed CLI arguments.

Separate module to avoid circular imports.
"""

from __future__ import annotations

from pathlib import Path

from ..maven import detect_os_properties


def _looks_like_pom(value: str) -> bool:
    """True if the string refers to a local POM file or a dir containing one."""
    value = value.strip()
    if value.endswith(".xml"):
        return True
    path = Path(value).expanduser()
    return path.is_dir() and (path / "pom.xml").is_file()


def resolve_pom_input(endpoint: str | None) -> Path | None:
    """
    Resolve an endpoint argument that points at a local POM file.

    Accepts either a path to a ``*.xml`` file or a directory containing
    ``pom.xml``. Returns the resolved POM path, or None if the endpoint is an
    ordinary coordinate expression.

    Raises:
        ValueError: if a POM file is combined with other coordinates via '+'.
    """
    if not endpoint:
        return None

    parts = endpoint.split("+")
    pom_parts = [p for p in parts if _looks_like_pom(p)]
    if not pom_parts:
        return None
    if len(parts) > 1:
        raise ValueError(
            "A local POM file cannot be combined with other coordinates using '+'."
        )

    path = Path(pom_parts[0].strip()).expanduser()
    if path.is_dir():
        path = path / "pom.xml"
    return path


def classify_javainfo_input(arg: str) -> tuple[str, Path]:
    """
    Classify a single ``jgo info javainfo`` argument.

    Returns a ``(kind, path)`` tuple where ``kind`` is one of:

      - ``"pom"``:        a local POM file, or a directory containing ``pom.xml``
      - ``"jar"``:        a local ``.jar`` file
      - ``"class"``:      a local ``.class`` file
      - ``"dir"``:        a local directory (scanned for ``.jar``/``.class`` files)
      - ``"coordinate"``: a Maven coordinate / endpoint expression

    For ``"coordinate"`` the returned path is undefined; otherwise it is the
    resolved local path. ``.jar``/``.class`` inputs are classified by suffix
    regardless of whether the file exists, so the caller can report a missing
    file rather than misinterpreting it as a coordinate. A directory containing
    ``pom.xml`` is treated as a project (``"pom"``), not a loose ``"dir"``.
    """
    value = arg.strip()
    if _looks_like_pom(value):
        path = Path(value).expanduser()
        if path.is_dir():
            path = path / "pom.xml"
        return "pom", path

    path = Path(value).expanduser()
    if value.endswith(".jar"):
        return "jar", path
    if value.endswith(".class"):
        return "class", path
    if path.is_dir():
        return "dir", path
    return "coordinate", Path()


class ParsedArgs:
    """
    Container for parsed CLI arguments.
    """

    def __init__(
        self,
        # General
        verbose: int = 0,
        quiet: bool = False,
        dry_run: bool = False,
        # Cache and update
        update: bool = False,
        offline: bool = False,
        no_cache: bool = False,
        timeout: int = 10,
        # Dependency resolution
        resolver: str = "auto",
        direct_only: bool = False,
        include_optional: bool = False,
        optional_depth: int | None = None,
        # Environment construction
        links: str | None = None,
        # Paths
        cache_dir: Path | None = None,
        repo_cache: Path | None = None,
        repositories: dict | None = None,
        # Program to run
        main_class: str | None = None,
        # Classpath
        classpath_append: list[str] | None = None,
        # Backward compatibility
        ignore_config: bool = False,
        additional_endpoints: list[str] | None = None,
        log_level: str | None = None,
        # Spec file
        file: Path | None = None,
        entrypoint: str | None = None,
        init: str | None = None,
        list_entrypoints: bool = False,
        # Java
        java_version: int | None = None,
        java_vendor: str | None = None,
        use_system_java: bool = False,
        # JVM options
        gc_options: tuple[str, ...] | None = None,
        max_heap: str | None = None,
        min_heap: str | None = None,
        # Profile constraints
        os_name: str | None = None,
        os_family: str | None = None,
        os_arch: str | None = None,
        os_version: str | None = None,
        properties: dict[str, str] | None = None,
        # Lenient mode
        lenient: bool = False,
        # Module mode
        class_path_only: bool = False,
        module_path_only: bool = False,
        # Mode override
        force_global: bool = False,
        # Endpoint and args
        endpoint: str | None = None,
        jvm_args: list[str] | None = None,
        app_args: list[str] | None = None,
        # Command (for new command-based interface)
        command: str | None = None,
    ):
        # General
        self.verbose = verbose
        self.quiet = quiet
        self.dry_run = dry_run
        # Cache and update
        self.update = update
        self.offline = offline
        self.no_cache = no_cache
        self.timeout = timeout
        # Dependency resolution
        self.resolver = resolver
        self.direct_only = direct_only
        self.include_optional = include_optional
        self.optional_depth = optional_depth
        # Environment construction
        self.links = links
        # Paths
        self.cache_dir = cache_dir
        self.repo_cache = repo_cache
        self.repositories = repositories or {}
        # Program to run
        self.main_class = main_class
        # Classpath
        self.classpath_append = classpath_append or []
        # Backward compatibility
        self.ignore_config = ignore_config
        self.additional_endpoints = additional_endpoints
        self.log_level = log_level
        # Spec file
        self.file = file
        self.entrypoint = entrypoint
        self.init = init
        self.list_entrypoints = list_entrypoints
        # Java
        self.java_version = java_version
        self.java_vendor = java_vendor
        self.use_system_java = use_system_java
        # JVM options
        self.gc_options = gc_options
        self.max_heap = max_heap
        self.min_heap = min_heap
        # Profile constraints
        self.os_name = os_name
        self.os_family = os_family
        self.os_arch = os_arch
        self.os_version = os_version
        self.properties = properties or {}
        # Lenient mode
        self.lenient = lenient
        # Module mode
        self.class_path_only = class_path_only
        self.module_path_only = module_path_only
        # Mode override
        self.force_global = force_global
        # Endpoint and args
        self.endpoint = endpoint
        self.jvm_args = jvm_args or []
        self.app_args = app_args or []
        # Command (for new command-based interface)
        self.command = command

    @property
    def module_mode(self) -> str:
        """Derive module mode from flags."""
        if self.class_path_only:
            return "class-path-only"
        elif self.module_path_only:
            return "module-path-only"
        return "auto"

    def get_effective_optional_depth(self) -> int:
        """
        Get the effective optional_depth based on command and flags.

        Returns:
            int | None: The optional_depth to use for dependency resolution
        """
        # If explicitly set via --optional-depth, use that value
        if self.optional_depth is not None:
            return self.optional_depth

        # If --include-optional flag is set, use depth 1
        return 1 if self.include_optional else 0

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


# Platform mappings: platform -> (os_name, os_family, os_arch)
PLATFORMS: dict[str, tuple[str, str, str]] = {
    # Linux
    "linux": ("Linux", "unix", "auto"),
    "linux-arm64": ("Linux", "unix", "aarch64"),
    "linux-x32": ("Linux", "unix", "i386"),
    "linux-x64": ("Linux", "unix", "amd64"),
    # macOS
    "macos": ("Mac OS X", "mac", "auto"),
    "macos-arm64": ("Mac OS X", "mac", "aarch64"),
    "macos-x32": ("Mac OS X", "mac", "x86"),
    "macos-x64": ("Mac OS X", "mac", "x86_64"),
    # Windows
    "windows": ("Windows", "windows", "auto"),
    "windows-arm64": ("Windows", "windows", "aarch64"),
    "windows-x32": ("Windows", "windows", "x86"),
    "windows-x64": ("Windows", "windows", "amd64"),
    # BSD variants
    "freebsd": ("FreeBSD", "unix", "auto"),
    "freebsd-x64": ("FreeBSD", "unix", "amd64"),
    "openbsd": ("OpenBSD", "unix", "auto"),
    "openbsd-x64": ("OpenBSD", "unix", "amd64"),
    "netbsd": ("NetBSD", "unix", "auto"),
    "netbsd-x64": ("NetBSD", "unix", "amd64"),
    # Solaris/SunOS
    "solaris": ("SunOS", "unix", "auto"),
    "solaris-x64": ("SunOS", "unix", "amd64"),
    # AIX
    "aix": ("AIX", "unix", "auto"),
    "aix-ppc64": ("AIX", "unix", "ppc64"),
}

# Convenience aliases
PLATFORM_ALIASES: dict[str, str] = {
    "linux32": "linux-x32",
    "linux64": "linux-x64",
    "macos32": "macos-x32",
    "macos64": "macos-x64",
    "win32": "windows-x32",
    "win64": "windows-x64",
}

# Windows os.arch values:
#
# | os.arch value | OpenJDK versions |
# |---------------|------------------|
# | aarch64       | 16 - 25+         |
# | amd64         | 6 - 25+          |
# | ia64          | 6 - 9            |
# | x86           | 6 - 23           |
# | unknown       | 6 - 25+          |
#
# As specified in the Windows java_props_md.c:
# - https://github.com/openjdk/jdk6/blob/jdk6-b49/jdk/src/windows/native/java/lang/java_props_md.c#L858-L866
# - https://github.com/openjdk/jdk/blob/jdk7-b147/jdk/src/windows/native/java/lang/java_props_md.c#L467-L474
# - https://github.com/openjdk/jdk/blob/jdk8-b120/jdk/src/windows/native/java/lang/java_props_md.c#L468-L476
# - https://github.com/openjdk/jdk/blob/jdk-9%2B181/jdk/src/java.base/windows/native/libjava/java_props_md.c#L562-L570
# - https://github.com/openjdk/jdk/blob/jdk-10%2B46/src/java.base/windows/native/libjava/java_props_md.c#L562-L568
# - https://github.com/openjdk/jdk/blob/jdk-11-ga/src/java.base/windows/native/libjava/java_props_md.c#L562-L568
# - https://github.com/openjdk/jdk/blob/jdk-12-ga/src/java.base/windows/native/libjava/java_props_md.c#L573-L579
# - https://github.com/openjdk/jdk/blob/jdk-13-ga/src/java.base/windows/native/libjava/java_props_md.c#L567-L573
# - https://github.com/openjdk/jdk/blob/jdk-14-ga/src/java.base/windows/native/libjava/java_props_md.c#L567-L573
# - https://github.com/openjdk/jdk/blob/jdk-15-ga/src/java.base/windows/native/libjava/java_props_md.c#L568-L574
# - https://github.com/openjdk/jdk/blob/jdk-16-ga/src/java.base/windows/native/libjava/java_props_md.c#L568-L576
# - https://github.com/openjdk/jdk/blob/jdk-17-ga/src/java.base/windows/native/libjava/java_props_md.c#L571-L579
# - https://github.com/openjdk/jdk/blob/jdk-18-ga/src/java.base/windows/native/libjava/java_props_md.c#L585-L593
# - https://github.com/openjdk/jdk/blob/jdk-19-ga/src/java.base/windows/native/libjava/java_props_md.c#L580-L588
# - https://github.com/openjdk/jdk/blob/jdk-20-ga/src/java.base/windows/native/libjava/java_props_md.c#L580-L588
# - https://github.com/openjdk/jdk/blob/jdk-21-ga/src/java.base/windows/native/libjava/java_props_md.c#L581-L589
# - https://github.com/openjdk/jdk/blob/jdk-22-ga/src/java.base/windows/native/libjava/java_props_md.c#L551-L559
# - https://github.com/openjdk/jdk/blob/jdk-23-ga/src/java.base/windows/native/libjava/java_props_md.c#L551-L559
# - https://github.com/openjdk/jdk/blob/jdk-24-ga/src/java.base/windows/native/libjava/java_props_md.c#L553-L559
# - https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/windows/native/libjava/java_props_md.c#L557-L563


def expand_platform(platform: str | None) -> tuple[str | None, str | None, str | None]:
    """
    Expand a platform shorthand to (os_name, os_family, os_arch).

    Args:
        platform: Platform name like 'linux-x64' or alias like 'win64'

    Returns:
        Tuple of (os_name, os_family, os_arch), or (None, None, None) if not found
    """
    if platform is None:
        return None, None, None

    # Resolve alias first
    platform = PLATFORM_ALIASES.get(platform, platform)

    # Look up in platforms
    return PLATFORMS.get(platform) or (None, None, None)


def parse_remaining(remaining):
    """
    Parse remaining args for JVM and app arguments.

    Format: [-- JVM_ARGS] [-- APP_ARGS]

    Returns:
        Tuple of (jvm_args, app_args)
    """
    if not remaining:
        return [], []

    # Convert to list
    remaining = list(remaining)

    # Find -- separators
    separators = [i for i, arg in enumerate(remaining) if arg == "--"]

    if not separators:
        # No separators - everything is app args
        return [], remaining

    if len(separators) == 1:
        # One separator
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


def build_parsed_args(opts, endpoint=None, jvm_args=None, app_args=None, command=None):
    """Build a ParsedArgs object from Click options."""
    # Parse repositories from NAME:URL format
    repositories = {}
    if opts.get("repository"):
        for repo in opts["repository"]:
            if ":" in repo:
                name, url = repo.split(":", 1)
                repositories[name] = url

    # Parse properties from KEY=VALUE format
    properties = {}
    if opts.get("properties"):
        for prop in opts["properties"]:
            if "=" in prop:
                key, value = prop.split("=", 1)
                properties[key] = value

    # Expand platform to os_name, os_family, os_arch.
    # Explicit --os-name/--os-family/--os-arch override --platform values.
    plat_name, plat_family, plat_arch = expand_platform(opts.get("platform"))
    os_name = opts.get("os_name") or plat_name
    os_family = opts.get("os_family") or plat_family
    os_arch = opts.get("os_arch") or plat_arch

    # Populate remaining None and "auto" values from the current system.
    # This ensures we always have concrete values for profile activation,
    # matching Maven's behavior where OS properties are always populated.
    detected_name, detected_family, detected_arch = detect_os_properties()
    if os_name is None or os_name == "auto":
        os_name = detected_name
    if os_family is None or os_family == "auto":
        os_family = detected_family
    if os_arch is None or os_arch == "auto":
        os_arch = detected_arch

    return ParsedArgs(
        # General
        verbose=opts.get("verbose", 0),
        quiet=opts.get("quiet", False),
        dry_run=opts.get("dry_run", False),
        # Cache and update
        update=opts.get("update", False),
        offline=opts.get("offline", False),
        no_cache=opts.get("no_cache", False),
        timeout=opts.get("timeout", 10),
        # Dependency resolution
        resolver=opts.get("resolver", "auto"),
        direct_only=opts.get("direct_only", False),
        include_optional=opts.get("include_optional", False),
        optional_depth=opts.get("optional_depth"),
        # Environment construction
        links=opts.get("links"),
        # Paths
        cache_dir=opts.get("cache_dir"),
        repo_cache=opts.get("repo_cache"),
        repositories=repositories,
        # Program to run
        main_class=opts.get("main_class"),
        # Classpath
        classpath_append=list(opts.get("add_classpath", [])),
        # Backward compatibility
        ignore_config=opts.get("ignore_config", False),
        additional_endpoints=None,
        log_level=None,
        # Spec file
        file=opts.get("file"),
        entrypoint=opts.get("entrypoint"),
        init=opts.get("init"),
        list_entrypoints=opts.get("list_entrypoints", False),
        # Java
        java_version=opts.get("java_version"),
        java_vendor=opts.get("java_vendor"),
        use_system_java=opts.get("use_system_java", False),
        # JVM options
        gc_options=opts.get("gc_options"),
        max_heap=opts.get("max_heap"),
        min_heap=opts.get("min_heap"),
        # Profile constraints
        os_name=os_name,
        os_family=os_family,
        os_arch=os_arch,
        os_version=opts.get("os_version"),
        properties=properties,
        # Lenient mode
        lenient=opts.get("lenient", False),
        # Module mode
        class_path_only=opts.get("class_path_only", False),
        module_path_only=opts.get("module_path_only", False),
        # Mode override
        force_global=opts.get("force_global", False),
        # Endpoint and args
        endpoint=endpoint,
        jvm_args=jvm_args or [],
        app_args=app_args or [],
        # Command
        command=command,
    )

Tests jgo help command.

  $ jgo help
  * (glob)
   Usage: jgo [OPTIONS] COMMAND [ARGS]...* (glob)
  * (glob)
   Environment manager and launcher for Java programs.* (glob)
   Launch Java applications directly from Maven coordinates, build reproducible* (glob)
   environments, manage Java versions, and resolve dependencies -- without manual* (glob)
   installation.* (glob)
  * (glob)
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --version                                      Show jgo version and exit.    │
  │ --ignore-config                                Ignore ~/.jgorc configuration │
  │                                                file.                         │
  │ --module-path-only                             Force all JARs to module-path │
  │                                                (treat as modular).           │
  │ --class-path-only                              Force all JARs to classpath   │
  │                                                (disable module detection).   │
  │ --lenient                                      Warn instead of failing on    │
  │                                                unresolved dependencies. [env │
  │                                                var: JGO_LENIENT]             │
  │ --link                  [hard|soft|copy|auto]  How to link JARs: hard, soft, │
  │                                                copy, or auto (default)       │
  │ --property          -D  KEY=VALUE              Set property for profile      │
  │                                                activation.                   │
  │ --os-version            VERSION                Set OS version for profile    │
  │                                                activation (e.g.,             │
  │                                                '5.1.2600').                  │
  │ --os-arch               ARCH                   Set OS architecture for       │
  │                                                profile activation (e.g.,     │
  │                                                'amd64', 'aarch64'). Use      │
  │                                                'auto' to auto-detect.        │
  │                                                Overrides --platform.         │
  │ --os-family             FAMILY                 Set OS family for profile     │
  │                                                activation (e.g., 'unix',     │
  │                                                'windows'). Use 'auto' to     │
  │                                                auto-detect. Overrides        │
  │                                                --platform.                   │
  │ --os-name               NAME                   Set OS name for profile       │
  │                                                activation (e.g., 'Linux',    │
  │                                                'Windows'). Use 'auto' to     │
  │                                                auto-detect. Overrides        │
  │                                                --platform.                   │
  │ --platform              PLATFORM               Target platform for profile   │
  │                                                activation. Sets os-name,     │
  │                                                os-family, and os-arch        │
  │                                                together. Choices: linux,     │
  │                                                linux-arm64, linux-x32,       │
  │                                                linux-x64, macos,             │
  │                                                macos-arm64, macos-x32,       │
  │                                                macos-x64, windows,           │
  │                                                windows-arm64, windows-x32,   │
  │                                                windows-x64, freebsd,         │
  │                                                freebsd-x64, openbsd,         │
  │                                                openbsd-x64, netbsd,          │
  │                                                netbsd-x64, solaris,          │
  │                                                solaris-x64, aix, aix-ppc64.  │
  │                                                Aliases: linux32=linux-x32,   │
  │                                                linux64=linux-x64,            │
  │                                                macos32=macos-x32,            │
  │                                                macos64=macos-x64,            │
  │                                                win32=windows-x32,            │
  │                                                win64=windows-x64.            │
  │ --system-java                                  Use system Java instead of    │
  │                                                downloading Java on demand.   │
  │ --java-vendor           VENDOR                 Prefer specific Java vendor   │
  │                                                (e.g., 'adoptium', 'zulu').   │
  │ --java-version          VERSION                Force specific Java version   │
  │                                                (e.g., 17). [env var:         │
  │                                                JAVA_VERSION]                 │
  │ --repository        -r  NAME=URL               Add remote Maven repository.  │
  │ --resolver              [auto|python|mvn]      Dependency resolver: auto     │
  │                                                (default), python, or mvn     │
  │ --repo-cache            PATH                   Override Maven repo cache.    │
  │                                                [env var: M2_REPO]            │
  │ --cache-dir             PATH                   Override cache directory.     │
  │                                                [env var: JGO_CACHE_DIR]      │
  │ --no-cache                                     Skip cache entirely, always   │
  │                                                rebuild. [env var:            │
  │                                                JGO_NO_CACHE]                 │
  │ --offline                                      Work offline, don't download. │
  │                                                [env var: JGO_OFFLINE]        │
  │ --update            -u                         Update cached environment.    │
  │                                                [env var: JGO_UPDATE]         │
  │ --dry-run                                      Show what would be done       │
  │                                                without doing it. Note: while │
  │                                                this mode prevents the        │
  │                                                primary action (e.g. running  │
  │                                                Java, creating files), jgo    │
  │                                                may still download            │
  │                                                dependencies and build cached │
  │                                                environments as needed to     │
  │                                                report accurate information.  │
  │ --file              -f  FILE                   Use specific environment file │
  │                                                (default: jgo.toml).          │
  │ --color                 [auto|always|never]    Control colored output: auto  │
  │                                                (default, color if TTY),      │
  │                                                always (force color), never   │
  │                                                (disable color). [env var:    │
  │                                                COLOR]                        │
  │ --quiet             -q                         Suppress all output.          │
  │ --verbose           -v  INTEGER RANGE          Verbose output (can be        │
  │                                                repeated: -vv, -vvv).         │
  │ --help                                         Show this message and exit.   │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ╭─ Commands ───────────────────────────────────────────────────────────────────╮
  │ add        Add dependencies to jgo.toml.                                     │
  │ config     Manage jgo configuration.                                         │
  │ help       Show help for jgo or a specific command.                          │
  │ info       Show information about environment or artifact.                   │
  │ init       Create a new jgo.toml environment file.                           │
  │ list       List resolved dependencies (flat list).                           │
  │ lock       Update jgo.lock.toml without building environment.                │
  │ remove     Remove dependencies from jgo.toml.                                │
  │ run        Run a Java application from Maven coordinates or jgo.toml.        │
  │ search     Search for artifacts in Maven repositories.                       │
  │ sync       Resolve dependencies and build environment.                       │
  │ tree       Show dependency tree.                                             │
  │ update     Update dependencies to latest versions.                           │
  │ version    Display jgo's version.                                            │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Tests jgo --color flag.

Test --color=never removes ANSI color codes.

  $ jgo --color=never remove
                                                                                  
   Usage: jgo remove [OPTIONS] COORDINATES...                                     
                                                                                  
   Try 'jgo remove --help' for help                                               
  ╭─ Error ──────────────────────────────────────────────────────────────────────╮
  │ Missing argument 'COORDINATES...'.                                           │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
  [2]

Test --color=always forces ANSI color codes.

  $ jgo --color=always remove
                                                                                  
   \x1b[33mUsage:\x1b[0m \x1b[1mjgo remove\x1b[0m [\x1b[1;36mOPTIONS\x1b[0m] \x1b[1;36mCOORDINATES\x1b[0m...                                      (esc)
                                                                                  
  \x1b[2m \x1b[0m\x1b[2mTry \x1b[0m\x1b[1;2;36m'jgo remove --help'\x1b[0m\x1b[2m for help\x1b[0m\x1b[2m                                              \x1b[0m\x1b[2m \x1b[0m (esc)
  \x1b[31m╭─\x1b[0m\x1b[31m Error \x1b[0m\x1b[31m─────────────────────────────────────────────────────────────────────\x1b[0m\x1b[31m─╮\x1b[0m (esc)
  \x1b[31m│\x1b[0m Missing argument 'COORDINATES...'.                                           \x1b[31m│\x1b[0m (esc)
  \x1b[31m╰──────────────────────────────────────────────────────────────────────────────╯\x1b[0m (esc)
                                                                                  
  [2]

Test --color with different commands.

  $ jgo --color=never help
                                                                                  
   Usage: jgo [OPTIONS] COMMAND [ARGS]...                                         
                                                                                  
   Environment manager and launcher for Java programs.                            
   Launch Java applications directly from Maven coordinates, build reproducible   
   environments, manage Java versions, and resolve dependencies -- without manual 
   installation.                                                                  
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --version                                          Show jgo version and      │
  │                                                    exit.                     │
  │ --ignore-config                                    Ignore ~/.jgorc           │
  │                                                    configuration file.       │
  │ --module-path-only                                 Force all JARs to         │
  │                                                    module-path (treat as     │
  │                                                    modular).                 │
  │ --class-path-only                                  Force all JARs to         │
  │                                                    classpath (disable module │
  │                                                    detection).               │
  │ --lenient                                          Warn instead of failing   │
  │                                                    on unresolved             │
  │                                                    dependencies. [env var:   │
  │                                                    JGO_LENIENT]              │
  │ --link                  [hard|soft|copy|auto]      How to link JARs: hard,   │
  │                                                    soft, copy, or auto       │
  │                                                    (default)                 │
  │ --property          -D  KEY=VALUE                  Set property for profile  │
  │                                                    activation.               │
  │ --os-version            VERSION                    Set OS version for        │
  │                                                    profile activation (e.g., │
  │                                                    '5.1.2600').              │
  │ --os-arch               ARCH                       Set OS architecture for   │
  │                                                    profile activation (e.g., │
  │                                                    'amd64', 'aarch64'). Use  │
  │                                                    'auto' to auto-detect.    │
  │                                                    Overrides --platform.     │
  │ --os-family             FAMILY                     Set OS family for profile │
  │                                                    activation (e.g., 'unix', │
  │                                                    'windows'). Use 'auto' to │
  │                                                    auto-detect. Overrides    │
  │                                                    --platform.               │
  │ --os-name               NAME                       Set OS name for profile   │
  │                                                    activation (e.g.,         │
  │                                                    'Linux', 'Windows'). Use  │
  │                                                    'auto' to auto-detect.    │
  │                                                    Overrides --platform.     │
  │ --platform              PLATFORM                   Target platform for       │
  │                                                    profile activation. Sets  │
  │                                                    os-name, os-family, and   │
  │                                                    os-arch together.         │
  │                                                    Choices: linux,           │
  │                                                    linux-arm64, linux-x32,   │
  │                                                    linux-x64, macos,         │
  │                                                    macos-arm64, macos-x32,   │
  │                                                    macos-x64, windows,       │
  │                                                    windows-arm64,            │
  │                                                    windows-x32, windows-x64, │
  │                                                    freebsd, freebsd-x64,     │
  │                                                    openbsd, openbsd-x64,     │
  │                                                    netbsd, netbsd-x64,       │
  │                                                    solaris, solaris-x64,     │
  │                                                    aix, aix-ppc64. Aliases:  │
  │                                                    linux32=linux-x32,        │
  │                                                    linux64=linux-x64,        │
  │                                                    macos32=macos-x32,        │
  │                                                    macos64=macos-x64,        │
  │                                                    win32=windows-x32,        │
  │                                                    win64=windows-x64.        │
  │ --min-heap              SIZE                       Minimum/initial heap size │
  │                                                    (e.g., 512M, 1G).         │
  │ --max-heap              SIZE                       Maximum heap size (e.g.,  │
  │                                                    4G, 512M). Overrides      │
  │                                                    auto-detection.           │
  │ --gc                    FLAG                       GC options. Use shorthand │
  │                                                    (e.g., --gc=G1, --gc=Z)   │
  │                                                    or explicit form          │
  │                                                    (--gc=-XX:+UseZGC).       │
  │                                                    Special values: 'auto'    │
  │                                                    (smart defaults), 'none'  │
  │                                                    (disable GC flags). Can   │
  │                                                    be repeated.              │
  │ --system-java                                      Use system Java instead   │
  │                                                    of downloading Java on    │
  │                                                    demand.                   │
  │ --java-vendor           VENDOR                     Prefer specific Java      │
  │                                                    vendor (e.g., 'adoptium', │
  │                                                    'zulu').                  │
  │ --java-version          VERSION                    Force specific Java       │
  │                                                    version (e.g., 17). [env  │
  │                                                    var: JAVA_VERSION]        │
  │ --include-optional                                 Include optional          │
  │                                                    dependencies of endpoint  │
  │                                                    coordinates in the        │
  │                                                    environment. [env var:    │
  │                                                    JGO_INCLUDE_OPTIONAL]     │
  │ --repository        -r  NAME:URL                   Add remote Maven          │
  │                                                    repository.               │
  │ --resolver              [auto|python|mvn]          Dependency resolver: auto │
  │                                                    (default), python, or mvn │
  │ --repo-cache            PATH                       Override Maven repo       │
  │                                                    cache. [env var: M2_REPO] │
  │ --cache-dir             PATH                       Override cache directory. │
  │                                                    [env var: JGO_CACHE_DIR]  │
  │ --no-cache                                         Skip cache entirely,      │
  │                                                    always rebuild. [env var: │
  │                                                    JGO_NO_CACHE]             │
  │ --offline                                          Work offline, don't       │
  │                                                    download. [env var:       │
  │                                                    JGO_OFFLINE]              │
  │ --update            -u                             Update cached             │
  │                                                    environment. [env var:    │
  │                                                    JGO_UPDATE]               │
  │ --dry-run                                          Show what would be done   │
  │                                                    without doing it. Note:   │
  │                                                    while this mode prevents  │
  │                                                    the primary action (e.g.  │
  │                                                    running Java, creating    │
  │                                                    files), jgo may still     │
  │                                                    download dependencies and │
  │                                                    build cached environments │
  │                                                    as needed to report       │
  │                                                    accurate information.     │
  │ --file              -f  FILE                       Use specific environment  │
  │                                                    file (default: jgo.toml). │
  │ --color                 [auto|rich|styled|plain|a  Control output            │
  │                         lways|never]               formatting: auto          │
  │                                                    (default, detect TTY),    │
  │                                                    rich (force color+style), │
  │                                                    styled (bold/italic only, │
  │                                                    no color), plain (no ANSI │
  │                                                    codes). Aliases:          │
  │                                                    always=rich, never=plain. │
  │                                                    [env var: COLOR]          │
  │ --no-wrap                                          Disable text wrapping in  │
  │                                                    rich output (trees,       │
  │                                                    tables, panels). Long     │
  │                                                    lines will extend beyond  │
  │                                                    terminal width.           │
  │ --quiet             -q                             Suppress all output.      │
  │ --verbose           -v  INTEGER RANGE              Verbose output (can be    │
  │                                                    repeated: -vv, -vvv).     │
  │ --help                                             Show this message and     │
  │                                                    exit.                     │
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

  $ jgo --color=always version
  jgo 2.0.0.dev0

  $ jgo --color=never version
  jgo 2.0.0.dev0

Test --color affects help output.

  $ jgo --color=never run --help
                                                                                  
   Usage: jgo run [OPTIONS] [ENDPOINT] [REMAINING]...                             
                                                                                  
   Run a Java application from Maven coordinates or jgo.toml.                     
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --main-class     CLASS  Main class to run (supports auto-completion for      │
  │                         simple names)                                        │
  │ --entrypoint     NAME   Run specific entrypoint from jgo.toml                │
  │ --add-classpath  PATH   Append to classpath (JARs, directories, etc.)        │
  │ --help                  Show this message and exit.                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
   TIP: Use jgo --dry-run run to see the command without executing it.            
                                                                                  

Test --color with info commands.

  $ jgo --color=never info
                                                                                  
   Usage: jgo info [OPTIONS] COMMAND [ARGS]...                                    
                                                                                  
   Show information about environment or artifact.                                
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ╭─ Commands ───────────────────────────────────────────────────────────────────╮
  │ classpath        Show classpath.                                             │
  │ deplist          Show flat list of dependencies.                             │
  │ deptree          Show dependency tree.                                       │
  │ entrypoints      Show entrypoints from jgo.toml.                             │
  │ envdir           Show environment directory path.                            │
  │ jars             Show all JAR paths (classpath + module-path).               │
  │ javainfo         Show Java version requirements.                             │
  │ mains            Show classes with public main methods.                      │
  │ manifest         Show JAR manifest.                                          │
  │ modulepath       Show module-path.                                           │
  │ pom              Show POM content.                                           │
  │ versions         List available versions of an artifact.                     │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
   TIP: To see the launch command, use: jgo --dry-run run <endpoint>              
                                                                                  
  [2]

Test --color respects environment variable COLOR.

  $ COLOR=always jgo remove
                                                                                  
   \x1b[33mUsage:\x1b[0m \x1b[1mjgo remove\x1b[0m [\x1b[1;36mOPTIONS\x1b[0m] \x1b[1;36mCOORDINATES\x1b[0m...                                      (esc)
                                                                                  
  \x1b[2m \x1b[0m\x1b[2mTry \x1b[0m\x1b[1;2;36m'jgo remove --help'\x1b[0m\x1b[2m for help\x1b[0m\x1b[2m                                              \x1b[0m\x1b[2m \x1b[0m (esc)
  \x1b[31m╭─\x1b[0m\x1b[31m Error \x1b[0m\x1b[31m─────────────────────────────────────────────────────────────────────\x1b[0m\x1b[31m─╮\x1b[0m (esc)
  \x1b[31m│\x1b[0m Missing argument 'COORDINATES...'.                                           \x1b[31m│\x1b[0m (esc)
  \x1b[31m╰──────────────────────────────────────────────────────────────────────────────╯\x1b[0m (esc)
                                                                                  
  [2]

Test that coordinate formatting prevents emoji substitution.
Coordinates use dim colons in rich mode to prevent patterns like :bear:
from being converted to emoji (🐻). Without proper markup, Rich would
interpret such patterns as emoji codes.

Verify that "bear" appears as text, not emoji (would be 🐻 without escaping).
If emoji substitution were happening, grep wouldn't find the text "bear".
And filter to known artifact to avoid brittleness from search result changes.

  $ jgo --color=plain search bear | grep bear | grep com.github.qydq:
  *. com.github.qydq:bear:* (glob)

  $ jgo --color=rich search bear | grep bear | grep com.github.qydq:
  *. com.github.qydq:bear:* (glob)

Tests jgo help command.

Test main help output.

  $ jgo help
                                                                                  
   Usage: jgo [OPTIONS] COMMAND [ARGS]...                                         
                                                                                  
   Environment manager and launcher for Java programs.                            
   Launch Java applications directly from Maven coordinates, build reproducible   
   environments, manage Java versions, and resolve dependencies -- without manual 
   installation.                                                                  
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --version                                          Show jgo version and      │
  │                                                    exit.                     │
  │ --ignore-config                                    Ignore ~/.config/jgo.conf │
  │                                                    file.                     │
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
  │ --wrap                  [smart|raw|crop]           Control line wrapping:    │
  │                                                    smart (default, Rich      │
  │                                                    formatting with padding), │
  │                                                    raw (natural terminal     │
  │                                                    wrapping, no              │
  │                                                    constraints), crop        │
  │                                                    (truncate at terminal     │
  │                                                    width).                   │
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

Test help for specific commands.

  $ jgo help run
                                                                                  
   Usage: jgo jgo [OPTIONS] [ENDPOINT] [REMAINING]...                             
                                                                                  
   Run a Java application from Maven coordinates or jgo.toml.                     
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --main-class     CLASS  Main class to run (supports auto-completion for      │
  │                         simple names)                                        │
  │ --entrypoint     NAME   Run specific entrypoint from jgo.toml                │
  │ --add-classpath  PATH   Append to classpath (JARs, directories, etc.)        │
  │ --help                  Show this message and exit.                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
   TIP: Use jgo --dry-run run to see the command without executing it.            
                                                                                  

  $ jgo help version
                                                                                  
   Usage: jgo jgo [OPTIONS]                                                       
                                                                                  
   Display jgo's version.                                                         
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help add
                                                                                  
   Usage: jgo jgo [OPTIONS] COORDINATES...                                        
                                                                                  
   Add dependencies to jgo.toml.                                                  
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --no-sync  Don't automatically sync after adding dependencies                │
  │ --help     Show this message and exit.                                       │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help remove
                                                                                  
   Usage: jgo jgo [OPTIONS] COORDINATES...                                        
                                                                                  
   Remove dependencies from jgo.toml.                                             
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --no-sync  Don't automatically sync after removing dependencies              │
  │ --help     Show this message and exit.                                       │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help init
                                                                                  
   Usage: jgo jgo [OPTIONS] [ENDPOINT]                                            
                                                                                  
   Create a new jgo.toml environment file.                                        
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help list
                                                                                  
   Usage: jgo jgo [OPTIONS] [ENDPOINT]                                            
                                                                                  
   List resolved dependencies (flat list).                                        
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --direct  Show only direct dependencies (non-transitive)                     │
  │ --help    Show this message and exit.                                        │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help tree
                                                                                  
   Usage: jgo jgo [OPTIONS] [ENDPOINT]                                            
                                                                                  
   Show dependency tree.                                                          
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help sync
                                                                                  
   Usage: jgo jgo [OPTIONS]                                                       
                                                                                  
   Resolve dependencies and build environment.                                    
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --force  Force rebuild even if cached                                        │
  │ --help   Show this message and exit.                                         │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help lock
                                                                                  
   Usage: jgo jgo [OPTIONS]                                                       
                                                                                  
   Update jgo.lock.toml without building environment.                             
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --check  Check if lock file is up to date                                    │
  │ --help   Show this message and exit.                                         │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help update
                                                                                  
   Usage: jgo jgo [OPTIONS]                                                       
                                                                                  
   Update dependencies to latest versions.                                        
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --force  Force rebuild even if cached                                        │
  │ --help   Show this message and exit.                                         │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help search
                                                                                  
   Usage: jgo jgo [OPTIONS] QUERY...                                              
                                                                                  
   Search for artifacts in Maven repositories.                                    
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --limit       N     Limit number of results (default: 20)                    │
  │ --repository  NAME  Search specific repository (default: central)            │
  │ --help              Show this message and exit.                              │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help config
                                                                                  
   Usage: jgo jgo [OPTIONS] COMMAND [ARGS]...                                     
                                                                                  
   Manage jgo configuration.                                                      
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ╭─ Commands ───────────────────────────────────────────────────────────────────╮
  │ get              Get a configuration value.                                  │
  │ list             List all configuration values.                              │
  │ set              Set a configuration value.                                  │
  │ shortcut         Manage global endpoint shortcuts.                           │
  │ unset            Remove a configuration value.                               │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help info
                                                                                  
   Usage: jgo jgo [OPTIONS] COMMAND [ARGS]...                                     
                                                                                  
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
                                                                                  

Test nested help for config subcommands.

  $ jgo help config shortcut
                                                                                  
   Usage: jgo config jgo [OPTIONS] [NAME] [ENDPOINT]                              
                                                                                  
   Manage global endpoint shortcuts.                                              
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --remove  -r  NAME  Remove a shortcut                                        │
  │ --list    -l        List all shortcuts                                       │
  │ --help              Show this message and exit.                              │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help config get
                                                                                  
   Usage: jgo config jgo [OPTIONS] KEY                                            
                                                                                  
   Get a configuration value.                                                     
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --global  Use global configuration (~/.config/jgo.conf)                      │
  │ --local   Use local configuration (jgo.toml)                                 │
  │ --help    Show this message and exit.                                        │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help config set
                                                                                  
   Usage: jgo config jgo [OPTIONS] KEY VALUE                                      
                                                                                  
   Set a configuration value.                                                     
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --global  Use global configuration (~/.config/jgo.conf)                      │
  │ --local   Use local configuration (jgo.toml)                                 │
  │ --help    Show this message and exit.                                        │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help config list
                                                                                  
   Usage: jgo config jgo [OPTIONS]                                                
                                                                                  
   List all configuration values.                                                 
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --global  Use global configuration (~/.config/jgo.conf).                     │
  │ --local   Use local configuration (jgo.toml).                                │
  │ --help    Show this message and exit.                                        │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Test nested help for info subcommands.

  $ jgo help info classpath
                                                                                  
   Usage: jgo info jgo [OPTIONS] [ENDPOINT]                                       
                                                                                  
   Show classpath.                                                                
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help info deptree
                                                                                  
   Usage: jgo info jgo [OPTIONS] [ENDPOINT]                                       
                                                                                  
   Show dependency tree.                                                          
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help info javainfo
                                                                                  
   Usage: jgo info jgo [OPTIONS] [ENDPOINT]                                       
                                                                                  
   Show Java version requirements.                                                
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯

  $ jgo help info versions
                                                                                  
   Usage: jgo info jgo [OPTIONS] COORDINATE                                       
                                                                                  
   List available versions of an artifact.                                        
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Test no-argument help (should show main help).

  $ jgo
                                                                                  
   Usage: jgo [OPTIONS] COMMAND [ARGS]...                                         
                                                                                  
   Environment manager and launcher for Java programs.                            
   Launch Java applications directly from Maven coordinates, build reproducible   
   environments, manage Java versions, and resolve dependencies -- without manual 
   installation.                                                                  
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --version                                          Show jgo version and      │
  │                                                    exit.                     │
  │ --ignore-config                                    Ignore ~/.config/jgo.conf │
  │                                                    file.                     │
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
  │ --wrap                  [smart|raw|crop]           Control line wrapping:    │
  │                                                    smart (default, Rich      │
  │                                                    formatting with padding), │
  │                                                    raw (natural terminal     │
  │                                                    wrapping, no              │
  │                                                    constraints), crop        │
  │                                                    (truncate at terminal     │
  │                                                    width).                   │
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

Test --help flag on main command.

  $ jgo --help
                                                                                  
   Usage: jgo [OPTIONS] COMMAND [ARGS]...                                         
                                                                                  
   Environment manager and launcher for Java programs.                            
   Launch Java applications directly from Maven coordinates, build reproducible   
   environments, manage Java versions, and resolve dependencies -- without manual 
   installation.                                                                  
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --version                                          Show jgo version and      │
  │                                                    exit.                     │
  │ --ignore-config                                    Ignore ~/.config/jgo.conf │
  │                                                    file.                     │
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
  │ --wrap                  [smart|raw|crop]           Control line wrapping:    │
  │                                                    smart (default, Rich      │
  │                                                    formatting with padding), │
  │                                                    raw (natural terminal     │
  │                                                    wrapping, no              │
  │                                                    constraints), crop        │
  │                                                    (truncate at terminal     │
  │                                                    width).                   │
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

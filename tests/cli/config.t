Tests jgo config command.

Test config with no subcommand shows help.

  $ jgo config
                                                                                  
   Usage: jgo config [OPTIONS] COMMAND [ARGS]...                                  
                                                                                  
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

Test config list subcommand.

  $ XDG_CONFIG_HOME="$TESTDIR" jgo -v config list
  Configuration from */jgo.conf: (glob)
  
  [settings]
    cache_dir = */.cache/jgo (glob)
    repo_cache = */.m2/repository (glob)
    links = soft
  
  [repositories]
    scijava.public = https://maven.scijava.org/content/groups/public
  
  [shortcuts]
    jd-cli = com.github.kwart.jd:jd-cli
    jython = org.python:jython-standalone
  

Test config get requires key argument.

  $ jgo -v config get
                                                                                  
   Usage: jgo config get [OPTIONS] KEY                                            
                                                                                  
   Try 'jgo config get --help' for help                                           
  ╭─ Error ──────────────────────────────────────────────────────────────────────╮
  │ Missing argument 'KEY'.                                                      │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
  [2]

Test config set requires both key and value arguments.

  $ jgo -v config set
                                                                                  
   Usage: jgo config set [OPTIONS] KEY VALUE                                      
                                                                                  
   Try 'jgo config set --help' for help                                           
  ╭─ Error ──────────────────────────────────────────────────────────────────────╮
  │ Missing argument 'KEY'.                                                      │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
  [2]

  $ jgo -v config set somekey
                                                                                  
   Usage: jgo config set [OPTIONS] KEY VALUE                                      
                                                                                  
   Try 'jgo config set --help' for help                                           
  ╭─ Error ──────────────────────────────────────────────────────────────────────╮
  │ Missing argument 'VALUE'.                                                    │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
  [2]

Test config unset requires key argument.

  $ jgo -v config unset
                                                                                  
   Usage: jgo config unset [OPTIONS] KEY                                          
                                                                                  
   Try 'jgo config unset --help' for help                                         
  ╭─ Error ──────────────────────────────────────────────────────────────────────╮
  │ Missing argument 'KEY'.                                                      │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
  [2]

Test config get and set commands.

  $ XDG_CONFIG_HOME="$TESTDIR" jgo -v config get links
  soft
  $ XDG_CONFIG_HOME="$TESTDIR" jgo -v config set links asdf
  $ XDG_CONFIG_HOME="$TESTDIR" jgo -v config get links
  asdf
  $ XDG_CONFIG_HOME="$TESTDIR" jgo -v config set links soft

Test config shortcut subcommand.

  $ jgo -v config shortcut --help
                                                                                  
   Usage: jgo config shortcut [OPTIONS] [NAME] [ENDPOINT]                         
                                                                                  
   Manage global endpoint shortcuts.                                              
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --remove  -r  NAME  Remove a shortcut                                        │
  │ --list    -l        List all shortcuts                                       │
  │ --help              Show this message and exit.                              │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Test config shortcut --list.

  $  XDG_CONFIG_HOME="$TESTDIR" jgo -v config shortcut --list
  Shortcuts from */jgo.conf: (glob)
  
    jd-cli  →  com.github.kwart.jd:jd-cli
    jython  →  org.python:jython-standalone
  
  Total: 2 shortcut(s)

  $ XDG_CONFIG_HOME="$TESTDIR" jgo config shortcut -r jython
  Removed shortcut: jython → org.python:jython-standalone

  $ XDG_CONFIG_HOME="$TESTDIR" jgo config shortcut --list
  Shortcuts from */jgo.conf: (glob)
  
    jd-cli  →  com.github.kwart.jd:jd-cli
  
  Total: 1 shortcut(s)

  $ XDG_CONFIG_HOME="$TESTDIR" jgo config shortcut jython org.python:jython-standalone
  Added shortcut: jython → org.python:jython-standalone

  $ XDG_CONFIG_HOME="$TESTDIR" jgo config shortcut --list
  Shortcuts from */jgo.conf: (glob)
  
    jd-cli  →  com.github.kwart.jd:jd-cli
    jython  →  org.python:jython-standalone
  
  Total: 2 shortcut(s)

  $ cat "$TESTDIR/jgo.conf"
  [shortcuts]
  jd-cli = com.github.kwart.jd:jd-cli
  jython = org.python:jython-standalone
  
  [repositories]
  scijava.public = https://maven.scijava.org/content/groups/public
  
  [settings]
  links = soft
  

Tests jgo remove command.

Test remove requires coordinates argument.

  $ jgo remove
                                                                                  
   Usage: jgo remove [OPTIONS] COORDINATES...                                     
                                                                                  
   Try 'jgo remove --help' for help                                               
  ╭─ Error ──────────────────────────────────────────────────────────────────────╮
  │ Missing argument 'COORDINATES...'.                                           │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
  [2]

Test remove --help shows usage.

  $ jgo remove --help
                                                                                  
   Usage: jgo remove [OPTIONS] COORDINATES...                                     
                                                                                  
   Remove dependencies from jgo.toml.                                             
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --no-sync  Don't automatically sync after removing dependencies              │
  │ --help     Show this message and exit.                                       │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Test remove requires jgo.toml to exist.

  $ cd "$TMPDIR" && mkdir -p jgo-test-remove && cd jgo-test-remove
  $ jgo -v remove org.python:jython-standalone
  ERROR    jgo.toml does not exist                                                
  INFO     Run 'jgo init' to create a new environment file first.                 
  [1]

Test remove with existing jgo.toml.

  $ jgo init com.google.guava:guava:33.0.0-jre
  $ jgo add org.python:jython-standalone:2.7.4
  $ jgo -v remove org.python:jython-standalone
  INFO     Removed 1 dependencies from jgo.toml                                   

Test remove multiple coordinates.

  $ jgo add net.imagej:ij:1.54g org.scijava:parsington:3.1.0
  $ jgo -v remove net.imagej:ij org.scijava:parsington
  INFO     Removed 2 dependencies from jgo.toml                                   

Test remove with --dry-run.

  $ jgo add org.scijava:scijava-common:2.97.1
  $ jgo --dry-run remove org.scijava:scijava-common
  [DRY-RUN] Would remove 1 dependencies from jgo.toml

  $ cd "$TMPDIR" && rm -rf jgo-test-remove

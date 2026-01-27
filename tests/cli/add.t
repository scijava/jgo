Tests jgo add command.

Test add requires coordinates argument.

  $ jgo add
                                                                                  
   Usage: jgo add [OPTIONS] COORDINATES...                                        
                                                                                  
   Try 'jgo add --help' for help                                                  
  ╭─ Error ──────────────────────────────────────────────────────────────────────╮
  │ Missing argument 'COORDINATES...'.                                           │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
  [2]

Test add --help shows usage.

  $ jgo add --help
                                                                                  
   Usage: jgo add [OPTIONS] COORDINATES...                                        
                                                                                  
   Add dependencies to jgo.toml.                                                  
                                                                                  
  ╭─ Arguments ──────────────────────────────────────────────────────────────────╮
  │ *  COORDINATES  TEXT  One or more Maven coordinates in format                │
  │                       groupId:artifactId:[version:[classifier] [required]    │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --no-sync  Don't automatically sync after adding dependencies                │
  │ --help     Show this message and exit.                                       │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Test add requires jgo.toml to exist.

  $ cd "$TMPDIR" && mkdir -p jgo-test-add && cd jgo-test-add
  $ jgo -v add org.python:jython-standalone:2.7.4
  ERROR    jgo.toml does not exist                                                
  INFO     Run 'jgo init' to create a new environment file first.                 
  [1]

Test add with existing jgo.toml.

  $ jgo init com.google.guava:guava:33.0.0-jre
  $ jgo -v add org.python:jython-standalone:2.7.4
  INFO     Added 1 dependencies to jgo.toml                                       

Test add multiple coordinates.

  $ jgo -v add net.imagej:ij:1.54f org.scijava:parsington:3.1.0
  INFO     Added 2 dependencies to jgo.toml                                       

Test add with --dry-run.

  $ jgo --dry-run add org.scijava:scijava-common:2.97.1
  [DRY-RUN] Would add 1 dependencies to jgo.toml

  $ cd "$TMPDIR" && rm -rf jgo-test-add

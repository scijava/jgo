Tests jgo run command.

Test run with no arguments.

  $ jgo run
  ERROR    No endpoint specified                                                  
  ERROR    Use 'jgo --help' for usage information                                 
  [1]

Test run --help output.

  $ jgo run --help
                                                                                  
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
                                                                                  

Test auto-completed main class.

  $ jgo run org.python:jython-standalone:2.7.4 -- --version
  Jython 2.7.4

Test inferred main class from JAR manifest.

  $ jgo run org.python:jython-standalone:2.7.4 -- --version
  Jython 2.7.4

Test shorthand syntax (no 'run' command).

  $ jgo org.python:jython-standalone:2.7.4 -- --version
  Jython 2.7.4

Test --main-class flag.

  $ jgo run --main-class org.python.util.jython org.python:jython-standalone:2.7.4 -- --version
  Jython 2.7.4

Test --dry-run shows java command without executing.

  $ jgo --dry-run run org.python:jython-standalone:2.7.4 -- --version
  */bin/java -XX:+UseG1GC -Xmx*G -cp */jars/*:*/modules/* org.python.util.jython --version (glob)

Test multiple endpoints with +.

  $ jgo --dry-run run org.python:jython-standalone:2.7.4+com.google.guava:guava:33.0.0-jre -- --version
  */bin/java -XX:+UseG1GC -Xmx*G -cp */jars/*:*/modules/* org.python.util.jython --version (glob)

Test --offline flag (should use cache).

  $ jgo --offline run org.python:jython-standalone:2.7.4 -- --version
  Jython 2.7.4

Test --update flag forces cache refresh.

  $ jgo --update --dry-run run org.python:jython-standalone:2.7.4 -- --version
  */bin/java -XX:+UseG1GC -Xmx*G -cp */jars/*:*/modules/* org.python.util.jython --version (glob)

Test --verbose flag.

  $ jgo -v run org.python:jython-standalone:2.7.4 -- --version
  INFO     Building environment for org.python:jython-standalone:2.7.4...
  INFO     Running Java application...
  Obtaining Java * automatically... (glob)
  Using Java * (*) at */bin/java (glob)
  */bin/java -XX:+UseG1GC -Xmx*G -cp */jars/*:*/modules/* org.python.util.jython --version (glob)
  Jython 2.7.4

Test --quiet flag suppresses output.

  $ jgo -q run org.python:jython-standalone:2.7.4 -- --version
  Jython 2.7.4

Test passing JVM args and app args.

  $ jgo --dry-run run org.python:jython-standalone:2.7.4 -Xmx2G -- --help
  */bin/java -XX:+UseG1GC -Xmx*G -Xmx2G -cp */jars/*:*/modules/\* org.python.util.jython --help (glob)

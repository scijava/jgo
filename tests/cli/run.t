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

  $ jgo run org.scijava:scijava-ops-image:1.0.0@About
  SciJava Ops Image v1.0.0
  Project license: Simplified BSD License
  Project website: https://github.com/scijava/scijava

Test inferred main class from JAR manifest.

  $ jgo run org.scijava:scijava-ops-image:1.0.0
  SciJava Ops Image v1.0.0
  Project license: Simplified BSD License
  Project website: https://github.com/scijava/scijava

Test shorthand syntax (no 'run' command).

  $ jgo org.scijava:scijava-ops-image:1.0.0
  SciJava Ops Image v1.0.0
  Project license: Simplified BSD License
  Project website: https://github.com/scijava/scijava

Test --main-class flag.

  $ jgo run --main-class About org.scijava:scijava-ops-image:1.0.0
  SciJava Ops Image v1.0.0
  Project license: Simplified BSD License
  Project website: https://github.com/scijava/scijava

Test --dry-run shows java command without executing.

  $ jgo --dry-run run org.scijava:scijava-ops-image:1.0.0@About
  */bin/java -XX:+UseG1GC -Xmx*G --module-path */modules --add-modules ALL-MODULE-PATH -cp */jars/\* --module org.scijava.ops.image/org.scijava.ops.image.About (glob)

Test multiple endpoints with +.

  $ jgo --dry-run run org.scijava:scijava-ops-image:1.0.0+net.imagej:ij:1.54g@About
  */bin/java -XX:+UseG1GC -Xmx*G --module-path */modules --add-modules ALL-MODULE-PATH --module org.scijava.ops.image/org.scijava.ops.image.About (glob)

Test --offline flag (should use cache).

  $ jgo --offline run org.scijava:scijava-ops-image:1.0.0@About
  SciJava Ops Image v1.0.0
  Project license: Simplified BSD License
  Project website: https://github.com/scijava/scijava

Test --update flag forces cache refresh.

  $ jgo --update --dry-run run org.scijava:scijava-ops-image:1.0.0@About
  */bin/java -XX:+UseG1GC -Xmx*G --module-path */modules --add-modules ALL-MODULE-PATH -cp */jars/\* --module org.scijava.ops.image/org.scijava.ops.image.About (glob)

Test --verbose flag.

  $ jgo -v run org.scijava:scijava-ops-image:1.0.0@About
  INFO     Building environment for org.scijava:scijava-ops-image:1.0.0@About...  
  INFO     Running Java application...                                            
  Obtaining Java 11 automatically...
  Using Java 11 (zulu) at */bin/java (glob)
  */bin/java -XX:+UseG1GC -Xmx*G --module-path */modules --add-modules ALL-MODULE-PATH -cp */jars/\* --module org.scijava.ops.image/org.scijava.ops.image.About (glob)
  SciJava Ops Image v1.0.0
  Project license: Simplified BSD License
  Project website: https://github.com/scijava/scijava

Test --quiet flag suppresses output.

  $ jgo -q run org.scijava:scijava-ops-image:1.0.0@About
  SciJava Ops Image v1.0.0
  Project license: Simplified BSD License
  Project website: https://github.com/scijava/scijava

Test passing JVM args and app args.

  $ jgo --dry-run run org.python:jython-standalone:2.7.4 -Xmx2G -- --help
  */bin/java -XX:+UseG1GC -Xmx*G -Xmx2G -cp */jars/*:*/modules/\* org.python.util.jython --help (glob)

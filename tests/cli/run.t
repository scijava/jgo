Tests jgo run command.

  $ jgo run
  ERROR    No endpoint specified* (glob)
  ERROR    Use 'jgo --help' for usage information* (glob)
  [1]

  $ jgo run --help
  * (glob)
   Usage: jgo run [OPTIONS] [ENDPOINT] [REMAINING]...* (glob)
  * (glob)
   Run a Java application from Maven coordinates or jgo.toml.* (glob)
  * (glob)
  ╭─ Options ──────────────────────────────────────────────────────────────*─╮ (glob)
  │ --main-class     CLASS  Main class to run (supports auto-completion for* │ (glob)
  │                         simple names)                                  * │ (glob)
  │ --entrypoint     NAME   Run specific entrypoint from jgo.toml          * │ (glob)
  │ --add-classpath  PATH   Append to classpath (JARs, directories, etc.)  * │ (glob)
  │ --help                  Show this message and exit.                    * │ (glob)
  ╰────────────────────────────────────────────────────────────────────────*─╯ (glob)
  * (glob)
   TIP: Use jgo --dry-run run to see the command without executing it.* (glob)
  * (glob)

Test auto-completed main class.

  $ jgo org.scijava:scijava-ops-image:1.0.0@About
  SciJava Ops Image v1.0.0
  Project license: Simplified BSD License
  Project website: https://github.com/scijava/scijava

Test inferred main class.

  $ jgo org.scijava:scijava-ops-image:1.0.0
  SciJava Ops Image v1.0.0
  Project license: Simplified BSD License
  Project website: https://github.com/scijava/scijava

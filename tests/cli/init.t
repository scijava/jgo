Tests jgo init command.

Test init --help shows usage.

  $ jgo init --help
                                                                                  
   Usage: jgo init [OPTIONS] [ENDPOINT]                                           
                                                                                  
   Create a new jgo.toml environment file.                                        
                                                                                  
  ╭─ Arguments ──────────────────────────────────────────────────────────────────╮
  │ ENDPOINT  TEXT  Maven coordinates (single or combined with +) optionally     │
  │                 followed by @MainClass                                       │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯




Test bare init (no endpoint) creates an empty environment.

  $ jgo --dry-run init
  [DRY-RUN] Would create jgo.toml:
  
  name = "init.t"
  
  
  coordinates = []
  
  
  cache_dir = ".jgo"
  







Test init with --dry-run.

  $ jgo --dry-run init org.python:jython-standalone:2.7.4
  [DRY-RUN] Would create jgo.toml:
  
  name = "init.t"
  description = "Generated from org.python:jython-standalone:2.7.4"
  
  
  coordinates = [
      "org.python:jython-standalone:2.7.4",
  ]
  
  
  main = "org.python:jython-standalone:2.7.4"
  default = "main"
  
  
  cache_dir = ".jgo"
  









Test init checks for existing jgo.toml.

  $ cd "$TMPDIR" && mkdir -p jgo-test-init && cd jgo-test-init
  $ jgo init com.google.guava:guava:33.0.0-jre
  $ test -f jgo.toml

  $ jgo init org.python:jython-standalone:2.7.4

  $ cd "$TMPDIR" && rm -rf jgo-test-init

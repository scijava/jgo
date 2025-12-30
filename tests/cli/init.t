Tests jgo init command.

Test init requires an endpoint argument.

  $ jgo init
  ERROR    init requires an endpoint                                              
  [1]

Test init --help shows usage.

  $ jgo init --help
                                                                                  
   Usage: jgo init [OPTIONS] [ENDPOINT]                                           
                                                                                  
   Create a new jgo.toml environment file.                                        
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Test init with --dry-run.

  $ jgo --dry-run init org.python:jython-standalone
  [DRY-RUN] Would create jgo.toml:
  
  name = "init.t"
  description = "Generated from org.python:jython-standalone"
  
  
  coordinates = [
      "org.python:jython-standalone",
  ]
  
  
  main = "org.python:jython-standalone"
  default = "main"
  
  
  cache_dir = ".jgo"
  

Test init checks for existing jgo.toml.

  $ cd "$TMPDIR" && mkdir -p jgo-test-init && cd jgo-test-init
  $ jgo init org.scijava:scijava-ops-image:1.0.0
  $ test -f jgo.toml

  $ jgo init org.python:jython-standalone

  $ cd "$TMPDIR" && rm -rf jgo-test-init

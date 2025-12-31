Tests jgo lock command.

Test lock requires jgo.toml to exist.

  $ jgo lock
  ERROR    jgo.toml does not exist                                                
  [1]

Test lock --help shows usage.

  $ jgo lock --help
                                                                                  
   Usage: jgo lock [OPTIONS]                                                      
                                                                                  
   Update jgo.lock.toml without building environment.                             
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --check  Check if lock file is up to date                                    │
  │ --help   Show this message and exit.                                         │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Test lock with existing jgo.toml.

  $ cd "$TMPDIR" && mkdir -p jgo-test-lock && cd jgo-test-lock
  $ jgo init com.google.guava:guava:33.0.0-jre
  $ jgo lock
  $ test -f jgo.lock.toml

Test lock with --dry-run.

  $ jgo --dry-run lock

Test lock with --update flag.

  $ jgo --update lock

  $ cd "$TMPDIR" && rm -rf jgo-test-lock

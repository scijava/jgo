Tests jgo sync command.

Test sync requires jgo.toml to exist.

  $ jgo sync
  ERROR    jgo.toml does not exist                                                
  [1]

Test sync --help shows usage.

  $ jgo sync --help
                                                                                  
   Usage: jgo sync [OPTIONS]                                                      
                                                                                  
   Resolve dependencies and build environment.                                    
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --force  Force rebuild even if cached                                        │
  │ --help   Show this message and exit.                                         │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Test sync with existing jgo.toml.

  $ cd "$TMPDIR" && mkdir -p jgo-test-sync && cd jgo-test-sync
  $ jgo init org.scijava:scijava-ops-image:1.0.0
  $ jgo sync

Test sync with --dry-run.

  $ jgo --dry-run sync
  [DRY-RUN] Would sync environment from jgo.toml

Test sync with --update flag.

  $ jgo --update sync

Test sync with --offline (uses cache).

  $ jgo --offline sync

  $ cd "$TMPDIR" && rm -rf jgo-test-sync

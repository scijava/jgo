Tests jgo update command.

Test update requires jgo.toml to exist.

  $ jgo update
  ERROR    jgo.toml does not exist                                                
  [1]

Test update --help shows usage.

  $ jgo update --help
                                                                                  
   Usage: jgo update [OPTIONS]                                                    
                                                                                  
   Update dependencies to latest versions.                                        
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --force  Force rebuild even if cached                                        │
  │ --help   Show this message and exit.                                         │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Test update with existing jgo.toml.

  $ cd "$TMPDIR" && mkdir -p jgo-test-update && cd jgo-test-update
  $ jgo init org.scijava:scijava-ops-image:1.0.0
  $ jgo update

Test update with --dry-run.

  $ jgo --dry-run update
  [DRY-RUN] Would sync environment from jgo.toml

Test update with --offline (should fail or warn).

  $ jgo --offline update

  $ cd "$TMPDIR" && rm -rf jgo-test-update

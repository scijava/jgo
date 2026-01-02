Tests jgo search command.

Test search requires query argument.

  $ jgo search
                                                                                  
   Usage: jgo search [OPTIONS] QUERY...                                           
                                                                                  
   Try 'jgo search --help' for help                                               
  ╭─ Error ──────────────────────────────────────────────────────────────────────╮
  │ Missing argument 'QUERY...'.                                                 │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
  [2]

Test search --help shows usage.

  $ jgo search --help
                                                                                  
   Usage: jgo search [OPTIONS] QUERY...                                           
                                                                                  
   Search for artifacts in Maven repositories.                                    
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --limit       N     Limit number of results (default: 20)                    │
  │ --repository  NAME  Search specific repository (default: central)            │
  │ --help              Show this message and exit.                              │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Test search with query.

  $ jgo search scijava-ops
  Found 9 artifacts:
  
  1. org.scijava:scijava-ops-indexer
     Latest version: [0-9.]+ (re)
  
  2. org.scijava:scijava-ops-api
     Latest version: [0-9.]+ (re)
  
  3. org.scijava:scijava-ops-engine
     Latest version: [0-9.]+ (re)
  
  4. org.scijava:scijava-ops-spi
     Latest version: [0-9.]+ (re)
  
  5. org.scijava:scijava-ops-flim
     Latest version: [0-9.]+ (re)
  
  6. org.scijava:scijava-ops-opencv
     Latest version: [0-9.]+ (re)
  
  7. org.scijava:scijava-ops-image
     Latest version: [0-9.]+ (re)
  
  8. org.scijava:scijava-ops-tutorial
     Latest version: [0-9.]+ (re)
  
  9. org.scijava:scijava-ops-ext-parser
     Latest version: [0-9.]+ (re)
  


Test search with --dry-run.

  $ jgo --dry-run search jython
  \[DRY-RUN\] Would search Maven Central for 'jython' with limit 20 (re)

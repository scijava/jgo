Tests jgo list command.

Test list requires endpoint or jgo.toml.

  $ jgo list
  ERROR    No endpoint specified                                                  
  [1]

Test list --help shows usage.

  $ jgo list --help
                                                                                  
   Usage: jgo list [OPTIONS] [ENDPOINT]                                           
                                                                                  
   List resolved dependencies (flat list).                                        
                                                                                  
  ╭─ Arguments ──────────────────────────────────────────────────────────────────╮
  │ ENDPOINT  TEXT  Maven coordinates (single or combined with +) optionally     │
  │                 followed by @MainClass                                       │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --direct  Show only direct dependencies (non-transitive)                     │
  │ --help    Show this message and exit.                                        │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Test list with endpoint.

  $ jgo list com.google.guava:guava:33.0.0-jre
  com.google.guava:guava:33.0.0-jre
     com.google.code.findbugs:jsr305:3.0.2
     com.google.errorprone:error_prone_annotations:2.23.0
     com.google.guava:failureaccess:1.0.2
     com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava
     com.google.j2objc:j2objc-annotations:2.8
     org.checkerframework:checker-qual:3.41.0

Test list with --dry-run.

  $ jgo --dry-run list com.google.guava:guava:33.0.0-jre
  com.google.guava:guava:33.0.0-jre
     com.google.code.findbugs:jsr305:3.0.2
     com.google.errorprone:error_prone_annotations:2.23.0
     com.google.guava:failureaccess:1.0.2
     com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava
     com.google.j2objc:j2objc-annotations:2.8
     org.checkerframework:checker-qual:3.41.0

Test list with --offline (uses cache).

  $ jgo --offline list com.google.guava:guava:33.0.0-jre
  com.google.guava:guava:33.0.0-jre
     com.google.code.findbugs:jsr305:3.0.2
     com.google.errorprone:error_prone_annotations:2.23.0
     com.google.guava:failureaccess:1.0.2
     com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava
     com.google.j2objc:j2objc-annotations:2.8
     org.checkerframework:checker-qual:3.41.0

Test list with MANAGED secondary coordinate.

  $ jgo list org.scijava:scijava-common:2.99.2+org.scijava:minimaven:MANAGED
  org.scijava:scijava-common:2.99.2
  org.scijava:minimaven:2.2.2
     org.scijava:parsington:3.1.0

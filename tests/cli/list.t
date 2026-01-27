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
     com.google.code.findbugs:jsr305:jar:3.0.2:compile
     com.google.errorprone:error_prone_annotations:jar:2.23.0:compile
     com.google.guava:failureaccess:jar:1.0.2:compile
     com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
     com.google.j2objc:j2objc-annotations:jar:2.8:compile
     org.checkerframework:checker-qual:jar:3.41.0:compile

Test list with --dry-run.

  $ jgo --dry-run list com.google.guava:guava:33.0.0-jre
  com.google.guava:guava:33.0.0-jre
     com.google.code.findbugs:jsr305:jar:3.0.2:compile
     com.google.errorprone:error_prone_annotations:jar:2.23.0:compile
     com.google.guava:failureaccess:jar:1.0.2:compile
     com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
     com.google.j2objc:j2objc-annotations:jar:2.8:compile
     org.checkerframework:checker-qual:jar:3.41.0:compile

Test list with --offline (uses cache).

  $ jgo --offline list com.google.guava:guava:33.0.0-jre
  com.google.guava:guava:33.0.0-jre
     com.google.code.findbugs:jsr305:jar:3.0.2:compile
     com.google.errorprone:error_prone_annotations:jar:2.23.0:compile
     com.google.guava:failureaccess:jar:1.0.2:compile
     com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
     com.google.j2objc:j2objc-annotations:jar:2.8:compile
     org.checkerframework:checker-qual:jar:3.41.0:compile

Test list with MANAGED secondary coordinate.

  $ jgo list org.scijava:scijava-common:2.99.2+org.scijava:minimaven:MANAGED
  org.scijava:scijava-common:2.99.2
  org.scijava:minimaven:2.2.2
     org.scijava:parsington:jar:3.1.0:compile

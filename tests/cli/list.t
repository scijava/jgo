Tests jgo list command.

Test list requires endpoint or jgo.toml.

  $ jgo list
  ERROR    No endpoint specified                                                  
  [1]

Test list --help shows usage.

  $ jgo list --help
                                                                                  
   Usage: jgo list [OPTIONS] [ENDPOINT]                                           
                                                                                  
   List resolved dependencies (flat list).                                        
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --direct  Show only direct dependencies (non-transitive)                     │
  │ --help    Show this message and exit.                                        │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Test list with endpoint.

  $ jgo list com.google.guava:guava:33.0.0-jre
  com.google.guava:guava:33.0.0-jre
     com.google.code.findbugs:jsr305:jar:*:compile (glob)
     com.google.errorprone:error_prone_annotations:jar:*:compile (glob)
     com.google.guava:failureaccess:jar:*:compile (glob)
     com.google.guava:listenablefuture:jar:*:compile (glob)
     com.google.j2objc:j2objc-annotations:jar:*:compile (glob)
     org.checkerframework:checker-qual:jar:*:compile (glob)

Test list with --dry-run.

  $ jgo --dry-run list com.google.guava:guava:33.0.0-jre
  com.google.guava:guava:33.0.0-jre
     com.google.code.findbugs:jsr305:jar:*:compile (glob)
     com.google.errorprone:error_prone_annotations:jar:*:compile (glob)
     com.google.guava:failureaccess:jar:*:compile (glob)
     com.google.guava:listenablefuture:jar:*:compile (glob)
     com.google.j2objc:j2objc-annotations:jar:*:compile (glob)
     org.checkerframework:checker-qual:jar:*:compile (glob)

Test list with --offline (uses cache).

  $ jgo --offline list com.google.guava:guava:33.0.0-jre
  com.google.guava:guava:33.0.0-jre
     com.google.code.findbugs:jsr305:jar:*:compile (glob)
     com.google.errorprone:error_prone_annotations:jar:*:compile (glob)
     com.google.guava:failureaccess:jar:*:compile (glob)
     com.google.guava:listenablefuture:jar:*:compile (glob)
     com.google.j2objc:j2objc-annotations:jar:*:compile (glob)
     org.checkerframework:checker-qual:jar:*:compile (glob)

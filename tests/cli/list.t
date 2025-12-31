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

  $ jgo list org.scijava:scijava-ops-image:1.0.0
  org.scijava:scijava-ops-image:1.0.0
     com.github.ben-manes.caffeine:caffeine:jar:2.9.3:compile
     com.google.code.findbugs:jsr305:jar:3.0.2:compile
     com.google.errorprone:error_prone_annotations:jar:2.19.0:compile
     com.google.guava:failureaccess:jar:1.0.1:compile
     com.google.guava:guava:jar:31.1-jre:compile
     com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
     com.google.j2objc:j2objc-annotations:jar:2.8:compile
     com.googlecode.efficient-java-matrix-library:ejml:jar:0.25:compile
     edu.mines:mines-jtk:jar:20151125:compile
     gov.nist.math:jama:jar:1.0.3:compile
     jitk:jitk-tps:jar:3.0.3:compile
     net.imglib2:imglib2:jar:6.2.0:compile
     net.imglib2:imglib2-algorithm:jar:0.14.0:compile
     net.imglib2:imglib2-algorithm-fft:jar:0.2.1:compile
     net.imglib2:imglib2-cache:jar:1.0.0-beta-17:compile
     net.imglib2:imglib2-mesh:jar:1.0.0:compile
     net.imglib2:imglib2-realtransform:jar:4.0.1:compile
     net.imglib2:imglib2-roi:jar:0.14.1:compile
     net.sf.trove4j:trove4j:jar:3.0.3:compile
     org.apache.commons:commons-lang3:jar:3.12.0:compile
     org.apache.commons:commons-math3:jar:3.6.1:compile
     org.checkerframework:checker-qual:jar:3.34.0:compile
     org.joml:joml:jar:1.10.5:compile
     org.ojalgo:ojalgo:jar:45.1.1:compile
     org.scijava:scijava-collections:jar:1.0.0:compile
     org.scijava:scijava-common3:jar:1.0.0:compile
     org.scijava:scijava-concurrent:jar:1.0.0:compile
     org.scijava:scijava-discovery:jar:1.0.0:compile
     org.scijava:scijava-function:jar:1.0.0:compile
     org.scijava:scijava-meta:jar:1.0.0:compile
     org.scijava:scijava-ops-api:jar:1.0.0:compile
     org.scijava:scijava-ops-spi:jar:1.0.0:compile
     org.scijava:scijava-optional:jar:1.0.1:compile
     org.scijava:scijava-priority:jar:1.0.0:compile
     org.scijava:scijava-progress:jar:1.0.0:compile
     org.scijava:scijava-struct:jar:1.0.0:compile
     org.scijava:scijava-types:jar:1.0.0:compile
     org.slf4j:slf4j-api:jar:1.7.36:compile
     org.smurn:jply:jar:0.2.1:compile

Test list with --dry-run.

  $ jgo --dry-run list org.scijava:scijava-ops-image:1.0.0
  org.scijava:scijava-ops-image:1.0.0
     com.github.ben-manes.caffeine:caffeine:jar:2.9.3:compile
     com.google.code.findbugs:jsr305:jar:3.0.2:compile
     com.google.errorprone:error_prone_annotations:jar:2.19.0:compile
     com.google.guava:failureaccess:jar:1.0.1:compile
     com.google.guava:guava:jar:31.1-jre:compile
     com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
     com.google.j2objc:j2objc-annotations:jar:2.8:compile
     com.googlecode.efficient-java-matrix-library:ejml:jar:0.25:compile
     edu.mines:mines-jtk:jar:20151125:compile
     gov.nist.math:jama:jar:1.0.3:compile
     jitk:jitk-tps:jar:3.0.3:compile
     net.imglib2:imglib2:jar:6.2.0:compile
     net.imglib2:imglib2-algorithm:jar:0.14.0:compile
     net.imglib2:imglib2-algorithm-fft:jar:0.2.1:compile
     net.imglib2:imglib2-cache:jar:1.0.0-beta-17:compile
     net.imglib2:imglib2-mesh:jar:1.0.0:compile
     net.imglib2:imglib2-realtransform:jar:4.0.1:compile
     net.imglib2:imglib2-roi:jar:0.14.1:compile
     net.sf.trove4j:trove4j:jar:3.0.3:compile
     org.apache.commons:commons-lang3:jar:3.12.0:compile
     org.apache.commons:commons-math3:jar:3.6.1:compile
     org.checkerframework:checker-qual:jar:3.34.0:compile
     org.joml:joml:jar:1.10.5:compile
     org.ojalgo:ojalgo:jar:45.1.1:compile
     org.scijava:scijava-collections:jar:1.0.0:compile
     org.scijava:scijava-common3:jar:1.0.0:compile
     org.scijava:scijava-concurrent:jar:1.0.0:compile
     org.scijava:scijava-discovery:jar:1.0.0:compile
     org.scijava:scijava-function:jar:1.0.0:compile
     org.scijava:scijava-meta:jar:1.0.0:compile
     org.scijava:scijava-ops-api:jar:1.0.0:compile
     org.scijava:scijava-ops-spi:jar:1.0.0:compile
     org.scijava:scijava-optional:jar:1.0.1:compile
     org.scijava:scijava-priority:jar:1.0.0:compile
     org.scijava:scijava-progress:jar:1.0.0:compile
     org.scijava:scijava-struct:jar:1.0.0:compile
     org.scijava:scijava-types:jar:1.0.0:compile
     org.slf4j:slf4j-api:jar:1.7.36:compile
     org.smurn:jply:jar:0.2.1:compile

Test list with --offline (uses cache).

  $ jgo --offline list org.scijava:scijava-ops-image:1.0.0
  org.scijava:scijava-ops-image:1.0.0
     com.github.ben-manes.caffeine:caffeine:jar:2.9.3:compile
     com.google.code.findbugs:jsr305:jar:3.0.2:compile
     com.google.errorprone:error_prone_annotations:jar:2.19.0:compile
     com.google.guava:failureaccess:jar:1.0.1:compile
     com.google.guava:guava:jar:31.1-jre:compile
     com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
     com.google.j2objc:j2objc-annotations:jar:2.8:compile
     com.googlecode.efficient-java-matrix-library:ejml:jar:0.25:compile
     edu.mines:mines-jtk:jar:20151125:compile
     gov.nist.math:jama:jar:1.0.3:compile
     jitk:jitk-tps:jar:3.0.3:compile
     net.imglib2:imglib2:jar:6.2.0:compile
     net.imglib2:imglib2-algorithm:jar:0.14.0:compile
     net.imglib2:imglib2-algorithm-fft:jar:0.2.1:compile
     net.imglib2:imglib2-cache:jar:1.0.0-beta-17:compile
     net.imglib2:imglib2-mesh:jar:1.0.0:compile
     net.imglib2:imglib2-realtransform:jar:4.0.1:compile
     net.imglib2:imglib2-roi:jar:0.14.1:compile
     net.sf.trove4j:trove4j:jar:3.0.3:compile
     org.apache.commons:commons-lang3:jar:3.12.0:compile
     org.apache.commons:commons-math3:jar:3.6.1:compile
     org.checkerframework:checker-qual:jar:3.34.0:compile
     org.joml:joml:jar:1.10.5:compile
     org.ojalgo:ojalgo:jar:45.1.1:compile
     org.scijava:scijava-collections:jar:1.0.0:compile
     org.scijava:scijava-common3:jar:1.0.0:compile
     org.scijava:scijava-concurrent:jar:1.0.0:compile
     org.scijava:scijava-discovery:jar:1.0.0:compile
     org.scijava:scijava-function:jar:1.0.0:compile
     org.scijava:scijava-meta:jar:1.0.0:compile
     org.scijava:scijava-ops-api:jar:1.0.0:compile
     org.scijava:scijava-ops-spi:jar:1.0.0:compile
     org.scijava:scijava-optional:jar:1.0.1:compile
     org.scijava:scijava-priority:jar:1.0.0:compile
     org.scijava:scijava-progress:jar:1.0.0:compile
     org.scijava:scijava-struct:jar:1.0.0:compile
     org.scijava:scijava-types:jar:1.0.0:compile
     org.slf4j:slf4j-api:jar:1.7.36:compile
     org.smurn:jply:jar:0.2.1:compile

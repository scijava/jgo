Tests jgo with custom Maven repositories.

Test run with custom repository using -r flag.

  $ cd "$TMPDIR" && mkdir -p jgo-test-repositories && cd jgo-test-repositories
  $ jgo -r maven.scijava.org:https://maven.scijava.org/content/groups/public run org.scijava:scijava-ops-image:1.0.0@About
  SciJava Ops Image v1.0.0
  Project license: Simplified BSD License
  Project website: https://github.com/scijava/scijava

Test tree with custom repository.

  $ jgo -r maven.scijava.org:https://maven.scijava.org/content/groups/public tree org.scijava:scijava-ops-image:1.0.0

  └── org.scijava:scijava-ops-image:1.0.0
      ├── org.scijava:scijava-collections:*
      ├── org.scijava:scijava-common3:*
      ├── org.scijava:scijava-concurrent:*
      ├── org.scijava:scijava-function:*
      ├── org.scijava:scijava-meta:*
      ├── org.scijava:scijava-ops-api:*
      │   ├── org.scijava:scijava-discovery:*
      │   └── org.scijava:scijava-struct:*
      ├── org.scijava:scijava-priority:*
      ├── org.scijava:scijava-progress:*
      ├── org.scijava:scijava-ops-spi:*
      ├── org.scijava:scijava-types:*
      │   ├── com.google.guava:guava:*
      │   │   ├── com.google.guava:failureaccess:*
      │   │   ├── com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict (glob)
      │   │   │   * (glob)
      │   │   ├── com.google.code.findbugs:jsr305:*
      │   │   ├── org.checkerframework:checker-qual:*
      │   │   ├── com.google.errorprone:error_prone_annotations:*
      │   │   └── com.google.j2objc:j2objc-annotations:*
      │   └── org.slf4j:slf4j-api:*
      ├── net.imglib2:imglib2:*
      ├── net.imglib2:imglib2-algorithm:*
      │   ├── net.sf.trove4j:trove4j:*
      │   └── net.imglib2:imglib2-cache:*
      │       ├── com.github.ben-manes.caffeine:caffeine:*
      │       └── org.scijava:scijava-optional:*
      ├── net.imglib2:imglib2-algorithm-fft:*
      │   └── edu.mines:mines-jtk:*
      ├── net.imglib2:imglib2-mesh:*
      │   └── org.smurn:jply:*
      │       └── org.apache.commons:commons-lang3:*
      ├── net.imglib2:imglib2-realtransform:*
      │   └── jitk:jitk-tps:*
      │       └── com.googlecode.efficient-java-matrix-library:ejml:*
      ├── net.imglib2:imglib2-roi:*
      ├── org.apache.commons:commons-math3:*
      ├── org.joml:joml:*
      ├── org.ojalgo:ojalgo:*
      └── gov.nist.math:jama:*

  $ cd "$TMPDIR" && rm -rf jgo-test-repositories

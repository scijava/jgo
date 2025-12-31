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
      ├── org.scijava:scijava-collections:1.0.0
      ├── org.scijava:scijava-common3:1.0.0
      ├── org.scijava:scijava-concurrent:1.0.0
      ├── org.scijava:scijava-function:1.0.0
      ├── org.scijava:scijava-meta:1.0.0
      ├── org.scijava:scijava-ops-api:1.0.0
      │   ├── org.scijava:scijava-discovery:1.0.0
      │   └── org.scijava:scijava-struct:1.0.0
      ├── org.scijava:scijava-priority:1.0.0
      ├── org.scijava:scijava-progress:1.0.0
      ├── org.scijava:scijava-ops-spi:1.0.0
      ├── org.scijava:scijava-types:1.0.0
      │   ├── com.google.guava:guava:31.1-jre
      │   │   ├── com.google.guava:failureaccess:1.0.1
      │   │   ├── com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict
      │   │   │   -with-guava
      │   │   ├── com.google.code.findbugs:jsr305:3.0.2
      │   │   ├── org.checkerframework:checker-qual:3.34.0
      │   │   ├── com.google.errorprone:error_prone_annotations:2.19.0
      │   │   └── com.google.j2objc:j2objc-annotations:2.8
      │   └── org.slf4j:slf4j-api:1.7.36
      ├── net.imglib2:imglib2:6.2.0
      ├── net.imglib2:imglib2-algorithm:0.14.0
      │   ├── net.sf.trove4j:trove4j:3.0.3
      │   └── net.imglib2:imglib2-cache:1.0.0-beta-17
      │       ├── com.github.ben-manes.caffeine:caffeine:2.9.3
      │       └── org.scijava:scijava-optional:1.0.1
      ├── net.imglib2:imglib2-algorithm-fft:0.2.1
      │   └── edu.mines:mines-jtk:20151125
      ├── net.imglib2:imglib2-mesh:1.0.0
      │   └── org.smurn:jply:0.2.1
      │       └── org.apache.commons:commons-lang3:3.12.0
      ├── net.imglib2:imglib2-realtransform:4.0.1
      │   └── jitk:jitk-tps:3.0.3
      │       └── com.googlecode.efficient-java-matrix-library:ejml:0.25
      ├── net.imglib2:imglib2-roi:0.14.1
      ├── org.apache.commons:commons-math3:3.6.1
      ├── org.joml:joml:1.10.5
      ├── org.ojalgo:ojalgo:45.1.1
      └── gov.nist.math:jama:1.0.3


  $ cd "$TMPDIR" && rm -rf jgo-test-repositories

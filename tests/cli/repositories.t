Tests jgo with custom Maven repositories.

Set up.

  $ cd "$TMPDIR" && mkdir -p jgo-test-repositories && cd jgo-test-repositories

Test run with custom repository using -r flag.
Note that scijava-ops-image is on Maven Central, but some deps are not.

  $ jgo --ignore-config -r maven.scijava.org:https://maven.scijava.org/content/groups/public run org.scijava:scijava-ops-image:1.0.0
  SciJava Ops Image v1.0.0
  Project license: Simplified BSD License
  Project website: https://github.com/scijava/scijava
 
Test tree with custom repository.

  $ jgo -r maven.scijava.org:https://maven.scijava.org/content/groups/public --ignore-config tree ome:formats-api:8.3.0
  
  └── ome:formats-api:8.3.0
      ├── org.openmicroscopy:ome-common:6.1.0
      │   ├── io.minio:minio:5.0.2
      │   │   ├── com.google.http-client:google-http-client-xml:1.20.0
      │   │   │   ├── com.google.http-client:google-http-client:1.20.0
      │   │   │   │   └── org.apache.httpcomponents:httpclient:4.0.1
      │   │   │   │       └── org.apache.httpcomponents:httpcore:4.0.1
      │   │   │   └── xpp3:xpp3:1.1.4c
      │   │   ├── com.squareup.okhttp3:okhttp:3.7.0
      │   │   └── com.squareup.okio:okio:1.12.0
      │   ├── com.fasterxml.jackson.core:jackson-databind:2.14.2
      │   │   └── com.fasterxml.jackson.core:jackson-core:2.14.2
      │   ├── com.fasterxml.jackson.core:jackson-annotations:2.14.2
      │   ├── com.esotericsoftware:kryo:5.4.0
      │   │   ├── com.esotericsoftware:reflectasm:1.11.9
      │   │   ├── org.objenesis:objenesis:3.3
      │   │   └── com.esotericsoftware:minlog:1.3.1
      │   ├── joda-time:joda-time:2.12.7
      │   └── com.google.guava:guava:32.0.1-jre
      │       ├── com.google.guava:failureaccess:1.0.1
      │       ├── com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-guava
      │       ├── com.google.code.findbugs:jsr305:3.0.2
      │       ├── org.checkerframework:checker-qual:3.33.0
      │       ├── com.google.errorprone:error_prone_annotations:2.18.0
      │       └── com.google.j2objc:j2objc-annotations:2.8
      ├── org.openmicroscopy:ome-xml:6.5.0
      │   └── org.openmicroscopy:specification:6.5.0
      ├── org.openmicroscopy:ome-codecs:1.1.1
      │   ├── org.openmicroscopy:ome-jai:0.1.5
      │   └── io.airlift:aircompressor:0.27
      ├── org.slf4j:slf4j-api:2.0.9
      ├── xalan:serializer:2.7.3:runtime
      └── xalan:xalan:2.7.3:runtime

  $ jgo --ignore-config -r maven.scijava.org:https://maven.scijava.org/content/groups/public tree net.imagej:imagej-common:2.1.1
  
  └── net.imagej:imagej-common:2.1.1
      ├── net.imglib2:imglib2:7.1.0
      ├── net.imglib2:imglib2-roi:0.15.0
      │   ├── net.imglib2:imglib2-realtransform:4.0.2
      │   │   ├── gov.nist.math:jama:1.0.3
      │   │   ├── jitk:jitk-tps:3.0.4
      │   │   │   └── org.ejml:ejml-all:0.41
      │   │   │       ├── org.ejml:ejml-core:0.41
      │   │   │       ├── org.ejml:ejml-fdense:0.41
      │   │   │       ├── org.ejml:ejml-ddense:0.41
      │   │   │       ├── org.ejml:ejml-cdense:0.41
      │   │   │       ├── org.ejml:ejml-zdense:0.41
      │   │   │       ├── org.ejml:ejml-dsparse:0.41
      │   │   │       └── org.ejml:ejml-simple:0.41
      │   │   │           └── org.ejml:ejml-fsparse:0.41
      │   │   └── org.slf4j:slf4j-api:1.7.36
      │   └── net.sf.trove4j:trove4j:3.0.3
      ├── org.scijava:scijava-common:2.98.0
      │   └── org.scijava:parsington:3.1.0
      ├── org.scijava:scijava-table:1.0.2
      │   └── org.scijava:scijava-optional:1.0.1
      └── edu.ucar:udunits:4.3.18

Clean up.

  $ cd "$TMPDIR" && rm -rf jgo-test-repositories

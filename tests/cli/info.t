Tests jgo info command.

Test info with no subcommand shows help.

  $ jgo info
                                                                                  
   Usage: jgo info [OPTIONS] COMMAND [ARGS]...                                    
                                                                                  
   Show information about environment or artifact.                                
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ╭─ Commands ───────────────────────────────────────────────────────────────────╮
  │ classpath        Show classpath.                                             │
  │ deplist          Show flat list of dependencies.                             │
  │ deptree          Show dependency tree.                                       │
  │ entrypoints      Show entrypoints from jgo.toml.                             │
  │ envdir           Show environment directory path.                            │
  │ jars             Show all JAR paths (classpath + module-path).               │
  │ javainfo         Show Java version requirements.                             │
  │ mains            Show classes with public main methods.                      │
  │ manifest         Show JAR manifest.                                          │
  │ modulepath       Show module-path.                                           │
  │ pom              Show POM content.                                           │
  │ versions         List available versions of an artifact.                     │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
   TIP: To see the launch command, use: jgo --dry-run run <endpoint>              
                                                                                  
  [2]

Test info classpath with no endpoint.

  $ jgo info classpath
  ERROR    No endpoint specified                                                  
  [1]

Test info classpath with endpoint.

  $ jgo info classpath com.google.guava:guava:33.0.0-jre
  No JARs on classpath
  TIP: Use 'jgo info module-path' to see module-path JARs

Test info modulepath with endpoint.

  $ jgo info modulepath com.google.guava:guava:33.0.0-jre
  */modules/checker-qual-3.41.0.jar (glob)
  */modules/error_prone_annotations-2.23.0.jar (glob)
  */modules/failureaccess-1.0.2.jar (glob)
  */modules/guava-33.0.0-jre.jar (glob)
  */modules/j2objc-annotations-2.8.jar (glob)
  */modules/jsr305-3.0.2.jar (glob)
  */modules/listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar (glob)

Test info jars with endpoint.

  $ jgo info jars com.google.guava:guava:33.0.0-jre
  No classpath JARs
  Module-path:
  */modules/checker-qual-3.41.0.jar (glob)
  */modules/error_prone_annotations-2.23.0.jar (glob)
  */modules/failureaccess-1.0.2.jar (glob)
  */modules/guava-33.0.0-jre.jar (glob)
  */modules/j2objc-annotations-2.8.jar (glob)
  */modules/jsr305-3.0.2.jar (glob)
  */modules/listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar (glob)

Test info deptree with no endpoint.

  $ jgo info deptree
  ERROR    No endpoint specified                                                  
  [1]

Test info deptree with endpoint.

  $ jgo info deptree com.google.guava:guava:33.0.0-jre
  
  └── com.google.guava:guava:33.0.0-jre
      ├── com.google.guava:failureaccess:1.0.2
      ├── com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict-with-gu
      │   ava
      ├── com.google.code.findbugs:jsr305:3.0.2
      ├── org.checkerframework:checker-qual:3.41.0
      ├── com.google.errorprone:error_prone_annotations:2.23.0
      └── com.google.j2objc:j2objc-annotations:2.8


Test info deplist with no endpoint.

  $ jgo info deplist
  ERROR    No endpoint specified                                                  
  [1]

Test info deplist with endpoint.

  $ jgo info deplist com.google.guava:guava:33.0.0-jre
  com.google.guava:guava:33.0.0-jre
     com.google.code.findbugs:jsr305:jar:3.0.2:compile
     com.google.errorprone:error_prone_annotations:jar:2.23.0:compile
     com.google.guava:failureaccess:jar:1.0.2:compile
     com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-gua
  va:compile
     com.google.j2objc:j2objc-annotations:jar:2.8:compile
     org.checkerframework:checker-qual:jar:3.41.0:compile

Test info deplist --direct flag.

  $ jgo info deplist --direct com.google.guava:guava:33.0.0-jre
  com.google.guava:guava:33.0.0-jre
     com.google.code.findbugs:jsr305:jar:3.0.2:compile
     com.google.errorprone:error_prone_annotations:jar:2.23.0:compile
     com.google.guava:failureaccess:jar:1.0.2:compile
     com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-gua
  va:compile
     com.google.j2objc:j2objc-annotations:jar:2.8:compile
     org.checkerframework:checker-qual:jar:3.41.0:compile

Test info javainfo with no endpoint.

  $ jgo info javainfo
  ERROR    No endpoint specified                                                  
  [1]

Test info javainfo with endpoint.

  $ jgo info javainfo com.google.guava:guava:33.0.0-jre
  
  Environment: 
  */.cache/jgo/envs/com/google/guava/guava/* (glob)
  Module-path JARs: 7
  Total JARs: 7
  
  ╭───────────────────────── Java Version Requirements ──────────────────────────╮
  │ Minimum Java version: 8                                                      │
  │ (already an LTS version)                                                     │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                  Per-JAR Analysis                                
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
  ┃ JAR                              ┃ Java Version ┃ Max Bytecode ┃ Class Count ┃
  ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
  │ checker-qual-3.41.0.jar          │            8 │           52 │         366 │
  │ error_prone_annotations-2.23.0.… │            8 │           52 │          27 │
  │ guava-33.0.0-jre.jar             │            8 │           52 │        2003 │
  │ failureaccess-1.0.2.jar          │            7 │           51 │           2 │
  │ j2objc-annotations-2.8.jar       │            7 │           51 │          13 │
  │ jsr305-3.0.2.jar                 │            5 │           49 │          35 │
  └──────────────────────────────────┴──────────────┴──────────────┴─────────────┘
  
  Bytecode Version Details:

Test info manifest requires endpoint.

  $ jgo info manifest
                                                                                  
   Usage: jgo info manifest [OPTIONS] ENDPOINT                                    
                                                                                  
   Try 'jgo info manifest --help' for help                                        
  ╭─ Error ──────────────────────────────────────────────────────────────────────╮
  │ Missing argument 'ENDPOINT'.                                                 │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
  [2]

Test info manifest with endpoint.

  $ jgo info manifest com.google.guava:guava:33.0.0-jre
  Manifest-Version: 1.0
  Automatic-Module-Name: com.google.common
  Build-Jdk-Spec: 11
  Bundle-Description: Guava is a suite of core and expanded libraries that include    utility classes, Google's collections, I/O classes, and    much more.
  Bundle-DocURL: https://github.com/google/guava/
  Bundle-License: http://www.apache.org/licenses/LICENSE-2.0.txt
  Bundle-ManifestVersion: 2
  Bundle-Name: Guava: Google Core Libraries for Java
  Bundle-SymbolicName: com.google.guava
  Bundle-Version: 33.0.0.jre
  Created-By: Apache Maven Bundle Plugin 5.1.8
  Export-Package: com.google.common.annotations;version="33.0.0",com.google.common.base;version="33.0.0";uses:="javax.annotation",com.google.common.cache;version="33.0.0";uses:="com.google.common.base,com.google.common.collect,com.google.common.util.concurrent,javax.annotation",com.google.common.collect;version="33.0.0";uses:="com.google.common.base,javax.annotation",com.google.common.escape;version="33.0.0";uses:="com.google.common.base,javax.annotation",com.google.common.eventbus;version="33.0.0",com.google.common.graph;version="33.0.0";uses:="com.google.common.collect,javax.annotation",com.google.common.hash;version="33.0.0";uses:="com.google.common.base,javax.annotation",com.google.common.html;version="33.0.0";uses:="com.google.common.escape",com.google.common.io;version="33.0.0";uses:="com.google.common.base,com.google.common.collect,com.google.common.graph,com.google.common.hash,javax.annotation",com.google.common.math;version="33.0.0";uses:="javax.annotation",com.google.common.net;version="33.0.0";uses:="com.google.common.base,com.google.common.collect,com.google.common.escape,javax.annotation",com.google.common.primitives;version="33.0.0";uses:="com.google.common.base,javax.annotation",com.google.common.reflect;version="33.0.0";uses:="com.google.common.collect,com.google.common.io,javax.annotation",com.google.common.util.concurrent;version="33.0.0";uses:="com.google.common.base,com.google.common.collect,com.google.common.util.concurrent.internal,javax.annotation",com.google.common.xml;version="33.0.0";uses:="com.google.common.escape"
  Import-Package: com.google.common.util.concurrent.internal;version="[1.0,2)",javax.annotation;resolution:=optional;version="[3.0,4)",javax.crypto;resolution:=optional,javax.crypto.spec;resolution:=optional,sun.misc;resolution:=optional
  Require-Capability: osgi.ee;filter:="(&(osgi.ee=JavaSE)(version=1.8))"
  Tool: Bnd-6.3.1.202206071316

Test info manifest --raw flag.

  $ jgo info manifest --raw com.google.guava:guava:33.0.0-jre
  Manifest-Version: 1.0\r (esc)
  Automatic-Module-Name: com.google.common\r (esc)
  Build-Jdk-Spec: 11\r (esc)
  Bundle-Description: Guava is a suite of core and expanded libraries th\r (esc)
   at include    utility classes, Google's collections, I/O classes, and\r (esc)
       much more.\r (esc)
  Bundle-DocURL: https://github.com/google/guava/\r (esc)
  Bundle-License: http://www.apache.org/licenses/LICENSE-2.0.txt\r (esc)
  Bundle-ManifestVersion: 2\r (esc)
  Bundle-Name: Guava: Google Core Libraries for Java\r (esc)
  Bundle-SymbolicName: com.google.guava\r (esc)
  Bundle-Version: 33.0.0.jre\r (esc)
  Created-By: Apache Maven Bundle Plugin 5.1.8\r (esc)
  Export-Package: com.google.common.annotations;version="33.0.0",com.goo\r (esc)
   gle.common.base;version="33.0.0";uses:="javax.annotation",com.google.\r (esc)
   common.cache;version="33.0.0";uses:="com.google.common.base,com.googl\r (esc)
   e.common.collect,com.google.common.util.concurrent,javax.annotation",\r (esc)
   com.google.common.collect;version="33.0.0";uses:="com.google.common.b\r (esc)
   ase,javax.annotation",com.google.common.escape;version="33.0.0";uses:\r (esc)
   ="com.google.common.base,javax.annotation",com.google.common.eventbus\r (esc)
   ;version="33.0.0",com.google.common.graph;version="33.0.0";uses:="com\r (esc)
   .google.common.collect,javax.annotation",com.google.common.hash;versi\r (esc)
   on="33.0.0";uses:="com.google.common.base,javax.annotation",com.googl\r (esc)
   e.common.html;version="33.0.0";uses:="com.google.common.escape",com.g\r (esc)
   oogle.common.io;version="33.0.0";uses:="com.google.common.base,com.go\r (esc)
   ogle.common.collect,com.google.common.graph,com.google.common.hash,ja\r (esc)
   vax.annotation",com.google.common.math;version="33.0.0";uses:="javax.\r (esc)
   annotation",com.google.common.net;version="33.0.0";uses:="com.google.\r (esc)
   common.base,com.google.common.collect,com.google.common.escape,javax.\r (esc)
   annotation",com.google.common.primitives;version="33.0.0";uses:="com.\r (esc)
   google.common.base,javax.annotation",com.google.common.reflect;versio\r (esc)
   n="33.0.0";uses:="com.google.common.collect,com.google.common.io,java\r (esc)
   x.annotation",com.google.common.util.concurrent;version="33.0.0";uses\r (esc)
   :="com.google.common.base,com.google.common.collect,com.google.common\r (esc)
   .util.concurrent.internal,javax.annotation",com.google.common.xml;ver\r (esc)
   sion="33.0.0";uses:="com.google.common.escape"\r (esc)
  Import-Package: com.google.common.util.concurrent.internal;version="[1\r (esc)
   .0,2)",javax.annotation;resolution:=optional;version="[3.0,4)",javax.\r (esc)
   crypto;resolution:=optional,javax.crypto.spec;resolution:=optional,su\r (esc)
   n.misc;resolution:=optional\r (esc)
  Require-Capability: osgi.ee;filter:="(&(osgi.ee=JavaSE)(version=1.8))"\r (esc)
  Tool: Bnd-6.3.1.202206071316\r (esc)
  \r (esc)

Test info pom requires endpoint.

  $ jgo info pom
                                                                                  
   Usage: jgo info pom [OPTIONS] ENDPOINT                                         
                                                                                  
   Try 'jgo info pom --help' for help                                             
  ╭─ Error ──────────────────────────────────────────────────────────────────────╮
  │ Missing argument 'ENDPOINT'.                                                 │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
  [2]

Test info pom with endpoint.

  $ jgo --wrap=raw info pom com.google.guava:guava:33.0.0-jre
  \x1b[38;5;245m<?xml version="1.0" ?>\x1b[39m (esc)
  \x1b[38;5;204m<project\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;148mxmlns=\x1b[39m\x1b[38;5;186m"http://maven.apache.org/POM/4.0.0"\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;148mxmlns:xsi=\x1b[39m\x1b[38;5;186m"http://www.w3.org/2001/XMLSchema-instance"\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;148mxsi:schemaLocation=\x1b[39m\x1b[38;5;186m"http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd"\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;245m<!-- do_not_remove: published-with-gradle-metadata -->\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m<modelVersion\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m4.0.0\x1b[39m\x1b[38;5;204m</modelVersion>\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m<parent\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m<groupId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mcom.google.guava\x1b[39m\x1b[38;5;204m</groupId>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mguava-parent\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m<version\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m33.0.0-jre\x1b[39m\x1b[38;5;204m</version>\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m</parent>\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mguava\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m<packaging\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mbundle\x1b[39m\x1b[38;5;204m</packaging>\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m<name\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mGuava:\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mGoogle\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mCore\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mLibraries\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mfor\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mJava\x1b[39m\x1b[38;5;204m</name>\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m<url\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mhttps://github.com/google/guava\x1b[39m\x1b[38;5;204m</url>\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m<description\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;15mGuava\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mis\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15ma\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15msuite\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mof\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mcore\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mand\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mexpanded\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mlibraries\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mthat\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15minclude\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;15mutility\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mclasses,\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mGoogle's\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mcollections,\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mI/O\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mclasses,\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mand\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;15mmuch\x1b[39m\x1b[38;5;15m \x1b[39m\x1b[38;5;15mmore.\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m</description>\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m<dependencies\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m<dependency\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<groupId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mcom.google.guava\x1b[39m\x1b[38;5;204m</groupId>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mfailureaccess\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<version\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m1.0.2\x1b[39m\x1b[38;5;204m</version>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m</dependency>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m<dependency\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<groupId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mcom.google.guava\x1b[39m\x1b[38;5;204m</groupId>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mlistenablefuture\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<version\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m9999.0-empty-to-avoid-conflict-with-guava\x1b[39m\x1b[38;5;204m</version>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m</dependency>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m<dependency\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<groupId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mcom.google.code.findbugs\x1b[39m\x1b[38;5;204m</groupId>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mjsr305\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m</dependency>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m<dependency\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<groupId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15morg.checkerframework\x1b[39m\x1b[38;5;204m</groupId>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mchecker-qual\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m</dependency>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m<dependency\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<groupId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mcom.google.errorprone\x1b[39m\x1b[38;5;204m</groupId>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15merror_prone_annotations\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m</dependency>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m<dependency\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<groupId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mcom.google.j2objc\x1b[39m\x1b[38;5;204m</groupId>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mj2objc-annotations\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m</dependency>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;245m<!-- TODO(cpovirk): does this comment belong on the <dependency> in <profiles>? -->\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;245m<!-- TODO(cpovirk): want this only for dependency plugin but seems not to work there? Maven runs without failure, but the resulting Javadoc is missing the hoped-for inherited text -->\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m</dependencies>\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m<build\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m<resources\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<resource\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<directory\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m..\x1b[39m\x1b[38;5;204m</directory>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<includes\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<include\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mLICENSE\x1b[39m\x1b[38;5;204m</include>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;245m<!-- copied from the parent pom because I couldn't figure out a way to make combine.children="append" work -->\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<include\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mproguard/*\x1b[39m\x1b[38;5;204m</include>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m</includes>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<targetPath\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mMETA-INF\x1b[39m\x1b[38;5;204m</targetPath>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</resource>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m</resources>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m<plugins\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<plugin\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mmaven-jar-plugin\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<configuration\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<archive\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<manifestEntries\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<Automatic-Module-Name\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mcom.google.common\x1b[39m\x1b[38;5;204m</Automatic-Module-Name>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</manifestEntries>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m</archive>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m</configuration>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</plugin>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<plugin\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<extensions\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mtrue\x1b[39m\x1b[38;5;204m</extensions>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<groupId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15morg.apache.felix\x1b[39m\x1b[38;5;204m</groupId>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mmaven-bundle-plugin\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<version\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m5.1.8\x1b[39m\x1b[38;5;204m</version>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<executions\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<execution\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<id\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mbundle-manifest\x1b[39m\x1b[38;5;204m</id>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<phase\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mprocess-classes\x1b[39m\x1b[38;5;204m</phase>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<goals\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<goal\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mmanifest\x1b[39m\x1b[38;5;204m</goal>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</goals>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m</execution>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m</executions>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<configuration\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<instructions\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<Export-Package\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;15m!com.google.common.base.internal,\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;15m!com.google.common.util.concurrent.internal,\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;15mcom.google.common.*\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</Export-Package>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<Import-Package\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;15mcom.google.common.util.concurrent.internal,\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;15mjavax.annotation;resolution:=optional,\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;15mjavax.crypto.*;resolution:=optional,\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;15msun.misc.*;resolution:=optional\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</Import-Package>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<Bundle-DocURL\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mhttps://github.com/google/guava/\x1b[39m\x1b[38;5;204m</Bundle-DocURL>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m</instructions>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m</configuration>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</plugin>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<plugin\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mmaven-compiler-plugin\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</plugin>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<plugin\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mmaven-source-plugin\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</plugin>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;245m<!-- TODO(cpovirk): include JDK sources when building testlib doc, too -->\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<plugin\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mmaven-dependency-plugin\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<executions\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<execution\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<id\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15munpack-jdk-sources\x1b[39m\x1b[38;5;204m</id>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<phase\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mgenerate-sources\x1b[39m\x1b[38;5;204m</phase>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<goals\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<goal\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15munpack-dependencies\x1b[39m\x1b[38;5;204m</goal>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</goals>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<configuration\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<includeArtifactIds\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15msrczip\x1b[39m\x1b[38;5;204m</includeArtifactIds>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<outputDirectory\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m${project.build.directory}/jdk-sources\x1b[39m\x1b[38;5;204m</outputDirectory>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<silent\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mfalse\x1b[39m\x1b[38;5;204m</silent>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;245m<!-- Exclude module-info files (since we're using -source 8 to avoid other modules problems) and FileDescriptor (which uses a language feature not available in Java 8). -->\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<excludes\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m**/module-info.java,**/java/io/FileDescriptor.java\x1b[39m\x1b[38;5;204m</excludes>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</configuration>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m</execution>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m</executions>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</plugin>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<plugin\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<groupId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15morg.codehaus.mojo\x1b[39m\x1b[38;5;204m</groupId>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15manimal-sniffer-maven-plugin\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</plugin>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<plugin\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mmaven-javadoc-plugin\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<configuration\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;245m<!-- TODO(cpovirk): Move this to the parent after making jdk-sources available there. -->\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;245m<!-- TODO(cpovirk): can we use includeDependencySources and a local com.oracle.java:jdk-lib:noversion:sources instead of all this unzipping and manual sourcepath modification? -->\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;245m<!-- (We need JDK *sources*, not just -link, so that {@inheritDoc} works.) -->\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<sourcepath\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m${project.build.sourceDirectory}:${project.build.directory}/jdk-sources\x1b[39m\x1b[38;5;204m</sourcepath>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;245m<!-- Passing `-subpackages com.google.common` breaks things, so we explicitly exclude everything else instead. -->\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;245m<!-- excludePackageNames requires specification of packages separately from "all subpackages".\x1b[39m (esc)
  \x1b[38;5;245m               https://issues.apache.org/jira/browse/MJAVADOC-584 -->\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<excludePackageNames\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;15mcom.azul.tooling.in,com.google.common.base.internal,com.google.common.base.internal.*,com.google.thirdparty.publicsuffix,com.google.thirdparty.publicsuffix.*,com.oracle.*,com.sun.*,java.*,javax.*,jdk,jdk.*,org.*,sun.*\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m</excludePackageNames>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;245m<!-- Ignore some tags that are found in Java 11 sources but not recognized... under -source 8, I think it was? I can no longer reproduce the failure. -->\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<tags\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<tag\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<name\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mapiNote\x1b[39m\x1b[38;5;204m</name>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<placement\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mX\x1b[39m\x1b[38;5;204m</placement>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</tag>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<tag\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<name\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mimplNote\x1b[39m\x1b[38;5;204m</name>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<placement\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mX\x1b[39m\x1b[38;5;204m</placement>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</tag>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<tag\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<name\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mimplSpec\x1b[39m\x1b[38;5;204m</name>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<placement\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mX\x1b[39m\x1b[38;5;204m</placement>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</tag>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<tag\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<name\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mjls\x1b[39m\x1b[38;5;204m</name>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<placement\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mX\x1b[39m\x1b[38;5;204m</placement>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</tag>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<tag\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<name\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mrevised\x1b[39m\x1b[38;5;204m</name>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<placement\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mX\x1b[39m\x1b[38;5;204m</placement>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</tag>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<tag\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<name\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mspec\x1b[39m\x1b[38;5;204m</name>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<placement\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mX\x1b[39m\x1b[38;5;204m</placement>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</tag>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m</tags>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;245m<!-- TODO(cpovirk): Move this to the parent after making the package-list files available there. -->\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;245m<!-- We add the link ourselves, both so that we can choose Java 9 over the version that -source suggests and so that we can solve the JSR305 problem described below. -->\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<detectJavaApiLink\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mfalse\x1b[39m\x1b[38;5;204m</detectJavaApiLink>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<offlineLinks\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;245m<!-- We need local copies of some of these for 2 reasons: a User-Agent problem (https://stackoverflow.com/a/47891403/28465) and an SSL problem (https://issues.apache.org/jira/browse/MJAVADOC-507). If we choose to work around the User-Agent problem, we can go back to <links>, sidestepping the SSL problem. -->\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;245m<!-- Even after we stop using JSR305 annotations in our own code, we'll want this link so that NullPointerTester's docs can link to @CheckForNull and friends... at least once we start using this config for guava-testlib. -->\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<offlineLink\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<url\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mhttps://static.javadoc.io/com.google.code.findbugs/jsr305/3.0.1/\x1b[39m\x1b[38;5;204m</url>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<location\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m${project.basedir}/javadoc-link/jsr305\x1b[39m\x1b[38;5;204m</location>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</offlineLink>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<offlineLink\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<url\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mhttps://static.javadoc.io/com.google.j2objc/j2objc-annotations/1.1/\x1b[39m\x1b[38;5;204m</url>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<location\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m${project.basedir}/javadoc-link/j2objc-annotations\x1b[39m\x1b[38;5;204m</location>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</offlineLink>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;245m<!-- The JDK doc must be listed after JSR305 (and as an <offlineLink>, not a <link>) so that JSR305 "claims" javax.annotation. -->\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<offlineLink\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<url\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mhttps://docs.oracle.com/javase/9/docs/api/\x1b[39m\x1b[38;5;204m</url>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<location\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mhttps://docs.oracle.com/javase/9/docs/api/\x1b[39m\x1b[38;5;204m</location>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</offlineLink>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;245m<!-- The Checker Framework likewise would claim javax.annotations, despite providing only a subset of the JSR305 annotations, so it must likewise come after JSR305. -->\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<offlineLink\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<url\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mhttps://checkerframework.org/api/\x1b[39m\x1b[38;5;204m</url>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<location\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m${project.basedir}/javadoc-link/checker-framework\x1b[39m\x1b[38;5;204m</location>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</offlineLink>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m</offlineLinks>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<links\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<link\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mhttps://errorprone.info/api/latest/\x1b[39m\x1b[38;5;204m</link>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m</links>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<overview\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m../overview.html\x1b[39m\x1b[38;5;204m</overview>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m</configuration>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</plugin>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<plugin\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mmaven-resources-plugin\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<executions\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<execution\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<id\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mgradle-module-metadata\x1b[39m\x1b[38;5;204m</id>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<phase\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mcompile\x1b[39m\x1b[38;5;204m</phase>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<goals\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<goal\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mcopy-resources\x1b[39m\x1b[38;5;204m</goal>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</goals>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<configuration\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<outputDirectory\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mtarget/publish\x1b[39m\x1b[38;5;204m</outputDirectory>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<resources\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m                \x1b[39m\x1b[38;5;204m<resource\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m                  \x1b[39m\x1b[38;5;204m<directory\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m.\x1b[39m\x1b[38;5;204m</directory>\x1b[39m (esc)
  \x1b[38;5;15m                  \x1b[39m\x1b[38;5;204m<includes\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m                    \x1b[39m\x1b[38;5;204m<include\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mmodule.json\x1b[39m\x1b[38;5;204m</include>\x1b[39m (esc)
  \x1b[38;5;15m                  \x1b[39m\x1b[38;5;204m</includes>\x1b[39m (esc)
  \x1b[38;5;15m                  \x1b[39m\x1b[38;5;204m<filtering\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mtrue\x1b[39m\x1b[38;5;204m</filtering>\x1b[39m (esc)
  \x1b[38;5;15m                \x1b[39m\x1b[38;5;204m</resource>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m</resources>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</configuration>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m</execution>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m</executions>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</plugin>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<plugin\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<groupId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15morg.codehaus.mojo\x1b[39m\x1b[38;5;204m</groupId>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mbuild-helper-maven-plugin\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<executions\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<execution\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<id\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mattach-gradle-module-metadata\x1b[39m\x1b[38;5;204m</id>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<goals\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<goal\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mattach-artifact\x1b[39m\x1b[38;5;204m</goal>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</goals>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<configuration\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<artifacts\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m                \x1b[39m\x1b[38;5;204m<artifact\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m                  \x1b[39m\x1b[38;5;204m<file\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mtarget/publish/module.json\x1b[39m\x1b[38;5;204m</file>\x1b[39m (esc)
  \x1b[38;5;15m                  \x1b[39m\x1b[38;5;204m<type\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mmodule\x1b[39m\x1b[38;5;204m</type>\x1b[39m (esc)
  \x1b[38;5;15m                \x1b[39m\x1b[38;5;204m</artifact>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m</artifacts>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</configuration>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m</execution>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m</executions>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</plugin>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m</plugins>\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m</build>\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m<profiles\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m<profile\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<id\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15msrczip-parent\x1b[39m\x1b[38;5;204m</id>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<activation\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<file\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<exists\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m${java.home}/../src.zip\x1b[39m\x1b[38;5;204m</exists>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m</file>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</activation>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<dependencies\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<dependency\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<groupId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mjdk\x1b[39m\x1b[38;5;204m</groupId>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15msrczip\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<version\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m999\x1b[39m\x1b[38;5;204m</version>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<scope\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15msystem\x1b[39m\x1b[38;5;204m</scope>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<systemPath\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m${java.home}/../src.zip\x1b[39m\x1b[38;5;204m</systemPath>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<optional\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mtrue\x1b[39m\x1b[38;5;204m</optional>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m</dependency>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</dependencies>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m</profile>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m<profile\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<id\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15msrczip-lib\x1b[39m\x1b[38;5;204m</id>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<activation\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<file\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<exists\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m${java.home}/lib/src.zip\x1b[39m\x1b[38;5;204m</exists>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m</file>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</activation>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<dependencies\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<dependency\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<groupId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mjdk\x1b[39m\x1b[38;5;204m</groupId>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15msrczip\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<version\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m999\x1b[39m\x1b[38;5;204m</version>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<scope\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15msystem\x1b[39m\x1b[38;5;204m</scope>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<systemPath\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m${java.home}/lib/src.zip\x1b[39m\x1b[38;5;204m</systemPath>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<optional\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mtrue\x1b[39m\x1b[38;5;204m</optional>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m</dependency>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</dependencies>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m<build\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m<plugins\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m<plugin\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<artifactId\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15mmaven-javadoc-plugin\x1b[39m\x1b[38;5;204m</artifactId>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m<configuration\x1b[39m\x1b[38;5;204m>\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;245m<!-- We need to point at the java.base subdirectory because Maven appears to assume that package foo.bar is located in foo/bar and not java.base/foo/bar when translating excludePackageNames into filenames to pass to javadoc. (Note that manually passing -exclude to javadoc appears to possibly not work at all for java.* types??) Also, referring only to java.base avoids a lot of other sources. -->\x1b[39m (esc)
  \x1b[38;5;15m              \x1b[39m\x1b[38;5;204m<sourcepath\x1b[39m\x1b[38;5;204m>\x1b[39m\x1b[38;5;15m${project.build.sourceDirectory}:${project.build.directory}/jdk-sources/java.base\x1b[39m\x1b[38;5;204m</sourcepath>\x1b[39m (esc)
  \x1b[38;5;15m            \x1b[39m\x1b[38;5;204m</configuration>\x1b[39m (esc)
  \x1b[38;5;15m          \x1b[39m\x1b[38;5;204m</plugin>\x1b[39m (esc)
  \x1b[38;5;15m        \x1b[39m\x1b[38;5;204m</plugins>\x1b[39m (esc)
  \x1b[38;5;15m      \x1b[39m\x1b[38;5;204m</build>\x1b[39m (esc)
  \x1b[38;5;15m    \x1b[39m\x1b[38;5;204m</profile>\x1b[39m (esc)
  \x1b[38;5;15m  \x1b[39m\x1b[38;5;204m</profiles>\x1b[39m (esc)
  \x1b[38;5;204m</project>\x1b[39m (esc)

Test info versions requires coordinates.

  $ jgo info versions
                                                                                  
   Usage: jgo info versions [OPTIONS] COORDINATE                                  
                                                                                  
   Try 'jgo info versions --help' for help                                        
  ╭─ Error ──────────────────────────────────────────────────────────────────────╮
  │ Missing argument 'COORDINATE'.                                               │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
  [2]

Test info versions with coordinates.

  $ jgo info versions com.google.guava:guava | head -n100
  Available versions for com.google.guava:guava:
    r03
    r05
    r06
    r07
    r08
    r09
    10.0-rc1
    10.0-rc2
    10.0-rc3
    10.0
    10.0.1
    11.0-rc1
    11.0
    11.0.1
    11.0.2
    12.0-rc1
    12.0-rc2
    12.0
    12.0.1
    13.0-rc1
    13.0-rc2
    13.0
    13.0.1
    14.0-rc1
    14.0-rc2
    14.0-rc3
    14.0
    14.0.1
    15.0-rc1
    15.0
    16.0-rc1
    16.0
    16.0.1
    17.0-rc1
    17.0-rc2
    17.0
    18.0-rc1
    18.0-rc2
    18.0
    19.0-rc1
    19.0-rc2
    19.0-rc3
    19.0
    20.0-rc1
    20.0
    21.0-rc1
    21.0-rc2
    21.0
    22.0-rc1
    22.0-rc1-android
    22.0
    22.0-android
    23.0-rc1
    23.0-rc1-android
    23.0
    23.0-android
    23.1-android
    23.1-jre
    23.2-android
    23.2-jre
    23.3-android
    23.3-jre
    23.4-android
    23.4-jre
    23.5-android
    23.5-jre
    23.6-android
    23.6-jre
    23.6.1-android
    23.6.1-jre
    24.0-android
    24.0-jre
    24.1-android
    24.1-jre
    24.1.1-android
    24.1.1-jre
    25.0-android
    25.0-jre
    25.1-android
    25.1-jre
    26.0-android
    26.0-jre
    27.0-android
    27.0-jre
    27.0.1-android
    27.0.1-jre
    27.1-android
    27.1-jre
    28.0-android
    28.0-jre
    28.1-android
    28.1-jre
    28.2-android
    28.2-jre
    29.0-android
    29.0-jre
    30.0-android
    30.0-jre
    30.1-android

Test info entrypoints without jgo.toml.

  $ jgo info entrypoints
  ERROR    jgo.toml not found                                                     
  [1]


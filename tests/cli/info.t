Tests jgo info command.

Test info with no subcommand shows help.

  $ jgo info
                                                                                  
   Usage: jgo info [OPTIONS] COMMAND [ARGS]...                                    
                                                                                  
   Show information about environment or artifact.                                
                                                                                  
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ╭─ Commands ───────────────────────────────────────────────────────────────────╮
  │ classpath          Show classpath.                                           │
  │ deplist            Show flat list of dependencies.                           │
  │ deptree            Show dependency tree.                                     │
  │ entrypoints        Show entrypoints from jgo.toml.                           │
  │ javainfo           Show Java version requirements.                           │
  │ manifest           Show JAR manifest.                                        │
  │ pom                Show POM content.                                         │
  │ versions           List available versions of an artifact.                   │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
   TIP: To see the launch command, use: jgo --dry-run run <endpoint>              
                                                                                  
  [2]

Test info classpath with no endpoint.

  $ jgo info classpath
  ERROR    No endpoint specified                                                  
  [1]

Test info classpath with endpoint.

  $ jgo info classpath com.google.guava:guava:33.0.0-jre
  */jars/j2objc-annotations-*.jar (glob)
  */jars/jsr305-*.jar (glob)
  */jars/listenablefuture-*.jar (glob)

Test info deptree with no endpoint.

  $ jgo info deptree
  ERROR    No endpoint specified                                                  
  [1]

Test info deptree with endpoint.

  $ jgo info deptree com.google.guava:guava:33.0.0-jre

  └── com.google.guava:guava:33.0.0-jre
      ├── com.google.guava:failureaccess:*
      ├── com.google.guava:listenablefuture:9999.0-empty-to-avoid-conflict (glob)
      │   *ava (glob)
      ├── com.google.code.findbugs:jsr305:*
      ├── org.checkerframework:checker-qual:*
      ├── com.google.errorprone:error_prone_annotations:*
      └── com.google.j2objc:j2objc-annotations:*

Test info deplist with no endpoint.

  $ jgo info deplist
  ERROR    No endpoint specified                                                  
  [1]

Test info deplist with endpoint.

  $ jgo info deplist com.google.guava:guava:33.0.0-jre
  com.google.guava:guava:33.0.0-jre
     com.google.code.findbugs:jsr305:jar:*:compile (glob)
     com.google.errorprone:error_prone_annotations:jar:*:compile (glob)
     com.google.guava:failureaccess:jar:*:compile (glob)
     com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
     com.google.j2objc:j2objc-annotations:jar:*:compile (glob)
     org.checkerframework:checker-qual:jar:*:compile (glob)

Test info deplist --direct flag.

  $ jgo info deplist --direct com.google.guava:guava:33.0.0-jre
  com.google.guava:guava:33.0.0-jre
     com.google.code.findbugs:jsr305:jar:*:compile (glob)
     com.google.errorprone:error_prone_annotations:jar:*:compile (glob)
     com.google.guava:failureaccess:jar:*:compile (glob)
     com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
     com.google.j2objc:j2objc-annotations:jar:*:compile (glob)
     org.checkerframework:checker-qual:jar:*:compile (glob)

Test info javainfo with no endpoint.

  $ jgo info javainfo
  ERROR    No endpoint specified                                                  
  [1]

Test info javainfo with endpoint.

  $ jgo info javainfo com.google.guava:guava:33.0.0-jre
  
  Environment: 
  */com/google/guava/guava/* (glob)
  JARs directory: 
  */com/google/guava/guava/*/jars (glob)
  Total JARs: 40
  
  ╭───────────────────────── Java Version Requirements ──────────────────────────╮
  │ Minimum Java version: 11                                                     │
  │ (already an LTS version)                                                     │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                  Per-JAR Analysis                                
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
  ┃ JAR                              ┃ Java Version ┃ Max Bytecode ┃ Class Count ┃
  ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
  │ scijava-collections-1.0.0.jar    │           11 │           55 │          11 │
  │ scijava-common3-1.0.0.jar        │           11 │           55 │          23 │
  │ scijava-concurrent-1.0.0.jar     │           11 │           55 │          10 │
  │ scijava-discovery-1.0.0.jar      │           11 │           55 │           6 │
  │ scijava-function-1.0.0.jar       │           11 │           55 │         360 │
  │ scijava-meta-1.0.0.jar           │           11 │           55 │           4 │
  │ scijava-ops-api-1.0.0.jar        │           11 │           55 │          97 │
  │ guava-33.0.0-jre.jar      │           11 │           55 │         918 │
  │ scijava-ops-spi-1.0.0.jar        │           11 │           55 │          11 │
  │ scijava-priority-1.0.0.jar       │           11 │           55 │           2 │
  │ scijava-progress-1.0.0.jar       │           11 │           55 │           4 │
  │ scijava-struct-1.0.0.jar         │           11 │           55 │          10 │
  │ scijava-types-1.0.0.jar          │           11 │           55 │          21 │
  │ caffeine-2.9.3.jar               │            8 │           52 │         692 │
  │ checker-qual-3.34.0.jar          │            8 │           52 │         359 │
  │ commons-lang3-3.12.0.jar         │            8 │           52 │         345 │
  │ error_prone_annotations-2.19.0.… │            8 │           52 │          27 │
  │ guava-31.1-jre.jar               │            8 │           52 │        2008 │
  │ imglib2-6.2.0.jar                │            8 │           52 │         758 │
  │ imglib2-algorithm-0.14.0.jar     │            8 │           52 │         756 │
  │ imglib2-algorithm-fft-0.2.1.jar  │            8 │           52 │           5 │
  │ imglib2-cache-1.0.0-beta-17.jar  │            8 │           52 │         161 │
  │ imglib2-mesh-1.0.0.jar           │            8 │           52 │          68 │
  │ imglib2-realtransform-4.0.1.jar  │            8 │           52 │          68 │
  │ imglib2-roi-0.14.1.jar           │            8 │           52 │         224 │
  │ jitk-tps-3.0.3.jar               │            8 │           52 │           4 │
  │ ojalgo-45.1.1.jar                │            8 │           52 │        1347 │
  │ scijava-optional-1.0.1.jar       │            8 │           52 │           5 │
  │ failureaccess-1.0.1.jar          │            7 │           51 │           2 │
  │ j2objc-annotations-2.8.jar       │            7 │           51 │          13 │
  │ mines-jtk-20151125.jar           │            7 │           51 │         900 │
  │ ejml-0.25.jar                    │            6 │           50 │         162 │
  │ jama-1.0.3.jar                   │            6 │           50 │           9 │
  │ jply-0.2.1.jar                   │            6 │           50 │          34 │
  │ commons-math3-3.6.1.jar          │            5 │           49 │        1301 │
  │ jsr305-3.0.2.jar                 │            5 │           49 │          35 │
  │ slf4j-api-1.7.36.jar             │            5 │           49 │          34 │
  │ trove4j-3.0.3.jar                │            5 │           49 │        1595 │
  │ joml-1.10.5.jar                  │            2 │           46 │         111 │
  └──────────────────────────────────┴──────────────┴──────────────┴─────────────┘
  
  Bytecode Version Details:
  
  ... and 29 more JARs (showing first 10)

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
  Created-By: Maven JAR Plugin 3.3.0
  Build-Jdk-Spec: 11
  Class-Path: scijava-collections-1.0.0.jar scijava-common3-1.0.0.jar scijava-concurrent-1.0.0.jar scijava-function-1.0.0.jar scijava-meta-1.0.0.jar scijava-ops-api-1.0.0.jar scijava-discovery-1.0.0.jar scijava-struct-1.0.0.jar scijava-priority-1.0.0.jar scijava-progress-1.0.0.jar scijava-ops-spi-1.0.0.jar scijava-types-1.0.0.jar guava-31.1-jre.jar failureaccess-1.0.1.jar listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar jsr305-3.0.2.jar checker-qual-3.34.0.jar error_prone_annotations-2.19.0.jar j2objc-annotations-2.8.jar slf4j-api-1.7.36.jar imglib2-6.2.0.jar imglib2-algorithm-0.14.0.jar trove4j-3.0.3.jar imglib2-cache-1.0.0-beta-17.jar caffeine-2.9.3.jar scijava-optional-1.0.1.jar imglib2-algorithm-fft-0.2.1.jar mines-jtk-20151125.jar imglib2-mesh-1.0.0.jar jply-0.2.1.jar commons-lang3-3.12.0.jar imglib2-realtransform-4.0.1.jar jitk-tps-3.0.3.jar ejml-0.25.jar imglib2-roi-0.14.1.jar commons-math3-3.6.1.jar joml-1.10.5.jar ojalgo-45.1.1.jar jama-1.0.3.jar
  Specification-Title: SciJava Ops Image
  Specification-Version: 1.0
  Specification-Vendor: SciJava
  Implementation-Title: SciJava Ops Image
  Implementation-Version: 1.0.0
  Implementation-Vendor: SciJava
  Main-Class: org.scijava.ops.image.About
  Package: org.scijava.ops.image
  Automatic-Module-Name: org.scijava.ops.image
  Implementation-Build: 202fcef4cb3eee7ffe0c105ab2d5bc36d34c9cd1
  Implementation-Date: 2024-06-04T01:54:54+0000
  Premain-Class: 

Test info manifest --raw flag.

  $ jgo info manifest --raw com.google.guava:guava:33.0.0-jre
  Manifest-Version: 1.0\r (esc)
  Created-By: Maven JAR Plugin 3.3.0\r (esc)
  Build-Jdk-Spec: 11\r (esc)
  Class-Path: scijava-collections-1.0.0.jar scijava-common3-1.0.0.jar scij\r (esc)
   ava-concurrent-1.0.0.jar scijava-function-1.0.0.jar scijava-meta-1.0.0.\r (esc)
   jar scijava-ops-api-1.0.0.jar scijava-discovery-1.0.0.jar scijava-struc\r (esc)
   t-1.0.0.jar scijava-priority-1.0.0.jar scijava-progress-1.0.0.jar scija\r (esc)
   va-ops-spi-1.0.0.jar scijava-types-1.0.0.jar guava-31.1-jre.jar failure\r (esc)
   access-1.0.1.jar listenablefuture-9999.0-empty-to-avoid-conflict-with-g\r (esc)
   uava.jar jsr305-3.0.2.jar checker-qual-3.34.0.jar error_prone_annotatio\r (esc)
   ns-2.19.0.jar j2objc-annotations-2.8.jar slf4j-api-1.7.36.jar imglib2-6\r (esc)
   .2.0.jar imglib2-algorithm-0.14.0.jar trove4j-3.0.3.jar imglib2-cache-1\r (esc)
   .0.0-beta-17.jar caffeine-2.9.3.jar scijava-optional-1.0.1.jar imglib2-\r (esc)
   algorithm-fft-0.2.1.jar mines-jtk-20151125.jar imglib2-mesh-1.0.0.jar j\r (esc)
   ply-0.2.1.jar commons-lang3-3.12.0.jar imglib2-realtransform-4.0.1.jar \r (esc)
   jitk-tps-3.0.3.jar ejml-0.25.jar imglib2-roi-0.14.1.jar commons-math3-3\r (esc)
   .6.1.jar joml-1.10.5.jar ojalgo-45.1.1.jar jama-1.0.3.jar\r (esc)
  Specification-Title: SciJava Ops Image\r (esc)
  Specification-Version: 1.0\r (esc)
  Specification-Vendor: SciJava\r (esc)
  Implementation-Title: SciJava Ops Image\r (esc)
  Implementation-Version: 1.0.0\r (esc)
  Implementation-Vendor: SciJava\r (esc)
  Main-Class: org.scijava.ops.image.About\r (esc)
  Package: org.scijava.ops.image\r (esc)
  Automatic-Module-Name: org.scijava.ops.image\r (esc)
  Implementation-Build: 202fcef4cb3eee7ffe0c105ab2d5bc36d34c9cd1\r (esc)
  Implementation-Date: 2024-06-04T01:54:54+0000\r (esc)
  Premain-Class: \r (esc)
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

  $ jgo info pom com.google.guava:guava:33.0.0-jre
  <?xml version="1.0" ?>
  <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
      <groupId>org.scijava</groupId>
      <artifactId>pom-scijava</artifactId>
      <version>37.0.0</version>
      <relativePath/>
    </parent>
    <artifactId>guava</artifactId>
    <version>1.0.0</version>
    <name>SciJava Ops Image</name>
    <description>Image processing operations for SciJava Ops.</description>
    <url>https://github.com/scijava/scijava</url>
    <inceptionYear>2014</inceptionYear>
    <organization>
      <name>SciJava</name>
      <url>https://scijava.org/</url>
    </organization>
    <licenses>
      <license>
        <name>Simplified BSD License</name>
        <distribution>repo</distribution>
      </license>
    </licenses>
    <developers>
      <developer>
        <id>ctrueden</id>
        <name>Curtis Rueden</name>
        <roles>
          <role>founder</role>
          <role>lead</role>
          <role>debugger</role>
          <role>reviewer</role>
          <role>support</role>
          <role>maintainer</role>
        </roles>
      </developer>
      <developer>
        <id>gselzer</id>
        <name>Gabriel Selzer</name>
        <roles>
          <role>founder</role>
          <role>debugger</role>
          <role>reviewer</role>
          <role>support</role>
        </roles>
      </developer>
      <developer>
        <id>bnorthan</id>
        <name>Brian Northan</name>
        <roles>
          <role>debugger</role>
          <role>reviewer</role>
          <role>support</role>
        </roles>
      </developer>
    </developers>
    <contributors>
      <!-- Co-founders -->
      <contributor>
        <name>Christian Birkhold</name>
        <roles>
          <role>founder</role>
        </roles>
        <properties>
          <id>dietzc</id>
        </properties>
      </contributor>
      <contributor>
        <name>Martin Horn</name>
        <roles>
          <role>founder</role>
        </roles>
        <properties>
          <id>hornm</id>
        </properties>
      </contributor>
      <contributor>
        <name>Johannes Schindelin</name>
        <roles>
          <role>founder</role>
        </roles>
        <properties>
          <id>dscho</id>
        </properties>
      </contributor>
      <!-- Contributors, in alphabetical order by surname. -->
      <contributor>
        <name>Matthias Arzt</name>
        <properties>
          <id>maarzt</id>
        </properties>
      </contributor>
      <contributor>
        <name>Tim-Oliver Buchholz</name>
        <properties>
          <id>tibuch</id>
        </properties>
      </contributor>
      <contributor>
        <name>Eric Czech</name>
        <properties>
          <id>eric-czech</id>
        </properties>
      </contributor>
      <contributor>
        <name>Barry DeZonia</name>
        <properties>
          <id>bdezonia</id>
        </properties>
      </contributor>
      <contributor>
        <name>Ellen Dobson</name>
        <properties>
          <id>etadobson</id>
        </properties>
      </contributor>
      <contributor>
        <name>Richard Domander</name>
        <properties>
          <id>rimadoma</id>
        </properties>
      </contributor>
      <contributor>
        <name>Michael Doube</name>
        <properties>
          <id>mdoube</id>
        </properties>
      </contributor>
      <contributor>
        <name>Karl Duderstadt</name>
        <properties>
          <id>karlduderstadt</id>
        </properties>
      </contributor>
      <contributor>
        <name>Jan Eglinger</name>
        <properties>
          <id>imagejan</id>
        </properties>
      </contributor>
      <contributor>
        <name>Gabriel Einsdorf</name>
        <properties>
          <id>gab1one</id>
        </properties>
      </contributor>
      <contributor>
        <name>Edward Evans</name>
        <properties>
          <id>elevans</id>
        </properties>
      </contributor>
      <contributor>
        <name>Andreas Graumann</name>
        <properties>
          <id>angrauma</id>
        </properties>
      </contributor>
      <contributor>
        <name>Robert Haase</name>
        <properties>
          <id>haesleinhuepf</id>
        </properties>
      </contributor>
      <contributor>
        <name>Jonathan Hale</name>
        <properties>
          <id>Squareys</id>
        </properties>
      </contributor>
      <contributor>
        <name>Philipp Hanslovsky</name>
        <properties>
          <id>hanslovsky</id>
        </properties>
      </contributor>
      <contributor>
        <name>Kyle Harrington</name>
        <properties>
          <id>kephale</id>
        </properties>
      </contributor>
      <contributor>
        <name>Eike Heinz</name>
        <properties>
          <id>EikeHeinz</id>
        </properties>
      </contributor>
      <contributor>
        <name>Stefan Helfrich</name>
        <properties>
          <id>stelfrich</id>
        </properties>
      </contributor>
      <contributor>
        <name>Mark Hiner</name>
        <properties>
          <id>hinerm</id>
        </properties>
      </contributor>
      <contributor>
        <name>Hadrien Mary</name>
        <properties>
          <id>hadim</id>
        </properties>
      </contributor>
      <contributor>
        <name>Dave Niles</name>
        <properties>
          <id>djniles</id>
        </properties>
      </contributor>
      <contributor>
        <name>Aparna Pal</name>
        <properties>
          <id>apal4</id>
        </properties>
      </contributor>
      <contributor>
        <name>Tobias Pietzsch</name>
        <properties>
          <id>tpietzsch</id>
        </properties>
      </contributor>
      <contributor>
        <name>Igor Pisarev</name>
        <properties>
          <id>igorpisarev</id>
        </properties>
      </contributor>
      <contributor>
        <name>Stephan Saalfeld</name>
        <properties>
          <id>axtimwalde</id>
        </properties>
      </contributor>
      <contributor>
        <name>Simon Schmid</name>
        <properties>
          <id>SimonSchmid</id>
        </properties>
      </contributor>
      <contributor>
        <name>Deborah Schmidt</name>
        <properties>
          <id>frauzufall</id>
        </properties>
      </contributor>
      <contributor>
        <name>Daniel Seebacher</name>
        <properties>
          <id>seebacherd</id>
        </properties>
      </contributor>
      <contributor>
        <name>Jean-Yves Tinevez</name>
        <properties>
          <id>tinevez</id>
        </properties>
      </contributor>
      <contributor>
        <name>Vladimir Ulman</name>
        <properties>
          <id>xulman</id>
        </properties>
      </contributor>
      <contributor>
        <name>Alison Walter</name>
        <properties>
          <id>awalter17</id>
        </properties>
      </contributor>
      <contributor>
        <name>Shulei Wang</name>
        <properties>
          <id>lakerwsl</id>
        </properties>
      </contributor>
      <contributor>
        <name>Leon Yang</name>
        <properties>
          <id>lnyng</id>
        </properties>
      </contributor>
      <contributor>
        <name>Michael Zinsmaier</name>
        <properties>
          <id>MichaelZinsmaier</id>
        </properties>
      </contributor>
    </contributors>
    <mailingLists>
      <mailingList>
        <name>Image.sc Forum</name>
        <archive>https://forum.image.sc/tag/scijava</archive>
      </mailingList>
    </mailingLists>
    <scm>
      <connection>scm:git:https://github.com/scijava/scijava</connection>
      <developerConnection>scm:git:git@github.com:scijava/scijava</developerConnection>
      <tag>scijava-aggregator-1.0.0</tag>
      <url>https://github.com/scijava/scijava</url>
    </scm>
    <issueManagement>
      <system>GitHub Issues</system>
      <url>https://github.com/scijava/scijava/issues</url>
    </issueManagement>
    <ciManagement>
      <system>GitHub Actions</system>
      <url>https://github.com/scijava/scijava/actions</url>
    </ciManagement>
    <properties>
      <package-name>org.scijava.ops.image</package-name>
      <main-class>org.scijava.ops.image.About</main-class>
      <license.licenseName>bsd_2</license.licenseName>
      <license.copyrightOwners>SciJava developers.</license.copyrightOwners>
      <!--
  \t\tNB: Older versions of OpenJDK 11 have a bug in the javadoc tool, (esc)
  \t\twhich causes errors like: (esc)
  \t\t[ERROR] javadoc: error - The code being documented uses packages (esc)
  \t\tin the unnamed module, but the packages defined in (esc)
  \t\thttps://github.com/scijava/scijava/apidocs/ are in named modules. (esc)
  \t\tThe most recent version of OpenJDK 11 known to have this problem (esc)
  \t\tis 11.0.8; the oldest version known to have fixed it is 11.0.17. (esc)
  \t\tTherefore, we set the minimum build JDK version to 11.0.17 here. (esc)
  \t\t--> (esc)
      <scijava.jvm.build.version>[11.0.17,)</scijava.jvm.build.version>
      <scijava.jvm.version>11</scijava.jvm.version>
      <scijava.ops.parse>true</scijava.ops.parse>
      <!-- TEMP: Until pom-scijava 38.0.0 is released. -->
      <scijava-maven-plugin.version>3.0.0</scijava-maven-plugin.version>
      <imglib2-mesh.version>1.0.0</imglib2-mesh.version>
      <net.imglib2.imglib2-mesh.version>${imglib2-mesh.version}</net.imglib2.imglib2-mesh.version>
    </properties>
    <dependencies>
      <!-- SciJava dependencies -->
      <dependency>
        <groupId>org.scijava</groupId>
        <artifactId>scijava-collections</artifactId>
        <version>${project.version}</version>
      </dependency>
      <dependency>
        <groupId>org.scijava</groupId>
        <artifactId>scijava-common3</artifactId>
        <version>${project.version}</version>
      </dependency>
      <dependency>
        <groupId>org.scijava</groupId>
        <artifactId>scijava-concurrent</artifactId>
        <version>${project.version}</version>
      </dependency>
      <dependency>
        <groupId>org.scijava</groupId>
        <artifactId>scijava-function</artifactId>
        <version>${project.version}</version>
      </dependency>
      <dependency>
        <groupId>org.scijava</groupId>
        <artifactId>scijava-meta</artifactId>
        <version>${project.version}</version>
      </dependency>
      <dependency>
        <groupId>org.scijava</groupId>
        <artifactId>scijava-ops-api</artifactId>
        <version>${project.version}</version>
      </dependency>
      <dependency>
        <groupId>org.scijava</groupId>
        <artifactId>scijava-priority</artifactId>
        <version>${project.version}</version>
      </dependency>
      <dependency>
        <groupId>org.scijava</groupId>
        <artifactId>scijava-progress</artifactId>
        <version>${project.version}</version>
      </dependency>
      <dependency>
        <groupId>org.scijava</groupId>
        <artifactId>scijava-ops-spi</artifactId>
        <version>${project.version}</version>
      </dependency>
      <dependency>
        <groupId>org.scijava</groupId>
        <artifactId>scijava-types</artifactId>
        <version>${project.version}</version>
      </dependency>
      <!-- ImgLib2 dependencies -->
      <dependency>
        <groupId>net.imglib2</groupId>
        <artifactId>imglib2</artifactId>
      </dependency>
      <dependency>
        <groupId>net.imglib2</groupId>
        <artifactId>imglib2-algorithm</artifactId>
      </dependency>
      <dependency>
        <groupId>net.imglib2</groupId>
        <artifactId>imglib2-algorithm-fft</artifactId>
      </dependency>
      <dependency>
        <groupId>net.imglib2</groupId>
        <artifactId>imglib2-mesh</artifactId>
        <!-- TEMP: until added to pom-scijava -->
        <version>${net.imglib2.imglib2-mesh.version}</version>
      </dependency>
      <dependency>
        <groupId>net.imglib2</groupId>
        <artifactId>imglib2-realtransform</artifactId>
      </dependency>
      <dependency>
        <groupId>net.imglib2</groupId>
        <artifactId>imglib2-roi</artifactId>
      </dependency>
      <!-- Third party dependencies -->
      <dependency>
        <groupId>org.apache.commons</groupId>
        <artifactId>commons-math3</artifactId>
      </dependency>
      <dependency>
        <groupId>org.joml</groupId>
        <artifactId>joml</artifactId>
      </dependency>
      <dependency>
        <groupId>org.ojalgo</groupId>
        <artifactId>ojalgo</artifactId>
      </dependency>
      <dependency>
        <groupId>gov.nist.math</groupId>
        <artifactId>jama</artifactId>
      </dependency>
      <!-- Test scope dependencies -->
      <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter-api</artifactId>
        <scope>test</scope>
      </dependency>
      <dependency>
        <groupId>org.scijava</groupId>
        <artifactId>scijava-ops-engine</artifactId>
        <version>${project.version}</version>
        <scope>test</scope>
      </dependency>
      <dependency>
        <groupId>org.scijava</groupId>
        <artifactId>scijava-testutil</artifactId>
        <version>${project.version}</version>
        <scope>test</scope>
      </dependency>
      <dependency>
        <groupId>org.scijava</groupId>
        <artifactId>scijava-common</artifactId>
        <scope>test</scope>
      </dependency>
      <dependency>
        <groupId>io.scif</groupId>
        <artifactId>scifio</artifactId>
        <scope>test</scope>
      </dependency>
    </dependencies>
    <repositories>
      <repository>
        <id>scijava.public</id>
        <url>https://maven.scijava.org/content/groups/public</url>
      </repository>
    </repositories>
    <build>
      <plugins>
        <plugin>
          <artifactId>maven-compiler-plugin</artifactId>
          <configuration>
            <annotationProcessorPaths>
              <path>
                <groupId>org.scijava</groupId>
                <artifactId>scijava-ops-indexer</artifactId>
                <version>${project.version}</version>
              </path>
            </annotationProcessorPaths>
            <fork>true</fork>
            <compilerArgs>
              <arg>-Ascijava.ops.parse=&quot;${scijava.ops.parse}&quot;</arg>
              <arg>-Ascijava.ops.opVersion=&quot;${project.version}&quot;</arg>
            </compilerArgs>
          </configuration>
        </plugin>
        <plugin>
          <artifactId>maven-javadoc-plugin</artifactId>
          <configuration>
            <links>
              <link>https://javadoc.scijava.org/Java11/</link>
              <link>https://javadoc.scijava.org/ImgLib2/</link>
              <link>https://javadoc.scijava.org/Apache-Commons-Math/</link>
              <link>https://javadoc.scijava.org/JAMA/</link>
              <link>https://javadoc.scijava.org/JOML/</link>
              <link>https://javadoc.scijava.org/Javassist/</link>
              <link>https://javadoc.scijava.org/ojAlgo/</link>
            </links>
            <tagletArtifacts>
              <tagletArtifact>
                <groupId>org.scijava</groupId>
                <artifactId>scijava-taglets</artifactId>
                <version>${project.version}</version>
              </tagletArtifact>
            </tagletArtifacts>
            <tags>
              <tag>
                <name>implNote</name>
                <placement>a</placement>
                <head>Implementation Note:</head>
              </tag>
            </tags>
          </configuration>
        </plugin>
        <plugin>
          <artifactId>maven-enforcer-plugin</artifactId>
          <executions>
            <execution>
              <id>enforce-package-rules</id>
              <goals>
                <goal>enforce</goal>
              </goals>
              <phase>test</phase>
              <configuration>
                <rules>
                  <NoPackageCyclesRule implementation="org.scijava.maven.plugin.enforcer.NoPackageCyclesRule"/>
                  <NoSubpackageDependenceRule implementation="org.scijava.maven.plugin.enforcer.NoSubpackageDependenceRule"/>
                </rules>
              </configuration>
            </execution>
          </executions>
        </plugin>
        <plugin>
          <groupId>com.alexecollins.maven.plugin</groupId>
          <artifactId>script-maven-plugin</artifactId>
          <version>1.0.0</version>
          <executions>
            <execution>
              <id>union-metadata-indices</id>
              <phase>process-test-classes</phase>
              <goals>
                <goal>execute</goal>
              </goals>
              <configuration>
                <language>ruby</language>
                <script>
  \t\t\t\t\t\t\t\t# Append the source plugin annotations to the test plugin annotations (esc)
  \t\t\t\t\t\t\t\trequire 'set' (esc)
  \t\t\t\t\t\t\t\t# Handle windows paths (esc)
  \t\t\t\t\t\t\t\tbasedir = '${project.basedir}'.gsub /\\\\+/, '\\\\\\\\' (esc)
  \t\t\t\t\t\t\t\t# Reads plugin metadata into a set of strings, one per plugin declaration. (esc)
  \t\t\t\t\t\t\t\tdef read_plugins(path) (esc)
  \t\t\t\t\t\t\t\tdelim = 'UNIQUE-SEQUENCE-THAT-NO-PLUGIN-WILL-EVER-USE' (esc)
  \t\t\t\t\t\t\t\treturn File.exist?(path) ? File.read(path).sub('}{', '}' + delim + '{').split(delim).to_set : Set.new() (esc)
  \t\t\t\t\t\t\t\tend (esc)
  \t\t\t\t\t\t\t\t# Read in main and test scope plugin annotations. (esc)
  \t\t\t\t\t\t\t\t['ops.yaml'].each do |pluginsPath| (esc)
  \t\t\t\t\t\t\t\tmainPluginsPath = &quot;#{basedir}/target/classes/#{pluginsPath}&quot; (esc)
  \t\t\t\t\t\t\t\ttestPluginsPath = &quot;#{basedir}/target/test-classes/#{pluginsPath}&quot; (esc)
  \t\t\t\t\t\t\t\tmainPlugins = read_plugins(mainPluginsPath) (esc)
  \t\t\t\t\t\t\t\ttestPlugins = read_plugins(testPluginsPath) (esc)
  \t\t\t\t\t\t\t\t# Write out unioned plugin annotations to test scope plugin annotations. (esc)
  \t\t\t\t\t\t\t\t# Without this, the test scope code does not know of the main scope plugins. (esc)
  \t\t\t\t\t\t\t\tallPlugins = mainPlugins.union(testPlugins) (esc)
  \t\t\t\t\t\t\t\tunless allPlugins.empty?() (esc)
  \t\t\t\t\t\t\t\trequire 'fileutils' (esc)
  \t\t\t\t\t\t\t\tFileUtils.mkdir_p File.dirname(testPluginsPath) (esc)
  \t\t\t\t\t\t\t\tFile.write(testPluginsPath, allPlugins.to_a.join('')) (esc)
  \t\t\t\t\t\t\t\tend (esc)
  \t\t\t\t\t\t\t\tend (esc)
  \t\t\t\t\t\t\t</script> (esc)
              </configuration>
            </execution>
          </executions>
          <dependencies>
            <dependency>
              <groupId>org.jruby</groupId>
              <artifactId>jruby-complete</artifactId>
              <version>9.2.11.1</version>
              <scope>runtime</scope>
            </dependency>
          </dependencies>
        </plugin>
      </plugins>
    </build>
    <profiles>
      <profile>
        <id>only-eclipse-scijava</id>
        <activation>
          <property>
            <name>m2e.version</name>
          </property>
        </activation>
        <build>
          <pluginManagement>
            <plugins>
              <!--
  \t\t\t\t\t\tConfigure the Eclipse m2e plugin to support needed plugins. (esc)
  \t\t\t\t\t\t--> (esc)
              <plugin>
                <groupId>org.eclipse.m2e</groupId>
                <artifactId>lifecycle-mapping</artifactId>
                <!--
  \t\t\t\t\t\t\tNB: Eclipse cannot handle an overridden version property here! (esc)
  \t\t\t\t\t\t\tThe version needs to stay hardcoded at 1.0.0. (esc)
  \t\t\t\t\t\t\t--> (esc)
                <version>1.0.0</version>
                <configuration>
                  <lifecycleMappingMetadata>
                    <pluginExecutions combine.children="append">
                      <!--
  \t\t\t\t\t\t\t\t\t\tNB: Make Eclipse union the metadata indices on every build; see: (esc)
  \t\t\t\t\t\t\t\t\t\thttps://www.eclipse.org/m2e/documentation/m2e-execution-not-covered.html (esc)
  \t\t\t\t\t\t\t\t\t\t--> (esc)
                      <pluginExecution>
                        <pluginExecutionFilter>
                          <groupId>com.alexecollins.maven.plugin</groupId>
                          <artifactId>script-maven-plugin</artifactId>
                          <versionRange>${script-maven-plugin.version}</versionRange>
                          <goals>
                            <goal>execute</goal>
                          </goals>
                        </pluginExecutionFilter>
                        <action>
                          <execute>
                            <runOnConfiguration>true</runOnConfiguration>
                            <!--
  \t\t\t\t\t\t\t\t\t\t\t\t\tNB: You might think we could run the annotations (esc)
  \t\t\t\t\t\t\t\t\t\t\t\t\tunion script once only, at configuration time. (esc)
  \t\t\t\t\t\t\t\t\t\t\t\t\tUnfortunately, when configuration happens in Eclipse, (esc)
  \t\t\t\t\t\t\t\t\t\t\t\t\tthe plugin annotations have not yet been generated. (esc)
  \t\t\t\t\t\t\t\t\t\t\t\t\tSo let's redo the union on every incremental build. (esc)
  \t\t\t\t\t\t\t\t\t\t\t\t\tThat'll show 'em! (esc)
  \t\t\t\t\t\t\t\t\t\t\t\t\t--> (esc)
                            <runOnIncremental>true</runOnIncremental>
                          </execute>
                        </action>
                      </pluginExecution>
                    </pluginExecutions>
                  </lifecycleMappingMetadata>
                </configuration>
              </plugin>
            </plugins>
          </pluginManagement>
        </build>
      </profile>
    </profiles>
  </project>

Test info versions requires coordinates.

  $ jgo info versions
                                                                                  
   Usage: jgo info versions [OPTIONS] COORDINATE                                  
                                                                                  
   Try 'jgo info versions --help' for help                                        
  ╭─ Error ──────────────────────────────────────────────────────────────────────╮
  │ Missing argument 'COORDINATE'.                                               │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                                                                                  
  [2]

Test info versions with coordinates.

  $ jgo info versions com.google.guava:guava
  Available versions for com.google.guava:guava:
    1.0.0 (release)
    2.0.0-SNAPSHOT (latest)
    2.0.0-SNAPSHOT (latest)

Test info entrypoints without jgo.toml.

  $ jgo info entrypoints
  ERROR    jgo.toml not found                                                     
  [1]


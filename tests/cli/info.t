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
  */jars/j2objc-annotations-2.8.jar (glob)
  */jars/jsr305-3.0.2.jar (glob)
  */jars/listenablefuture-9999.0-empty-to-avoid-conflict-with-guava.jar (glob)

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
     com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
     com.google.j2objc:j2objc-annotations:jar:2.8:compile
     org.checkerframework:checker-qual:jar:3.41.0:compile

Test info deplist --direct flag.

  $ jgo info deplist --direct com.google.guava:guava:33.0.0-jre
  com.google.guava:guava:33.0.0-jre
     com.google.code.findbugs:jsr305:jar:3.0.2:compile
     com.google.errorprone:error_prone_annotations:jar:2.23.0:compile
     com.google.guava:failureaccess:jar:1.0.2:compile
     com.google.guava:listenablefuture:jar:9999.0-empty-to-avoid-conflict-with-guava:compile
     com.google.j2objc:j2objc-annotations:jar:2.8:compile
     org.checkerframework:checker-qual:jar:3.41.0:compile

Test info javainfo with no endpoint.

  $ jgo info javainfo
  ERROR    No endpoint specified                                                  
  [1]

Test info javainfo with endpoint.

  $ jgo info javainfo com.google.guava:guava:33.0.0-jre
  
  Environment: /home/*/.cache/jgo/com/google/guava/guava/* (glob)
  JARs directory: 
  /home/*/.cache/jgo/com/google/guava/guava/*/jars (glob)
  Total JARs: 3
  
  ╭───────────────────────── Java Version Requirements ──────────────────────────╮
  │ Minimum Java version: 7                                                      │
  │ Rounded to LTS: 8                                                            │
  ╰──────────────────────────────────────────────────────────────────────────────╯
                               Per-JAR Analysis                             
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
  ┃ JAR                        ┃ Java Version ┃ Max Bytecode ┃ Class Count ┃
  ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
  │ j2objc-annotations-2.8.jar │            7 │           51 │          13 │
  │ jsr305-3.0.2.jar           │            5 │           49 │          35 │
  └────────────────────────────┴──────────────┴──────────────┴─────────────┘
  
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

  $ jgo info pom com.google.guava:guava:33.0.0-jre
  <?xml version="1.0" ?>
  <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd">
    <!-- do_not_remove: published-with-gradle-metadata -->
    <modelVersion>4.0.0</modelVersion>
    <parent>
      <groupId>com.google.guava</groupId>
      <artifactId>guava-parent</artifactId>
      <version>33.0.0-jre</version>
    </parent>
    <artifactId>guava</artifactId>
    <packaging>bundle</packaging>
    <name>Guava: Google Core Libraries for Java</name>
    <url>https://github.com/google/guava</url>
    <description>
      Guava is a suite of core and expanded libraries that include
      utility classes, Google's collections, I/O classes, and
      much more.
    </description>
    <dependencies>
      <dependency>
        <groupId>com.google.guava</groupId>
        <artifactId>failureaccess</artifactId>
        <version>1.0.2</version>
      </dependency>
      <dependency>
        <groupId>com.google.guava</groupId>
        <artifactId>listenablefuture</artifactId>
        <version>9999.0-empty-to-avoid-conflict-with-guava</version>
      </dependency>
      <dependency>
        <groupId>com.google.code.findbugs</groupId>
        <artifactId>jsr305</artifactId>
      </dependency>
      <dependency>
        <groupId>org.checkerframework</groupId>
        <artifactId>checker-qual</artifactId>
      </dependency>
      <dependency>
        <groupId>com.google.errorprone</groupId>
        <artifactId>error_prone_annotations</artifactId>
      </dependency>
      <dependency>
        <groupId>com.google.j2objc</groupId>
        <artifactId>j2objc-annotations</artifactId>
      </dependency>
      <!-- TODO(cpovirk): does this comment belong on the <dependency> in <profiles>? -->
      <!-- TODO(cpovirk): want this only for dependency plugin but seems not to work there? Maven runs without failure, but the resulting Javadoc is missing the hoped-for inherited text -->
    </dependencies>
    <build>
      <resources>
        <resource>
          <directory>..</directory>
          <includes>
            <include>LICENSE</include>
            <!-- copied from the parent pom because I couldn't figure out a way to make combine.children="append" work -->
            <include>proguard/*</include>
          </includes>
          <targetPath>META-INF</targetPath>
        </resource>
      </resources>
      <plugins>
        <plugin>
          <artifactId>maven-jar-plugin</artifactId>
          <configuration>
            <archive>
              <manifestEntries>
                <Automatic-Module-Name>com.google.common</Automatic-Module-Name>
              </manifestEntries>
            </archive>
          </configuration>
        </plugin>
        <plugin>
          <extensions>true</extensions>
          <groupId>org.apache.felix</groupId>
          <artifactId>maven-bundle-plugin</artifactId>
          <version>5.1.8</version>
          <executions>
            <execution>
              <id>bundle-manifest</id>
              <phase>process-classes</phase>
              <goals>
                <goal>manifest</goal>
              </goals>
            </execution>
          </executions>
          <configuration>
            <instructions>
              <Export-Package>
                !com.google.common.base.internal,
                !com.google.common.util.concurrent.internal,
                com.google.common.*
              </Export-Package>
              <Import-Package>
                com.google.common.util.concurrent.internal,
                javax.annotation;resolution:=optional,
                javax.crypto.*;resolution:=optional,
                sun.misc.*;resolution:=optional
              </Import-Package>
              <Bundle-DocURL>https://github.com/google/guava/</Bundle-DocURL>
            </instructions>
          </configuration>
        </plugin>
        <plugin>
          <artifactId>maven-compiler-plugin</artifactId>
        </plugin>
        <plugin>
          <artifactId>maven-source-plugin</artifactId>
        </plugin>
        <!-- TODO(cpovirk): include JDK sources when building testlib doc, too -->
        <plugin>
          <artifactId>maven-dependency-plugin</artifactId>
          <executions>
            <execution>
              <id>unpack-jdk-sources</id>
              <phase>generate-sources</phase>
              <goals>
                <goal>unpack-dependencies</goal>
              </goals>
              <configuration>
                <includeArtifactIds>srczip</includeArtifactIds>
                <outputDirectory>${project.build.directory}/jdk-sources</outputDirectory>
                <silent>false</silent>
                <!-- Exclude module-info files (since we're using -source 8 to avoid other modules problems) and FileDescriptor (which uses a language feature not available in Java 8). -->
                <excludes>**/module-info.java,**/java/io/FileDescriptor.java</excludes>
              </configuration>
            </execution>
          </executions>
        </plugin>
        <plugin>
          <groupId>org.codehaus.mojo</groupId>
          <artifactId>animal-sniffer-maven-plugin</artifactId>
        </plugin>
        <plugin>
          <artifactId>maven-javadoc-plugin</artifactId>
          <configuration>
            <!-- TODO(cpovirk): Move this to the parent after making jdk-sources available there. -->
            <!-- TODO(cpovirk): can we use includeDependencySources and a local com.oracle.java:jdk-lib:noversion:sources instead of all this unzipping and manual sourcepath modification? -->
            <!-- (We need JDK *sources*, not just -link, so that {@inheritDoc} works.) -->
            <sourcepath>${project.build.sourceDirectory}:${project.build.directory}/jdk-sources</sourcepath>
            <!-- Passing `-subpackages com.google.common` breaks things, so we explicitly exclude everything else instead. -->
            <!-- excludePackageNames requires specification of packages separately from "all subpackages".
                 https://issues.apache.org/jira/browse/MJAVADOC-584 -->
            <excludePackageNames>
              com.azul.tooling.in,com.google.common.base.internal,com.google.common.base.internal.*,com.google.thirdparty.publicsuffix,com.google.thirdparty.publicsuffix.*,com.oracle.*,com.sun.*,java.*,javax.*,jdk,jdk.*,org.*,sun.*
            </excludePackageNames>
            <!-- Ignore some tags that are found in Java 11 sources but not recognized... under -source 8, I think it was? I can no longer reproduce the failure. -->
            <tags>
              <tag>
                <name>apiNote</name>
                <placement>X</placement>
              </tag>
              <tag>
                <name>implNote</name>
                <placement>X</placement>
              </tag>
              <tag>
                <name>implSpec</name>
                <placement>X</placement>
              </tag>
              <tag>
                <name>jls</name>
                <placement>X</placement>
              </tag>
              <tag>
                <name>revised</name>
                <placement>X</placement>
              </tag>
              <tag>
                <name>spec</name>
                <placement>X</placement>
              </tag>
            </tags>
            <!-- TODO(cpovirk): Move this to the parent after making the package-list files available there. -->
            <!-- We add the link ourselves, both so that we can choose Java 9 over the version that -source suggests and so that we can solve the JSR305 problem described below. -->
            <detectJavaApiLink>false</detectJavaApiLink>
            <offlineLinks>
              <!-- We need local copies of some of these for 2 reasons: a User-Agent problem (https://stackoverflow.com/a/47891403/28465) and an SSL problem (https://issues.apache.org/jira/browse/MJAVADOC-507). If we choose to work around the User-Agent problem, we can go back to <links>, sidestepping the SSL problem. -->
              <!-- Even after we stop using JSR305 annotations in our own code, we'll want this link so that NullPointerTester's docs can link to @CheckForNull and friends... at least once we start using this config for guava-testlib. -->
              <offlineLink>
                <url>https://static.javadoc.io/com.google.code.findbugs/jsr305/3.0.1/</url>
                <location>${project.basedir}/javadoc-link/jsr305</location>
              </offlineLink>
              <offlineLink>
                <url>https://static.javadoc.io/com.google.j2objc/j2objc-annotations/1.1/</url>
                <location>${project.basedir}/javadoc-link/j2objc-annotations</location>
              </offlineLink>
              <!-- The JDK doc must be listed after JSR305 (and as an <offlineLink>, not a <link>) so that JSR305 "claims" javax.annotation. -->
              <offlineLink>
                <url>https://docs.oracle.com/javase/9/docs/api/</url>
                <location>https://docs.oracle.com/javase/9/docs/api/</location>
              </offlineLink>
              <!-- The Checker Framework likewise would claim javax.annotations, despite providing only a subset of the JSR305 annotations, so it must likewise come after JSR305. -->
              <offlineLink>
                <url>https://checkerframework.org/api/</url>
                <location>${project.basedir}/javadoc-link/checker-framework</location>
              </offlineLink>
            </offlineLinks>
            <links>
              <link>https://errorprone.info/api/latest/</link>
            </links>
            <overview>../overview.html</overview>
          </configuration>
        </plugin>
        <plugin>
          <artifactId>maven-resources-plugin</artifactId>
          <executions>
            <execution>
              <id>gradle-module-metadata</id>
              <phase>compile</phase>
              <goals>
                <goal>copy-resources</goal>
              </goals>
              <configuration>
                <outputDirectory>target/publish</outputDirectory>
                <resources>
                  <resource>
                    <directory>.</directory>
                    <includes>
                      <include>module.json</include>
                    </includes>
                    <filtering>true</filtering>
                  </resource>
                </resources>
              </configuration>
            </execution>
          </executions>
        </plugin>
        <plugin>
          <groupId>org.codehaus.mojo</groupId>
          <artifactId>build-helper-maven-plugin</artifactId>
          <executions>
            <execution>
              <id>attach-gradle-module-metadata</id>
              <goals>
                <goal>attach-artifact</goal>
              </goals>
              <configuration>
                <artifacts>
                  <artifact>
                    <file>target/publish/module.json</file>
                    <type>module</type>
                  </artifact>
                </artifacts>
              </configuration>
            </execution>
          </executions>
        </plugin>
      </plugins>
    </build>
    <profiles>
      <profile>
        <id>srczip-parent</id>
        <activation>
          <file>
            <exists>${java.home}/../src.zip</exists>
          </file>
        </activation>
        <dependencies>
          <dependency>
            <groupId>jdk</groupId>
            <artifactId>srczip</artifactId>
            <version>999</version>
            <scope>system</scope>
            <systemPath>${java.home}/../src.zip</systemPath>
            <optional>true</optional>
          </dependency>
        </dependencies>
      </profile>
      <profile>
        <id>srczip-lib</id>
        <activation>
          <file>
            <exists>${java.home}/lib/src.zip</exists>
          </file>
        </activation>
        <dependencies>
          <dependency>
            <groupId>jdk</groupId>
            <artifactId>srczip</artifactId>
            <version>999</version>
            <scope>system</scope>
            <systemPath>${java.home}/lib/src.zip</systemPath>
            <optional>true</optional>
          </dependency>
        </dependencies>
        <build>
          <plugins>
            <plugin>
              <artifactId>maven-javadoc-plugin</artifactId>
              <configuration>
                <!-- We need to point at the java.base subdirectory because Maven appears to assume that package foo.bar is located in foo/bar and not java.base/foo/bar when translating excludePackageNames into filenames to pass to javadoc. (Note that manually passing -exclude to javadoc appears to possibly not work at all for java.* types??) Also, referring only to java.base avoids a lot of other sources. -->
                <sourcepath>${project.build.sourceDirectory}:${project.build.directory}/jdk-sources/java.base</sourcepath>
              </configuration>
            </plugin>
          </plugins>
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

  $ jgo info versions com.google.guava:guava | head -n100
  Available versions for com.google.guava:guava:
    HEAD-android-SNAPSHOT
    HEAD-jre-SNAPSHOT
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
    11.0.2-atlassian-01
    11.0.2-atlassian-02
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
    19.0.0.jbossorg-1
    19.0.0.jbossorg-2
    19.0.20150826
    20.0-rc1
    20.0
    20.0-hal
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
    24.0-SNAPSHOT
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

Test info entrypoints without jgo.toml.

  $ jgo info entrypoints
  ERROR    jgo.toml not found                                                     
  [1]


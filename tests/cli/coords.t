Tests jgo info coords, and the local-JAR forms of jgo info pom and manifest.

An input is required.

  $ jgo info coords
  ERROR    No JAR specified
  [1]

A missing local JAR file is reported as an error, not treated as a coordinate.

  $ jgo info coords "$TMPDIR/does-not-exist.jar"
  ERROR    *does-not-exist.jar not found* (glob)
  [1]

A file that is not a JAR at all is rejected.

  $ echo "not a jar" > "$TMPDIR/bogus.jar"
  $ jgo info coords "$TMPDIR/bogus.jar"
  ERROR    Not a valid JAR file: *bogus.jar (glob)
  [1]

Show the coordinate a resolved artifact was built from.

  $ jgo info coords com.google.code.findbugs:jsr305:3.0.2
  Artifact Coordinates
  ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
  ┃ JAR              ┃ Coordinate                            ┃ Source         ┃
  ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
  │ jsr305-3.0.2.jar │ com.google.code.findbugs:jsr305:3.0.2 │ pom.properties │
  └──────────────────┴───────────────────────────────────────┴────────────────┘

Show the coordinate of the same artifact by local JAR path.

  $ jar=$(jgo info jars com.google.code.findbugs:jsr305:3.0.2 | grep jsr305)
  $ jgo info coords "$jar"
  Artifact Coordinates
  ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
  ┃ JAR              ┃ Coordinate                            ┃ Source         ┃
  ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
  │ jsr305-3.0.2.jar │ com.google.code.findbugs:jsr305:3.0.2 │ pom.properties │
  └──────────────────┴───────────────────────────────────────┴────────────────┘

Dump the POM embedded in a local JAR.

  $ jgo info pom "$jar" | head -6
  <?xml version="1.0" ?>
  <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 http://maven.apache.org/maven-v4_0_0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
      <groupId>org.sonatype.oss</groupId>
      <artifactId>oss-parent</artifactId>

Show the manifest of a local JAR.

  $ jgo info manifest "$jar" | head -3
  Manifest-Version: 1.0
  Bundle-Description: JSR305 Annotations for Findbugs
  Bundle-License: http://www.apache.org/licenses/LICENSE-2.0.txt

A JAR with no Maven metadata and no usable manifest cannot be identified.

  $ jgo info coords antlr:antlr:2.7.7
  Artifact Coordinates
  ┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━┓
  ┃ JAR             ┃ Coordinate   ┃ Source ┃
  ┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━┩
  │ antlr-2.7.7.jar │ unidentified │        │
  └─────────────────┴──────────────┴────────┘
  TIP: Use --remote to identify JARs by checksum via Maven Central

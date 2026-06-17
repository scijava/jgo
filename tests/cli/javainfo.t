Tests jgo info javainfo with local JARs, class files, POMs, and flags.

The --direct and --self flags are mutually exclusive.

  $ jgo info javainfo --direct --self com.google.guava:guava:33.0.0-jre
  ERROR    --direct and --self are mutually exclusive                             
  [1]

A missing local JAR file is reported as an error, not treated as a coordinate.

  $ jgo info javainfo "$TMPDIR/does-not-exist.jar"
  ERROR    $TMPDIR/does-not-exist.jar not found             
  [1]

Analyze a single named artifact with --self (no transitive dependencies).

  $ jgo info javainfo --self com.google.guava:guava:33.0.0-jre
  ╭───────────────────────── Java Version Requirements ──────────────────────────╮
  │ Minimum Java version: 8                                                      │
  │ (already an LTS version)                                                     │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  Per-JAR Analysis
  ┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
  ┃ JAR                  ┃ Java Version ┃ Max Bytecode ┃ Class Count ┃
  ┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
  │ guava-33.0.0-jre.jar │            8 │           52 │        2003 │
  └──────────────────────┴──────────────┴──────────────┴─────────────┘

Analyze the dependencies of a local project POM (also ensures jsr305 is cached).

  $ cat > "$TMPDIR/javainfo-pom.xml" <<'POM'
  > <?xml version="1.0" encoding="UTF-8"?>
  > <project xmlns="http://maven.apache.org/POM/4.0.0">
  >   <modelVersion>4.0.0</modelVersion>
  >   <groupId>org.example</groupId>
  >   <artifactId>javainfo-demo</artifactId>
  >   <version>1.0.0</version>
  >   <dependencies>
  >     <dependency>
  >       <groupId>com.google.code.findbugs</groupId>
  >       <artifactId>jsr305</artifactId>
  >       <version>3.0.2</version>
  >     </dependency>
  >   </dependencies>
  > </project>
  > POM

  $ jgo info javainfo "$TMPDIR/javainfo-pom.xml"
  ╭───────────────────────── Java Version Requirements ──────────────────────────╮
  │ Minimum Java version: 5                                                      │
  │ Rounded to LTS: 8                                                            │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  Per-JAR Analysis
  ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
  ┃ JAR              ┃ Java Version ┃ Max Bytecode ┃ Class Count ┃
  ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
  │ jsr305-3.0.2.jar │            5 │           49 │          35 │
  └──────────────────┴──────────────┴──────────────┴─────────────┘

Analyze a local JAR file directly (no Maven resolution).

  $ jgo info javainfo "$HOME/.m2/repository/com/google/code/findbugs/jsr305/3.0.2/jsr305-3.0.2.jar"
  ╭───────────────────────── Java Version Requirements ──────────────────────────╮
  │ Minimum Java version: 5                                                      │
  │ Rounded to LTS: 8                                                            │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  Per-JAR Analysis
  ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
  ┃ JAR              ┃ Java Version ┃ Max Bytecode ┃ Class Count ┃
  ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
  │ jsr305-3.0.2.jar │            5 │           49 │          35 │
  └──────────────────┴──────────────┴──────────────┴─────────────┘

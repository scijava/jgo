Tests jgo info javainfo with local JARs, class files, POMs, and flags.

The --direct and --self flags are mutually exclusive.

  $ jgo info javainfo --direct --self com.google.guava:guava:33.0.0-jre
  ERROR    --direct and --self are mutually exclusive
  [1]

A missing local JAR file is reported as an error, not treated as a coordinate.

  $ jgo info javainfo "$TMPDIR/does-not-exist.jar"
  ERROR    *does-not-exist.jar not found* (glob)
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

A pom.xml is treated as a project checkout. Before it is built, jgo warns that
the project's own classes could not be analyzed.

  $ mkdir -p "$TMPDIR/javainfo-proj"
  $ cp "$TMPDIR/javainfo-pom.xml" "$TMPDIR/javainfo-proj/pom.xml"
  $ jgo info javainfo --self "$TMPDIR/javainfo-proj"
  WARNING  */javainfo-proj/pom.xml: no build output found at *Build it first (e.g. `mvn compile`).* (glob)
  No analyzable classes found

Once built, the project's own classes are analyzed ahead of its dependencies.

  $ mkdir -p "$TMPDIR/javainfo-proj/target/classes/org/example"
  $ printf '\312\376\272\276\000\000\000\067' > "$TMPDIR/javainfo-proj/target/classes/org/example/Demo.class"
  $ jgo info javainfo "$TMPDIR/javainfo-proj"
  ╭───────────────────────── Java Version Requirements ──────────────────────────╮
  │ Minimum Java version: 11                                                     │
  │ (already an LTS version)                                                     │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  Per-JAR Analysis
  ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
  ┃ JAR              ┃ Java Version ┃ Max Bytecode ┃ Class Count ┃
  ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
  │ target/classes/  │           11 │           55 │           1 │
  │ jsr305-3.0.2.jar │            5 │           49 │          35 │
  └──────────────────┴──────────────┴──────────────┴─────────────┘

A published POM (any name other than pom.xml) resolves its own artifact from
the local repository instead.

  $ jgo info javainfo --self "$HOME/.m2/repository/com/google/code/findbugs/jsr305/3.0.2/jsr305-3.0.2.pom"
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

Tests jgo --color and --wrap flags.

Color modes:
* plain = no ANSI markup
* styled = ANSI styles (bold, italic, underline) but no colors
* rich = full ANSI colors and styles

Wrap modes:
* raw = no artificial line breaks added
* smart = intelligent wrapping to stay within terminal width

Because --color and --wrap can interact in unintuitive ways, we validate
each combination of these flags with each of four different kinds of output.

* Output modes: Table, Tree, List, XML
* Color modes: plain, styled, rich
* Wrap modes: raw, smart

Total test sections: 4 x 2 x 3 = 24

Note that when running via prysk, jgo/rich operates in non-tty mode:
* implicit --color -> --color=auto -> --color=plain
* implicit --wrap -> --wrap=auto -> --wrap=raw
In the interest faster execution, we do not test implicit nor auto modes here;
if those behave differently, it is a bug in the parser, not --color nor --wrap.

For the output modes, we use the following jgo commands:
* Table: `jgo info javainfo`
* Tree: `jgo tree`
* List: `jgo list`
* XML: `jgo info pom`

Under the hood, both List and XML use the rich Console, but each has
a history of its own distinct bugs over the course of development.

-- Table output | color=plain | wrap=raw --

The table should be as wide as it needs to be to fully render the content.

  $ jgo --color=plain --wrap=raw info javainfo com.google.guava:guava:33.0.0-jre
  
  Environment: */.cache/jgo/envs/com/google/guava/guava/d1c57891c188d58a (glob)
  Module-path JARs: 7
  Total JARs: 7
  
  ╭───────────────────────── Java Version Requirements ──────────────────────────╮
  │ Minimum Java version: 8                                                      │
  │ (already an LTS version)                                                     │
  ╰──────────────────────────────────────────────────────────────────────────────╯
   *Per-JAR Analysis * (re)
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
  ┃ JAR                                ┃ Java Version ┃ Max Bytecode ┃ Class Count ┃
  ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
  │ checker-qual-3.41.0.jar            │            8 │           52 │         366 │
  │ error_prone_annotations-2.23.0.jar │            8 │           52 │          27 │
  │ guava-33.0.0-jre.jar               │            8 │           52 │        2003 │
  │ failureaccess-1.0.2.jar            │            7 │           51 │           2 │
  │ j2objc-annotations-2.8.jar         │            7 │           51 │          13 │
  │ jsr305-3.0.2.jar                   │            5 │           49 │          35 │
  └────────────────────────────────────┴──────────────┴──────────────┴─────────────┘

-- Table output | color=plain | wrap=smart --

Ellipses should be used to keep table width within terminal width (80 chars).

  $ jgo --color=plain --wrap=smart info javainfo com.google.guava:guava:33.0.0-jre
  
  Environment: 
  */.cache/jgo/envs/com/google/guava/guava/d1c57891c188d58a (glob)
  Module-path JARs: 7
  Total JARs: 7
  
  ╭───────────────────────── Java Version Requirements ──────────────────────────╮
  │ Minimum Java version: 8                                                      │
  │ (already an LTS version)                                                     │
  ╰──────────────────────────────────────────────────────────────────────────────╯
   *Per-JAR Analysis * (re)
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

-- Table output | color=styled | wrap=raw --

  $ jgo --color=styled --wrap=raw info javainfo com.google.guava:guava:33.0.0-jre
  
  \x1b[1mEnvironment:\x1b[0m */.cache/jgo/envs/com/google/guava/guava/d1c57891c188d58a (esc) (glob)
  \x1b[1mModule-path JARs:\x1b[0m \x1b[1m7\x1b[0m (esc)
  \x1b[1mTotal JARs:\x1b[0m \x1b[1m7\x1b[0m (esc)
   (esc)
  ╭───────────────────────── \x1b[1mJava Version Requirements\x1b[0m ──────────────────────────╮ (esc)
  │ \x1b[1mMinimum Java version:\x1b[0m 8                                                      │ (esc)
  │ \x1b[2m(already an LTS version)\x1b[0m                                                     │ (esc)
  ╰──────────────────────────────────────────────────────────────────────────────╯ (esc)
  *Per-JAR Analysis* (glob)
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓ (esc)
  ┃\x1b[1m \x1b[0m\x1b[1mJAR                               \x1b[0m\x1b[1m \x1b[0m┃\x1b[1m \x1b[0m\x1b[1mJava Version\x1b[0m\x1b[1m \x1b[0m┃\x1b[1m \x1b[0m\x1b[1mMax Bytecode\x1b[0m\x1b[1m \x1b[0m┃\x1b[1m \x1b[0m\x1b[1mClass Count\x1b[0m\x1b[1m \x1b[0m┃ (esc)
  ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩ (esc)
  │\x1b[1m \x1b[0m\x1b[1mchecker-qual-3.41.0.jar           \x1b[0m\x1b[1m \x1b[0m│            8 │           52 │         366 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1merror_prone_annotations-2.23.0.jar\x1b[0m\x1b[1m \x1b[0m│            8 │           52 │          27 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mguava-33.0.0-jre.jar              \x1b[0m\x1b[1m \x1b[0m│            8 │           52 │        2003 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mfailureaccess-1.0.2.jar           \x1b[0m\x1b[1m \x1b[0m│            7 │           51 │           2 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mj2objc-annotations-2.8.jar        \x1b[0m\x1b[1m \x1b[0m│            7 │           51 │          13 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mjsr305-3.0.2.jar                  \x1b[0m\x1b[1m \x1b[0m│            5 │           49 │          35 │ (esc)
  └────────────────────────────────────┴──────────────┴──────────────┴─────────────┘ (esc)

-- Table output | color=styled | wrap=smart --

  $ jgo --color=styled --wrap=smart info javainfo com.google.guava:guava:33.0.0-jre
  
  \x1b[1mEnvironment:\x1b[0m  (esc)
  */.cache/jgo/envs/com/google/guava/guava/d1c57891c188d58a (glob)
  \x1b[1mModule-path JARs:\x1b[0m \x1b[1m7\x1b[0m (esc)
  \x1b[1mTotal JARs:\x1b[0m \x1b[1m7\x1b[0m (esc)
   (esc)
  ╭───────────────────────── \x1b[1mJava Version Requirements\x1b[0m ──────────────────────────╮ (esc)
  │ \x1b[1mMinimum Java version:\x1b[0m 8                                                      │ (esc)
  │ \x1b[2m(already an LTS version)\x1b[0m                                                     │ (esc)
  ╰──────────────────────────────────────────────────────────────────────────────╯ (esc)
  *Per-JAR Analysis* (glob)
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓ (esc)
  ┃\x1b[1m \x1b[0m\x1b[1mJAR                             \x1b[0m\x1b[1m \x1b[0m┃\x1b[1m \x1b[0m\x1b[1mJava Version\x1b[0m\x1b[1m \x1b[0m┃\x1b[1m \x1b[0m\x1b[1mMax Bytecode\x1b[0m\x1b[1m \x1b[0m┃\x1b[1m \x1b[0m\x1b[1mClass Count\x1b[0m\x1b[1m \x1b[0m┃ (esc)
  ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩ (esc)
  │\x1b[1m \x1b[0m\x1b[1mchecker-qual-3.41.0.jar         \x1b[0m\x1b[1m \x1b[0m│            8 │           52 │         366 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1merror_prone_annotations-2.23.0.…\x1b[0m\x1b[1m \x1b[0m│            8 │           52 │          27 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mguava-33.0.0-jre.jar            \x1b[0m\x1b[1m \x1b[0m│            8 │           52 │        2003 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mfailureaccess-1.0.2.jar         \x1b[0m\x1b[1m \x1b[0m│            7 │           51 │           2 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mj2objc-annotations-2.8.jar      \x1b[0m\x1b[1m \x1b[0m│            7 │           51 │          13 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mjsr305-3.0.2.jar                \x1b[0m\x1b[1m \x1b[0m│            5 │           49 │          35 │ (esc)
  └──────────────────────────────────┴──────────────┴──────────────┴─────────────┘

-- Table output | color=rich | wrap=raw --

  $ jgo --color=rich --wrap=raw info javainfo com.google.guava:guava:33.0.0-jre
  
  \x1b[1;36mEnvironment:\x1b[0m \x1b[35m*/.cache/jgo/envs/com/google/guava/guava/\x1b[0m\x1b[95md1c57891c188d58a\x1b[0m (esc) (glob)
  \x1b[1;36mModule-path JARs:\x1b[0m \x1b[1;36m7\x1b[0m (esc)
  \x1b[1;36mTotal JARs:\x1b[0m \x1b[1;36m7\x1b[0m (esc)
  
  \x1b[36m╭─\x1b[0m\x1b[36m────────────────────────\x1b[0m\x1b[36m \x1b[0m\x1b[1;36mJava Version Requirements\x1b[0m\x1b[36m \x1b[0m\x1b[36m─────────────────────────\x1b[0m\x1b[36m─╮\x1b[0m (esc)
  \x1b[36m│\x1b[0m \x1b[1;36mMinimum Java version:\x1b[0m 8                                                      \x1b[36m│\x1b[0m (esc)
  \x1b[36m│\x1b[0m \x1b[2m(already an LTS version)\x1b[0m                                                     \x1b[36m│\x1b[0m (esc)
  \x1b[36m╰──────────────────────────────────────────────────────────────────────────────╯\x1b[0m (esc)
  *Per-JAR Analysis* (glob)
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
  ┃\x1b[1;36m \x1b[0m\x1b[1;36mJAR                               \x1b[0m\x1b[1;36m \x1b[0m┃\x1b[1;36m \x1b[0m\x1b[1;36mJava Version\x1b[0m\x1b[1;36m \x1b[0m┃\x1b[1;36m \x1b[0m\x1b[1;36mMax Bytecode\x1b[0m\x1b[1;36m \x1b[0m┃\x1b[1;36m \x1b[0m\x1b[1;36mClass Count\x1b[0m\x1b[1;36m \x1b[0m┃ (esc)
  ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
  │\x1b[1m \x1b[0m\x1b[1mchecker-qual-3.41.0.jar           \x1b[0m\x1b[1m \x1b[0m│\x1b[32m \x1b[0m\x1b[32m           8\x1b[0m\x1b[32m \x1b[0m│           52 │         366 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1merror_prone_annotations-2.23.0.jar\x1b[0m\x1b[1m \x1b[0m│\x1b[32m \x1b[0m\x1b[32m           8\x1b[0m\x1b[32m \x1b[0m│           52 │          27 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mguava-33.0.0-jre.jar              \x1b[0m\x1b[1m \x1b[0m│\x1b[32m \x1b[0m\x1b[32m           8\x1b[0m\x1b[32m \x1b[0m│           52 │        2003 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mfailureaccess-1.0.2.jar           \x1b[0m\x1b[1m \x1b[0m│\x1b[32m \x1b[0m\x1b[32m           7\x1b[0m\x1b[32m \x1b[0m│           51 │           2 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mj2objc-annotations-2.8.jar        \x1b[0m\x1b[1m \x1b[0m│\x1b[32m \x1b[0m\x1b[32m           7\x1b[0m\x1b[32m \x1b[0m│           51 │          13 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mjsr305-3.0.2.jar                  \x1b[0m\x1b[1m \x1b[0m│\x1b[32m \x1b[0m\x1b[32m           5\x1b[0m\x1b[32m \x1b[0m│           49 │          35 │ (esc)
  └────────────────────────────────────┴──────────────┴──────────────┴─────────────┘

-- Table output | color=rich | wrap=smart --

  $ jgo --color=rich --wrap=smart info javainfo com.google.guava:guava:33.0.0-jre
  
  \x1b[1;36mEnvironment:\x1b[0m  (esc)
  \x1b[35m*/.cache/jgo/envs/com/google/guava/guava/\x1b[0m\x1b[95md1c57891c188d58a\x1b[0m (esc) (glob)
  \x1b[1;36mModule-path JARs:\x1b[0m \x1b[1;36m7\x1b[0m (esc)
  \x1b[1;36mTotal JARs:\x1b[0m \x1b[1;36m7\x1b[0m (esc)
  
  \x1b[36m╭─\x1b[0m\x1b[36m────────────────────────\x1b[0m\x1b[36m \x1b[0m\x1b[1;36mJava Version Requirements\x1b[0m\x1b[36m \x1b[0m\x1b[36m─────────────────────────\x1b[0m\x1b[36m─╮\x1b[0m (esc)
  \x1b[36m│\x1b[0m \x1b[1;36mMinimum Java version:\x1b[0m 8                                                      \x1b[36m│\x1b[0m (esc)
  \x1b[36m│\x1b[0m \x1b[2m(already an LTS version)\x1b[0m                                                     \x1b[36m│\x1b[0m (esc)
  \x1b[36m╰──────────────────────────────────────────────────────────────────────────────╯\x1b[0m (esc)
  *Per-JAR Analysis* (glob)
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┓
  ┃\x1b[1;36m \x1b[0m\x1b[1;36mJAR                             \x1b[0m\x1b[1;36m \x1b[0m┃\x1b[1;36m \x1b[0m\x1b[1;36mJava Version\x1b[0m\x1b[1;36m \x1b[0m┃\x1b[1;36m \x1b[0m\x1b[1;36mMax Bytecode\x1b[0m\x1b[1;36m \x1b[0m┃\x1b[1;36m \x1b[0m\x1b[1;36mClass Count\x1b[0m\x1b[1;36m \x1b[0m┃ (esc)
  ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━┩
  │\x1b[1m \x1b[0m\x1b[1mchecker-qual-3.41.0.jar         \x1b[0m\x1b[1m \x1b[0m│\x1b[32m \x1b[0m\x1b[32m           8\x1b[0m\x1b[32m \x1b[0m│           52 │         366 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1merror_prone_annotations-2.23.0.…\x1b[0m\x1b[1m \x1b[0m│\x1b[32m \x1b[0m\x1b[32m           8\x1b[0m\x1b[32m \x1b[0m│           52 │          27 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mguava-33.0.0-jre.jar            \x1b[0m\x1b[1m \x1b[0m│\x1b[32m \x1b[0m\x1b[32m           8\x1b[0m\x1b[32m \x1b[0m│           52 │        2003 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mfailureaccess-1.0.2.jar         \x1b[0m\x1b[1m \x1b[0m│\x1b[32m \x1b[0m\x1b[32m           7\x1b[0m\x1b[32m \x1b[0m│           51 │           2 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mj2objc-annotations-2.8.jar      \x1b[0m\x1b[1m \x1b[0m│\x1b[32m \x1b[0m\x1b[32m           7\x1b[0m\x1b[32m \x1b[0m│           51 │          13 │ (esc)
  │\x1b[1m \x1b[0m\x1b[1mjsr305-3.0.2.jar                \x1b[0m\x1b[1m \x1b[0m│\x1b[32m \x1b[0m\x1b[32m           5\x1b[0m\x1b[32m \x1b[0m│           49 │          35 │ (esc)
  └──────────────────────────────────┴──────────────┴──────────────┴─────────────┘

-- Tree output | color=plain | wrap=raw --

One tree element per line, no matter how long.

  $ jgo --color=plain --wrap=raw --ignore-config --include-optional --full-coordinates tree org.apache.logging.log4j:log4j-core:2.25.1
  
  └── org.apache.logging.log4j:log4j-core:jar:2.25.1:compile
      ├── org.apache.logging.log4j:log4j-api:jar:2.25.1:compile
      ├── org.apache.commons:commons-compress:jar:1.27.1:compile (optional)
      │   ├── commons-codec:commons-codec:jar:1.18.0:compile
      │   ├── commons-io:commons-io:jar:2.19.0:compile
      │   └── org.apache.commons:commons-lang3:jar:3.17.0:compile
      ├── org.apache.commons:commons-csv:jar:1.14.0:compile (optional)
      ├── com.conversantmedia:disruptor:jar:1.2.15:compile (optional)
      │   └── org.slf4j:slf4j-api:jar:1.7.13:compile
      ├── com.lmax:disruptor:jar:3.4.4:compile (optional)
      ├── com.fasterxml.jackson.core:jackson-core:jar:2.19.1:compile (optional)
      ├── com.fasterxml.jackson.core:jackson-databind:jar:2.19.1:compile (optional)
      │   └── com.fasterxml.jackson.core:jackson-annotations:jar:2.19.1:compile
      ├── com.fasterxml.jackson.dataformat:jackson-dataformat-xml:jar:2.19.1:compile (optional)
      │   ├── org.codehaus.woodstox:stax2-api:jar:4.2.2:compile
      │   └── com.fasterxml.woodstox:woodstox-core:jar:7.1.1:compile
      ├── com.fasterxml.jackson.dataformat:jackson-dataformat-yaml:jar:2.19.1:compile (optional)
      │   └── org.yaml:snakeyaml:jar:2.4:compile
      ├── org.jctools:jctools-core:jar:4.0.5:compile (optional)
      ├── org.zeromq:jeromq:jar:0.6.0:compile (optional)
      │   └── eu.neilalexander:jnacl:jar:1.0.0:compile
      ├── org.apache.kafka:kafka-clients:jar:3.9.1:compile (optional)
      │   ├── com.github.luben:zstd-jni:jar:1.5.7-4:runtime
      │   ├── org.lz4:lz4-java:jar:1.8.0:runtime
      │   └── org.xerial.snappy:snappy-java:jar:1.1.10.5:runtime
      └── com.sun.mail:javax.mail:jar:1.6.2:runtime (optional)
          └── javax.activation:activation:jar:1.1:runtime

-- Tree output | color=plain | wrap=smart --

Word-wrapped (optional) qualifiers should be aligned with tree node indentation.

  $ jgo --color=plain --wrap=smart --ignore-config --include-optional --full-coordinates tree org.apache.logging.log4j:log4j-core:2.25.1
  
  └── org.apache.logging.log4j:log4j-core:jar:2.25.1:compile
      ├── org.apache.logging.log4j:log4j-api:jar:2.25.1:compile
      ├── org.apache.commons:commons-compress:jar:1.27.1:compile (optional)
      │   ├── commons-codec:commons-codec:jar:1.18.0:compile
      │   ├── commons-io:commons-io:jar:2.19.0:compile
      │   └── org.apache.commons:commons-lang3:jar:3.17.0:compile
      ├── org.apache.commons:commons-csv:jar:1.14.0:compile (optional)
      ├── com.conversantmedia:disruptor:jar:1.2.15:compile (optional)
      │   └── org.slf4j:slf4j-api:jar:1.7.13:compile
      ├── com.lmax:disruptor:jar:3.4.4:compile (optional)
      ├── com.fasterxml.jackson.core:jackson-core:jar:2.19.1:compile (optional)
      ├── com.fasterxml.jackson.core:jackson-databind:jar:2.19.1:compile 
      │   (optional)
      │   └── com.fasterxml.jackson.core:jackson-annotations:jar:2.19.1:compile
      ├── com.fasterxml.jackson.dataformat:jackson-dataformat-xml:jar:2.19.1:compi
      │   le (optional)
      │   ├── org.codehaus.woodstox:stax2-api:jar:4.2.2:compile
      │   └── com.fasterxml.woodstox:woodstox-core:jar:7.1.1:compile
      ├── com.fasterxml.jackson.dataformat:jackson-dataformat-yaml:jar:2.19.1:comp
      │   ile (optional)
      │   └── org.yaml:snakeyaml:jar:2.4:compile
      ├── org.jctools:jctools-core:jar:4.0.5:compile (optional)
      ├── org.zeromq:jeromq:jar:0.6.0:compile (optional)
      │   └── eu.neilalexander:jnacl:jar:1.0.0:compile
      ├── org.apache.kafka:kafka-clients:jar:3.9.1:compile (optional)
      │   ├── com.github.luben:zstd-jni:jar:1.5.7-4:runtime
      │   ├── org.lz4:lz4-java:jar:1.8.0:runtime
      │   └── org.xerial.snappy:snappy-java:jar:1.1.10.5:runtime
      └── com.sun.mail:javax.mail:jar:1.6.2:runtime (optional)
          └── javax.activation:activation:jar:1.1:runtime

-- Tree output | color=styled | wrap=raw --

  $ jgo --color=styled --wrap=raw --ignore-config --include-optional --full-coordinates tree org.apache.logging.log4j:log4j-core:2.25.1
  
  └── org.apache.logging.log4j\x1b[2m:\x1b[0m\x1b[1mlog4j-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.25.1\x1b[2m:\x1b[0mcompile (esc)
      ├── org.apache.logging.log4j\x1b[2m:\x1b[0m\x1b[1mlog4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.25.1\x1b[2m:\x1b[0mcompile (esc)
      ├── org.apache.commons\x1b[2m:\x1b[0m\x1b[1mcommons-compress\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.27.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      │   ├── commons-codec\x1b[2m:\x1b[0m\x1b[1mcommons-codec\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.18.0\x1b[2m:\x1b[0mcompile (esc)
      │   ├── commons-io\x1b[2m:\x1b[0m\x1b[1mcommons-io\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.0\x1b[2m:\x1b[0mcompile (esc)
      │   └── org.apache.commons\x1b[2m:\x1b[0m\x1b[1mcommons-lang3\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m3.17.0\x1b[2m:\x1b[0mcompile (esc)
      ├── org.apache.commons\x1b[2m:\x1b[0m\x1b[1mcommons-csv\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.14.0\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      ├── com.conversantmedia\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.2.15\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      │   └── org.slf4j\x1b[2m:\x1b[0m\x1b[1mslf4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.7.13\x1b[2m:\x1b[0mcompile (esc)
      ├── com.lmax\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m3.4.4\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      ├── com.fasterxml.jackson.core\x1b[2m:\x1b[0m\x1b[1mjackson-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      ├── com.fasterxml.jackson.core\x1b[2m:\x1b[0m\x1b[1mjackson-databind\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      │   └── com.fasterxml.jackson.core\x1b[2m:\x1b[0m\x1b[1mjackson-annotations\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile (esc)
      ├── com.fasterxml.jackson.dataformat\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-xml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      │   ├── org.codehaus.woodstox\x1b[2m:\x1b[0m\x1b[1mstax2-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m4.2.2\x1b[2m:\x1b[0mcompile (esc)
      │   └── com.fasterxml.woodstox\x1b[2m:\x1b[0m\x1b[1mwoodstox-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m7.1.1\x1b[2m:\x1b[0mcompile (esc)
      ├── com.fasterxml.jackson.dataformat\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-yaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      │   └── org.yaml\x1b[2m:\x1b[0m\x1b[1msnakeyaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.4\x1b[2m:\x1b[0mcompile (esc)
      ├── org.jctools\x1b[2m:\x1b[0m\x1b[1mjctools-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m4.0.5\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      ├── org.zeromq\x1b[2m:\x1b[0m\x1b[1mjeromq\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m0.6.0\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      │   └── eu.neilalexander\x1b[2m:\x1b[0m\x1b[1mjnacl\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.0.0\x1b[2m:\x1b[0mcompile (esc)
      ├── org.apache.kafka\x1b[2m:\x1b[0m\x1b[1mkafka-clients\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m3.9.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      │   ├── com.github.luben\x1b[2m:\x1b[0m\x1b[1mzstd-jni\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.5.7-4\x1b[2m:\x1b[0mruntime (esc)
      │   ├── org.lz4\x1b[2m:\x1b[0m\x1b[1mlz4-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.8.0\x1b[2m:\x1b[0mruntime (esc)
      │   └── org.xerial.snappy\x1b[2m:\x1b[0m\x1b[1msnappy-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.1.10.5\x1b[2m:\x1b[0mruntime (esc)
      └── com.sun.mail\x1b[2m:\x1b[0m\x1b[1mjavax.mail\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.6.2\x1b[2m:\x1b[0mruntime \x1b[2m(optional)\x1b[0m (esc)
          └── javax.activation\x1b[2m:\x1b[0m\x1b[1mactivation\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.1\x1b[2m:\x1b[0mruntime (esc)

-- Tree output | color=styled | wrap=smart --

  $ jgo --color=styled --wrap=smart --ignore-config --include-optional --full-coordinates tree org.apache.logging.log4j:log4j-core:2.25.1
  
  └── org.apache.logging.log4j\x1b[2m:\x1b[0m\x1b[1mlog4j-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.25.1\x1b[2m:\x1b[0mcompile (esc)
      ├── org.apache.logging.log4j\x1b[2m:\x1b[0m\x1b[1mlog4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.25.1\x1b[2m:\x1b[0mcompile (esc)
      ├── org.apache.commons\x1b[2m:\x1b[0m\x1b[1mcommons-compress\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.27.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      │   ├── commons-codec\x1b[2m:\x1b[0m\x1b[1mcommons-codec\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.18.0\x1b[2m:\x1b[0mcompile (esc)
      │   ├── commons-io\x1b[2m:\x1b[0m\x1b[1mcommons-io\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.0\x1b[2m:\x1b[0mcompile (esc)
      │   └── org.apache.commons\x1b[2m:\x1b[0m\x1b[1mcommons-lang3\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m3.17.0\x1b[2m:\x1b[0mcompile (esc)
      ├── org.apache.commons\x1b[2m:\x1b[0m\x1b[1mcommons-csv\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.14.0\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      ├── com.conversantmedia\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.2.15\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      │   └── org.slf4j\x1b[2m:\x1b[0m\x1b[1mslf4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.7.13\x1b[2m:\x1b[0mcompile (esc)
      ├── com.lmax\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m3.4.4\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      ├── com.fasterxml.jackson.core\x1b[2m:\x1b[0m\x1b[1mjackson-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      ├── com.fasterxml.jackson.core\x1b[2m:\x1b[0m\x1b[1mjackson-databind\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile  (esc)
      │   \x1b[2m(optional)\x1b[0m (esc)
      │   └── com.fasterxml.jackson.core\x1b[2m:\x1b[0m\x1b[1mjackson-annotations\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile (esc)
      ├── com.fasterxml.jackson.dataformat\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-xml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompi (esc)
      │   le \x1b[2m(optional)\x1b[0m (esc)
      │   ├── org.codehaus.woodstox\x1b[2m:\x1b[0m\x1b[1mstax2-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m4.2.2\x1b[2m:\x1b[0mcompile (esc)
      │   └── com.fasterxml.woodstox\x1b[2m:\x1b[0m\x1b[1mwoodstox-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m7.1.1\x1b[2m:\x1b[0mcompile (esc)
      ├── com.fasterxml.jackson.dataformat\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-yaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcomp (esc)
      │   ile \x1b[2m(optional)\x1b[0m (esc)
      │   └── org.yaml\x1b[2m:\x1b[0m\x1b[1msnakeyaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.4\x1b[2m:\x1b[0mcompile (esc)
      ├── org.jctools\x1b[2m:\x1b[0m\x1b[1mjctools-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m4.0.5\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      ├── org.zeromq\x1b[2m:\x1b[0m\x1b[1mjeromq\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m0.6.0\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      │   └── eu.neilalexander\x1b[2m:\x1b[0m\x1b[1mjnacl\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.0.0\x1b[2m:\x1b[0mcompile (esc)
      ├── org.apache.kafka\x1b[2m:\x1b[0m\x1b[1mkafka-clients\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m3.9.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
      │   ├── com.github.luben\x1b[2m:\x1b[0m\x1b[1mzstd-jni\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.5.7-4\x1b[2m:\x1b[0mruntime (esc)
      │   ├── org.lz4\x1b[2m:\x1b[0m\x1b[1mlz4-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.8.0\x1b[2m:\x1b[0mruntime (esc)
      │   └── org.xerial.snappy\x1b[2m:\x1b[0m\x1b[1msnappy-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.1.10.5\x1b[2m:\x1b[0mruntime (esc)
      └── com.sun.mail\x1b[2m:\x1b[0m\x1b[1mjavax.mail\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.6.2\x1b[2m:\x1b[0mruntime \x1b[2m(optional)\x1b[0m (esc)
          └── javax.activation\x1b[2m:\x1b[0m\x1b[1mactivation\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.1\x1b[2m:\x1b[0mruntime (esc)

-- Tree output | color=rich | wrap=raw --

  $ jgo --color=rich --wrap=raw --ignore-config --include-optional --full-coordinates tree org.apache.logging.log4j:log4j-core:2.25.1
  
  └── \x1b[36morg.apache.logging.log4j\x1b[0m\x1b[2m:\x1b[0m\x1b[1mlog4j-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.25.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36morg.apache.logging.log4j\x1b[0m\x1b[2m:\x1b[0m\x1b[1mlog4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.25.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36morg.apache.commons\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-compress\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.27.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      │   ├── \x1b[36mcommons-codec\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-codec\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.18.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      │   ├── \x1b[36mcommons-io\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-io\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      │   └── \x1b[36morg.apache.commons\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-lang3\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m3.17.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36morg.apache.commons\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-csv\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.14.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      ├── \x1b[36mcom.conversantmedia\x1b[0m\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.2.15\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      │   └── \x1b[36morg.slf4j\x1b[0m\x1b[2m:\x1b[0m\x1b[1mslf4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.7.13\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36mcom.lmax\x1b[0m\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m3.4.4\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      ├── \x1b[36mcom.fasterxml.jackson.core\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      ├── \x1b[36mcom.fasterxml.jackson.core\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-databind\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      │   └── \x1b[36mcom.fasterxml.jackson.core\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-annotations\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36mcom.fasterxml.jackson.dataformat\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-xml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      │   ├── \x1b[36morg.codehaus.woodstox\x1b[0m\x1b[2m:\x1b[0m\x1b[1mstax2-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m4.2.2\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      │   └── \x1b[36mcom.fasterxml.woodstox\x1b[0m\x1b[2m:\x1b[0m\x1b[1mwoodstox-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m7.1.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36mcom.fasterxml.jackson.dataformat\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-yaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      │   └── \x1b[36morg.yaml\x1b[0m\x1b[2m:\x1b[0m\x1b[1msnakeyaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.4\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36morg.jctools\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjctools-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m4.0.5\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      ├── \x1b[36morg.zeromq\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjeromq\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m0.6.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      │   └── \x1b[36meu.neilalexander\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjnacl\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.0.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36morg.apache.kafka\x1b[0m\x1b[2m:\x1b[0m\x1b[1mkafka-clients\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m3.9.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      │   ├── \x1b[36mcom.github.luben\x1b[0m\x1b[2m:\x1b[0m\x1b[1mzstd-jni\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.5.7-4\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
      │   ├── \x1b[36morg.lz4\x1b[0m\x1b[2m:\x1b[0m\x1b[1mlz4-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.8.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
      │   └── \x1b[36morg.xerial.snappy\x1b[0m\x1b[2m:\x1b[0m\x1b[1msnappy-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.1.10.5\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
      └── \x1b[36mcom.sun.mail\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjavax.mail\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.6.2\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
          └── \x1b[36mjavax.activation\x1b[0m\x1b[2m:\x1b[0m\x1b[1mactivation\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)

-- Tree output | color=rich | wrap=smart --

  $ jgo --color=rich --wrap=smart --ignore-config --include-optional --full-coordinates tree org.apache.logging.log4j:log4j-core:2.25.1
  
  └── \x1b[36morg.apache.logging.log4j\x1b[0m\x1b[2m:\x1b[0m\x1b[1mlog4j-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.25.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36morg.apache.logging.log4j\x1b[0m\x1b[2m:\x1b[0m\x1b[1mlog4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.25.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36morg.apache.commons\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-compress\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.27.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      │   ├── \x1b[36mcommons-codec\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-codec\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.18.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      │   ├── \x1b[36mcommons-io\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-io\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      │   └── \x1b[36morg.apache.commons\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-lang3\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m3.17.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36morg.apache.commons\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-csv\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.14.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      ├── \x1b[36mcom.conversantmedia\x1b[0m\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.2.15\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      │   └── \x1b[36morg.slf4j\x1b[0m\x1b[2m:\x1b[0m\x1b[1mslf4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.7.13\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36mcom.lmax\x1b[0m\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m3.4.4\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      ├── \x1b[36mcom.fasterxml.jackson.core\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      ├── \x1b[36mcom.fasterxml.jackson.core\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-databind\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m  (esc)
      │   \x1b[2m(optional)\x1b[0m (esc)
      │   └── \x1b[36mcom.fasterxml.jackson.core\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-annotations\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36mcom.fasterxml.jackson.dataformat\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-xml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompi\x1b[0m (esc)
      │   \x1b[34mle\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      │   ├── \x1b[36morg.codehaus.woodstox\x1b[0m\x1b[2m:\x1b[0m\x1b[1mstax2-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m4.2.2\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      │   └── \x1b[36mcom.fasterxml.woodstox\x1b[0m\x1b[2m:\x1b[0m\x1b[1mwoodstox-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m7.1.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36mcom.fasterxml.jackson.dataformat\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-yaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcomp\x1b[0m (esc)
      │   \x1b[34mile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      │   └── \x1b[36morg.yaml\x1b[0m\x1b[2m:\x1b[0m\x1b[1msnakeyaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.4\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36morg.jctools\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjctools-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m4.0.5\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      ├── \x1b[36morg.zeromq\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjeromq\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m0.6.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      │   └── \x1b[36meu.neilalexander\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjnacl\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.0.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
      ├── \x1b[36morg.apache.kafka\x1b[0m\x1b[2m:\x1b[0m\x1b[1mkafka-clients\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m3.9.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
      │   ├── \x1b[36mcom.github.luben\x1b[0m\x1b[2m:\x1b[0m\x1b[1mzstd-jni\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.5.7-4\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
      │   ├── \x1b[36morg.lz4\x1b[0m\x1b[2m:\x1b[0m\x1b[1mlz4-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.8.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
      │   └── \x1b[36morg.xerial.snappy\x1b[0m\x1b[2m:\x1b[0m\x1b[1msnappy-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.1.10.5\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
      └── \x1b[36mcom.sun.mail\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjavax.mail\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.6.2\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
          └── \x1b[36mjavax.activation\x1b[0m\x1b[2m:\x1b[0m\x1b[1mactivation\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)

-- List output | color=plain | wrap=raw --

There should be no artificial line breaks.

  $ jgo --color=plain --wrap=raw --ignore-config --include-optional --full-coordinates list org.apache.logging.log4j:log4j-core:2.25.1
  org.apache.logging.log4j:log4j-core:jar:2.25.1:compile
     com.conversantmedia:disruptor:jar:1.2.15:compile (optional)
     com.fasterxml.jackson.core:jackson-annotations:jar:2.19.1:compile
     com.fasterxml.jackson.core:jackson-core:jar:2.19.1:compile (optional)
     com.fasterxml.jackson.core:jackson-databind:jar:2.19.1:compile (optional)
     com.fasterxml.jackson.dataformat:jackson-dataformat-xml:jar:2.19.1:compile (optional)
     com.fasterxml.jackson.dataformat:jackson-dataformat-yaml:jar:2.19.1:compile (optional)
     com.fasterxml.woodstox:woodstox-core:jar:7.1.1:compile
     com.github.luben:zstd-jni:jar:1.5.7-4:runtime
     com.lmax:disruptor:jar:3.4.4:compile (optional)
     com.sun.mail:javax.mail:jar:1.6.2:runtime (optional)
     commons-codec:commons-codec:jar:1.18.0:compile
     commons-io:commons-io:jar:2.19.0:compile
     eu.neilalexander:jnacl:jar:1.0.0:compile
     javax.activation:activation:jar:1.1:runtime
     org.apache.commons:commons-compress:jar:1.27.1:compile (optional)
     org.apache.commons:commons-csv:jar:1.14.0:compile (optional)
     org.apache.commons:commons-lang3:jar:3.17.0:compile
     org.apache.kafka:kafka-clients:jar:3.9.1:compile (optional)
     org.apache.logging.log4j:log4j-api:jar:2.25.1:compile
     org.codehaus.woodstox:stax2-api:jar:4.2.2:compile
     org.jctools:jctools-core:jar:4.0.5:compile (optional)
     org.lz4:lz4-java:jar:1.8.0:runtime
     org.slf4j:slf4j-api:jar:1.7.13:compile
     org.xerial.snappy:snappy-java:jar:1.1.10.5:runtime
     org.yaml:snakeyaml:jar:2.4:compile
     org.zeromq:jeromq:jar:0.6.0:compile (optional)

-- List output | color=plain | wrap=smart --

Smart wrapping should use intelligent word-boundary wrapping.

  $ jgo --color=plain --wrap=smart --ignore-config --include-optional --full-coordinates list org.apache.logging.log4j:log4j-core:2.25.1
  org.apache.logging.log4j:log4j-core:jar:2.25.1:compile
     com.conversantmedia:disruptor:jar:1.2.15:compile (optional)
     com.fasterxml.jackson.core:jackson-annotations:jar:2.19.1:compile
     com.fasterxml.jackson.core:jackson-core:jar:2.19.1:compile (optional)
     com.fasterxml.jackson.core:jackson-databind:jar:2.19.1:compile (optional)
     com.fasterxml.jackson.dataformat:jackson-dataformat-xml:jar:2.19.1:compile 
  (optional)
     com.fasterxml.jackson.dataformat:jackson-dataformat-yaml:jar:2.19.1:compile 
  (optional)
     com.fasterxml.woodstox:woodstox-core:jar:7.1.1:compile
     com.github.luben:zstd-jni:jar:1.5.7-4:runtime
     com.lmax:disruptor:jar:3.4.4:compile (optional)
     com.sun.mail:javax.mail:jar:1.6.2:runtime (optional)
     commons-codec:commons-codec:jar:1.18.0:compile
     commons-io:commons-io:jar:2.19.0:compile
     eu.neilalexander:jnacl:jar:1.0.0:compile
     javax.activation:activation:jar:1.1:runtime
     org.apache.commons:commons-compress:jar:1.27.1:compile (optional)
     org.apache.commons:commons-csv:jar:1.14.0:compile (optional)
     org.apache.commons:commons-lang3:jar:3.17.0:compile
     org.apache.kafka:kafka-clients:jar:3.9.1:compile (optional)
     org.apache.logging.log4j:log4j-api:jar:2.25.1:compile
     org.codehaus.woodstox:stax2-api:jar:4.2.2:compile
     org.jctools:jctools-core:jar:4.0.5:compile (optional)
     org.lz4:lz4-java:jar:1.8.0:runtime
     org.slf4j:slf4j-api:jar:1.7.13:compile
     org.xerial.snappy:snappy-java:jar:1.1.10.5:runtime
     org.yaml:snakeyaml:jar:2.4:compile
     org.zeromq:jeromq:jar:0.6.0:compile (optional)

-- List output | color=styled | wrap=raw --

There should be ANSI styles but no color, and no extra line breaks.

  $ jgo --color=styled --wrap=raw --ignore-config --include-optional --full-coordinates list org.apache.logging.log4j:log4j-core:2.25.1
  org.apache.logging.log4j\x1b[2m:\x1b[0m\x1b[1mlog4j-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.25.1\x1b[2m:\x1b[0mcompile (esc)
     com.conversantmedia\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.2.15\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     com.fasterxml.jackson.core\x1b[2m:\x1b[0m\x1b[1mjackson-annotations\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile (esc)
     com.fasterxml.jackson.core\x1b[2m:\x1b[0m\x1b[1mjackson-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     com.fasterxml.jackson.core\x1b[2m:\x1b[0m\x1b[1mjackson-databind\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     com.fasterxml.jackson.dataformat\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-xml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     com.fasterxml.jackson.dataformat\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-yaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     com.fasterxml.woodstox\x1b[2m:\x1b[0m\x1b[1mwoodstox-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m7.1.1\x1b[2m:\x1b[0mcompile (esc)
     com.github.luben\x1b[2m:\x1b[0m\x1b[1mzstd-jni\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.5.7-4\x1b[2m:\x1b[0mruntime (esc)
     com.lmax\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m3.4.4\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     com.sun.mail\x1b[2m:\x1b[0m\x1b[1mjavax.mail\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.6.2\x1b[2m:\x1b[0mruntime \x1b[2m(optional)\x1b[0m (esc)
     commons-codec\x1b[2m:\x1b[0m\x1b[1mcommons-codec\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.18.0\x1b[2m:\x1b[0mcompile (esc)
     commons-io\x1b[2m:\x1b[0m\x1b[1mcommons-io\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.0\x1b[2m:\x1b[0mcompile (esc)
     eu.neilalexander\x1b[2m:\x1b[0m\x1b[1mjnacl\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.0.0\x1b[2m:\x1b[0mcompile (esc)
     javax.activation\x1b[2m:\x1b[0m\x1b[1mactivation\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.1\x1b[2m:\x1b[0mruntime (esc)
     org.apache.commons\x1b[2m:\x1b[0m\x1b[1mcommons-compress\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.27.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     org.apache.commons\x1b[2m:\x1b[0m\x1b[1mcommons-csv\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.14.0\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     org.apache.commons\x1b[2m:\x1b[0m\x1b[1mcommons-lang3\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m3.17.0\x1b[2m:\x1b[0mcompile (esc)
     org.apache.kafka\x1b[2m:\x1b[0m\x1b[1mkafka-clients\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m3.9.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     org.apache.logging.log4j\x1b[2m:\x1b[0m\x1b[1mlog4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.25.1\x1b[2m:\x1b[0mcompile (esc)
     org.codehaus.woodstox\x1b[2m:\x1b[0m\x1b[1mstax2-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m4.2.2\x1b[2m:\x1b[0mcompile (esc)
     org.jctools\x1b[2m:\x1b[0m\x1b[1mjctools-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m4.0.5\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     org.lz4\x1b[2m:\x1b[0m\x1b[1mlz4-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.8.0\x1b[2m:\x1b[0mruntime (esc)
     org.slf4j\x1b[2m:\x1b[0m\x1b[1mslf4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.7.13\x1b[2m:\x1b[0mcompile (esc)
     org.xerial.snappy\x1b[2m:\x1b[0m\x1b[1msnappy-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.1.10.5\x1b[2m:\x1b[0mruntime (esc)
     org.yaml\x1b[2m:\x1b[0m\x1b[1msnakeyaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.4\x1b[2m:\x1b[0mcompile (esc)
     org.zeromq\x1b[2m:\x1b[0m\x1b[1mjeromq\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m0.6.0\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)

-- List output | color=styled | wrap=smart --

There should be ANSI styling but no color, with word wrapping.

  $ jgo --color=styled --wrap=smart --ignore-config --include-optional --full-coordinates list org.apache.logging.log4j:log4j-core:2.25.1
  org.apache.logging.log4j\x1b[2m:\x1b[0m\x1b[1mlog4j-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.25.1\x1b[2m:\x1b[0mcompile (esc)
     com.conversantmedia\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.2.15\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     com.fasterxml.jackson.core\x1b[2m:\x1b[0m\x1b[1mjackson-annotations\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile (esc)
     com.fasterxml.jackson.core\x1b[2m:\x1b[0m\x1b[1mjackson-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     com.fasterxml.jackson.core\x1b[2m:\x1b[0m\x1b[1mjackson-databind\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     com.fasterxml.jackson.dataformat\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-xml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile  (esc)
  \x1b[2m(optional)\x1b[0m (esc)
     com.fasterxml.jackson.dataformat\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-yaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.1\x1b[2m:\x1b[0mcompile  (esc)
  \x1b[2m(optional)\x1b[0m (esc)
     com.fasterxml.woodstox\x1b[2m:\x1b[0m\x1b[1mwoodstox-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m7.1.1\x1b[2m:\x1b[0mcompile (esc)
     com.github.luben\x1b[2m:\x1b[0m\x1b[1mzstd-jni\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.5.7-4\x1b[2m:\x1b[0mruntime (esc)
     com.lmax\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m3.4.4\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     com.sun.mail\x1b[2m:\x1b[0m\x1b[1mjavax.mail\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.6.2\x1b[2m:\x1b[0mruntime \x1b[2m(optional)\x1b[0m (esc)
     commons-codec\x1b[2m:\x1b[0m\x1b[1mcommons-codec\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.18.0\x1b[2m:\x1b[0mcompile (esc)
     commons-io\x1b[2m:\x1b[0m\x1b[1mcommons-io\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.19.0\x1b[2m:\x1b[0mcompile (esc)
     eu.neilalexander\x1b[2m:\x1b[0m\x1b[1mjnacl\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.0.0\x1b[2m:\x1b[0mcompile (esc)
     javax.activation\x1b[2m:\x1b[0m\x1b[1mactivation\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.1\x1b[2m:\x1b[0mruntime (esc)
     org.apache.commons\x1b[2m:\x1b[0m\x1b[1mcommons-compress\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.27.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     org.apache.commons\x1b[2m:\x1b[0m\x1b[1mcommons-csv\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.14.0\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     org.apache.commons\x1b[2m:\x1b[0m\x1b[1mcommons-lang3\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m3.17.0\x1b[2m:\x1b[0mcompile (esc)
     org.apache.kafka\x1b[2m:\x1b[0m\x1b[1mkafka-clients\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m3.9.1\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     org.apache.logging.log4j\x1b[2m:\x1b[0m\x1b[1mlog4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.25.1\x1b[2m:\x1b[0mcompile (esc)
     org.codehaus.woodstox\x1b[2m:\x1b[0m\x1b[1mstax2-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m4.2.2\x1b[2m:\x1b[0mcompile (esc)
     org.jctools\x1b[2m:\x1b[0m\x1b[1mjctools-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m4.0.5\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)
     org.lz4\x1b[2m:\x1b[0m\x1b[1mlz4-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.8.0\x1b[2m:\x1b[0mruntime (esc)
     org.slf4j\x1b[2m:\x1b[0m\x1b[1mslf4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.7.13\x1b[2m:\x1b[0mcompile (esc)
     org.xerial.snappy\x1b[2m:\x1b[0m\x1b[1msnappy-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m1.1.10.5\x1b[2m:\x1b[0mruntime (esc)
     org.yaml\x1b[2m:\x1b[0m\x1b[1msnakeyaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m2.4\x1b[2m:\x1b[0mcompile (esc)
     org.zeromq\x1b[2m:\x1b[0m\x1b[1mjeromq\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m0.6.0\x1b[2m:\x1b[0mcompile \x1b[2m(optional)\x1b[0m (esc)

-- List output | color=rich | wrap=raw --

There should be full ANSI color, but no extra line breaks.

  $ jgo --color=rich --wrap=raw --ignore-config --include-optional --full-coordinates list org.apache.logging.log4j:log4j-core:2.25.1
  \x1b[36morg.apache.logging.log4j\x1b[0m\x1b[2m:\x1b[0m\x1b[1mlog4j-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.25.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36mcom.conversantmedia\x1b[0m\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.2.15\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcom.fasterxml.jackson.core\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-annotations\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36mcom.fasterxml.jackson.core\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcom.fasterxml.jackson.core\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-databind\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcom.fasterxml.jackson.dataformat\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-xml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcom.fasterxml.jackson.dataformat\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-yaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcom.fasterxml.woodstox\x1b[0m\x1b[2m:\x1b[0m\x1b[1mwoodstox-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m7.1.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36mcom.github.luben\x1b[0m\x1b[2m:\x1b[0m\x1b[1mzstd-jni\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.5.7-4\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
     \x1b[36mcom.lmax\x1b[0m\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m3.4.4\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcom.sun.mail\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjavax.mail\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.6.2\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcommons-codec\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-codec\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.18.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36mcommons-io\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-io\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36meu.neilalexander\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjnacl\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.0.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36mjavax.activation\x1b[0m\x1b[2m:\x1b[0m\x1b[1mactivation\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
     \x1b[36morg.apache.commons\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-compress\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.27.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36morg.apache.commons\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-csv\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.14.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36morg.apache.commons\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-lang3\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m3.17.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36morg.apache.kafka\x1b[0m\x1b[2m:\x1b[0m\x1b[1mkafka-clients\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m3.9.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36morg.apache.logging.log4j\x1b[0m\x1b[2m:\x1b[0m\x1b[1mlog4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.25.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36morg.codehaus.woodstox\x1b[0m\x1b[2m:\x1b[0m\x1b[1mstax2-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m4.2.2\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36morg.jctools\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjctools-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m4.0.5\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36morg.lz4\x1b[0m\x1b[2m:\x1b[0m\x1b[1mlz4-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.8.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
     \x1b[36morg.slf4j\x1b[0m\x1b[2m:\x1b[0m\x1b[1mslf4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.7.13\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36morg.xerial.snappy\x1b[0m\x1b[2m:\x1b[0m\x1b[1msnappy-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.1.10.5\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
     \x1b[36morg.yaml\x1b[0m\x1b[2m:\x1b[0m\x1b[1msnakeyaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.4\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36morg.zeromq\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjeromq\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m0.6.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)

-- List output | color=rich | wrap=smart --

There should be full ANSI color, with word wrapping.

  $ jgo --color=rich --wrap=smart --ignore-config --include-optional --full-coordinates list org.apache.logging.log4j:log4j-core:2.25.1
  \x1b[36morg.apache.logging.log4j\x1b[0m\x1b[2m:\x1b[0m\x1b[1mlog4j-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.25.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36mcom.conversantmedia\x1b[0m\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.2.15\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcom.fasterxml.jackson.core\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-annotations\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36mcom.fasterxml.jackson.core\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcom.fasterxml.jackson.core\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-databind\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcom.fasterxml.jackson.dataformat\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-xml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m  (esc)
  \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcom.fasterxml.jackson.dataformat\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjackson-dataformat-yaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m  (esc)
  \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcom.fasterxml.woodstox\x1b[0m\x1b[2m:\x1b[0m\x1b[1mwoodstox-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m7.1.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36mcom.github.luben\x1b[0m\x1b[2m:\x1b[0m\x1b[1mzstd-jni\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.5.7-4\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
     \x1b[36mcom.lmax\x1b[0m\x1b[2m:\x1b[0m\x1b[1mdisruptor\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m3.4.4\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcom.sun.mail\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjavax.mail\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.6.2\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36mcommons-codec\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-codec\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.18.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36mcommons-io\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-io\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.19.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36meu.neilalexander\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjnacl\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.0.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36mjavax.activation\x1b[0m\x1b[2m:\x1b[0m\x1b[1mactivation\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
     \x1b[36morg.apache.commons\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-compress\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.27.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36morg.apache.commons\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-csv\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.14.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36morg.apache.commons\x1b[0m\x1b[2m:\x1b[0m\x1b[1mcommons-lang3\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m3.17.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36morg.apache.kafka\x1b[0m\x1b[2m:\x1b[0m\x1b[1mkafka-clients\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m3.9.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36morg.apache.logging.log4j\x1b[0m\x1b[2m:\x1b[0m\x1b[1mlog4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.25.1\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36morg.codehaus.woodstox\x1b[0m\x1b[2m:\x1b[0m\x1b[1mstax2-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m4.2.2\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36morg.jctools\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjctools-core\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m4.0.5\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)
     \x1b[36morg.lz4\x1b[0m\x1b[2m:\x1b[0m\x1b[1mlz4-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.8.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
     \x1b[36morg.slf4j\x1b[0m\x1b[2m:\x1b[0m\x1b[1mslf4j-api\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.7.13\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36morg.xerial.snappy\x1b[0m\x1b[2m:\x1b[0m\x1b[1msnappy-java\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m1.1.10.5\x1b[0m\x1b[2m:\x1b[0m\x1b[34mruntime\x1b[0m (esc)
     \x1b[36morg.yaml\x1b[0m\x1b[2m:\x1b[0m\x1b[1msnakeyaml\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m2.4\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m (esc)
     \x1b[36morg.zeromq\x1b[0m\x1b[2m:\x1b[0m\x1b[1mjeromq\x1b[0m\x1b[2m:\x1b[0mjar\x1b[2m:\x1b[0m\x1b[92m0.6.0\x1b[0m\x1b[2m:\x1b[0m\x1b[34mcompile\x1b[0m \x1b[2m(optional)\x1b[0m (esc)

-- XML output | color=plain | wrap=raw --

The long <project> tag should be on one line.

  $ jgo --color=plain --wrap=raw info pom xalan:serializer:2.7.3
  <?xml version="1.0" ?>
  <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>xalan</groupId>
    <artifactId>serializer</artifactId>
    <version>2.7.3</version>
  </project>

-- XML output | color=plain | wrap=smart --

The long <project> tag should be word-wrapped along its attrs.

  $ jgo --color=plain --wrap=smart info pom xalan:serializer:2.7.3
  <?xml version="1.0" ?>
  <project xmlns="http://maven.apache.org/POM/4.0.0" 
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
  xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
  https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <groupId>xalan</groupId>
    <artifactId>serializer</artifactId>
    <version>2.7.3</version>
  </project>

-- XML output | color=styled | wrap=raw --

There should be ANSI styling but no color, and no extra line breaks.

  $ jgo --color=styled --wrap=raw info pom xalan:serializer:2.7.3
  \x1b[1m<\x1b[0m?xml version="1.0" ?> (esc)
  <project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd"> (esc)
    <modelVersion>\x1b[1m4.0\x1b[0m.\x1b[1m0\x1b[0m</modelVersion> (esc)
    <groupId>xalan</groupId> (esc)
    <artifactId>serializer</artifactId> (esc)
    <version>\x1b[1m2.7\x1b[0m.\x1b[1m3\x1b[0m</version> (esc)
  </project\x1b[1m>\x1b[0m (esc)

-- XML output | color=styled | wrap=smart --

There should be ANSI styling but no color, with word wrapping.

  $ jgo --color=styled --wrap=smart info pom xalan:serializer:2.7.3
  \x1b[1m<\x1b[0m?xml version="1.0" ?> (esc)
  <project xmlns="http://maven.apache.org/POM/4.0.0"  (esc)
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"  (esc)
  xsi:schemaLocation="http://maven.apache.org/POM/4.0.0  (esc)
  https://maven.apache.org/xsd/maven-4.0.0.xsd"> (esc)
    <modelVersion>\x1b[1m4.0\x1b[0m.\x1b[1m0\x1b[0m</modelVersion> (esc)
    <groupId>xalan</groupId> (esc)
    <artifactId>serializer</artifactId> (esc)
    <version>\x1b[1m2.7\x1b[0m.\x1b[1m3\x1b[0m</version> (esc)
  </project\x1b[1m>\x1b[0m (esc)

-- XML output | color=rich | wrap=raw --

There should be full ANSI color, but no extra line breaks.

  $ jgo --color=rich --wrap=raw info pom xalan:serializer:2.7.3
  \x1b[1m<\x1b[0m\x1b[39m?xml \x1b[0m\x1b[33mversion\x1b[0m\x1b[39m=\x1b[0m\x1b[32m"1\x1b[0m\x1b[32m.0"\x1b[0m\x1b[39m ?>\x1b[0m (esc)
  \x1b[39m<project \x1b[0m\x1b[33mxmlns\x1b[0m\x1b[39m=\x1b[0m\x1b[32m"http\x1b[0m\x1b[32m://maven.apache.org/POM/4.0.0"\x1b[0m\x1b[39m xmlns:\x1b[0m\x1b[33mxsi\x1b[0m\x1b[39m=\x1b[0m\x1b[32m"http\x1b[0m\x1b[32m://www.w3.org/2001/XMLSchema-instance"\x1b[0m\x1b[39m xsi:\x1b[0m\x1b[33mschemaLocation\x1b[0m\x1b[39m=\x1b[0m\x1b[32m"http\x1b[0m\x1b[32m://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd"\x1b[0m\x1b[39m>\x1b[0m (esc)
  \x1b[39m  <modelVersion>\x1b[0m\x1b[1;36m4.0\x1b[0m\x1b[39m.\x1b[0m\x1b[1;36m0\x1b[0m\x1b[39m<\x1b[0m\x1b[35m/\x1b[0m\x1b[95mmodelVersion\x1b[0m\x1b[39m>\x1b[0m (esc)
  \x1b[39m  <groupId>xalan<\x1b[0m\x1b[35m/\x1b[0m\x1b[95mgroupId\x1b[0m\x1b[39m>\x1b[0m (esc)
  \x1b[39m  <artifactId>serializer<\x1b[0m\x1b[35m/\x1b[0m\x1b[95martifactId\x1b[0m\x1b[39m>\x1b[0m (esc)
  \x1b[39m  <version>\x1b[0m\x1b[1;36m2.7\x1b[0m\x1b[39m.\x1b[0m\x1b[1;36m3\x1b[0m\x1b[39m<\x1b[0m\x1b[35m/\x1b[0m\x1b[95mversion\x1b[0m\x1b[39m>\x1b[0m (esc)
  \x1b[39m<\x1b[0m\x1b[35m/\x1b[0m\x1b[95mproject\x1b[0m\x1b[1m>\x1b[0m (esc)

-- XML output | color=rich | wrap=smart --

There should be full ANSI color, with word wrapping.

  $ jgo --color=rich --wrap=smart info pom xalan:serializer:2.7.3
  \x1b[1m<\x1b[0m\x1b[39m?xml \x1b[0m\x1b[33mversion\x1b[0m\x1b[39m=\x1b[0m\x1b[32m"1\x1b[0m\x1b[32m.0"\x1b[0m\x1b[39m ?>\x1b[0m (esc)
  \x1b[39m<project \x1b[0m\x1b[33mxmlns\x1b[0m\x1b[39m=\x1b[0m\x1b[32m"http\x1b[0m\x1b[32m://maven.apache.org/POM/4.0.0"\x1b[0m\x1b[39m \x1b[0m (esc)
  \x1b[39mxmlns:\x1b[0m\x1b[33mxsi\x1b[0m\x1b[39m=\x1b[0m\x1b[32m"http\x1b[0m\x1b[32m://www.w3.org/2001/XMLSchema-instance"\x1b[0m\x1b[39m \x1b[0m (esc)
  \x1b[39mxsi:\x1b[0m\x1b[33mschemaLocation\x1b[0m\x1b[39m=\x1b[0m\x1b[32m"http\x1b[0m\x1b[32m://maven.apache.org/POM/4.0.0 \x1b[0m (esc)
  \x1b[32mhttps://maven.apache.org/xsd/maven-4.0.0.xsd"\x1b[0m\x1b[39m>\x1b[0m (esc)
  \x1b[39m  <modelVersion>\x1b[0m\x1b[1;36m4.0\x1b[0m\x1b[39m.\x1b[0m\x1b[1;36m0\x1b[0m\x1b[39m<\x1b[0m\x1b[35m/\x1b[0m\x1b[95mmodelVersion\x1b[0m\x1b[39m>\x1b[0m (esc)
  \x1b[39m  <groupId>xalan<\x1b[0m\x1b[35m/\x1b[0m\x1b[95mgroupId\x1b[0m\x1b[39m>\x1b[0m (esc)
  \x1b[39m  <artifactId>serializer<\x1b[0m\x1b[35m/\x1b[0m\x1b[95martifactId\x1b[0m\x1b[39m>\x1b[0m (esc)
  \x1b[39m  <version>\x1b[0m\x1b[1;36m2.7\x1b[0m\x1b[39m.\x1b[0m\x1b[1;36m3\x1b[0m\x1b[39m<\x1b[0m\x1b[35m/\x1b[0m\x1b[95mversion\x1b[0m\x1b[39m>\x1b[0m (esc)
  \x1b[39m<\x1b[0m\x1b[35m/\x1b[0m\x1b[95mproject\x1b[0m\x1b[1m>\x1b[0m (esc)

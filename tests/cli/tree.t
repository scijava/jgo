Tests jgo tree command.

Test tree requires endpoint or jgo.toml.

  $ jgo tree
  ERROR    No endpoint specified                                                  
  [1]

Test tree --help shows usage.

  $ jgo tree --help
                                                                                  
   Usage: jgo tree [OPTIONS] [ENDPOINT]                                           
                                                                                  
   Show dependency tree.                                                          
                                                                                  
  ╭─ Arguments ──────────────────────────────────────────────────────────────────╮
  │ ENDPOINT  TEXT  Maven coordinates (single or combined with +) optionally     │
  │                 followed by @MainClass                                       │
  ╰──────────────────────────────────────────────────────────────────────────────╯
  ╭─ Options ────────────────────────────────────────────────────────────────────╮
  │ --help  Show this message and exit.                                          │
  ╰──────────────────────────────────────────────────────────────────────────────╯

Test tree with endpoint.

  $ jgo tree org.jruby:jruby:10.0.2.0
  
  └── org.jruby:jruby:10.0.2.0
      ├── org.jruby:jruby-base:10.0.2.0
      │   ├── org.ow2.asm:asm:9.7.1
      │   ├── org.ow2.asm:asm-commons:9.7.1
      │   │   └── org.ow2.asm:asm-tree:9.7.1
      │   ├── org.ow2.asm:asm-util:9.7.1
      │   │   └── org.ow2.asm:asm-analysis:9.7.1
      │   ├── com.github.jnr:jnr-netdb:1.2.0
      │   ├── com.github.jnr:jnr-enxio:0.32.18
      │   ├── com.github.jnr:jnr-unixsocket:0.38.23
      │   ├── com.github.jnr:jnr-posix:3.1.20
      │   ├── com.github.jnr:jnr-constants:0.10.4
      │   ├── com.github.jnr:jnr-ffi:2.2.17
      │   │   ├── com.github.jnr:jnr-a64asm:1.0.0
      │   │   └── com.github.jnr:jnr-x86asm:1.0.2
      │   ├── com.github.jnr:jffi:1.3.13
      │   ├── com.github.jnr:jffi:native:1.3.13
      │   ├── org.jruby.joni:joni:2.2.6
      │   ├── org.jruby.jcodings:jcodings:1.0.63
      │   ├── org.jruby:dirgra:0.5
      │   ├── com.headius:invokebinder:1.14
      │   ├── com.headius:options:1.6
      │   ├── org.jruby:jzlib:1.1.5
      │   ├── joda-time:joda-time:2.14.0
      │   ├── me.qmx.jitescript:jitescript:0.4.1
      │   ├── com.headius:backport9:1.13
      │   └── org.crac:crac:1.5.0
      └── org.jruby:jruby-stdlib:10.0.2.0


Test tree with --dry-run.

  $ jgo --dry-run tree org.jruby:jruby:10.0.2.0
  
  └── org.jruby:jruby:10.0.2.0
      ├── org.jruby:jruby-base:10.0.2.0
      │   ├── org.ow2.asm:asm:9.7.1
      │   ├── org.ow2.asm:asm-commons:9.7.1
      │   │   └── org.ow2.asm:asm-tree:9.7.1
      │   ├── org.ow2.asm:asm-util:9.7.1
      │   │   └── org.ow2.asm:asm-analysis:9.7.1
      │   ├── com.github.jnr:jnr-netdb:1.2.0
      │   ├── com.github.jnr:jnr-enxio:0.32.18
      │   ├── com.github.jnr:jnr-unixsocket:0.38.23
      │   ├── com.github.jnr:jnr-posix:3.1.20
      │   ├── com.github.jnr:jnr-constants:0.10.4
      │   ├── com.github.jnr:jnr-ffi:2.2.17
      │   │   ├── com.github.jnr:jnr-a64asm:1.0.0
      │   │   └── com.github.jnr:jnr-x86asm:1.0.2
      │   ├── com.github.jnr:jffi:1.3.13
      │   ├── com.github.jnr:jffi:native:1.3.13
      │   ├── org.jruby.joni:joni:2.2.6
      │   ├── org.jruby.jcodings:jcodings:1.0.63
      │   ├── org.jruby:dirgra:0.5
      │   ├── com.headius:invokebinder:1.14
      │   ├── com.headius:options:1.6
      │   ├── org.jruby:jzlib:1.1.5
      │   ├── joda-time:joda-time:2.14.0
      │   ├── me.qmx.jitescript:jitescript:0.4.1
      │   ├── com.headius:backport9:1.13
      │   └── org.crac:crac:1.5.0
      └── org.jruby:jruby-stdlib:10.0.2.0


Test tree with --offline (uses cache).

  $ jgo --offline tree org.jruby:jruby:10.0.2.0
  
  └── org.jruby:jruby:10.0.2.0
      ├── org.jruby:jruby-base:10.0.2.0
      │   ├── org.ow2.asm:asm:9.7.1
      │   ├── org.ow2.asm:asm-commons:9.7.1
      │   │   └── org.ow2.asm:asm-tree:9.7.1
      │   ├── org.ow2.asm:asm-util:9.7.1
      │   │   └── org.ow2.asm:asm-analysis:9.7.1
      │   ├── com.github.jnr:jnr-netdb:1.2.0
      │   ├── com.github.jnr:jnr-enxio:0.32.18
      │   ├── com.github.jnr:jnr-unixsocket:0.38.23
      │   ├── com.github.jnr:jnr-posix:3.1.20
      │   ├── com.github.jnr:jnr-constants:0.10.4
      │   ├── com.github.jnr:jnr-ffi:2.2.17
      │   │   ├── com.github.jnr:jnr-a64asm:1.0.0
      │   │   └── com.github.jnr:jnr-x86asm:1.0.2
      │   ├── com.github.jnr:jffi:1.3.13
      │   ├── com.github.jnr:jffi:native:1.3.13
      │   ├── org.jruby.joni:joni:2.2.6
      │   ├── org.jruby.jcodings:jcodings:1.0.63
      │   ├── org.jruby:dirgra:0.5
      │   ├── com.headius:invokebinder:1.14
      │   ├── com.headius:options:1.6
      │   ├── org.jruby:jzlib:1.1.5
      │   ├── joda-time:joda-time:2.14.0
      │   ├── me.qmx.jitescript:jitescript:0.4.1
      │   ├── com.headius:backport9:1.13
      │   └── org.crac:crac:1.5.0
      └── org.jruby:jruby-stdlib:10.0.2.0


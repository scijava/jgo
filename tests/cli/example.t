Tests the example jgo.toml configuration patterns.

Validates that GC shorthands and dotted property names are handled correctly,
mirroring the patterns used in the examples/ directory.

GC shorthand (e.g., gc = "G1") must be normalized to -XX:+UseG1GC.
Dotted property names (e.g., app.name = "foo" under [java.properties]) must
be flattened to -Dapp.name=foo, not passed as -Dapp={'name': 'foo'}.

  $ mkdir -p "$TMPDIR/jgo-example-test" && cd "$TMPDIR/jgo-example-test"
  $ cat > jgo.toml << 'EOF'
  > [environment]
  > name = "test-app"
  > [java]
  > gc = "G1"
  > max_heap = "2G"
  > [java.properties]
  > app.name = "test-app"
  > log.level = "INFO"
  > [dependencies]
  > coordinates = ["org.python:jython-standalone:2.7.4"]
  > [entrypoints]
  > default = "jython"
  > jython = "org.python.util.jython"
  > EOF
  $ jgo --dry-run run
  */bin/java -XX:+UseG1GC -Xmx2G -Dapp.name=test-app -Dlog.level=INFO -cp */jars/\*:*/modules/\* org.python.util.jython (glob)
  $ cd "$TMPDIR" && rm -rf jgo-example-test

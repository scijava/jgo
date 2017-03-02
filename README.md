## Summary

I got really, really fed up with the fact that there is no easy package manager
for Java. We have Maven, which is amazing, but no easy way to actually __launch
code__ from the beautifully managed dependencies stored so lovingly into
`~/.m2/repository`.

So now I have jrun. A lovely tool, just for me! And maybe you too.

## Usage example

```
jrun org.scijava:scijava-common:org.scijava.script.ScriptREPL
```

## Alternatives

There is [JPM4J](http://jpm4j.org/), but it did not work too well for me:

* It wants to maintain its _own_ local repository of JARs outside of Maven—why?
  Everyone should use Maven repositories, a thoroughly established standard.

* For each artifact, you have to choose a single main class as its sole command
  which gets linked into a shell command that runs it.

* It does not seem well-synced with Maven Central, and/or does not
  seem to deal with dependencies in the expected way; e.g.:

    ```
    $ jpm install -l -f -m org.scijava.script.ScriptREPL org.scijava:scijava-common
    Errors
      0. Target specifies Class-Path in JAR but the indicated file .../repo/scijava-expression-parser-3.0.0.jar is not found
      1. Target specifies Class-Path in JAR but the indicated file .../repo/gentyref-1.1.0.jar is not found
      2. Target specifies Class-Path in JAR but the indicated file .../repo/eventbus-1.4.jar is not found
    ```

* The source is, oddly, in part of [bnd](https://github.com/bndtools/bnd)
  rather than in the [jpm4j organization](https://github.com/jpm4j) anywhere,
  which is not a good sign, modularity-wise.

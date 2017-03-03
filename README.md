# jrun: painless Java component execution

## Summary

I got really fed up with the fact that there is no easy package manager
for Java. We have Maven, which is amazing, but no easy way to actually
__launch code__ from the beautifully managed dependencies stored so
lovingly into `~/.m2/repository`.

So now I have jrun. A lovely tool, just for me! And maybe you too.

## Installation

Just clone this repo, and symlink `jrun` into your favorite `bin` directory.

The script uses some common utilities (e.g., `cat`) as well as `mvn` and `java`
for the heavy lifting. If you are missing anything, the script will tell you.

## Usage

```
Usage: jrun [-v] <jvm-args> <endpoint> <main-args>

  -v          : verbose mode flag
  <jvm-args>  : any list of arguments to the JVM
  <endpoint>  : the artifact and main class to execute
  <main-args> : any list of arguments to the main class

The endpoint should have one of the following formats:

- groupId:artifactId
- groupId:artifactId:version
- groupId:artifactId:mainClass
- groupId:artifactId:version:mainClass
- groupId:artifactId:version:classifier:mainClass

If version is omitted, then RELEASE is used.
If mainClass is omitted, it is auto-detected.
You can also write part of a class beginning with an @ sign,
and it will be auto-completed.
```

### Examples

| Tool         | Command                                                                |
|:------------:|:----------------------------------------------------------------------:|
| Jython REPL  | `jrun org.python:jython-standalone`                                    |
| JRuby eval   | `echo "puts 'Hello Ruby'" | jrun org.jruby:jruby-complete:@jruby.Main` |
| SciJava REPL | `jrun org.scijava:scijava-common:@ScriptREPL`                          |

Note that for the SciJava REPL, there are no `scripting-<foo>` language plugins
on the classpath in this case; see "Configuration" below for a solution.

### Configuration

In the file `$HOME/.jrunrc`, you can define shortcuts and repositories; e.g.:
```ini
[shortcuts]
repl = imagej:org.scijava.script.ScriptREPL
imagej = net.imagej:imagej

[repositories]
imagej.public = https://maven.imagej.net/content/groups/public
```

Shortcuts are substituted verbatim from the beginning of the endpoint,
single-pass in the order they are defined. So e.g. now you can run:
```
jrun repl
```
Note that in the example above, the main class
(`org.scijava.script.ScriptREPL`) comes from a _different_ artifact than the
toplevel artifact (`net.imagej:imagej`). This is intentional, so that the
various SciJava `scripting-<foo>` artifacts are included in the classpath of
the REPL.

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

* The source is, oddly, part of [bnd](https://github.com/bndtools/bnd)
  rather than in the [jpm4j organization](https://github.com/jpm4j) anywhere,
  which is not a good sign, modularity-wise.

## FAQ

__Q:__
Why is startup so slow?

__A:__
The Maven bootstrapper needs to download JARs from the Internet into
`~/.m2/repository`. Then the script copies the JARs into a temporary directory.
Then the main class inference and autocompletion logic scans them.
In the future, we could cache this work so that subsequent invocations with the
same endpoint are speedy.

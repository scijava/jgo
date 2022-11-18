[![build status](https://github.com/scijava/jgo/actions/workflows/build.yml/badge.svg)](https://github.com/scijava/jgo/actions/workflows/build.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# jgo: painless Java component execution

![](https://raw.githubusercontent.com/scijava/jgo/main/jgo.png)

## Summary

[Maven](https://maven.apache.org/) is a great tool. It manages dependencies so
that Java projects become reusable "building blocks" in a robust way, like
`pip` for Python, `npm` for JavaScript, `gem` for Ruby, `cpan` for Perl, etc.
And the [Maven Central repository](https://search.maven.org/) contains a
tremendous wealth of code, ripe for reuse in your own projects.

Unfortunately, Maven provides no easy way to actually __launch code__ from the
beautifully managed dependencies stored so lovingly into `~/.m2/repository`.

This project fills that gap: `jgo` launches Java code. You do not need to
download or install any JARs; you just specify an "endpoint" consisting of a
[Maven artifact](https://stackoverflow.com/a/2487511/1207769) identifier, plus
a main class if needed/desired, and `jgo` uses Maven to obtain and run it.

To do this, `jgo` builds the local environment on demand, caching it into a
subfolder of `~/.jgo`, so that the endpoint's particular dependencies are
available in one place.

## Installation

The `jgo` project began life as a shell script, but was later translated into
Python, so that tools such as [scyjava](https://github.com/scijava/scyjava)
could leverage its environment-building capabilities.

As such, there are now two implementations from which to choose!
Each has pros and cons.

### Prerequisites

`jgo` uses `mvn` and `java` for the heavy lifting.
The shell script version needs some common utilities (e.g., `cat`).
If you are missing anything, the script will tell you.

### The shell script

The `jgo.sh` shell script requires a POSIX-friendly system. It is known to
work on Linux, macOS, [Cygwin](https://www.cygwin.com/), Microsoft's
[Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install),
and Git BASH from the [Git for Windows](https://git-for-windows.github.io/) project.

<details><summary><strong>Installing the shell script</strong></summary>

Just clone this repo and symlink `jgo.sh` into your favorite `bin` directory.

For example, assuming `~/bin` is on your PATH:

```shell
cd
git clone https://github.com/scijava/jgo
cd bin
ln -s ../jgo/jgo.sh jgo
jgo --help
```

</details>

### The Python module

The Python version of `jgo` offers a `jgo` console script, as
well as a `jgo` module for programmatically creating endpoints.

<details><summary><strong>Installing with pip</strong></summary>

```shell
pip install jgo
```

</details>
<details><summary><strong>Installing with conda</strong></summary>

```shell
conda install -c conda-forge jgo
```

</details>
<details><summary><strong>Installing from source</strong></summary>

```shell
git clone https://github.com/scijava/jgo
cd jgo

# install globally (not recommended unless using a virtual environment)
pip install .

# install into ~/.local (see pip install --help for details)
pip install --user .

# install into $PREFIX
pip install --prefix=$PREFIX .

# install globally in developer mode (hot linked to working copy folder)
pip install -e .
```

</details>

## Usage

```
Usage: jgo [-v] [-u] [-U] [-m] <jvm-args> <endpoint> <main-args>

  -v          : verbose mode flag
  -u          : update/regenerate cached environment
  -U          : force update from remote Maven repositories (implies -u)
  -m          : use endpoints for dependency management (see "Pitfalls" below)
  <jvm-args>  : any list of arguments to the JVM
  <endpoint>  : the artifact(s) + main class to execute
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

Multiple artifacts can be concatenated with pluses,
and all of them will be included on the classpath.
However, you should not specify multiple main classes.
```

### Examples

| Program                      | Command                                                                             |
|-----------------------------:|:------------------------------------------------------------------------------------|
| Jython REPL                  | `jgo org.python:jython-standalone`                                                  |
| JRuby eval                   | `echo "puts 'Hello Ruby'" \| jgo org.jruby:jruby-complete:@jruby.Main`              |
| Groovy REPL                  | `jgo org.codehaus.groovy:groovy-groovysh:@shell.Main+commons-cli:commons-cli:1.3.1` |

Note the usage of the `+` syntax as needed to append elements to the classpath.

If you add
`scijava.public = https://maven.scijava.org/content/groups/public`
to the
`[repositories]` section of your `.jgorc`
(see [Repositories](#repositories) below),
you can also try:

| Program                      | Command                                                                             |
|-----------------------------:|:------------------------------------------------------------------------------------|
| SciJava REPL with JRuby      | `jgo org.scijava:scijava-common:@ScriptREPL+org.scijava:scripting-jruby`            |
| SciJava REPL with Jython     | `jgo org.scijava:scijava-common:@ScriptREPL+org.scijava:scripting-jython`           |
| SciJava REPL with Groovy     | `jgo org.scijava:scijava-common:@ScriptREPL+org.scijava:scripting-groovy`           |
| SciJava REPL with Clojure    | `jgo org.scijava:scijava-common:@ScriptREPL+org.scijava:scripting-clojure`          |
| SciJava REPL with JavaScript | `jgo org.scijava:scijava-common:@ScriptREPL+org.scijava:scripting-javascript`       |

### FAQ

* __Is it fast?__
  Endpoints are synthesized in a local cache under `~/.jgo`.
  So invoking the same endpoint a second time is really quick.
* __What does "no installation" mean?__
  Classpath elements are [hard-linked](https://en.wikipedia.org/wiki/Hard_link)
  into `~/.jgo` from `~/.m2/repository` rather than copied, so the `~/.jgo`
  folder has a tiny footprint even if you execute lots of different endpoints.
* __What if an endpoint has a new version?__
  Pass the `-U` flag to `jgo` to rebuild the endpoint.
  Note that unlike `mvn`, though, `jgo` does not check for updates otherwise.

### Configuration

You can configure the behavior of `jgo` using the `~/.jgorc` file.

#### Repositories

You can define additional remote Maven repositories,
from which artifacts will be retrieved. E.g.:

```ini
[repositories]
scijava.public = https://maven.scijava.org/content/groups/public
```

If you need more control over where artifacts come from—for example, if you
want to use your own remote Maven repository as a mirror of Maven Central—you
can do it using Maven's usual `~/.m2/settings.xml`; see [Using Mirrors for
Repositories](https://maven.apache.org/guides/mini/guide-mirror-settings.html).

You can also use the `-r` flag to pass additional repositories to individual
invocations of jgo.

#### Shortcuts

You can define shortcuts for launching commonly used programs:

```ini
[shortcuts]
repl = imagej:org.scijava.script.ScriptREPL
imagej = net.imagej:imagej
fiji = sc.fiji:fiji:LATEST
scifio = io.scif:scifio-cli
```

Shortcuts are substituted verbatim from the beginning of the endpoint,
single-pass in the order they are defined. So e.g. now you can run:
```shell
jgo repl
```
Note that with the `repl` shortcut above, the main class
(`org.scijava.script.ScriptREPL`) comes from a _different_ artifact than
the toplevel artifact (`net.imagej:imagej`). This is intentional, so that
all of [ImageJ](https://imagej.net/), including all of the various SciJava
`scripting-<foo>` plugins, is included in the classpath of the REPL.

#### Settings

There are a few configurable settings:

```ini
[settings]
m2Repo = /path/to/.m2Repo (default ~/.m2/repository)
cacheDir = /path/to/.jgo (default ~/.jgo)
links = soft (options: hard, soft, none; default hard)
```
Note that the `jgo` cache dir can also be set via the `JGO_CACHE_DIR` environment
variable when using **Python** `jgo`. The precedence of reading the cache dir, from
highest to lowest:
  - `JGO_CACHE_DIR` environment variable
  - `cacheDir` in `settings` sections in `~/.jgorc`
  - default to `~/.jgo`

### Pitfalls

#### Dependency management

Maven has a feature whereby a project can override the versions of transitive
(a.k.a. inherited) dependencies, via a `<dependencyManagement>` configuration.
The problem is: a library may then believe it depends on components at
particular versions as defined by its `<dependencyManagement>`, but downstream
projects which depend on that library will resolve to different versions.
See [this SO thread](https://stackoverflow.com/q/45041888/1207769) and
[this gist](https://gist.github.com/ctrueden/d058330c8a3687317806ce8cc18332c3)
for full details.

To work around this issue, you can pass `-m` to jgo, which
causes it to add all endpoints to the synthesized POM's
`<dependencyManagement>` section using
[import scope](https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html#Importing_Dependencies).
By doing this, the versions of transitive dependencies used in the synthesized
project should more precisely match those of each endpoint itself—although in
the case of multiple endpoints concatenated via the `+` operator with
conflicting dependency management, the earlier endpoints will win because they
will be declared earlier in the POM. See also
[issue #9](https://github.com/scijava/jgo/issues/9) in the jgo issue tracker.

## Development

### Code style

`jgo` uses [`black`](https://github.com/psf/black) for its code style.

After `pip install tox`, you can lint the code with:

```shell
tox -e lint
```

## Alternatives

* [JBang](https://github.com/jbangdev/jbang)
* [mvnx](https://github.com/mvnx/mvnx)
* [JPM4J](https://github.com/jpm4j) (discontinued)
* [Mop](https://github.com/chirino/mop) (unmaintained)
* [marun](https://github.com/nishemon/marun) (unmaintained, Python 2 only)

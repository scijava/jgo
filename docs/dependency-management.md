# Dependency Management

## How jgo handles dependency versions

Maven has a feature whereby a project can override the versions of transitive (inherited) dependencies via a `<dependencyManagement>` configuration. The problem is: a library may believe it depends on components at particular versions as defined by its `<dependencyManagement>`, but downstream projects which depend on that library will resolve to **different versions**. This means the library's actual dependencies differ from what it was built against.

See [this Stack Overflow thread](https://stackoverflow.com/q/45041888/1207769) and [this gist](https://gist.github.com/ctrueden/d058330c8a3687317806ce8cc18332c3) for full details.

**By default, jgo works around this Maven limitation** by adding all endpoints to the synthesized POM's `<dependencyManagement>` section using [import scope](https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html#Importing_Dependencies). This ensures that the versions of transitive dependencies match those that each endpoint was actually built with.

When multiple endpoints are concatenated via `+` with conflicting dependency management, earlier endpoints win because they are declared first in the POM.

### Disabling managed mode per coordinate

If a specific coordinate should *not* have its BOM imported into `<dependencyManagement>`, append `!` to the coordinate:

```bash
# Resolve scijava-common without importing its dependency management
jgo org.scijava:scijava-common!

# Mix managed and raw in the same endpoint
jgo org.scijava:scijava-common+org.scijava:scripting-jython!
```

:::{tip}
The `!` suffix is rarely needed. It is useful when you want raw Maven transitive resolution for a particular artifact -- for example, to debug version conflicts or to intentionally allow Maven's default "nearest wins" strategy for that coordinate.
:::

See also [issue #9](https://github.com/apposed/jgo/issues/9) for more discussion.

## Version resolution

### How `RELEASE` and `LATEST` work

When you omit a version (or explicitly write `RELEASE`), jgo resolves it to the newest release across all configured repositories by comparing version numbers directly. This differs from Maven, which picks the release from whichever repository was *most recently updated* -- a heuristic that can return an older version when artifacts are split across multiple repositories.

For example, if `net.imagej:ij` version `1.54p` is on Maven Central and version `1.48q` is on maven.scijava.org, Maven might resolve `RELEASE` to `1.48q` (because maven.scijava.org was updated more recently), while jgo correctly resolves to `1.54p` (the highest version number).

`LATEST` works the same way but includes SNAPSHOT versions. It returns the highest version by Maven version ordering across all repositories, rather than the most recently deployed build.

### Checking resolved versions

```bash
# Show all versions with markers indicating which is RELEASE and LATEST
jgo info versions org.python:jython-standalone
```

## Resolver options

jgo includes two dependency resolvers:

**Pure Python resolver** (`--resolver python`)
: Resolves dependencies without a Maven installation. Parses POM files directly, handles transitive dependencies, property interpolation, dependency management (BOMs), exclusions, and scopes.

**Maven resolver** (`--resolver mvn`)
: Shells out to the system `mvn` command. Handles all Maven features including plugins and complex profiles.

**Auto resolver** (`--resolver auto`, the default)
: Tries the pure Python resolver first, falling back to the Maven resolver if needed.

```bash
# Force pure Python resolver
jgo --resolver python org.python:jython-standalone

# Force Maven resolver
jgo --resolver mvn org.python:jython-standalone
```

### Known Maven resolver bug: runtime scope promoted to compile

Maven's dependency resolver has a known bug where `runtime`-scoped dependencies are reported as `compile` scope in certain scenarios. This can be observed with `jython-slim`:

```bash
# Python resolver — correctly shows antlr-runtime as runtime scope
jgo tree org.python:jython-slim:2.7.4

# Maven resolver — incorrectly shows antlr-runtime as compile scope
jgo --resolver mvn tree org.python:jython-slim:2.7.4
```

The `jython-slim-2.7.4.pom` explicitly declares:

```xml
<dependency>
  <groupId>org.antlr</groupId>
  <artifactId>antlr-runtime</artifactId>
  <version>3.5.3</version>
  <scope>runtime</scope>
</dependency>
```

Despite this, Maven's `dependency:tree` and `dependency:list` output promotes `antlr-runtime` to `compile` scope, whereas the pure Python resolver reports the correct scope.

## Link strategies

When building an environment, jgo links JARs from the Maven local repository (`~/.m2/repository`) into the environment directory. The link strategy controls how:

| Strategy | Disk overhead | Cross-filesystem | Notes |
|:---------|:--------------|:-----------------|:------|
| `hard` | None | No | Default. Fastest, zero disk overhead. |
| `soft` | None | Yes | Symbolic links. |
| `copy` | Full | Yes | Copies files. Works everywhere. |
| `auto` | None | Yes | Tries hard, then soft, then copy. |

Configure via settings file, CLI flag, or `jgo.toml`:

```bash
jgo --links soft org.python:jython-standalone
```

```ini
# ~/.config/jgo.conf
[settings]
links = soft
```

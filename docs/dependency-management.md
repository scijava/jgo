# Dependency Management

## How jgo handles dependency versions

Maven has a feature whereby a project can override the versions of transitive (inherited) dependencies via a `<dependencyManagement>` configuration. The problem is: a library may believe it depends on components at particular versions as defined by its `<dependencyManagement>`, but downstream projects which depend on that library will resolve to **different versions**. This means the library's actual dependencies differ from what it was built against.

See [this Stack Overflow thread](https://stackoverflow.com/q/45041888/1207769) and [this gist](https://gist.github.com/ctrueden/d058330c8a3687317806ce8cc18332c3) for full details.

**By default, jgo works around this Maven limitation** by adding all endpoints to the synthesized POM's `<dependencyManagement>` section using [import scope](https://maven.apache.org/guides/introduction/introduction-to-dependency-mechanism.html#Importing_Dependencies). This ensures that the versions of transitive dependencies match those that each endpoint was actually built with.

When multiple endpoints are concatenated via `+` with conflicting dependency management, earlier endpoints win because they are declared first in the POM.

### Disabling managed mode

If you need raw Maven transitive dependency resolution without the dependencyManagement workaround (rare), use `--no-managed`:

```bash
jgo --no-managed org.scijava:scijava-common
```

The `-m`/`--managed` flags still work for backward compatibility, but managed mode is now the default.

See also [issue #9](https://github.com/apposed/jgo/issues/9) for more discussion.

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

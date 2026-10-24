# Packaging, Types, and Classifiers

Maven uses three related but distinct concepts to say which file of a component
you want. They often share the same values (`jar`, `pom`), which makes them easy
to conflate, but they are not interchangeable.

## Three concepts

**Component packaging**
: The `<packaging>` declared once in a project's POM, defaulting to `jar`. It is a
  fact about the *component*: it selects the build lifecycle and declares what the
  component's primary artifact is, or that there is none. For example, a
  `<packaging>pom</packaging>` component (such as a parent POM or BOM) publishes
  only a `.pom` file. Common values: `jar`, `pom`, `bundle`, `maven-plugin`, `war`.

**Dependency packaging type**
: The `<type>` declared on a *dependency reference*, defaulting to `jar`. It
  selects which artifact of the target component to resolve. Different references
  to the same component can ask for different types, e.g. `jar` for the main code
  and `test-jar` for its test classes.

**Extension and classifier**
: What actually names the file in the repository: `foo-1.0.jar`,
  `foo-1.0-tests.jar`, `foo-1.0.pom`. The classifier distinguishes several files
  of the same component with the same extension, such as `sources`, `javadoc`,
  or `natives-linux`.

## From type to file

Maven maps each packaging type to a file extension and an implied classifier.
jgo uses the same standard mapping:

| Packaging type | Extension | Implied classifier |
| -------------- | --------- | ------------------ |
| `jar`          | `jar`     | —                  |
| `pom`          | `pom`     | —                  |
| `war`          | `war`     | —                  |
| `ear`          | `ear`     | —                  |
| `rar`          | `rar`     | —                  |
| `maven-plugin` | `jar`     | —                  |
| `bundle`       | `jar`     | —                  |
| `ejb`          | `jar`     | —                  |
| `ejb-client`   | `jar`     | `client`           |
| `test-jar`     | `jar`     | `tests`            |
| `java-source`  | `jar`     | `sources`          |
| `javadoc`      | `jar`     | `javadoc`          |

So the type is not always the extension: a `maven-plugin` or `bundle` is a plain
`.jar`, and a `test-jar` is the `-tests.jar` file. A type not in this table, such
as `zip`, is used directly as the extension, with no implied classifier.

An explicit classifier takes precedence over the implied one.

## Types in coordinates

The packaging position in a coordinate (`groupId:artifactId:packaging:version`, or
`groupId:artifactId:packaging:classifier:version`) holds the packaging type:

```bash
jgo info path org.apache.commons:commons-lang3:test-jar:3.12.0
# .../commons-lang3-3.12.0-tests.jar

jgo info path org.scijava:script-editor:jar:sources:1.4.0
# .../script-editor-1.4.0-sources.jar
```

## In the Python API

```python
from jgo.maven import MavenContext, artifact_handler

component = MavenContext().project("org.apache.commons", "commons-lang3").at_version("3.12.0")

component.packaging        # "jar": the <packaging> declared in the POM

artifact = component.artifact(type="test-jar")
artifact.type              # "test-jar"
artifact.extension         # "jar"
artifact.effective_classifier  # "tests"
artifact.filename          # "commons-lang3-3.12.0-tests.jar"

artifact_handler("maven-plugin")  # ("jar", "")
```

`Component.packaging` resolves the component's POM on first access (downloading
it if needed). Like Maven, it is not inherited from a parent POM.

## A note on naming

For historical reasons, two places use the name `packaging` for what is really the
packaging type:

- `Coordinate.packaging` in `jgo.parse`.
- The `packaging` key of each dependency in `jgo.lock.toml`.

By contrast, the `p:` filter of `jgo search` really does match each component's
declared `<packaging>`.

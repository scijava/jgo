# Recipes

Common patterns and use cases for jgo.

## Running language REPLs

```bash
# Jython (Python on JVM)
jgo org.python:jython-standalone

# JRuby
echo "puts 'Hello'" | jgo org.jruby:jruby-complete@jruby.Main

# Groovy shell
jgo org.codehaus.groovy:groovy-groovysh+commons-cli:commons-cli:1.3.1@shell.Main
```

## Custom JVM options

```bash
# Increase heap size
jgo org.example:myapp -Xmx8G --

# Combine JVM args and app args
jgo org.example:myapp -Xmx8G -ea -- --app-flag value

# Use global heap flags
jgo --max-heap 8G --gc Z org.example:myapp
```

## Building a classpath for your IDE

```bash
# Classpath as a single string
jgo info classpath org.python:jython-standalone

# Module path
jgo info modulepath org.scijava:scijava-ops-image

# All JARs
jgo info jars org.scijava:scijava-common
```

## Combining multiple artifacts

Use `+` to build a classpath from multiple Maven artifacts:

```bash
# SciJava Script Editor with Jython scripting
jgo org.scijava:scijava-editor+org.scijava:scripting-jython

# Specify a main class from any artifact
jgo org.scijava:scijava-common+org.scijava:scripting-jython@ScriptREPL
```

## Working with SNAPSHOT versions

```bash
# Force update to get latest SNAPSHOT
jgo -u org.example:mylib:1.0-SNAPSHOT
```

## CI/CD usage

```bash
# Work offline with pre-populated cache
jgo --offline --cache-dir /build/cache org.example:myapp

# Print classpath for build scripts
CP=$(jgo info classpath org.example:mylib | tr '\n' ':')
javac -cp "$CP" MyClass.java
```

## Reproducible project environments

```bash
# Initialize a project
jgo init net.imagej:imagej:2.15.0

# Add dependencies
jgo add org.scijava:scripting-jython

# Commit and push spec and lock file
git add jgo.toml jgo.lock.toml
echo ".jgo/" >> .gitignore
git commit -m 'Add jgo environment'
git push

# Collaborator clones and runs
git clone ...
cd project-dir
jgo run  # Rebuilds environment from lock file and runs
```

## Searching for artifacts

```bash
# Plain text search
jgo search apache commons

# Search with field syntax:
jgo search g:org.scijava a:scripting-java

# Coordinate search with detailed output
jgo search --detailed org.python:jython-standalone
```

## Using jgo as a library

### Running ImageJ macro in a subprocess from Python

```python
import jgo

jgo.run(
    "net.imagej:imagej:2.17.0",
    app_args=["--headless", "-macro", "macro.ijm"],
    repositories={"scijava": "https://maven.scijava.org/content/groups/public"},
)
```

### Getting a classpath for subprocess calls

```python
import jgo
import subprocess

env = jgo.build("org.python:jython-standalone:2.7.3")
classpath = ":".join(str(p) for p in env.classpath)

subprocess.run(["java", "-cp", classpath, "org.python.util.jython", "script.py"])
```

### Dependency analysis

```python
from jgo.maven import MavenContext

maven = MavenContext()
component = maven.project("org.scijava", "scijava-common").at_version("2.96.0")
model = component.model()
deps, root = model.dependencies()

for dep in deps:
    print(f"{dep.groupId}:{dep.artifactId}:{dep.version} [{dep.scope}]")
```

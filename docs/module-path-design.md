# JPMS Module-Path Support for jgo

## Overview

This document describes the design for adding Java Platform Module System (JPMS) module-path support to jgo. The goal is to enable jgo to intelligently route modular JARs to `--module-path` and non-modular JARs to `-cp`, while providing explicit control when needed.

## Background

### The Java Platform Module System (JPMS)

Introduced in Java 9, JPMS provides:
- Strong encapsulation of internal APIs
- Explicit dependency declarations between modules
- Reliable configuration (no classpath hell)

A modular JAR contains a `module-info.class` file at its root that declares:
- The module name
- Required dependencies (`requires`)
- Exported packages (`exports`)
- Services provided and consumed

### Automatic Modules

JARs without `module-info.class` can still be placed on the module-path as "automatic modules". Their module name is derived from:
1. The `Automatic-Module-Name` manifest header (if present)
2. The JAR filename (as a fallback)

### Current jgo Behavior

Currently, jgo places all resolved JARs on the classpath using `-cp`:

```bash
java [JVM_ARGS] -cp /path/to/jar1.jar:/path/to/jar2.jar MainClass [APP_ARGS]
```

This works but doesn't leverage JPMS for modular applications.

## Requirements

### R1: Auto-Detection of Modular JARs

jgo should automatically detect whether each JAR is modular by checking for `module-info.class`. Modular JARs go on `--module-path`; non-modular JARs go on `-cp`.

### R2: Coordinate Syntax for Explicit Control

Users can override auto-detection per-coordinate using suffixes:
- `org.example:artifact:1.0` → auto-detect (default)
- `org.example:artifact:1.0(c)` or `(cp)` → force class-path
- `org.example:artifact:1.0(m)` or `(p)` → force module-path

This syntax works in:
- Command-line endpoints: `jgo run org.example:artifact:1.0(m)`
- jgo.toml dependencies: `coordinates = ["org.example:artifact:1.0(c)"]`

### R3: Smart Main Class Handling

When the main class resides in a modular JAR, jgo should use `--module` instead of appending the class name directly:

```bash
# Non-modular main class
java -cp jars... com.example.Main

# Modular main class
java --module-path modules... -cp jars... --module com.example.mod/com.example.Main
```

### R4: CLI Override Flags

Global flags to override auto-detection for all JARs:
- `--class-path-only`: Force all JARs to class-path (disable module detection)
- `--module-path-only`: Force all JARs to module-path

### R5: Pass-Through for Other JPMS Flags

jgo already supports passing arbitrary JVM arguments via the `--` separator. This mechanism handles JPMS flags like `--add-opens`, `--add-reads`, `--add-exports`, etc.:

```bash
jgo run org.example:artifact --add-opens java.base/java.lang=ALL-UNNAMED -- app-arg
```

No special handling needed for these flags.

## Design

### Environment Directory Structure

With module support, the environment directory structure changes from:

```
<env-dir>
├── jars/
│   ├── artifact-1.0.jar
│   ├── dep1-2.0.jar
│   └── dep2-3.0.jar
└── jgo.lock.toml
```

To:

```
<env-dir>
├── jars/          # Non-modular JARs (class-path)
│   ├── legacy-lib-1.0.jar
│   └── old-dep-2.0.jar
├── modules/       # Modular JARs (module-path)
│   ├── modular-lib-1.0.jar
│   └── jpms-dep-2.0.jar
└── jgo.lock.toml
```

**Benefits of separate directories:**

1. **Simpler command construction**:
   ```bash
   # Instead of enumerating each JAR:
   java --module-path mod1.jar:mod2.jar:mod3.jar -cp jar1.jar:jar2.jar ...

   # Use directory paths:
   java --module-path modules -cp "jars/*" ...
   ```

2. **`--add-modules=ALL-MODULE-PATH`**: Automatically includes all modules from the directory

3. **Clear separation**: Easy to inspect which JARs are modular

4. **Wildcard classpath**: Can use `jars/*` instead of enumerating (shorter command)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLI Layer                                  │
│  ┌───────────────────┐  ┌──────────────────┐  ┌───────────────────┐ │
│  │ parser.py         │  │ run.py           │  │ ParsedArgs        │ │
│  │ --class-path-only │  │ module_mode      │  │ module_mode field │ │
│  │ --module-path-only│  │ parameter        │  │                   │ │
│  │   flags           │  │ handling         │  │                   │ │
│  └───────────────────┘  └──────────────────┘  └───────────────────┘ │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                       Environment Layer                             │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────────┐   │
│  │ environment.py  │  │ lockfile.py      │  │ builder.py        │   │
│  │ module_path_jars│  │ is_modular field │  │ detect and store  │   │
│  │ classpath_jars  │  │ module_name      │  │ module info       │   │
│  │ properties      │  │ placement        │  │                   │   │
│  └─────────────────┘  └──────────────────┘  └───────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                        Core Utilities                               │
│  ┌─────────────────┐  ┌──────────────────┐                          │
│  │ jar_util.py     │  │ coordinate.py    │                          │
│  │ has_module_info │  │ placement field  │                          │
│  │ get_module_name │  │ (c)/(m) parsing  │                          │
│  └─────────────────┘  └──────────────────┘                          │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                       Execution Layer                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ runner.py                                                     │  │
│  │ - Build --module-path and -cp arguments                       │  │
│  │ - Use --module for modular main class                         │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Component Details

#### 1. Module Detection (`src/jgo/env/jar_util.py`)

New functions for detecting modular JARs:

```python
@dataclass
class ModuleInfo:
    """Information about a JAR's module status."""
    is_modular: bool           # Has module-info.class at root
    module_name: str | None    # Module name if modular
    is_automatic: bool         # True if using Automatic-Module-Name


def has_module_info(jar_path: Path) -> bool:
    """
    Check if JAR contains module-info.class at its root.

    Args:
        jar_path: Path to JAR file

    Returns:
        True if module-info.class exists at JAR root
    """
    try:
        with zipfile.ZipFile(jar_path) as jar:
            return "module-info.class" in jar.namelist()
    except (zipfile.BadZipFile, FileNotFoundError):
        return False


def get_automatic_module_name(jar_path: Path) -> str | None:
    """
    Get Automatic-Module-Name from JAR manifest.

    Args:
        jar_path: Path to JAR file

    Returns:
        Automatic-Module-Name value if present, None otherwise
    """
    manifest = parse_manifest(jar_path)  # Reuse existing function
    return manifest.get("Automatic-Module-Name") if manifest else None


def parse_module_name_from_descriptor(jar_path: Path) -> str | None:
    """
    Extract module name from module-info.class bytecode.

    The module-info.class file is a standard class file with a Module attribute.
    The module name is stored as a CONSTANT_Module_info entry in the constant pool.

    Args:
        jar_path: Path to JAR file

    Returns:
        Module name if parseable, None otherwise
    """
    # Implementation: Read class file, parse constant pool, extract module name
    # See "Parsing module-info.class" section below


def detect_module_info(jar_path: Path) -> ModuleInfo:
    """
    Detect module information for a JAR.

    Priority:
    1. Explicit module-info.class → extract module name
    2. Automatic-Module-Name manifest header → use as module name
    3. Neither → not modular

    Args:
        jar_path: Path to JAR file

    Returns:
        ModuleInfo with detection results
    """
    if has_module_info(jar_path):
        module_name = parse_module_name_from_descriptor(jar_path)
        return ModuleInfo(is_modular=True, module_name=module_name, is_automatic=False)

    auto_name = get_automatic_module_name(jar_path)
    if auto_name:
        return ModuleInfo(is_modular=True, module_name=auto_name, is_automatic=True)

    return ModuleInfo(is_modular=False, module_name=None, is_automatic=False)
```

#### 2. Parsing module-info.class

The `module-info.class` file follows the standard Java class file format (JVMS §4). The module name is found in:

1. **Constant Pool**: Contains a `CONSTANT_Module_info` entry (tag 19)
2. **Module Attribute**: References the module name via constant pool index

Simplified parsing approach:

```python
def parse_module_name_from_descriptor(jar_path: Path) -> str | None:
    """Extract module name from module-info.class."""
    try:
        with zipfile.ZipFile(jar_path) as jar:
            with jar.open("module-info.class") as f:
                data = f.read()
                return _parse_module_name(data)
    except (zipfile.BadZipFile, KeyError, FileNotFoundError):
        return None


def _parse_module_name(class_bytes: bytes) -> str | None:
    """
    Parse module name from class file bytes.

    Class file structure:
    - u4 magic (0xCAFEBABE)
    - u2 minor_version
    - u2 major_version
    - u2 constant_pool_count
    - cp_info constant_pool[constant_pool_count-1]
    - u2 access_flags
    - u2 this_class
    - u2 super_class
    - u2 interfaces_count
    - u2 interfaces[interfaces_count]
    - u2 fields_count
    - field_info fields[fields_count]
    - u2 methods_count
    - method_info methods[methods_count]
    - u2 attributes_count
    - attribute_info attributes[attributes_count]

    The Module attribute contains a module_name_index pointing to
    a CONSTANT_Module_info, which points to a CONSTANT_Utf8_info.
    """
    import struct

    # Verify magic number
    if data[:4] != b'\xca\xfe\xba\xbe':
        return None

    # Skip to constant pool (after magic, minor, major versions)
    pos = 8
    cp_count = struct.unpack(">H", data[pos:pos+2])[0]
    pos += 2

    # Parse constant pool, looking for CONSTANT_Module_info (tag 19)
    # and building UTF-8 string table
    constant_pool = [None]  # 1-indexed
    i = 1
    while i < cp_count:
        tag = data[pos]
        pos += 1

        if tag == 1:  # CONSTANT_Utf8_info
            length = struct.unpack(">H", data[pos:pos+2])[0]
            pos += 2
            utf8_str = data[pos:pos+length].decode("utf-8", errors="replace")
            pos += length
            constant_pool.append(("Utf8", utf8_str))
        elif tag == 19:  # CONSTANT_Module_info
            name_index = struct.unpack(">H", data[pos:pos+2])[0]
            pos += 2
            constant_pool.append(("Module", name_index))
        # ... handle other constant types (skip them)
        else:
            # Skip based on tag type
            pos += _constant_size(tag, data, pos)
            constant_pool.append(None)
        i += 1

    # Find the Module attribute and get module name
    # (Skip to attributes section and look for "Module" attribute)
    # The module name index is the first u2 after attribute_length

    # ... implementation continues
```

**Alternative**: Use the JAR filename as a fallback module name derivation (less accurate but simpler).

#### 3. Coordinate Parsing (`src/jgo/parse/coordinate.py`)

Extend `Coordinate` dataclass:

```python
@dataclass
class Coordinate:
    groupId: str
    artifactId: str
    version: str | None = None
    classifier: str | None = None
    packaging: str | None = None
    scope: str | None = None
    optional: bool = False
    raw: bool | None = None
    placement: Literal["auto", "class-path", "module-path"] | None = None  # NEW
```

Modify `_parse_coordinate_dict()`:

```python
def _parse_coordinate_dict(coordinate: str) -> dict[str, str | None]:
    # ... existing raw/! handling ...

    # NEW: Check for module placement suffix
    # Must come after ! handling but before splitting on :
    placement = None
    placement_suffixes = [
        ("(cp)", "class-path"),
        ("(c)", "class-path"),
        ("(mp)", "module-path"),
        ("(m)", "module-path"),
        ("(p)", "module-path"),
    ]
    for suffix, value in placement_suffixes:
        if coordinate.endswith(suffix):
            coordinate = coordinate[:-len(suffix)]
            placement = value
            break

    # ... existing parsing logic ...

    return {
        # ... existing fields ...
        "placement": placement,  # NEW
    }
```

Update `coord2str()`:

```python
def coord2str(..., placement: str | None = None) -> str:
    # ... existing logic ...

    # Append placement suffix
    if placement == "class-path":
        result += "(c)"
    elif placement == "module-path":
        result += "(m)"

    return result
```

#### 4. Lockfile Extension (`src/jgo/env/lockfile.py`)

Extend `LockedDependency`:

```python
class LockedDependency(TOMLSerializableMixin, FieldValidatorMixin):
    def __init__(
        self,
        groupId: str,
        artifactId: str,
        version: str,
        packaging: str = "jar",
        classifier: str | None = None,
        sha256: str | None = None,
        # NEW fields:
        is_modular: bool = False,
        module_name: str | None = None,
        placement: str | None = None,  # "class-path", "module-path", or None
    ):
        # ... existing init ...
        self.is_modular = is_modular
        self.module_name = module_name
        self.placement = placement

    def to_dict(self) -> dict:
        data = {
            # ... existing fields ...
        }
        # Only include if modular (sparse representation)
        if self.is_modular:
            data["is_modular"] = True
            if self.module_name:
                data["module_name"] = self.module_name
        if self.placement:
            data["placement"] = self.placement
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "LockedDependency":
        return cls(
            # ... existing fields ...
            is_modular=data.get("is_modular", False),
            module_name=data.get("module_name"),
            placement=data.get("placement"),
        )
```

#### 5. Environment Extension (`src/jgo/env/environment.py`)

With the directory-based approach, classification is simpler - JARs are already in their target directories:

```python
class Environment:
    # ... existing code ...

    @property
    def jars_dir(self) -> Path:
        """Directory containing class-path JARs."""
        return self.path / "jars"

    @property
    def modules_dir(self) -> Path:
        """Directory containing module-path JARs."""
        return self.path / "modules"

    @property
    def all_jars(self) -> list[Path]:
        """All JAR files in this environment (both jars/ and modules/)."""
        jars = []
        if self.jars_dir.exists():
            jars.extend(sorted(self.jars_dir.glob("*.jar")))
        if self.modules_dir.exists():
            jars.extend(sorted(self.modules_dir.glob("*.jar")))
        return jars

    @property
    def class_path_jars(self) -> list[Path]:
        """JARs in the jars/ directory (class-path)."""
        if not self.jars_dir.exists():
            return []
        return sorted(self.jars_dir.glob("*.jar"))

    @property
    def module_path_jars(self) -> list[Path]:
        """JARs in the modules/ directory (module-path)."""
        if not self.modules_dir.exists():
            return []
        return sorted(self.modules_dir.glob("*.jar"))

    @property
    def has_modules(self) -> bool:
        """True if environment has any modular JARs."""
        return self.modules_dir.exists() and any(self.modules_dir.glob("*.jar"))

    @property
    def has_classpath(self) -> bool:
        """True if environment has any classpath JARs."""
        return self.jars_dir.exists() and any(self.jars_dir.glob("*.jar"))

    def get_module_for_main_class(self, main_class: str) -> tuple[str | None, bool]:
        """
        Find the module containing a main class.

        Args:
            main_class: Fully qualified class name

        Returns:
            (module_name, is_modular) - module_name is None if not in modular JAR
        """
        # Convert class name to internal path
        class_path = main_class.replace(".", "/") + ".class"

        for jar in self.module_path_jars:
            try:
                with zipfile.ZipFile(jar) as zf:
                    if class_path in zf.namelist():
                        # Found it - get module name from lockfile or detect
                        lockfile = self.lockfile
                        if lockfile:
                            for dep in lockfile.dependencies:
                                if jar.name.startswith(f"{dep.artifactId}-{dep.version}"):
                                    if dep.module_name:
                                        return dep.module_name, True
                        # Fallback: detect module name
                        from .jar_util import detect_module_info
                        info = detect_module_info(jar)
                        return info.module_name, True
            except (zipfile.BadZipFile, IOError):
                continue

        return None, False
```

#### 6. Runner Modification (`src/jgo/exec/runner.py`)

Update `JavaRunner.run()` to use directory-based paths:

```python
class JavaRunner:
    def run(
        self,
        environment,
        main_class: str | None = None,
        app_args: list[str] | None = None,
        additional_jvm_args: list[str] | None = None,
        additional_classpath: list[str] | None = None,
        print_command: bool = False,
        dry_run: bool = False,
        module_mode: str = "auto",  # NEW: "auto", "class-path-only", "module-path-only"
    ) -> subprocess.CompletedProcess:
        # Determine main class
        effective_main_class = main_class or environment.main_class
        if not effective_main_class:
            raise RuntimeError("No main class specified...")

        # Get directory paths based on module mode
        jars_dir = environment.path / "jars"
        modules_dir = environment.path / "modules"

        has_classpath = jars_dir.exists() and any(jars_dir.glob("*.jar"))
        has_modules = modules_dir.exists() and any(modules_dir.glob("*.jar"))

        if module_mode == "class-path-only":
            # Force all JARs to classpath - use jars/* even for modules
            use_modules = False
            use_classpath = True
            # Note: In class-path-only mode, builder puts all in jars/
        elif module_mode == "module-path-only":
            use_modules = True
            use_classpath = False
            # Note: In module-path-only mode, builder puts all in modules/
        else:  # "auto"
            use_modules = has_modules
            use_classpath = has_classpath

        if not use_modules and not use_classpath:
            raise RuntimeError(f"No JARs found in environment: {environment.path}")

        # Locate Java executable
        locator = JavaLocator(...)
        java_path = locator.locate(...)

        # Build command
        cmd = [str(java_path)]

        # Add JVM arguments
        jvm_args = self.jvm_config.to_jvm_args()
        cmd.extend(jvm_args)

        if additional_jvm_args:
            cmd.extend(additional_jvm_args)

        # Add module-path (directory, not enumerated JARs)
        if use_modules:
            cmd.extend(["--module-path", str(modules_dir)])
            # Add all modules from the module-path
            cmd.extend(["--add-modules", "ALL-MODULE-PATH"])

        # Add classpath using wildcard (directory/*)
        if use_classpath:
            classpath_parts = [f"{jars_dir}/*"]
            if additional_classpath:
                classpath_parts.extend(additional_classpath)
            separator = ";" if sys.platform == "win32" else ":"
            cmd.extend(["-cp", separator.join(classpath_parts)])

        # Determine if main class is in modular JAR
        module_name, is_modular = environment.get_module_for_main_class(
            effective_main_class
        )

        if is_modular and module_name:
            # Use --module for modular main class
            cmd.extend(["--module", f"{module_name}/{effective_main_class}"])
        else:
            # Traditional main class on command line
            cmd.append(effective_main_class)

        # Add application arguments
        if app_args:
            cmd.extend(app_args)

        # ... rest of method unchanged ...
```

#### 7. CLI Flags (`src/jgo/cli/parser.py`)

Add global options:

```python
def global_options(f):
    # ... existing options ...

    f = click.option(
        "--class-path-only",
        is_flag=True,
        help="Force all JARs to classpath (disable module detection).",
    )(f)

    f = click.option(
        "--module-path-only",
        is_flag=True,
        help="Force all JARs to module-path (treat as modular).",
    )(f)

    return f
```

Update `ParsedArgs`:

```python
class ParsedArgs:
    def __init__(
        self,
        # ... existing fields ...
        class_path_only: bool = False,
        module_path_only: bool = False,
    ):
        # ... existing init ...
        self.class_path_only = class_path_only
        self.module_path_only = module_path_only

    @property
    def module_mode(self) -> str:
        """Derive module mode from flags."""
        if self.class_path_only:
            return "class-path-only"
        elif self.module_path_only:
            return "module-path-only"
        return "auto"
```

#### 8. Run Command (`src/jgo/cli/commands/run.py`)

Pass module mode to runner:

```python
def _run_endpoint(...):
    # ... existing code ...

    result = runner.run(
        environment,
        main_class=main_class_to_use,
        app_args=args.app_args,
        additional_jvm_args=args.jvm_args,
        additional_classpath=args.classpath_append,
        print_command=args.print_command,
        dry_run=args.dry_run,
        module_mode=args.module_mode,  # NEW
    )
```

#### 9. Builder Integration (`src/jgo/env/builder.py`)

The builder links JARs to the correct directory based on module detection:

```python
def _build_environment(self, env_path: Path, dependencies: list[Dependency], ...):
    """Build environment by linking JARs to appropriate directories."""
    from .jar_util import detect_module_info

    jars_dir = env_path / "jars"
    modules_dir = env_path / "modules"

    # Create directories
    jars_dir.mkdir(parents=True, exist_ok=True)
    modules_dir.mkdir(parents=True, exist_ok=True)

    locked_deps = []

    for dep in dependencies:
        artifact = dep.artifact
        source_jar = artifact.resolve()  # Path in Maven repo

        # Detect module info
        info = detect_module_info(source_jar)

        # Check for explicit placement override from coordinate
        coord = dep.coordinate
        if hasattr(coord, 'placement') and coord.placement:
            if coord.placement == "class-path":
                target_dir = jars_dir
            elif coord.placement == "module-path":
                target_dir = modules_dir
            else:
                # Auto: use detection result
                target_dir = modules_dir if info.is_modular else jars_dir
        else:
            # Auto-detect: modular JARs go to modules/, others to jars/
            target_dir = modules_dir if info.is_modular else jars_dir

        # Link JAR to target directory
        target_jar = target_dir / artifact.filename
        self._link_jar(source_jar, target_jar)

        # Create locked dependency with module info
        locked_deps.append(LockedDependency(
            groupId=artifact.groupId,
            artifactId=artifact.artifactId,
            version=artifact.version,
            packaging=artifact.packaging,
            classifier=artifact.classifier,
            sha256=compute_sha256(source_jar),
            is_modular=info.is_modular,
            module_name=info.module_name,
            placement=coord.placement if hasattr(coord, 'placement') else None,
        ))

    # Create lockfile
    lockfile = LockFile(
        dependencies=locked_deps,
        # ... other fields ...
    )
    lockfile.save(env_path / "jgo.lock.toml")
```

**Key changes:**
1. JARs are linked to `jars/` or `modules/` based on module detection
2. Explicit `(c)`/`(m)` placement overrides auto-detection
3. Module info is stored in lockfile for fast subsequent lookups

## Example Usage

### Auto-Detection (Default)

```bash
# SLF4J 2.x is modular, Logback is not (typically)
jgo run org.slf4j:slf4j-api:2.0.9+ch.qos.logback:logback-classic:1.4.11

# Generated command (clean directory-based paths):
java --module-path ~/.jgo/.../modules \
     --add-modules ALL-MODULE-PATH \
     -cp "~/.jgo/.../jars/*" \
     --module org.slf4j/org.slf4j.simple.SimpleLogger

# Environment structure:
# ~/.jgo/.../
# ├── modules/
# │   └── slf4j-api-2.0.9.jar       # Modular
# ├── jars/
# │   └── logback-classic-1.4.11.jar # Non-modular
# └── jgo.lock.toml
```

### Explicit Placement

```bash
# Force SLF4J to classpath (avoid module issues)
jgo run "org.slf4j:slf4j-api:2.0.9(c)+ch.qos.logback:logback-classic:1.4.11"

# Force everything to module-path
jgo run --module-path-only org.example:my-app:1.0
```

### With JPMS Flags

```bash
# Add --add-opens for reflection access
jgo run org.example:my-app:1.0 \
    --add-opens java.base/java.lang=ALL-UNNAMED \
    -- app-arg1 app-arg2
```

## Testing Strategy

### Unit Tests

1. **Module detection** (`tests/test_jar_util.py`):
   - `has_module_info()` with modular/non-modular JARs
   - `parse_module_name_from_descriptor()` with various module-info.class files
   - `get_automatic_module_name()` with manifest entries

2. **Coordinate parsing** (`tests/test_coordinate.py`):
   - Parse `g:a:v(c)`, `g:a:v(m)`, `g:a:v(cp)`, etc.
   - Round-trip serialization with placement suffix

3. **Environment classification** (`tests/test_environment.py`):
   - `module_path_jars` vs `class_path_jars` properties
   - `get_module_for_main_class()`

### Integration Tests

1. **Known modular libraries**:
   - `org.slf4j:slf4j-api:2.0.x` (modular since 2.0)
   - Verify correct placement on module-path

2. **Mixed dependencies**:
   - Combine modular and non-modular JARs
   - Verify split between `--module-path` and `-cp`

3. **CLI flags**:
   - `--class-path-only` forces all to classpath
   - `--module-path-only` forces all to module-path

### Test Fixtures

Create test JAR files:
- `modular-test.jar`: Contains `module-info.class` with `module test.module { }`
- `automatic-test.jar`: Manifest with `Automatic-Module-Name: automatic.module`
- `legacy-test.jar`: No module info (plain JAR)

## Migration & Compatibility

### Backward Compatibility

- **Default behavior changes**: Auto-detection is enabled by default. This should be transparent for most users but could cause issues with:
  - JARs that have `module-info.class` but aren't meant to be used as modules
  - Split package scenarios

- **Escape hatch**: `--class-path-only` reverts to pre-module behavior

### Breaking Changes

None. All changes are additive:
- New coordinate syntax `(c)`/`(m)` is optional
- New CLI flags are optional
- Default behavior improves modular app support

## Future Considerations

1. **Module path in jgo.toml**: Could add explicit module-path section
2. **Automatic `--add-opens`**: Detect common reflection patterns
3. **Module graph visualization**: Show module dependencies
4. **Service provider detection**: Automatic `--add-modules` for services

# Entrypoint Inference Design

This document describes the design and implementation of entrypoint inference in jgo.

## Problem Statement

When running `jgo init org.python:jython-slim`, the main class is inferred from the JAR's manifest. However:

1. This inferred value was not written to `jgo.toml`
2. After `jgo update`, if the main class changes in a new version, the behavior is undefined
3. It was unclear whether to crystallize the main class or keep it "magical"

## Design Decision

We use a **hybrid approach** with coordinate references:

### jgo.toml (User Intent)

```toml
[dependencies]
coordinates = ["org.python:jython-slim"]

[entrypoints]
main = "org.python:jython-slim"  # Coordinate reference - re-infer on update
# OR
repl = "org.python.util.jython"  # Concrete class - fixed
default = "main"
```

**Disambiguation**: Colons indicate Maven coordinates; no colons means class name.

### jgo.lock.toml (Locked Reality)

```toml
[metadata]
generated = "2025-12-22T02:08:42Z"
spec_hash = "a1b2c3d4"  # For staleness detection

[java]
version = "17"           # User preference
vendor = "corretto"      # User preference
min_version = "11"       # Computed from bytecode

[entrypoints]
main = "org.python.util.jython"  # Always concrete

[[dependencies]]
# ... exact versions with checksums
```

## Implementation

### Key Functions

**`is_coordinate_reference(value: str) -> bool`**
- Returns `True` if value contains `:` (Maven coordinate)
- Returns `False` otherwise (class name)

**`infer_main_class_from_coordinates(coord_str, components, jars_dir)`**
- Parses coordinate string (handles `+` composition)
- Searches JARs for matching artifactId
- Reads Main-Class from JAR manifest
- Returns first found main class or None

**`_infer_concrete_entrypoints(spec, components, jars_dir)`**
- Iterates over spec.entrypoints
- For coordinate references: infers from JARs
- For class names: auto-completes if needed
- Returns dict of concrete main classes

### Lockfile Enhancements

Added fields to `LockFile`:
- `spec_hash`: SHA256 hash of jgo.toml (first 16 chars) for staleness detection
- `java_version`: User's preferred Java version (from spec)
- `java_vendor`: User's preferred Java vendor (from spec)
- `min_java_version`: Computed minimum (from bytecode analysis)

### jgo init Behavior

`jgo init org.python:jython-slim` creates:

```toml
[entrypoints]
main = "org.python:jython-slim"
default = "main"
```

`jgo init org.python:jython-slim@MyMain` creates:

```toml
[entrypoints]
main = "MyMain"
default = "main"
```

### jgo sync/update Behavior

1. Resolves dependencies
2. For each entrypoint:
   - If coordinate reference: Re-infer from new JARs
   - If class name: Keep as-is
3. Always recalculate `min_java_version`
4. Generate lockfile with concrete entrypoints

### Staleness Detection

`spec_hash` enables detection of when `jgo.toml` has changed:

```python
def is_lockfile_stale(spec_path, lockfile_path):
    if not lockfile_path.exists():
        return True
    
    current_hash = compute_spec_hash(spec_path)
    lockfile = LockFile.load(lockfile_path)
    
    return lockfile.spec_hash != current_hash
```

## Benefits

1. **No premature materialization**: `jgo init` stays fast and offline
2. **Explicit control**: Users choose inference vs. fixed via coordinate reference
3. **Single source of truth**: `jgo.lock.toml` is what actually runs
4. **Reproducibility**: Full version locking + main class locking
5. **Update flexibility**: Can re-infer or keep fixed based on jgo.toml

## Edge Cases

### No Main-Class Found

If inference fails (no Main-Class in JAR):
- Entrypoint is **omitted** from lockfile
- At runtime, error: "No Main-Class found. Specify with `jgo run --main-class`"
- Future `jgo update` will re-attempt inference (maybe new version has Main-Class)

### Composite Coordinates

`jgo init org.foo:foo+org.bar:bar` creates:

```toml
[entrypoints]
main = "org.foo:foo+org.bar:bar"
```

Inference tries each coordinate in order until Main-Class is found.

### manifest.json Status

Currently kept for backward compatibility. It stores:
- `main_class`: Concrete main class (redundant with lockfile)
- `min_java_version`: Cached bytecode analysis (redundant with lockfile)

**Future**: Can be eliminated or made pure performance optimization.

## Migration Path

Existing jgo.toml files with concrete entrypoints continue to work unchanged.

New `jgo init` creates coordinate references by default, enabling the "magical" re-inference behavior.

## Testing

See `tests/test_entrypoint_inference.py` for comprehensive tests covering:
- Coordinate reference inference
- Explicit class name preservation
- Lockfile spec hash generation
- Staleness detection

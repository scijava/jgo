# Dependency Exclusion Feature Design

## Overview

This document specifies dependency exclusion support for jgo v2, allowing users to exclude specific transitive dependencies from the classpath when running Java applications.

## Motivation

Maven supports `<exclusions>` blocks within `<dependency>` elements to exclude transitive dependencies. Users need equivalent functionality in jgo without creating custom pom.xml files.

Common use cases:
- **Logging conflicts**: Exclude commons-logging when using slf4j
- **Version conflicts**: Exclude older component versions when explicitly including newer ones with different G:A
- **Unwanted dependencies**: Remove unused transitive dependencies that cause classpath bloat

## Design Summary

### Three Ways to Specify Exclusions

1. **Endpoint syntax (inline)**: Exclusions specified directly in coordinate strings
   - `coord(x)` - Mark this coordinate AS a global exclusion
   - `coord(x:excl1,x:excl2)` - This coordinate HAS per-dependency exclusions

2. **jgo.toml (project mode)**: Exclusions in project configuration files
   - Global exclusions: `exclusions = ["g:a", ...]`
   - Per-coordinate: Use inline syntax in coordinate strings

3. **jgo exclude (management)**: CLI command to add/remove exclusions from jgo.toml
   - `jgo exclude add g:a`
   - `jgo exclude remove g:a`
   - `jgo exclude list`

### Design Rationale

**Why inline syntax?**
- Exclusions modify the dependency graph and must affect the cache key
- Users may need to include exclusions in shortcuts (which expand to endpoints, not CLI flags)
- Enables per-coordinate exclusions: exclude X from coordinate A but not from coordinate B

**Why no `--exclude` CLI flag?**
- Redundant with inline syntax: `+coord(x)` achieves same result
- Simplicity: One way to specify exclusions (Python philosophy)
- Consistency: Other coordinate modifiers (placement, raw) use inline syntax

**Why `jgo exclude` command?**
- Convenience for managing jgo.toml without manual editing
- Validates exclusion coordinates before writing
- Prevents syntax errors in TOML files
- Symmetry with `jgo add` and `jgo remove` for coordinates themselves

## Detailed Specification

### 1. Endpoint Syntax

All coordinate modifiers use a **unified parenthetical** with comma-separated values:

#### Grammar

```
coordinate := G:A[:V][:C][:P] [modifiers] [!] [@mainClass]
modifiers  := '(' modifier [',' modifier]* ')'
modifier   := placement | exclusion-marker | exclusion
placement  := 'c' | 'cp' | 'm' | 'mp' | 'p'
exclusion-marker := 'x'                              # this coord IS an exclusion
exclusion        := 'x:' groupId ':' artifactId      # this coord HAS this exclusion
```

**Key simplification:** Each exclusion is a separate modifier with its own `x:` prefix. This eliminates comma ambiguity - commas only separate modifiers, never parts within a modifier.

#### Two Meanings of `(x)`

**1. Exclusion Marker**: `coord(x)` - this coordinate IS a global exclusion

```bash
# Include httpclient, but globally exclude commons-logging and log4j
jgo httpclient+commons-logging:commons-logging(x)+log4j:log4j(x)
```

The marked coordinates are excluded from ALL dependencies in the dependency graph.

**2. Exclusion List**: `coord(x:excl1,x:excl2)` - this coordinate HAS per-dependency exclusions

```bash
# Include httpclient, but exclude commons-logging only from httpclient's dependency tree
jgo httpclient(x:commons-logging:commons-logging)
```

The exclusions apply only to the specified coordinate's transitive dependencies.

#### Multiple Exclusions

Specify multiple exclusions by repeating the `x:` modifier:

```bash
# Exclude multiple dependencies from httpclient
jgo httpclient(x:commons-logging:commons-logging,x:commons-codec:commons-codec)
```

#### Wildcard Support

Maven-style wildcards (`*`) are supported for groupId or artifactId:

```bash
# Exclude all artifacts from org.slf4j group
jgo spring-web(x:org.slf4j:*)

# Exclude commons-logging from any group
jgo httpclient(x:*:commons-logging)
```

#### Combining Modifiers

Multiple modifiers can coexist in one parenthetical (order independent):

```bash
# Placement + exclusions
jgo httpclient(c,x:commons-logging:commons-logging)
jgo httpclient(x:commons-logging:commons-logging,c)  # same thing

# Multiple exclusions + placement + raw flag
jgo httpclient:4.5.14(c,x:commons-logging:commons-logging,x:commons-codec:commons-codec)!

# Module-path + exclusions
jgo lwjgl:3.3.1(m,x:lwjgl-opengl:lwjgl-opengl)
```

**Key properties:**
- **Single parenthetical** - no ambiguity about ordering
- **Comma-separated** - readable and familiar
- **Order independent** - `(c,x:...)` equals `(x:...,c)`
- **Extensible** - easy to add new modifiers
- **Raw flag `!` always last** - logical termination symbol

#### Examples

**Basic global exclusion:**
```bash
jgo httpclient+commons-logging:commons-logging(x)
```

**Per-coordinate exclusion:**
```bash
jgo httpclient(x:commons-logging:commons-logging)+spring-web
```

**Multiple per-coordinate exclusions:**
```bash
jgo spring-web(x:commons-logging:commons-logging,x:log4j:log4j)
```

**Combined with placement modifiers:**
```bash
jgo lwjgl:3.3.1(m,x:lwjgl-opengl:lwjgl-opengl)
```

**Complex scenario with main class:**
```bash
jgo 'httpclient(x:commons-logging:commons-logging)+lwjgl:3.3.1(m)@MyApp'
```

#### Shortcuts with Exclusions

Shortcuts can include exclusions since they're part of the coordinate syntax:

```ini
# ~/.config/jgo.conf
[shortcuts]
# Per-coordinate exclusions
httpclient-clean = httpclient:4.5.14(x:commons-logging:commons-logging,x:commons-codec:commons-codec)
spring-clean = spring-web(x:commons-logging:commons-logging,x:log4j:log4j)

# Exclusions + placement
lwjgl-modular = lwjgl:3.3.1(m,x:lwjgl-opengl:lwjgl-opengl)

# Global exclusion markers
no-logging = httpclient+commons-logging:commons-logging(x)+log4j:log4j(x)
```

Usage:
```bash
jgo httpclient-clean
jgo spring-clean@MyApp
jgo lwjgl-modular
```

### 2. jgo.toml Integration

#### Global Exclusions

Global exclusions apply to all dependencies in the environment:

```toml
[environment]
name = "my-app"

[dependencies]
coordinates = [
    "org.springframework:spring-web:5.3.20",
    "org.apache.httpcomponents:httpclient:4.5.13"
]

# Global exclusions - applied to ALL dependencies above
exclusions = [
    "commons-logging:commons-logging",
    "log4j:log4j"
]
```

#### Per-Coordinate Exclusions

Use inline endpoint syntax directly in coordinate strings:

```toml
[dependencies]
coordinates = [
    # Exclude commons-logging only from httpclient
    "org.apache:httpclient:4.5.14(x:commons-logging:commons-logging)",

    # Exclude multiple dependencies from spring-web
    "org.springframework:spring-web:5.3.20(x:commons-logging:commons-logging,x:log4j:log4j)",

    # Regular coordinate without exclusions
    "org.slf4j:slf4j-api:1.7.32"
]
```

**Rationale for inline syntax:**
- Reuses existing endpoint parsing logic
- No special TOML schema needed
- Clear and self-documenting
- Consistent with CLI usage

#### Complete Example

```toml
[environment]
name = "web-app"

[dependencies]
# Mix of global and per-coordinate exclusions
coordinates = [
    # This has its own exclusions
    "org.apache:httpclient:4.5.14(x:commons-codec:commons-codec)",

    # This one too
    "org.springframework:spring-web:5.3.20(x:log4j:log4j)",

    # This gets global exclusions only
    "org.slf4j:slf4j-api:1.7.32"
]

# These apply to ALL coordinates
exclusions = [
    "commons-logging:commons-logging"
]

[entrypoints]
default = "com.example.WebApp"
```

**Effective exclusions:**
- httpclient: excludes commons-logging (global) + commons-codec (per-coord)
- spring-web: excludes commons-logging (global) + log4j (per-coord)
- slf4j-api: excludes commons-logging (global only)

### 3. jgo exclude Command

Manage exclusions in jgo.toml files via CLI.

#### Command Syntax

```bash
# Add global exclusion
jgo exclude add <groupId>:<artifactId>

# Remove global exclusion
jgo exclude remove <groupId>:<artifactId>

# List all exclusions
jgo exclude list

# Add exclusion to specific coordinate (optional feature)
jgo exclude add --coordinate <coordinate> <exclusion>
```

#### Options

- `--file FILE` or `-f FILE`: Path to jgo.toml (default: ./jgo.toml)
- `--coordinate <coordinate>`: Coordinate to modify with the exclusion

#### Examples

**Add global exclusion:**
```bash
jgo exclude add commons-logging:commons-logging
# Adds to [dependencies] exclusions array in jgo.toml
```

**Remove global exclusion:**
```bash
jgo exclude remove commons-logging:commons-logging
# Removes from [dependencies] exclusions array
```

**List all exclusions:**
```bash
jgo exclude list
# Output:
# Global exclusions:
#   - commons-logging:commons-logging
#   - log4j:log4j
#
# Per-coordinate exclusions:
#   org.apache:httpclient:4.5.14
#     - commons-codec:commons-codec
#   org.springframework:spring-web:5.3.20
#     - log4j:log4j
```

**Add per-coordinate exclusion (optional):**
```bash
jgo exclude add --coordinate httpclient:4.5.14 commons-logging:commons-logging
# Modifies the coordinate string in jgo.toml to add x:commons-logging:commons-logging modifier
```

#### Behavior

**Adding exclusions:**
1. Validate exclusion coordinate format (groupId:artifactId)
2. Load existing jgo.toml
3. Check if exclusion already exists (idempotent)
4. Add to `[dependencies] exclusions` array
5. Write updated jgo.toml (preserve formatting where possible)
6. Print confirmation message

**Removing exclusions:**
1. Validate exclusion coordinate format
2. Load existing jgo.toml
3. Remove from exclusions array (no error if not present)
4. Write updated jgo.toml
5. Print confirmation message

**Listing exclusions:**
1. Load jgo.toml
2. Parse global exclusions from `[dependencies] exclusions`
3. Parse per-coordinate exclusions from coordinate strings
4. Display grouped by type (global vs per-coordinate)

**Error handling:**
- No jgo.toml exists: Create new file with minimal structure
- Invalid coordinate format: Print error and exit
- TOML syntax error: Print error and suggest manual fix
- File not writable: Print error with permission details

#### Implementation Notes

The `jgo exclude` command modifies jgo.toml programmatically using a TOML library (e.g., `tomli`/`tomli-w`).

**For global exclusions:**
- Simple array manipulation in `[dependencies] exclusions`

**For per-coordinate exclusions (optional feature):**
- Parse existing coordinate string
- Add/remove exclusion from `(x:...)` modifier
- Reconstruct coordinate string
- Replace in coordinates array

**Preservation of comments:**
- Best-effort preservation using TOML library features
- Document that some formatting may be lost during automated edits

## Technical Implementation

### 1. Parsing

Extend coordinate parsing in `src/jgo/parse/endpoint.py`:

```python
def parse_coordinate_modifiers(coordinate: str) -> tuple[str, dict]:
    """
    Parse unified parenthetical modifiers from a coordinate string.

    Returns: (coordinate_without_modifiers, modifiers_dict)

    Example:
        >>> parse_coordinate_modifiers("httpclient:4.5.14(c,x:commons-logging:commons-logging,x:log4j:log4j)!")
        ("httpclient:4.5.14", {
            'placement': 'class-path',
            'exclusions': [
                Project(groupId='commons-logging', artifactId='commons-logging'),
                Project(groupId='log4j', artifactId='log4j')
            ],
            'is_exclusion': False,
            'raw': True
        })
    """
    modifiers = {
        'placement': None,        # 'class-path' | 'module-path' | None
        'exclusions': [],         # list[Project]
        'is_exclusion': False,    # bool (this coord IS an exclusion)
        'raw': False              # bool (disable dependency management)
    }

    # 1. Check for raw flag (always at end)
    if coordinate.endswith('!'):
        modifiers['raw'] = True
        coordinate = coordinate[:-1]

    # 2. Extract single parenthetical (if present)
    if '(' in coordinate:
        match = re.search(r'\(([^)]+)\)$', coordinate)
        if match:
            modifier_str = match.group(1)
            coordinate = coordinate[:match.start()]

            # 3. Parse comma-separated modifiers
            for modifier in modifier_str.split(','):
                modifier = modifier.strip()

                # Placement modifiers
                if modifier in ('c', 'cp'):
                    modifiers['placement'] = 'class-path'
                elif modifier in ('m', 'mp', 'p'):
                    modifiers['placement'] = 'module-path'

                # Exclusion marker (this coord IS an exclusion)
                elif modifier == 'x':
                    modifiers['is_exclusion'] = True

                # Exclusion (this coord HAS this exclusion)
                elif modifier.startswith('x:'):
                    excl_str = modifier[2:]  # Strip 'x:'
                    # Parse groupId:artifactId
                    if ':' in excl_str:
                        parts = excl_str.split(':', 1)
                        if len(parts) == 2:
                            groupId, artifactId = parts
                            modifiers['exclusions'].append(
                                Project(groupId=groupId, artifactId=artifactId)
                            )

    return coordinate, modifiers
```

**Parsing strategy:**
1. Strip `!` raw flag (always last)
2. Extract single `(...)` parenthetical
3. Simple comma-split to get modifiers (no special cases needed!)
4. Parse each modifier: placement (`c`, `m`, etc.), exclusion marker (`x`), or exclusion (`x:g:a`)
5. Return cleaned coordinate + modifiers dict

**Key simplification:** No need for complex state machines or special splitting logic. Each `x:groupId:artifactId` is a complete, self-contained modifier.

### 2. Cache Key Integration ✅ **IMPLEMENTED**

Exclusions must affect the cache key since they modify the dependency graph.

**Implemented design:** Changed to use `list[Dependency]` which includes exclusions, classifier, and packaging.

```python
def _cache_key(self, dependencies: list[Dependency]) -> str:
    """
    Generate a stable hash for a set of dependencies.

    Uses full artifact coordinates (G:A:V:C:P) plus exclusions to ensure:
    - Different classifiers get different caches (e.g., natives-linux vs natives-windows)
    - Different packaging types get different caches
    - Different exclusions get different caches (different dependency trees)

    Args:
        dependencies: List of Dependency objects with full coordinate info and exclusions

    Returns:
        16-character hex hash string
    """
    # Sort to ensure stable ordering
    # Use resolved version to ensure RELEASE/LATEST resolve to consistent cache keys
    coord_strings = []
    for dep in sorted(
        dependencies,
        key=lambda d: (
            d.artifact.groupId,
            d.artifact.artifactId,
            d.artifact.version,  # Resolved version
            d.artifact.classifier,
            d.artifact.packaging,
        ),
    ):
        # Include full artifact coordinates: G:A:V:C:P
        coord_str = (
            f"{dep.artifact.groupId}:"
            f"{dep.artifact.artifactId}:"
            f"{dep.artifact.version}:"
            f"{dep.artifact.classifier}:"
            f"{dep.artifact.packaging}"
        )

        # Include exclusions for this dependency
        if dep.exclusions:
            excl_strs = sorted(
                [f"{e.groupId}:{e.artifactId}" for e in dep.exclusions]
            )
            coord_str += f":excl={','.join(excl_strs)}"

        coord_strings.append(coord_str)

    combined = "+".join(coord_strings)

    # Include optional_depth in cache key
    # This ensures different optional_depth values get separate cache directories
    combined += f":optional_depth={self.optional_depth}"

    return hashlib.sha256(combined.encode()).hexdigest()[:16]
```

**Helper methods for conversion:**

```python
def _coordinates_to_dependencies(
    self, coordinates: list[Coordinate]
) -> list[Dependency]:
    """
    Convert Coordinate objects to Dependency objects for cache key generation.
    Preserves classifier, packaging, and exclusion information.
    """
    dependencies = []
    for coord in coordinates:
        version = coord.version or "RELEASE"
        component = self.context.project(coord.groupId, coord.artifactId).at_version(version)

        # Create Artifact with classifier and packaging (G:A:V:C:P)
        classifier = coord.classifier or ""
        packaging = coord.packaging or "jar"
        artifact = component.artifact(classifier=classifier, packaging=packaging)

        # Create Dependency with scope and exclusions
        # TODO: Parse exclusions from coord when exclusion syntax is implemented
        scope = coord.scope or "compile"
        optional = coord.optional or False
        exclusions = []  # Will be populated when exclusion parsing is added

        dependency = Dependency(
            artifact=artifact,
            scope=scope,
            optional=optional,
            exclusions=exclusions,
        )
        dependencies.append(dependency)

    return dependencies

def _components_to_dependencies(
    self, components: list[Component]
) -> list[Dependency]:
    """
    Convert Component objects to Dependency objects with default classifier/packaging.
    Backward compatibility helper for code that still uses Components.
    """
    dependencies = []
    for component in components:
        artifact = component.artifact(classifier="", packaging="jar")
        dependency = Dependency(
            artifact=artifact,
            scope="compile",
            optional=False,
            exclusions=[],
        )
        dependencies.append(dependency)
    return dependencies
```

**Key improvements:**
- ✅ Exclusions baked into Dependency objects (no separate parameters needed)
- ✅ Classifier and packaging included (fixes LWJGL natives bug)
- ✅ Single source of truth for cache key components
- ✅ Ready for exclusion feature (just need to populate `exclusions` field)

### 3. Dependency Resolution Integration

Pass exclusions to Maven resolver when creating synthetic POM:

```python
def create_pom_with_exclusions(
    components: list[Component],
    boms: list[Component] | None,
    global_exclusions: list[Project] | None = None,
    per_coord_exclusions: dict[Component, list[Project]] | None = None
) -> POM:
    """
    Create a synthetic wrapper POM with dependency exclusions.

    Args:
        components: Components to include as dependencies
        boms: BOM imports for dependencyManagement
        global_exclusions: Exclusions applied to all dependencies
        per_coord_exclusions: Per-component exclusions

    Returns:
        POM object representing the synthetic wrapper
    """
    dependencies = []

    for comp in components:
        artifact = comp.artifact()

        # Merge global and per-coordinate exclusions
        exclusions = (global_exclusions or []).copy()
        if per_coord_exclusions and comp in per_coord_exclusions:
            exclusions.extend(per_coord_exclusions[comp])

        # Remove duplicates while preserving order
        seen = set()
        unique_exclusions = []
        for excl in exclusions:
            key = (excl.groupId, excl.artifactId)
            if key not in seen:
                seen.add(key)
                unique_exclusions.append(excl)

        dep = Dependency(
            artifact=artifact,
            scope="compile",
            exclusions=tuple(unique_exclusions)
        )
        dependencies.append(dep)

    # Create wrapper POM with dependencies
    return create_wrapper_pom(dependencies, boms)
```

### 4. EnvironmentBuilder Updates

Extend `EnvironmentBuilder` to handle exclusions:

```python
class EnvironmentBuilder:
    def __init__(
        self,
        context: MavenContext,
        cache_dir: Path | None = None,
        link_strategy: LinkStrategy = LinkStrategy.AUTO,
        optional_depth: int = 0,
        global_exclusions: list[Project] | None = None,
        per_coord_exclusions: dict[Component, list[Project]] | None = None,
    ):
        self.context = context
        self.link_strategy = link_strategy
        self.optional_depth = optional_depth
        self.global_exclusions = global_exclusions or []
        self.per_coord_exclusions = per_coord_exclusions or {}
        # ... rest of initialization
```

## Complete Examples

### Example 1: Exclude Commons Logging Globally

**Problem:** Multiple dependencies pull in commons-logging, but you want to use slf4j.

**Solution:**

```bash
# Using inline syntax
jgo httpclient+spring-web+commons-logging:commons-logging(x)
```

### Example 2: Per-Coordinate Exclusions

**Problem:** Want different exclusions for different coordinates.

**Solution:**

```bash
# Exclude commons-logging from httpclient, log4j from spring-web
jgo httpclient(x:commons-logging:commons-logging)+spring-web(x:log4j:log4j)
```

### Example 3: Project with jgo.toml

**Setup:**

```toml
# jgo.toml
[environment]
name = "web-app"

[dependencies]
coordinates = [
    "org.springframework:spring-web:5.3.20(x:log4j:log4j)",
    "org.apache:httpclient:4.5.14",
]

# Global exclusion for commons-logging
exclusions = [
    "commons-logging:commons-logging"
]

[entrypoints]
default = "com.example.WebApp"
```

**Usage:**

```bash
# Initialize environment
jgo sync

# Run default entrypoint
jgo run

# Add another global exclusion
jgo exclude add org.slf4j:slf4j-log4j12

# List all exclusions
jgo exclude list
```

### Example 4: Shortcuts with Exclusions

**Setup:**

```ini
# ~/.config/jgo.conf
[shortcuts]
httpclient-clean = httpclient:4.5.14(x:commons-logging:commons-logging,x:commons-codec:commons-codec)
spring-minimal = spring-web:5.3.20(x:commons-logging:commons-logging,x:log4j:log4j)
```

**Usage:**

```bash
jgo httpclient-clean@org.example.HttpDemo
jgo spring-minimal+slf4j-simple@org.example.WebDemo
```

### Example 5: Complex Multi-Coordinate Setup

**Scenario:** Spring web app with LWJGL on module-path, excluding problematic logging libraries.

```bash
jgo 'spring-web:5.3.20(c,x:commons-logging:commons-logging,x:log4j:log4j)+lwjgl:3.3.1(m)+commons-logging:commons-logging(x)@WebApp'
```

**Breakdown:**
- `spring-web:5.3.20(c,x:commons-logging:commons-logging,x:log4j:log4j)` - Spring on classpath, excludes its commons-logging and log4j
- `lwjgl:3.3.1(m)` - LWJGL on module-path
- `commons-logging:commons-logging(x)` - Global exclusion marker for commons-logging
- `@WebApp` - Main class

## Benefits

1. **Resolves dependency conflicts**: Exclude problematic transitive dependencies
2. **Consistent with Maven**: Uses same exclusion semantics as Maven POMs
3. **Cache-aware**: Different exclusions create separate cached environments
4. **Composable**: Works seamlessly with existing jgo features (+, @, !, placement modifiers)
5. **Flexible**: Supports both global and per-coordinate exclusions
6. **Shortcut-compatible**: Exclusions can be embedded in shortcuts
7. **Simple**: One primary syntax (inline), with convenience command for jgo.toml

## Open Questions

### 1. Validation

**Question:** Should we validate that excluded dependencies actually exist in the resolved tree?

**Decision:** No validation (following Maven's approach).

**Rationale:**
- Maven doesn't validate exclusions
- Allows "defensive" exclusions that may not always be present
- Simpler implementation
- Avoids coupling exclusion spec to resolution results

### 2. Wildcard Exclusion Scope

**Question:** Should wildcards in per-coordinate exclusions (`coord(x:org.slf4j:*)`) apply transitively?

**Decision:** Yes, follow Maven semantics (wildcards apply transitively).

**Example:**
```
A depends on B depends on slf4j-simple
A(x:org.slf4j:*) excludes slf4j-simple even though it's transitive
```

### 3. jgo exclude --coordinate Feature

**Question:** Should `jgo exclude` support per-coordinate exclusions or only global?

**Options:**
- **Option A:** Only global exclusions (simpler)
- **Option B:** Support per-coordinate via `--coordinate` flag (more features)

**Recommendation:** Start with Option A (global only). Users can manually edit jgo.toml for per-coordinate exclusions. Add Option B later if demand exists.

## Implementation Checklist

### Phase 1: Core Parsing and Syntax

- [ ] Implement `parse_coordinate_modifiers()` with exclusion support
- [ ] Add wildcard support (`*` for groupId/artifactId)
- [ ] Handle combined modifiers (placement + exclusions)
- [ ] Ensure `!` raw flag processed after parenthetical
- [ ] Add unit tests for all parsing edge cases
- [ ] Test repeated `x:` modifiers work correctly

### Phase 2: Exclusion Integration

- [x] ✅ Extend `_cache_key()` to include exclusions (uses Dependency objects)
- [x] ✅ Update `_cache_key()` to include classifier and packaging (fixes LWJGL bug)
- [x] ✅ Add `_coordinates_to_dependencies()` helper method
- [x] ✅ Add `_components_to_dependencies()` compatibility helper
- [x] ✅ Update `from_components()` to accept optional coordinates parameter
- [x] ✅ Update `from_spec()` to preserve coordinates for cache key
- [x] ✅ Add tests for cache key with classifiers and packaging
- [ ] Update `EnvironmentBuilder` to accept global and per-coord exclusions
- [ ] Update `create_pom()` to propagate exclusions to dependencies
- [ ] Implement exclusion merging logic (global + per-coord)
- [ ] Add exclusion deduplication
- [ ] Update POM generation to include `<exclusions>` blocks

### Phase 3: jgo.toml Support

- [ ] Add `exclusions` field to TOML schema
- [ ] Parse global exclusions from `[dependencies] exclusions`
- [ ] Parse per-coordinate exclusions from inline syntax
- [ ] Update `jgo sync` to handle exclusions
- [ ] Update lockfile to record effective exclusions
- [ ] Add validation for exclusion coordinate format

### Phase 4: jgo exclude Command

- [ ] Implement `jgo exclude add` subcommand
- [ ] Implement `jgo exclude remove` subcommand
- [ ] Implement `jgo exclude list` subcommand
- [ ] Add `--file` option for custom jgo.toml paths
- [ ] Implement TOML loading and updating
- [ ] Add coordinate validation
- [ ] Add error handling (missing file, invalid TOML, etc.)
- [ ] Preserve TOML formatting where possible

### Phase 5: Testing

- [ ] Unit tests for `(x)` marker (global exclusion)
- [ ] Unit tests for repeated `x:` modifiers: `(x:excl1,x:excl2)`
- [ ] Unit tests for combined modifiers: `(c,x:...,x:...)`
- [ ] Unit tests for order independence
- [ ] Unit tests for wildcard exclusions
- [ ] Integration tests with real Maven artifacts
- [ ] Test shortcuts with exclusions
- [ ] Test jgo.toml with exclusions
- [ ] Test `jgo exclude` command operations
- [ ] Test cache key changes with exclusions

### Phase 6: Documentation

- [ ] Update README.md with exclusion examples
- [ ] Document exclusion syntax in user guide
- [ ] Add exclusion examples to cookbook
- [ ] Document jgo.toml exclusions field
- [ ] Document `jgo exclude` command
- [ ] Add migration guide for cache key changes
- [ ] Update grammar specification

## Alternatives Considered

### CLI Flags Only

**Proposal:** Use only `--exclude` flags without inline syntax.

```bash
jgo --exclude commons-logging:commons-logging httpclient
```

**Rejected because:**
- Cannot include exclusions in shortcuts (deal-breaker)
- Less flexible for per-coordinate exclusions
- Doesn't affect cache key naturally (needs special handling)
- Verbose when same exclusions needed repeatedly

### Special Character Syntax

**Proposal:** Use symbols like `~`, `^`, or `/` instead of `(x)`.

```bash
jgo httpclient~commons-logging:commons-logging  # tilde
jgo httpclient^commons-logging:commons-logging  # caret
jgo httpclient/commons-logging:commons-logging  # slash
```

**Rejected because:**
- `~` and `^` have version semantics in poetry
- Less self-documenting than `(x)`
- Harder to distinguish from coordinate body
- Shell escaping issues
- Inconsistent with existing `(...)` placement modifiers

### Multiple Separate Parentheticals

**Proposal:** Allow multiple parentheticals instead of unified syntax.

```bash
jgo httpclient(c)(x:excl1)(x:excl2)!
```

**Rejected because:**
- Order ambiguity (does `(c)` come before or after `(x:...)`?)
- More verbose
- Harder to parse (multiple passes)
- Less readable

### Configuration File Only

**Proposal:** Require jgo.toml for all exclusions.

**Rejected because:**
- Too heavyweight for quick one-off runs
- No support for shortcuts with exclusions
- Inconsistent with other jgo features
- Doesn't solve ad-hoc use cases

---

## Summary

This design provides a comprehensive, coherent exclusion system for jgo v2:

- **One primary syntax**: Inline `(x)` and `(x:...)` modifiers
- **Three access methods**: Direct inline, jgo.toml, jgo exclude command
- **Two exclusion scopes**: Global (apply everywhere) and per-coordinate (apply to one dependency)
- **Cache-aware**: Exclusions properly affect cache keys
- **Maven-compatible**: Semantics match Maven's `<exclusions>` blocks

The system is simple, composable, and consistent with jgo's existing design principles.

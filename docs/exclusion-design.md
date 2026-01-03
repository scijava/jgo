# Dependency Exclusion Feature Design

## Overview

Add CLI-based dependency exclusion support to jgo v2, allowing users to exclude specific transitive dependencies from the classpath.

## Motivation

Maven supports `<exclusions>` blocks within `<dependency>` elements. Users need a way to specify these exclusions when running Java applications via jgo, without creating a custom pom.xml file.

## Design Decisions

### Why CLI Flag (not inline syntax)?

jgo v2 already has other "dirty" CLI flags (like `--add-classpath`) that affect the cache key. Adding `--exclude` follows this established pattern and provides:
- Clearer syntax (no special character needed)
- Better shell compatibility (no escaping issues)
- Consistent with existing jgo v2 design
- Easy to implement (already have the infrastructure)

### Why not use special characters?

Considered characters for inline exclusion syntax:
- `!` - Already taken for raw/unmanaged marker (e.g., `g:a:v!`)
- `-` - Used heavily in GAVs (group-ids, artifact-ids)
- `~` - Could work, but CLI flag is cleaner
- `^` - Could work, but CLI flag is cleaner

## Proposed Design

### CLI Syntax

```bash
# Exclude single dependency
jgo --exclude commons-logging:commons-logging org.apache.httpcomponents:httpclient

# Exclude multiple dependencies
jgo -x commons-logging:commons-logging \
    -x log4j:log4j \
    org.springframework:spring-web

# Exclude with wildcards (Maven-style)
jgo --exclude '*:commons-logging' org.springframework:spring-web
jgo --exclude 'org.slf4j:*' com.example:my-app
```

### Flag Details

**Long form:** `--exclude COORDINATE`
**Short form:** `-x COORDINATE`
**Can be specified multiple times:** Yes
**Coordinate format:** `groupId:artifactId` (minimal form)
**Wildcard support:** `*` for groupId or artifactId (Maven standard)

### Technical Implementation

#### 1. CLI Option Addition

Add to relevant commands (run, info, init, etc.):

```python
@click.option(
    "--exclude", "-x",
    "exclusions",  # Store as list
    multiple=True,
    metavar="COORDINATE",
    help="Exclude dependency (format: groupId:artifactId or *:artifactId)",
)
```

#### 2. Exclusion Parsing

Parse exclusion coordinates:

```python
def parse_exclusion(coord: str) -> Project:
    """
    Parse exclusion coordinate string.

    Args:
        coord: Exclusion coordinate (e.g., "commons-logging:commons-logging" or "*:slf4j-api")

    Returns:
        Project object for exclusion

    Raises:
        ValueError: If coordinate format is invalid
    """
    parts = coord.split(":")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid exclusion coordinate '{coord}'. "
            "Expected format: groupId:artifactId"
        )

    groupId, artifactId = parts

    # Validate (Maven allows * wildcards)
    if not groupId or not artifactId:
        raise ValueError(f"Empty groupId or artifactId in exclusion '{coord}'")

    return Project(groupId=groupId, artifactId=artifactId, context=None)
```

#### 3. Cache Key Integration

Update `EnvironmentBuilder._cache_key()` to include exclusions:

```python
def _cache_key(self, components: list[Component], exclusions: list[Project] = None) -> str:
    """Generate a stable hash for a set of components and exclusions."""
    # Existing coordinate sorting
    coord_strings = sorted(
        [f"{c.groupId}:{c.artifactId}:{c.resolved_version}" for c in components]
    )
    combined = "+".join(coord_strings)

    # Include optional_depth
    combined += f":optional_depth={self.optional_depth}"

    # Include exclusions (NEW)
    if exclusions:
        exclusion_strings = sorted(
            [f"{e.groupId}:{e.artifactId}" for e in exclusions]
        )
        combined += f":exclusions={','.join(exclusion_strings)}"

    return hashlib.sha256(combined.encode()).hexdigest()[:16]
```

#### 4. Dependency Resolution Integration

Pass exclusions to the root-level dependencies in the synthetic POM:

```python
def create_pom_with_exclusions(
    components: list[Component],
    boms: list[Component] | None,
    exclusions: list[Project] | None = None
) -> POM:
    """
    Create a synthetic wrapper POM with dependency exclusions.

    Args:
        components: Components to include
        boms: BOM imports for dependency management
        exclusions: Global exclusions to apply to all dependencies
    """
    # Create dependencies with exclusions
    dependencies = []
    for comp in components:
        artifact = comp.artifact()
        dep = Dependency(
            artifact=artifact,
            scope="compile",
            exclusions=exclusions if exclusions else tuple()
        )
        dependencies.append(dep)

    # ... rest of POM creation
```

#### 5. Environment Builder Updates

Update `EnvironmentBuilder` to accept and propagate exclusions:

```python
class EnvironmentBuilder:
    def __init__(
        self,
        context: MavenContext,
        cache_dir: Path | None = None,
        link_strategy: LinkStrategy = LinkStrategy.AUTO,
        optional_depth: int = 0,
        exclusions: list[Project] | None = None,  # NEW
    ):
        self.context = context
        self.link_strategy = link_strategy
        self.optional_depth = optional_depth
        self.exclusions = exclusions or []  # NEW

        # ... rest of __init__
```

## Examples

### Example 1: Exclude Commons Logging

```bash
# Problem: httpclient depends on commons-logging, but you want to use slf4j
jgo --exclude commons-logging:commons-logging \
    org.apache.httpcomponents:httpclient:4.5.13 \
    -- -Xmx2G \
    -- org.example.MyApp
```

### Example 2: Exclude All SLF4J Implementations

```bash
# Keep slf4j-api but exclude all implementations (use your own)
jgo -x 'org.slf4j:slf4j-simple' \
    -x 'org.slf4j:slf4j-log4j12' \
    -x 'ch.qos.logback:*' \
    org.springframework:spring-web:5.3.20
```

### Example 3: Complex Exclusion Scenario

```bash
# Exclude multiple conflicting dependencies
jgo \
  --exclude 'commons-logging:commons-logging' \
  --exclude 'log4j:log4j' \
  --exclude 'org.slf4j:slf4j-log4j12' \
  org.springframework:spring-web:5.3.20+org.apache.httpcomponents:httpclient:4.5.13 \
  @org.example.WebApp
```

## Integration with jgo.toml

For project mode, add exclusions to the config file:

```toml
[environment]
name = "my-app"

[dependencies]
coordinates = [
    "org.springframework:spring-web:5.3.20",
    "org.apache.httpcomponents:httpclient:4.5.13"
]

# Global exclusions applied to all dependencies
exclusions = [
    "commons-logging:commons-logging",
    "log4j:log4j"
]
```

## Benefits

1. **Resolves dependency conflicts** - Users can exclude problematic transitive dependencies
2. **Consistent with Maven** - Uses same exclusion semantics as Maven POMs
3. **Cache-aware** - Different exclusions create separate cached environments
4. **Shell-friendly** - No special characters that need escaping
5. **Composable** - Works with all existing jgo features (+, @, !, etc.)

## Implementation Checklist

### Parsing
- [ ] Update `_parse_coordinate_dict()` to extract unified parenthetical
- [ ] Parse comma-separated modifiers within parenthetical
- [ ] Support `(x)` exclusion marker vs `(x:...)` exclusion list
- [ ] Handle placement modifiers in same parenthetical
- [ ] Ensure `!` raw flag is processed after parenthetical
- [ ] Add tests for parenthetical parsing

### CLI Integration
- [ ] Add `--exclude`/`-x` CLI option to run command
- [ ] Add to other relevant commands (info, init, etc.)
- [ ] Parse CLI exclusions into Project objects
- [ ] Update CLI help text

### Core Integration
- [ ] Update `_cache_key()` to include exclusions
- [ ] Update `create_pom()` to accept exclusions parameter
- [ ] Update `EnvironmentBuilder` to propagate exclusions
- [ ] Handle global exclusions (CLI + `(x)` markers)
- [ ] Handle per-coordinate exclusions `(x:...)`
- [ ] Merge all exclusion sources in dependency resolution

### Testing
- [ ] Test `(x)` marker (global exclusion)
- [ ] Test `(x:excl1,excl2)` list (per-coordinate)
- [ ] Test combined `(c,x:...)` modifiers
- [ ] Test order independence `(c,x:...)` vs `(x:...,c)`
- [ ] Test `!` after parenthetical
- [ ] Test shortcuts with exclusions
- [ ] Integration tests with real Maven artifacts

### Documentation
- [ ] Update README.md with examples
- [ ] Add to jgo.toml spec for project mode
- [ ] Document grammar in user guide

## Unified Parenthetical Syntax ⭐

**FINAL DESIGN:** Single parenthetical with comma-separated modifiers.

### Core Concept

All coordinate modifiers go in **one parenthetical block** with comma-separated values:
- Placement modifiers: `c`, `cp`, `m`, `mp`, `p` (existing)
- Exclusion marker: `(x)` - marks coordinate AS a global exclusion
- Exclusion list: `(x:excl1,excl2)` - coordinate HAS per-dependency exclusions
- Raw flag: `!` always comes **after** the parenthetical (termination symbol)

### Grammar

```
coordinate := G:A[:V][:C][:P] [modifiers] [!] [@mainClass]
modifiers  := '(' modifier [',' modifier]* ')'
modifier   := placement | exclusion-marker | exclusion-list
placement  := 'c' | 'cp' | 'm' | 'mp' | 'p'
exclusion-marker := 'x'                              # this coord IS an exclusion
exclusion-list   := 'x:' exclusion [',' exclusion]*  # this coord HAS exclusions
exclusion        := groupId ':' artifactId
```

### Two Meanings of `(x)`

**1. Exclusion Marker:** `coord(x)` - this coordinate **IS** a global exclusion

```bash
# Include httpclient, globally exclude commons-logging and log4j
jgo httpclient+commons-logging:commons-logging(x)+log4j:log4j(x)
```

**2. Exclusion List:** `coord(x:excl1,excl2)` - this coordinate **HAS** exclusions

```bash
# Include httpclient, but exclude commons-logging from its dependency tree
jgo httpclient(x:commons-logging:commons-logging,commons-codec:commons-codec)
```

### Combining Modifiers

Multiple modifiers in one parenthetical - **order doesn't matter**:

```bash
# Placement + exclusions
jgo httpclient(c,x:commons-logging:commons-logging)
jgo httpclient(x:commons-logging:commons-logging,c)  # same thing

# Multiple exclusions + placement + raw flag
jgo httpclient:4.5.14(c,x:commons-logging:commons-logging,commons-codec:commons-codec)!

# Module-path + exclusions
jgo lwjgl:3.3.1(m,x:lwjgl-opengl:lwjgl-opengl)
```

**Advantages:**
- ✅ **Single parenthetical** - no ambiguity about ordering
- ✅ **Comma-separated** - readable and familiar
- ✅ **Bang at end** - logical termination symbol
- ✅ **Order independent** - `(c,x:...)` = `(x:...,c)`
- ✅ **Extensible** - easy to add new modifiers

### Shortcuts Now Work!

```ini
[shortcuts]
# Per-coordinate exclusions
httpclient-clean = httpclient:4.5.14(x:commons-logging:commons-logging,commons-codec:commons-codec)
spring-clean = spring-web(x:commons-logging:commons-logging,log4j:log4j)

# Exclusions + placement
lwjgl-modular = lwjgl:3.3.1(m,x:lwjgl-opengl:lwjgl-opengl)

# Global exclusion markers (exclude these everywhere)
no-logging = httpclient+commons-logging:commons-logging(x)+log4j:log4j(x)
```

Then use:
```bash
jgo httpclient-clean
jgo spring-clean
jgo lwjgl-modular
jgo no-logging
```

### Three Ways to Specify Exclusions

**1. CLI Flag (global):**
```bash
jgo --exclude commons-logging:commons-logging httpclient
```

**2. Exclusion Marker `(x)` (global):**
```bash
jgo httpclient+commons-logging:commons-logging(x)
```

**3. Exclusion List `(x:...)` (per-coordinate):**
```bash
jgo httpclient(x:commons-logging:commons-logging)
```

All three can be **combined**:

```bash
# CLI global + marker + per-coordinate
jgo --exclude 'org.slf4j:slf4j-log4j12' \
    'httpclient(x:commons-logging:commons-logging)+log4j:log4j(x)'
```

**Semantics:**
- CLI `--exclude` → global exclusion
- Coordinate `(x)` → global exclusion marker
- Coordinate `(x:...)` → per-coordinate exclusion
- All are merged in dependency resolution

### Parsing Implementation

Parse **single parenthetical** with comma-separated modifiers:

```python
def parse_coordinate_modifiers(coordinate: str) -> tuple[str, dict]:
    """
    Parse unified parenthetical modifiers.

    Returns: (coordinate_without_modifiers, modifiers_dict)
    """
    modifiers = {
        'placement': None,
        'exclusions': [],
        'is_exclusion': False,
        'raw': False
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

                # Exclusion marker
                elif modifier == 'x':
                    modifiers['is_exclusion'] = True

                # Exclusion list
                elif modifier.startswith('x:'):
                    excl_str = modifier[2:]  # Strip 'x:'
                    for excl in excl_str.split(','):
                        excl = excl.strip()
                        parts = excl.split(':')
                        if len(parts) >= 2:
                            modifiers['exclusions'].append(
                                Project(groupId=parts[0], artifactId=parts[1])
                            )

    return coordinate, modifiers
```

**Parsing order:**
1. Strip `!` raw flag (if present) - **always last**
2. Extract single `(...)` parenthetical
3. Parse comma-separated modifiers (order independent)
4. Parse coordinate components (G:A:V:C:P)
5. Merge with global `--exclude` CLI flags

### Comprehensive Examples

**Example 1: Shortcut with per-coordinate exclusions**
```ini
[shortcuts]
httpclient = httpclient:4.5.14(x:commons-logging:commons-logging,commons-codec:commons-codec)
spring = spring-web:5.3.20(x:commons-logging:commons-logging,log4j:log4j)
```

**Example 2: Shortcut with placement + exclusions**
```ini
[shortcuts]
# Single parenthetical with both modifiers
lwjgl = lwjgl:3.3.1(m,x:lwjgl-opengl:lwjgl-opengl)
```

**Example 3: Global exclusion markers**
```bash
# Include httpclient, but globally exclude commons-logging and log4j
jgo httpclient:4.5.14+commons-logging:commons-logging(x)+log4j:log4j(x)
```

**Example 4: Mixed exclusions + placement + raw + main class**
```bash
# Per-coordinate exclusion + placement + raw flag + main class
jgo 'httpclient:4.5.14(c,x:commons-logging:commons-logging,commons-codec:commons-codec)!+lwjgl:3.3.1(m)@MyApp'
```

**Example 5: All three exclusion methods combined**
```bash
# CLI global + marker + per-coordinate
jgo --exclude 'org.slf4j:slf4j-log4j12' \
    'httpclient(x:commons-logging:commons-logging)+log4j:log4j(x)'
```

**Example 6: Complex real-world scenario**
```bash
# Spring web app with modular LWJGL, excluding problematic logging libs
jgo --exclude 'commons-logging:commons-logging' \
    'spring-web:5.3.20(c)+lwjgl:3.3.1(m,x:lwjgl-opengl:lwjgl-opengl)+log4j:log4j(x)@WebApp'
```

**Example 7: Order independence**
```bash
# These are equivalent:
jgo 'httpclient(c,x:commons-logging:commons-logging)'
jgo 'httpclient(x:commons-logging:commons-logging,c)'
```

## Open Questions

1. **Scope of exclusions** - Should exclusions apply globally to all components, or per-component?
   - **Decision:** Support BOTH via hybrid approach (CLI for global, inline for per-coordinate)

2. **Validation** - Should we validate that excluded dependencies actually exist in the tree?
   - **Decision:** No validation (Maven doesn't validate either, makes it more flexible)

3. **Exclusion syntax** - Use `~`, `^`, or parenthetical?
   - **Decision:** Unified parenthetical `(modifier,modifier,...)` - consistent with existing placement suffixes

4. **Multiple exclusions format** - How to specify multiple exclusions?
   - **Decision:** Comma-separated within `x:` prefix: `coord(x:excl1,excl2,excl3)`

5. **Multiple parentheticals vs. single** - Allow `(c)(x:...)` or require single `(c,x:...)`?
   - **Decision:** Single parenthetical only - simpler parsing, no ordering ambiguity

6. **Bang position** - Before or after parenthetical?
   - **Decision:** After - logical termination symbol: `coord(modifiers)!`

7. **Two meanings for (x)** - Support both marker and list?
   - **Decision:** Yes! `(x)` = global marker, `(x:...)` = per-coordinate exclusions

## Alternatives Considered

### Inline Syntax with ~ or ^

```bash
# With ~
jgo 'org.apache.httpcomponents:httpclient~commons-logging:commons-logging'

# With ^
jgo 'org.apache.httpcomponents:httpclient^commons-logging:commons-logging'
```

**Rejected because:**
- Less consistent with existing jgo v2 syntax
- Harder to distinguish from coordinate body
- More potential for shell escaping issues
- `(x:...)` suffix is more self-documenting

### CLI Flags Only (Original Design)

Use only `--exclude` flag without inline syntax.

**Rejected because:**
- **Shortcuts cannot include exclusions** (deal-breaker!)
- Less flexible for per-coordinate exclusions
- Verbose when same exclusions needed repeatedly

### Multiple Separate Parentheticals

Allow `coord(c)(x:excl1)(x:excl2)!` instead of unified syntax.

**Rejected because:**
- Order ambiguity - should `(c)` come before or after `(x:...)`?
- More characters to type
- Harder to parse (multiple suffix passes)
- Less readable

### Configuration File Only

Require users to create jgo.toml for exclusions.

**Rejected because:**
- Too heavyweight for quick one-off runs
- Inconsistent with existing --add-classpath pattern
- Doesn't solve the ad-hoc use case

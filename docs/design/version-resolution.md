# Version Resolution: LATEST and RELEASE

This document explains how jgo resolves `LATEST` and `RELEASE` version specifiers, how this differs from Maven's behavior, and why.

## Background: Maven's Behavior

When you specify a dependency version as `RELEASE` or `LATEST`, Maven needs to determine which concrete version to use. Maven does this by:

1. Fetching `maven-metadata.xml` from each configured repository
2. Each metadata file contains a `<release>` and `<latest>` tag indicating the newest versions **in that repository**
3. Maven uses the values from the **most recently updated** metadata file (based on `<lastUpdated>` timestamp)

### The Problem

This approach has a critical limitation when artifacts are deployed to multiple repositories:

**Example: net.imagej:ij**
- Versions 1.48c through 1.54p deployed to **Maven Central** (last update: 2025-02-18)
- Versions 1.23y through 1.48q deployed to **maven.scijava.org** (last update: 2025-12-22)
- Maven selects **1.48q** as `RELEASE` because maven.scijava.org was updated more recently
- But **1.54p is actually the newest release**!

This happens because:
- The maven.scijava.org metadata was updated recently (with a SNAPSHOT build)
- Its `<release>` tag correctly says `1.48q` (the newest release **in that repo**)
- Maven doesn't compare version numbers across repositories

## jgo's Approach

jgo improves on Maven's behavior while maintaining a clear separation of concerns:

### Data Layer: Maven-Compatible

The `Metadata` and `Metadatas` classes faithfully reflect Maven's behavior:
- `Metadata.release`: Returns the `<release>` tag from the XML
- `Metadata.latest`: Returns the `<latest>` tag from the XML
- `Metadatas.release`: Returns `release` from the most recently updated metadata
- `Metadatas.latest`: Returns `latest` from the most recently updated metadata

This ensures the data layer is a faithful representation of the Maven repository metadata, with no heuristics or workarounds applied.

### Business Logic Layer: Smart Resolution

The `Project` class implements intelligent version resolution:

#### `Project.release` - Newest Release Across All Repositories

**Algorithm:**
1. Collect all versions from all configured repositories
2. Filter out SNAPSHOT versions (those ending in `-SNAPSHOT`)
3. Use Maven version comparison to find the truly newest version
4. Return that version

**Result:** For net.imagej:ij, correctly returns `1.54p` instead of `1.48q`.

**Deviation from Maven:** Yes, but in a way that prioritizes correctness. Maven has the same bug; jgo fixes it.

#### `Project.latest` - Highest Version (Including SNAPSHOTs)

**Algorithm:**
1. Collect all versions from all configured repositories
2. Use Maven version comparison to find the highest version
3. Unlike `release`, this **includes SNAPSHOT versions**

**Rationale:**
`LATEST` means "highest version number", not "most recently deployed". This is critical for correct multi-branch development:

Example scenario:
- Main branch: `2.4.0-SNAPSHOT` (deployed 2025-12-28)
- Maintenance branch: `1.23.4-SNAPSHOT` (deployed 2025-12-30)
- Expected: `2.4.0-SNAPSHOT` (highest version, represents current development)
- If using temporal ordering: Would ping-pong between branches based on commit timing ❌

**Limitation:**
Projects using unconventional SNAPSHOT naming schemes cannot be handled correctly:

Example: net.imagej:ij always uses `1.x-SNAPSHOT` for all development builds
- `1.54p` is the newest release (Maven Central, 2025-02-18)
- `1.x-SNAPSHOT` is current development (maven.scijava.org, 2025-12-22)
- Version comparison: `1.x-SNAPSHOT` < `1.54p` (due to qualifier ordering)
- jgo returns: `1.54p` (highest version by Maven ordering)
- Expected by project: `1.x-SNAPSHOT` (most recent development build)
- **This is unavoidable** - version comparison cannot infer temporal relationships

**Result:** For most projects, returns the expected highest version. For net.imagej:ij specifically, returns `1.54p` instead of `1.x-SNAPSHOT` due to unconventional versioning.

**Deviation from Maven:** Yes, same as `release` - compares versions across all repositories instead of using most recently updated repo.

## Rationale for Deviation

jgo deviates from Maven's behavior for `RELEASE` resolution because:

1. **Correctness**: Maven's behavior is objectively wrong when dealing with multiple repositories
2. **Predictability**: Users expect `RELEASE` to mean "newest release version", not "newest release from whichever repo happened to be updated recently"
3. **Precedent**: jgo already deviates from Maven with "managed by default" behavior
4. **Minimal surprise**: The deviation only matters for projects split across multiple repos, and it fixes a bug rather than introducing new behavior

## Principle of Least Astonishment (PoLA)

While jgo deviates from Maven, we argue this actually **improves** PoLA:

- **Maven's behavior is astonishing**: Getting version 1.48q when 1.54p exists is surprising
- **jgo's behavior is intuitive**: Getting the newest version is what users expect
- **Well-documented**: This document, plus docstrings, explain the nuances
- **Testable**: `jgo info versions` clearly shows which version is marked as `(release)`

## How to Check Which Version Will Be Used

```bash
# Show all versions with markers
jgo info versions <groupId>:<artifactId>

# The version marked (release) is what RELEASE resolves to
# The version marked (latest) is what LATEST resolves to
```

## Implementation Details

See the source code for implementation:
- `src/jgo/maven/metadata.py`: Data layer (Maven-compatible)
- `src/jgo/maven/core.py`: `Project` class with smart resolution
- `src/jgo/cli/commands/versions.py`: Uses `Project` resolution for display

## References

- Maven Version Order Specification: https://maven.apache.org/pom.html#version-order-specification
- Maven Metadata XML format: https://maven.apache.org/ref/current/maven-repository-metadata/

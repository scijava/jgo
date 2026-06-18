# Proposal: distinguish artifact *type* from *packaging* and *extension*

Status: design note (not yet implemented)
Target version: `4.0.0.dev0` (breaking public API change)

## Summary

jgo's `Artifact` collapses three distinct Maven concepts into a single
`packaging` field, then uses that field *directly* as the file extension when
building filenames and download URLs. This is correct only for the cases where
the type name happens to equal the file extension (`jar`, `pom`, `war`, `ear`).
It is wrong for `maven-plugin`, `bundle`, `test-jar`, `ejb`, `ejb-client`,
`java-source`, and `javadoc`, where the on-disk extension is something else
(usually `jar`) and several of them also imply a classifier.

The fix is to model Maven's **artifact handler** concept: a *type* resolves to
an *(extension, classifier)* pair. Concretely:

1. Rename `Artifact.packaging` → `Artifact.type` (the dependency *type* being
   requested; default `jar`).
2. Add a type → `(extension, classifier)` handler table.
3. Derive the filename/URL extension (and any implied classifier) through the
   handler instead of using the raw type string.

Because this renames a widely used public attribute, it is a breaking change and
should bump the version to `4.0.0.dev0`.

## Background: three Maven concepts, correct nomenclature

These are genuinely different and must not be conflated:

- **Component `<packaging>`** — declared once in a project's POM (default
  `jar`). A *component-level* fact. It selects the build lifecycle and declares
  what the component's **primary artifact** is — or that there is none
  (`<packaging>pom</packaging>`, e.g. an aggregator/BOM, publishes only a
  `.pom`). Example values: `jar`, `bundle`, `maven-plugin`, `pom`, `war`, `ear`.

- **Dependency `<type>`** — declared on a *dependency reference*
  (`<dependency><type>…`), default `jar`. It selects *which* artifact of the
  target component to resolve. This is a *per-reference* fact, not a property of
  the component.

- **Artifact extension + classifier** — what actually names the file on disk
  (`foo-1.0.jar`, `foo-1.0-tests.jar`, `foo-1.0.pom`).

Maven maps *type* (and, for a component's primary artifact, *packaging*) to
*(extension, classifier)* via an **`ArtifactHandler`**. The standard handlers:

| type / packaging | extension | implied classifier |
| ---------------- | --------- | ------------------ |
| `jar`            | `jar`     | —                  |
| `pom`            | `pom`     | —                  |
| `war`            | `war`     | —                  |
| `ear`            | `ear`     | —                  |
| `rar`            | `rar`     | —                  |
| `maven-plugin`   | `jar`     | —                  |
| `bundle`         | `jar`     | —                  |
| `ejb`            | `jar`     | —                  |
| `ejb-client`     | `jar`     | `client`           |
| `test-jar`       | `jar`     | `tests`            |
| `java-source`    | `jar`     | `sources`          |
| `javadoc`        | `jar`     | `javadoc`          |

Key takeaway: **type ≠ extension**. Only the identity rows
(`jar`/`pom`/`war`/`ear`/`rar`) coincide.

## The bug in jgo today

The data model already names the levels correctly in prose
(`src/jgo/maven/_core.py:14-19`):

```
- Component [G:A:V]: A Project at a specific version (V)
- Artifact [G:A:P:C:V]: One file of a Component, with classifier (C) and packaging (P)
- Dependency [G:A:P:C:V:S]: An Artifact with scope, optional flag, and exclusions
```

…but the `P` slot is used as the literal file extension:

- `src/jgo/maven/_pom.py:54` — `packaging = _text(el, "type")`: a dependency's
  `<type>` element is read straight into the `packaging` field. So `type` and
  "packaging" are already the same value here; the field is mis-named.
- `src/jgo/maven/_core.py:864` and `:877` — `filename` / `cached_filename`
  return `f"{artifactId}-{version}{-classifier}.{self.packaging}"`, i.e. the
  type string is used *as the extension*.
- `src/jgo/maven/_core.py:1029` — the resolver URL passes
  `&maven.extension={self.packaging}`.
- `src/jgo/maven/_core.py:858` → `src/jgo/maven/_metadata.py:135,152` —
  `get_timestamped_version(packaging=…, classifier=…)` compares the
  maven-metadata `<extension>` against `packaging`. For a `test-jar` the
  metadata records `extension=jar, classifier=tests`, so a lookup keyed on
  `packaging=test-jar` can never match.

### Why it mostly works anyway

Callers request a component's **primary** artifact with the default
`packaging="jar"` (`DEFAULT_PACKAGING`, `src/jgo/maven/_core.py:60`). The primary
file of a `bundle`- or `maven-plugin`-packaged component genuinely *is*
`foo-1.0.jar`, so asking for `jar` yields the right filename even though the
component's packaging is bundle/plugin. The breakage only surfaces when an
`Artifact`'s type is set to a non-identity value — e.g. resolving a
`<type>test-jar</type>` or `<type>maven-plugin</type>` dependency — at which
point the computed extension (and, for `test-jar`, the missing `tests`
classifier) is wrong and resolution fails.

## Proposed implementation

### 1. Rename and re-document

- `Artifact.packaging` → `Artifact.type` (default `jar`). Update `__init__`,
  `__eq__`, `__hash__`, `key`, `__str__`, and the class docstring
  (`G:A:P:C:V` → `G:A:T:C:V`; "packaging (P)" → "type (T)").
- `Component.artifact(classifier, packaging=…)` → `…, type=…`
  (`src/jgo/maven/_core.py:742-756`).
- `DEFAULT_PACKAGING` → `DEFAULT_TYPE` (`src/jgo/maven/_core.py:60`; used at
  `:203`, `:780`, `:743`, …).
- `Dependency.type` (`src/jgo/maven/_core.py:1105-1107`) now delegates to
  `self.artifact.type`; drop the "packaging/type" wording in favor of "type".
- `src/jgo/maven/_pom.py:54` — store into the `type` field; keep the default of
  `jar` when `<type>` is absent.
- Update the module data-model docstring (`_core.py:14-19`) and `parse`
  coordinate docs/fields (`src/jgo/parse/_coordinate.py:56-76`, `coord2str` at
  `:258`), where `P` in `G:A:P:C:V` is really the *type*.

### 2. Add an artifact-handler table

A small, data-driven mapping (e.g. in `src/jgo/maven/_core.py` or a new
`src/jgo/maven/_handlers.py`):

```python
# type -> (extension, implied_classifier)
ARTIFACT_HANDLERS: dict[str, tuple[str, str]] = {
    "jar": ("jar", ""),
    "pom": ("pom", ""),
    "war": ("war", ""),
    "ear": ("ear", ""),
    "rar": ("rar", ""),
    "maven-plugin": ("jar", ""),
    "bundle": ("jar", ""),
    "ejb": ("jar", ""),
    "ejb-client": ("jar", "client"),
    "test-jar": ("jar", "tests"),
    "java-source": ("jar", "sources"),
    "javadoc": ("jar", "javadoc"),
}

def handler_for(type_: str) -> tuple[str, str]:
    # Unknown types fall back to "extension == type" (current behavior),
    # so custom packagings keep resolving as before.
    return ARTIFACT_HANDLERS.get(type_, (type_, ""))
```

The unknown-type fallback (`extension == type`) preserves today's behavior for
any custom packaging not in the table, so the change is forward-compatible.

### 3. Derive extension + effective classifier from the handler

Add helper properties on `Artifact` and route filename/URL building through
them:

```python
@property
def extension(self) -> str:
    return handler_for(self.type)[0]

@property
def effective_classifier(self) -> str:
    # An explicit classifier wins; otherwise use the handler's implied one.
    return self.classifier or handler_for(self.type)[1]
```

Then:

- `filename` / `cached_filename` (`_core.py:864,877`) use `self.extension` and
  `self.effective_classifier`.
- The resolver URL (`_core.py:1029`) uses `maven.extension={self.extension}`.
- `get_timestamped_version(...)` (`_core.py:858` →
  `_metadata.py:135,152`) is called with `extension=self.extension` and
  `classifier=self.effective_classifier`, and its parameter is renamed
  `packaging` → `extension` to match what it actually compares against.

**Classifier precedence.** Explicit classifier takes precedence over the
handler's implied one. Note that `(type=test-jar)` and
`(type=jar, classifier=tests)` denote the *same* file
(`foo-1.0-tests.jar`); both should resolve identically. If both an explicit
classifier and an implied one are present and differ, prefer the explicit value
(optionally log at debug).

## Affected files

`grep -rn "packaging\|DEFAULT_PACKAGING" src/jgo` currently reports ~112 hits
across 17 files. The semantically important ones:

- `src/jgo/maven/_core.py` — `Artifact`, `Component.artifact`, `Dependency.type`,
  `DEFAULT_PACKAGING`, filename/URL building, model docstring.
- `src/jgo/maven/_pom.py` — reads `<type>` into the field.
- `src/jgo/maven/_metadata.py` — SNAPSHOT timestamp lookup by extension+classifier.
- `src/jgo/maven/_model.py`, `_resolver.py` — propagation.
- `src/jgo/parse/_coordinate.py`, `_endpoint.py` — `Coordinate.packaging`,
  `coord2str`, the `G:A:P:C:V` parsing/format and its docstrings.
- CLI/help/formatting and env modules: `src/jgo/cli/_parser.py`,
  `src/jgo/cli/_commands/{run,search,info}.py`, `src/jgo/cli/rich/_formatters.py`,
  `src/jgo/styles.py`, `src/jgo/env/{_lockfile,_javaversion,_builder}.py`,
  `src/jgo/maven/__init__.py` (re-exports).

The user-facing coordinate grammar `G:A:P:C:V` keeps the same *positions*; only
the nomenclature changes (the third placement is the *type*). No coordinate
string the user types needs to change.

## Backward compatibility

This renames a public attribute (`Artifact.packaging`) and a public constant
(`DEFAULT_PACKAGING`), hence the major bump.

Optional softening (decide at implementation time):

- Keep a deprecated `Artifact.packaging` property that returns `self.type` and
  emits `DeprecationWarning`, removed in a later release.
- Keep `DEFAULT_PACKAGING = DEFAULT_TYPE` as a deprecated alias.
- Accept a `packaging=` keyword in `Component.artifact(...)` as a deprecated
  alias for `type=`.

If we prefer a clean break (simpler, and 4.0 justifies it), drop the aliases and
document the rename in `docs/migration.md` + `docs/changelog.md`.

## Out of scope (possible follow-up)

- **Track `Component.packaging`.** jgo does not currently read a component's own
  POM `<packaging>`. Adding it would let jgo answer "does this component publish
  a primary jar at all?" and, for `pom`-packaged components, avoid even
  attempting a `.jar` resolution (which 404s today). Not required for the
  type/extension fix; the handler table is the core correctness piece.

## Versioning

Bump `pyproject.toml` `version` from `3.2.0.dev0` to `4.0.0.dev0` (breaking
public API change: `Artifact.packaging` → `Artifact.type`, `DEFAULT_PACKAGING` →
`DEFAULT_TYPE`, `Component.artifact(packaging=…)` → `type=…`).

## Testing

- Unit tests asserting `handler_for` mappings, and `Artifact.filename` /
  `cached_filename` / `extension` / `effective_classifier` for representative
  types: `jar`, `pom`, `test-jar` (→ `*-tests.jar`), `maven-plugin` (→ `*.jar`),
  `bundle` (→ `*.jar`), and a sources/javadoc classifier artifact.
- A SNAPSHOT metadata test that resolves a `test-jar` timestamped filename
  (extension `jar`, classifier `tests`).
- An unknown-type test asserting the `extension == type` fallback.
- Regression: existing `jar`/`pom` resolution paths unchanged.

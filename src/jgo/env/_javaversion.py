"""Cached per-artifact minimum-Java-version detection.

Scanning a JAR's class files to determine the minimum Java version it requires
is relatively expensive, and the same artifacts recur across many resolutions
(and across repeated runs of tools built on jgo). This module memoizes the
result both in-process and on disk.

The on-disk cache is deliberately kept *separate* from the richer JPMS metadata
cache in :mod:`jgo.env._cache` (which also stores module info and JAR-type
classification). That metadata feeds environment building, where an imprecise
value can send a JAR to the wrong path; keeping the bytecode-only lookup in its
own cache means a lightweight caller that only wants a Java version can never
degrade the classification data env building relies on.

Disk cache layout::

    <cache>/info/<groupId>/<artifactId>/<version>/<filename>.java-version.json
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from ..constants import default_jgo_cache
from ._bytecode import detect_jar_java_version, round_to_lts
from ._lockfile import compute_sha256

if TYPE_CHECKING:
    from ..maven import Artifact

_log = logging.getLogger(__name__)

# Cache format version - increment when the schema changes.
_CACHE_FORMAT_VERSION = 1

# In-process memo keyed by (resolved jar path, round flag). Within a single run a
# resolved path's contents are stable, so this avoids even re-hashing the JAR on
# repeat lookups of the same artifact across many dependency closures.
_MEMO: dict[tuple[str, bool], int | None] = {}


def jar_java_version(
    artifact: Artifact,
    cache_dir: Path | None = None,
    *,
    round_to_lts_version: bool = False,
) -> int | None:
    """Return the minimum Java version required by an artifact's JAR.

    Resolves the artifact (downloading if necessary), then returns the highest
    class-file bytecode version among its classes expressed as a Java feature
    version (e.g. 8, 11, 17). The raw result is cached on disk keyed by the
    JAR's SHA-256 and memoized in-process, so repeat lookups are cheap.

    Args:
        artifact: The Maven artifact to inspect (JAR packaging expected).
        cache_dir: Base jgo cache directory. Defaults to
            :func:`jgo.constants.default_jgo_cache`.
        round_to_lts_version: If True, round the result up to the nearest LTS
            (8, 11, 17, 21). The cache stores the un-rounded value, so the same
            entry serves rounded and un-rounded callers.

    Returns:
        The minimum Java version, or None if the JAR cannot be resolved or
        contains no class files.
    """
    if cache_dir is None:
        cache_dir = default_jgo_cache()

    try:
        jar_path = artifact.resolve()
    except Exception:
        _log.debug("Could not resolve artifact %s", artifact)
        return None
    if jar_path is None or not jar_path.exists():
        return None

    memo_key = (str(jar_path), round_to_lts_version)
    if memo_key in _MEMO:
        return _MEMO[memo_key]

    sha256 = compute_sha256(jar_path)
    found, raw = _read(artifact, cache_dir, sha256)
    if not found:
        raw = detect_jar_java_version(jar_path, round_to_lts_version=False)
        _write(artifact, cache_dir, sha256, raw)

    result = round_to_lts(raw) if (raw is not None and round_to_lts_version) else raw
    _MEMO[memo_key] = result
    return result


def _cache_path(artifact: Artifact, cache_dir: Path) -> Path:
    group_path = Path(*artifact.groupId.split("."))
    return (
        cache_dir
        / "info"
        / group_path
        / artifact.artifactId
        / artifact.version
        / f"{artifact.filename}.java-version.json"
    )


def _read(artifact: Artifact, cache_dir: Path, sha256: str) -> tuple[bool, int | None]:
    """Return ``(found, raw_min_java_version)`` for a valid, matching cache entry.

    ``found`` is False when no entry exists or it is stale/corrupt; callers must
    use it to distinguish a miss from a cached value of None.
    """
    path = _cache_path(artifact, cache_dir)
    if not path.exists():
        return False, None
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return False, None
    if data.get("version") != _CACHE_FORMAT_VERSION or data.get("sha256") != sha256:
        return False, None
    return True, data.get("min_java_version")


def _write(
    artifact: Artifact, cache_dir: Path, sha256: str, min_java_version: int | None
) -> None:
    path = _cache_path(artifact, cache_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": _CACHE_FORMAT_VERSION,
        "sha256": sha256,
        "min_java_version": min_java_version,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        path.write_text(json.dumps(payload, indent=2))
    except OSError as e:
        _log.warning("Could not write java-version cache to %s: %s", path, e)

"""
Artifact metadata caching for jgo.

Caches analyzed metadata about JAR files to avoid repeated expensive operations:
- JAR type classification (1-4 for JPMS compatibility)
- Module information (module-info.class or Automatic-Module-Name)
- Minimum Java version requirements

Cache structure: ~/.cache/jgo/info/<groupId>/<artifactId>/<version>/<filename>.json
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from ._jar import JarType, ModuleInfo

# Cache format version - increment when schema changes
CACHE_FORMAT_VERSION = 2


@dataclass
class ArtifactMetadata:
    """Cached metadata about a JAR artifact."""

    version: int  # Cache format version
    sha256: str  # SHA256 hash of the JAR file
    analyzed_at: str  # ISO 8601 timestamp
    jar_type: JarType | None  # JPMS classification, or None if not analyzed
    min_java_version: int | None  # Minimum Java version, or None
    module_info: dict[str, object]  # ModuleInfo as dict


def get_cache_path(
    groupId: str,
    artifactId: str,
    version: str,
    filename: str,
    cache_dir: Path,
) -> Path:
    """
    Get the cache file path for an artifact.

    Args:
        groupId: Maven groupId (e.g., "org.example")
        artifactId: Maven artifactId (e.g., "foo")
        version: Version string (e.g., "1.0.0")
        filename: JAR filename (e.g., "foo-1.0.0.jar")
        cache_dir: Base cache directory (e.g., ~/.cache/jgo)

    Returns:
        Path to cache file: cache_dir/info/org/example/foo/1.0.0/foo-1.0.0.jar.json
    """
    # Convert groupId to path segments (e.g., "org.example" -> "org/example")
    group_path = Path(*groupId.split("."))
    return cache_dir / "info" / group_path / artifactId / version / f"{filename}.json"


def read_metadata_cache(
    groupId: str,
    artifactId: str,
    version: str,
    filename: str,
    cache_dir: Path,
) -> ArtifactMetadata | None:
    """
    Read cached metadata for an artifact.

    Args:
        groupId: Maven groupId
        artifactId: Maven artifactId
        version: Version string
        filename: JAR filename
        cache_dir: Base cache directory

    Returns:
        ArtifactMetadata if cache exists and is readable, None otherwise
    """
    cache_path = get_cache_path(groupId, artifactId, version, filename, cache_dir)

    if not cache_path.exists():
        return None

    try:
        with open(cache_path) as f:
            data = json.load(f)

        # Validate cache format version
        if data.get("version") != CACHE_FORMAT_VERSION:
            return None

        raw_jar_type = data.get("jar_type")
        return ArtifactMetadata(
            version=data["version"],
            sha256=data["sha256"],
            analyzed_at=data["analyzed_at"],
            jar_type=JarType(raw_jar_type) if raw_jar_type is not None else None,
            min_java_version=data.get("min_java_version"),
            module_info=data["module_info"],
        )
    except (json.JSONDecodeError, KeyError, OSError):
        # Invalid or corrupted cache file
        return None


def write_metadata_cache(
    groupId: str,
    artifactId: str,
    version: str,
    filename: str,
    cache_dir: Path,
    sha256: str,
    jar_type: JarType | None,
    min_java_version: int | None,
    module_info: ModuleInfo,
) -> None:
    """
    Write metadata to cache.

    Args:
        groupId: Maven groupId
        artifactId: Maven artifactId
        version: Version string
        filename: JAR filename
        cache_dir: Base cache directory
        sha256: SHA256 hash of the JAR
        jar_type: JPMS classification or None
        min_java_version: Minimum Java version or None
        module_info: Module information
    """
    cache_path = get_cache_path(groupId, artifactId, version, filename, cache_dir)

    # Create cache directory if needed
    cache_path.parent.mkdir(parents=True, exist_ok=True)

    metadata = ArtifactMetadata(
        version=CACHE_FORMAT_VERSION,
        sha256=sha256,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
        jar_type=jar_type,
        min_java_version=min_java_version,
        module_info=asdict(module_info),
    )

    try:
        with open(cache_path, "w") as f:
            json.dump(asdict(metadata), f, indent=2)
    except OSError:
        # Silently fail if we can't write cache - not critical
        pass


def is_cache_valid(cached: ArtifactMetadata, current_sha256: str) -> bool:
    """
    Check if cached metadata is valid for the current artifact.

    Args:
        cached: Cached metadata
        current_sha256: Current SHA256 hash of the JAR

    Returns:
        True if cache is valid (SHA256 matches), False otherwise
    """
    return cached.sha256 == current_sha256

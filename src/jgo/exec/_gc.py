"""
Garbage-collector-related functionality for jgo, including smart GC defaults and normalization.

Provides version-aware garbage collector selection and shorthand normalization.
"""

from __future__ import annotations

import logging
from difflib import get_close_matches
from typing import Literal

_log = logging.getLogger(__name__)


def get_default_gc_options(java_version: int) -> list[str]:
    """
    Get recommended GC options for a given Java version.

    GC Evolution:
    - Java 6-7: ParallelGC is safest
    - Java 8: G1GC available and stable
    - Java 9+: G1GC is default (but explicit flag ensures predictability)
    - Java 15+: ZGC production-ready (but we stick with G1GC for compatibility)
    - Java 21+: Generational ZGC available (but we stick with G1GC for compatibility)

    We use G1GC for Java 8+ because:
    - Lower pause times than ParallelGC
    - Predictable behavior across versions
    - Good balance of throughput and latency
    - Default in Java 9+ anyway

    Args:
        java_version: Java major version (e.g., 8, 11, 17, 21)

    Returns:
        List of GC flags to use
    """
    if java_version >= 9:
        # G1GC is already default, but explicit flag ensures predictability
        # and makes behavior consistent across versions
        return ["-XX:+UseG1GC"]
    elif java_version == 8:
        # G1GC stable but not default, safe to enable
        return ["-XX:+UseG1GC"]
    elif java_version >= 6:
        # G1GC experimental in Java 7, use ParallelGC for stability
        return ["-XX:+UseParallelGC"]
    else:
        # Very old Java (pre-6), ParallelGC safest bet
        return ["-XX:+UseParallelGC"]


# Known GC collectors (for validation and suggestions)
KNOWN_GCS = {
    "g1",
    "parallel",
    "serial",
    "z",
    "zgc",
    "cms",
    "concmarksweep",
    "shenandoah",
    "epsilon",
}

# Mapping from shorthand to proper GC name
GC_NAME_MAP = {
    "g1": "G1",
    "parallel": "Parallel",
    "serial": "Serial",
    "cms": "ConcMarkSweep",
    "concmarksweep": "ConcMarkSweep",
    "z": "Z",
    "zgc": "Z",
    "shenandoah": "Shenandoah",
    "epsilon": "Epsilon",
}


def normalize_gc_flag(value: str) -> str | None | Literal["auto"]:
    """
    Convert GC shorthand to full JVM flag.

    Supported formats:
      - Shorthand: G1, Parallel, Z, etc. → -XX:+UseG1GC
      - Explicit: -XX:+UseG1GC → -XX:+UseG1GC (pass through)
      - Special: "none" → None (disable GC flags)
      - Special: "auto" → "auto" (use smart defaults)

    Unknown shorthands trigger a warning but are passed through for
    future-proofing (e.g., new GCs in future Java versions).

    Args:
        value: GC shorthand or explicit flag

    Returns:
        Full JVM flag, None (for "none"), or "auto" (for smart defaults)

    Examples:
        >>> normalize_gc_flag("G1")
        '-XX:+UseG1GC'
        >>> normalize_gc_flag("-XX:+UseZGC")
        '-XX:+UseZGC'
        >>> normalize_gc_flag("none")
        None
        >>> normalize_gc_flag("auto")
        'auto'
    """
    if value.lower() == "none":
        return None

    if value.lower() == "auto":
        return "auto"

    # Explicit form bypasses normalization
    if value.startswith("-XX:"):
        return value

    # Normalize shorthand
    key = value.lower()
    gc_name = GC_NAME_MAP.get(key, value)

    # Warn if unknown (might be typo or future GC)
    if key not in KNOWN_GCS:
        # Fuzzy match for better error messages
        suggestions = get_close_matches(key, KNOWN_GCS, n=2, cutoff=0.6)
        suggestion_str = (
            f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
        )

        _log.warning(
            f"Unknown GC '{value}' - will try -XX:+Use{gc_name}GC.{suggestion_str}\n"
            f"         Known GCs: {', '.join(sorted(KNOWN_GCS))}"
        )

    return f"-XX:+Use{gc_name}GC"


def is_gc_flag(arg: str) -> bool:
    """
    Detect if a JVM argument is a GC collector selection flag.

    Matches flags like -XX:+UseG1GC, -XX:+UseZGC, etc.

    Args:
        arg: JVM argument to check

    Returns:
        True if arg is a GC collector flag
    """
    gc_patterns = [
        "-XX:+UseG1GC",
        "-XX:+UseZGC",
        "-XX:+UseParallelGC",
        "-XX:+UseSerialGC",
        "-XX:+UseShenandoahGC",
        "-XX:+UseEpsilonGC",
        "-XX:+UseConcMarkSweepGC",  # Deprecated in Java 9, removed in Java 14
    ]
    return any(arg.startswith(pattern) for pattern in gc_patterns)

"""
Bytecode version detection for Java class files.

Reads class file headers from JARs to determine minimum required Java version.
"""

from __future__ import annotations

import struct
import zipfile
from collections import Counter
from pathlib import Path

# Map class file major version to Java version
# Source: https://docs.oracle.com/javase/specs/jvms/se21/html/jvms-4.html
BYTECODE_TO_JAVA = {
    45: 1,  # Java 1.1
    46: 2,  # Java 1.2
    47: 3,  # Java 1.3
    48: 4,  # Java 1.4
    49: 5,  # Java 5
    50: 6,  # Java 6
    51: 7,  # Java 7
    52: 8,  # Java 8
    53: 9,  # Java 9
    54: 10,  # Java 10
    55: 11,  # Java 11
    56: 12,  # Java 12
    57: 13,  # Java 13
    58: 14,  # Java 14
    59: 15,  # Java 15
    60: 16,  # Java 16
    61: 17,  # Java 17
    62: 18,  # Java 18
    63: 19,  # Java 19
    64: 20,  # Java 20
    65: 21,  # Java 21
    66: 22,  # Java 22
    67: 23,  # Java 23
    68: 24,  # Java 24
}

# LTS versions to round up to
LTS_VERSIONS = [8, 11, 17, 21]


def read_class_version(class_bytes: bytes) -> int | None:
    """
    Read the major version from a Java class file.

    Class file format:
        u4 magic;              // 0xCAFEBABE
        u2 minor_version;
        u2 major_version;

    Args:
        class_bytes: Raw bytes of the class file

    Returns:
        Major version number, or None if not a valid class file
    """
    if len(class_bytes) < 8:
        return None

    # Check magic number (0xCAFEBABE)
    magic = struct.unpack(">I", class_bytes[0:4])[0]
    if magic != 0xCAFEBABE:
        return None

    # Read major version (big-endian unsigned short at offset 6)
    major_version = struct.unpack(">H", class_bytes[6:8])[0]
    return major_version


def bytecode_to_java_version(major_version: int) -> int:
    """
    Convert bytecode major version to Java version number.

    Args:
        major_version: Class file major version

    Returns:
        Java version (e.g., 8, 11, 17, 21)
    """
    # Look up in mapping
    java_version = BYTECODE_TO_JAVA.get(major_version)

    if java_version is None:
        # Unknown version - assume it's a future version
        # Use major_version - 44 as Java version (standard formula)
        java_version = major_version - 44

    return java_version


def round_to_lts(java_version: int) -> int:
    """
    Round Java version up to the nearest LTS release.

    LTS versions: 8, 11, 17, 21, ...

    Args:
        java_version: Java version number

    Returns:
        Nearest LTS version (rounded up)
    """
    for lts in LTS_VERSIONS:
        if java_version <= lts:
            return lts

    # If higher than known LTS versions, return as-is
    # (or we could extrapolate future LTS versions)
    return java_version


def detect_jar_java_version(
    jar_path: Path, round_to_lts_version: bool = True
) -> int | None:
    """
    Detect the minimum Java version required by a JAR file.

    Scans all .class files in the JAR and returns the maximum
    bytecode version found (which determines minimum Java requirement).

    Args:
        jar_path: Path to JAR file
        round_to_lts_version: If True, round up to nearest LTS version

    Returns:
        Minimum Java version required, or None if no class files found
    """
    if not jar_path.exists():
        return None

    max_version = None

    try:
        with zipfile.ZipFile(jar_path, "r") as jar:
            for name in jar.namelist():
                # Only process .class files
                if not name.endswith(".class"):
                    continue

                # Skip META-INF/versions/* (Multi-Release JAR version-specific classes)
                # Only base classes determine the minimum Java version
                if name.startswith("META-INF/versions/"):
                    continue

                # Skip module-info.class and package-info.class
                # (they might have different versions)
                basename = name.split("/")[-1]
                if basename in ("module-info.class", "package-info.class"):
                    continue

                try:
                    class_bytes = jar.read(name)
                    major_version = read_class_version(class_bytes)

                    if major_version is not None:
                        if max_version is None or major_version > max_version:
                            max_version = major_version

                except Exception:
                    # Skip corrupt or unreadable class files
                    continue

    except (zipfile.BadZipFile, OSError):
        # Not a valid JAR file
        return None

    if max_version is None:
        return None

    # Convert to Java version
    java_version = bytecode_to_java_version(max_version)

    if round_to_lts_version:
        java_version = round_to_lts(java_version)

    return java_version


def detect_environment_java_version(jars_dir: Path) -> int | None:
    """
    Detect the minimum Java version for an environment directory.

    Scans all JAR files and returns the maximum version required.

    Args:
        jars_dir: Directory containing JAR files

    Returns:
        Minimum Java version required, or None if no JARs found
    """
    if not jars_dir.exists():
        return None

    max_version = None

    for jar_path in jars_dir.glob("*.jar"):
        version = detect_jar_java_version(jar_path, round_to_lts_version=False)
        if version is not None:
            if max_version is None or version > max_version:
                max_version = version

    if max_version is not None:
        # Round the final result to LTS
        max_version = round_to_lts(max_version)

    return max_version


def analyze_jar_bytecode(jar_path: Path) -> dict:
    """
    Analyze bytecode versions in a JAR file.

    Returns detailed information about class file versions.

    Args:
        jar_path: Path to JAR file

    Returns:
        Dictionary with analysis results:
        {
            'version_counts': {50: 466, 52: 2, 53: 1},  # bytecode version -> count
            'max_version': 52,  # maximum bytecode version (excluding skipped)
            'java_version': 8,  # Java version required
            'skipped': ['module-info.class'],  # skipped files
            'high_version_classes': [('ij/plugin/MacAdapter.class', 52)],  # top classes
        }
    """
    if not jar_path.exists():
        return {}

    version_counts = Counter()
    skipped = []
    class_versions = []  # List of (class_name, major_version) tuples

    try:
        with zipfile.ZipFile(jar_path, "r") as jar:
            for name in jar.namelist():
                if not name.endswith(".class"):
                    continue

                # Track skipped files
                if name.startswith("META-INF/versions/"):
                    skipped.append(name)
                    continue

                basename = name.split("/")[-1]
                if basename in ("module-info.class", "package-info.class"):
                    skipped.append(name)
                    continue

                try:
                    class_bytes = jar.read(name)
                    major_version = read_class_version(class_bytes)

                    if major_version is not None:
                        version_counts[major_version] += 1
                        class_versions.append((name, major_version))

                except Exception:
                    continue

    except (zipfile.BadZipFile, OSError):
        return {}

    if not version_counts:
        return {"version_counts": {}, "max_version": None, "java_version": None}

    max_version = max(version_counts.keys())
    java_version = bytecode_to_java_version(max_version)

    # Get top N classes with highest bytecode versions
    class_versions.sort(key=lambda x: x[1], reverse=True)
    high_version_classes = class_versions[:10]  # Top 10

    return {
        "version_counts": dict(version_counts),
        "max_version": max_version,
        "java_version": java_version,
        "skipped": skipped[:10] if skipped else [],  # Sample of skipped files
        "high_version_classes": high_version_classes,
    }

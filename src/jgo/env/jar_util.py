"""
Utilities for working with JAR files.
"""

from __future__ import annotations

import re
import warnings
import zipfile
from pathlib import Path


def detect_main_class_from_jar(jar_path: Path) -> str | None:
    """
    Detect the Main-Class from a JAR file's MANIFEST.MF.

    Args:
        jar_path: Path to JAR file

    Returns:
        Main class name if found in manifest, None otherwise
    """
    try:
        with zipfile.ZipFile(jar_path) as jar_file:
            try:
                with jar_file.open("META-INF/MANIFEST.MF") as manifest:
                    main_class_pattern = re.compile(r".*Main-Class:\s*")
                    main_class = None
                    for line in manifest.readlines():
                        line = line.strip().decode("utf-8")
                        if main_class_pattern.match(line):
                            main_class = main_class_pattern.sub("", line)
                            break
                    return main_class
            except KeyError:
                # No MANIFEST.MF in this JAR
                return None
    except (zipfile.BadZipFile, FileNotFoundError):
        return None


def parse_manifest(jar_path: Path) -> dict[str, str] | None:
    """
    Parse JAR manifest into key-value pairs, handling line continuations.

    JAR manifests use a special format where lines starting with a space
    are continuations of the previous line.

    Args:
        jar_path: Path to JAR file

    Returns:
        Dictionary of manifest key-value pairs, or None if no manifest
    """
    try:
        with zipfile.ZipFile(jar_path) as jar_file:
            try:
                with jar_file.open("META-INF/MANIFEST.MF") as manifest:
                    manifest_dict = {}
                    current_key = None
                    current_value = []

                    for line in manifest.readlines():
                        line = line.decode("utf-8").rstrip("\r\n")

                        # Line continuation (starts with space)
                        if line.startswith(" ") and current_key:
                            current_value.append(line[1:])  # Strip leading space
                        # New key-value pair
                        elif ":" in line:
                            # Save previous key-value pair
                            if current_key:
                                manifest_dict[current_key] = "".join(current_value)

                            # Parse new key-value pair
                            key, value = line.split(":", 1)
                            current_key = key.strip()
                            current_value = [value.strip()]
                        # Empty line or invalid format
                        else:
                            # Save previous key-value pair if any
                            if current_key:
                                manifest_dict[current_key] = "".join(current_value)
                                current_key = None
                                current_value = []

                    # Save last key-value pair
                    if current_key:
                        manifest_dict[current_key] = "".join(current_value)

                    return manifest_dict
            except KeyError:
                # No MANIFEST.MF in this JAR
                return None
    except (zipfile.BadZipFile, FileNotFoundError):
        return None


def read_raw_manifest(jar_path: Path) -> str | None:
    """
    Read raw JAR manifest contents without parsing.

    Args:
        jar_path: Path to JAR file

    Returns:
        Raw manifest contents as string, or None if no manifest
    """
    try:
        with zipfile.ZipFile(jar_path) as jar_file:
            try:
                with jar_file.open("META-INF/MANIFEST.MF") as manifest:
                    return manifest.read().decode("utf-8")
            except KeyError:
                # No MANIFEST.MF in this JAR
                return None
    except (zipfile.BadZipFile, FileNotFoundError):
        return None


def autocomplete_main_class(main_class: str, artifact_id: str, jars_dir: Path) -> str:
    """
    Auto-complete a main class name by searching in JARs.

    New behavior:
    - If main_class contains dots (e.g., "org.example.Main"), treat as fully qualified and return as-is
    - If no dots (e.g., "Main"), attempt to find matching class in relevant JARs

    Old behavior (backward compatibility):
    - If main_class starts with @, search for partial match (e.g., "@ScriptREPL" -> "org.scijava.script.ScriptREPL")

    Args:
        main_class: Main class name (fully qualified, simple name, or @-prefixed for partial match)
        artifact_id: Artifact ID to filter relevant JARs
        jars_dir: Directory containing JAR files

    Returns:
        Fully qualified main class name
    """
    main_class = main_class.replace("/", ".")

    # Old format: @MainClass prefix (backward compatibility)
    if main_class.startswith("@"):
        pattern_str = f".*{re.escape(main_class[1:])}\\.class"
        pattern = re.compile(pattern_str)
        relevant_jars = [
            jar for jar in jars_dir.glob("*.jar") if artifact_id in jar.name
        ]
        for jar in relevant_jars:
            try:
                with zipfile.ZipFile(jar) as jar_file:
                    for entry in jar_file.namelist():
                        entry = entry.strip()
                        if pattern.match(entry):
                            return entry[:-6].replace("/", ".")
            except (zipfile.BadZipFile, IOError):
                continue
        # If auto-completion fails, raise error for old format
        raise ValueError(f"Unable to auto-complete main class: {main_class}")

    # New format: automatic fallback for non-fully-qualified class names
    # If the main class contains dots, assume it's fully qualified and use as-is
    # Otherwise, attempt auto-completion
    if "." not in main_class:
        # No dots, so try to auto-complete
        pattern_str = f".*{re.escape(main_class)}\\.class"
        pattern = re.compile(pattern_str)
        relevant_jars = [
            jar for jar in jars_dir.glob("*.jar") if artifact_id in jar.name
        ]
        for jar in relevant_jars:
            try:
                with zipfile.ZipFile(jar) as jar_file:
                    for entry in jar_file.namelist():
                        entry = entry.strip()
                        if pattern.match(entry):
                            return entry[:-6].replace("/", ".")
            except (zipfile.BadZipFile, IOError):
                continue
        # If auto-completion fails, return the original name (might still work if it's in default package)
        warnings.warn(
            f"Could not auto-complete main class '{main_class}'. Using as-is.",
            UserWarning,
            stacklevel=3,
        )

    # Main class contains dots or auto-completion failed, assume it's fully qualified
    return main_class

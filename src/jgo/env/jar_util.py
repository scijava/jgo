"""
Utilities for working with JAR files.
"""

from __future__ import annotations

import re
import struct
import warnings
import zipfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModuleInfo:
    """Information about a JAR's module status."""

    is_modular: bool  # Has module-info.class at root or Automatic-Module-Name
    module_name: str | None  # Module name if modular
    is_automatic: bool  # True if using Automatic-Module-Name (no module-info.class)


def has_module_info(jar_path: Path) -> bool:
    """
    Check if JAR contains module-info.class at its root.

    Args:
        jar_path: Path to JAR file

    Returns:
        True if module-info.class exists at JAR root
    """
    try:
        with zipfile.ZipFile(jar_path) as jar:
            return "module-info.class" in jar.namelist()
    except (zipfile.BadZipFile, FileNotFoundError):
        return False


def get_automatic_module_name(jar_path: Path) -> str | None:
    """
    Get Automatic-Module-Name from JAR manifest.

    Args:
        jar_path: Path to JAR file

    Returns:
        Automatic-Module-Name value if present, None otherwise
    """
    manifest = parse_manifest(jar_path)
    return manifest.get("Automatic-Module-Name") if manifest else None


def parse_module_name_from_descriptor(jar_path: Path) -> str | None:
    """
    Extract module name from module-info.class bytecode.

    The module-info.class file is a standard class file with a Module attribute.
    The module name is stored as a CONSTANT_Module_info entry in the constant pool.

    Args:
        jar_path: Path to JAR file

    Returns:
        Module name if parseable, None otherwise
    """
    try:
        with zipfile.ZipFile(jar_path) as jar:
            with jar.open("module-info.class") as f:
                data = f.read()
                return _parse_module_name(data)
    except (zipfile.BadZipFile, KeyError, FileNotFoundError):
        return None


def _parse_module_name(class_bytes: bytes) -> str | None:
    """
    Parse module name from class file bytes.

    Class file structure (JVMS §4):
    - u4 magic (0xCAFEBABE)
    - u2 minor_version
    - u2 major_version
    - u2 constant_pool_count
    - cp_info constant_pool[constant_pool_count-1]
    - u2 access_flags
    - u2 this_class
    - u2 super_class
    - u2 interfaces_count
    - u2 interfaces[interfaces_count]
    - u2 fields_count
    - field_info fields[fields_count]
    - u2 methods_count
    - method_info methods[methods_count]
    - u2 attributes_count
    - attribute_info attributes[attributes_count]

    The Module attribute contains a module_name_index pointing to
    a CONSTANT_Module_info, which points to a CONSTANT_Utf8_info.
    """
    # Verify magic number
    if len(class_bytes) < 10 or class_bytes[:4] != b"\xca\xfe\xba\xbe":
        return None

    # Skip to constant pool (after magic, minor, major versions)
    pos = 8
    cp_count = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
    pos += 2

    # Parse constant pool, collecting UTF-8 strings and Module entries
    constant_pool: list[tuple[str, object] | None] = [None]  # 1-indexed
    i = 1
    while i < cp_count:
        if pos >= len(class_bytes):
            return None

        tag = class_bytes[pos]
        pos += 1

        if tag == 1:  # CONSTANT_Utf8_info
            if pos + 2 > len(class_bytes):
                return None
            length = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
            pos += 2
            if pos + length > len(class_bytes):
                return None
            utf8_str = class_bytes[pos : pos + length].decode("utf-8", errors="replace")
            pos += length
            constant_pool.append(("Utf8", utf8_str))
        elif tag == 19:  # CONSTANT_Module_info
            if pos + 2 > len(class_bytes):
                return None
            name_index = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
            pos += 2
            constant_pool.append(("Module", name_index))
        elif tag == 20:  # CONSTANT_Package_info
            pos += 2
            constant_pool.append(None)
        elif tag == 7:  # CONSTANT_Class_info
            pos += 2
            constant_pool.append(None)
        elif tag == 9:  # CONSTANT_Fieldref_info
            pos += 4
            constant_pool.append(None)
        elif tag == 10:  # CONSTANT_Methodref_info
            pos += 4
            constant_pool.append(None)
        elif tag == 11:  # CONSTANT_InterfaceMethodref_info
            pos += 4
            constant_pool.append(None)
        elif tag == 8:  # CONSTANT_String_info
            pos += 2
            constant_pool.append(None)
        elif tag == 3:  # CONSTANT_Integer_info
            pos += 4
            constant_pool.append(None)
        elif tag == 4:  # CONSTANT_Float_info
            pos += 4
            constant_pool.append(None)
        elif tag == 5:  # CONSTANT_Long_info (takes 2 slots)
            pos += 8
            constant_pool.append(None)
            constant_pool.append(None)
            i += 1
        elif tag == 6:  # CONSTANT_Double_info (takes 2 slots)
            pos += 8
            constant_pool.append(None)
            constant_pool.append(None)
            i += 1
        elif tag == 12:  # CONSTANT_NameAndType_info
            pos += 4
            constant_pool.append(None)
        elif tag == 15:  # CONSTANT_MethodHandle_info
            pos += 3
            constant_pool.append(None)
        elif tag == 16:  # CONSTANT_MethodType_info
            pos += 2
            constant_pool.append(None)
        elif tag == 17:  # CONSTANT_Dynamic_info
            pos += 4
            constant_pool.append(None)
        elif tag == 18:  # CONSTANT_InvokeDynamic_info
            pos += 4
            constant_pool.append(None)
        else:
            # Unknown tag, can't continue
            return None

        i += 1

    # Find the first CONSTANT_Module_info and resolve its name
    for entry in constant_pool:
        if entry and entry[0] == "Module":
            name_index = entry[1]
            if 0 < name_index < len(constant_pool):
                name_entry = constant_pool[name_index]
                if name_entry and name_entry[0] == "Utf8":
                    return name_entry[1]

    return None


def detect_module_info(jar_path: Path) -> ModuleInfo:
    """
    Detect module information for a JAR.

    Priority:
    1. Explicit module-info.class → extract module name
    2. Automatic-Module-Name manifest header → use as module name
    3. Neither → not modular

    Args:
        jar_path: Path to JAR file

    Returns:
        ModuleInfo with detection results
    """
    if has_module_info(jar_path):
        module_name = parse_module_name_from_descriptor(jar_path)
        return ModuleInfo(is_modular=True, module_name=module_name, is_automatic=False)

    auto_name = get_automatic_module_name(jar_path)
    if auto_name:
        return ModuleInfo(is_modular=True, module_name=auto_name, is_automatic=True)

    return ModuleInfo(is_modular=False, module_name=None, is_automatic=False)


def detect_main_class_from_jar(jar_path: Path) -> str | None:
    """
    Detect the Main-Class from a JAR file's MANIFEST.MF.

    Args:
        jar_path: Path to JAR file

    Returns:
        Main class name if found in manifest, None otherwise
    """
    manifest = parse_manifest(jar_path)
    return manifest.get("Main-Class") if manifest else None


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


def autocomplete_main_class(
    main_class: str,
    artifact_id: str,
    jars_dir: Path | list[Path],
) -> str:
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
        jars_dir: Directory or list of directories containing JAR files

    Returns:
        Fully qualified main class name
    """
    main_class = main_class.replace("/", ".")

    # Normalize jars_dir to a list
    if isinstance(jars_dir, Path):
        jar_dirs = [jars_dir]
    else:
        jar_dirs = list(jars_dir)

    # Collect all JARs from all directories
    def get_all_jars():
        for d in jar_dirs:
            if d.exists():
                yield from d.glob("*.jar")

    # Old format: @MainClass prefix (backward compatibility)
    if main_class.startswith("@"):
        pattern_str = f".*{re.escape(main_class[1:])}\\.class"
        pattern = re.compile(pattern_str)
        relevant_jars = [jar for jar in get_all_jars() if artifact_id in jar.name]
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
    # Otherwise, attempt auto-completion in artifact-filtered JARs
    if "." in main_class:
        # Fully qualified name: use as-is without searching
        return main_class

    # Simple name: try to auto-complete in artifact-filtered JARs
    pattern_str = f".*{re.escape(main_class)}\\.class"
    pattern = re.compile(pattern_str)
    relevant_jars = [jar for jar in get_all_jars() if artifact_id in jar.name]
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
    return main_class

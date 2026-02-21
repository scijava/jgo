"""
Utilities for working with JAR files.
"""

from __future__ import annotations

import re
import struct
import subprocess
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


def get_module_info_paths(jar_path: Path) -> dict[int | None, str]:
    """
    Get all available module-info.class paths in a JAR with their Java versions.

    Args:
        jar_path: Path to JAR file

    Returns:
        Dictionary mapping Java version to module-info.class path:
        - None: module-info.class at root (base version)
        - int: Java version for META-INF/versions/N/module-info.class

    Examples:
        >>> get_module_info_paths(Path("regular.jar"))
        {None: "module-info.class"}
        >>> get_module_info_paths(Path("snakeyaml-2.0.jar"))
        {9: "META-INF/versions/9/module-info.class"}
        >>> get_module_info_paths(Path("multi.jar"))
        {None: "module-info.class", 9: "META-INF/versions/9/module-info.class", 11: "META-INF/versions/11/module-info.class"}
    """
    paths: dict[int | None, str] = {}
    try:
        with zipfile.ZipFile(jar_path) as jar:
            namelist = jar.namelist()

            # Check root
            if "module-info.class" in namelist:
                paths[None] = "module-info.class"

            # Check multi-release JAR versioned directories
            for name in namelist:
                if name.startswith("META-INF/versions/") and name.endswith(
                    "/module-info.class"
                ):
                    try:
                        parts = name.split("/")
                        if len(parts) >= 4:  # META-INF, versions, N, module-info.class
                            version = int(parts[2])
                            paths[version] = name
                    except ValueError:
                        continue

    except (zipfile.BadZipFile, FileNotFoundError):
        pass

    return paths


def has_module_info(jar_path: Path) -> bool:
    """
    Check if JAR contains module-info.class at its root or in versioned directories.

    Supports both:
    - Regular modular JARs: module-info.class at root
    - Multi-release JARs: META-INF/versions/N/module-info.class

    Args:
        jar_path: Path to JAR file

    Returns:
        True if module-info.class exists at JAR root or in versioned directory
    """
    return bool(get_module_info_paths(jar_path))


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


def has_toplevel_classes(jar_path: Path) -> bool:
    """
    Check if a JAR has .class files in the top-level directory (unnamed package).

    JARs with classes in the unnamed package cannot be used as automatic modules
    on the Java module path (Java 9+). This would cause:
        java.lang.module.InvalidModuleDescriptorException:
            Foo.class found in top-level directory (unnamed package not allowed in module)

    Args:
        jar_path: Path to JAR file

    Returns:
        True if any .class files exist in the top-level directory
    """
    try:
        with zipfile.ZipFile(jar_path) as jar:
            for name in jar.namelist():
                # Top-level .class: no "/" in name (or only a trailing slash for dirs)
                if name.endswith(".class") and "/" not in name:
                    return True
    except (zipfile.BadZipFile, FileNotFoundError):
        pass
    return False


def _find_module_info_path(
    jar_path: Path, java_version: int | None = None
) -> str | None:
    """
    Find the appropriate module-info.class path for a target Java version.

    For multi-release JARs, selects the versioned module-info.class that best
    matches the target Java version:
    - Uses the highest version <= target Java version
    - Falls back to root module-info.class if no suitable version found
    - For Java < 9 or None, prefers root over versioned

    Args:
        jar_path: Path to JAR file
        java_version: Target Java version (e.g., 11, 17). If None, uses highest available.

    Returns:
        Path to module-info.class within the JAR, or None if not found

    Examples:
        >>> _find_module_info_path(Path("snakeyaml-2.0.jar"), java_version=11)
        "META-INF/versions/9/module-info.class"  # Uses version 9 (highest <= 11)
        >>> _find_module_info_path(Path("snakeyaml-2.0.jar"), java_version=8)
        None  # Java 8 doesn't support modules
    """
    paths = get_module_info_paths(jar_path)
    if not paths:
        return None

    # If Java version not specified or < 9, prefer root (Java 8 doesn't support modules)
    if java_version is None or java_version < 9:
        # Return root if available, otherwise highest versioned (for detection purposes)
        if None in paths:
            return paths[None]
        if paths:
            max_version = max(v for v in paths.keys() if v is not None)
            return paths[max_version]
        return None

    # Java 9+: prefer root first (most compatible), then highest version <= java_version
    if None in paths:
        return paths[None]

    # Find highest versioned module-info that's <= target Java version
    suitable_versions = [v for v in paths.keys() if v is not None and v <= java_version]
    if suitable_versions:
        best_version = max(suitable_versions)
        return paths[best_version]

    # No suitable version found - use lowest available version as fallback
    # (Better than nothing, Java will error if truly incompatible)
    versioned_keys = [v for v in paths.keys() if v is not None]
    if versioned_keys:
        return paths[min(versioned_keys)]

    return None


def parse_module_name_from_descriptor(
    jar_path: Path, java_version: int | None = None
) -> str | None:
    """
    Extract module name from module-info.class bytecode.

    The module-info.class file is a standard class file with a Module attribute.
    The module name is stored as a CONSTANT_Module_info entry in the constant pool.

    Supports both regular modular JARs and multi-release JARs.

    Args:
        jar_path: Path to JAR file
        java_version: Target Java version for selecting appropriate module-info in multi-release JARs

    Returns:
        Module name if parseable, None otherwise
    """
    module_info_path = _find_module_info_path(jar_path, java_version)
    if not module_info_path:
        return None

    try:
        with zipfile.ZipFile(jar_path) as jar:
            with jar.open(module_info_path) as f:
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
            if isinstance(name_index, int) and 0 < name_index < len(constant_pool):
                name_entry = constant_pool[name_index]
                if name_entry and name_entry[0] == "Utf8":
                    utf8_value = name_entry[1]
                    if isinstance(utf8_value, str):
                        return utf8_value

    return None


def detect_module_info(jar_path: Path, java_version: int | None = None) -> ModuleInfo:
    """
    Detect module information for a JAR.

    Priority:
    1. Explicit module-info.class → extract module name
    2. Automatic-Module-Name manifest header → use as module name
    3. Neither → not modular

    Args:
        jar_path: Path to JAR file
        java_version: Target Java version for selecting appropriate module-info in multi-release JARs

    Returns:
        ModuleInfo with detection results
    """
    if has_module_info(jar_path):
        module_name = parse_module_name_from_descriptor(jar_path, java_version)
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
                    manifest_dict: dict[str, str] = {}
                    current_key: str | None = None
                    current_value: list[str] = []

                    for raw_line in manifest.readlines():
                        line = raw_line.decode("utf-8").rstrip("\r\n")

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


def classify_jar(jar_path: Path, jar_executable: Path) -> int:
    """
    Classify a JAR file's module compatibility using `jar --describe-module`.

    Uses the `jar` tool from a JDK 9+ to analyze the JAR and determine its
    module type according to JPMS (Java Platform Module System).

    Supports multi-release JARs by automatically retrying with --release flag
    when needed.

    Args:
        jar_path: Path to the JAR file to classify
        jar_executable: Path to the `jar` executable (from JDK 9+)

    Returns:
        JAR type classification:
        1: Explicit module (has module-info.class)
        2: Automatic module with name (has Automatic-Module-Name in manifest)
        3: Derivable automatic module (filename produces valid module name)
        4: Non-modularizable (invalid module name or other JPMS issues)

    Examples:
        >>> classify_jar(Path("asm-9.7.jar"), Path("/usr/lib/jvm/java-11/bin/jar"))
        1  # Has module-info.class
        >>> classify_jar(Path("args4j-2.33.jar"), Path("/usr/lib/jvm/java-11/bin/jar"))
        2  # Has Automatic-Module-Name
        >>> classify_jar(Path("commons-io-2.11.0.jar"), Path("/usr/lib/jvm/java-11/bin/jar"))
        3  # Can derive "commons.io" from filename
        >>> classify_jar(Path("compiler-interface-1.3.5.jar"), Path("/usr/lib/jvm/java-11/bin/jar"))
        4  # "compiler.interface" is invalid (interface is keyword)
        >>> classify_jar(Path("snakeyaml-2.0.jar"), Path("/usr/lib/jvm/java-11/bin/jar"))
        1  # Multi-release JAR with module-info in META-INF/versions/9/
    """
    try:
        result = subprocess.run(
            [str(jar_executable), "--describe-module", "--file", str(jar_path)],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # jar tool not available or timed out - assume non-modularizable
        return 4

    output = result.stdout.strip()
    stderr = result.stderr.strip()

    # Check if this is a multi-release JAR requiring --release flag
    # Example output: "releases: 9\n\nNo root module descriptor, specify --release"
    if "No root module descriptor" in output and "specify --release" in output:
        # Extract the release version from output (e.g., "releases: 9")
        release_version = None
        for line in output.split("\n"):
            if line.startswith("releases:"):
                try:
                    # Parse "releases: 9" or "releases: 9 10 11"
                    versions = line.split(":", 1)[1].strip().split()
                    if versions:
                        # Use the first (lowest) version that has the module descriptor
                        release_version = versions[0]
                        break
                except (IndexError, ValueError):
                    pass

        if release_version:
            # Retry with --release flag
            try:
                result = subprocess.run(
                    [
                        str(jar_executable),
                        "--describe-module",
                        "--file",
                        str(jar_path),
                        "--release",
                        release_version,
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=False,
                )
                output = result.stdout.strip()
                stderr = result.stderr.strip()
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return 4

    # Check for errors in stderr indicating JPMS issues
    if result.returncode != 0 or stderr:
        stderr_lower = stderr.lower()
        # Check for specific JPMS errors
        if (
            "invalid module name" in stderr_lower
            or "not a java identifier" in stderr_lower
        ):
            return 4
        if "provider class" in stderr_lower and "not in jar" in stderr_lower:
            # InvalidModuleDescriptorException (e.g., xalan case)
            return 4
        # Other errors - assume non-modularizable
        if result.returncode != 0:
            return 4

    # Type 1: Explicit module (has module-info.class)
    # Example: "org.objectweb.asm@9.7 jar:file:///path/to/asm-9.7.jar!/module-info.class"
    # Multi-release: "org.yaml.snakeyaml@2.0 jar:file:///.../snakeyaml-2.0.jar/!META-INF/versions/9/module-info.class"
    if "!/module-info.class" in output or (
        "!/META-INF/versions/" in output and "/module-info.class" in output
    ):
        return 1
    # Alternative format without path separator
    if "jar:file:" in output and "@" in output and " automatic" not in output:
        return 1

    # Type 3: Derivable automatic module (check BEFORE type 2!)
    # Example: "No module descriptor found. Derived automatic module.\n\nmines.jtk@20151125 automatic"
    if "No module descriptor found" in output:
        if "Derived automatic module" in output:
            # JARs with classes in the unnamed package cannot be used as automatic
            # modules: Java raises InvalidModuleDescriptorException at runtime.
            # jar --describe-module does not check for this condition.
            if has_toplevel_classes(jar_path):
                return 4
            return 3
        else:
            # Derivation failed - non-modularizable
            return 4

    # Type 2: Automatic module with Automatic-Module-Name
    # Example: "args4j@2.33 automatic"
    # This check comes AFTER type 3 to avoid false matches
    if " automatic" in output and "@" in output:
        # Same unnamed-package check applies to Automatic-Module-Name JARs
        if has_toplevel_classes(jar_path):
            return 4
        return 2

    # Unknown output format - conservatively assume non-modularizable
    return 4


def has_main_method(class_bytes: bytes) -> bool:
    """
    Check if a class file has a public static void main(String[]) method.

    Parses the class file to check:
    1. Class is public
    2. Has a method named "main"
    3. The method is public and static
    4. The method signature is "([Ljava/lang/String;)V"

    Args:
        class_bytes: Raw bytes of the class file

    Returns:
        True if the class has a valid main method
    """
    if len(class_bytes) < 10 or class_bytes[:4] != b"\xca\xfe\xba\xbe":
        return False

    try:
        # Skip magic (4), minor (2), major (2) = 8 bytes
        pos = 8

        # Read constant pool count
        cp_count = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
        pos += 2

        # Parse constant pool to extract UTF-8 strings
        constant_pool: list[tuple[str, object] | None] = [None]  # 1-indexed
        i = 1
        while i < cp_count:
            if pos >= len(class_bytes):
                return False

            tag = class_bytes[pos]
            pos += 1

            if tag == 1:  # CONSTANT_Utf8
                length = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
                pos += 2
                if pos + length > len(class_bytes):
                    return False
                utf8_str = class_bytes[pos : pos + length].decode(
                    "utf-8", errors="replace"
                )
                pos += length
                constant_pool.append(("Utf8", utf8_str))
            elif tag in (7, 8, 16, 19, 20):  # 2-byte entries
                pos += 2
                constant_pool.append(None)
            elif tag in (3, 4, 9, 10, 11, 12, 17, 18):  # 4-byte entries
                pos += 4
                constant_pool.append(None)
            elif tag == 15:  # CONSTANT_MethodHandle
                pos += 3
                constant_pool.append(None)
            elif tag in (5, 6):  # CONSTANT_Long/Double (takes 2 slots)
                pos += 8
                constant_pool.append(None)
                constant_pool.append(None)
                i += 1
            else:
                return False  # Unknown tag

            i += 1

        # Read access flags
        if pos + 2 > len(class_bytes):
            return False
        access_flags = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
        pos += 2

        # Check if class is public (0x0001)
        is_public = (access_flags & 0x0001) != 0
        if not is_public:
            return False

        # Skip this_class (2), super_class (2)
        pos += 4

        # Skip interfaces
        if pos + 2 > len(class_bytes):
            return False
        interfaces_count = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
        pos += 2 + (interfaces_count * 2)

        # Skip fields
        if pos + 2 > len(class_bytes):
            return False
        fields_count = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
        pos += 2
        for _ in range(fields_count):
            # Skip access_flags (2), name_index (2), descriptor_index (2)
            pos += 6
            if pos + 2 > len(class_bytes):
                return False
            attributes_count = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
            pos += 2
            # Skip attributes
            for _ in range(attributes_count):
                if pos + 6 > len(class_bytes):
                    return False
                pos += 2  # name_index
                length = struct.unpack(">I", class_bytes[pos : pos + 4])[0]
                pos += 4 + length

        # Read methods
        if pos + 2 > len(class_bytes):
            return False
        methods_count = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
        pos += 2

        for _ in range(methods_count):
            if pos + 6 > len(class_bytes):
                return False

            method_access_flags = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
            pos += 2

            name_index = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
            pos += 2

            descriptor_index = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
            pos += 2

            # Check if method is public (0x0001) and static (0x0008)
            is_public_static = (method_access_flags & 0x0009) == 0x0009

            # Get method name and descriptor
            method_name = None
            method_descriptor = None

            if 0 < name_index < len(constant_pool) and constant_pool[name_index]:
                entry = constant_pool[name_index]
                if entry[0] == "Utf8":
                    method_name = entry[1]

            if (
                0 < descriptor_index < len(constant_pool)
                and constant_pool[descriptor_index]
            ):
                entry = constant_pool[descriptor_index]
                if entry[0] == "Utf8":
                    method_descriptor = entry[1]

            # Check if this is the main method
            if (
                is_public_static
                and method_name == "main"
                and method_descriptor == "([Ljava/lang/String;)V"
            ):
                return True

            # Skip method attributes
            if pos + 2 > len(class_bytes):
                return False
            attributes_count = struct.unpack(">H", class_bytes[pos : pos + 2])[0]
            pos += 2
            for _ in range(attributes_count):
                if pos + 6 > len(class_bytes):
                    return False
                pos += 2  # name_index
                length = struct.unpack(">I", class_bytes[pos : pos + 4])[0]
                pos += 4 + length

        return False

    except Exception:
        return False


def find_main_classes(jar_path: Path) -> list[str]:
    """
    Find all classes in a JAR that have a public static void main(String[]) method.

    Args:
        jar_path: Path to JAR file

    Returns:
        List of fully qualified class names that have main methods
    """
    main_classes = []

    try:
        with zipfile.ZipFile(jar_path) as jar:
            for name in jar.namelist():
                # Only process .class files
                if not name.endswith(".class"):
                    continue

                # Skip module-info and package-info
                if name.endswith("module-info.class") or name.endswith(
                    "package-info.class"
                ):
                    continue

                # Skip inner classes (contain $)
                if "$" in name:
                    continue

                try:
                    with jar.open(name) as class_file:
                        class_bytes = class_file.read()
                        if has_main_method(class_bytes):
                            # Convert path to class name
                            class_name = name[:-6].replace("/", ".")
                            main_classes.append(class_name)
                except Exception:
                    continue

    except (zipfile.BadZipFile, FileNotFoundError):
        pass

    return sorted(main_classes)

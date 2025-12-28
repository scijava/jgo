"""
Tests for JAR module detection functionality.
"""

import io
import zipfile

from jgo.env.jar import (
    ModuleInfo,
    detect_module_info,
    get_automatic_module_name,
    get_module_info_paths,
    has_module_info,
    parse_module_name_from_descriptor,
)

# =============================================================================
# Test fixtures - create test JARs in memory
# =============================================================================


def create_jar_with_module_info(module_name: str = "test.module") -> bytes:
    """
    Create a minimal JAR with a module-info.class file.

    The module-info.class is a minimal valid class file with:
    - Magic number (0xCAFEBABE)
    - Minimal constant pool with module name
    - Module access flags
    """
    # Minimal module-info.class bytecode
    # This is a simplified version that contains the module name
    # in the constant pool for parsing
    class_bytes = bytearray()

    # Magic number
    class_bytes.extend(b"\xca\xfe\xba\xbe")

    # Minor version (0)
    class_bytes.extend(b"\x00\x00")

    # Major version (53 = Java 9)
    class_bytes.extend(b"\x00\x35")

    # Constant pool count (4 entries: 0 is unused, 1=Utf8, 2=Module, 3=Utf8)
    class_bytes.extend(b"\x00\x04")

    # Entry 1: CONSTANT_Utf8_info for module name
    module_name_bytes = module_name.encode("utf-8")
    class_bytes.append(1)  # tag = Utf8
    class_bytes.extend(len(module_name_bytes).to_bytes(2, "big"))
    class_bytes.extend(module_name_bytes)

    # Entry 2: CONSTANT_Module_info pointing to entry 1
    class_bytes.append(19)  # tag = Module
    class_bytes.extend(b"\x00\x01")  # name_index = 1

    # Entry 3: CONSTANT_Utf8_info for "module-info"
    class_name = b"module-info"
    class_bytes.append(1)  # tag = Utf8
    class_bytes.extend(len(class_name).to_bytes(2, "big"))
    class_bytes.extend(class_name)

    # Access flags (ACC_MODULE = 0x8000)
    class_bytes.extend(b"\x80\x00")

    # this_class (index 0 - unused for module-info)
    class_bytes.extend(b"\x00\x00")

    # super_class (index 0)
    class_bytes.extend(b"\x00\x00")

    # interfaces_count (0)
    class_bytes.extend(b"\x00\x00")

    # fields_count (0)
    class_bytes.extend(b"\x00\x00")

    # methods_count (0)
    class_bytes.extend(b"\x00\x00")

    # attributes_count (0 - simplified, no Module attribute needed for name parsing)
    class_bytes.extend(b"\x00\x00")

    # Create JAR with module-info.class
    jar_buffer = io.BytesIO()
    with zipfile.ZipFile(jar_buffer, "w", zipfile.ZIP_DEFLATED) as jar:
        jar.writestr("module-info.class", bytes(class_bytes))
        jar.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n")
    return jar_buffer.getvalue()


def create_jar_with_automatic_module_name(module_name: str) -> bytes:
    """Create a JAR with Automatic-Module-Name in manifest."""
    jar_buffer = io.BytesIO()
    with zipfile.ZipFile(jar_buffer, "w", zipfile.ZIP_DEFLATED) as jar:
        manifest = f"Manifest-Version: 1.0\nAutomatic-Module-Name: {module_name}\n"
        jar.writestr("META-INF/MANIFEST.MF", manifest)
        jar.writestr("com/example/Test.class", b"dummy class content")
    return jar_buffer.getvalue()


def create_legacy_jar() -> bytes:
    """Create a JAR without any module information."""
    jar_buffer = io.BytesIO()
    with zipfile.ZipFile(jar_buffer, "w", zipfile.ZIP_DEFLATED) as jar:
        jar.writestr("META-INF/MANIFEST.MF", "Manifest-Version: 1.0\n")
        jar.writestr("com/example/Test.class", b"dummy class content")
    return jar_buffer.getvalue()


def create_multirelease_jar(module_name: str = "multi.release.module") -> bytes:
    """
    Create a multi-release JAR with module-info.class in versioned directory.

    This simulates JARs like snakeyaml-2.0.jar that have their module-info.class
    in META-INF/versions/N/ instead of at the root.
    """
    # Minimal module-info.class bytecode (same as create_jar_with_module_info)
    class_bytes = bytearray()
    class_bytes.extend(b"\xca\xfe\xba\xbe")  # Magic
    class_bytes.extend(b"\x00\x00")  # Minor version
    class_bytes.extend(b"\x00\x35")  # Major version (53 = Java 9)
    class_bytes.extend(b"\x00\x04")  # Constant pool count

    # Entry 1: CONSTANT_Utf8_info for module name
    module_name_bytes = module_name.encode("utf-8")
    class_bytes.append(1)
    class_bytes.extend(len(module_name_bytes).to_bytes(2, "big"))
    class_bytes.extend(module_name_bytes)

    # Entry 2: CONSTANT_Module_info
    class_bytes.append(19)
    class_bytes.extend(b"\x00\x01")

    # Entry 3: CONSTANT_Utf8_info for "module-info"
    class_name = b"module-info"
    class_bytes.append(1)
    class_bytes.extend(len(class_name).to_bytes(2, "big"))
    class_bytes.extend(class_name)

    # Access flags, this_class, super_class, etc.
    class_bytes.extend(b"\x80\x00")  # ACC_MODULE
    class_bytes.extend(b"\x00\x00")  # this_class
    class_bytes.extend(b"\x00\x00")  # super_class
    class_bytes.extend(b"\x00\x00")  # interfaces_count
    class_bytes.extend(b"\x00\x00")  # fields_count
    class_bytes.extend(b"\x00\x00")  # methods_count
    class_bytes.extend(b"\x00\x00")  # attributes_count

    # Create multi-release JAR
    jar_buffer = io.BytesIO()
    with zipfile.ZipFile(jar_buffer, "w", zipfile.ZIP_DEFLATED) as jar:
        # Mark as multi-release JAR in manifest
        manifest = "Manifest-Version: 1.0\nMulti-Release: true\n"
        jar.writestr("META-INF/MANIFEST.MF", manifest)

        # Add module-info.class in versioned directory (Java 9)
        jar.writestr("META-INF/versions/9/module-info.class", bytes(class_bytes))

        # Add some dummy content
        jar.writestr("com/example/Test.class", b"dummy class content")

    return jar_buffer.getvalue()


# =============================================================================
# get_module_info_paths() tests
# =============================================================================


def test_get_module_info_paths_regular_jar(tmp_path):
    """Test get_module_info_paths with regular modular JAR."""
    jar_path = tmp_path / "modular.jar"
    jar_path.write_bytes(create_jar_with_module_info("test.module"))

    paths = get_module_info_paths(jar_path)
    assert paths == {None: "module-info.class"}


def test_get_module_info_paths_multirelease_jar(tmp_path):
    """Test get_module_info_paths with multi-release JAR."""
    jar_path = tmp_path / "multirelease.jar"
    jar_path.write_bytes(create_multirelease_jar("test.module"))

    paths = get_module_info_paths(jar_path)
    assert paths == {9: "META-INF/versions/9/module-info.class"}


def test_get_module_info_paths_legacy_jar(tmp_path):
    """Test get_module_info_paths with legacy JAR (no module-info)."""
    jar_path = tmp_path / "legacy.jar"
    jar_path.write_bytes(create_legacy_jar())

    paths = get_module_info_paths(jar_path)
    assert paths == {}


# =============================================================================
# has_module_info() tests
# =============================================================================


def test_has_module_info_with_modular_jar(tmp_path):
    """Test that has_module_info returns True for modular JAR."""
    jar_path = tmp_path / "modular.jar"
    jar_path.write_bytes(create_jar_with_module_info("test.module"))

    assert has_module_info(jar_path) is True


def test_has_module_info_with_automatic_module(tmp_path):
    """Test that has_module_info returns False for automatic module (no module-info.class)."""
    jar_path = tmp_path / "automatic.jar"
    jar_path.write_bytes(create_jar_with_automatic_module_name("automatic.module"))

    assert has_module_info(jar_path) is False


def test_has_module_info_with_legacy_jar(tmp_path):
    """Test that has_module_info returns False for legacy JAR."""
    jar_path = tmp_path / "legacy.jar"
    jar_path.write_bytes(create_legacy_jar())

    assert has_module_info(jar_path) is False


def test_has_module_info_with_nonexistent_file(tmp_path):
    """Test that has_module_info returns False for nonexistent file."""
    jar_path = tmp_path / "nonexistent.jar"

    assert has_module_info(jar_path) is False


def test_has_module_info_with_invalid_zip(tmp_path):
    """Test that has_module_info returns False for invalid ZIP file."""
    jar_path = tmp_path / "invalid.jar"
    jar_path.write_bytes(b"not a zip file")

    assert has_module_info(jar_path) is False


def test_has_module_info_with_multirelease_jar(tmp_path):
    """Test that has_module_info returns True for multi-release JAR."""
    jar_path = tmp_path / "multirelease.jar"
    jar_path.write_bytes(create_multirelease_jar("test.multirelease"))

    assert has_module_info(jar_path) is True


# =============================================================================
# get_automatic_module_name() tests
# =============================================================================


def test_get_automatic_module_name_with_automatic_module(tmp_path):
    """Test getting Automatic-Module-Name from manifest."""
    jar_path = tmp_path / "automatic.jar"
    jar_path.write_bytes(create_jar_with_automatic_module_name("my.automatic.module"))

    assert get_automatic_module_name(jar_path) == "my.automatic.module"


def test_get_automatic_module_name_with_modular_jar(tmp_path):
    """Test that get_automatic_module_name returns None for modular JAR (no manifest entry)."""
    jar_path = tmp_path / "modular.jar"
    jar_path.write_bytes(create_jar_with_module_info("test.module"))

    assert get_automatic_module_name(jar_path) is None


def test_get_automatic_module_name_with_legacy_jar(tmp_path):
    """Test that get_automatic_module_name returns None for legacy JAR."""
    jar_path = tmp_path / "legacy.jar"
    jar_path.write_bytes(create_legacy_jar())

    assert get_automatic_module_name(jar_path) is None


# =============================================================================
# parse_module_name_from_descriptor() tests
# =============================================================================


def test_parse_module_name_from_descriptor(tmp_path):
    """Test parsing module name from module-info.class."""
    jar_path = tmp_path / "modular.jar"
    jar_path.write_bytes(create_jar_with_module_info("org.example.mymodule"))

    assert parse_module_name_from_descriptor(jar_path) == "org.example.mymodule"


def test_parse_module_name_from_descriptor_no_module_info(tmp_path):
    """Test that parse_module_name_from_descriptor returns None without module-info.class."""
    jar_path = tmp_path / "legacy.jar"
    jar_path.write_bytes(create_legacy_jar())

    assert parse_module_name_from_descriptor(jar_path) is None


def test_parse_module_name_from_descriptor_multirelease(tmp_path):
    """Test parsing module name from multi-release JAR."""
    jar_path = tmp_path / "multirelease.jar"
    jar_path.write_bytes(create_multirelease_jar("org.yaml.snakeyaml"))

    assert parse_module_name_from_descriptor(jar_path) == "org.yaml.snakeyaml"


# =============================================================================
# detect_module_info() tests
# =============================================================================


def test_detect_module_info_modular(tmp_path):
    """Test detect_module_info with modular JAR."""
    jar_path = tmp_path / "modular.jar"
    jar_path.write_bytes(create_jar_with_module_info("my.module"))

    info = detect_module_info(jar_path)
    assert info.is_modular is True
    assert info.module_name == "my.module"
    assert info.is_automatic is False


def test_detect_module_info_automatic(tmp_path):
    """Test detect_module_info with automatic module."""
    jar_path = tmp_path / "automatic.jar"
    jar_path.write_bytes(create_jar_with_automatic_module_name("auto.module"))

    info = detect_module_info(jar_path)
    assert info.is_modular is True
    assert info.module_name == "auto.module"
    assert info.is_automatic is True


def test_detect_module_info_legacy(tmp_path):
    """Test detect_module_info with legacy JAR."""
    jar_path = tmp_path / "legacy.jar"
    jar_path.write_bytes(create_legacy_jar())

    info = detect_module_info(jar_path)
    assert info.is_modular is False
    assert info.module_name is None
    assert info.is_automatic is False


def test_detect_module_info_multirelease(tmp_path):
    """Test detect_module_info with multi-release JAR."""
    jar_path = tmp_path / "multirelease.jar"
    jar_path.write_bytes(create_multirelease_jar("org.yaml.snakeyaml"))

    info = detect_module_info(jar_path)
    assert info.is_modular is True
    assert info.module_name == "org.yaml.snakeyaml"
    assert info.is_automatic is False


# =============================================================================
# ModuleInfo dataclass tests
# =============================================================================


def test_module_info_dataclass():
    """Test ModuleInfo dataclass."""
    info = ModuleInfo(is_modular=True, module_name="test.module", is_automatic=False)
    assert info.is_modular is True
    assert info.module_name == "test.module"
    assert info.is_automatic is False


def test_module_info_equality():
    """Test ModuleInfo equality."""
    info1 = ModuleInfo(is_modular=True, module_name="test", is_automatic=False)
    info2 = ModuleInfo(is_modular=True, module_name="test", is_automatic=False)
    info3 = ModuleInfo(is_modular=True, module_name="other", is_automatic=False)

    assert info1 == info2
    assert info1 != info3

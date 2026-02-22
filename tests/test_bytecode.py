#!/usr/bin/env python3
"""
Tests for bytecode version detection.
"""

import tempfile
import zipfile
from pathlib import Path

from jgo.env._bytecode import (
    BYTECODE_TO_JAVA,
    bytecode_to_java_version,
    detect_environment_java_version,
    detect_jar_java_version,
    read_class_version,
    round_to_lts,
)


def create_fake_class_file(major_version: int, minor_version: int = 0) -> bytes:
    """
    Create a minimal valid Java class file with specified version.

    Class file structure:
        u4 magic;              // 0xCAFEBABE
        u2 minor_version;
        u2 major_version;
        ... (we'll keep it minimal)
    """
    import struct

    # Magic number (0xCAFEBABE)
    magic = struct.pack(">I", 0xCAFEBABE)

    # Minor version
    minor = struct.pack(">H", minor_version)

    # Major version
    major = struct.pack(">H", major_version)

    # Minimal rest of class file (just enough to be valid)
    # Constant pool count (0 = empty)
    const_pool_count = struct.pack(">H", 0)

    return magic + minor + major + const_pool_count


def create_fake_jar(jar_path: Path, class_versions: dict):
    """
    Create a fake JAR file with class files of specified versions.

    Args:
        jar_path: Path where JAR should be created
        class_versions: Dict mapping class names to major versions
                       e.g., {"Foo.class": 52, "Bar.class": 61}
    """
    with zipfile.ZipFile(jar_path, "w") as jar:
        for class_name, major_version in class_versions.items():
            class_bytes = create_fake_class_file(major_version)
            jar.writestr(class_name, class_bytes)


def test_read_class_version():
    """Test reading class file version from bytes."""
    # Java 8 class file (major version 52)
    java8_class = create_fake_class_file(52)
    assert read_class_version(java8_class) == 52

    # Java 17 class file (major version 61)
    java17_class = create_fake_class_file(61)
    assert read_class_version(java17_class) == 61

    # Invalid class file (wrong magic)
    invalid = b"\x00\x00\x00\x00\x00\x00\x00\x34"
    assert read_class_version(invalid) is None

    # Too short
    short = b"\xca\xfe\xba"
    assert read_class_version(short) is None


def test_bytecode_to_java_version():
    """Test mapping bytecode version to Java version."""
    assert bytecode_to_java_version(52) == 8  # Java 8
    assert bytecode_to_java_version(55) == 11  # Java 11
    assert bytecode_to_java_version(61) == 17  # Java 17
    assert bytecode_to_java_version(65) == 21  # Java 21

    # Unknown future version (uses formula: major - 44)
    assert bytecode_to_java_version(70) == 26


def test_round_to_lts():
    """Test rounding to LTS versions."""
    assert round_to_lts(8) == 8  # Already LTS
    assert round_to_lts(9) == 11  # Round up
    assert round_to_lts(10) == 11  # Round up
    assert round_to_lts(11) == 11  # Already LTS
    assert round_to_lts(12) == 17  # Round up
    assert round_to_lts(16) == 17  # Round up
    assert round_to_lts(17) == 17  # Already LTS
    assert round_to_lts(20) == 21  # Round up
    assert round_to_lts(21) == 21  # Already LTS
    assert round_to_lts(22) == 22  # Beyond known LTS, return as-is


def test_detect_jar_java_version():
    """Test detecting Java version from JAR file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jar_path = Path(tmp_dir) / "test.jar"

        # JAR with Java 8 classes
        create_fake_jar(jar_path, {"Foo.class": 52, "Bar.class": 52})
        assert detect_jar_java_version(jar_path) == 8

        # JAR with mixed versions (should return max)
        jar_path2 = Path(tmp_dir) / "mixed.jar"
        create_fake_jar(jar_path2, {"Old.class": 52, "New.class": 61})
        assert detect_jar_java_version(jar_path2) == 17  # 61 -> Java 17

        # JAR with non-LTS version (should round up)
        jar_path3 = Path(tmp_dir) / "java9.jar"
        create_fake_jar(jar_path3, {"Java9.class": 53})  # Java 9
        assert detect_jar_java_version(jar_path3) == 11  # Rounds to LTS

        # Empty JAR (no class files)
        jar_path4 = Path(tmp_dir) / "empty.jar"
        with zipfile.ZipFile(jar_path4, "w") as jar:
            jar.writestr("README.txt", "No classes here")
        assert detect_jar_java_version(jar_path4) is None

        # Non-existent JAR
        assert detect_jar_java_version(Path(tmp_dir) / "missing.jar") is None


def test_detect_jar_skips_metadata_classes():
    """Test that module-info.class and package-info.class are skipped."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jar_path = Path(tmp_dir) / "test.jar"

        # Create JAR with regular class (Java 8) and module-info (Java 9)
        # module-info should be ignored
        with zipfile.ZipFile(jar_path, "w") as jar:
            jar.writestr("com/example/Foo.class", create_fake_class_file(52))  # Java 8
            jar.writestr("module-info.class", create_fake_class_file(53))  # Java 9
            jar.writestr(
                "com/example/package-info.class", create_fake_class_file(53)
            )  # Java 9

        # Should detect Java 8, not Java 9
        assert detect_jar_java_version(jar_path) == 8


def test_detect_jar_skips_multi_release_jar_versions():
    """Test that META-INF/versions/* classes are skipped (Multi-Release JARs)."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jar_path = Path(tmp_dir) / "mrjar.jar"

        # Create a Multi-Release JAR with base classes (Java 8) and
        # version-specific optimizations (Java 11, 17, 21)
        with zipfile.ZipFile(jar_path, "w") as jar:
            # Base classes - these determine minimum Java version
            jar.writestr("com/example/Foo.class", create_fake_class_file(52))  # Java 8
            jar.writestr("com/example/Bar.class", create_fake_class_file(52))  # Java 8

            # Multi-release version-specific classes (should be ignored)
            jar.writestr(
                "META-INF/versions/11/com/example/Foo.class",
                create_fake_class_file(55),  # Java 11
            )
            jar.writestr(
                "META-INF/versions/17/com/example/Foo.class",
                create_fake_class_file(61),  # Java 17
            )
            jar.writestr(
                "META-INF/versions/21/com/example/Bar.class",
                create_fake_class_file(65),  # Java 21
            )

        # Should detect Java 8 from base classes, ignoring META-INF/versions
        assert detect_jar_java_version(jar_path) == 8


def test_detect_environment_java_version():
    """Test detecting Java version from environment directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jars_dir = Path(tmp_dir) / "jars"
        jars_dir.mkdir()

        # Create multiple JARs with different versions
        create_fake_jar(jars_dir / "lib1.jar", {"Foo.class": 52})  # Java 8
        create_fake_jar(jars_dir / "lib2.jar", {"Bar.class": 55})  # Java 11
        create_fake_jar(jars_dir / "lib3.jar", {"Baz.class": 61})  # Java 17

        # Should return highest version (17)
        assert detect_environment_java_version(jars_dir) == 17

        # Non-existent directory
        assert detect_environment_java_version(Path(tmp_dir) / "missing") is None

        # Empty directory
        empty_dir = Path(tmp_dir) / "empty"
        empty_dir.mkdir()
        assert detect_environment_java_version(empty_dir) is None


def test_bytecode_mapping_completeness():
    """Verify BYTECODE_TO_JAVA mapping covers expected range."""
    # Should have entries for Java 1.1 through at least Java 21
    assert 45 in BYTECODE_TO_JAVA  # Java 1.1
    assert 52 in BYTECODE_TO_JAVA  # Java 8
    assert 55 in BYTECODE_TO_JAVA  # Java 11
    assert 61 in BYTECODE_TO_JAVA  # Java 17
    assert 65 in BYTECODE_TO_JAVA  # Java 21

    # Verify mapping is correct for key versions
    assert BYTECODE_TO_JAVA[52] == 8
    assert BYTECODE_TO_JAVA[55] == 11
    assert BYTECODE_TO_JAVA[61] == 17
    assert BYTECODE_TO_JAVA[65] == 21


def test_detect_jar_handles_corrupt_classes():
    """Test that corrupt class files are gracefully skipped."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jar_path = Path(tmp_dir) / "corrupt.jar"

        with zipfile.ZipFile(jar_path, "w") as jar:
            # Valid class
            jar.writestr("Good.class", create_fake_class_file(52))

            # Corrupt class (garbage data)
            jar.writestr("Bad.class", b"not a real class file")

            # Another valid class
            jar.writestr("AlsoGood.class", create_fake_class_file(55))

        # Should still detect version from valid classes
        assert detect_jar_java_version(jar_path) == 11  # Max of 52 and 55


def test_no_rounding_option():
    """Test detecting version without LTS rounding."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        jar_path = Path(tmp_dir) / "java9.jar"
        create_fake_jar(jar_path, {"Java9.class": 53})  # Java 9

        # With rounding (default)
        assert detect_jar_java_version(jar_path, round_to_lts_version=True) == 11

        # Without rounding
        assert detect_jar_java_version(jar_path, round_to_lts_version=False) == 9


if __name__ == "__main__":
    test_read_class_version()
    test_bytecode_to_java_version()
    test_round_to_lts()
    test_detect_jar_java_version()
    test_detect_jar_skips_metadata_classes()
    test_detect_jar_skips_multi_release_jar_versions()
    test_detect_environment_java_version()
    test_bytecode_mapping_completeness()
    test_detect_jar_handles_corrupt_classes()
    test_no_rounding_option()
    print("All bytecode tests passed!")

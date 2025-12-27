"""
Tests for jgo.maven.util utility functions.
"""

from jgo.util.io import binary, text


def test_text(tmp_path):
    """Test the text function."""
    test_file = tmp_path / "test.txt"
    test_content = "Hello, World!\nThis is a test."
    test_file.write_text(test_content)

    result = text(test_file)
    assert result == test_content


def test_binary(tmp_path):
    """Test the binary function."""
    test_file = tmp_path / "test.bin"
    test_content = b"\x00\x01\x02\x03\xff\xfe"
    test_file.write_bytes(test_content)

    result = binary(test_file)
    assert result == test_content

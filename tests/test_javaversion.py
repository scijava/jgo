"""Tests for cached per-artifact minimum-Java-version detection."""

import struct
import zipfile
from pathlib import Path

import jgo.env._javaversion as jv
from jgo.env._javaversion import jar_java_version


def _class_bytes(major_version: int) -> bytes:
    """Minimal valid .class file header with the given major version."""
    return (
        struct.pack(">I", 0xCAFEBABE)
        + struct.pack(">H", 0)
        + struct.pack(">H", major_version)
    )


def _make_jar(path: Path, major_version: int) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("com/example/Foo.class", _class_bytes(major_version))


class _StubArtifact:
    """Just enough of jgo's Artifact for jar_java_version()."""

    def __init__(self, jar_path: Path, groupId, artifactId, version):
        self._jar = jar_path
        self.groupId = groupId
        self.artifactId = artifactId
        self.version = version
        self.filename = f"{artifactId}-{version}.jar"

    def resolve(self) -> Path:
        return self._jar


def test_detects_and_rounds(tmp_path, monkeypatch):
    monkeypatch.setattr(jv, "_MEMO", {})
    cache = tmp_path / "cache"
    jar = tmp_path / "foo.jar"
    _make_jar(jar, 53)  # Java 9
    art = _StubArtifact(jar, "com.example", "foo", "1.0.0")

    assert jar_java_version(art, cache) == 9
    assert jar_java_version(art, cache, round_to_lts_version=True) == 11


def test_disk_cache_avoids_rescan(tmp_path, monkeypatch):
    monkeypatch.setattr(jv, "_MEMO", {})
    cache = tmp_path / "cache"
    jar = tmp_path / "bar.jar"
    _make_jar(jar, 55)  # Java 11
    art = _StubArtifact(jar, "com.example", "bar", "2.0.0")

    calls = {"n": 0}
    real = jv.detect_jar_java_version

    def counting(jar_path, round_to_lts_version=True):
        calls["n"] += 1
        return real(jar_path, round_to_lts_version=round_to_lts_version)

    monkeypatch.setattr(jv, "detect_jar_java_version", counting)

    # Cold: scans once and writes the cache file.
    assert jar_java_version(art, cache) == 11
    assert calls["n"] == 1
    cache_file = (
        cache
        / "info"
        / "com"
        / "example"
        / "bar"
        / "2.0.0"
        / "bar-2.0.0.jar.java-version.json"
    )
    assert cache_file.exists()

    # Drop the in-process memo; the disk cache must satisfy the next lookup.
    monkeypatch.setattr(jv, "_MEMO", {})
    assert jar_java_version(art, cache) == 11
    assert calls["n"] == 1  # not re-scanned


def test_in_process_memo(tmp_path, monkeypatch):
    monkeypatch.setattr(jv, "_MEMO", {})
    cache = tmp_path / "cache"
    jar = tmp_path / "baz.jar"
    _make_jar(jar, 52)  # Java 8
    art = _StubArtifact(jar, "com.example", "baz", "3.0.0")

    calls = {"n": 0}
    real = jv.detect_jar_java_version

    def counting(jar_path, round_to_lts_version=True):
        calls["n"] += 1
        return real(jar_path, round_to_lts_version=round_to_lts_version)

    monkeypatch.setattr(jv, "detect_jar_java_version", counting)

    assert jar_java_version(art, cache) == 8
    assert jar_java_version(art, cache) == 8
    assert calls["n"] == 1  # second call served from the in-process memo


def test_unresolvable_artifact_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(jv, "_MEMO", {})

    class _Broken(_StubArtifact):
        def resolve(self):
            raise RuntimeError("not found")

    art = _Broken(tmp_path / "missing.jar", "com.example", "x", "1.0.0")
    assert jar_java_version(art, tmp_path / "cache") is None

"""
Test locating a project's local build output (e.g. target/classes) from its POM.
"""

from pathlib import Path

from jgo.maven import POM, MavenContext


def _write_pom(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<project xmlns="http://maven.apache.org/POM/4.0.0">\n'
        "  <modelVersion>4.0.0</modelVersion>\n"
        f"{body}\n"
        "</project>\n"
    )
    return path


def test_build_outputs_defaults(tmp_path):
    """With no <build> settings, the super POM's layout applies."""
    pom_path = _write_pom(
        tmp_path / "proj" / "pom.xml",
        "  <groupId>org.example</groupId>\n"
        "  <artifactId>demo</artifactId>\n"
        "  <version>1.0.0-SNAPSHOT</version>",
    )
    context = MavenContext(repo_cache=tmp_path / "repo")

    classes_dir, jar = context.pom_build_outputs(POM(pom_path))

    assert classes_dir == tmp_path / "proj" / "target" / "classes"
    assert jar == tmp_path / "proj" / "target" / "demo-1.0.0-SNAPSHOT.jar"


def test_build_outputs_inherited_and_interpolated(tmp_path):
    """<build> settings are inherited from the parent; the child's take precedence."""
    repo = tmp_path / "repo"
    _write_pom(
        repo / "org" / "example" / "parent" / "1" / "parent-1.pom",
        "  <groupId>org.example</groupId>\n"
        "  <artifactId>parent</artifactId>\n"
        "  <version>1</version>\n"
        "  <packaging>pom</packaging>\n"
        "  <build>\n"
        "    <directory>${project.basedir}/build</directory>\n"
        "    <finalName>${project.artifactId}-parent-named</finalName>\n"
        "  </build>",
    )
    pom_path = _write_pom(
        tmp_path / "proj" / "pom.xml",
        "  <parent>\n"
        "    <groupId>org.example</groupId>\n"
        "    <artifactId>parent</artifactId>\n"
        "    <version>1</version>\n"
        "  </parent>\n"
        "  <artifactId>child</artifactId>\n"
        "  <build>\n"
        "    <outputDirectory>out/main</outputDirectory>\n"
        "  </build>",
    )
    context = MavenContext(repo_cache=repo)

    classes_dir, jar = context.pom_build_outputs(POM(pom_path))

    # Relative paths resolve against the child project's base directory.
    assert classes_dir == tmp_path / "proj" / "out" / "main"
    assert jar == tmp_path / "proj" / "build" / "child-parent-named.jar"

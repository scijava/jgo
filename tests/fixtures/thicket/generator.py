#!/usr/bin/env python

"""
Generate a complex collection of parent POMs and BOMs, and a project
that inherits from them. The goal is to better understand how Maven POM
interpolation works, and test the correctness of jgo's implementation.
"""

import random
from pathlib import Path
from xml.etree import ElementTree as ET

# -- Constants --

# Register the Maven POM namespace
ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")
ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

TEMPLATE: bytes = """\
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" \
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
\t<modelVersion>4.0.0</modelVersion>
</project>
""".encode("UTF-8")

# for l in a b c d e f g h i j k l m n o p q r s t u v w x y z
# do
# grep "^$l.\{4\}" google-10000-english-usa-no-swears.txt | grep -v '.\{8\}' | shuf | head -n1
# done
# fmt: off
NAMES = [
    "active", "bullet", "coral", "detail", "essence", "fonts", "games",
    "heating", "ignore", "journal", "knives", "lodge", "major", "neutral",
    "optics", "permits", "quoted", "rotary", "socket", "tickets",
    "upload", "vendors", "weight", "xhtml", "younger", "zoning",
]
# fmt: on

GROUP_ID = "org.scijava.jgo.thicket"
ANCESTOR_COUNT = 4
MAX_IMPORTS = 3
MAX_DEPTH = 8
DEFAULT_SEED = 42  # Fixed seed for reproducible tests


# -- Functions --

# Maven namespace
MAVEN_NS = "{http://maven.apache.org/POM/4.0.0}"


def create_child(element, tagname, text=None):
    # Add namespace to tag name
    qualified_tag = f"{MAVEN_NS}{tagname}"
    child = ET.SubElement(element, qualified_tag)
    if text:
        child.text = text
    return child


class ThicketGenerator:
    """Generator for thicket POMs with configurable random seed."""

    def __init__(self, output_dir: Path, seed: int = DEFAULT_SEED):
        """
        Initialize the thicket generator.

        Args:
            output_dir: Directory where POMs will be written
            seed: Random seed for reproducible generation
        """
        self.output_dir = Path(output_dir)
        self.versions: set[int] = set()
        random.seed(seed)

    def random_version(self) -> str:
        """Generate a unique random version number."""
        assert len(self.versions) < 9999
        v = random.randint(0, 9999)
        while v in self.versions:
            v = random.randint(0, 9999)
        self.versions.add(v)
        return str(v)

    def generate_pom(
        self, name, packaging=None, version=None, ancestor_count=ANCESTOR_COUNT, depth=0
    ):
        """
        Generate a POM file with the given parameters.

        Args:
            name: Artifact ID for this POM
            packaging: POM packaging type (default: jar)
            version: Version string (auto-generated if None)
            ancestor_count: Number of parent POMs to generate
            depth: Current depth in the hierarchy (for limiting imports)
        """
        root = ET.fromstring(TEMPLATE)
        if ancestor_count > 0:
            parent = create_child(root, "parent")
            parent_name = f"{name}-parent{ancestor_count}"
            v = self.random_version()
            create_child(parent, "groupId", GROUP_ID)
            create_child(parent, "artifactId", parent_name)
            create_child(parent, "version", v)
            create_child(parent, "relativePath")
            self.generate_pom(
                parent_name,
                packaging="pom",
                version=v,
                ancestor_count=ancestor_count - 1,
                depth=depth + 1,
            )
        else:
            create_child(root, "groupId", GROUP_ID)

        create_child(root, "artifactId", name)
        create_child(root, "version", version or self.random_version())
        if packaging:
            create_child(root, "packaging", packaging)

        bom_count = min(MAX_IMPORTS - depth, random.randint(0, MAX_IMPORTS))
        dep_mgmt = create_child(root, "dependencyManagement")
        dep_mgmt_deps = create_child(dep_mgmt, "dependencies")
        for i in range(bom_count):
            dep = create_child(dep_mgmt_deps, "dependency")
            bom_name = f"{name}-bom{i + 1}"
            create_child(dep, "groupId", GROUP_ID)
            create_child(dep, "artifactId", bom_name)
            # TODO: Sometimes use properties; sometimes allow the version to be managed.
            v = self.random_version()
            create_child(dep, "version", v)
            create_child(dep, "type", "pom")
            create_child(dep, "scope", "import")
            self.generate_pom(
                bom_name,
                packaging="pom",
                version=v,
                ancestor_count=ancestor_count,
                depth=depth + 1,
            )

        # Manage some dependencies.
        properties = None
        dep_count = random.randint(0, 5)
        deps = set(random.choices(NAMES, k=dep_count))
        for artifact_id in deps:
            dep = create_child(dep_mgmt_deps, "dependency")
            create_child(dep, "groupId", GROUP_ID)
            create_child(dep, "artifactId", artifact_id)
            # Sometimes use a property for the version, but other times not.
            # - Sometimes we want to define the property also in this POM, sometimes not.
            # - Sometimes we want to add an explicit version element override here, sometimes not.
            # TODO: Sometimes allow the version to be managed.
            v = self.random_version()
            use_property = random.choice((True, False))
            if use_property:
                if properties is None:
                    properties = create_child(root, "properties")
                prop_tag = artifact_id + ".version"
                create_child(properties, prop_tag, v)
                v = "${" + prop_tag + "}"
            create_child(dep, "version", v)
            # TODO: Consider randomizing classifier and/or scope of these as well.

        # Pretty-print the XML
        ET.indent(root, space="\t", level=0)

        # Write to file with XML declaration
        tree = ET.ElementTree(root)
        with open((self.output_dir / name).with_suffix(".pom"), "wb") as f:
            tree.write(f, encoding="UTF-8", xml_declaration=True)

    def generate(self):
        """Generate the complete thicket POM hierarchy."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Generate thicket as a normal (jar) artifact
        # Note: The jar itself doesn't exist, but the Python resolver doesn't need it
        # and the tests focus on dependency resolution, not artifact downloading
        self.generate_pom("thicket")


# -- Main --


def generate_thicket(output_dir: Path, seed: int = DEFAULT_SEED):
    """
    Generate thicket POMs in the specified directory.

    Args:
        output_dir: Directory where POMs will be written
        seed: Random seed for reproducible generation (default: 42)
    """
    generator = ThicketGenerator(output_dir, seed)
    generator.generate()


if __name__ == "__main__":
    import sys

    # Allow specifying seed and output directory from command line
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SEED
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")

    print(f"Generating thicket POMs with seed={seed} in {output_dir}")
    generate_thicket(output_dir, seed)
    print("Done!")

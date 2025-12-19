"""
Maven POM (Project Object Model) parsing and handling.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from ..parse.coordinate import Coordinate


def parse_dependency_element_to_coordinate(
    el: ElementTree.Element,
) -> tuple[Coordinate, list[tuple[str, str]]]:
    """
    Parse a <dependency> XML element into a Coordinate plus exclusions data.

    This function bridges the XML parsing layer (pom.py) and the data layer (endpoint.py),
    allowing core.py to work with Coordinates without touching ElementTree.

    :param el: The XML element to parse.
    :return: Tuple of (Coordinate object, list of exclusion (groupId, artifactId) tuples)
    """
    groupId = el.findtext("groupId")
    artifactId = el.findtext("artifactId")
    version = el.findtext("version")  # NB: Might be None, which means managed.
    classifier = el.findtext("classifier")
    packaging = el.findtext("type")
    scope = el.findtext("scope")
    optional = el.findtext("optional") == "true"

    # Parse exclusions as list of (groupId, artifactId) tuples
    exclusions = [
        (ex.findtext("groupId"), ex.findtext("artifactId"))
        for ex in el.findall("exclusions/exclusion")
    ]

    coord = Coordinate(
        groupId=groupId,
        artifactId=artifactId,
        version=version,
        classifier=classifier,
        packaging=packaging,
        scope=scope,
        optional=optional,
    )

    return coord, exclusions


class XML:
    """Base class for XML document wrappers."""

    def __init__(self, source: Path | str):
        self.source = source
        self.tree: ElementTree.ElementTree = (
            ElementTree.ElementTree(ElementTree.fromstring(source))
            if isinstance(source, str)
            else ElementTree.parse(source)
        )
        XML._strip_ns(self.tree.getroot())

    def dump(self, el: ElementTree.Element = None) -> str:
        """
        Get a string representation of the given XML element.
        :param el: Element to stringify, or None to stringify the root node.
        :return: The XML as a string.
        """
        # NB: Be careful: childless ElementTree.Element objects are falsy!
        if el is None:
            el = self.tree.getroot()
        return ElementTree.tostring(el).decode()

    def elements(self, path: str) -> list[ElementTree.Element]:
        return self.tree.findall(path)

    def element(self, path: str) -> ElementTree.Element | None:
        els = self.elements(path)
        assert len(els) <= 1
        return els[0] if els else None

    def values(self, path: str) -> list[str]:
        return [el.text for el in self.elements(path)]

    def value(self, path: str) -> str | None:
        el = self.element(path)
        # NB: Be careful: childless ElementTree.Element objects are falsy!
        return None if el is None else el.text

    @staticmethod
    def _strip_ns(el: ElementTree.Element) -> None:
        """
        Remove namespace prefixes from elements and attributes.
        Credit: https://stackoverflow.com/a/32552776/1207769
        """
        if el.tag.startswith("{"):
            el.tag = el.tag[el.tag.find("}") + 1 :]
        for k in list(el.attrib.keys()):
            if k.startswith("{"):
                k2 = k[k.find("}") + 1 :]
                el.attrib[k2] = el.attrib[k]
                del el.attrib[k]
        for child in el:
            XML._strip_ns(child)


class POM(XML):
    """
    Convenience wrapper around a Maven POM XML document.
    """

    @property
    def groupId(self) -> str | None:
        """The POM's <groupId> (or <parent><groupId>) value."""
        return self.value("groupId") or self.value("parent/groupId")

    @property
    def artifactId(self) -> str | None:
        """The POM's <artifactId> value."""
        return self.value("artifactId")

    @property
    def version(self) -> str | None:
        """The POM's <version> (or <parent><version>) value."""
        return self.value("version") or self.value("parent/version")

    @property
    def name(self) -> str | None:
        """The POM's <name> value."""
        return self.value("name")

    @property
    def description(self) -> str | None:
        """The POM's <description> value."""
        return self.value("description")

    @property
    def scmURL(self) -> str | None:
        """The POM's <scm><url> value."""
        return self.value("scm/url")

    @property
    def issuesURL(self) -> str | None:
        """The POM's <issueManagement><url> value."""
        return self.value("issueManagement/url")

    @property
    def ciURL(self) -> str | None:
        """The POM's <ciManagement><url> value."""
        return self.value("ciManagement/url")

    @property
    def developers(self) -> list[dict[str, Any]]:
        """Dictionary of the POM's <developer> entries."""
        return self._people("developers/developer")

    @property
    def contributors(self) -> list[dict[str, Any]]:
        """Dictionary of the POM's <contributor> entries."""
        return self._people("contributors/contributor")

    def _people(self, path: str) -> list[dict[str, Any]]:
        people = []
        for el in self.elements(path):
            person: dict[str, Any] = {}
            for child in el:
                if len(child) == 0:
                    person[child.tag] = child.text
                else:
                    if child.tag == "properties":
                        for grand in child:
                            person[grand.tag] = grand.text
                    else:
                        person[child.tag] = [grand.text for grand in child]
            people.append(person)
        return people

    @property
    def properties(self) -> dict[str, str]:
        """Dictionary of key/value pairs from the POM's <properties>."""
        return {el.tag: el.text for el in self.elements("properties/*")}


def write_pom(pom: POM, dest: Path | str) -> None:
    Path(dest).write_text(pom.source)


def write_temp_pom(pom: POM) -> Path:
    """
    Write a POM object to a temporary file.

    Args:
        pom: POM object to write

    Returns:
        Path to the generated temporary POM file
    """
    import tempfile

    temp_file = Path(tempfile.mktemp(suffix=".pom.xml", prefix="jgo-"))
    write_pom(pom, temp_file)

    return temp_file

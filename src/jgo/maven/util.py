"""
Utility functions for Maven operations.
"""

from datetime import datetime
from pathlib import Path
from re import match
from typing import Optional, Union


def ts2dt(ts: str) -> datetime:
    """
    Convert a Maven-style timestamp string into a Python datetime object.

    Valid forms:
    * 20210702144918 (seen in <lastUpdated> in maven-metadata.xml)
    * 20210702.144917 (seen in deployed SNAPSHOT filenames and <snapshotVersion><value>)
    """
    m = match(r"(\d{4})(\d\d)(\d\d)\.?(\d\d)(\d\d)(\d\d)", ts)
    if not m:
        raise ValueError(f"Invalid timestamp: {ts}")
    return datetime(*map(int, m.groups()))  # noqa


def coord2str(
    groupId: str,
    artifactId: str,
    version: Optional[str] = None,
    classifier: Optional[str] = None,
    packaging: Optional[str] = None,
    scope: Optional[str] = None,
    optional: bool = False,
) -> str:
    """
    Return a string representation of the given Maven coordinates.

    For an overview of Maven coordinates, see:
    * https://maven.apache.org/pom.html#Maven_Coordinates
    * https://maven.apache.org/pom.html#dependencies

    :param groupId: The groupId of the Maven coordinate.
    :param artifactId: The artifactId of the Maven coordinate.
    :param version The version of the Maven coordinate.
    :param classifier: The classifier of the Maven coordinate.
    :param packaging: The packaging/type of the Maven coordinate.
    :param scope: The scope of the Maven dependency.
    :param optional: Whether the Maven dependency is optional.
    :return:
        A string encompassing the given fields, matching the
        G:A:P:C:V:S order used by mvn's dependency:list goal.
    """
    s = f"{groupId}:{artifactId}"
    if packaging:
        s += f":{packaging}"
    if classifier:
        s += f":{classifier}"
    if version:
        s += f":{version}"
    if scope:
        s += f":{scope}"
    if optional:
        s += " (optional)"
    return s


def read(p: Path, mode: str) -> Union[str, bytes]:
    """Read a file in the specified mode."""
    with open(p, mode) as f:
        return f.read()


def text(p: Path) -> str:
    """Read a text file."""
    return read(p, "r")


def binary(p: Path) -> bytes:
    """Read a binary file."""
    return read(p, "rb")

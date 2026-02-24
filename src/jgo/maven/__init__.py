"""
Maven dependency resolution for Python.

This module provides pure-Python Maven functionality including:
- Dependency resolution (transitive dependencies, scopes, exclusions)
- POM parsing and property interpolation
- Metadata querying (available versions, release/snapshot)
- Artifact downloading from Maven repositories
"""

from ._core import (
    Artifact,
    Component,
    Dependency,
    DependencyNode,
    MavenContext,
    Project,
    Resolver,
)
from ._metadata import Metadata, Metadatas, MetadataXML
from ._model import Model, ProfileConstraints
from ._pom import POM, XML
from ._resolver import MvnResolver, PythonResolver
from ._version import (
    MavenVersion,
    VersionRange,
    compare_semver,
    compare_versions,
    is_semver_1x,
    parse_version_range,
    version_in_range,
)

__all__ = [
    # core
    "Artifact",
    "Component",
    "Dependency",
    "DependencyNode",
    "MavenContext",
    "Project",
    # metadata
    "Metadata",
    "Metadatas",
    "MetadataXML",
    # model
    "Model",
    "ProfileConstraints",
    # pom
    "POM",
    "XML",
    # resolver
    "MvnResolver",
    "PythonResolver",
    "Resolver",
    # version
    "MavenVersion",
    "VersionRange",
    "compare_semver",
    "compare_versions",
    "is_semver_1x",
    "parse_version_range",
    "version_in_range",
]

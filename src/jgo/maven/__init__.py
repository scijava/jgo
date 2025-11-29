"""
Maven dependency resolution for Python.

This module provides pure-Python Maven functionality including:
- Dependency resolution (transitive dependencies, scopes, exclusions)
- POM parsing and property interpolation
- Metadata querying (available versions, release/snapshot)
- Artifact downloading from Maven repositories
"""

from .core import (
    Artifact,
    Component,
    Dependency,
    MavenContext,
    Project,
    XML,
    DEFAULT_CLASSIFIER,
    DEFAULT_PACKAGING,
)
from .metadata import Metadata, MetadataXML, Metadatas
from .model import Model
from .pom import POM
from .resolver import MavenResolver, Resolver, SimpleResolver
from .util import coord2str, ts2dt

__all__ = [
    # Core classes
    "MavenContext",
    "Project",
    "Component",
    "Artifact",
    "Dependency",
    "XML",
    # Resolvers
    "Resolver",
    "SimpleResolver",
    "MavenResolver",
    # POM and metadata
    "POM",
    "Metadata",
    "MetadataXML",
    "Metadatas",
    "Model",
    # Constants
    "DEFAULT_CLASSIFIER",
    "DEFAULT_PACKAGING",
    # Utilities
    "coord2str",
    "ts2dt",
]

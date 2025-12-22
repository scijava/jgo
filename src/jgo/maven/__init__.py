"""
Maven dependency resolution for Python.

This module provides pure-Python Maven functionality including:
- Dependency resolution (transitive dependencies, scopes, exclusions)
- POM parsing and property interpolation
- Metadata querying (available versions, release/snapshot)
- Artifact downloading from Maven repositories
"""

from .core import (
    DEFAULT_CLASSIFIER,
    DEFAULT_PACKAGING,
    Artifact,
    Component,
    Dependency,
    MavenContext,
    Project,
)
from .metadata import Metadata, Metadatas, MetadataXML
from .model import Model
from .pom import POM, XML
from .resolver import MvnResolver, PythonResolver, Resolver

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
    "PythonResolver",
    "MvnResolver",
    # POM and metadata
    "POM",
    "Metadata",
    "MetadataXML",
    "Metadatas",
    "Model",
    # Constants
    "DEFAULT_CLASSIFIER",
    "DEFAULT_PACKAGING",
]

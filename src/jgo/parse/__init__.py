"""
Maven coordinate and endpoint parsing and representation.

This module provides simple data structures for representing and parsing Maven
coordinates and endpoints. These are "dumb" data structures that hold parsed
components (groupId, artifactId, version, etc.) but do not perform any Maven
operations like:
- Version resolution (RELEASE, LATEST)
- Dependency management
- POM interpolation
- Artifact downloading
- Transitive dependency resolution

For "smart" data structures capable of Maven resolution and interpolation,
see the jgo.maven subpackage.
"""

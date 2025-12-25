"""
Thicket test fixture generator.

The thicket is a complex hierarchy of Maven POMs designed to test:
- Multi-level parent POM inheritance
- BOM imports and transitive imports
- Property-based versioning and interpolation
- Complex dependency management

Usage:
    from tests.fixtures.thicket import generate_thicket

    generate_thicket(output_dir, seed=42)
"""

from .generator import DEFAULT_SEED, generate_thicket

__all__ = ["generate_thicket", "DEFAULT_SEED"]

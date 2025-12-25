"""Pytest configuration and shared fixtures."""

import pytest
from tests.fixtures.thicket import DEFAULT_SEED, generate_thicket


@pytest.fixture(scope="session")
def thicket_poms(tmp_path_factory):
    """
    Generate thicket POMs for testing.

    This is a session-scoped fixture that generates the thicket POM hierarchy
    once at the beginning of the test session. The POMs are generated with a
    fixed random seed for reproducibility.

    Returns:
        Path: Directory containing generated thicket POMs
    """
    # Create a temporary directory for this test session
    pom_dir = tmp_path_factory.mktemp("thicket_poms")

    # Generate the thicket POMs with a fixed seed for reproducibility
    generate_thicket(pom_dir, seed=DEFAULT_SEED)

    return pom_dir

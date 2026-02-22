"""Pytest configuration and shared fixtures."""

import shutil
import subprocess
from pathlib import Path

import pytest
from tests.fixtures.thicket import DEFAULT_SEED, generate_thicket

from jgo.util._maven import ensure_maven_available


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


@pytest.fixture(scope="session")
def m2_repo(tmp_path_factory):
    """
    Provide a bootstrapped Maven repository for testing.

    This fixture creates a cached Maven repository in .cache/m2_repo that
    contains Maven's own infrastructure JARs. On first run, these are
    downloaded from Maven Central. On subsequent runs, the cache is reused,
    making tests much faster.

    For each test session, the cache is copied to a temporary directory to
    provide test isolation while still benefiting from pre-downloaded Maven
    infrastructure.

    Returns:
        Path: Temporary Maven repository directory for this test session
    """
    # Ensure cache directory exists
    cache_dir = Path(".cache/m2_repo")
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Bootstrap Maven infrastructure by running commands that will download
    # Maven's own plugins and dependencies
    bootstrap_pom = Path(__file__).parent / "fixtures" / "bootstrap-pom.xml"
    maven_cmd = ensure_maven_available()

    # Run the Maven commands that tests will actually use
    # If cache is already populated, these will be quick no-ops
    for goal in ["dependency:list", "dependency:tree"]:
        subprocess.run(
            [
                maven_cmd,
                "-f",
                str(bootstrap_pom),
                f"-Dmaven.repo.local={cache_dir}",
                goal,
            ],
            check=True,
            capture_output=True,
        )

    # Copy cache to temp directory for test isolation
    test_repo = tmp_path_factory.mktemp("m2_repo")
    shutil.copytree(cache_dir, test_repo, dirs_exist_ok=True)

    return test_repo

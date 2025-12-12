"""
Java source and locator for jgo.

Handles finding or downloading the appropriate Java executable.
"""

from __future__ import annotations

import subprocess
import sys
from enum import Enum
from pathlib import Path

import cjdk


class JavaSource(Enum):
    """
    Strategy for locating Java executable.
    """

    SYSTEM = "system"  # Use system Java (from PATH or JAVA_HOME)
    CJDK = "cjdk"  # Use cjdk to download/manage Java


class JavaLocator:
    """
    Locates or downloads Java executables based on requirements.

    Integrates with cjdk for automatic Java version management.
    """

    def __init__(
        self,
        java_source: JavaSource = JavaSource.CJDK,
        java_version: int | None = None,
        java_vendor: str | None = None,
        verbose: bool = False,
    ):
        """
        Initialize Java locator.

        Args:
            java_source: Strategy for locating Java
            java_version: Desired Java version (e.g., 17)
            java_vendor: Desired Java vendor (e.g., "adoptium", "zulu")
            verbose: Enable verbose output
        """
        self.java_source = java_source
        self.java_version = java_version
        # Default to "zulu" vendor for cjdk since it has the widest Java version support
        # (including Java 8 which adoptium lacks)
        self.java_vendor = java_vendor or "zulu"
        self.verbose = verbose

    def locate(self, min_version: int | None = None) -> Path:
        """
        Locate or download appropriate Java executable.

        Args:
            min_version: Minimum required Java version (from bytecode detection)

        Returns:
            Path to java executable

        Raises:
            RuntimeError: If Java cannot be located or version requirement cannot be met
        """
        # Determine effective version requirement
        required_version = self.java_version or min_version

        # Select strategy
        if self.java_source == JavaSource.SYSTEM:
            return self._locate_system_java(required_version)
        elif self.java_source == JavaSource.CJDK:
            return self._locate_cjdk_java(required_version)
        else:
            raise ValueError(f"Unknown JavaSource: {self.java_source}")

    def _locate_system_java(self, required_version: int | None = None) -> Path:
        """
        Locate system Java executable.

        Args:
            required_version: Minimum required Java version

        Returns:
            Path to java executable

        Raises:
            RuntimeError: If java not found or version too old
        """
        # Try to find java executable
        java_path = self._find_java_in_path()
        if java_path is None:
            raise RuntimeError(
                "Java not found. Please install Java or use jgo[cjdk] for automatic Java management."
            )

        # Check version if required
        if required_version is not None:
            actual_version = self._get_java_version(java_path)
            if actual_version < required_version:
                raise RuntimeError(
                    f"Java {required_version} or higher required, but system Java is version {actual_version}. "
                    f"Please upgrade Java or use jgo[cjdk] for automatic Java management."
                )
            elif self.verbose:
                print(
                    f"Using system Java {actual_version} at {java_path}",
                    file=sys.stderr,
                )

        return java_path

    def _locate_cjdk_java(self, required_version: int | None = None) -> Path:
        """
        Locate Java using cjdk.

        Args:
            required_version: Desired Java version

        Returns:
            Path to java executable

        Raises:
            RuntimeError: If cjdk fails
        """

        # Default to latest LTS if no version specified
        version = required_version or 21

        if self.verbose:
            print(f"Obtaining Java {version} via cjdk...", file=sys.stderr)

        try:
            # Get or download Java via cjdk
            java_home = cjdk.java_home(version=str(version), vendor=self.java_vendor)
            java_path = Path(java_home) / "bin" / "java"

            if not java_path.exists():
                raise RuntimeError(f"cjdk returned invalid Java path: {java_path}")

            if self.verbose:
                actual_version = self._get_java_version(java_path)
                vendor_info = f" ({self.java_vendor})" if self.java_vendor else ""
                print(
                    f"Using Java {actual_version}{vendor_info} at {java_path}",
                    file=sys.stderr,
                )

            return java_path

        except Exception as e:
            raise RuntimeError(f"Failed to obtain Java via cjdk: {e}")

    def _find_java_in_path(self) -> Path | None:
        """
        Find java executable in PATH or JAVA_HOME.

        Returns:
            Path to java executable, or None if not found
        """
        import os
        import shutil

        # Check JAVA_HOME first
        java_home = os.environ.get("JAVA_HOME")
        if java_home:
            java_path = Path(java_home) / "bin" / "java"
            if java_path.exists():
                return java_path

        # Check PATH
        java_cmd = shutil.which("java")
        if java_cmd:
            return Path(java_cmd)

        return None

    def _get_java_version(self, java_path: Path) -> int:
        """
        Get Java version from executable.

        Args:
            java_path: Path to java executable

        Returns:
            Java major version (e.g., 17)

        Raises:
            RuntimeError: If version cannot be determined
        """
        try:
            result = subprocess.run(
                [str(java_path), "-version"], capture_output=True, text=True, timeout=5
            )

            # Java version output goes to stderr
            version_output = result.stderr

            # Parse version string
            # Examples:
            #   "java version "1.8.0_292""
            #   "openjdk version "11.0.11" 2021-04-20"
            #   "openjdk version "17.0.1" 2021-10-19"
            import re

            match = re.search(r'version "([^"]+)"', version_output)
            if not match:
                raise RuntimeError(
                    f"Could not parse Java version from: {version_output}"
                )

            version_str = match.group(1)

            # Parse major version
            # Handle both old format (1.8.x) and new format (11.x, 17.x)
            parts = version_str.split(".")
            if parts[0] == "1":
                # Old format: 1.8.x -> version 8
                return int(parts[1])
            else:
                # New format: 17.x -> version 17
                return int(parts[0])

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Timeout while checking Java version at {java_path}")
        except Exception as e:
            raise RuntimeError(f"Failed to determine Java version: {e}")

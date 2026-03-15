"""
Classes and functions for working with Maven profiles.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class ProfileConstraints:
    """Constraints for profile activation."""

    jdk: str | None = None
    os_name: str | None = None
    os_family: str | None = None
    os_arch: str | None = None
    os_version: str | None = None
    properties: dict[str, str] = field(default_factory=dict)
    file_exists: Callable[[str], bool] = field(default=os.path.exists)
    basedir: str = "."
    lenient: bool = False


def detect_os_properties() -> tuple[str, str, str]:
    """
    Detect current platform as (os_name, os_family, os_arch).

    Returns values that match Maven's OS property conventions for use in
    profile activation.
    """
    system = platform.system()
    machine = platform.machine()

    # Map system -> (os_name, os_family)
    # Match Maven's OS family conventions from plexus-utils
    if system == "Linux":
        os_name, os_family = "Linux", "unix"
    elif system == "Darwin":
        os_name, os_family = "Mac OS X", "mac"
    elif system == "Windows":
        os_name, os_family = "Windows", "windows"
    elif system == "FreeBSD":
        os_name, os_family = "FreeBSD", "unix"
    elif system == "OpenBSD":
        os_name, os_family = "OpenBSD", "unix"
    elif system == "NetBSD":
        os_name, os_family = "NetBSD", "unix"
    elif system in ("SunOS", "Solaris"):
        os_name, os_family = "SunOS", "unix"
    elif system == "AIX":
        os_name, os_family = "AIX", "unix"
    else:
        # Unknown system - use the raw value
        os_name, os_family = system or "Unknown", "unknown"

    # Map machine -> os_arch (Python -> Java conventions)
    # Java uses different arch names than Python in some cases
    arch_map = {
        "x86_64": "amd64",  # Linux 64-bit
        "AMD64": "amd64",  # Windows 64-bit
        "arm64": "aarch64",  # macOS ARM (M1/M2/M3)
        "aarch64": "aarch64",  # Linux ARM
        "i386": "i386",  # Linux 32-bit
        "i486": "i386",
        "i586": "i386",
        "i686": "i386",
        "x86": "x86",  # Windows 32-bit
    }
    os_arch = arch_map.get(machine, machine)

    return os_name, os_family, os_arch

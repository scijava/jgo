"""
Subcommands for jgo CLI.

Each subcommand is implemented in its own module with:
- execute(args, config) -> int
"""

from __future__ import annotations

from pathlib import Path

__all__ = ["parse_requirements_file"]


def parse_requirements_file(path: Path) -> list[str]:
    """
    Read Maven coordinates from a requirements file.

    Lines starting with '#' and blank lines are ignored.

    Args:
        path: Path to the requirements file

    Returns:
        List of coordinate strings
    """
    coords = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            coords.append(line)
    return coords

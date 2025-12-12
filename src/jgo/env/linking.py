"""
Linking strategies for jgo.

Defines how to link JAR files from Maven repository to jgo cache.
"""

import errno
import os
import shutil
from enum import Enum
from pathlib import Path


class LinkStrategy(Enum):
    """
    How to link JAR files from Maven repository to jgo cache.
    """

    HARD = "hard"
    SOFT = "soft"
    COPY = "copy"
    AUTO = "auto"


def link_file(source: Path, link_name: Path, strategy: LinkStrategy):
    """
    Link a file using the specified strategy.

    :param source: Source file path
    :param link_name: Target link path
    :param strategy: Link strategy to use
    """
    if strategy == LinkStrategy.HARD:
        return os.link(source, link_name)
    elif strategy == LinkStrategy.SOFT:
        return os.symlink(source, link_name)
    elif strategy == LinkStrategy.COPY:
        return shutil.copyfile(source, link_name)
    elif strategy == LinkStrategy.AUTO:
        # Try hard link first
        try:
            return os.link(source, link_name)
        except OSError as e:
            # Only fall back if it's a cross-device link error
            # Re-raise other errors (permissions, file not found, etc.)
            if e.errno != errno.EXDEV:
                raise

        # Try soft link next
        try:
            return os.symlink(source, link_name)
        except OSError as e:
            # If symlink fails for reasons other than permission or cross-device,
            # fall through to copy
            if e.errno not in (errno.EPERM, errno.EACCES, errno.EXDEV):
                raise

        # Fall back to copy
        return shutil.copyfile(source, link_name)

    raise ValueError(f"Unsupported link strategy: {strategy}")

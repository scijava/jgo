"""
Linking strategies for jgo 2.0.

Defines how to link JAR files from Maven repository to jgo cache.
"""

from enum import Enum
from pathlib import Path
import os
import shutil

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
        try:
            return os.link(source, link_name)
        except OSError as e:
            if e.errno != 18:  # Different filesystem error
                raise e
        try:
            return os.symlink(source, link_name)
        except OSError:
            pass

        return shutil.copyfile(source, link_name)

    raise ValueError(f"Unsupported link strategy: {strategy}")

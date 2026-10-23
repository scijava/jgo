"""
Linking strategies for jgo.

Defines how to link JAR files from Maven repository to jgo cache.
"""

import errno
import os
import shutil
import sys
from enum import Enum
from pathlib import Path


class LinkStrategy(Enum):
    """
    How to link JAR files from Maven repository to jgo cache.
    """

    REFLINK = "reflink"
    HARD = "hard"
    SOFT = "soft"
    COPY = "copy"
    AUTO = "auto"


# Errors indicating that reflinks are unsupported for the given source/target,
# as opposed to real failures (permissions, file not found, etc.).
_REFLINK_UNSUPPORTED = {
    errno.EXDEV,
    errno.EINVAL,
    errno.ENOTTY,
    errno.EOPNOTSUPP,
    getattr(errno, "ENOTSUP", errno.EOPNOTSUPP),
    getattr(errno, "ENOSYS", errno.EOPNOTSUPP),
}

# Linux ioctl request code for FICLONE: _IOW(0x94, 9, int).
_FICLONE = 0x40049409


def reflink(source: Path, link_name: Path):
    """
    Create a copy-on-write clone (reflink) of a file.

    Uses the FICLONE ioctl on Linux (e.g. Btrfs, XFS, bcachefs, ZFS) and
    clonefile(2) on macOS (APFS). Raises OSError with errno EOPNOTSUPP on
    platforms or filesystems without reflink support, or EXDEV when source
    and target are on different filesystems.

    Args:
        source: Source file path
        link_name: Target file path (must not already exist)
    """
    if sys.platform == "darwin":
        return _clonefile(source, link_name)
    if sys.platform.startswith("linux"):
        return _ficlone(source, link_name)
    raise OSError(
        errno.EOPNOTSUPP, f"Reflinks not supported on {sys.platform}", str(link_name)
    )


def _clonefile(source: Path, link_name: Path):
    import ctypes

    libc = ctypes.CDLL(None, use_errno=True)
    clonefile = getattr(libc, "clonefile", None)
    if clonefile is None:
        raise OSError(errno.EOPNOTSUPP, "clonefile unavailable", str(link_name))
    clonefile.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint32)
    clonefile.restype = ctypes.c_int
    if clonefile(os.fsencode(source), os.fsencode(link_name), 0) != 0:
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err), str(link_name))


def _ficlone(source: Path, link_name: Path):
    import fcntl

    with open(source, "rb") as src:
        # Note: O_EXCL ensures we never clobber, nor later delete, an existing file.
        fd = os.open(link_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        try:
            fcntl.ioctl(fd, _FICLONE, src.fileno())
        except OSError:
            os.close(fd)
            os.unlink(link_name)
            raise
        os.close(fd)
    shutil.copymode(source, link_name)


def link_file(source: Path, link_name: Path, strategy: LinkStrategy):
    """
    Link a file using the specified strategy.

    Args:
        source: Source file path
        link_name: Target link path
        strategy: Link strategy to use
    """
    if strategy == LinkStrategy.REFLINK:
        return reflink(source, link_name)
    elif strategy == LinkStrategy.HARD:
        return os.link(source, link_name)
    elif strategy == LinkStrategy.SOFT:
        return os.symlink(source, link_name)
    elif strategy == LinkStrategy.COPY:
        return shutil.copyfile(source, link_name)
    elif strategy == LinkStrategy.AUTO:
        # Try reflink first: zero disk overhead, but isolated from source edits
        try:
            return reflink(source, link_name)
        except OSError as e:
            # Only fall back if reflinks are unsupported here
            if e.errno not in _REFLINK_UNSUPPORTED:
                raise

        # Try hard link next
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

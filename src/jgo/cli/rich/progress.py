"""
Progress reporting for jgo CLI using Rich.

Provides progress callbacks for download operations.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import TYPE_CHECKING

from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from ...util.console import get_err_console, is_quiet

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


@contextmanager
def download_progress_callback(
    filename: str, total_size: int
) -> Iterator[Callable[[int], None]]:
    """
    Create a Rich progress bar for download operations.

    This is a context manager that yields an update function for reporting
    download progress. It respects quiet mode and NO_PROGRESS environment variable.

    Args:
        filename: Name of file being downloaded
        total_size: Total size in bytes

    Yields:
        Update function that accepts bytes_count to report progress

    Example:
        >>> with download_progress_callback("file.jar", 1000) as update:
        ...     for chunk in download_chunks():
        ...         update(len(chunk))
    """
    # Skip progress bar if in quiet mode or NO_PROGRESS is set
    if is_quiet() or os.environ.get("NO_PROGRESS"):
        # Yield a no-op update function
        yield lambda bytes_count: None
        return

    # Create progress bar for this download
    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=get_err_console(),
    )

    with progress:
        task = progress.add_task(f"Downloading {filename}", total=total_size)

        def update_progress(bytes_count: int) -> None:
            """Update progress bar with downloaded bytes."""
            progress.update(task, advance=bytes_count)

        yield update_progress

"""
Rich library utilities and extensions for jgo.

Provides custom Rich components that respect jgo's output settings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.table import Table
from rich.tree import Tree

if TYPE_CHECKING:
    from rich.console import Console, ConsoleOptions, RenderResult


class NoWrapTree(Tree):
    """
    A Tree that doesn't wrap long lines.

    When printed with soft_wrap=True, this tree renders with unlimited width,
    allowing long lines to extend beyond the terminal width without being
    wrapped or truncated.

    Usage:
        tree = NoWrapTree("Root")
        tree.add("Long dependency name...")
        console.print(tree, soft_wrap=True)
    """

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Render tree with unlimited width to prevent wrapping."""
        # Use a very large max_width to prevent Rich from wrapping
        new_options = options.update(max_width=10000)
        yield from super().__rich_console__(console, new_options)


class NoWrapTable(Table):
    """
    A Table that doesn't constrain column widths to terminal width.

    When printed with soft_wrap=True, this table renders with unlimited width,
    allowing columns to display their full content without truncation.

    Usage:
        table = NoWrapTable(title="Dependencies")
        table.add_column("Name", no_wrap=True)
        table.add_column("Version")
        table.add_row("very-long-artifact-name.jar", "1.0.0")
        console.print(table, soft_wrap=True)
    """

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Render table with unlimited width to prevent column truncation."""
        new_options = options.update(max_width=10000)
        yield from super().__rich_console__(console, new_options)


def create_tree(label: str, no_wrap: bool = False) -> Tree:
    """
    Create a Tree or NoWrapTree based on the no_wrap setting.

    Args:
        label: Root label for the tree
        no_wrap: If True, create a NoWrapTree that doesn't wrap lines

    Returns:
        Tree or NoWrapTree instance
    """
    if no_wrap:
        return NoWrapTree(label)
    return Tree(label)


def create_table(no_wrap: bool = False, **kwargs) -> Table:
    """
    Create a Table or NoWrapTable based on the no_wrap setting.

    Args:
        no_wrap: If True, create a NoWrapTable that doesn't truncate columns
        **kwargs: Additional arguments passed to Table constructor

    Returns:
        Table or NoWrapTable instance
    """
    if no_wrap:
        return NoWrapTable(**kwargs)
    return Table(**kwargs)

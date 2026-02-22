"""
Main entry point for jgo CLI.

This module implements the command-line interface for jgo.
"""

# Import ANSI color support FIRST before anything else.
from .cli import _colors  # noqa: F401
from .cli._parser import cli


def main():
    """Main entry point for the jgo CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()

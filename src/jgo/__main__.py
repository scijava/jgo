"""
Main entry point for jgo CLI.

This module implements the command-line interface for jgo.
"""

from .cli.parser import cli


def main():
    """Main entry point for the jgo CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()

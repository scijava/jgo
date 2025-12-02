"""
Main entry point for jgo CLI.

This module implements the command-line interface for jgo 2.0.
"""

import sys

from .cli.commands import JgoCommands
from .cli.parser import JgoArgumentParser
from .config.jgorc import JgoConfig
from .util.logging import setup_logging


def main():
    """
    Main entry point for the jgo CLI.
    """
    # Parse arguments
    parser = JgoArgumentParser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose, quiet=args.quiet)

    # Load configuration (unless --ignore-jgorc is set)
    if args.ignore_jgorc:
        config = JgoConfig()  # Empty config
    else:
        config = JgoConfig.load()

    # Apply shortcuts to endpoint if present
    if args.endpoint and not args.ignore_jgorc:
        args.endpoint = config.expand_shortcuts(args.endpoint)

    # Execute command
    commands = JgoCommands(args, config.to_dict())
    exit_code = commands.execute()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

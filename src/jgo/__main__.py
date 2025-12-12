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

    # Show help if no command and no endpoint and not in spec mode
    if hasattr(args, 'command') and args.command:
        # Subcommand mode - dispatch to subcommand handler
        pass  # Will handle below
    elif not args.endpoint and not args.is_spec_mode():
        # No command, no endpoint, no jgo.toml - show help
        parser.parser.print_help()
        sys.exit(0)

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

    # Execute command or use legacy path
    if hasattr(args, 'command') and args.command:
        # Dispatch to subcommand
        from .cli.subcommands import run, init, info, list as list_cmd, tree, versions
        
        if args.command == 'run':
            exit_code = run.execute(args, config.to_dict())
        elif args.command == 'init':
            exit_code = init.execute(args, config.to_dict())
        elif args.command == 'info':
            exit_code = info.execute(args, config.to_dict())
        elif args.command == 'list':
            exit_code = list_cmd.execute(args, config.to_dict())
        elif args.command == 'tree':
            exit_code = tree.execute(args, config.to_dict())
        elif args.command == 'versions':
            exit_code = versions.execute(args, config.to_dict())
        else:
            print(f"Error: Unknown command: {args.command}", file=sys.stderr)
            exit_code = 1
    else:
        # Legacy path: use JgoCommands directly
        commands = JgoCommands(args, config.to_dict())
        exit_code = commands.execute()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()

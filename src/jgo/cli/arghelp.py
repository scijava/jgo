"""
Reusable help text for common CLI arguments.

These constants provide consistent documentation across commands for arguments
like ENDPOINT, COORDINATE, etc.
"""

# Single Maven coordinate: groupId:artifactId[:version][:classifier]
COORDINATE = (
    "Maven coordinate in format [cyan]groupId:artifactId[:version][:classifier][/]"
)

# Multiple coordinates
COORDINATES = (
    "One or more Maven coordinates in format "
    "[cyan]groupId:artifactId[:version][:classifier][/]"
)

# Endpoint: can be multiple coordinates combined with +, optionally with @MainClass
ENDPOINT = (
    "Maven coordinates (single or combined with [yellow]+[/]) "
    "optionally followed by [yellow]@MainClass[/]. "
    "Example: [dim]org.scijava:parsington+org.scijava:scijava-common@ScriptREPL[/]"
)

# Configuration key
CONFIG_KEY = "Configuration key in dot notation (e.g., [cyan]repositories.scijava[/])"

# Configuration value
CONFIG_VALUE = "Configuration value to set"

# Shortcut name
SHORTCUT_NAME = "Shortcut name (e.g., [cyan]imagej[/])"

# Commands for help
HELP_COMMANDS = (
    "Command name(s) to show help for. Example: [dim]run[/] or [dim]config shortcut[/]"
)

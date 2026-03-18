"""
CLI entry point.

Usage:
    python cli_tool.py --help
    python cli_tool.py list
    python cli_tool.py add --title "Deploy app" --priority high
"""

from cli.commands import main

if __name__ == "__main__":
    main()

"""
GitHub Projects v2 Python Library

A Python library for programmatic management of GitHub Projects v2 boards.
Provides functionality to move tasks between stages and add comments without AI dependencies.
"""

__version__ = "1.6.0"
__author__ = "GitHub MCP Server"
__description__ = "Python library for GitHub Projects v2 task management"

from .manager import GitHubProjectsManager

__all__ = ["GitHubProjectsManager"]
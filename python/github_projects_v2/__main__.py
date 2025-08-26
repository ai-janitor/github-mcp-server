"""
UNDERSTANDING: Module entry point for python -m github_projects_v2
DEPENDENCIES: cli module for command-line interface
EXPORTS: Direct execution support
INTEGRATION: Enables 'python -m github_projects_v2' usage
"""

from .cli import main

if __name__ == '__main__':
    main()
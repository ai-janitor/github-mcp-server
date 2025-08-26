"""
Setup configuration for GitHub Projects v2 Python package.
"""

from setuptools import setup, find_packages
import os

# Read long description from README
current_dir = os.path.dirname(os.path.abspath(__file__))
readme_path = os.path.join(current_dir, 'README.md')

try:
    with open(readme_path, 'r', encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "GitHub Projects v2 Python library for task management"

setup(
    name="github-projects-v2",
    version="1.11.0",
    author="GitHub MCP Server",
    author_email="",
    description="Python library for GitHub Projects v2 task management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/github/github-mcp-server",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    python_requires=">=3.7",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "gh-projects-v2=github_projects_v2.cli:main",
        ],
    },
    keywords="github projects api automation task management",
    project_urls={
        "Bug Reports": "https://github.com/github/github-mcp-server/issues",
        "Source": "https://github.com/github/github-mcp-server",
        "Documentation": "https://github.com/github/github-mcp-server/blob/main/python/docs/",
    },
)
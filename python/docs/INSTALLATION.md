# Installation Guide - GitHub Projects v2 Python Library

## Overview

The `github-projects-v2` package provides Python tools for programmatic management of GitHub Projects v2 boards. This guide covers installation, setup, and initial configuration.

## Installation Methods

### Option 1: Install from PyPI (Recommended)

```bash
pip install github-projects-v2
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/github/github-mcp-server.git
cd github-mcp-server/python

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Option 3: Install with Development Dependencies

```bash
pip install github-projects-v2[dev]
```

This includes additional tools for development:
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `black` - Code formatting
- `flake8` - Code linting

## Requirements

### System Requirements
- **Python**: 3.7 or higher
- **Operating System**: Any (Linux, macOS, Windows)
- **Network**: Internet access for GitHub API

### Python Dependencies
- `requests>=2.25.0` - HTTP library for API calls

Dependencies are automatically installed with the package.

## GitHub Setup

### 1. Create Personal Access Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select required scopes:
   - ✅ `project` - Full access to projects
   - ✅ `repo` - Repository access (for adding comments to issues)
4. Copy the generated token (starts with `ghp_`)

### 2. Find Your Project ID

#### Method A: Using the CLI Tool

After installation, use the tool to list your projects:

```bash
# This will be available after implementing list projects functionality
gh-projects-v2 --token ghp_your_token list-projects
```

#### Method B: Using GraphQL API

```bash
curl -H "Authorization: bearer ghp_your_token" -X POST \
  -d '{"query":"query{viewer{projectsV2(first:10){nodes{id title number}}}}"}' \
  https://api.github.com/graphql
```

#### Method C: From Project URL

If your project URL is: `https://github.com/users/username/projects/123`
You need to convert this to the GraphQL node ID format (PVT_xxx).

## Verification

### Test Installation

```bash
# Check that the command is available
gh-projects-v2 --version

# Test API connectivity
gh-projects-v2 --token ghp_your_token --project-id PVT_your_project statuses
```

### Test Python Import

```python
from github_projects_v2 import GitHubProjectsManager

# Initialize manager
manager = GitHubProjectsManager("ghp_your_token")

# Test API connection
try:
    statuses = manager.get_available_statuses("PVT_your_project_id")
    print(f"✅ Connected! Available statuses: {statuses}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

## Environment Variables

For convenience, set up environment variables:

### Linux/macOS (Bash/Zsh)

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export GITHUB_TOKEN=ghp_your_token_here
export GITHUB_PROJECT_ID=PVT_your_project_id
```

Then reload: `source ~/.bashrc`

### Windows (PowerShell)

```powershell
$env:GITHUB_TOKEN="ghp_your_token_here"
$env:GITHUB_PROJECT_ID="PVT_your_project_id"
```

### Windows (Command Prompt)

```cmd
set GITHUB_TOKEN=ghp_your_token_here
set GITHUB_PROJECT_ID=PVT_your_project_id
```

## Configuration File (Optional)

Create a configuration file for easier management:

### `~/.gh-projects-config.json`

```json
{
  "default_token": "ghp_your_token_here",
  "projects": {
    "main": "PVT_project_id_1",
    "backup": "PVT_project_id_2"
  }
}
```

Note: Configuration file support is not implemented in v1.0.0 but planned for future versions.

## Usage After Installation

### Command Line

```bash
# Using environment variables
gh-projects-v2 --token "$GITHUB_TOKEN" --project-id "$GITHUB_PROJECT_ID" list

# Direct usage
gh-projects-v2 --token ghp_xxx --project-id PVT_xxx move --item-id PVTI_xxx --status "Done"
```

### Python Module

```python
import os
from github_projects_v2 import GitHubProjectsManager

# Using environment variables
manager = GitHubProjectsManager(os.getenv('GITHUB_TOKEN'))
project_id = os.getenv('GITHUB_PROJECT_ID')

# List items
items = manager.list_project_items(project_id)
```

### Python Module Execution

```bash
# Run as module
python -m github_projects_v2 --token ghp_xxx --project-id PVT_xxx list
```

## Troubleshooting

### Common Installation Issues

#### ImportError: No module named 'github_projects_v2'

**Solution**: Ensure installation completed successfully
```bash
pip list | grep github-projects-v2
# Should show: github-projects-v2    1.0.0
```

#### Command not found: gh-projects-v2

**Solutions**:
1. Check PATH includes pip installation directory
2. Try using full path: `python -m github_projects_v2`
3. Reinstall: `pip uninstall github-projects-v2 && pip install github-projects-v2`

### Common API Issues

#### 401 Unauthorized

**Causes & Solutions**:
- Invalid token → Generate new token with correct scopes
- Expired token → Tokens expire after set period, regenerate
- Wrong scopes → Ensure `project` and `repo` scopes are selected

#### 404 Not Found

**Causes & Solutions**:
- Invalid project ID → Verify PVT_xxx format is correct
- No access to project → Ensure token owner has project access
- Project doesn't exist → Check project URL and ID conversion

#### 403 Forbidden

**Causes & Solutions**:
- Insufficient permissions → Need project write access for move operations
- Rate limiting → Wait and retry, consider adding delays between operations
- Repository access needed → Ensure `repo` scope for comment operations

### Debug Mode

Enable verbose output for troubleshooting:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

from github_projects_v2 import GitHubProjectsManager
manager = GitHubProjectsManager("ghp_your_token")
```

## Performance Considerations

### Rate Limits

GitHub API has rate limits:
- **GraphQL API**: 5,000 points per hour
- **REST API**: 5,000 requests per hour

Each operation consumes different amounts:
- List items: ~50-100 points
- Move task: ~10 points  
- Add comment: 1 request

### Batch Operations

For multiple tasks, use batch operations:

```python
# Efficient - single project info fetch
manager.move_multiple_tasks(project_id, item_ids, status, comment)

# Less efficient - multiple API calls
for item_id in item_ids:
    manager.move_task_to_status(project_id, item_id, status)
```

## Next Steps

After installation:

1. **Read the [API Reference](API_REFERENCE.md)** for detailed usage
2. **Try the examples** in the documentation
3. **Set up automation scripts** for your workflow
4. **Consider CI/CD integration** for automated task management

## Support

- **Issues**: Report bugs at the GitHub repository
- **Documentation**: See `/docs/` directory for comprehensive guides
- **Examples**: Check `/examples/` directory for real-world use cases
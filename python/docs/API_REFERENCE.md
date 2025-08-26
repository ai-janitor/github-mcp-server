# GitHub Projects v2 Python Library - API Reference

## Overview

The `github-projects-v2` library provides a Python interface to GitHub Projects v2 API, enabling programmatic task management without AI dependencies.

## Installation

```bash
pip install github-projects-v2
```

## Quick Start

```python
from github_projects_v2 import GitHubProjectsManager

# Initialize with GitHub token
manager = GitHubProjectsManager("ghp_your_token_here")

# List project items
items = manager.list_project_items("PVT_kwHOxxx")

# Move task to In Progress
manager.move_task_to_status("PVT_kwHOxxx", "PVTI_xxx", "In Progress")

# Add comment to issue
manager.add_issue_comment(
    "https://github.com/owner/repo/issues/123", 
    "Task completed"
)
```

## Command Line Usage

**Security**: The CLI uses environment variables to prevent tokens from appearing in command history or process lists.

```bash
# Required environment variables
export GITHUB_TOKEN=ghp_your_token
export GITHUB_PROJECT_ID=PVT_your_project_id

# List all items
gh-projects-v2 list

# Move single task
gh-projects-v2 move --item-id PVTI_xxx --status "Done"

# Move multiple tasks  
gh-projects-v2 batch-move --item-ids PVTI_xxx1 PVTI_xxx2 --status "Done" --comment "Batch completion"

# Override project ID for specific commands
gh-projects-v2 --project-id PVT_different_project list
```

---

## GitHubProjectsManager Class

### Constructor

#### `GitHubProjectsManager(token: str)`

Initialize the manager with a GitHub personal access token.

**Parameters:**
- `token` (str): GitHub personal access token with `project` and `repo` scopes

**Raises:**
- Authentication errors will be raised on first API call

**Example:**
```python
manager = GitHubProjectsManager("ghp_your_token_here")
```

---

### Core Methods

#### `list_project_items(project_id: str) -> List[Dict[str, Any]]`

List all items in a GitHub Projects v2 board with their current status.

**Parameters:**
- `project_id` (str): GitHub Projects v2 project ID in PVT_xxx format

**Returns:**
- List of dictionaries containing item details:
  ```python
  [
      {
          'id': 'PVTI_xxx',           # Project item ID
          'database_id': 123456,      # Database ID
          'issue': {                  # Issue details
              'id': 'I_xxx',
              'number': 42,
              'title': 'Task title',
              'url': 'https://github.com/...'
          },
          'status': 'In Progress'     # Current status
      }
  ]
  ```

**Example:**
```python
items = manager.list_project_items("PVT_kwHODSyt1s4BBe5J")
for item in items:
    print(f"{item['status']}: #{item['issue']['number']} {item['issue']['title']}")
```

---

#### `move_task_to_status(project_id: str, item_id: str, status_name: str) -> Dict[str, Any]`

Move a project item to a different status column.

**Parameters:**
- `project_id` (str): GitHub Projects v2 project ID
- `item_id` (str): Project item ID in PVTI_xxx format  
- `status_name` (str): Target status name (e.g., "Todo", "In Progress", "Done")

**Returns:**
- GraphQL mutation result with updated item details

**Raises:**
- `Exception`: If status field not found or invalid status name

**Example:**
```python
# Move task to In Progress
result = manager.move_task_to_status(
    "PVT_kwHODSyt1s4BBe5J",
    "PVTI_lAHODSyt1s4BBe5JzgeB2aw", 
    "In Progress"
)
```

---

#### `add_issue_comment(issue_url: str, comment: str) -> Dict[str, Any]`

Add a comment to a GitHub issue for audit trail purposes.

**Parameters:**
- `issue_url` (str): Full GitHub issue URL
- `comment` (str): Comment text to add

**Returns:**
- REST API response with created comment details

**Raises:**
- `Exception`: If URL format invalid or comment creation fails

**Example:**
```python
result = manager.add_issue_comment(
    "https://github.com/ai-janitor/project-automation-demo/issues/1",
    "Task moved to In Progress - starting work"
)
```

---

#### `get_available_statuses(project_id: str) -> List[str]`

Get all available status options for a project.

**Parameters:**
- `project_id` (str): GitHub Projects v2 project ID

**Returns:**
- List of available status names

**Example:**
```python
statuses = manager.get_available_statuses("PVT_kwHOxxx")
print(statuses)  # ['Todo', 'In Progress', 'Done']
```

---

### Advanced Methods

#### `move_multiple_tasks(project_id: str, item_ids: List[str], status_name: str, comment: Optional[str] = None) -> List[Dict[str, Any]]`

Move multiple tasks to the same status with optional comments.

**Parameters:**
- `project_id` (str): GitHub Projects v2 project ID
- `item_ids` (List[str]): List of project item IDs to move
- `status_name` (str): Target status for all items
- `comment` (Optional[str]): Optional comment to add to each issue

**Returns:**
- List of results for each item with success/failure status

**Example:**
```python
results = manager.move_multiple_tasks(
    "PVT_kwHODSyt1s4BBe5J",
    ["PVTI_xxx1", "PVTI_xxx2", "PVTI_xxx3"],
    "Done",
    "Batch completion - all tasks finished"
)

# Check results
for result in results:
    if result['move_success']:
        print(f"✅ Moved {result['item_id']}")
    else:
        print(f"❌ Failed {result['item_id']}: {result['move_error']}")
```

---

#### `get_project_info(project_id: str) -> Dict[str, Any]`

Get comprehensive project information including all fields and items.

**Parameters:**
- `project_id` (str): GitHub Projects v2 project ID

**Returns:**
- Complete project data structure with fields, options, and items

**Example:**
```python
info = manager.get_project_info("PVT_kwHOxxx")
project = info['node']
print(f"Project: {project['title']}")
print(f"Items: {len(project['items']['nodes'])}")
```

---

## Command Line Interface

### Available Commands

#### `list` - List Project Items

```bash
gh-projects-v2 list [--status-filter STATUS] [--project-id PROJECT_ID]
```

**Environment Variables Required:**
- `GITHUB_TOKEN`: GitHub personal access token
- `GITHUB_PROJECT_ID`: Default project ID (can be overridden with --project-id)

**Options:**
- `--status-filter`: Filter items by specific status
- `--project-id`: Override default project ID for this command

**Example:**
```bash
# Set environment variables
export GITHUB_TOKEN=ghp_your_token
export GITHUB_PROJECT_ID=PVT_your_project_id

# List all items
gh-projects-v2 list

# List only items in "In Progress"
gh-projects-v2 list --status-filter "In Progress"

# Use different project for this command
gh-projects-v2 --project-id PVT_other_project list
```

---

#### `move` - Move Single Task

```bash
gh-projects-v2 move --item-id ITEM_ID --status STATUS [--comment COMMENT] [--project-id PROJECT_ID]
```

**Options:**
- `--item-id`: Project item ID to move
- `--status`: Target status name
- `--comment`: Optional comment to add to the issue
- `--project-id`: Override default project ID for this command

**Example:**
```bash
gh-projects-v2 move --item-id PVTI_xxx --status "Done" --comment "Task completed successfully"
```

---

#### `batch-move` - Move Multiple Tasks

```bash
gh-projects-v2 batch-move --item-ids ITEM_ID1 ITEM_ID2 --status STATUS [--comment COMMENT] [--project-id PROJECT_ID]
```

**Options:**
- `--item-ids`: Space-separated list of item IDs
- `--status`: Target status for all items
- `--comment`: Optional comment for all issues
- `--project-id`: Override default project ID for this command

**Example:**
```bash
gh-projects-v2 batch-move --item-ids PVTI_xxx1 PVTI_xxx2 PVTI_xxx3 --status "In Progress" --comment "Starting batch work"
```

---

#### `comment` - Add Comment to Issue

```bash
gh-projects-v2 comment --issue-url URL --message MESSAGE [--project-id PROJECT_ID]
```

**Options:**
- `--issue-url`: Full GitHub issue URL
- `--message`: Comment message text
- `--project-id`: Override default project ID (not used for comment, but maintains consistency)

**Example:**
```bash
gh-projects-v2 comment --issue-url "https://github.com/owner/repo/issues/123" --message "Progress update: 75% complete"
```

---

#### `statuses` - List Available Statuses

```bash
gh-projects-v2 statuses [--project-id PROJECT_ID]
```

**Example:**
```bash
gh-projects-v2 statuses
# Output:
# Available statuses in project PVT_xxx:
#   - Todo
#   - In Progress  
#   - Done
```

---

## Error Handling

All methods raise `Exception` with descriptive messages for common error cases:

- **Authentication**: Invalid or missing GitHub token
- **Project Not Found**: Invalid project ID or insufficient permissions
- **Item Not Found**: Invalid item ID
- **Invalid Status**: Status name not found in project
- **API Limits**: Rate limiting or API errors

**Example:**
```python
try:
    manager.move_task_to_status("PVT_xxx", "PVTI_xxx", "Invalid Status")
except Exception as e:
    print(f"Error: {e}")
    # Output: Error: Status 'Invalid Status' not found. Available: ['Todo', 'In Progress', 'Done']
```

---

## Environment Variables

You can use environment variables for common configuration:

```bash
export GITHUB_TOKEN=ghp_your_token_here
export GITHUB_PROJECT_ID=PVT_your_project_id

gh-projects-v2 list
```

---

## Integration Examples

### CI/CD Pipeline

```yaml
# GitHub Actions
- name: Move completed tasks to Done
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    GITHUB_PROJECT_ID: ${{ vars.PROJECT_ID }}
  run: |
    gh-projects-v2 batch-move \
      --item-ids ${{ vars.COMPLETED_ITEMS }} \
      --status "Done" \
      --comment "Automatically completed by CI/CD pipeline"
```

### Python Script Automation

```python
import os
from github_projects_v2 import GitHubProjectsManager

def weekly_project_cleanup():
    """Move all completed items to Done status."""
    manager = GitHubProjectsManager(os.getenv('GITHUB_TOKEN'))
    project_id = os.getenv('GITHUB_PROJECT_ID')
    
    # Get all items
    items = manager.list_project_items(project_id)
    
    # Find items ready to be marked as done
    completed_items = [
        item['id'] for item in items 
        if item['status'] == 'In Progress' and 
           'completed' in item['issue']['title'].lower()
    ]
    
    if completed_items:
        results = manager.move_multiple_tasks(
            project_id,
            completed_items, 
            'Done',
            'Weekly cleanup - marking completed tasks as done'
        )
        print(f"Moved {len(completed_items)} items to Done")

if __name__ == '__main__':
    weekly_project_cleanup()
```

---

## Requirements

- **Python**: 3.7+
- **Dependencies**: `requests>=2.25.0`
- **GitHub Token**: Personal Access Token with `project` and `repo` scopes
- **Permissions**: Access to target GitHub Projects v2 board and associated repositories

---

## Project Structure

```
github_projects_v2/
├── __init__.py          # Package initialization and exports
├── manager.py           # Core GitHubProjectsManager class
├── cli.py              # Command-line interface
└── __main__.py         # Module entry point (python -m support)
```

---

## License

MIT License - See project repository for full license details.
# GitHub Projects v2 Python Tool

Move tasks between columns on GitHub project boards from the command line. No more clicking through hundreds of tasks!

## Install

```bash
pip install github-projects-v2
```

## Setup

Set your GitHub credentials once:

```bash
export GITHUB_TOKEN=ghp_your_token_here
export GITHUB_PROJECT_ID=PVT_your_project_id
export GITHUB_OWNER=your-username
export GITHUB_REPO=your-repo-name
```

## What Your Tool Can Do

### See All Your Tasks
```bash
gh-projects-v2 list
```

### See Tasks in One Column
```bash
# See only "In Progress" tasks
gh-projects-v2 list --status-filter "In Progress"

# See only "Todo" tasks  
gh-projects-v2 list --status-filter "Todo"

# See only "Done" tasks
gh-projects-v2 list --status-filter "Done"
```

### Move One Task
```bash
# Move task to "In Progress"
gh-projects-v2 move --item-id PVTI_xxx --status "In Progress"

# Move task to "Done" with a comment
gh-projects-v2 move --item-id PVTI_xxx --status "Done" --comment "Task completed"
```

### Move Multiple Tasks at Once
```bash
# Move several tasks to "In Progress"
gh-projects-v2 batch-move --item-ids PVTI_xxx1 PVTI_xxx2 PVTI_xxx3 --status "In Progress"

# Move several tasks to "Done" with comment
gh-projects-v2 batch-move --item-ids PVTI_xxx1 PVTI_xxx2 --status "Done" --comment "All finished"
```

### Add Comments to Issues
```bash
gh-projects-v2 comment --issue-url "https://github.com/owner/repo/issues/123" --message "Progress update"
```

### See What Columns Are Available
```bash
gh-projects-v2 statuses
```

### Trigger GitHub Workflows
```bash
# See what workflows are available
gh-projects-v2 list-workflows

# Trigger a workflow
gh-projects-v2 trigger-workflow --workflow build.yml
gh-projects-v2 trigger-workflow --workflow deploy.yml --ref main

# Or override the repo for one command
gh-projects-v2 trigger-workflow --owner different-user --repo different-repo --workflow build.yml
```

## How to Get Item IDs and Move Tasks

### Step 1: See What Status Options You Have
```bash
gh-projects-v2 statuses
```
Output shows all available columns:
```
Available statuses in project:
  - Backlog
  - Todo
  - In Progress  
  - In Review
  - Done
  - Closed
```

### Step 2: List Tasks to See Their IDs
```bash
gh-projects-v2 list
```
You'll see output like this:
```
Todo (3 items):
----------------------------------------
  #42 Fix login bug
    Item ID: PVTI_lAHODSyt1s4BBe5JzgeB2aw
    URL: https://github.com/owner/repo/issues/42

  #55 Add user dashboard  
    Item ID: PVTI_lAHODSyt1s4BBe5JzgeB3cx
    URL: https://github.com/owner/repo/issues/55
```

### Step 3: Move Any Task to Any Status
Copy the **Item ID** and move to any status from Step 1:
```bash
# Move to any available status
gh-projects-v2 move --item-id PVTI_lAHODSyt1s4BBe5JzgeB2aw --status "Backlog"
gh-projects-v2 move --item-id PVTI_lAHODSyt1s4BBe5JzgeB2aw --status "In Review"  
gh-projects-v2 move --item-id PVTI_lAHODSyt1s4BBe5JzgeB2aw --status "Closed"
```

**Pro Tip:** Filter first to find specific tasks:
```bash
gh-projects-v2 list --status-filter "Todo"  # Find tasks in Todo
# Copy Item ID from output, then move it
gh-projects-v2 move --item-id PVTI_xxx --status "In Progress"
```

## Common Tasks

### Move All "Todo" Tasks to "In Progress"
```bash
# 1. List todo tasks to see their IDs
gh-projects-v2 list --status-filter "Todo"

# 2. Copy all the Item IDs and move them
gh-projects-v2 batch-move --item-ids PVTI_xxx1 PVTI_xxx2 PVTI_xxx3 --status "In Progress" --comment "Starting sprint work"
```

### Mark Tasks as Done When Pull Requests Merge
```bash
gh-projects-v2 move --item-id PVTI_xxx --status "Done" --comment "Completed via PR #123"
```

### Weekly Cleanup - Move Completed Items
```bash
# 1. See what's currently in progress
gh-projects-v2 list --status-filter "In Progress"

# 2. Move finished items to done
gh-projects-v2 batch-move --item-ids PVTI_finished1 PVTI_finished2 --status "Done" --comment "Weekly cleanup"
```

## Getting Your GitHub Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Give it `project` and `repo` permissions
4. Copy the token (starts with `ghp_`)

## Getting Your Project ID

Run this command to find your project IDs:
```bash
curl -H "Authorization: bearer $GITHUB_TOKEN" -X POST \
  -d '{"query":"query{viewer{projectsV2(first:10){nodes{id title number}}}}"}' \
  https://api.github.com/graphql
```

Look for the `"id"` field - it will start with `PVT_`.

## Troubleshooting

**"GITHUB_TOKEN environment variable is required"**
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

**"Project ID required"**  
```bash
export GITHUB_PROJECT_ID=PVT_your_project_id
```

**"Status 'XYZ' not found"**
```bash
# See what statuses are available
gh-projects-v2 statuses
```

## Python Scripts

If you want to write Python scripts instead of using command line:

```python
import os
from github_projects_v2 import GitHubProjectsManager

# Setup
manager = GitHubProjectsManager(os.getenv('GITHUB_TOKEN'))
project_id = os.getenv('GITHUB_PROJECT_ID')

# List all tasks
items = manager.list_project_items(project_id)
for item in items:
    print(f"{item['status']}: {item['issue']['title']}")

# Move a task
manager.move_task_to_status(project_id, "PVTI_xxx", "Done")

# Move multiple tasks
manager.move_multiple_tasks(project_id, ["PVTI_xxx1", "PVTI_xxx2"], "In Progress", "Starting work")
```

That's it! Install, set your tokens, and start moving tasks around without clicking through the web interface.
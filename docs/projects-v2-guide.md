# GitHub Projects v2 Integration Guide

This document explains the GitHub Projects v2 API integration in the GitHub MCP Server and clarifies the differences between Projects v2 and the deprecated Projects Classic.

## 📋 Overview

The GitHub MCP Server provides complete integration with **GitHub Projects v2** through GraphQL API. This enables automated project board management, issue tracking, project-repository linking, issue hierarchy management (Epic → Story → Task), bulk status operations, and complete workflow automation.

**Eliminates Manual Work**: No more "point and click 1000 tickets" - fully automated project board management with audit trails and bulk operations.

## 🆚 Projects v2 vs Projects Classic

### Projects Classic (Deprecated ❌)
- **Status**: Deprecated as of 2025-04-01 UTC
- **API**: REST API endpoints return 410 errors
- **Scope**: Repository-scoped projects appeared in repository's Projects tab
- **Location**: `github.com/owner/repo/projects`
- **Features**: Basic kanban boards with limited automation

### Projects v2 (Current ✅)
- **Status**: Active and fully supported
- **API**: GraphQL API with rich automation capabilities
- **Scope**: User-level and organization-level projects
- **Location**: `github.com/users/username/projects` or `github.com/orgs/orgname/projects`
- **Features**: Advanced project management with custom fields, views, and workflows

## 🔗 Repository Linking

**Important**: Projects v2 can be linked to repositories and will appear in the repository's Projects tab when they contain issues from that repository.

### Automatic Linking
When you add issues from a repository to a Projects v2 board:
- The project automatically appears in the repository's Projects tab
- Shows as "1 Open" (or number of active projects linked)
- Provides seamless navigation between repo and project

### Manual Linking 

**Via MCP Tools (Recommended)**:
- Use `link_project_to_repository` tool for programmatic linking
- Use `unlink_project_from_repository` tool to disconnect projects
- Ideal for automation and "put it back" scenarios

**Via GitHub Web Interface**:
You can also link projects to repositories through the GitHub web interface:
1. Go to your project board
2. Click "Settings" → "Manage access"  
3. Add repositories to link them explicitly

## 🛠️ Available MCP Tools

The GitHub MCP Server provides these Projects v2 tools:

### Read Tools
- **`list_user_projects`** - List all Projects v2 boards for a user or organization
  - Parameters: `login` (username/org), `first` (pagination)
  - Returns: Project list with IDs, titles, URLs, and metadata

### Write Tools
- **`create_project`** - Create new Projects v2 board
  - Parameters: `owner_id` (GitHub node ID), `title`, `description` (optional)
  - Returns: Complete project details including project_id for immediate use
  
- **`add_item_to_project`** - Add issues/PRs to project board
  - Parameters: `project_id`, `issue_url` 
  - Returns: Item details with item_id and database_id
  
- **`update_project_item_status`** - Move items between columns/update fields
  - Parameters: `project_id`, `item_id`, `field_id`, `value`
  - Returns: Success confirmation with updated item details

- **`link_project_to_repository`** - Link existing project to repository
  - Parameters: `project_id` (PVT_xxxx format), `repository_id` (R_xxxx format)
  - Returns: Success confirmation with project and repository details
  - **Use Case**: Reconnect projects that were previously unlinked ("put it back" functionality)

- **`unlink_project_from_repository`** - Unlink project from repository
  - Parameters: `project_id` (PVT_xxxx format), `repository_id` (R_xxxx format)
  - Returns: Success confirmation with project and repository details
  - **Note**: Project data remains intact, only removes from repository's Projects tab

### Issue Hierarchy Tools
- **`add_sub_issue`** - Create parent-child relationships between issues  
  - Parameters: `owner`, `repo`, `issue_number` (parent), `sub_issue_id` (child issue ID)
  - Returns: Success confirmation with hierarchy details
  - **Use Case**: Retrofit hierarchy onto existing issues (Epic → Story → Task)

- **`list_sub_issues`** - List all sub-issues under a parent issue
  - Parameters: `owner`, `repo`, `issue_number` (parent)  
  - Returns: Array of child issues with full details

- **`remove_sub_issue`** - Remove parent-child relationship
  - Parameters: `owner`, `repo`, `issue_number` (parent), `sub_issue_id` (child)
  - Returns: Success confirmation

- **`reprioritize_sub_issue`** - Reorder sub-issues within parent
  - Parameters: `owner`, `repo`, `issue_number` (parent), `sub_issue_id`, `after_id`
  - Returns: Updated priority order

## 🚀 Complete Automation Workflow

### 1. Project Creation
```bash
# Create new project board
create_project --owner-id "U_kgDODSyt1g" --title "My Automated Project"
# Returns: project_id for immediate use
```

### 2. Issue Management  
```bash
# Add existing issues to project
add_item_to_project --project-id "PVT_kwHO..." --issue-url "https://github.com/owner/repo/issues/1"

# Update single item status (move between columns)
update_project_item_status --project-id "PVT_kwHO..." --item-id "PVTI_..." --field-id "PVTSSF_..." --value "In Progress"

# Bulk status updates (move all items from "No Status" to "Todo")
# 1. Query project to get field IDs and item IDs
# 2. Loop through all items and update status field
# 3. Use singleSelectOptionId for status field values
```

**Status Field Values**:
- **Todo**: Use `singleSelectOptionId` for the Todo option
- **In Progress**: Use `singleSelectOptionId` for the In Progress option  
- **Done**: Use `singleSelectOptionId` for the Done option

### 3. Repository Integration
```bash
# Link existing project to repository
link_project_to_repository --project-id "PVT_kwHO..." --repository-id "R_kgDO..."

# Unlink project from repository (maintains project data)
unlink_project_from_repository --project-id "PVT_kwHO..." --repository-id "R_kgDO..."
```

**Automatic vs Manual Linking**:
- **Automatic**: Issues added from repository automatically link project to repo
- **Manual**: Use `link_project_to_repository` to explicitly connect projects
- Project appears in repository's Projects tab when linked
- Seamless navigation between GitHub repo and project board

### 4. Issue Hierarchy Management
```bash
# Create Epic → Story → Task hierarchy for existing issues
# Link stories to epic (retrofit hierarchy)
add_sub_issue --owner "ai-janitor" --repo "project-automation-demo" --issue-number 1 --sub-issue-id 3354753592  # Story #2
add_sub_issue --owner "ai-janitor" --repo "project-automation-demo" --issue-number 1 --sub-issue-id 3354754148  # Story #3

# Create tasks and link to stories  
create_issue --title "Task: Document API differences" --body "Implementation task" --labels '["task"]'
# Then link the created task (use returned issue ID)
add_sub_issue --owner "ai-janitor" --repo "project-automation-demo" --issue-number 2 --sub-issue-id <TASK_ID>

# Verify hierarchy structure
list_sub_issues --owner "ai-janitor" --repo "project-automation-demo" --issue-number 1  # List Epic's stories
list_sub_issues --owner "ai-janitor" --repo "project-automation-demo" --issue-number 2  # List Story's tasks
```

**Real-World Hierarchy Use Cases**:
- **Retrofit Hierarchy**: Link existing issues after they've been created
- **Mistake Recovery**: Use `remove_sub_issue` to fix wrong parent-child relationships  
- **Priority Changes**: Use `reprioritize_sub_issue` to reorder tasks within stories
- **Audit Structure**: Use `list_sub_issues` to verify current hierarchy

**Example Hierarchy Result**:
```
📊 EPIC #1: Automated GitHub Project Board Management
   ├─ Story #2: Research GitHub Projects v2 API Integration
   │  ├─ Task #6: Document Projects v2 vs Classic differences  
   │  └─ Task #7: Test GitHub GraphQL API mutations
   ├─ Story #3: Implement Bulk Ticket Status Updates
   │  ├─ Task #8: Design batch processing API
   │  └─ Task #9: Implement parallel status updates
   └─ [Additional stories and tasks...]
```

### 5. Bulk Status Management & Workflow Automation
```bash
# Real-world scenario: Move all 13 issues from "No Status" to "Todo"
# Step 1: Query project to get field IDs and current status
# Step 2: Identify items that need status updates  
# Step 3: Batch update all items to new status

# Example GraphQL for bulk status updates:
# - Project ID: PVT_kwHODSyt1s4BBe5J
# - Status Field ID: PVTSSF_lAHODSyt1s4BBe5Jzgz-a7o
# - Todo Option ID: f75ad846
# - In Progress Option ID: 47fc9ee4
# - Done Option ID: 98236657

# Complete workflow automation example:
# 1. Move 5 items: Todo → In Progress (add "demo demo demo" comment)
# 2. Move same 5 items: In Progress → Done (add "done done done demo" comment)

# Each update uses updateProjectV2ItemFieldValue mutation
# with singleSelectOptionId for status field changes
# Plus add_issue_comment for audit trail
```

**Complete Workflow Example**:
```bash
# Demonstrated workflow: Epic + 4 Stories through complete lifecycle
# Selected items:
#   - Issue #1: EPIC: Automated GitHub Project Board Management via AI
#   - Issue #2: Story: Research GitHub Projects v2 API Integration  
#   - Issue #3: Story: Implement Bulk Ticket Status Updates
#   - Issue #4: Story: AI-Driven Workflow Automation
#   - Issue #5: Story: Extend GitHub MCP Server with Projects API

# Result: Todo: 8, In Progress: 0, Done: 5 (with audit comments)
```

**Bulk Operations Benefits**:
- **Mass Triage**: Move all new issues to appropriate columns
- **Sprint Planning**: Batch move selected issues to "In Progress"
- **Release Management**: Move completed features to "Done"  
- **Workflow Automation**: Automatically organize issues by labels/milestones
- **Audit Trail**: Add consistent comments during status transitions
- **No Manual Work**: Eliminate "point and click 1000 tickets" scenarios

## 🎯 Complete Real-World Example

### Automated Project Board Management Demo

**Starting State**: 13 issues created with Epic → Story → Task hierarchy
```
📊 Project Board Initial State:
   • No Status: 13 issues (Epic + Stories + Tasks)
   • Todo: 0
   • In Progress: 0  
   • Done: 0
```

**Step 1: Mass Triage (All issues: No Status → Todo)**
- Used `update_project_item_status` tool for bulk operations
- All 13 issues moved to Todo column in batch
- Result: Todo: 13, In Progress: 0, Done: 0

**Step 2: Sprint Planning (5 items: Todo → In Progress)**  
- Selected Epic #1 + 4 Stories for workflow demo
- Added "demo demo demo" comments for audit trail
- Used GraphQL mutations with single-select field handling
- Result: Todo: 8, In Progress: 5, Done: 0

**Step 3: Release Management (5 items: In Progress → Done)**
- Moved same 5 items to completion 
- Added "done done done demo" comments for final audit
- Demonstrated complete automation workflow
- **Final Result: Todo: 8, In Progress: 0, Done: 5**

**Key Achievement**: Eliminated manual "point and click" for all 13 issues across multiple status transitions, with full audit trail and hierarchy management.

## 📚 GraphQL API Reference

### Core Mutations Used

#### Create Project
```graphql
mutation {
  createProjectV2(input: {
    ownerId: "USER_OR_ORG_NODE_ID"
    title: "PROJECT_TITLE"
  }) {
    projectV2 {
      id
      number  
      title
      url
      createdAt
    }
  }
}
```

#### Add Item to Project
```graphql
mutation {
  addProjectV2ItemById(input: {
    projectId: "PROJECT_NODE_ID"
    contentId: "ISSUE_OR_PR_NODE_ID"
  }) {
    item {
      id
      databaseId
    }
  }
}
```

#### Update Item Status (Text Field)
```graphql
mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: "PROJECT_NODE_ID"
    itemId: "ITEM_NODE_ID" 
    fieldId: "FIELD_NODE_ID"
    value: {
      text: "NEW_VALUE"
    }
  }) {
    projectV2Item {
      id
    }
  }
}
```

#### Update Item Status (Single Select Field)
```graphql
mutation {
  updateProjectV2ItemFieldValue(input: {
    projectId: "PVT_kwHODSyt1s4BBe5J"
    itemId: "PVTI_lAHODSyt1s4BBe5JzgeB2aw"
    fieldId: "PVTSSF_lAHODSyt1s4BBe5Jzgz-a7o"
    value: {
      singleSelectOptionId: "f75ad846"
    }
  }) {
    projectV2Item {
      id
    }
  }
}
```

#### Link Project to Repository
```graphql
mutation {
  linkProjectV2ToRepository(input: {
    projectId: "PROJECT_NODE_ID"
    repositoryId: "REPOSITORY_NODE_ID"
  }) {
    repository {
      id
      name
    }
  }
}
```

#### Unlink Project from Repository
```graphql
mutation {
  unlinkProjectV2FromRepository(input: {
    projectId: "PROJECT_NODE_ID"
    repositoryId: "REPOSITORY_NODE_ID"
  }) {
    repository {
      id
      name
    }
  }
}
```

## 🔑 Authentication & Permissions

### Required Scopes
- **Read operations**: `read:project` scope
- **Write operations**: `project` scope  
- **Repository linking**: `repo` or `Contents` permission for target repositories

### Token Types
- **Personal Access Token**: Works for user projects
- **GitHub App Installation Token**: Works for organization projects
- **Fine-grained PAT**: Limited to specific repositories

## 💡 Best Practices

### 1. Project Organization
- Use descriptive project titles for easier identification
- Leverage custom fields for categorization and tracking
- Set up saved views for different team perspectives

### 2. Automation Strategies
- **Bulk Operations**: Process multiple issues efficiently
- **Status Synchronization**: Keep external systems in sync
- **Workflow Triggers**: Automate based on issue/PR events

### 3. Repository Integration
- Link projects to relevant repositories early
- Use consistent naming conventions across repos and projects
- Document project board structure for team members

## 🚨 Common Issues & Solutions

### "Project not showing in repository"
- **Cause**: No issues from that repository added to project yet
- **Solution**: Add at least one issue from the repository to auto-link

### "Empty Projects tab shows 0/0"
- **Cause**: Looking at deprecated Projects Classic interface  
- **Solution**: Projects v2 appear here only when linked via issues

### "Permission denied" errors
- **Cause**: Insufficient token permissions
- **Solution**: Ensure token has `project` scope and repository access

## 📖 Additional Resources

- [GitHub Projects v2 Documentation](https://docs.github.com/en/issues/planning-and-tracking-with-projects)
- [GraphQL API Reference](https://docs.github.com/en/graphql/reference/mutations)
- [MCP Server GitHub Repository](https://github.com/github/github-mcp-server)

---

*This integration enables complete automation of GitHub project management, eliminating manual "point and click" workflows for enterprise-scale issue management.*
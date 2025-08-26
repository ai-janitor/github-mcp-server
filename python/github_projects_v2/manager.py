"""
UNDERSTANDING: Core GitHub Projects v2 API manager class
DEPENDENCIES: requests library for HTTP/GraphQL API calls
EXPORTS: GitHubProjectsManager class for all project operations
INTEGRATION: Replicates MCP Server functionality for environments without AI
"""

import requests
import re
from typing import Dict, Any, List, Optional, Tuple


class GitHubProjectsManager:
    """
    GitHub Projects v2 API Manager
    
    Main class for GitHub Projects v2 API operations including moving tasks
    between stages, adding comments, and listing project items.
    
    Args:
        token (str): GitHub personal access token with 'project' and 'repo' scopes
    
    Example:
        >>> manager = GitHubProjectsManager("ghp_your_token")
        >>> items = manager.list_project_items("PVT_kwHOxxx")
        >>> manager.move_task_to_status("PVT_kwHOxxx", "PVTI_xxx", "In Progress")
    """
    
    def __init__(self, token: str):
        """
        Initialize GitHub Projects v2 manager with authentication token.
        
        Args:
            token: GitHub personal access token with required scopes
        """
        self.token = token
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/vnd.github+json'
        }
        self.graphql_url = 'https://api.github.com/graphql'
        self.rest_url = 'https://api.github.com'
    
    def execute_graphql(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute GraphQL query against GitHub API.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
            
        Returns:
            API response data
            
        Raises:
            Exception: If GraphQL request fails or returns errors
        """
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
            
        response = requests.post(self.graphql_url, headers=self.headers, json=payload)
        
        if response.status_code != 200:
            raise Exception(f"GraphQL request failed: {response.status_code} - {response.text}")
        
        result = response.json()
        if 'errors' in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
            
        return result['data']
    
    def get_project_info(self, project_id: str) -> Dict[str, Any]:
        """
        Get comprehensive project information including fields and items.
        
        Args:
            project_id: GitHub Projects v2 project ID (PVT_xxx format)
            
        Returns:
            Complete project data with fields, options, and items
            
        Example:
            >>> info = manager.get_project_info("PVT_kwHOxxx")
            >>> print(info['node']['title'])
        """
        query = """
        query($projectId: ID!) {
            node(id: $projectId) {
                ... on ProjectV2 {
                    id
                    title
                    number
                    fields(first: 20) {
                        nodes {
                            ... on ProjectV2Field {
                                id
                                name
                                dataType
                            }
                            ... on ProjectV2SingleSelectField {
                                id
                                name
                                dataType
                                options {
                                    id
                                    name
                                }
                            }
                        }
                    }
                    items(first: 100) {
                        nodes {
                            id
                            databaseId
                            content {
                                ... on Issue {
                                    id
                                    number
                                    title
                                    body
                                    url
                                }
                            }
                            fieldValues(first: 20) {
                                nodes {
                                    ... on ProjectV2ItemFieldTextValue {
                                        text
                                        field {
                                            ... on ProjectV2Field {
                                                id
                                                name
                                            }
                                        }
                                    }
                                    ... on ProjectV2ItemFieldSingleSelectValue {
                                        name
                                        field {
                                            ... on ProjectV2SingleSelectField {
                                                id
                                                name
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        return self.execute_graphql(query, {'projectId': project_id})
    
    def get_all_project_items(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get ALL project items using proper GraphQL pagination (handles 1000+ items).
        
        Args:
            project_id: GitHub Projects v2 project ID (PVT_xxx format)
            
        Returns:
            List of all project items with their details
        """
        all_items = []
        has_next_page = True
        cursor = None
        
        while has_next_page:
            # Build the query with cursor pagination
            after_clause = f', after: "{cursor}"' if cursor else ""
            
            query = f"""
            query($projectId: ID!) {{
                node(id: $projectId) {{
                    ... on ProjectV2 {{
                        id
                        title
                        number
                        fields(first: 20) {{
                            nodes {{
                                ... on ProjectV2Field {{
                                    id
                                    name
                                    dataType
                                }}
                                ... on ProjectV2SingleSelectField {{
                                    id
                                    name
                                    dataType
                                    options {{
                                        id
                                        name
                                    }}
                                }}
                            }}
                        }}
                        items(first: 100{after_clause}) {{
                            pageInfo {{
                                hasNextPage
                                endCursor
                            }}
                            nodes {{
                                id
                                databaseId
                                content {{
                                    ... on Issue {{
                                        id
                                        number
                                        title
                                        body
                                        url
                                    }}
                                }}
                                fieldValues(first: 20) {{
                                    nodes {{
                                        ... on ProjectV2ItemFieldTextValue {{
                                            text
                                            field {{
                                                ... on ProjectV2Field {{
                                                    id
                                                    name
                                                }}
                                            }}
                                        }}
                                        ... on ProjectV2ItemFieldSingleSelectValue {{
                                            name
                                            field {{
                                                ... on ProjectV2SingleSelectField {{
                                                    id
                                                    name
                                                }}
                                            }}
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
            """
            
            result = self.execute_graphql(query, {'projectId': project_id})
            project = result['node']
            
            # Add items from this page
            page_items = []
            for item in project['items']['nodes']:
                item_data = {
                    'id': item['id'],
                    'database_id': item['databaseId'],
                    'issue': item['content'],
                    'status': 'No Status'  # default
                }
                
                # Find status field value
                for field_value in item['fieldValues']['nodes']:
                    if 'field' in field_value and field_value['field']['name'] == 'Status':
                        if 'name' in field_value:
                            item_data['status'] = field_value['name']
                        break
                
                page_items.append(item_data)
            
            all_items.extend(page_items)
            
            # Check if there are more pages
            page_info = project['items']['pageInfo']
            has_next_page = page_info['hasNextPage']
            cursor = page_info['endCursor']
            
            print(f"Fetched {len(page_items)} items (total: {len(all_items)})...")
        
        print(f"✅ Fetched all {len(all_items)} project items")
        return all_items
    
    def get_task_detail(self, project_id: str, item_id: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific task including comments and metadata.
        
        Args:
            project_id: GitHub Projects v2 project ID (PVT_xxx format)
            item_id: Project item ID (PVTI_xxx format)
            
        Returns:
            Detailed task information with comments, status, fields, and metadata
            
        Example:
            >>> detail = manager.get_task_detail("PVT_kwHOxxx", "PVTI_xxx")
            >>> print(detail['issue']['title'])
        """
        # Get the project item details
        query = """
        query($projectId: ID!, $itemId: ID!) {
            node(id: $projectId) {
                ... on ProjectV2 {
                    item(id: $itemId) {
                        id
                        databaseId
                        createdAt
                        updatedAt
                        content {
                            ... on Issue {
                                id
                                number
                                title
                                body
                                url
                                state
                                author {
                                    login
                                }
                                createdAt
                                updatedAt
                                assignees(first: 10) {
                                    nodes {
                                        login
                                        name
                                    }
                                }
                                labels(first: 20) {
                                    nodes {
                                        name
                                        color
                                    }
                                }
                                comments(first: 100) {
                                    nodes {
                                        id
                                        body
                                        createdAt
                                        author {
                                            login
                                        }
                                    }
                                }
                            }
                        }
                        fieldValues(first: 20) {
                            nodes {
                                ... on ProjectV2ItemFieldTextValue {
                                    text
                                    field {
                                        ... on ProjectV2Field {
                                            id
                                            name
                                        }
                                    }
                                }
                                ... on ProjectV2ItemFieldSingleSelectValue {
                                    name
                                    field {
                                        ... on ProjectV2SingleSelectField {
                                            id
                                            name
                                        }
                                    }
                                }
                                ... on ProjectV2ItemFieldNumberValue {
                                    number
                                    field {
                                        ... on ProjectV2Field {
                                            id
                                            name
                                        }
                                    }
                                }
                                ... on ProjectV2ItemFieldDateValue {
                                    date
                                    field {
                                        ... on ProjectV2Field {
                                            id
                                            name
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        result = self.execute_graphql(query, {
            'projectId': project_id,
            'itemId': item_id
        })
        
        if not result.get('node') or not result['node'].get('item'):
            raise Exception(f"Project item {item_id} not found in project {project_id}")
        
        # Process the result to make it easier to work with
        item = result['node']['item']
        issue = item.get('content', {})
        
        # Extract field values into a readable format
        fields = {}
        if 'fieldValues' in item:
            for field_value in item['fieldValues']['nodes']:
                if 'field' in field_value and field_value['field']:
                    field_name = field_value['field']['name']
                    if 'text' in field_value:
                        fields[field_name] = field_value['text']
                    elif 'name' in field_value:
                        fields[field_name] = field_value['name']
                    elif 'number' in field_value:
                        fields[field_name] = field_value['number']
                    elif 'date' in field_value:
                        fields[field_name] = field_value['date']
        
        return {
            'item_id': item['id'],
            'database_id': item.get('databaseId'),
            'created_at': item.get('createdAt'),
            'updated_at': item.get('updatedAt'),
            'issue': issue,
            'fields': fields,
            'status': fields.get('Status', 'Unknown')
        }
    
    def move_task_to_status(self, project_id: str, item_id: str, status_name: str) -> Dict[str, Any]:
        """
        Move a project item to a specific status column.
        
        Args:
            project_id: GitHub Projects v2 project ID (PVT_xxx format)
            item_id: Project item ID (PVTI_xxx format)
            status_name: Target status ("Todo", "In Progress", "Done")
            
        Returns:
            Updated item details from GraphQL mutation
            
        Raises:
            Exception: If status field or option not found, or mutation fails
            
        Example:
            >>> result = manager.move_task_to_status(
            ...     "PVT_kwHOxxx", 
            ...     "PVTI_xxx", 
            ...     "In Progress"
            ... )
        """
        # First get project info to find status field and option IDs
        project_info = self.get_project_info(project_id)
        project = project_info['node']
        
        # Find the Status field
        status_field_id = None
        status_option_id = None
        
        for field in project['fields']['nodes']:
            if field['name'] == 'Status' and 'options' in field:
                status_field_id = field['id']
                # Find the option ID for the requested status
                for option in field['options']:
                    if option['name'] == status_name:
                        status_option_id = option['id']
                        break
                break
        
        if not status_field_id:
            raise Exception("Status field not found in project")
        if not status_option_id:
            available_statuses = []
            for field in project['fields']['nodes']:
                if field['name'] == 'Status' and 'options' in field:
                    available_statuses = [opt['name'] for opt in field['options']]
                    break
            raise Exception(f"Status '{status_name}' not found. Available: {available_statuses}")
        
        # Update the item status
        mutation = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
            updateProjectV2ItemFieldValue(input: {
                projectId: $projectId
                itemId: $itemId
                fieldId: $fieldId
                value: {
                    singleSelectOptionId: $optionId
                }
            }) {
                projectV2Item {
                    id
                    databaseId
                }
            }
        }
        """
        
        variables = {
            'projectId': project_id,
            'itemId': item_id,
            'fieldId': status_field_id,
            'optionId': status_option_id
        }
        
        return self.execute_graphql(mutation, variables)
    
    def add_issue_comment(self, issue_url: str, comment: str) -> Dict[str, Any]:
        """
        Add a comment to a GitHub issue.
        
        Args:
            issue_url: Full GitHub issue URL
            comment: Comment text to add
            
        Returns:
            Created comment details from REST API
            
        Raises:
            Exception: If URL format is invalid or comment creation fails
            
        Example:
            >>> result = manager.add_issue_comment(
            ...     "https://github.com/owner/repo/issues/123",
            ...     "Task completed successfully"
            ... )
        """
        # Extract owner, repo, and issue number from URL
        # URL format: https://github.com/owner/repo/issues/123
        url_parts = issue_url.replace('https://github.com/', '').split('/')
        if len(url_parts) < 4 or url_parts[2] != 'issues':
            raise Exception(f"Invalid issue URL format: {issue_url}")
        
        owner = url_parts[0]
        repo = url_parts[1]
        issue_number = int(url_parts[3])
        
        # Use REST API to add comment
        comment_url = f"{self.rest_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        payload = {'body': comment}
        
        response = requests.post(comment_url, headers=self.headers, json=payload)
        
        if response.status_code != 201:
            raise Exception(f"Failed to add comment: {response.status_code} - {response.text}")
        
        return response.json()
    
    def list_project_items(self, project_id: str) -> List[Dict[str, Any]]:
        """
        List all items in a project with their current status.
        
        Args:
            project_id: GitHub Projects v2 project ID (PVT_xxx format)
            
        Returns:
            List of project items with status and issue details
            
        Example:
            >>> items = manager.list_project_items("PVT_kwHOxxx")
            >>> for item in items:
            ...     print(f"{item['status']}: {item['issue']['title']}")
        """
        # Use the new paginated method to get ALL items
        return self.get_all_project_items(project_id)
    
    def search_project_items(self, project_id: str, search_terms: str, status_filter: str = None, exact_match: bool = False) -> List[Dict[str, Any]]:
        """
        Search project items by content (title, body) and optionally filter by status.
        
        Args:
            project_id: GitHub Projects v2 project ID (PVT_xxx format)
            search_terms: Search terms - keywords (default) or exact phrase (with exact_match=True)
            status_filter: Optional status filter to apply after search
            exact_match: If True, search for exact phrase; if False, search for all keywords
            
        Returns:
            List of matching project items
            
        Example:
            >>> items = manager.search_project_items("PVT_kwHOxxx", "login bug")  # Finds items with both "login" AND "bug"
            >>> items = manager.search_project_items("PVT_kwHOxxx", "login bug", exact_match=True)  # Finds "login bug" phrase
            >>> items = manager.search_project_items("PVT_kwHOxxx", "API", "In Progress")
        """
        # Get all items
        all_items = self.list_project_items(project_id)
        
        # Convert search terms to lowercase for case-insensitive search
        search_terms_lower = search_terms.lower()
        
        matching_items = []
        for item in all_items:
            issue = item['issue']
            
            # Search in title and body (description)
            title = issue.get('title', '').lower()
            body = issue.get('body', '') or ''  # Handle None body
            body = body.lower()
            
            # Check if search terms match title or body
            if exact_match:
                # Exact phrase match
                matches = search_terms_lower in title or search_terms_lower in body
            else:
                # Keyword match - all keywords must be present
                keywords = search_terms_lower.split()
                title_matches = all(keyword in title for keyword in keywords)
                body_matches = all(keyword in body for keyword in keywords)
                matches = title_matches or body_matches
            
            if matches:
                # Apply status filter if specified (case-insensitive, space-tolerant)
                if status_filter is None or self._status_matches(item['status'], status_filter):
                    matching_items.append(item)
        
        return matching_items
    
    def _status_matches(self, actual_status: str, filter_status: str) -> bool:
        """
        Compare two status strings with case-insensitive, space-tolerant matching.
        
        Args:
            actual_status: The actual status from the project item
            filter_status: The status filter provided by user
            
        Returns:
            True if statuses match (after normalization)
            
        Example:
            >>> self._status_matches("In Progress", "in progress")  # True
            >>> self._status_matches("In Progress", "inprogress")   # True  
            >>> self._status_matches("Todo", "to do")               # False
        """
        if not actual_status or not filter_status:
            return False
            
        # Normalize both strings: lowercase and remove spaces
        actual_normalized = actual_status.lower().replace(' ', '')
        filter_normalized = filter_status.lower().replace(' ', '')
        
        return actual_normalized == filter_normalized
    
    def get_available_statuses(self, project_id: str) -> List[str]:
        """
        Get all available status options for a project.
        
        Args:
            project_id: GitHub Projects v2 project ID (PVT_xxx format)
            
        Returns:
            List of available status names
            
        Example:
            >>> statuses = manager.get_available_statuses("PVT_kwHOxxx")
            >>> print(statuses)  # ['Todo', 'In Progress', 'Done']
        """
        project_info = self.get_project_info(project_id)
        project = project_info['node']
        
        for field in project['fields']['nodes']:
            if field['name'] == 'Status' and 'options' in field:
                return [option['name'] for option in field['options']]
        
        return []
    
    def trigger_workflow(self, owner: str, repo: str, workflow_id: str, branch: str = "main", inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Trigger a GitHub Actions workflow manually on a specific branch.
        
        Args:
            owner: Repository owner (username or organization)
            repo: Repository name
            workflow_id: Workflow ID or filename (e.g., "12345678" or "build.yml")
            branch: Git branch to run workflow on (default: "main")
            inputs: Optional inputs for workflow_dispatch (if workflow accepts them)
            
        Returns:
            Success confirmation from GitHub API
            
        Raises:
            Exception: If workflow trigger fails or workflow doesn't support manual dispatch
            
        Example:
            >>> result = manager.trigger_workflow("owner", "repo", "build.yml", "development")
            >>> result = manager.trigger_workflow("owner", "repo", "deploy.yml", "stage", {"environment": "staging"})
        """
        # Use REST API to trigger workflow
        trigger_url = f"{self.rest_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
        
        payload = {"ref": branch}
        if inputs:
            payload["inputs"] = inputs
        
        response = requests.post(trigger_url, headers=self.headers, json=payload)
        
        if response.status_code == 204:
            return {"success": True, "message": "Workflow triggered successfully"}
        elif response.status_code == 404:
            raise Exception(f"Workflow '{workflow_id}' not found or doesn't support manual triggering")
        elif response.status_code == 422:
            raise Exception(f"Workflow '{workflow_id}' doesn't support manual dispatch (missing workflow_dispatch trigger)")
        else:
            raise Exception(f"Failed to trigger workflow: {response.status_code} - {response.text}")
    
    def list_workflows(self, owner: str, repo: str, branch: str = None) -> List[Dict[str, Any]]:
        """
        List all GitHub Actions workflows in a repository, optionally filtered by branch.
        
        Args:
            owner: Repository owner (username or organization)
            repo: Repository name
            branch: Optional branch to filter workflows (shows workflows that exist in that branch)
            
        Returns:
            List of workflows with their details
            
        Example:
            >>> workflows = manager.list_workflows("owner", "repo")
            >>> workflows = manager.list_workflows("owner", "repo", "development")
            >>> for wf in workflows:
            ...     print(f"{wf['name']} ({wf['id']}): {wf['path']}")
        """
        workflows_url = f"{self.rest_url}/repos/{owner}/{repo}/actions/workflows"
        
        # Add branch parameter if specified
        params = {}
        if branch:
            params['ref'] = branch
        
        response = requests.get(workflows_url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            raise Exception(f"Failed to list workflows: {response.status_code} - {response.text}")
        
        return response.json().get('workflows', [])
    
    def move_multiple_tasks(self, project_id: str, item_ids: List[str], 
                           status_name: str, comment: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Move multiple tasks to the same status with optional comments.
        
        Args:
            project_id: GitHub Projects v2 project ID
            item_ids: List of project item IDs to move
            status_name: Target status for all items
            comment: Optional comment to add to each issue
            
        Returns:
            List of results for each item moved
            
        Example:
            >>> results = manager.move_multiple_tasks(
            ...     "PVT_kwHOxxx",
            ...     ["PVTI_xxx1", "PVTI_xxx2"],
            ...     "Done",
            ...     "Batch completion"
            ... )
        """
        results = []
        
        # Get project info once to find issue URLs if commenting
        issue_urls = {}
        if comment:
            project_info = self.get_project_info(project_id)
            for item in project_info['node']['items']['nodes']:
                issue_urls[item['id']] = item['content']['url']
        
        for item_id in item_ids:
            try:
                # Move the item
                move_result = self.move_task_to_status(project_id, item_id, status_name)
                
                result = {
                    'item_id': item_id,
                    'move_success': True,
                    'move_result': move_result
                }
                
                # Add comment if requested
                if comment and item_id in issue_urls:
                    try:
                        comment_result = self.add_issue_comment(issue_urls[item_id], comment)
                        result['comment_success'] = True
                        result['comment_result'] = comment_result
                    except Exception as e:
                        result['comment_success'] = False
                        result['comment_error'] = str(e)
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'item_id': item_id,
                    'move_success': False,
                    'move_error': str(e)
                })
        
        return results
    
    def list_workflow_runs(self, owner: str, repo: str, workflow_id: str, branch: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent runs for a specific workflow, optionally filtered by branch.
        
        Args:
            owner: Repository owner (username or organization)
            repo: Repository name
            workflow_id: Workflow ID or filename (e.g., "12345678" or "build.yml")
            branch: Optional branch to filter runs
            limit: Maximum number of runs to return (default: 10)
            
        Returns:
            List of workflow runs with their details
            
        Example:
            >>> runs = manager.list_workflow_runs("owner", "repo", "build.yml", "development", 5)
            >>> for run in runs:
            ...     print(f"Run {run['id']}: {run['status']} - {run['conclusion']}")
        """
        runs_url = f"{self.rest_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
        
        params = {'per_page': limit}
        if branch:
            params['branch'] = branch
        
        response = requests.get(runs_url, headers=self.headers, params=params)
        
        if response.status_code != 200:
            raise Exception(f"Failed to list workflow runs: {response.status_code} - {response.text}")
        
        return response.json().get('workflow_runs', [])
    
    def get_workflow_run(self, owner: str, repo: str, workflow_id: str = None, run_id: str = None, 
                        branch: str = None, last: int = 1) -> Dict[str, Any]:
        """
        Get details for a specific workflow run or the Nth most recent run.
        
        Args:
            owner: Repository owner (username or organization)
            repo: Repository name
            workflow_id: Workflow ID or filename (required if using last parameter)
            run_id: Specific run ID (if not using last parameter)
            branch: Branch to filter runs when using last parameter
            last: Get the Nth most recent run (1 = most recent, 2 = second most recent, etc.)
            
        Returns:
            Workflow run details
            
        Example:
            >>> run = manager.get_workflow_run("owner", "repo", run_id="12345678")
            >>> run = manager.get_workflow_run("owner", "repo", "build.yml", last=1)  # Most recent
            >>> run = manager.get_workflow_run("owner", "repo", "build.yml", "development", last=2)  # 2nd most recent
        """
        if run_id:
            # Get specific run by ID
            run_url = f"{self.rest_url}/repos/{owner}/{repo}/actions/runs/{run_id}"
            response = requests.get(run_url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Failed to get workflow run: {response.status_code} - {response.text}")
            
            return response.json()
        
        elif workflow_id:
            # Get Nth most recent run
            runs = self.list_workflow_runs(owner, repo, workflow_id, branch, limit=last)
            
            if len(runs) < last:
                available = len(runs)
                raise Exception(f"Only {available} runs available, cannot get run #{last}")
            
            # Return the Nth run (last-1 because list is 0-indexed)
            return runs[last - 1]
        
        else:
            raise Exception("Either run_id or workflow_id must be provided")
    
    def get_workflow_logs(self, owner: str, repo: str, workflow_id: str = None, run_id: str = None,
                         branch: str = None, last: int = 1) -> str:
        """
        Download and return logs for a workflow run.
        
        Args:
            owner: Repository owner (username or organization)
            repo: Repository name
            workflow_id: Workflow ID or filename (required if using last parameter)
            run_id: Specific run ID (if not using last parameter)  
            branch: Branch to filter runs when using last parameter
            last: Get logs for the Nth most recent run (1 = most recent, etc.)
            
        Returns:
            Workflow run logs as text
            
        Example:
            >>> logs = manager.get_workflow_logs("owner", "repo", run_id="12345678")
            >>> logs = manager.get_workflow_logs("owner", "repo", "build.yml", last=1)
            >>> logs = manager.get_workflow_logs("owner", "repo", "deploy.yml", "stage", last=2)
        """
        # Get the run details first
        if run_id:
            target_run_id = run_id
        else:
            run_details = self.get_workflow_run(owner, repo, workflow_id, None, branch, last)
            target_run_id = run_details['id']
        
        # Download logs
        logs_url = f"{self.rest_url}/repos/{owner}/{repo}/actions/runs/{target_run_id}/logs"
        response = requests.get(logs_url, headers=self.headers)
        
        if response.status_code != 200:
            if response.status_code == 404:
                raise Exception(f"Logs not available for run {target_run_id} (run may still be in progress or logs expired)")
            else:
                raise Exception(f"Failed to download logs: {response.status_code} - {response.text}")
        
        # GitHub returns logs as a ZIP file, but for simplicity we'll handle it as text
        # Note: In practice, you might want to extract the ZIP and process individual log files
        try:
            return response.text
        except UnicodeDecodeError:
            # If it's actually a ZIP file, return a helpful message
            return f"Logs are available as ZIP download from: {logs_url}\nUse a web browser or curl to download the complete log archive."
    
    def parse_github_url(self, url: str) -> Dict[str, Optional[str]]:
        """
        Parse various GitHub URL formats to extract owner, repo, and other components.
        
        Args:
            url: GitHub URL in various formats
            
        Returns:
            Dictionary with parsed components: owner, repo, project_number, url_type, is_org
            
        Example:
            >>> manager.parse_github_url("https://github.com/owner/repo")
            {'owner': 'owner', 'repo': 'repo', 'project_number': None, 'url_type': 'repository', 'is_org': False}
            >>> manager.parse_github_url("https://github.com/users/owner/projects/1")
            {'owner': 'owner', 'repo': None, 'project_number': 1, 'url_type': 'user_project', 'is_org': False}
        """
        # Normalize URL - remove trailing slashes and ensure https
        url = url.strip().rstrip('/')
        if not url.startswith(('http://', 'https://', 'git@')):
            url = f"https://{url}"
        
        # Repository URL patterns
        repo_patterns = [
            r'https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$',  # https://github.com/owner/repo
            r'git@github\.com:([^/]+)/([^/]+?)(?:\.git)?/?$',       # git@github.com:owner/repo.git
            r'https?://github\.com/([^/]+)/([^/]+)/(?:issues|pulls|actions)',  # issue/PR URLs
        ]
        
        for pattern in repo_patterns:
            match = re.match(pattern, url)
            if match:
                owner, repo = match.groups()
                return {
                    'owner': owner,
                    'repo': repo,
                    'project_number': None,
                    'url_type': 'repository',
                    'is_org': False  # Cannot determine from URL alone
                }
        
        # User project URL pattern
        user_project_pattern = r'https?://github\.com/users/([^/]+)/projects/(\d+)'
        match = re.match(user_project_pattern, url)
        if match:
            owner, project_number = match.groups()
            return {
                'owner': owner,
                'repo': None,
                'project_number': int(project_number),
                'url_type': 'user_project',
                'is_org': False
            }
        
        # Organization project URL pattern
        org_project_pattern = r'https?://github\.com/orgs/([^/]+)/projects/(\d+)'
        match = re.match(org_project_pattern, url)
        if match:
            owner, project_number = match.groups()
            return {
                'owner': owner,
                'repo': None,
                'project_number': int(project_number),
                'url_type': 'org_project', 
                'is_org': True
            }
        
        # If no patterns match, return empty result
        return {
            'owner': None,
            'repo': None,
            'project_number': None,
            'url_type': 'unknown',
            'is_org': False
        }
    
    def resolve_project_id_from_number(self, owner: str, project_number: int, is_org: bool = False) -> str:
        """
        Resolve a public project number to internal PVT_xxx project ID via GitHub API.
        
        Args:
            owner: Project owner (username or organization name)
            project_number: Public project number from URL
            is_org: True if this is an organization project, False for user project
            
        Returns:
            Internal PVT_xxx project ID
            
        Raises:
            Exception: If project not found or insufficient permissions
            
        Example:
            >>> manager.resolve_project_id_from_number("ai-janitor", 1, False)
            "PVT_kwHODSyt1s4BBe5J"
        """
        if is_org:
            # Query for organization project
            query = """
            query($owner: String!, $number: Int!) {
                organization(login: $owner) {
                    projectV2(number: $number) {
                        id
                        title
                        number
                    }
                }
            }
            """
        else:
            # Query for user project
            query = """
            query($owner: String!, $number: Int!) {
                user(login: $owner) {
                    projectV2(number: $number) {
                        id
                        title
                        number
                    }
                }
            }
            """
        
        variables = {
            'owner': owner,
            'number': project_number
        }
        
        try:
            result = self.execute_graphql(query, variables)
            
            # Extract project from response
            entity_key = 'organization' if is_org else 'user'
            entity = result.get(entity_key)
            
            if not entity:
                raise Exception(f"{'Organization' if is_org else 'User'} '{owner}' not found or not accessible")
            
            project = entity.get('projectV2')
            if not project:
                raise Exception(f"Project #{project_number} not found for {owner} or not accessible")
            
            return project['id']
            
        except Exception as e:
            if "Could not resolve" in str(e) or "Field 'projectV2' doesn't exist" in str(e):
                raise Exception(f"Project #{project_number} not found for {owner}. It may be private or you may lack permissions.")
            raise e
    
    def generate_env_setup_from_url(self, url: str) -> Dict[str, Any]:
        """
        Parse GitHub URL and generate environment variable setup commands.
        
        Args:
            url: GitHub repository or project URL
            
        Returns:
            Dictionary with parsed info and generated export commands
            
        Example:
            >>> result = manager.generate_env_setup_from_url("https://github.com/users/ai-janitor/projects/1")
            >>> print(result['export_commands'])
        """
        parsed = self.parse_github_url(url)
        
        if parsed['url_type'] == 'unknown':
            return {
                'success': False,
                'error': f"Could not parse GitHub URL: {url}",
                'parsed': parsed,
                'export_commands': []
            }
        
        export_commands = []
        project_info = None
        
        try:
            if parsed['url_type'] in ['user_project', 'org_project']:
                # Resolve project number to PVT_xxx ID
                project_id = self.resolve_project_id_from_number(
                    parsed['owner'], 
                    parsed['project_number'], 
                    parsed['is_org']
                )
                
                # Get project details for display
                project_details = self.get_project_info(project_id)
                project_info = {
                    'id': project_id,
                    'title': project_details['node']['title'],
                    'number': parsed['project_number']
                }
                
                export_commands = [
                    f"export GITHUB_TOKEN=your_personal_token  # Set this manually",
                    f"export GITHUB_PROJECT_ID={project_id}",
                    f"export GITHUB_OWNER={parsed['owner']}"
                ]
                
            elif parsed['url_type'] == 'repository':
                export_commands = [
                    f"export GITHUB_TOKEN=your_personal_token  # Set this manually",
                    f"export GITHUB_OWNER={parsed['owner']}",
                    f"export GITHUB_REPO={parsed['repo']}"
                ]
            
            return {
                'success': True,
                'parsed': parsed,
                'project_info': project_info,
                'export_commands': export_commands,
                'url_type': parsed['url_type']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'parsed': parsed,
                'export_commands': []
            }
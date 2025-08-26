"""
UNDERSTANDING: Core GitHub Projects v2 API manager class
DEPENDENCIES: requests library for HTTP/GraphQL API calls
EXPORTS: GitHubProjectsManager class for all project operations
INTEGRATION: Replicates MCP Server functionality for environments without AI
"""

import requests
from typing import Dict, Any, List, Optional


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
                    items(first: 50) {
                        nodes {
                            id
                            databaseId
                            content {
                                ... on Issue {
                                    id
                                    number
                                    title
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
        project_info = self.get_project_info(project_id)
        project = project_info['node']
        
        items = []
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
            
            items.append(item_data)
        
        return items
    
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
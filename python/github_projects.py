#!/usr/bin/env python3
"""
UNDERSTANDING: Standalone Python script for GitHub Projects v2 task management
DEPENDENCIES: requests library for HTTP/GraphQL API calls
EXPORTS: Functions for moving tasks between stages and adding comments
INTEGRATION: Replicates MCP Server functionality for environments without AI
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, Any, List, Optional

class GitHubProjectsManager:
    """
    UNDERSTANDING: Main class for GitHub Projects v2 API operations
    EXPECTS: GitHub token with project and repo scopes
    RETURNS: Success/failure for task management operations
    INTEGRATION: Standalone alternative to MCP Server tools
    """
    
    def __init__(self, token: str):
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
        UNDERSTANDING: Execute GraphQL query against GitHub API
        EXPECTS: GraphQL query string and optional variables
        RETURNS: API response data or raises exception
        INTEGRATION: Core method for all GraphQL operations
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
        UNDERSTANDING: Get project details including field information
        EXPECTS: GitHub Projects v2 project ID (PVT_xxx format)
        RETURNS: Project data with fields and their options
        INTEGRATION: Required for identifying status field and option IDs
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
        UNDERSTANDING: Move a project item to a specific status column
        EXPECTS: project_id, item_id, and status_name (Todo/In Progress/Done)
        RETURNS: Updated item details
        INTEGRATION: Core functionality for task stage management
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
            raise Exception(f"Status option '{status_name}' not found in project")
        
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
        UNDERSTANDING: Add a comment to a GitHub issue
        EXPECTS: Full GitHub issue URL and comment text
        RETURNS: Created comment details
        INTEGRATION: Audit trail functionality for task movements
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
        UNDERSTANDING: List all items in a project with their current status
        EXPECTS: GitHub Projects v2 project ID
        RETURNS: List of items with status and issue details
        INTEGRATION: Helper for bulk operations and status reporting
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

def main():
    """
    UNDERSTANDING: Command-line interface for GitHub Projects v2 task management
    EXPECTS: Command-line arguments for operation type and parameters
    RETURNS: Exit code 0 for success, 1 for failure
    INTEGRATION: Standalone script entry point
    """
    parser = argparse.ArgumentParser(description='GitHub Projects v2 Task Management')
    parser.add_argument('--token', required=True, help='GitHub personal access token')
    parser.add_argument('--project-id', required=True, help='GitHub Projects v2 ID (PVT_xxx format)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Move task command
    move_parser = subparsers.add_parser('move', help='Move task to different status')
    move_parser.add_argument('--item-id', required=True, help='Project item ID')
    move_parser.add_argument('--status', required=True, choices=['Todo', 'In Progress', 'Done'], help='Target status')
    move_parser.add_argument('--comment', help='Optional comment to add to the issue')
    
    # Add comment command
    comment_parser = subparsers.add_parser('comment', help='Add comment to issue')
    comment_parser.add_argument('--issue-url', required=True, help='GitHub issue URL')
    comment_parser.add_argument('--message', required=True, help='Comment message')
    
    # List items command
    list_parser = subparsers.add_parser('list', help='List all project items')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        manager = GitHubProjectsManager(args.token)
        
        if args.command == 'move':
            print(f"Moving item {args.item_id} to {args.status}...")
            result = manager.move_task_to_status(args.project_id, args.item_id, args.status)
            print(f"✅ Successfully moved item")
            
            if args.comment:
                # Need to get issue URL from project item
                project_info = manager.get_project_info(args.project_id)
                item_url = None
                for item in project_info['node']['items']['nodes']:
                    if item['id'] == args.item_id:
                        item_url = item['content']['url']
                        break
                
                if item_url:
                    print(f"Adding comment: {args.comment}")
                    comment_result = manager.add_issue_comment(item_url, args.comment)
                    print(f"✅ Successfully added comment")
        
        elif args.command == 'comment':
            print(f"Adding comment to {args.issue_url}")
            result = manager.add_issue_comment(args.issue_url, args.message)
            print(f"✅ Successfully added comment")
        
        elif args.command == 'list':
            print(f"Listing items in project {args.project_id}")
            items = manager.list_project_items(args.project_id)
            
            print(f"\nFound {len(items)} items:")
            print("-" * 80)
            for item in items:
                issue = item['issue']
                print(f"Status: {item['status']:<12} | #{issue['number']} {issue['title']}")
                print(f"  Item ID: {item['id']}")
                print(f"  URL: {issue['url']}")
                print()
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
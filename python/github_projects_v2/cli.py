"""
UNDERSTANDING: Command-line interface for GitHub Projects v2 task management
DEPENDENCIES: argparse for CLI, manager module for API operations
EXPORTS: main() function and CLI entry point
INTEGRATION: Provides command-line tool after pip installation
"""

import sys
import argparse
from .manager import GitHubProjectsManager


def main():
    """
    Command-line interface for GitHub Projects v2 task management.
    
    Entry point for the gh-projects-v2 command after pip installation.
    
    Security: Uses GITHUB_TOKEN and GITHUB_PROJECT_ID environment variables
    to avoid exposing tokens in command line history or process lists.
    """
    parser = argparse.ArgumentParser(
        description='GitHub Projects v2 Task Management CLI - Uses GITHUB_TOKEN and GITHUB_PROJECT_ID environment variables',
        prog='gh-projects-v2'
    )
    parser.add_argument('--project-id', help='GitHub Projects v2 ID (PVT_xxx format) - overrides GITHUB_PROJECT_ID env var')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0.0')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Move task command
    move_parser = subparsers.add_parser('move', help='Move task to different status')
    move_parser.add_argument('--item-id', required=True, help='Project item ID')
    move_parser.add_argument('--status', required=True, help='Target status')
    move_parser.add_argument('--comment', help='Optional comment to add to the issue')
    
    # Batch move command
    batch_parser = subparsers.add_parser('batch-move', help='Move multiple tasks to same status')
    batch_parser.add_argument('--item-ids', required=True, nargs='+', help='List of project item IDs')
    batch_parser.add_argument('--status', required=True, help='Target status for all items')
    batch_parser.add_argument('--comment', help='Optional comment to add to all issues')
    
    # Add comment command
    comment_parser = subparsers.add_parser('comment', help='Add comment to issue')
    comment_parser.add_argument('--issue-url', required=True, help='GitHub issue URL')
    comment_parser.add_argument('--message', required=True, help='Comment message')
    
    # List items command
    list_parser = subparsers.add_parser('list', help='List all project items')
    list_parser.add_argument('--status-filter', help='Filter by status name')
    
    # List statuses command
    statuses_parser = subparsers.add_parser('statuses', help='List available status options')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Get token from environment variable (required for security)
    import os
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable is required", file=sys.stderr)
        print("Set it with: export GITHUB_TOKEN=ghp_your_token", file=sys.stderr)
        return 1
    
    # Get project ID from argument or environment variable
    project_id = args.project_id or os.getenv('GITHUB_PROJECT_ID')
    if not project_id:
        print("❌ Error: Project ID required", file=sys.stderr)
        print("Use --project-id PVT_xxx or set GITHUB_PROJECT_ID environment variable", file=sys.stderr)
        return 1
    
    try:
        manager = GitHubProjectsManager(token)
        
        if args.command == 'move':
            print(f"Moving item {args.item_id} to {args.status}...")
            result = manager.move_task_to_status(project_id, args.item_id, args.status)
            print(f"✅ Successfully moved item")
            
            if args.comment:
                # Get issue URL from project item
                project_info = manager.get_project_info(project_id)
                item_url = None
                for item in project_info['node']['items']['nodes']:
                    if item['id'] == args.item_id:
                        item_url = item['content']['url']
                        break
                
                if item_url:
                    print(f"Adding comment: {args.comment}")
                    comment_result = manager.add_issue_comment(item_url, args.comment)
                    print(f"✅ Successfully added comment")
        
        elif args.command == 'batch-move':
            print(f"Moving {len(args.item_ids)} items to {args.status}...")
            results = manager.move_multiple_tasks(
                project_id, 
                args.item_ids, 
                args.status, 
                args.comment
            )
            
            success_count = sum(1 for r in results if r['move_success'])
            print(f"✅ Successfully moved {success_count}/{len(results)} items")
            
            # Show any failures
            for result in results:
                if not result['move_success']:
                    print(f"❌ Failed to move {result['item_id']}: {result['move_error']}")
        
        elif args.command == 'comment':
            print(f"Adding comment to {args.issue_url}")
            result = manager.add_issue_comment(args.issue_url, args.message)
            print(f"✅ Successfully added comment")
        
        elif args.command == 'list':
            print(f"Listing items in project {project_id}")
            items = manager.list_project_items(project_id)
            
            # Apply status filter if specified
            if args.status_filter:
                items = [item for item in items if item['status'] == args.status_filter]
                print(f"Filtering by status: {args.status_filter}")
            
            print(f"\nFound {len(items)} items:")
            print("-" * 80)
            
            # Group by status
            status_groups = {}
            for item in items:
                status = item['status']
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(item)
            
            for status, status_items in status_groups.items():
                print(f"\n{status} ({len(status_items)} items):")
                print("-" * 40)
                for item in status_items:
                    issue = item['issue']
                    print(f"  #{issue['number']} {issue['title']}")
                    print(f"    Item ID: {item['id']}")
                    print(f"    URL: {issue['url']}")
                    print()
        
        elif args.command == 'statuses':
            print(f"Available statuses in project {project_id}:")
            statuses = manager.get_available_statuses(project_id)
            for status in statuses:
                print(f"  - {status}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
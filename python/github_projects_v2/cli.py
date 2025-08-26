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
        description='GitHub Projects v2 Task Management CLI - Uses GITHUB_TOKEN, GITHUB_PROJECT_ID, GITHUB_OWNER, and GITHUB_REPO environment variables',
        prog='gh-projects-v2'
    )
    parser.add_argument('--project-id', help='GitHub Projects v2 ID (PVT_xxx format) - overrides GITHUB_PROJECT_ID env var')
    parser.add_argument('--version', action='version', version='%(prog)s 1.9.0')
    parser.add_argument('--help-setup', action='store_true', help='Show environment variable setup examples')
    parser.add_argument('--extract-setup', metavar='URL', help='Extract environment setup from GitHub URL (repo or project)')
    
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
    list_parser.add_argument('--search', help='Search for keywords in task titles and descriptions')
    list_parser.add_argument('--exact', action='store_true', help='Search for exact phrase instead of keywords')
    
    # Detail command
    detail_parser = subparsers.add_parser('detail', help='Show detailed information for a specific task')
    detail_parser.add_argument('--item-id', required=True, help='Project item ID (PVTI_xxx format)')
    
    # List statuses command
    statuses_parser = subparsers.add_parser('statuses', help='List available status options')
    
    # Workflow commands
    workflow_parser = subparsers.add_parser('trigger-workflow', help='Trigger GitHub Actions workflow')
    workflow_parser.add_argument('--owner', help='Repository owner (username or organization) - overrides GITHUB_OWNER env var')
    workflow_parser.add_argument('--repo', help='Repository name - overrides GITHUB_REPO env var')
    workflow_parser.add_argument('--workflow', required=True, help='Workflow ID or filename (e.g., build.yml)')
    workflow_parser.add_argument('--branch', default='main', help='Git branch to run workflow on (default: main)')
    
    # List workflows command
    list_workflows_parser = subparsers.add_parser('list-workflows', help='List all workflows in repository')
    list_workflows_parser.add_argument('--owner', help='Repository owner - overrides GITHUB_OWNER env var')
    list_workflows_parser.add_argument('--repo', help='Repository name - overrides GITHUB_REPO env var')
    list_workflows_parser.add_argument('--branch', help='Show workflows available in specific branch')
    
    # List workflow runs command
    list_runs_parser = subparsers.add_parser('list-workflow-runs', help='List recent runs for a workflow')
    list_runs_parser.add_argument('--owner', help='Repository owner - overrides GITHUB_OWNER env var')
    list_runs_parser.add_argument('--repo', help='Repository name - overrides GITHUB_REPO env var')
    list_runs_parser.add_argument('--workflow', required=True, help='Workflow ID or filename (e.g., build.yml)')
    list_runs_parser.add_argument('--branch', help='Filter runs by branch')
    list_runs_parser.add_argument('--limit', type=int, default=10, help='Maximum number of runs to show (default: 10)')
    
    # Get workflow run command
    get_run_parser = subparsers.add_parser('get-workflow-run', help='Get details for a specific workflow run')
    get_run_parser.add_argument('--owner', help='Repository owner - overrides GITHUB_OWNER env var')
    get_run_parser.add_argument('--repo', help='Repository name - overrides GITHUB_REPO env var')
    get_run_parser.add_argument('--workflow', help='Workflow ID or filename (required if using --last)')
    get_run_parser.add_argument('--run-id', help='Specific run ID')
    get_run_parser.add_argument('--branch', help='Filter runs by branch (when using --last)')
    get_run_parser.add_argument('--last', type=int, default=1, help='Get Nth most recent run (default: 1 = most recent)')
    
    # Get workflow logs command
    get_logs_parser = subparsers.add_parser('get-workflow-logs', help='Download logs for a workflow run')
    get_logs_parser.add_argument('--owner', help='Repository owner - overrides GITHUB_OWNER env var')
    get_logs_parser.add_argument('--repo', help='Repository name - overrides GITHUB_REPO env var')
    get_logs_parser.add_argument('--workflow', help='Workflow ID or filename (required if using --last)')
    get_logs_parser.add_argument('--run-id', help='Specific run ID')
    get_logs_parser.add_argument('--branch', help='Filter runs by branch (when using --last)')
    get_logs_parser.add_argument('--last', type=int, default=1, help='Get logs from Nth most recent run (default: 1 = most recent)')
    
    args = parser.parse_args()
    
    if args.help_setup:
        print("GitHub Projects v2 CLI - Environment Setup Guide")
        print("=" * 55)
        print()
        print("Required Environment Variables:")
        print("  export GITHUB_TOKEN=your_personal_token")
        print("  export GITHUB_PROJECT_ID=your_project_id")
        print()
        print("Optional Environment Variables (can override per command):")
        print("  export GITHUB_OWNER=repo_owner_username")
        print("  export GITHUB_REPO=repository_name")
        print()
        print("Setup Examples:")
        print("  # For your own repository")
        print("  export GITHUB_TOKEN=ghp_abc123def456")
        print("  export GITHUB_PROJECT_ID=PVT_kwHODSyt1s4BBe5J")
        print("  export GITHUB_OWNER=your-username")
        print("  export GITHUB_REPO=your-repo-name")
        print()
        print("  # For someone else's repository (you need collaborator access)")
        print("  export GITHUB_TOKEN=your_personal_token")
        print("  export GITHUB_PROJECT_ID=their_project_id")  
        print("  export GITHUB_OWNER=their-username")
        print("  export GITHUB_REPO=their-repo-name")
        print()
        print("Required GitHub Token Permissions:")
        print("  ✅ repo     - Access to repositories and issues")
        print("  ✅ project  - Access to GitHub Projects v2")
        print("  ✅ actions  - Trigger and monitor workflows (optional)")
        print()
        print("Usage Examples:")
        print("  gh-projects-v2 list")
        print("  gh-projects-v2 trigger-workflow --workflow deploy.yml --branch stage")
        print("  gh-projects-v2 get-workflow-logs --workflow build.yml --last 1")
        print()
        return 0
    
    if args.extract_setup:
        print("GitHub Projects v2 CLI - URL Setup Extraction")
        print("=" * 50)
        print(f"Processing URL: {args.extract_setup}")
        print()
        
        # Get token from environment variable (required for API calls)
        import os
        token = os.getenv('GITHUB_TOKEN')
        if not token:
            print("⚠️  Warning: GITHUB_TOKEN environment variable not set")
            print("   API calls may fail for private projects or organizations")
            print("   Set with: export GITHUB_TOKEN=your_personal_token")
            print()
        
        try:
            # Create manager instance (with or without token)
            manager = GitHubProjectsManager(token or "dummy_token")
            
            # Generate environment setup from URL
            result = manager.generate_env_setup_from_url(args.extract_setup)
            
            if result['success']:
                print("✅ Successfully parsed GitHub URL")
                
                # Show parsed information
                parsed = result['parsed']
                print(f"URL Type: {parsed['url_type'].replace('_', ' ').title()}")
                print(f"Owner: {parsed['owner']}")
                if parsed['repo']:
                    print(f"Repository: {parsed['repo']}")
                if result.get('project_info'):
                    project = result['project_info']
                    print(f"Project: #{project['number']} - {project['title']}")
                    print(f"Project ID: {project['id']}")
                print()
                
                # Show generated export commands
                print("Generated Environment Setup:")
                print("-" * 35)
                for cmd in result['export_commands']:
                    print(cmd)
                print()
                
                # Additional guidance based on URL type
                if result['url_type'] in ['user_project', 'org_project']:
                    print("✨ Ready for project management commands:")
                    print("   gh-projects-v2 list")
                    print("   gh-projects-v2 move --item-id PVTI_xxx --status 'Done'")
                elif result['url_type'] == 'repository':
                    print("✨ Ready for workflow commands (also need GITHUB_PROJECT_ID for tasks):")
                    print("   gh-projects-v2 list-workflows")
                    print("   gh-projects-v2 trigger-workflow --workflow build.yml")
                
            else:
                print("❌ Failed to parse GitHub URL")
                print(f"Error: {result['error']}")
                print()
                print("Supported URL formats:")
                print("  • https://github.com/owner/repo")
                print("  • https://github.com/users/owner/projects/N")
                print("  • https://github.com/orgs/organization/projects/N")
                print("  • git@github.com:owner/repo.git")
                return 1
                
        except Exception as e:
            print(f"❌ Error processing URL: {e}")
            return 1
        
        return 0
    
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
            
            # Use search if provided, otherwise get all items
            if args.search:
                items = manager.search_project_items(project_id, args.search, args.status_filter, args.exact)
                search_type = "exact phrase" if args.exact else "keywords"
                print(f"Searching for {search_type}: '{args.search}'")
                if args.status_filter:
                    print(f"Filtering by status: {args.status_filter}")
            else:
                items = manager.list_project_items(project_id)
                # Apply status filter if specified (case-insensitive, space-tolerant)
                if args.status_filter:
                    items = [item for item in items if manager._status_matches(item['status'], args.status_filter)]
                    print(f"Filtering by status: {args.status_filter}")
            
            print(f"\nFound {len(items)} items:")
            print()
            
            if items:
                # Table format with columns: Status, Issue#, Title, Item ID
                print(f"{'Status':<15} {'Issue#':<8} {'Title':<50} {'Item ID'}")
                print("-" * 100)
                
                for item in items:
                    issue = item['issue']
                    status = item['status'][:14]  # Truncate status if too long
                    issue_num = f"#{issue['number']}"
                    title = issue['title'][:49] + "..." if len(issue['title']) > 49 else issue['title']
                    item_id = item['id']
                    
                    print(f"{status:<15} {issue_num:<8} {title:<50} {item_id}")
                
                print()
                print(f"💡 To move a task: gh-projects-v2 move --item-id ITEM_ID --status \"New Status\"")
            else:
                print("No items found matching your criteria.")
        
        elif args.command == 'detail':
            print(f"Getting detailed information for item {args.item_id}...")
            detail = manager.get_task_detail(project_id, args.item_id)
            
            issue = detail['issue']
            
            # Print main task information
            print(f"\n{'='*80}")
            print(f"TASK DETAILS")
            print(f"{'='*80}")
            print(f"Issue #{issue['number']}: {issue['title']}")
            print(f"Status: {detail['status']}")
            print(f"URL: {issue['url']}")
            print(f"State: {issue.get('state', 'Unknown').upper()}")
            print(f"Author: {issue.get('author', {}).get('login', 'Unknown')}")
            print(f"Created: {issue.get('createdAt', 'Unknown')}")
            print(f"Updated: {issue.get('updatedAt', 'Unknown')}")
            print(f"Item ID: {detail['item_id']}")
            
            # Print assignees if any
            if issue.get('assignees') and issue['assignees'].get('nodes'):
                assignees = [a.get('login') for a in issue['assignees']['nodes']]
                print(f"Assignees: {', '.join(assignees)}")
            
            # Print labels if any  
            if issue.get('labels') and issue['labels'].get('nodes'):
                labels = [f"{l['name']}" for l in issue['labels']['nodes']]
                print(f"Labels: {', '.join(labels)}")
                
            # Print custom project fields
            if detail['fields']:
                print(f"\nProject Fields:")
                for field_name, field_value in detail['fields'].items():
                    if field_name != 'Status':  # Already shown above
                        print(f"  {field_name}: {field_value}")
            
            # Print description/body
            if issue.get('body'):
                print(f"\n{'='*80}")
                print(f"DESCRIPTION")
                print(f"{'='*80}")
                print(issue['body'])
            
            # Print comments
            if issue.get('comments') and issue['comments'].get('nodes'):
                comments = issue['comments']['nodes']
                print(f"\n{'='*80}")
                print(f"COMMENTS ({len(comments)})")
                print(f"{'='*80}")
                
                for i, comment in enumerate(comments, 1):
                    author = comment.get('author', {}).get('login', 'Unknown')
                    created = comment.get('createdAt', 'Unknown')
                    body = comment.get('body', '')
                    
                    print(f"\n--- Comment #{i} ---")
                    print(f"Author: {author}")
                    print(f"Date: {created}")
                    print(f"Content:")
                    print(body)
                    print("-" * 40)
            else:
                print(f"\n{'='*80}")
                print(f"COMMENTS")
                print(f"{'='*80}")
                print("No comments found.")
        
        elif args.command == 'statuses':
            print(f"Available statuses in project {project_id}:")
            statuses = manager.get_available_statuses(project_id)
            for status in statuses:
                print(f"  - {status}")
        
        elif args.command == 'trigger-workflow':
            # Get owner/repo from arguments or environment variables
            owner = args.owner or os.getenv('GITHUB_OWNER')
            repo = args.repo or os.getenv('GITHUB_REPO')
            
            if not owner:
                print("❌ Error: Repository owner required", file=sys.stderr)
                print("Use --owner USERNAME or set GITHUB_OWNER environment variable", file=sys.stderr)
                return 1
            if not repo:
                print("❌ Error: Repository name required", file=sys.stderr)
                print("Use --repo REPONAME or set GITHUB_REPO environment variable", file=sys.stderr)
                return 1
            
            print(f"Triggering workflow '{args.workflow}' in {owner}/{repo} on branch '{args.branch}'...")
            result = manager.trigger_workflow(owner, repo, args.workflow, args.branch)
            print(f"✅ {result['message']}")
        
        elif args.command == 'list-workflows':
            # Get owner/repo from arguments or environment variables
            owner = args.owner or os.getenv('GITHUB_OWNER')
            repo = args.repo or os.getenv('GITHUB_REPO')
            
            if not owner:
                print("❌ Error: Repository owner required", file=sys.stderr)
                print("Use --owner USERNAME or set GITHUB_OWNER environment variable", file=sys.stderr)
                return 1
            if not repo:
                print("❌ Error: Repository name required", file=sys.stderr)
                print("Use --repo REPONAME or set GITHUB_REPO environment variable", file=sys.stderr)
                return 1
            
            branch_text = f" (branch: {args.branch})" if args.branch else ""
            print(f"Listing workflows in {owner}/{repo}{branch_text}:")
            workflows = manager.list_workflows(owner, repo, args.branch)
            
            if not workflows:
                print("No workflows found in this repository.")
            else:
                print(f"\nFound {len(workflows)} workflows:")
                print("-" * 80)
                for wf in workflows:
                    print(f"Name: {wf['name']}")
                    print(f"  ID: {wf['id']}")
                    print(f"  File: {wf['path']}")
                    print(f"  State: {wf['state']}")
                    if 'badge_url' in wf:
                        print(f"  Badge: {wf['badge_url']}")
                    print()
        
        elif args.command == 'list-workflow-runs':
            # Get owner/repo from arguments or environment variables
            owner = args.owner or os.getenv('GITHUB_OWNER')
            repo = args.repo or os.getenv('GITHUB_REPO')
            
            if not owner:
                print("❌ Error: Repository owner required", file=sys.stderr)
                print("Use --owner USERNAME or set GITHUB_OWNER environment variable", file=sys.stderr)
                return 1
            if not repo:
                print("❌ Error: Repository name required", file=sys.stderr)
                print("Use --repo REPONAME or set GITHUB_REPO environment variable", file=sys.stderr)
                return 1
            
            branch_text = f" (branch: {args.branch})" if args.branch else ""
            print(f"Listing recent runs for workflow '{args.workflow}' in {owner}/{repo}{branch_text}:")
            
            runs = manager.list_workflow_runs(owner, repo, args.workflow, args.branch, args.limit)
            
            if not runs:
                print("No workflow runs found.")
            else:
                print(f"\nFound {len(runs)} recent runs:")
                print("-" * 100)
                for run in runs:
                    status = run.get('status', 'unknown')
                    conclusion = run.get('conclusion', 'N/A')
                    branch = run.get('head_branch', 'N/A')
                    created = run.get('created_at', 'N/A')
                    print(f"Run ID: {run['id']}")
                    print(f"  Status: {status} | Conclusion: {conclusion}")
                    print(f"  Branch: {branch} | Created: {created}")
                    if run.get('html_url'):
                        print(f"  URL: {run['html_url']}")
                    print()
        
        elif args.command == 'get-workflow-run':
            # Get owner/repo from arguments or environment variables
            owner = args.owner or os.getenv('GITHUB_OWNER')
            repo = args.repo or os.getenv('GITHUB_REPO')
            
            if not owner:
                print("❌ Error: Repository owner required", file=sys.stderr)
                print("Use --owner USERNAME or set GITHUB_OWNER environment variable", file=sys.stderr)
                return 1
            if not repo:
                print("❌ Error: Repository name required", file=sys.stderr)
                print("Use --repo REPONAME or set GITHUB_REPO environment variable", file=sys.stderr)
                return 1
            
            if args.run_id:
                print(f"Getting workflow run {args.run_id} details:")
                run = manager.get_workflow_run(owner, repo, run_id=args.run_id)
            elif args.workflow:
                ordinal = "st" if args.last == 1 else "nd" if args.last == 2 else "rd" if args.last == 3 else "th"
                branch_text = f" from branch {args.branch}" if args.branch else ""
                print(f"Getting {args.last}{ordinal} most recent run for '{args.workflow}'{branch_text}:")
                run = manager.get_workflow_run(owner, repo, args.workflow, branch=args.branch, last=args.last)
            else:
                print("❌ Error: Either --run-id or --workflow must be provided", file=sys.stderr)
                return 1
            
            print(f"\nWorkflow Run Details:")
            print("-" * 50)
            print(f"Run ID: {run['id']}")
            print(f"Status: {run.get('status', 'unknown')}")
            print(f"Conclusion: {run.get('conclusion', 'N/A')}")
            print(f"Branch: {run.get('head_branch', 'N/A')}")
            print(f"Commit: {run.get('head_sha', 'N/A')[:8]}")
            print(f"Created: {run.get('created_at', 'N/A')}")
            print(f"Updated: {run.get('updated_at', 'N/A')}")
            if run.get('html_url'):
                print(f"URL: {run['html_url']}")
        
        elif args.command == 'get-workflow-logs':
            # Get owner/repo from arguments or environment variables
            owner = args.owner or os.getenv('GITHUB_OWNER')
            repo = args.repo or os.getenv('GITHUB_REPO')
            
            if not owner:
                print("❌ Error: Repository owner required", file=sys.stderr)
                print("Use --owner USERNAME or set GITHUB_OWNER environment variable", file=sys.stderr)
                return 1
            if not repo:
                print("❌ Error: Repository name required", file=sys.stderr)
                print("Use --repo REPONAME or set GITHUB_REPO environment variable", file=sys.stderr)
                return 1
            
            if args.run_id:
                print(f"Downloading logs for workflow run {args.run_id}:")
                logs = manager.get_workflow_logs(owner, repo, run_id=args.run_id)
            elif args.workflow:
                ordinal = "st" if args.last == 1 else "nd" if args.last == 2 else "rd" if args.last == 3 else "th"
                branch_text = f" from branch {args.branch}" if args.branch else ""
                print(f"Downloading logs for {args.last}{ordinal} most recent run of '{args.workflow}'{branch_text}:")
                logs = manager.get_workflow_logs(owner, repo, args.workflow, branch=args.branch, last=args.last)
            else:
                print("❌ Error: Either --run-id or --workflow must be provided", file=sys.stderr)
                return 1
            
            print("\n" + "="*80)
            print("WORKFLOW LOGS")
            print("="*80)
            print(logs)
            print("="*80)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
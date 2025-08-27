"""
UNDERSTANDING: Command-line interface for GitHub Projects v2 task management
DEPENDENCIES: argparse for CLI, manager module for API operations, argcomplete for shell completion
EXPORTS: main() function and CLI entry point
INTEGRATION: Provides command-line tool after pip installation with shell completion support
"""

import sys
import argparse
from .manager import GitHubProjectsManager
from .bashrc_manager import BashrcManager

# Import completion functions
try:
    import argcomplete
    from .completers import (
        item_id_completer, status_completer, workflow_completer, 
        branch_completer, issue_url_completer
    )
    COMPLETION_AVAILABLE = True
except ImportError:
    COMPLETION_AVAILABLE = False


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
    parser.add_argument('--version', action='version', version='%(prog)s 1.13.0')
    parser.add_argument('--help-setup', action='store_true', help='Show environment variable setup examples')
    parser.add_argument('--extract-setup', metavar='URL', help='Extract environment setup from GitHub URL (repo or project)')
    parser.add_argument('--update-bashrc', action='store_true', help='Automatically update .bashrc/.zshrc with extracted environment variables and completion setup (use with --extract-setup)')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Move task command
    move_parser = subparsers.add_parser('move', help='Move task to different status')
    item_id_arg = move_parser.add_argument('--item-id', required=True, help='Project item ID')
    status_arg = move_parser.add_argument('--status', required=True, help='Target status')
    move_parser.add_argument('--comment', help='Optional comment to add to the issue')
    
    # Add completers if available
    if COMPLETION_AVAILABLE:
        item_id_arg.completer = item_id_completer
        status_arg.completer = status_completer
    
    # Batch move command
    batch_parser = subparsers.add_parser('batch-move', help='Move multiple tasks to same status')
    batch_item_ids_arg = batch_parser.add_argument('--item-ids', required=True, nargs='+', help='List of project item IDs')
    batch_status_arg = batch_parser.add_argument('--status', required=True, help='Target status for all items')
    batch_parser.add_argument('--comment', help='Optional comment to add to all issues')
    
    # Add completers if available
    if COMPLETION_AVAILABLE:
        batch_item_ids_arg.completer = item_id_completer
        batch_status_arg.completer = status_completer
    
    # Add comment command
    comment_parser = subparsers.add_parser('comment', help='Add comment to issue')
    issue_url_arg = comment_parser.add_argument('--issue-url', required=True, help='GitHub issue URL')
    comment_parser.add_argument('--message', required=True, help='Comment message')
    
    # Add completers if available
    if COMPLETION_AVAILABLE:
        issue_url_arg.completer = issue_url_completer
    
    # List items command
    list_parser = subparsers.add_parser('list', help='List all project items')
    list_status_filter_arg = list_parser.add_argument('--status-filter', help='Filter by status name')
    list_parser.add_argument('--search', help='Search for keywords in task titles and descriptions')
    list_parser.add_argument('--exact', action='store_true', help='Search for exact phrase instead of keywords')
    
    # Add completers if available
    if COMPLETION_AVAILABLE:
        list_status_filter_arg.completer = status_completer
    
    # Detail command
    detail_parser = subparsers.add_parser('detail', help='Show detailed information for a specific task')
    detail_item_id_arg = detail_parser.add_argument('--item-id', required=True, help='Project item ID (PVTI_xxx format)')
    
    # Add completers if available
    if COMPLETION_AVAILABLE:
        detail_item_id_arg.completer = item_id_completer
    
    # List statuses command
    statuses_parser = subparsers.add_parser('statuses', help='List available status options')
    
    # Workflow commands
    workflow_parser = subparsers.add_parser('trigger-workflow', help='Trigger GitHub Actions workflow')
    workflow_parser.add_argument('--owner', help='Repository owner (username or organization) - overrides GITHUB_OWNER env var')
    workflow_parser.add_argument('--repo', help='Repository name - overrides GITHUB_REPO env var')
    workflow_arg = workflow_parser.add_argument('--workflow', required=True, help='Workflow ID or filename (e.g., build.yml)')
    workflow_branch_arg = workflow_parser.add_argument('--branch', default='main', help='Git branch to run workflow on (default: main)')
    
    # Add completers if available
    if COMPLETION_AVAILABLE:
        workflow_arg.completer = workflow_completer
        workflow_branch_arg.completer = branch_completer
    
    # List workflows command
    list_workflows_parser = subparsers.add_parser('list-workflows', help='List all workflows in repository')
    list_workflows_parser.add_argument('--owner', help='Repository owner - overrides GITHUB_OWNER env var')
    list_workflows_parser.add_argument('--repo', help='Repository name - overrides GITHUB_REPO env var')
    list_wf_branch_arg = list_workflows_parser.add_argument('--branch', help='Show workflows available in specific branch')
    
    # Add completers if available
    if COMPLETION_AVAILABLE:
        list_wf_branch_arg.completer = branch_completer
    
    # List workflow runs command
    list_runs_parser = subparsers.add_parser('list-workflow-runs', help='List recent runs for a workflow')
    list_runs_parser.add_argument('--owner', help='Repository owner - overrides GITHUB_OWNER env var')
    list_runs_parser.add_argument('--repo', help='Repository name - overrides GITHUB_REPO env var')
    list_runs_wf_arg = list_runs_parser.add_argument('--workflow', required=True, help='Workflow ID or filename (e.g., build.yml)')
    list_runs_branch_arg = list_runs_parser.add_argument('--branch', help='Filter runs by branch')
    list_runs_parser.add_argument('--limit', type=int, default=10, help='Maximum number of runs to show (default: 10)')
    
    # Add completers if available
    if COMPLETION_AVAILABLE:
        list_runs_wf_arg.completer = workflow_completer
        list_runs_branch_arg.completer = branch_completer
    
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
    
    # Metrics command
    metrics_parser = subparsers.add_parser('metrics', help='Show project assignment metrics')
    metrics_parser.add_argument('--by-status', action='store_true', help='Break down metrics by status')
    
    # Cache management command
    cache_parser = subparsers.add_parser('cache', help='Manage completion cache')
    cache_subparsers = cache_parser.add_subparsers(dest='cache_action', help='Cache actions')
    
    # Cache refresh command
    cache_refresh_parser = cache_subparsers.add_parser('refresh', help='Refresh completion cache')
    cache_refresh_parser.add_argument('--project-id', help='Refresh cache for specific project ID')
    cache_refresh_parser.add_argument('--owner', help='Repository owner for workflow cache')
    cache_refresh_parser.add_argument('--repo', help='Repository name for workflow cache')
    
    # Cache clear command
    cache_clear_parser = cache_subparsers.add_parser('clear', help='Clear completion cache')
    cache_clear_parser.add_argument('--pattern', help='Clear cache files matching pattern (clears all if not specified)')
    
    # Cache info command
    cache_info_parser = cache_subparsers.add_parser('info', help='Show completion cache information')
    
    # Enable shell completion if available
    if COMPLETION_AVAILABLE:
        argcomplete.autocomplete(parser)
    
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
        print("=" * 55)
        print("SHELL COMPLETION SETUP (Copy & Paste)")
        print("=" * 55)
        print()
        print("🚀 Enable TAB completion for commands, item IDs, statuses, and workflows!")
        print()
        print("STEP 1: Install the tool")
        print("  pip install .")
        print()
        print("STEP 2: Enable completion (choose your shell)")
        print()
        print("For BASH users:")
        print('  eval "$(register-python-argcomplete gh-projects-v2)"')
        print()
        print("  # Make it permanent:")
        print('  echo \'eval "$(register-python-argcomplete gh-projects-v2)"\' >> ~/.bashrc')
        print("  source ~/.bashrc")
        print()
        print("For ZSH users:")
        print('  eval "$(register-python-argcomplete gh-projects-v2)"')
        print()
        print("  # Make it permanent:")
        print('  echo \'eval "$(register-python-argcomplete gh-projects-v2)"\' >> ~/.zshrc')
        print("  source ~/.zshrc")
        print()
        print("STEP 3: Set up cache for fast completion")
        print("  gh-projects-v2 cache refresh --project-id $GITHUB_PROJECT_ID")
        print("  gh-projects-v2 cache refresh --owner $GITHUB_OWNER --repo $GITHUB_REPO")
        print()
        print("STEP 4: Test it!")
        print("  gh-projects-v2 <TAB>                    # Shows all commands")
        print("  gh-projects-v2 detail --item-id <TAB>   # Shows your PVTI_ IDs")
        print("  gh-projects-v2 move --status <TAB>      # Shows project statuses")
        print("  gh-projects-v2 trigger-workflow --workflow <TAB>  # Shows .yml files")
        print()
        print("💡 No more copy/pasting long PVTI_xxx identifiers!")
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
                
                # Handle bashrc update if requested
                if args.update_bashrc:
                    print()
                    print("🔧 Updating shell configuration...")
                    print("-" * 35)
                    
                    # Extract token and project_id from the export commands
                    github_token = token or "PLEASE_SET_TOKEN"
                    project_id = ""
                    
                    for cmd in result['export_commands']:
                        if 'GITHUB_PROJECT_ID=' in cmd:
                            project_id = cmd.split('GITHUB_PROJECT_ID=')[1].strip().strip("'\"")
                            break
                    
                    if not project_id and result.get('project_info'):
                        project_id = result['project_info']['id']
                    
                    if project_id:
                        bashrc_manager = BashrcManager()
                        
                        # Ask for user confirmation before modifying shell files
                        shell_file = bashrc_manager.detect_shell_file()
                        print(f"This will modify: {shell_file}")
                        print("A backup will be created automatically.")
                        
                        response = input("Continue? (y/N): ").lower().strip()
                        if response in ['y', 'yes']:
                            success, message, backup_path = bashrc_manager.update_shell_config(
                                github_token, project_id
                            )
                            
                            if success:
                                print(f"✅ {message}")
                                print()
                                print("To activate the changes immediately:")
                                print(f"  {bashrc_manager.get_shell_reload_instruction(shell_file)}")
                                print()
                                print("Or open a new terminal window.")
                            else:
                                print(f"❌ {message}")
                                return 1
                        else:
                            print("Shell configuration update cancelled.")
                    else:
                        print("⚠️  Could not determine PROJECT_ID for shell configuration")
                        print("   Please run without --update-bashrc and set environment variables manually")
                
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
                # Table format with columns: Status, Issue#, Title, Assigned, Last Updated, Item ID
                print(f"{'Status':<15} {'Issue#':<8} {'Title':<35} {'Assigned':<12} {'Updated':<10} {'Item ID'}")
                print("-" * 125)
                
                for item in items:
                    issue = item['issue']
                    status = item['status'][:14]  # Truncate status if too long
                    issue_num = f"#{issue['number']}"
                    title = issue['title'][:34] + "..." if len(issue['title']) > 34 else issue['title']
                    item_id = item['id']
                    
                    # Format assignees
                    assignees = issue.get('assignees', {}).get('nodes', [])
                    if assignees:
                        # Show first assignee, or count if multiple
                        if len(assignees) == 1:
                            assigned = assignees[0]['login'][:11]  # Truncate long usernames
                        else:
                            assigned = f"{assignees[0]['login'][:7]}+{len(assignees)-1}"  # "user+2" format
                    else:
                        assigned = 'Unassigned'
                    
                    # Format the updated date
                    updated_at = issue.get('updatedAt', '')
                    if updated_at:
                        # Parse ISO date and format as MM-DD
                        try:
                            from datetime import datetime
                            dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                            last_updated = dt.strftime('%m-%d')
                        except:
                            last_updated = updated_at[:10] if len(updated_at) >= 10 else updated_at
                    else:
                        last_updated = 'Unknown'
                    
                    print(f"{status:<15} {issue_num:<8} {title:<35} {assigned:<12} {last_updated:<10} {item_id}")
                
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
            
            # Always show helpful comment command at the bottom
            print(f"\n{'='*80}")
            print(f"💡 To add a comment to this task:")
            print(f"gh-projects-v2 comment --issue-url \"{issue['url']}\" --message \"Your comment here\"")
            print(f"{'='*80}")
        
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
        
        elif args.command == 'metrics':
            print(f"Assignment metrics for project {project_id}")
            print("=" * 50)
            
            metrics = manager.get_assignment_metrics(project_id, args.by_status)
            
            if not metrics['success']:
                print(f"❌ Error getting metrics: {metrics['error']}")
                return 1
            
            total_items = metrics['total_items']
            user_counts = metrics['user_counts']
            unassigned_count = metrics['unassigned_count']
            
            print(f"Total Items: {total_items}")
            print()
            
            if not args.by_status:
                # Simple user assignment table
                print("Assignment Distribution:")
                print("-" * 40)
                print(f"{'User':<25} {'Count':<8} {'Percentage'}")
                print("-" * 40)
                
                # Sort users by count (descending)
                sorted_users = sorted(user_counts.items(), key=lambda x: x[1]['count'], reverse=True)
                
                for login, data in sorted_users:
                    count = data['count']
                    percentage = (count / total_items * 100) if total_items > 0 else 0
                    display_name = data['display_name'][:24]  # Truncate long names
                    print(f"{display_name:<25} {count:<8} {percentage:6.1f}%")
                
                if unassigned_count > 0:
                    percentage = (unassigned_count / total_items * 100) if total_items > 0 else 0
                    print(f"{'Unassigned':<25} {unassigned_count:<8} {percentage:6.1f}%")
            else:
                # Status breakdown
                status_breakdown = metrics['status_breakdown']
                
                print("Assignment Distribution by Status:")
                print("-" * 50)
                
                for status, data in status_breakdown.items():
                    print(f"\n{status}:")
                    print("-" * (len(status) + 1))
                    
                    status_total = data['unassigned'] + sum(user_data['count'] for user_data in data['users'].values())
                    
                    if status_total == 0:
                        print("  (no items)")
                        continue
                    
                    # Sort users by count within this status
                    sorted_status_users = sorted(data['users'].items(), key=lambda x: x[1]['count'], reverse=True)
                    
                    for login, user_data in sorted_status_users:
                        count = user_data['count']
                        percentage = (count / status_total * 100) if status_total > 0 else 0
                        display_name = user_data['display_name'][:20]
                        print(f"  {display_name:<22} {count:<4} ({percentage:4.1f}%)")
                    
                    if data['unassigned'] > 0:
                        percentage = (data['unassigned'] / status_total * 100) if status_total > 0 else 0
                        print(f"  {'Unassigned':<22} {data['unassigned']:<4} ({percentage:4.1f}%)")
        
        elif args.command == 'cache':
            from .completion_cache import CompletionCache
            cache = CompletionCache()
            
            if args.cache_action == 'refresh':
                print("Refreshing completion cache...")
                
                # Refresh project cache if specified
                project_id = args.project_id or os.getenv('GITHUB_PROJECT_ID')
                if project_id:
                    print(f"Refreshing cache for project {project_id}...")
                    try:
                        # Refresh item IDs
                        items = manager.list_project_items(project_id)
                        item_ids = [item['id'] for item in items if 'id' in item]
                        cache.set_item_ids(project_id, item_ids)
                        print(f"✅ Cached {len(item_ids)} item IDs")
                        
                        # Refresh statuses
                        statuses = manager.get_available_statuses(project_id)
                        cache.set_statuses(project_id, statuses)
                        print(f"✅ Cached {len(statuses)} status options")
                        
                    except Exception as e:
                        print(f"❌ Error refreshing project cache: {e}")
                
                # Refresh workflow cache if specified
                owner = args.owner or os.getenv('GITHUB_OWNER')
                repo = args.repo or os.getenv('GITHUB_REPO')
                if owner and repo:
                    print(f"Refreshing workflow cache for {owner}/{repo}...")
                    try:
                        workflows = manager.list_workflows(owner, repo)
                        workflow_files = [wf['path'].split('/')[-1] for wf in workflows if 'path' in wf]
                        cache.set_workflows(owner, repo, workflow_files)
                        print(f"✅ Cached {len(workflow_files)} workflow files")
                        
                    except Exception as e:
                        print(f"❌ Error refreshing workflow cache: {e}")
                
                if not project_id and not (owner and repo):
                    print("❌ Specify --project-id or --owner/--repo to refresh cache")
                    return 1
            
            elif args.cache_action == 'clear':
                print("Clearing completion cache...")
                removed = cache.clear_cache(args.pattern)
                if args.pattern:
                    print(f"✅ Removed {removed} cache files matching '{args.pattern}'")
                else:
                    print(f"✅ Removed {removed} cache files")
            
            elif args.cache_action == 'info':
                print("Completion Cache Information")
                print("="*40)
                cache_info = cache.get_cache_info()
                
                if not cache_info:
                    print("No cache files found")
                else:
                    for cache_key, info in cache_info.items():
                        print(f"\nCache: {cache_key}")
                        print(f"  Size: {info['size_bytes']} bytes")
                        print(f"  Age: {int(info['age_seconds'])} seconds")
                        print(f"  Valid (fast TTL): {'Yes' if info['valid_fast'] else 'No'}")
                        print(f"  Valid (slow TTL): {'Yes' if info['valid_slow'] else 'No'}")
            
            else:
                print("❌ Unknown cache action. Use: refresh, clear, or info")
                return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
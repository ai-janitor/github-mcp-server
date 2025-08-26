"""
UNDERSTANDING: Shell completion functions for gh-projects-v2 CLI tool
DEPENDENCIES: os, argcomplete, manager module, completion_cache module
EXPORTS: Completion functions for item IDs, statuses, and workflows
INTEGRATION: Used by CLI argument parser with argcomplete for shell completion
"""

import os
from typing import List, Optional

from .manager import GitHubProjectsManager
from .completion_cache import CompletionCache


def get_env_or_none(var_name: str) -> Optional[str]:
    """Get environment variable value or None if not set."""
    value = os.getenv(var_name)
    return value if value else None


def item_id_completer(prefix, parsed_args, **kwargs) -> List[str]:
    """
    Complete project item IDs (PVTI_xxx format) with caching for performance.
    
    Uses cached item IDs when available to ensure fast completion response.
    Falls back to API call only if cache is empty/expired.
    """
    # Get project ID from environment or parsed args
    project_id = getattr(parsed_args, 'project_id', None) or get_env_or_none('GITHUB_PROJECT_ID')
    
    if not project_id:
        return []
    
    cache = CompletionCache()
    
    # Try to get cached item IDs first
    cached_items = cache.get_item_ids(project_id)
    if cached_items:
        # Filter by prefix for faster completion
        return [item_id for item_id in cached_items if item_id.startswith(prefix)]
    
    # Cache miss - try API call (but keep it fast with timeout)
    token = get_env_or_none('GITHUB_TOKEN')
    if not token:
        return []
    
    try:
        manager = GitHubProjectsManager(token)
        
        # Get only recent items for faster completion (limit to first 100)
        # This is a compromise between speed and completeness
        items = manager.list_project_items(project_id)[:100]  # Limit for speed
        
        # Extract item IDs
        item_ids = [item['id'] for item in items if 'id' in item]
        
        # Cache the results for future completions
        cache.set_item_ids(project_id, item_ids)
        
        # Return filtered results
        return [item_id for item_id in item_ids if item_id.startswith(prefix)]
        
    except Exception:
        # Silently fail completion to avoid breaking shell
        return []


def status_completer(prefix, parsed_args, **kwargs) -> List[str]:
    """
    Complete status names with caching for performance.
    
    Status names change rarely, so cache them with longer TTL.
    """
    # Get project ID from environment or parsed args
    project_id = getattr(parsed_args, 'project_id', None) or get_env_or_none('GITHUB_PROJECT_ID')
    
    if not project_id:
        return []
    
    cache = CompletionCache()
    
    # Try cached statuses first
    cached_statuses = cache.get_statuses(project_id)
    if cached_statuses:
        return [status for status in cached_statuses if status.lower().startswith(prefix.lower())]
    
    # Cache miss - get from API
    token = get_env_or_none('GITHUB_TOKEN')
    if not token:
        return []
    
    try:
        manager = GitHubProjectsManager(token)
        statuses = manager.get_available_statuses(project_id)
        
        # Cache the results
        cache.set_statuses(project_id, statuses)
        
        # Return filtered results (case insensitive)
        return [status for status in statuses if status.lower().startswith(prefix.lower())]
        
    except Exception:
        # Silently fail completion to avoid breaking shell
        return []


def workflow_completer(prefix, parsed_args, **kwargs) -> List[str]:
    """
    Complete workflow filenames with caching.
    
    Completes .yml/.yaml workflow files from the repository.
    """
    # Get owner/repo from environment or parsed args
    owner = getattr(parsed_args, 'owner', None) or get_env_or_none('GITHUB_OWNER')
    repo = getattr(parsed_args, 'repo', None) or get_env_or_none('GITHUB_REPO')
    
    if not owner or not repo:
        return []
    
    cache = CompletionCache()
    
    # Try cached workflows first
    cached_workflows = cache.get_workflows(owner, repo)
    if cached_workflows:
        return [wf for wf in cached_workflows if wf.startswith(prefix)]
    
    # Cache miss - get from API
    token = get_env_or_none('GITHUB_TOKEN')
    if not token:
        return []
    
    try:
        manager = GitHubProjectsManager(token)
        workflows = manager.list_workflows(owner, repo)
        
        # Extract just the filenames
        workflow_files = []
        for wf in workflows:
            if 'path' in wf:
                # Extract filename from path (e.g., ".github/workflows/build.yml" -> "build.yml")
                filename = wf['path'].split('/')[-1]
                workflow_files.append(filename)
        
        # Cache the results
        cache.set_workflows(owner, repo, workflow_files)
        
        # Return filtered results
        return [wf for wf in workflow_files if wf.startswith(prefix)]
        
    except Exception:
        # Silently fail completion to avoid breaking shell
        return []


def branch_completer(prefix, parsed_args, **kwargs) -> List[str]:
    """
    Complete git branch names.
    
    For now, return common branch names. Could be enhanced to call git API.
    """
    common_branches = [
        "main", "master", "development", "develop", "dev", 
        "staging", "stage", "production", "prod", "release"
    ]
    
    return [branch for branch in common_branches if branch.startswith(prefix)]


def issue_url_completer(prefix, parsed_args, **kwargs) -> List[str]:
    """
    Complete GitHub issue URLs based on current project context.
    
    Provides template URLs that users can modify.
    """
    owner = get_env_or_none('GITHUB_OWNER')
    repo = get_env_or_none('GITHUB_REPO')
    
    if owner and repo:
        return [f"https://github.com/{owner}/{repo}/issues/"]
    
    return ["https://github.com/owner/repo/issues/"]
"""
UNDERSTANDING: Caching system for shell completion data to ensure fast TAB responses
DEPENDENCIES: json, os, time for file operations and timestamps
EXPORTS: CompletionCache class for managing cached completion data
INTEGRATION: Used by CLI completers to avoid slow API calls during shell completion
"""

import json
import os
import time
from typing import Dict, List, Optional
from pathlib import Path


class CompletionCache:
    """
    Manages local caching for shell completion data to ensure fast responses.
    
    Caches item IDs, status names, and workflow files locally to avoid slow API calls
    during shell completion. Implements TTL-based expiration and background refresh.
    """
    
    def __init__(self, cache_dir: str = None):
        """
        Initialize completion cache with specified or default directory.
        
        Args:
            cache_dir: Optional custom cache directory path
        """
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Default to ~/.gh-projects-v2/cache/
            home = Path.home()
            self.cache_dir = home / '.gh-projects-v2' / 'cache'
        
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache TTL in seconds (default: 1 hour for fast data, 24 hours for slow data)
        self.ttl_fast = 3600    # 1 hour for statuses/workflows  
        self.ttl_slow = 86400   # 24 hours for item IDs
    
    def _get_cache_file(self, cache_key: str) -> Path:
        """Get cache file path for a given key."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_file: Path, ttl: int) -> bool:
        """Check if cache file exists and is still valid based on TTL."""
        if not cache_file.exists():
            return False
        
        file_mtime = cache_file.stat().st_mtime
        return (time.time() - file_mtime) < ttl
    
    def get_cached_data(self, cache_key: str, ttl: int = None) -> Optional[List[str]]:
        """
        Retrieve cached data if valid, otherwise return None.
        
        Args:
            cache_key: Unique key for the cached data
            ttl: Time-to-live in seconds (uses default if not specified)
            
        Returns:
            Cached data list if valid, None if expired or missing
        """
        if ttl is None:
            ttl = self.ttl_fast
            
        cache_file = self._get_cache_file(cache_key)
        
        if not self._is_cache_valid(cache_file, ttl):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('items', [])
        except (json.JSONDecodeError, IOError):
            # Cache file corrupted, remove it
            try:
                cache_file.unlink()
            except OSError:
                pass
            return None
    
    def set_cached_data(self, cache_key: str, items: List[str]) -> None:
        """
        Store data in cache with current timestamp.
        
        Args:
            cache_key: Unique key for the cached data
            items: List of strings to cache
        """
        cache_file = self._get_cache_file(cache_key)
        
        cache_data = {
            'timestamp': time.time(),
            'items': items
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except IOError as e:
            # Silently fail cache writes to avoid breaking completion
            pass
    
    def get_item_ids(self, project_id: str) -> Optional[List[str]]:
        """Get cached item IDs for a project."""
        cache_key = f"items_{project_id}"
        return self.get_cached_data(cache_key, self.ttl_slow)
    
    def set_item_ids(self, project_id: str, item_ids: List[str]) -> None:
        """Cache item IDs for a project."""
        cache_key = f"items_{project_id}"
        self.set_cached_data(cache_key, item_ids)
    
    def get_statuses(self, project_id: str) -> Optional[List[str]]:
        """Get cached status names for a project."""
        cache_key = f"statuses_{project_id}"
        return self.get_cached_data(cache_key, self.ttl_fast)
    
    def set_statuses(self, project_id: str, statuses: List[str]) -> None:
        """Cache status names for a project."""
        cache_key = f"statuses_{project_id}"
        self.set_cached_data(cache_key, statuses)
    
    def get_workflows(self, owner: str, repo: str) -> Optional[List[str]]:
        """Get cached workflow files for a repository."""
        cache_key = f"workflows_{owner}_{repo}"
        return self.get_cached_data(cache_key, self.ttl_fast)
    
    def set_workflows(self, owner: str, repo: str, workflows: List[str]) -> None:
        """Cache workflow files for a repository."""
        cache_key = f"workflows_{owner}_{repo}"
        self.set_cached_data(cache_key, workflows)
    
    def clear_cache(self, pattern: str = None) -> int:
        """
        Clear cache files matching optional pattern.
        
        Args:
            pattern: Optional pattern to match cache keys (None clears all)
            
        Returns:
            Number of cache files removed
        """
        removed_count = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            if pattern is None or pattern in cache_file.stem:
                try:
                    cache_file.unlink()
                    removed_count += 1
                except OSError:
                    pass
        
        return removed_count
    
    def get_cache_info(self) -> Dict[str, Dict]:
        """
        Get information about all cache files.
        
        Returns:
            Dictionary with cache file info including size and age
        """
        cache_info = {}
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                stat = cache_file.stat()
                cache_info[cache_file.stem] = {
                    'size_bytes': stat.st_size,
                    'modified_time': stat.st_mtime,
                    'age_seconds': time.time() - stat.st_mtime,
                    'valid_fast': self._is_cache_valid(cache_file, self.ttl_fast),
                    'valid_slow': self._is_cache_valid(cache_file, self.ttl_slow)
                }
            except OSError:
                continue
        
        return cache_info
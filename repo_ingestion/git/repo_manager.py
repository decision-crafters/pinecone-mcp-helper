"""
Git repository management module for the repository ingestion pipeline.

This module provides functionality to clone a new Git repository or update an existing one
based on the provided URL or local path.
"""

import logging
import os
import re
from typing import Optional

import git
from git import Repo, GitCommandError

# Configure logging
logger = logging.getLogger(__name__)


def extract_repo_name(repo_url: str) -> str:
    """
    Extract the repository name from a Git repository URL or local path.

    Args:
        repo_url: Git repository URL or local path.

    Returns:
        Repository name.

    Examples:
        >>> extract_repo_name("https://github.com/user/repo.git")
        'repo'
        >>> extract_repo_name("https://github.com/user/repo")
        'repo'
        >>> extract_repo_name("/path/to/repo")
        'repo'
    """
    # Handle local paths
    if os.path.exists(repo_url) and not repo_url.startswith(('http://', 'https://')):
        return os.path.basename(os.path.normpath(repo_url))
    
    # Handle URLs
    # Extract the repository name from the URL (remove .git extension if present)
    match = re.search(r'/([^/]+?)(?:\.git)?$', repo_url)
    if match:
        return match.group(1)
    
    # Fallback: use the last part of the URL
    parts = repo_url.rstrip('/').split('/')
    return parts[-1].replace('.git', '')


def is_git_repo(directory: str) -> bool:
    """
    Check if a directory is a valid Git repository.

    Args:
        directory: Path to the directory to check.

    Returns:
        True if the directory is a valid Git repository, False otherwise.
    """
    try:
        # Try to open the repository
        Repo(directory)
        return True
    except (git.NoSuchPathError, git.InvalidGitRepositoryError):
        return False


def clone_or_update_repo(repo_url: str, target_dir: Optional[str] = None) -> str:
    """
    Clone a new Git repository or update an existing one.

    Args:
        repo_url: Git repository URL or local path.
        target_dir: Target directory for the repository. If None, a directory
                    with the repository name will be created in the current directory.

    Returns:
        Path to the repository.

    Raises:
        git.GitCommandError: If a Git command fails.
        ValueError: If the repository URL is invalid or the target directory is not a Git repository.
    """
    # Extract repository name if target_dir is not provided
    if target_dir is None:
        repo_name = extract_repo_name(repo_url)
        target_dir = os.path.join(os.getcwd(), repo_name)
    
    logger.info(f"Repository target directory: {target_dir}")
    
    # Check if the target directory exists
    if os.path.exists(target_dir):
        # Check if it's a Git repository
        if is_git_repo(target_dir):
            logger.info(f"Updating existing repository at {target_dir}")
            try:
                repo = Repo(target_dir)
                
                # Check if the remote URL matches
                if repo_url.startswith(('http://', 'https://')):
                    # For remote URLs, check if the remote URL matches
                    remotes = list(repo.remotes)
                    if remotes:
                        origin_url = remotes[0].url
                        if origin_url != repo_url and origin_url != repo_url + '.git':
                            logger.warning(f"Remote URL mismatch: {origin_url} != {repo_url}")
                            # Continue anyway, as we'll just pull from the existing remote
                
                # Pull the latest changes
                logger.info("Pulling latest changes")
                try:
                    # Check if the repository has remotes
                    if len(repo.remotes) > 0:
                        origin = repo.remotes.origin
                        origin.pull()
                    else:
                        logger.info("Repository has no remotes, skipping pull")
                except Exception as e:
                    logger.warning(f"Error during pull, continuing anyway: {e}")
                
                return target_dir
            except GitCommandError as e:
                logger.error(f"Error updating repository: {e}")
                raise
        else:
            # Directory exists but is not a Git repository
            error_msg = f"Directory {target_dir} exists but is not a Git repository"
            logger.error(error_msg)
            raise ValueError(error_msg)
    else:
        # Directory doesn't exist, clone the repository
        logger.info(f"Cloning repository from {repo_url} to {target_dir}")
        try:
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(target_dir), exist_ok=True)
            
            # Clone the repository
            Repo.clone_from(repo_url, target_dir)
            
            return target_dir
        except GitCommandError as e:
            logger.error(f"Error cloning repository: {e}")
            raise

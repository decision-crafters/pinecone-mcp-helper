"""
Unit tests for the Git repository management module.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from git import Repo, GitCommandError

from repo_ingestion.git.repo_manager import (
    extract_repo_name, is_git_repo, clone_or_update_repo
)


class TestRepoManager(unittest.TestCase):
    """Test cases for the Git repository management module."""

    def test_extract_repo_name_from_url(self):
        """Test extracting repository name from a URL."""
        # Test with .git extension
        self.assertEqual(extract_repo_name("https://github.com/user/repo.git"), "repo")
        
        # Test without .git extension
        self.assertEqual(extract_repo_name("https://github.com/user/repo"), "repo")
        
        # Test with trailing slash
        self.assertEqual(extract_repo_name("https://github.com/user/repo/"), "repo")
        
        # Test with complex URL
        self.assertEqual(extract_repo_name("https://github.com/org/project-name.git"), "project-name")

    def test_extract_repo_name_from_path(self):
        """Test extracting repository name from a local path."""
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertEqual(extract_repo_name(temp_dir), os.path.basename(temp_dir))

    def test_is_git_repo(self):
        """Test checking if a directory is a Git repository."""
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Not a Git repository
            self.assertFalse(is_git_repo(temp_dir))
            
            # Initialize Git repository
            Repo.init(temp_dir)
            
            # Now it should be a Git repository
            self.assertTrue(is_git_repo(temp_dir))

    @patch('repo_ingestion.git.repo_manager.Repo')
    def test_clone_or_update_repo_new(self, mock_repo):
        """Test cloning a new repository."""
        # Mock Repo.clone_from
        mock_repo.clone_from.return_value = MagicMock()
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up test parameters
            repo_url = "https://github.com/user/repo.git"
            target_dir = os.path.join(temp_dir, "repo")
            
            # Call function
            result = clone_or_update_repo(repo_url, target_dir)
            
            # Verify result
            self.assertEqual(result, target_dir)
            
            # Verify Repo.clone_from was called
            mock_repo.clone_from.assert_called_once_with(repo_url, target_dir)

    @patch('repo_ingestion.git.repo_manager.Repo')
    @patch('repo_ingestion.git.repo_manager.is_git_repo')
    def test_clone_or_update_repo_existing(self, mock_is_git_repo, mock_repo):
        """Test updating an existing repository."""
        # Mock is_git_repo
        mock_is_git_repo.return_value = True
        
        # Mock Repo
        mock_repo_instance = MagicMock()
        mock_repo_instance.remotes.origin.pull.return_value = None
        mock_repo.return_value = mock_repo_instance
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create target directory
            target_dir = os.path.join(temp_dir, "repo")
            os.makedirs(target_dir)
            
            # Set up test parameters
            repo_url = "https://github.com/user/repo.git"
            
            # Call function
            result = clone_or_update_repo(repo_url, target_dir)
            
            # Verify result
            self.assertEqual(result, target_dir)
            
            # Verify Repo was called
            mock_repo.assert_called_once_with(target_dir)
            
            # Verify pull was called
            mock_repo_instance.remotes.origin.pull.assert_called_once()

    @patch('repo_ingestion.git.repo_manager.is_git_repo')
    def test_clone_or_update_repo_existing_not_git(self, mock_is_git_repo):
        """Test handling a directory that exists but is not a Git repository."""
        # Mock is_git_repo
        mock_is_git_repo.return_value = False
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create target directory
            target_dir = os.path.join(temp_dir, "repo")
            os.makedirs(target_dir)
            
            # Set up test parameters
            repo_url = "https://github.com/user/repo.git"
            
            # Call function and expect ValueError
            with self.assertRaises(ValueError):
                clone_or_update_repo(repo_url, target_dir)

    @patch('repo_ingestion.git.repo_manager.Repo')
    def test_clone_or_update_repo_error(self, mock_repo):
        """Test handling errors during Git operations."""
        # Mock Repo.clone_from to raise GitCommandError
        mock_repo.clone_from.side_effect = GitCommandError("git clone", 128)
        
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up test parameters
            repo_url = "https://github.com/user/repo.git"
            target_dir = os.path.join(temp_dir, "repo")
            
            # Call function and expect GitCommandError
            with self.assertRaises(GitCommandError):
                clone_or_update_repo(repo_url, target_dir)


if __name__ == "__main__":
    unittest.main()

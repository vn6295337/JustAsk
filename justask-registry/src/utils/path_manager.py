#!/usr/bin/env python3
"""
Groq Pipeline Path Manager
=========================

Centralized path management for the Groq pipeline following
OpenRouter/Google pipeline patterns.

Features:
- Consistent relative path handling
- Directory validation and creation
- File path resolution for configs, outputs, scripts
- Cross-platform path compatibility
- Automatic directory structure maintenance

Author: AI Models Discovery Pipeline
Version: 1.0
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


class GroqPaths:
    """Centralized path management for Groq pipeline"""

    def __init__(self):
        """Initialize path manager with base directory structure"""
        # Project root is 3 levels up from src/utils/path_manager.py
        self.project_root = Path(__file__).parent.parent.parent

        # Define standard directory structure (new locations)
        self.configs_dir = self.project_root / "config" / "groq"
        self.outputs_dir = self.project_root / "outputs" / "groq"

        # Scripts and utils are now in src/pipelines/groq/
        self.scripts_dir = self.project_root / "src" / "pipelines" / "groq" / "steps"
        self.utils_dir = self.project_root / "src" / "utils"

        # Ensure all directories exist
        self._ensure_directory_structure()

    def _ensure_directory_structure(self):
        """Ensure all required directories exist"""
        directories = [
            self.outputs_dir,
            self.configs_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_config_path(self, filename: str) -> Path:
        """
        Get path to configuration file in 03_configs/

        Args:
            filename: Config filename (with or without .json extension)

        Returns:
            Path to configuration file
        """
        # Add .json extension if not present
        if not filename.endswith('.json'):
            filename += '.json'

        return self.configs_dir / filename

    def get_output_path(self, filename: str) -> Path:
        """
        Get path to output file in 02_outputs/

        Args:
            filename: Output filename

        Returns:
            Path to output file
        """
        return self.outputs_dir / filename

    def get_script_path(self, filename: str) -> Path:
        """
        Get path to script file in 01_scripts/

        Args:
            filename: Script filename (with or without .py extension)

        Returns:
            Path to script file
        """
        # Add .py extension if not present
        if not filename.endswith('.py'):
            filename += '.py'

        return self.scripts_dir / filename

    def get_utils_path(self, filename: str) -> Path:
        """
        Get path to utility file in 04_utils/

        Args:
            filename: Utility filename (with or without .py extension)

        Returns:
            Path to utility file
        """
        # Add .py extension if not present
        if not filename.endswith('.py'):
            filename += '.py'

        return self.utils_dir / filename

    def get_relative_path(self, target_path: Path, from_dir: Optional[Path] = None) -> str:
        """
        Get relative path from one directory to another

        Args:
            target_path: Target file/directory path
            from_dir: Source directory (defaults to scripts directory)

        Returns:
            Relative path string
        """
        if from_dir is None:
            from_dir = self.scripts_dir

        try:
            relative = os.path.relpath(target_path, from_dir)
            return relative
        except ValueError:
            # Fallback to absolute path if relative calculation fails
            return str(target_path)

    def ensure_output_dir_exists(self):
        """Ensure outputs directory exists and is writable"""
        self.outputs_dir.mkdir(exist_ok=True)

        # Test write permissions
        test_file = self.outputs_dir / ".test_write"
        try:
            test_file.write_text("test")
            test_file.unlink()
            print(f"✓ Output directory ready: {self.outputs_dir}")
        except PermissionError:
            print(f"❌ No write permission to: {self.outputs_dir}")
            raise

    def clean_output_directory(self, confirm: bool = False):
        """
        Clean the outputs directory

        Args:
            confirm: If True, skip confirmation prompt
        """
        if not confirm:
            response = input(f"Clean output directory {self.outputs_dir}? [y/N]: ")
            if response.lower() != 'y':
                print("Output directory cleaning cancelled")
                return

        if self.outputs_dir.exists():
            print(f"🧹 Cleaning output directory: {self.outputs_dir}")

            # Remove all files and subdirectories
            for item in self.outputs_dir.iterdir():
                if item.is_file():
                    item.unlink()
                    print(f"   Removed file: {item.name}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    print(f"   Removed directory: {item.name}")

        # Ensure directory exists (recreate if it was deleted)
        self.outputs_dir.mkdir(exist_ok=True)
        print("✓ Output directory cleaned and ready")

    def list_output_files(self, pattern: str = "*") -> List[Path]:
        """
        List files in output directory

        Args:
            pattern: Glob pattern for file matching

        Returns:
            List of matching file paths
        """
        return list(self.outputs_dir.glob(pattern))

    def list_config_files(self) -> List[Path]:
        """
        List all configuration files

        Returns:
            List of configuration file paths
        """
        return list(self.configs_dir.glob("*.json"))

    def list_script_files(self) -> List[Path]:
        """
        List all script files

        Returns:
            List of script file paths
        """
        return list(self.scripts_dir.glob("*.py"))

    def get_timestamped_filename(self, base_name: str, extension: str = "") -> str:
        """
        Generate filename with timestamp

        Args:
            base_name: Base filename without extension
            extension: File extension (with or without leading dot)

        Returns:
            Timestamped filename
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Ensure extension has leading dot
        if extension and not extension.startswith('.'):
            extension = '.' + extension

        return f"{base_name}-{timestamp}{extension}"

    def archive_output_file(self, filename: str) -> Optional[Path]:
        """
        Archive an output file by adding timestamp

        Args:
            filename: Output filename to archive

        Returns:
            Path to archived file or None if original doesn't exist
        """
        original_path = self.get_output_path(filename)

        if not original_path.exists():
            print(f"⚠️ File not found for archiving: {original_path}")
            return None

        # Generate archived filename
        stem = original_path.stem
        suffix = original_path.suffix
        archived_name = self.get_timestamped_filename(stem + "-archived", suffix)
        archived_path = self.get_output_path(archived_name)

        # Move file to archived location
        shutil.move(str(original_path), str(archived_path))
        print(f"📦 Archived: {filename} → {archived_name}")

        return archived_path

    def validate_file_path(self, file_path: Path) -> bool:
        """
        Validate that a file path exists and is readable

        Args:
            file_path: Path to validate

        Returns:
            True if file exists and is readable
        """
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            return False

        if not file_path.is_file():
            print(f"❌ Path is not a file: {file_path}")
            return False

        try:
            # Test read permissions
            with open(file_path, 'r') as f:
                f.read(1)
            return True
        except PermissionError:
            print(f"❌ No read permission: {file_path}")
            return False
        except Exception as e:
            print(f"❌ Error accessing file {file_path}: {e}")
            return False

    def get_directory_info(self) -> Dict[str, Any]:
        """
        Get information about the directory structure

        Returns:
            Dictionary with directory information
        """
        def get_dir_stats(directory: Path) -> Dict[str, Any]:
            if not directory.exists():
                return {"exists": False, "file_count": 0, "size": 0}

            files = list(directory.glob("*"))
            file_count = len([f for f in files if f.is_file()])
            dir_count = len([f for f in files if f.is_dir()])

            # Calculate total size
            total_size = 0
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, PermissionError):
                        pass

            return {
                "exists": True,
                "file_count": file_count,
                "dir_count": dir_count,
                "total_size": total_size,
                "path": str(directory)
            }

        return {
            "project_root": str(self.project_root),
            "scripts": get_dir_stats(self.scripts_dir),
            "outputs": get_dir_stats(self.outputs_dir),
            "configs": get_dir_stats(self.configs_dir),
            "utils": get_dir_stats(self.utils_dir)
        }

    def find_files_by_pattern(self, pattern: str, directory: Optional[str] = None) -> List[Path]:
        """
        Find files matching a pattern in specified directory

        Args:
            pattern: Glob pattern to match
            directory: Directory to search ('scripts', 'outputs', 'configs', 'utils')
                      If None, searches all directories

        Returns:
            List of matching file paths
        """
        if directory:
            search_dirs = {
                'scripts': [self.scripts_dir],
                'outputs': [self.outputs_dir],
                'configs': [self.configs_dir],
                'utils': [self.utils_dir]
            }
            dirs_to_search = search_dirs.get(directory.lower(), [])
        else:
            dirs_to_search = [self.scripts_dir, self.outputs_dir, self.configs_dir, self.utils_dir]

        found_files = []
        for search_dir in dirs_to_search:
            if search_dir.exists():
                found_files.extend(search_dir.glob(pattern))

        return found_files


# Global path manager instance
groq_paths = GroqPaths()


def get_paths() -> GroqPaths:
    """
    Get global path manager instance

    Returns:
        Global GroqPaths instance
    """
    return groq_paths


# Convenience functions for common path operations
def get_config_path(filename: str) -> Path:
    """Get path to configuration file"""
    return groq_paths.get_config_path(filename)


def get_output_path(filename: str) -> Path:
    """Get path to output file"""
    return groq_paths.get_output_path(filename)


def get_script_path(filename: str) -> Path:
    """Get path to script file"""
    return groq_paths.get_script_path(filename)


def ensure_output_dir_exists():
    """Ensure output directory exists"""
    groq_paths.ensure_output_dir_exists()


def list_output_files(pattern: str = "*") -> List[Path]:
    """List files in output directory"""
    return groq_paths.list_output_files(pattern)


if __name__ == "__main__":
    # Test path management
    path_manager = GroqPaths()

    print("=== Groq Path Manager Test ===")
    print(f"Project root: {path_manager.project_root}")

    print("\nDirectory Information:")
    dir_info = path_manager.get_directory_info()
    for name, info in dir_info.items():
        if name != "base_path":
            print(f"  {name}: {info}")

    print("\nTesting path operations...")

    # Test config path
    config_path = path_manager.get_config_path("01_groq_api_endpoints")
    print(f"Config path: {config_path}")
    print(f"Config exists: {config_path.exists()}")

    # Test output path
    output_path = path_manager.get_output_path("test.json")
    print(f"Output path: {output_path}")

    # Test relative paths
    relative = path_manager.get_relative_path(config_path)
    print(f"Relative config path: {relative}")

    # List configuration files
    config_files = path_manager.list_config_files()
    print(f"Config files found: {len(config_files)}")

    print("\n✓ Path manager test completed")
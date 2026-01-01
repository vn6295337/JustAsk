#!/usr/bin/env python3
"""
Output utilities for JustAsk Registry pipelines.
Provides centralized output directory management and cleanup functions.

Supports both new structure (outputs/) and legacy structure (*_pipeline/02_outputs/).
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone, timedelta


# Current pipeline context (set by runner)
_current_pipeline: Optional[str] = None


def set_current_pipeline(pipeline: str):
    """Set the current pipeline context for output path resolution."""
    global _current_pipeline
    _current_pipeline = pipeline


def get_current_pipeline() -> Optional[str]:
    """Get the current pipeline context."""
    return _current_pipeline


def get_project_root() -> Path:
    """Get the project root directory (justask-registry)."""
    # Navigate from src/utils to project root
    return Path(__file__).parent.parent.parent


def get_output_dir(pipeline: Optional[str] = None) -> str:
    """
    Get the absolute path to the outputs directory for a pipeline.

    Args:
        pipeline: Pipeline name ('google', 'groq', 'openrouter').
                 If None, uses current pipeline context or returns base outputs dir.

    Returns:
        Path to outputs directory
    """
    pipeline = pipeline or _current_pipeline
    project_root = get_project_root()

    if pipeline:
        output_dir = project_root / "outputs" / pipeline
    else:
        output_dir = project_root / "outputs"

    return str(output_dir.resolve())


def get_output_file_path(filename: str) -> str:
    """
    Get the full path for an output file

    Args:
        filename: Name of the output file

    Returns:
        Full path to the output file
    """
    output_dir = Path(get_output_dir())
    return str(output_dir / filename)


def get_input_file_path(filename: str) -> str:
    """
    Get the full path for an input file from previous pipeline stages.
    Input files are read from the same outputs directory.

    Args:
        filename: Name of the input file

    Returns:
        Full path to the input file in outputs directory
    """
    return get_output_file_path(filename)


def ensure_output_directory():
    """
    Ensure the outputs directory exists.
    Creates it if it doesn't exist.
    """
    output_dir = Path(get_output_dir())
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output directory ensured: {output_dir}")


# Alias for backward compatibility with openrouter scripts
ensure_output_dir_exists = ensure_output_directory


def clean_output_directory():
    """
    Clean the 02_outputs directory by removing all files
    Keeps the directory structure but removes all contents
    """
    output_dir = Path(get_output_dir())

    if output_dir.exists():
        print(f"🧹 Cleaning output directory: {output_dir}")
        # Remove all files and subdirectories except .gitkeep
        for item in output_dir.iterdir():
            if item.name == '.gitkeep':
                continue  # Keep .gitkeep file

            if item.is_file():
                item.unlink()
                print(f"   Removed file: {item.name}")
            elif item.is_dir():
                shutil.rmtree(item)
                print(f"   Removed directory: {item.name}")

    # Ensure the directory exists (recreate if it was deleted)
    output_dir.mkdir(exist_ok=True)
    print(f"✅ Output directory cleaned and ready")


def get_ist_timestamp() -> str:
    """
    Get current timestamp in IST (Indian Standard Time) in readable format

    Returns:
        Formatted timestamp string in IST
    """
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist_tz)
    return now_ist.strftime('%Y-%m-%d %H:%M:%S IST')

"""
Configuration module for AI Models Discoverer pipelines.

Provides centralized configuration loading for all pipelines.

Directory structure:
    config/
    ├── google/           # Google pipeline configs
    ├── groq/             # Groq pipeline configs
    └── openrouter/       # OpenRouter pipeline configs
"""

import json
from pathlib import Path
from typing import Any, Dict


def get_config_dir() -> Path:
    """Get the root config directory."""
    return Path(__file__).parent


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load a JSON configuration file.

    Args:
        config_path: Path relative to config directory (e.g., 'google/licenses.json')

    Returns:
        Parsed JSON as dictionary
    """
    full_path = get_config_dir() / config_path
    with open(full_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_pipeline_config(pipeline: str, name: str) -> Dict[str, Any]:
    """
    Load a pipeline-specific configuration file.

    Args:
        pipeline: Pipeline name ('google', 'groq', 'openrouter')
        name: Config name without extension (e.g., 'licenses')

    Returns:
        Parsed JSON as dictionary
    """
    return load_config(f'{pipeline}/{name}.json')


__all__ = [
    'get_config_dir',
    'load_config',
    'load_pipeline_config',
]

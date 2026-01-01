"""
AI Models Discoverer Pipelines.

This module contains pipelines for discovering AI model metadata from various providers:
- google: Google AI Models
- groq: Groq Models
- openrouter: OpenRouter Models (aggregates multiple providers)

Each pipeline follows a standard structure:
    pipelines/{provider}/
    ├── __init__.py
    ├── runner.py          # Pipeline orchestrator
    └── steps/
        ├── __init__.py
        ├── step_01_*.py   # First step
        ├── step_02_*.py   # Second step
        └── ...

Usage:
    from src.pipelines.google.runner import GooglePipelineRunner
    from src.pipelines.groq.runner import GroqPipelineRunner
    from src.pipelines.openrouter.runner import OpenRouterPipelineRunner

    # Run a specific pipeline
    runner = GooglePipelineRunner()
    runner.run(steps='1-6')
"""

__all__ = [
    'google',
    'groq',
    'openrouter',
]

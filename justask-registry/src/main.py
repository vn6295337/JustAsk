#!/usr/bin/env python3
"""
AI Models Discoverer - Unified CLI Entry Point.

This script provides a unified interface for running all discovery pipelines.

Usage:
    python -m src.main google --steps 1-6
    python -m src.main groq --steps 1-7
    python -m src.main openrouter --steps 1-19
    python -m src.main all --parallel

Examples:
    # Run Google pipeline (default steps 1-6)
    python -m src.main google

    # Run specific steps
    python -m src.main openrouter --steps 1-5,7

    # Dry run (show what would be executed)
    python -m src.main groq --dry-run

    # Run all pipelines sequentially
    python -m src.main all
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Type

from src.pipelines.base import BasePipelineRunner


# Lazy imports to avoid circular dependencies
def get_google_runner():
    from src.pipelines.google.runner import GooglePipelineRunner
    return GooglePipelineRunner


def get_groq_runner():
    from src.pipelines.groq.runner import GroqPipelineRunner
    return GroqPipelineRunner


def get_openrouter_runner():
    from src.pipelines.openrouter.runner import OpenRouterPipelineRunner
    return OpenRouterPipelineRunner


PIPELINE_RUNNERS = {
    'google': get_google_runner,
    'groq': get_groq_runner,
    'openrouter': get_openrouter_runner,
}


def run_pipeline(pipeline: str, steps: str = None, dry_run: bool = False, clean: bool = True) -> bool:
    """
    Run a single pipeline.

    Args:
        pipeline: Pipeline name ('google', 'groq', 'openrouter')
        steps: Step specification (e.g., '1-6')
        dry_run: If True, only print what would be executed
        clean: If True, clean output directory before running

    Returns:
        True if pipeline succeeded
    """
    if pipeline not in PIPELINE_RUNNERS:
        print(f"Unknown pipeline: {pipeline}")
        print(f"Available pipelines: {', '.join(PIPELINE_RUNNERS.keys())}")
        return False

    runner_class = PIPELINE_RUNNERS[pipeline]()
    runner = runner_class()
    return runner.run(steps=steps, dry_run=dry_run, clean=clean)


def run_all_pipelines(steps: Dict[str, str] = None, parallel: bool = False, dry_run: bool = False) -> bool:
    """
    Run all pipelines.

    Args:
        steps: Dict of pipeline name to step specification
        parallel: If True, run pipelines in parallel
        dry_run: If True, only print what would be executed

    Returns:
        True if all pipelines succeeded
    """
    steps = steps or {}

    if parallel:
        print("Running pipelines in parallel...")
        results = {}

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    run_pipeline,
                    pipeline,
                    steps.get(pipeline),
                    dry_run
                ): pipeline
                for pipeline in PIPELINE_RUNNERS
            }

            for future in as_completed(futures):
                pipeline = futures[future]
                try:
                    results[pipeline] = future.result()
                except Exception as e:
                    print(f"Pipeline {pipeline} failed with exception: {e}")
                    results[pipeline] = False

        return all(results.values())

    else:
        print("Running pipelines sequentially...")
        all_success = True

        for pipeline in PIPELINE_RUNNERS:
            success = run_pipeline(pipeline, steps.get(pipeline), dry_run)
            if not success:
                all_success = False
                print(f"\n⚠️  Pipeline {pipeline} failed. Continuing with next pipeline...")

        return all_success


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AI Models Discoverer Pipeline CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m src.main google                    # Run Google pipeline (default steps)
    python -m src.main groq --steps 1-7          # Run Groq pipeline steps 1-7
    python -m src.main openrouter --steps 1,3,5  # Run specific steps
    python -m src.main all                       # Run all pipelines sequentially
    python -m src.main all --parallel            # Run all pipelines in parallel
    python -m src.main google --dry-run          # Preview without executing
        """
    )

    parser.add_argument(
        'pipeline',
        choices=['google', 'groq', 'openrouter', 'all'],
        help='Pipeline to run (or "all" for all pipelines)'
    )

    parser.add_argument(
        '--steps',
        type=str,
        default=None,
        help='Step range to run (e.g., "1-6", "1,3,5", "1-3,5"). Defaults to pipeline default.'
    )

    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run all pipelines in parallel (only used with "all")'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be executed without running'
    )

    parser.add_argument(
        '--no-clean',
        action='store_true',
        help='Skip cleaning output directory before running'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 3.0.0'
    )

    args = parser.parse_args()

    if args.pipeline == 'all':
        steps_dict = {}
        if args.steps:
            # Apply same steps to all pipelines
            for pipeline in PIPELINE_RUNNERS:
                steps_dict[pipeline] = args.steps

        success = run_all_pipelines(
            steps=steps_dict,
            parallel=args.parallel,
            dry_run=args.dry_run
        )
    else:
        success = run_pipeline(
            pipeline=args.pipeline,
            steps=args.steps,
            dry_run=args.dry_run,
            clean=not args.no_clean
        )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

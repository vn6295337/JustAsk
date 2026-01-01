"""
Base Pipeline class for AI Models Discoverer.

Provides common functionality for all pipeline runners including:
- Step execution and ordering
- Output directory management
- Logging and reporting
"""

import os
import sys
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

from src.utils.output import (
    set_current_pipeline,
    get_output_dir,
    ensure_output_directory,
    clean_output_directory,
    get_ist_timestamp,
)


class BasePipelineRunner(ABC):
    """Abstract base class for pipeline runners."""

    def __init__(self, pipeline_name: str):
        """
        Initialize the pipeline runner.

        Args:
            pipeline_name: Name of the pipeline ('google', 'groq', 'openrouter')
        """
        self.pipeline_name = pipeline_name
        self.project_root = Path(__file__).parent.parent.parent
        self.steps_dir = Path(__file__).parent / pipeline_name / 'steps'
        set_current_pipeline(pipeline_name)

    @property
    @abstractmethod
    def step_mapping(self) -> dict:
        """
        Return mapping of step numbers to step file names (new structure).

        Example:
            {
                1: 'step_01_fetch.py',
                2: 'step_02_filter.py',
                ...
            }
        """
        pass

    @property
    @abstractmethod
    def default_steps(self) -> str:
        """Return default step range to run (e.g., '1-6')."""
        pass

    def parse_steps(self, steps: Optional[str] = None) -> List[int]:
        """
        Parse step specification into list of step numbers.

        Args:
            steps: Step specification (e.g., '1-6', '1,3,5', '1-3,5')

        Returns:
            List of step numbers to execute
        """
        if steps is None:
            steps = self.default_steps

        result = []
        for part in steps.split(','):
            part = part.strip()
            if '-' in part:
                start, end = part.split('-')
                result.extend(range(int(start), int(end) + 1))
            else:
                result.append(int(part))

        return sorted(set(result))

    def run_step(self, step_num: int) -> Tuple[bool, str]:
        """
        Execute a single pipeline step.

        Uses new step files from src/pipelines/*/steps/.

        Args:
            step_num: Step number to execute

        Returns:
            Tuple of (success, output/error message)
        """
        if step_num not in self.step_mapping:
            return False, f"Step {step_num} not found in mapping"

        # Use new step files from src/pipelines/*/steps/
        step_script = self.steps_dir / self.step_mapping[step_num]

        if not step_script.exists():
            return False, f"Script not found: {step_script}"

        print(f"\n{'='*60}")
        print(f"Running Step {step_num}: {self.step_mapping[step_num]}")
        print(f"{'='*60}")

        try:
            result = subprocess.run(
                [sys.executable, str(step_script)],
                capture_output=True,
                text=True,
                cwd=str(self.project_root),  # Run from project root for proper imports
                env={**os.environ},  # Pass environment variables
                timeout=900,  # 15 minute timeout
            )

            if result.returncode == 0:
                print(result.stdout)
                return True, result.stdout
            else:
                print(f"STDERR: {result.stderr}")
                print(f"STDOUT: {result.stdout}")
                return False, result.stderr or result.stdout

        except subprocess.TimeoutExpired:
            return False, "Step timed out after 15 minutes"
        except Exception as e:
            return False, str(e)

    def run(self, steps: Optional[str] = None, dry_run: bool = False, clean: bool = True) -> bool:
        """
        Execute the pipeline.

        Args:
            steps: Step specification (e.g., '1-6')
            dry_run: If True, only print what would be executed
            clean: If True, clean output directory before running

        Returns:
            True if all steps succeeded
        """
        step_list = self.parse_steps(steps)

        print(f"\n{'#'*60}")
        print(f"# {self.pipeline_name.upper()} PIPELINE")
        print(f"# Started: {get_ist_timestamp()}")
        print(f"# Steps: {step_list}")
        print(f"{'#'*60}")

        if dry_run:
            print("\n[DRY RUN] Would execute:")
            for step_num in step_list:
                step_name = self.step_mapping.get(step_num, 'UNKNOWN')
                print(f"  - Step {step_num}: {step_name}")
            return True

        # Clean output directory if requested and running from step 1
        if clean and 1 in step_list:
            clean_output_directory()
        else:
            ensure_output_directory()

        # Execute steps
        results = []
        for step_num in step_list:
            success, message = self.run_step(step_num)
            results.append((step_num, success, message))

            if not success:
                print(f"\n❌ Step {step_num} FAILED")
                print(f"Error: {message}")
                break

        # Print summary
        print(f"\n{'#'*60}")
        print(f"# PIPELINE SUMMARY")
        print(f"# Finished: {get_ist_timestamp()}")
        print(f"{'#'*60}")

        for step_num, success, _ in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"  Step {step_num}: {status}")

        all_passed = all(success for _, success, _ in results)

        if all_passed:
            print(f"\n✅ All {len(results)} steps completed successfully!")
        else:
            print(f"\n❌ Pipeline failed at step {results[-1][0]}")

        return all_passed

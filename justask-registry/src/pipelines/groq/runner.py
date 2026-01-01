#!/usr/bin/env python3
"""
Groq Pipeline Runner.

Executes the Groq AI models discovery pipeline.

Pipeline Flow: step_01 → step_02 → ... → step_07
Deploy Flow (manual): step_08 → step_09

Usage:
    from src.pipelines.groq.runner import GroqPipelineRunner
    runner = GroqPipelineRunner()
    runner.run(steps='1-7')
"""

import sys
import os
import argparse

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.pipelines.base import BasePipelineRunner


class GroqPipelineRunner(BasePipelineRunner):
    """Runner for the Groq AI Models discovery pipeline."""

    def __init__(self):
        super().__init__('groq')

    @property
    def step_mapping(self) -> dict:
        """Map step numbers to new file names."""
        return {
            1: 'step_01_scrape_models.py',
            2: 'step_02_scrape_modalities.py',
            3: 'step_03_extract_meta_licenses.py',
            4: 'step_04_extract_opensource_licenses.py',
            5: 'step_05_consolidate_licenses.py',
            6: 'step_06_normalize_data.py',
            7: 'step_07_compare_supabase.py',
            8: 'step_08_refresh_working.py',
            9: 'step_09_deploy_main.py',
        }

    @property
    def default_steps(self) -> str:
        """Default steps to run (excluding manual deploy steps 8-9)."""
        return '1-7'

    # Legacy letter to step number mapping for backward compatibility
    LEGACY_MAPPING = {
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8, 'I': 9
    }

    def parse_legacy_scripts(self, scripts: list) -> str:
        """Convert legacy letter-based script selection to step numbers."""
        step_nums = []
        for script in scripts:
            letter = script.upper()
            if letter in self.LEGACY_MAPPING:
                step_nums.append(str(self.LEGACY_MAPPING[letter]))
            else:
                raise ValueError(f"Invalid script letter: {letter}")
        return ','.join(step_nums)

    def parse_legacy_range(self, start: str, end: str) -> str:
        """Convert legacy letter range to step range."""
        start_num = self.LEGACY_MAPPING.get(start.upper())
        end_num = self.LEGACY_MAPPING.get(end.upper())
        if start_num is None or end_num is None:
            raise ValueError(f"Invalid range: {start} to {end}")
        return f'{start_num}-{end_num}'


def parse_arguments():
    """Parse command-line arguments with legacy support."""
    parser = argparse.ArgumentParser(
        description="Groq Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (new style):
  python -m src.pipelines.groq.runner                   # Run default steps 1-7
  python -m src.pipelines.groq.runner --steps 1-7       # Run steps 1 through 7
  python -m src.pipelines.groq.runner --steps 1,3,5     # Run specific steps
  python -m src.pipelines.groq.runner --dry-run         # Preview execution

Examples (legacy style - for backward compatibility):
  python runner.py --auto-all                           # Run all scripts A to G
  python runner.py --scripts A B C                      # Run specific scripts
  python runner.py --range C E                          # Run script range C to E
        """
    )

    # New style arguments
    parser.add_argument(
        '--steps', type=str, default=None,
        help='Step range to run (e.g., "1-7", "1,3,5")'
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Preview what would be executed without running'
    )
    parser.add_argument(
        '--no-clean', action='store_true',
        help='Skip cleaning output directory before running'
    )

    # Legacy arguments for backward compatibility
    parser.add_argument(
        '--auto-all', action='store_true',
        help='[Legacy] Run all scripts (A to G)'
    )
    parser.add_argument(
        '--scripts', nargs='+', metavar='SCRIPT',
        help='[Legacy] Run specific scripts by letter (e.g., --scripts A B C)'
    )
    parser.add_argument(
        '--range', nargs=2, metavar=('START', 'END'),
        help='[Legacy] Run script range by letter (e.g., --range C E)'
    )

    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_arguments()
    runner = GroqPipelineRunner()

    # Determine steps to run
    steps = args.steps

    # Handle legacy arguments
    if args.auto_all:
        steps = '1-7'
    elif args.scripts:
        steps = runner.parse_legacy_scripts(args.scripts)
    elif args.range:
        steps = runner.parse_legacy_range(args.range[0], args.range[1])

    # Run the pipeline
    success = runner.run(
        steps=steps,
        dry_run=args.dry_run,
        clean=not args.no_clean
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Pipeline crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

#!/usr/bin/env python3
"""
OpenRouter Pipeline Runner.

Executes the OpenRouter AI models discovery pipeline.

Pipeline Flow: step_01 → step_02 → ... → step_19
Deploy Flow (manual): step_20 → step_21

Usage:
    from src.pipelines.openrouter.runner import OpenRouterPipelineRunner
    runner = OpenRouterPipelineRunner()
    runner.run(steps='1-19')
"""

import sys
import os
import argparse

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.pipelines.base import BasePipelineRunner


class OpenRouterPipelineRunner(BasePipelineRunner):
    """Runner for the OpenRouter AI Models discovery pipeline."""

    def __init__(self):
        super().__init__('openrouter')

    @property
    def step_mapping(self) -> dict:
        """Map step numbers to new file names."""
        return {
            1: 'step_01_fetch.py',
            2: 'step_02_filter.py',
            3: 'step_03_extract_google_licenses.py',
            4: 'step_04_extract_meta_licenses.py',
            5: 'step_05_fetch_hf_license_urls.py',
            6: 'step_06_fetch_hf_license_names.py',
            7: 'step_07_standardize_license_names.py',
            8: 'step_08_bucketize_licenses.py',
            9: 'step_09_opensource_license_urls.py',
            10: 'step_10_custom_license_urls.py',
            11: 'step_11_collate_opensource.py',
            12: 'step_12_collate_custom.py',
            13: 'step_13_final_licenses.py',
            14: 'step_14_extract_modalities.py',
            15: 'step_15_standardize_modalities.py',
            16: 'step_16_enrich_provider.py',
            17: 'step_17_create_db_data.py',
            18: 'step_18_filter_db_data.py',
            19: 'step_19_compare_supabase.py',
            20: 'step_20_refresh_working.py',
            21: 'step_21_deploy_main.py',
        }

    @property
    def default_steps(self) -> str:
        """Default steps to run (excluding manual deploy steps 20-21)."""
        return '1-19'

    # Legacy letter to step number mapping for backward compatibility
    LEGACY_MAPPING = {
        'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,
        'I': 9, 'J': 10, 'K': 11, 'L': 12, 'M': 13, 'N': 14, 'O': 15,
        'P': 16, 'Q': 17, 'R': 18, 'S': 19, 'T': 20, 'U': 21
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
        description="OpenRouter Pipeline Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples (new style):
  python -m src.pipelines.openrouter.runner                 # Run default steps 1-19
  python -m src.pipelines.openrouter.runner --steps 1-19    # Run steps 1 through 19
  python -m src.pipelines.openrouter.runner --steps 1,3,5   # Run specific steps
  python -m src.pipelines.openrouter.runner --dry-run       # Preview execution

Examples (legacy style - for backward compatibility):
  python runner.py --auto-all                               # Run all scripts A to S
  python runner.py --scripts A B C                          # Run specific scripts
  python runner.py --range C E                              # Run script range C to E
        """
    )

    # New style arguments
    parser.add_argument(
        '--steps', type=str, default=None,
        help='Step range to run (e.g., "1-19", "1,3,5")'
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
        help='[Legacy] Run all scripts (A to S)'
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
    runner = OpenRouterPipelineRunner()

    # Determine steps to run
    steps = args.steps

    # Handle legacy arguments
    if args.auto_all:
        steps = '1-19'
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

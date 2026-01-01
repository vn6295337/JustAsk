"""
Groq AI Models Discovery Pipeline.

This pipeline scrapes, processes, and enriches AI model data from Groq's platform.

Steps:
    1. step_01_scrape_models - Scrape production models from Groq
    2. step_02_scrape_modalities - Scrape modality information
    3. step_03_extract_meta_licenses - Extract Meta model licenses
    4. step_04_extract_opensource_licenses - Extract open-source licenses
    5. step_05_consolidate_licenses - Consolidate all license information
    6. step_06_normalize_data - Normalize data for database
    7. step_07_compare_supabase - Compare with existing Supabase data
    8. step_08_refresh_working - Refresh working/staging table (manual)
    9. step_09_deploy_main - Deploy to main table (manual)

Usage:
    from src.pipelines.groq.runner import GroqPipelineRunner
    runner = GroqPipelineRunner()
    runner.run(steps='1-7')
"""

__all__ = ['GroqPipelineRunner']

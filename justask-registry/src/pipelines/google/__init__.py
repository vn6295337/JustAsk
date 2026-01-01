"""
Google AI Models Discovery Pipeline.

This pipeline fetches, filters, and enriches AI model data from Google's API.

Steps:
    1. step_01_fetch - Fetch models from Google AI API
    2. step_02_filter - Filter and validate models
    3. step_03_scrape_modalities - Scrape modality information
    4. step_04_enrich_modalities - Enrich modality data
    5. step_05_create_db_data - Create database-ready records
    6. step_06_compare_supabase - Compare with existing Supabase data
    7. step_07_refresh_working - Refresh working/staging table (manual)
    8. step_08_deploy_main - Deploy to main table (manual)

Usage:
    from src.pipelines.google.runner import GooglePipelineRunner
    runner = GooglePipelineRunner()
    runner.run(steps='1-6')
"""

__all__ = ['GooglePipelineRunner']

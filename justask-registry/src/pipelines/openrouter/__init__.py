"""
OpenRouter AI Models Discovery Pipeline.

This pipeline fetches, processes, and enriches AI model data from OpenRouter's API.
It has the most comprehensive processing with 21 steps covering license extraction,
modality detection, and provider enrichment.

Steps:
    1. step_01_fetch - Fetch models from OpenRouter API
    2. step_02_filter - Filter and validate models
    3. step_03_extract_google_licenses - Extract Google model licenses
    4. step_04_extract_meta_licenses - Extract Meta model licenses
    5. step_05_fetch_hf_license_urls - Fetch license URLs from HuggingFace
    6. step_06_fetch_hf_license_names - Fetch license names from HuggingFace
    7. step_07_standardize_license_names - Standardize license names
    8. step_08_bucketize_licenses - Categorize licenses into buckets
    9. step_09_opensource_license_urls - Process open-source license URLs
    10. step_10_custom_license_urls - Process custom license URLs
    11. step_11_collate_opensource - Collate open-source licenses
    12. step_12_collate_custom - Collate custom licenses
    13. step_13_final_licenses - Generate final license list
    14. step_14_extract_modalities - Extract raw modalities
    15. step_15_standardize_modalities - Standardize modality names
    16. step_16_enrich_provider - Enrich provider information
    17. step_17_create_db_data - Create database-ready records
    18. step_18_filter_db_data - Filter database data
    19. step_19_compare_supabase - Compare with existing Supabase data
    20. step_20_refresh_working - Refresh working/staging table (manual)
    21. step_21_deploy_main - Deploy to main table (manual)

Usage:
    from src.pipelines.openrouter.runner import OpenRouterPipelineRunner
    runner = OpenRouterPipelineRunner()
    runner.run(steps='1-19')
"""

__all__ = ['OpenRouterPipelineRunner']

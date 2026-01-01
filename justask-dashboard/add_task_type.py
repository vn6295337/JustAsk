#!/usr/bin/env python3
"""
Add task_type field to existing Supabase records
"""

import os
from supabase import create_client

def determine_task_type(model_name, provider):
    """Determine task type based on model name and provider"""
    model_lower = model_name.lower()
    
    # Embedding models
    if 'embed' in model_lower or 'embedding' in model_lower:
        return 'embedding'
    
    # Vision/Multimodal models
    if 'vision' in model_lower or 'image' in model_lower or 'vl' in model_lower or 'multimodal' in model_lower:
        return 'multimodal'
    
    # Code generation models
    if ('code' in model_lower or 'coder' in model_lower or 'codestral' in model_lower or 
        'devstral' in model_lower or 'programming' in model_lower):
        return 'code_generation'
    
    # Conversational/Chat models
    if ('chat' in model_lower or 'instruct' in model_lower or 'gemini' in model_lower or
        'turbo' in model_lower or 'conversation' in model_lower):
        return 'conversational'
    
    # Audio models
    if 'audio' in model_lower or 'ast-' in model_lower or 'clap' in model_lower:
        return 'audio'
    
    # Language models (general text generation)
    if ('gpt' in model_lower or 'llama' in model_lower or 'mistral' in model_lower or
        'gemma' in model_lower or 'bert' in model_lower or 't5' in model_lower or
        'bloom' in model_lower or 'pythia' in model_lower or 'olmo' in model_lower):
        return 'text_generation'
    
    # Default to text generation for language models
    return 'text_generation'

def main():
    client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))

    print('=== ADDING TASK_TYPE FIELD ONLY ===')

    # Get all current records
    all_records = client.table('ai_models_discovery').select('*').execute()
    records = all_records.data

    print(f'Found {len(records)} records to update')

    # Process each record
    updated_count = 0
    for record in records:
        model_name = record.get('model_name', '')
        provider = record.get('provider', '')
        
        # Determine task type
        task_type = determine_task_type(model_name, provider)
        
        try:
            # Update only the task_type field
            result = client.table('ai_models_discovery')\
                .update({'task_type': task_type})\
                .eq('id', record['id'])\
                .execute()
            
            if result.data:
                updated_count += 1
                print(f'✓ Updated {model_name}: {task_type}')
            
        except Exception as e:
            print(f'✗ Failed to update {model_name}: {str(e)}')

    print(f'\nSuccessfully updated {updated_count} records')

    # Verify the updates
    print('\n=== VERIFYING TASK TYPE DISTRIBUTION ===')
    verify_result = client.table('ai_models_discovery').select('task_type').execute()

    task_type_counts = {}
    for record in verify_result.data:
        task_type = record.get('task_type', 'unknown')
        task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1

    for task_type, count in sorted(task_type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f'  {task_type}: {count} models')

if __name__ == "__main__":
    main()
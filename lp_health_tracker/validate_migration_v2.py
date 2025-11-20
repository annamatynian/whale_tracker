#!/usr/bin/env python3
"""
Migration Validation Script
==========================

Validates that ALL settings from .env are properly transferred to YAML.
"""

import os
import yaml
import re
from pathlib import Path


def extract_env_variables(env_file_path):
    """Extract all variables from .env file."""
    env_vars = {}
    
    if not os.path.exists(env_file_path):
        print(f"❌ .env file not found: {env_file_path}")
        return env_vars
    
    with open(env_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")  # Remove quotes
                env_vars[key] = {
                    'value': value,
                    'line': line_num,
                    'original_line': line
                }
    
    return env_vars


def load_yaml_config(yaml_file_path):
    """Load YAML configuration."""
    if not os.path.exists(yaml_file_path):
        print(f"❌ YAML file not found: {yaml_file_path}")
        return {}
    
    with open(yaml_file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def flatten_yaml_keys(yaml_data, prefix=''):
    """Flatten nested YAML structure to dot notation."""
    flattened = {}
    
    if isinstance(yaml_data, dict):
        for key, value in yaml_data.items():
            new_prefix = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                flattened.update(flatten_yaml_keys(value, new_prefix))
            else:
                flattened[new_prefix] = value
    
    return flattened


def create_mapping_rules():
    """Define how .env variables map to YAML paths."""
    return {
        'INFURA_API_KEY': 'blockchain.providers.infura.api_key',
        'ALCHEMY_API_KEY': 'blockchain.providers.alchemy.api_key', 
        'ANKR_API_KEY': 'blockchain.providers.ankr.api_key',
        'TELEGRAM_BOT_TOKEN': 'notifications.telegram.bot_token',
        'TELEGRAM_CHAT_ID': 'notifications.telegram.chat_id',
        'COINGECKO_API_KEY': 'apis.coingecko.api_key',
        'WALLET_ADDRESSES': 'monitoring.wallet_addresses',
        'DEFAULT_NETWORK': 'blockchain.default_network',
        'CHECK_INTERVAL_MINUTES': 'monitoring.intervals.check_minutes',
        'DEFAULT_IL_THRESHOLD': 'monitoring.thresholds.default_il_threshold',
        'LOG_LEVEL': 'logging.level',
        'LOG_TO_FILE': 'logging.file_logging',
        'USE_MOCK_DATA': 'development.mock_data',
        'TEST_NETWORK': 'development.test_network',
    }


def validate_migration():
    """Main validation function."""
    project_root = Path(__file__).parent
    env_file = project_root / '.env'
    yaml_file = project_root / 'config' / 'environments' / 'development.yaml'
    
    print("🔍 MIGRATION VALIDATION")
    print("=" * 50)
    
    # Load files
    env_vars = extract_env_variables(env_file)
    yaml_config = load_yaml_config(yaml_file)
    flattened_yaml = flatten_yaml_keys(yaml_config)
    
    print(f"📄 Found {len(env_vars)} variables in .env")
    print(f"📄 Loaded YAML config with {len(flattened_yaml)} flattened keys")
    
    # Get mapping rules
    mapping_rules = create_mapping_rules()
    
    # Validation results
    mapped_correctly = []
    not_mapped = []
    value_mismatches = []
    missing_in_yaml = []
    
    print(f"\n🔍 CHECKING MAPPING...")
    print("-" * 30)
    
    for env_key, env_data in env_vars.items():
        env_value = env_data['value']
        
        if env_key in mapping_rules:
            yaml_path = mapping_rules[env_key]
            yaml_value = flattened_yaml.get(yaml_path)
            
            if yaml_value is None:
                missing_in_yaml.append(f"{env_key} -> {yaml_path}")
                print(f"❌ MISSING: {env_key} not found at {yaml_path}")
            else:
                # Type conversions for comparison
                yaml_str = str(yaml_value).lower()
                env_str = str(env_value).lower()
                
                # Special handling for boolean conversions
                if yaml_str in ['true', 'false']:
                    env_str = 'true' if env_str in ['true', '1', 'yes'] else 'false'
                
                # Special handling for lists (wallet addresses)
                if env_key == 'WALLET_ADDRESSES':
                    if isinstance(yaml_value, list) and len(yaml_value) > 0:
                        # Compare first address
                        if env_value and yaml_value[0].lower() == env_value.lower():
                            yaml_str = env_str  # Mark as matching
                
                if yaml_str == env_str or (not env_value and not yaml_value):
                    mapped_correctly.append(f"✅ {env_key} = {env_value}")
                    print(f"✅ OK: {env_key}")
                else:
                    value_mismatches.append(f"{env_key}: '{env_value}' != '{yaml_value}'")
                    print(f"⚠️  MISMATCH: {env_key} = '{env_value}' vs '{yaml_value}'")
        else:
            not_mapped.append(f"{env_key} = {env_value}")
            print(f"❓ NO RULE: {env_key} (might be optional)")
    
    # Print summary
    print(f"\n📊 MIGRATION SUMMARY")
    print("=" * 30)
    print(f"✅ Correctly mapped: {len(mapped_correctly)}")
    print(f"❌ Missing in YAML: {len(missing_in_yaml)}")
    print(f"⚠️  Value mismatches: {len(value_mismatches)}")
    print(f"❓ No mapping rule: {len(not_mapped)}")
    
    # Detailed output
    if missing_in_yaml:
        print(f"\n❌ CRITICAL: Missing in YAML:")
        for item in missing_in_yaml:
            print(f"   {item}")
    
    if value_mismatches:
        print(f"\n⚠️  Value mismatches:")
        for item in value_mismatches:
            print(f"   {item}")
    
    if not_mapped:
        print(f"\n❓ Variables without mapping rules:")
        for item in not_mapped:
            print(f"   {item}")
    
    # Final verdict
    is_safe = len(missing_in_yaml) == 0 and len(value_mismatches) == 0
    
    print(f"\n🎯 MIGRATION VERDICT:")
    if is_safe:
        print("✅ SAFE TO MIGRATE - All critical data preserved")
    else:
        print("❌ NOT SAFE - Fix issues above before migrating")
    
    return is_safe


if __name__ == "__main__":
    try:
        is_safe = validate_migration()
        exit(0 if is_safe else 1)
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

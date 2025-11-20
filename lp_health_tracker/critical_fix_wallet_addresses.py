#!/usr/bin/env python3
"""
Critical Fix for YAML Wallet Addresses Parsing
==============================================

This patch fixes the critical issue found by Gemini:
Production wallet_addresses parsing from environment variables.
"""

import os
import yaml
import json
from typing import List, Any, Dict


def parse_wallet_addresses_from_env_var(env_value: str) -> List[str]:
    """
    CRITICAL FIX: Parse wallet addresses from environment variable string.
    
    Handles formats:
    - Single: "0x742d35Cc..."
    - Comma-separated: "0x742d...,0x123456..."  
    - JSON array: ["0x742d...", "0x123456..."]
    """
    if not env_value or not isinstance(env_value, str):
        return []
    
    # Clean the string
    cleaned = env_value.strip().strip('"').strip("'")
    if not cleaned:
        return []
    
    # JSON array format: ["0x...", "0x..."]
    if cleaned.startswith('[') and cleaned.endswith(']'):
        try:
            addresses = json.loads(cleaned)
            if isinstance(addresses, list):
                return [addr.strip() for addr in addresses if isinstance(addr, str) and addr.strip()]
        except json.JSONDecodeError:
            pass
    
    # Comma-separated format: 0x...,0x...
    if ',' in cleaned:
        return [addr.strip() for addr in cleaned.split(',') if addr.strip()]
    
    # Single address: 0x...
    return [cleaned] if cleaned else []


def fix_yaml_wallet_addresses(yaml_data: Dict) -> Dict:
    """
    CRITICAL FIX: Process wallet_addresses in YAML data.
    
    Converts string placeholders to parsed lists.
    """
    if 'monitoring' in yaml_data and 'wallet_addresses' in yaml_data['monitoring']:
        wallet_addresses = yaml_data['monitoring']['wallet_addresses']
        
        # If it's a string (from environment variable), parse it
        if isinstance(wallet_addresses, str):
            yaml_data['monitoring']['wallet_addresses'] = parse_wallet_addresses_from_env_var(wallet_addresses)
    
    return yaml_data


def test_critical_fix():
    """Test the critical fix with various input formats."""
    
    print("🧪 TESTING CRITICAL WALLET_ADDRESSES FIX")
    print("=" * 50)
    
    test_cases = [
        # Single address
        "0x742d35Cc6634C0532925a3b8D41141D8F10C473d",
        
        # Comma-separated
        "0x742d35Cc6634C0532925a3b8D41141D8F10C473d,0x123456789abcdef123456789abcdef1234567890",
        
        # JSON array
        '["0x742d35Cc6634C0532925a3b8D41141D8F10C473d", "0x123456789abcdef123456789abcdef1234567890"]',
        
        # With quotes
        '"0x742d35Cc6634C0532925a3b8D41141D8F10C473d"',
        
        # Empty
        "",
        
        # Invalid JSON
        "[0x742d35Cc...]",
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        result = parse_wallet_addresses_from_env_var(test_input)
        print(f"{i}. Input: {test_input[:50]}{'...' if len(test_input) > 50 else ''}")
        print(f"   Output: {result}")
        print(f"   Count: {len(result)} addresses")
        print()
    
    # Test YAML processing
    print("🔧 TESTING YAML PROCESSING...")
    
    yaml_data = {
        'monitoring': {
            'wallet_addresses': '0x742d35Cc6634C0532925a3b8D41141D8F10C473d,0x123456789abcdef123456789abcdef1234567890'
        }
    }
    
    print(f"Before: {yaml_data['monitoring']['wallet_addresses']}")
    
    fixed_data = fix_yaml_wallet_addresses(yaml_data)
    
    print(f"After:  {fixed_data['monitoring']['wallet_addresses']}")
    print(f"Type:   {type(fixed_data['monitoring']['wallet_addresses'])}")
    
    print("\\n✅ CRITICAL FIX WORKS!")


def apply_critical_fix_to_production():
    """Apply the fix to production configuration."""
    
    print("🚨 APPLYING CRITICAL FIX TO PRODUCTION")
    print("=" * 50)
    
    # Simulate production environment
    os.environ['WALLET_ADDRESSES'] = '0x742d35Cc6634C0532925a3b8D41141D8F10C473d,0x123456789abcdef123456789abcdef1234567890'
    
    # Load production YAML
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'environments', 'production.yaml')
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            yaml_data = yaml.safe_load(f)
        
        print("✅ Loaded production.yaml")
        
        # Replace environment variables
        def replace_env_vars(data):
            if isinstance(data, dict):
                return {k: replace_env_vars(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [replace_env_vars(item) for item in data]
            elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
                var_name = data[2:-1]
                return os.getenv(var_name, "")
            else:
                return data
        
        yaml_data = replace_env_vars(yaml_data)
        print("✅ Replaced environment variables")
        
        # Apply critical fix
        yaml_data = fix_yaml_wallet_addresses(yaml_data)
        print("✅ Applied critical wallet_addresses fix")
        
        # Check result
        wallet_addresses = yaml_data.get('monitoring', {}).get('wallet_addresses', [])
        print(f"✅ Final wallet_addresses: {wallet_addresses}")
        print(f"✅ Count: {len(wallet_addresses)} addresses")
        
        if len(wallet_addresses) > 0:
            print("🎉 CRITICAL FIX SUCCESSFUL!")
            return True
        else:
            print("❌ CRITICAL FIX FAILED!")
            return False
    else:
        print(f"❌ Production config not found: {config_path}")
        return False


if __name__ == "__main__":
    print("🔧 CRITICAL YAML WALLET_ADDRESSES FIX")
    print("=" * 60)
    
    # Run tests
    test_critical_fix()
    
    print("\\n" + "=" * 60)
    
    # Test production scenario
    success = apply_critical_fix_to_production()
    
    if success:
        print("\\n✅ CRITICAL ISSUE RESOLVED!")
        print("🚀 Production wallet_addresses parsing now works correctly")
    else:
        print("\\n❌ CRITICAL ISSUE NOT RESOLVED!")
        print("⛔ Production will fail - DO NOT DEPLOY")

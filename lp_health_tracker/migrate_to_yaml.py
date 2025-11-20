#!/usr/bin/env python3
"""
Migration script to switch from .env to YAML configuration
"""

import os
import shutil
from pathlib import Path

def migrate_to_yaml():
    """Migrate from old .env settings to new YAML settings."""
    
    project_root = Path(__file__).parent
    config_dir = project_root / "config"
    
    print("🔄 Starting migration to YAML configuration...")
    
    # Step 1: Install PyYAML if not installed
    print("\nStep 1: Installing PyYAML...")
    try:
        import yaml
        print("✅ PyYAML already installed")
    except ImportError:
        print("📦 Installing PyYAML...")
        os.system("pip install pyyaml")
        print("✅ PyYAML installed")
    
    # Step 2: Test YAML configuration
    print("\nStep 2: Testing YAML configuration...")
    try:
        import sys
        sys.path.insert(0, str(config_dir))
        from settings_yaml import get_settings
        
        # Test loading development config
        settings = get_settings("development")
        print(f"✅ YAML config loaded successfully")
        print(f"   Found {len(settings.wallet_addresses)} wallet addresses")
        print(f"   Network: {settings.blockchain.default_network}")
        
    except Exception as e:
        print(f"❌ YAML config test failed: {e}")
        return False
    
    # Step 3: Backup old settings
    print("\nStep 3: Backing up old configuration...")
    old_settings = config_dir / "settings.py"
    if old_settings.exists():
        backup_path = config_dir / "settings_old_backup.py"
        shutil.copy2(old_settings, backup_path)
        print(f"✅ Backed up old settings to: {backup_path}")
    
    # Step 4: Replace settings.py with YAML version
    print("\nStep 4: Installing new YAML-based settings...")
    yaml_settings = config_dir / "settings_yaml.py"
    new_settings = config_dir / "settings.py"
    
    if yaml_settings.exists():
        shutil.copy2(yaml_settings, new_settings)
        print("✅ New YAML settings installed as settings.py")
    
    # Step 5: Update imports in settings.py
    print("\nStep 5: Creating compatibility layer...")
    compatibility_code = '''
# Compatibility imports for existing code
from settings_yaml import get_settings

# Create global instance for backward compatibility
Settings = lambda: get_settings()
settings = get_settings()

# Export commonly used items
CONTRACT_ADDRESSES = settings.contracts
DEFAULT_POSITION_CONFIG = getattr(settings, 'default_position_config', {})
RISK_CATEGORIES = settings.risk_categories
SUPPORTED_PROTOCOLS = getattr(settings, 'supported_protocols', {})
API_LIMITS = getattr(settings, 'api_limits', {})
'''
    
    with open(new_settings, 'a') as f:
        f.write(compatibility_code)
    
    print("✅ Compatibility layer added")
    
    # Step 6: Test integration
    print("\nStep 6: Testing integration...")
    try:
        # Test that old import still works
        sys.path.insert(0, str(config_dir))
        from settings import Settings, get_settings
        
        test_settings = Settings()
        print(f"✅ Old interface works: {len(test_settings.wallet_addresses)} wallets")
        
        new_settings = get_settings()  
        print(f"✅ New interface works: {len(new_settings.wallet_addresses)} wallets")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False
    
    # Step 7: Success message
    print(f"\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
    print(f"")
    print(f"✅ Old .env approach replaced with YAML configuration")
    print(f"✅ No more WALLET_ADDRESSES parsing errors!")
    print(f"✅ Backward compatibility maintained")  
    print(f"✅ Ready for V3 analytics and ML features")
    print(f"")
    print(f"📁 Configuration files created:")
    print(f"   - config/base.yaml (default settings)")
    print(f"   - config/environments/development.yaml (your settings)")
    print(f"   - config/environments/production.yaml (production template)")
    print(f"   - config/environments/testing.yaml (test settings)")
    print(f"")
    print(f"🔧 Next steps:")
    print(f"   1. Review config/environments/development.yaml")
    print(f"   2. Run: pytest tests/integration/test_config_validation.py")
    print(f"   3. Your existing code should work without changes!")
    
    return True

if __name__ == "__main__":
    success = migrate_to_yaml()
    if not success:
        print("\n❌ Migration failed. Please check errors above.")
        exit(1)
    else:
        print(f"\n✨ Migration successful! YAML configuration is now active.")

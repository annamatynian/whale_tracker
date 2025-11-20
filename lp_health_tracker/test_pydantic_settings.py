#!/usr/bin/env python3
"""
Quick test to verify Pydantic Settings integration works.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_pydantic_settings():
    """Test that new Pydantic Settings class works."""
    print("🧪 Testing Pydantic Settings integration...")
    
    try:
        # Import the updated Settings class
        from config.settings import Settings
        print("✅ Import successful")
        
        # Try to create Settings instance
        # This should work even without .env file (using defaults)
        try:
            settings = Settings(
                TELEGRAM_BOT_TOKEN="test_token",
                TELEGRAM_CHAT_ID="test_chat_id"
            )
            print("✅ Settings creation successful")
            
            # Test basic functionality
            print(f"✅ Default network: {settings.DEFAULT_NETWORK}")
            print(f"✅ Check interval: {settings.CHECK_INTERVAL_MINUTES}")
            print(f"✅ IL threshold: {settings.DEFAULT_IL_THRESHOLD}")
            
            # Test method compatibility
            rpc_url = settings.get_rpc_url()
            print(f"✅ RPC URL method works: {rpc_url[:50]}...")
            
            # Test validation
            try:
                invalid_settings = Settings(
                    TELEGRAM_BOT_TOKEN="test",
                    TELEGRAM_CHAT_ID="test",
                    CHECK_INTERVAL_MINUTES=0  # Should fail validation
                )
                print("❌ Validation should have failed!")
                return False
            except ValueError as e:
                print(f"✅ Validation works: {e}")
            
            print("\n🎉 All tests passed! Pydantic Settings integration successful.")
            return True
            
        except Exception as e:
            print(f"❌ Settings creation failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

if __name__ == "__main__":
    success = test_pydantic_settings()
    sys.exit(0 if success else 1)

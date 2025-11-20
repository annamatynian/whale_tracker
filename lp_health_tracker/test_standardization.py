#!/usr/bin/env python3
"""
Test Standardization - Проверка стандартизации IL
=================================================

Тестирует корректность стандартизированной логики IL.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_il_standardization():
    """Тест стандартизации IL логики."""
    print("🧪 Testing IL Standardization...")
    
    try:
        from data_analyzer import ImpermanentLossCalculator
        
        calc = ImpermanentLossCalculator()
        
        # Тест 1: Цена выросла в 2 раза
        print("\n1. Testing 2x price increase:")
        initial_ratio = 1.0  # $1000 / $1000
        current_ratio = 2.0  # $2000 / $1000 
        
        il = calc.calculate_impermanent_loss(initial_ratio, current_ratio)
        print(f"   IL = {il:.4f} (should be positive ~0.0572)")
        
        assert il > 0, "IL should be positive for price divergence"
        assert 0.055 < il < 0.060, f"IL should be ~0.0572, got {il}"
        print("   ✅ PASS")
        
        # Тест 2: Цена не изменилась
        print("\n2. Testing no price change:")
        il_no_change = calc.calculate_impermanent_loss(1.0, 1.0)
        print(f"   IL = {il_no_change:.4f} (should be 0)")
        
        assert il_no_change == 0.0, "IL should be 0 for no price change"
        print("   ✅ PASS")
        
        # Тест 3: Цена упала вдвое
        print("\n3. Testing 50% price drop:")
        il_drop = calc.calculate_impermanent_loss(1.0, 0.5)
        print(f"   IL = {il_drop:.4f} (should be positive ~0.0572)")
        
        assert il_drop > 0, "IL should be positive for price divergence"
        print("   ✅ PASS")
        
        # Тест 4: Percentage formatting
        print("\n4. Testing percentage formatting:")
        il_pct = calc.calculate_impermanent_loss_percentage(1.0, 2.0)
        print(f"   IL% = {il_pct} (should be ~5.72%)")
        
        assert "%" in il_pct, "Should contain % symbol"
        assert "5.7" in il_pct, "Should show ~5.7%"
        print("   ✅ PASS")
        
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ IL standardization working correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False

def test_imports():
    """Тест корректности импортов."""
    print("\n🔗 Testing imports...")
    
    try:
        from data_analyzer import ImpermanentLossCalculator, NetPnLCalculator
        print("   ✅ ImpermanentLossCalculator imported")
        print("   ✅ NetPnLCalculator imported")
        
        from simple_multi_pool import SimpleMultiPoolManager
        print("   ✅ SimpleMultiPoolManager imported")
        
        from data_providers import MockDataProvider, LiveDataProvider
        print("   ✅ DataProviders imported")
        
        print("✅ All imports working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_no_duplicates():
    """Проверяем, что дублирующие файлы удалены."""
    print("\n🗑️ Testing duplicate removal...")
    
    try:
        # Попытка импорта из удаленных файлов должна провалиться
        try:
            from standard_net_pnl_calculator import StandardNetPnLCalculator
            print("❌ standard_net_pnl_calculator still accessible!")
            return False
        except ImportError:
            print("   ✅ standard_net_pnl_calculator properly removed")
            
        try:
            from updated_simple_multi_pool_manager import UpdatedSimpleMultiPoolManager
            print("❌ updated_simple_multi_pool_manager still accessible!")
            return False
        except ImportError:
            print("   ✅ updated_simple_multi_pool_manager properly removed")
            
        print("✅ Duplicate files properly handled")
        return True
        
    except Exception as e:
        print(f"❌ Duplicate test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 LP Health Tracker - Standardization Tests")
    print("=" * 50)
    
    all_passed = True
    
    # Запускаем все тесты
    all_passed &= test_imports()
    all_passed &= test_il_standardization()
    all_passed &= test_no_duplicates()
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Standardization successful!")
        print("✅ Project ready for next development phase")
    else:
        print("❌ Some tests failed. Check output above.")
        
    print("=" * 50)

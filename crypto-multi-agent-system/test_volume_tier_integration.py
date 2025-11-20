"""
Test Tier Integration with Volume Analysis
Проверяет работу новой volume_tier_integration.py

Author: Tier Integration Test
Date: 2025-01-20
"""

import sys
import asyncio
sys.path.insert(0, r'C:\Users\annam\Documents\DeFi-RAG-Project\crypto-multi-agent-system')

from agents.discovery.volume_tier_integration import VolumeMetricsFetcher
from agents.pump_analysis import TokenTier


class MockDiscoveryReport:
    """Mock объект для тестирования"""
    def __init__(
        self,
        token_address: str,
        symbol: str = "TEST",
        is_honeypot: bool = False,
        is_open_source: bool = True,
        buy_tax: float = 5.0,
        sell_tax: float = 5.0
    ):
        self.base_token_address = token_address
        self.base_token_symbol = symbol
        self.chain_id = "ethereum"
        self.is_honeypot = is_honeypot
        self.is_open_source = is_open_source
        self.buy_tax = buy_tax
        self.sell_tax = sell_tax
        self.discovery_score = 50  # Базовый балл
        self.discovery_reason = "Initial discovery"


def test_tier_creation_from_volume():
    """Тест 1: Создание tier'а из volume метрик"""
    print("=" * 70)
    print("TEST 1: Tier Creation from Volume Metrics")
    print("=" * 70)
    
    fetcher = VolumeMetricsFetcher("dummy_key")
    
    # Mock volume metrics - PREMIUM scenario
    premium_volume = {
        'volume_ratio': 2.0,
        'volume_ratio_healthy': True,
        'volume_ratio_overheated': False,
        'volume_ratio_dead': False,
        'is_accelerating': True,
        'acceleration_factor': 2.5,
        'avg_volume_last_1_hour': 50000
    }
    
    mock_report = MockDiscoveryReport(
        token_address="0x1234567890abcdef",
        symbol="PERFECT",
        is_honeypot=False,
        is_open_source=True,
        buy_tax=2.0,
        sell_tax=5.0
    )
    
    tier_result = fetcher._create_tier_analysis_from_volume_and_security(
        premium_volume,
        mock_report,
        data_completeness=0.6
    )
    
    print(f"\n📊 Input Metrics:")
    print(f"   Volume ratio: {premium_volume['volume_ratio']}")
    print(f"   Acceleration: {premium_volume['acceleration_factor']}x")
    print(f"   Honeypot: {mock_report.is_honeypot}")
    print(f"   Taxes: {mock_report.buy_tax}% / {mock_report.sell_tax}%")
    
    print(f"\n🎯 Tier Result:")
    print(f"   Tier: {tier_result.tier.value}")
    print(f"   Confidence: {tier_result.confidence:.0%}")
    
    summary = tier_result.get_summary()
    print(f"   Tags: {summary['green_count']}✅ {summary['yellow_count']}⚠️ {summary['red_count']}❌")
    
    # В этом случае ожидаем STRONG или выше (без OnChain данных не может быть PREMIUM)
    # Но точно не AVOID
    assert tier_result.tier != TokenTier.AVOID, "Should not be AVOID with good metrics"
    
    print("\n✅ TEST 1 PASSED\n")
    return True


def test_tier_with_bad_metrics():
    """Тест 2: AVOID tier с плохими метриками"""
    print("=" * 70)
    print("TEST 2: AVOID Tier with Bad Metrics")
    print("=" * 70)
    
    fetcher = VolumeMetricsFetcher("dummy_key")
    
    # Mock volume metrics - DEAD token
    dead_volume = {
        'volume_ratio': 0.2,
        'volume_ratio_healthy': False,
        'volume_ratio_overheated': False,
        'volume_ratio_dead': True,
        'is_accelerating': False,
        'acceleration_factor': 0.5,
        'avg_volume_last_1_hour': 100
    }
    
    mock_report = MockDiscoveryReport(
        token_address="0xdead000000000000",
        symbol="DEAD",
        is_honeypot=False,
        is_open_source=True,
        buy_tax=5.0,
        sell_tax=10.0
    )
    
    tier_result = fetcher._create_tier_analysis_from_volume_and_security(
        dead_volume,
        mock_report,
        data_completeness=0.6
    )
    
    print(f"\n📊 Input Metrics:")
    print(f"   Volume ratio: {dead_volume['volume_ratio']} (DEAD)")
    print(f"   Acceleration: {dead_volume['acceleration_factor']}x")
    
    print(f"\n🎯 Tier Result:")
    print(f"   Tier: {tier_result.tier.value}")
    print(f"   Critical flags: {tier_result.critical_flags}")
    
    # Должен быть AVOID
    assert tier_result.tier == TokenTier.AVOID, f"Expected AVOID, got {tier_result.tier}"
    assert len(tier_result.critical_flags) > 0, "Should have critical flags"
    
    print("\n✅ TEST 2 PASSED\n")
    return True


def test_tier_with_honeypot():
    """Тест 3: AVOID tier с honeypot"""
    print("=" * 70)
    print("TEST 3: AVOID Tier with Honeypot")
    print("=" * 70)
    
    fetcher = VolumeMetricsFetcher("dummy_key")
    
    # Good volume, but HONEYPOT
    good_volume = {
        'volume_ratio': 2.0,
        'volume_ratio_healthy': True,
        'volume_ratio_overheated': False,
        'volume_ratio_dead': False,
        'is_accelerating': True,
        'acceleration_factor': 3.0,
        'avg_volume_last_1_hour': 100000
    }
    
    mock_report = MockDiscoveryReport(
        token_address="0xscam000000000000",
        symbol="SCAM",
        is_honeypot=True,  # HONEYPOT!
        is_open_source=True,
        buy_tax=5.0,
        sell_tax=99.0
    )
    
    tier_result = fetcher._create_tier_analysis_from_volume_and_security(
        good_volume,
        mock_report,
        data_completeness=0.6
    )
    
    print(f"\n📊 Input Metrics:")
    print(f"   Volume ratio: {good_volume['volume_ratio']} (HEALTHY)")
    print(f"   Acceleration: {good_volume['acceleration_factor']}x (STRONG)")
    print(f"   BUT Honeypot: {mock_report.is_honeypot}")
    
    print(f"\n🎯 Tier Result:")
    print(f"   Tier: {tier_result.tier.value}")
    print(f"   Critical flags: {tier_result.critical_flags}")
    
    # Должен быть AVOID несмотря на хорошие volume метрики
    assert tier_result.tier == TokenTier.AVOID, f"Expected AVOID, got {tier_result.tier}"
    assert "HONEYPOT" in str(tier_result.critical_flags), "Should mention honeypot"
    
    print("\n✅ TEST 3 PASSED\n")
    return True


def test_stats_collection():
    """Тест 4: Сбор статистики tier'ов"""
    print("=" * 70)
    print("TEST 4: Tier Statistics Collection")
    print("=" * 70)
    
    fetcher = VolumeMetricsFetcher("dummy_key")
    
    # Создать несколько tier'ов
    test_cases = [
        ("PREMIUM", True, 2.5, False),  # Should be STRONG (no onchain)
        ("AVOID", False, 0.3, False),   # Dead token
        ("GOOD", True, 1.8, False),     # Should be SPECULATIVE/STRONG
        ("SCAM", True, 2.0, True),      # Honeypot - AVOID
    ]
    
    for symbol, is_accel, ratio, is_honey in test_cases:
        volume = {
            'volume_ratio': ratio,
            'volume_ratio_healthy': 0.5 < ratio < 3.0,
            'volume_ratio_overheated': ratio > 3.0,
            'volume_ratio_dead': ratio < 0.5,
            'is_accelerating': is_accel,
            'acceleration_factor': 2.0 if is_accel else 0.8,
            'avg_volume_last_1_hour': 10000
        }
        
        mock_report = MockDiscoveryReport(
            token_address=f"0x{symbol}",
            symbol=symbol,
            is_honeypot=is_honey
        )
        
        tier_result = fetcher._create_tier_analysis_from_volume_and_security(
            volume, mock_report, 0.6
        )
        
        # Обновить статистику
        tier_name = f"tier_{tier_result.tier.value.lower()}"
        if tier_name in fetcher.stats:
            fetcher.stats[tier_name] += 1
    
    # Получить статистику
    stats = fetcher.get_stats()
    
    print(f"\n📊 Tier Statistics:")
    if "tier_distribution" in stats:
        for tier, pct in stats["tier_distribution"].items():
            count = stats[f"tier_{tier}"]
            print(f"   {tier.upper():12s}: {count} ({pct})")
    else:
        print("   (No tier distribution calculated yet)")
    
    # Проверить, что есть разные tier'ы
    total_tiers = (
        stats["tier_premium"] + 
        stats["tier_strong"] + 
        stats["tier_speculative"] + 
        stats["tier_avoid"]
    )
    
    assert total_tiers == len(test_cases), f"Expected {len(test_cases)} tiers, got {total_tiers}"
    assert stats["tier_avoid"] >= 2, "Should have at least 2 AVOID tier'ов"
    
    print("\n✅ TEST 4 PASSED\n")
    return True


def run_all_tests():
    """Запустить все тесты"""
    print("\n" + "━" * 70)
    print("TIER + VOLUME INTEGRATION - TEST SUITE")
    print("━" * 70)
    
    tests = [
        ("Tier Creation", test_tier_creation_from_volume),
        ("AVOID - Dead Token", test_tier_with_bad_metrics),
        ("AVOID - Honeypot", test_tier_with_honeypot),
        ("Stats Collection", test_stats_collection)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ TEST FAILED: {name}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "━" * 70)
    print("TEST SUMMARY")
    print("━" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status:12s} - {name}")
    
    print("\n" + "━" * 70)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Tier + Volume integration is working!")
        print("\n📋 Next steps:")
        print("   1. Test with real API (if you have GRAPH_API_KEY)")
        print("   2. Integrate into main discovery pipeline")
        print("   3. Add OnChain data for complete tier analysis")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
    
    print("━" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

"""
End-to-End Test: Discovery Pipeline with Volume Enrichment
Тестирует полную цепочку: Discovery → Volume Enrichment → Filtering

Usage:
    python test_discovery_with_volume_e2e.py
"""

import sys
import asyncio
import logging

sys.path.insert(0, r'C:\Users\annam\Documents\DeFi-RAG-Project\crypto-multi-agent-system')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(name)s - %(message)s'
)

from agents.discovery.thegraph_discovery_agent_part4 import TheGraphDiscoveryAgentV4
from agents.discovery.part4_volume_patch import (
    enrich_reports_with_volume,
    filter_reports_by_volume,
    print_volume_enrichment_summary,
    VolumeEnrichedDiscoverySession
)


async def test_discovery_with_volume():
    """
    End-to-End тест:
    1. Запускает discovery для поиска токенов
    2. Обогащает найденные токены volume metrics
    3. Фильтрует по volume criteria
    4. Показывает результаты
    """
    
    print("=" * 70)
    print("END-TO-END TEST: Discovery Pipeline with Volume Enrichment")
    print("=" * 70)
    
    # ===== ЭТАП 1: DISCOVERY =====
    print("\n🔍 STAGE 1: Running token discovery...")
    print("-" * 70)
    
    agent = TheGraphDiscoveryAgentV4()
    
    # Запустить discovery
    session = await agent.discover_tokens_full_pipeline()
    
    initial_reports = session.discovery_reports
    
    print(f"\n✅ Discovery complete:")
    print(f"   Total tokens found: {len(initial_reports)}")
    print(f"   Session duration: {session.session_stats['session_duration_seconds']:.1f}s")
    
    if not initial_reports:
        print("\n⚠️ No tokens found in discovery. Stopping test.")
        return
    
    # Показать топ-5 найденных токенов
    print(f"\n   Top 5 discovered tokens:")
    for i, report in enumerate(initial_reports[:5], 1):
        print(f"      {i}. {report.base_token_symbol} - "
              f"Score: {report.discovery_score}, "
              f"Liquidity: ${report.liquidity_usd:,.0f}")
    
    # ===== ЭТАП 2: VOLUME ENRICHMENT =====
    print(f"\n\n📊 STAGE 2: Enriching with volume metrics...")
    print("-" * 70)
    
    # Получить subgraph_id и api_key из первого активного subgraph
    active_subgraphs = agent.get_active_subgraphs()
    if not active_subgraphs:
        print("⚠️ No active subgraphs found")
        return
    
    # Используем первый активный subgraph (обычно Uniswap V2)
    first_subgraph = active_subgraphs[0]
    subgraph_id = first_subgraph.subgraph_id
    graph_api_key = agent.config.graph_api_key
    
    print(f"   Using subgraph: {first_subgraph.name}")
    print(f"   Enriching {len(initial_reports)} reports...")
    
    # Обогатить volume metrics (ОГРАНИЧИВАЕМ до первых 10 для теста)
    test_reports = initial_reports[:10]
    print(f"   ⚠️ TEST MODE: Processing only first {len(test_reports)} tokens")
    
    enriched_reports, enrichment_stats = await enrich_reports_with_volume(
        test_reports,
        subgraph_id,
        graph_api_key
    )
    
    print(f"\n✅ Volume enrichment complete:")
    print(f"   Success rate: {enrichment_stats.get('success_rate', 0):.1f}%")
    print(f"   Reports with acceleration: {enrichment_stats.get('pairs_with_acceleration', 0)}")
    
    # ===== ЭТАП 3: FILTERING =====
    print(f"\n\n🔽 STAGE 3: Filtering by volume criteria...")
    print("-" * 70)
    
    filtered_reports, filtered_count = filter_reports_by_volume(
        enriched_reports,
        require_acceleration=True,  # Требуем ускорение
        require_healthy_ratio=False  # Не требуем healthy ratio (многие токены не пройдут)
    )
    
    print(f"\n✅ Filtering complete:")
    print(f"   Removed: {filtered_count} reports")
    print(f"   Remaining: {len(filtered_reports)} reports")
    
    # ===== ЭТАП 4: РЕЗУЛЬТАТЫ =====
    print(f"\n\n📋 STAGE 4: Results")
    print("=" * 70)
    
    if filtered_reports:
        print(f"\n✅ TOKENS WITH VOLUME ACCELERATION:")
        print("-" * 70)
        
        for i, report in enumerate(filtered_reports, 1):
            print(f"\n{i}. {report.base_token_symbol} ({report.base_token_name[:30]})")
            print(f"   Address: {report.base_token_address[:10]}...")
            print(f"   Discovery Score: {report.discovery_score}")
            print(f"   Liquidity: ${report.liquidity_usd:,.0f}")
            
            if hasattr(report, 'volume_metrics') and report.volume_metrics:
                metrics = report.volume_metrics
                print(f"   Volume Metrics:")
                print(f"      avg_7d: ${metrics['avg_volume_last_7_days']:,.0f}")
                print(f"      avg_30d: ${metrics['avg_volume_last_30_days']:,.0f}")
                print(f"      acceleration: {metrics['acceleration_factor']:.2f}x")
                print(f"      volume_ratio: {metrics['volume_ratio']:.3f}")
            
            if hasattr(report, 'volume_filter_reason'):
                print(f"   Filter: {report.volume_filter_reason}")
    else:
        print("\n⚠️ No tokens passed volume filters")
        print("   This is expected for mature tokens without recent acceleration")
        print("   Try running during high volatility period for better results")
    
    # ===== СТАТИСТИКА =====
    print(f"\n\n📊 OVERALL STATISTICS")
    print("=" * 70)
    
    # Создаем VolumeEnrichedDiscoverySession для статистики
    enriched_session = VolumeEnrichedDiscoverySession(session, enrichment_stats)
    enriched_session.update_reports(enriched_reports)
    
    print_volume_enrichment_summary(enriched_session)
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(test_discovery_with_volume())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

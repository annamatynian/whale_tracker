"""
Диагностика низких баллов - почему система не находит хорошие токены
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent
from tools.market_data.coingecko_client import CoinGeckoClient
from tools.security.goplus_client import GoPlusClient
from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators
from agents.pump_analysis.pump_models import NarrativeType

async def diagnose_scoring():
    """Диагностика почему баллы низкие"""
    print("🔍 Диагностика системы скоринга...")
    
    # Получаем один токен
    discovery_agent = PumpDiscoveryAgent()
    candidates = await discovery_agent.discover_tokens_async()
    
    if not candidates:
        print("❌ Нет кандидатов для диагностики")
        return
    
    candidate = candidates[0]  # Берем первый для анализа
    print(f"\n📊 Анализируем токен: {candidate.base_token_symbol}")
    print(f"   Discovery score: {candidate.discovery_score}")
    
    # Получаем данные
    coingecko_client = CoinGeckoClient()
    goplus_client = GoPlusClient()
    
    coingecko_data = coingecko_client.get_token_info_by_contract(
        candidate.chain_id, candidate.base_token_address
    )
    goplus_data = goplus_client.get_token_security(
        candidate.chain_id, candidate.base_token_address
    )
    
    print(f"\n🔍 CoinGecko данные:")
    print(f"   Найден: {bool(coingecko_data)}")
    if coingecko_data:
        print(f"   Community score: {coingecko_data.get('community_score')}")
        print(f"   Categories: {coingecko_data.get('categories', [])}")
    
    print(f"\n🛡️ GoPlus данные:")
    print(f"   Найден: {bool(goplus_data)}")
    if goplus_data:
        print(f"   Is honeypot: {goplus_data.get('is_honeypot')}")
        print(f"   Buy tax: {goplus_data.get('buy_tax')}")
        print(f"   Sell tax: {goplus_data.get('sell_tax')}")
    
    # Создаем indicators
    indicators = RealisticPumpIndicators(
        narrative_type=NarrativeType.UNKNOWN,
        has_trending_narrative=False,
        coingecko_score=coingecko_data.get("community_score") if coingecko_data else None,
        is_honeypot=goplus_data.get('is_honeypot') == '1' if goplus_data else True,
        is_open_source=goplus_data.get('is_open_source') == '1' if goplus_data else False,
        buy_tax_percent=float(goplus_data.get('buy_tax', '1')) * 100 if goplus_data else 100,
        sell_tax_percent=float(goplus_data.get('sell_tax', '1')) * 100 if goplus_data else 100
    )
    
    # Анализируем баллы
    scoring_matrix = RealisticScoringMatrix(indicators=indicators)
    analysis = scoring_matrix.get_detailed_analysis()
    
    print(f"\n📈 Детальный анализ баллов:")
    print(f"   Итого: {analysis['total_score']}/105")
    print(f"   По категориям: {analysis['category_scores']}")
    print(f"   Рекомендация: {analysis['recommendation']}")
    # Убираем reasoning - его нет в analysis

if __name__ == "__main__":
    asyncio.run(diagnose_scoring())

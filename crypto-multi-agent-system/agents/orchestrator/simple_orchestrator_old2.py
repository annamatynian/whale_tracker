"""
Simple Orchestrator - Crypto Multi-Agent System (v4 - МНОГОУРОВНЕВАЯ ВОРОНКА)

Координирует pump-specific агентов для реализации многоуровневой воронки анализа:
1. УРОВЕНЬ 1: Обнаружение - широкая сеть для поиска кандидатов
2. УРОВЕНЬ 2: Обогащение и Первичный Скоринг - анализ ВСЕХ кандидатов  
3. УРОВЕНЬ 3: Ранжирование и Отбор - выбор топ-15 лучших
4. УРОВЕНЬ 4: Глубокий OnChain Анализ - дорогие проверки только для лучших
5. УРОВЕНЬ 5: Генерация Алертов - финальные рекомендации

Автор: Crypto Multi-Agent Team (Gemini Architecture Optimization)
"""
import asyncio
import logging
from typing import List

# --- Абсолютные импорты от корня проекта ---
from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent
from tools.market_data.coingecko_client import CoinGeckoClient
from tools.security.goplus_client import GoPlusClient
from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators, PumpRecommendationMVP, should_run_onchain_analysis
from agents.pump_analysis.pump_models import ApiUsageTracker, NarrativeType
from agents.pump_analysis.narrative_analyzer import find_narrative_in_categories
from agents.onchain.onchain_agent import OnChainAgent
# from agents.social_intelligence.telegram_social_agent import TelegramSocialAgent  # ОТКЛЮЧЕНО


# --- КОНФИГУРАЦИЯ МНОГОУРОВНЕВОЙ ВОРОНКИ ---
ALERT_RECOMMENDATIONS = [
    PumpRecommendationMVP.HIGH_POTENTIAL,
    PumpRecommendationMVP.MEDIUM_POTENTIAL  # Временно для MVP, чтобы тестировать алерты
]

# Конфигурация воронки
FUNNEL_CONFIG = {
    'top_n_for_onchain': 15,        # Топ-15 для Level 4 (OnChain)
    'min_score_for_alert': 60,      # Минимальный балл для алерта
    'api_calls_threshold': 45       # Минимальный Discovery score для API calls
}


class SimpleOrchestrator:
    """Координирует pump-detection pipeline с многоуровневой воронкой."""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.discovery_agent = PumpDiscoveryAgent()
            self.coingecko_client = CoinGeckoClient()
            self.goplus_client = GoPlusClient()
            self.onchain_agent = OnChainAgent()
            # self.telegram_agent = TelegramSocialAgent()  # ОТКЛЮЧЕНО пока
            self.api_tracker = ApiUsageTracker()
            self.logger.info("Оркестратор многоуровневой воронки инициализирован.")
        except ValueError as e:
            self.logger.error(f"Критическая ошибка инициализации: {e}. Пожалуйста, проверьте ваш .env файл.")
            raise

    def should_spend_api_calls(self, preliminary_score: int) -> bool:
        """
        Решает, стоит ли тратить API вызовы на Level 2.
        
        В многоуровневой воронке мы более агрессивно используем API calls
        для обогащения ВСЕХ перспективных кандидатов.
        """
        available_calls = self.api_tracker.coingecko_daily_limit - self.api_tracker.coingecko_calls_today
        
        # При критическом остатке - только лучшие
        if available_calls < 20:
            return preliminary_score > 75
        # В воронке - мягкие требования для максимального охвата
        return preliminary_score > FUNNEL_CONFIG['api_calls_threshold']

    async def run_analysis_pipeline(self) -> List[dict]:
        """МНОГОУРОВНЕВАЯ ВОРОНКА АНАЛИЗА - Главный конвейер."""
        self.logger.info("🌊 ================ МНОГОУРОВНЕВАЯ ВОРОНКА START ================")
        alerts = []
        
        try:
            # === УРОВЕНЬ 1: ОБНАРУЖЕНИЕ (ШИРОКАЯ СЕТЬ) ===
            self.logger.info("🔍 УРОВЕНЬ 1: Поиск кандидатов с помощью PumpDiscoveryAgent...")
            initial_candidates = await self.discovery_agent.discover_tokens_async()
            self.logger.info(f"   ✅ Найдено {len(initial_candidates)} кандидатов из широкой сети.")

            if not initial_candidates:
                self.logger.warning("   ⚠️ Нет кандидатов для анализа.")
                return []

            # === УРОВЕНЬ 2: ОБОГАЩЕНИЕ И ПЕРВИЧНЫЙ СКОРИНГ ВСЕХ КАНДИДАТОВ ===
            self.logger.info(f"\n🔎 УРОВЕНЬ 2: Обогащение и скоринг ВСЕХ {len(initial_candidates)} кандидатов...")
            enriched_candidates = []
            
            for i, candidate in enumerate(initial_candidates):
                try:
                    # Прогресс для больших списков
                    if (i + 1) % 10 == 0:
                        self.logger.info(f"   📊 Обработано {i + 1}/{len(initial_candidates)} кандидатов...")
                    
                    # Быстрая проверка API limits
                    if not self.should_spend_api_calls(candidate.discovery_score):
                        self.logger.debug(f"   ⏭️ Пропускаем {candidate.base_token_symbol}: низкий предварительный балл ({candidate.discovery_score}).")
                        continue

                    # Быстрое обогащение данных
                    coingecko_data = self.coingecko_client.get_token_info_by_contract(
                        candidate.chain_id, candidate.base_token_address
                    )
                    self.api_tracker.coingecko_calls_today += 1
                    
                    goplus_data = self.goplus_client.get_token_security(
                        candidate.chain_id, candidate.base_token_address
                    )

                    found_narrative = find_narrative_in_categories(coingecko_data.get("categories", []))

                    indicators = RealisticPumpIndicators(
                        narrative_type=found_narrative if found_narrative else NarrativeType.UNKNOWN,
                        has_trending_narrative=bool(found_narrative),
                        coingecko_score=coingecko_data.get("community_score"),
                        is_honeypot=goplus_data.get('is_honeypot') == '1',
                        is_open_source=goplus_data.get('is_open_source') == '1',
                        buy_tax_percent=float(goplus_data.get('buy_tax', '1')) * 100,
                        sell_tax_percent=float(goplus_data.get('sell_tax', '1')) * 100
                    )

                    scoring_matrix = RealisticScoringMatrix(indicators=indicators)
                    final_analysis = scoring_matrix.get_detailed_analysis()
                    final_score = final_analysis['total_score']
                    
                    # Сохраняем обогащенного кандидата для сортировки
                    enriched_candidates.append({
                        'candidate': candidate,
                        'final_score': final_score,
                        'recommendation': final_analysis['recommendation'],
                        'analysis': final_analysis,
                        'indicators': indicators
                    })
                    
                except Exception as e:
                    self.logger.error(f"   ❌ Ошибка при обогащении токена {candidate.base_token_symbol}: {e}")
                    continue
            
            self.logger.info(f"   ✅ Успешно обогащено {len(enriched_candidates)} из {len(initial_candidates)} кандидатов.")
            
            if not enriched_candidates:
                self.logger.warning("   ⚠️ Нет обогащенных кандидатов для дальнейшего анализа.")
                return []

            # === УРОВЕНЬ 3: РАНЖИРОВАНИЕ И ОТБОР ТОПОВ ===
            self.logger.info(f"\n🏆 УРОВЕНЬ 3: Ранжирование {len(enriched_candidates)} обогащенных кандидатов...")
            
            # Сортируем по итоговому баллу (убывание)
            enriched_candidates.sort(key=lambda x: x['final_score'], reverse=True)
            
            # Показываем топ-10 для логов
            self.logger.info("\\n📊 ТОП-10 КАНДИДАТОВ ПО ИТОГОВОМУ БАЛЛУ:")
            for i, item in enumerate(enriched_candidates[:10]):
                candidate = item['candidate']
                score = item['final_score']
                recommendation = item['recommendation']
                self.logger.info(f"   #{i+1}: {candidate.base_token_symbol} - {score}/105 баллов ({recommendation})")
            
            # Выбираем топ-N для следующего уровня
            top_candidates = enriched_candidates[:FUNNEL_CONFIG['top_n_for_onchain']]
            
            self.logger.info(f"\\n🎯 Выбрано {len(top_candidates)} кандидатов для следующего уровня анализа.")
            if len(enriched_candidates) > FUNNEL_CONFIG['top_n_for_onchain']:
                worst_selected = top_candidates[-1]['final_score']
                best_rejected = enriched_candidates[FUNNEL_CONFIG['top_n_for_onchain']]['final_score']
                self.logger.info(f"   📏 Граница отбора: {worst_selected} баллов (отсечен {best_rejected} баллов)")

            # === УРОВЕНЬ 4: ГЛУБОКИЙ АНАЛИЗ (В БУДУЩЕМ - ONCHAIN) ===
            self.logger.info(f"\\n🔬 УРОВЕНЬ 4: Подготовка к глубокому анализу топ-{len(top_candidates)} кандидатов...")
            self.logger.info("   💡 Здесь будет OnChain анализ: Sterile Deployer, Holder Concentration, LP Locks...")
            
            # Пока что применяем дополнительную фильтрацию по баллам
            high_quality_candidates = [
                item for item in top_candidates 
                if item['final_score'] >= FUNNEL_CONFIG['min_score_for_alert']
            ]
            
            self.logger.info(f"   ✅ {len(high_quality_candidates)} кандидатов прошли фильтр качества (≥{FUNNEL_CONFIG['min_score_for_alert']} баллов)")

            # === УРОВЕНЬ 5: ГЕНЕРАЦИЯ АЛЕРТОВ ===
            self.logger.info(f"\\n🚨 УРОВЕНЬ 5: Генерация алертов для {len(high_quality_candidates)} финалистов...")
            
            for item in high_quality_candidates:
                recommendation = item['recommendation']
                if recommendation in ALERT_RECOMMENDATIONS:
                    alerts.append({
                        'token_symbol': item['candidate'].base_token_symbol,
                        'final_score': item['final_score'],
                        'recommendation': recommendation,
                        'details': item['analysis']
                    })
                    self.logger.info(f"   Алерт создан: {item['candidate'].base_token_symbol} ({item['final_score']}/105, {recommendation})")
                    
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка в многоуровневой воронке: {e}")

        # === ФИНАЛЬНАЯ СТАТИСТИКА ВОРОНКИ ===
        total_discovered = len(initial_candidates) if 'initial_candidates' in locals() else 0
        total_enriched = len(enriched_candidates) if 'enriched_candidates' in locals() else 0
        total_selected = len(top_candidates) if 'top_candidates' in locals() else 0
        total_alerts = len(alerts)
        
        self.logger.info(f"\\n📈 СТАТИСТИКА МНОГОУРОВНЕВОЙ ВОРОНКИ:")
        self.logger.info(f"   🔍 Уровень 1 (Discovery): {total_discovered} кандидатов")
        self.logger.info(f"   🔎 Уровень 2 (Enrichment): {total_enriched} обогащено")
        self.logger.info(f"   🏆 Уровень 3 (Top Selection): {total_selected} отобрано")
        self.logger.info(f"   🔬 Уровень 4 (Deep Analysis): {total_selected} подготовлено")
        self.logger.info(f"   🚨 Уровень 5 (Alerts): {total_alerts} алертов")
        
        if total_discovered > 0:
            funnel_efficiency = (total_alerts / total_discovered) * 100
            self.logger.info(f"   ⚡ Эффективность воронки: {funnel_efficiency:.1f}%")
            
            if total_enriched > 0:
                selection_rate = (total_selected / total_enriched) * 100
                self.logger.info(f"   🎯 Селективность: {selection_rate:.1f}% (топ-{FUNNEL_CONFIG['top_n_for_onchain']} из обогащенных)")
        
        self.logger.info("\\n✅ МНОГОУРОВНЕВАЯ ВОРОНКА ЗАВЕРШЕНА!")
        self.logger.info("🌊 ================ МНОГОУРОВНЕВАЯ ВОРОНКА END ================\\n")
        return alerts

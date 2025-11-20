"""
Simple Orchestrator - Crypto Multi-Agent System (v3 - Pump Detection MVP)

Координирует pump-specific агентов для реализации конвейера анализа:
1. Поиск pump-кандидатов с помощью PumpDiscoveryAgent.
2. Обогащение данных через CoinGecko (нарратив) и GoPlus (безопасность).
3. Финальная оценка с помощью RealisticScoringMatrix.
4. Генерация алертов для токенов с высоким и средним потенциалом.

Автор: Crypto Multi-Agent Team
"""
import asyncio
import logging
from typing import List

# --- Абсолютные импорты от корня проекта ---
from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent
from tools.market_data.coingecko_client import CoinGeckoClient
from tools.security.goplus_client import GoPlusClient
from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators, PumpRecommendationMVP
from agents.pump_analysis.pump_models import ApiUsageTracker, NarrativeType
from agents.pump_analysis.narrative_analyzer import find_narrative_in_categories
# from agents.social_intelligence.telegram_social_agent import TelegramSocialAgent  # ОТКЛЮЧЕНО


# --- КОНФИГУРАЦИЯ БИЗНЕС-ЛОГИКИ ---
# В перспективе, когда мы добавим Social Score, мы уберем отсюда MEDIUM_POTENTIAL
ALERT_RECOMMENDATIONS = [
    PumpRecommendationMVP.HIGH_POTENTIAL,
    PumpRecommendationMVP.MEDIUM_POTENTIAL  # Временно для MVP, чтобы тестировать алерты
]


class SimpleOrchestrator:
    """Координирует pump-detection pipeline."""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            self.discovery_agent = PumpDiscoveryAgent()
            self.coingecko_client = CoinGeckoClient()
            self.goplus_client = GoPlusClient()
            # self.telegram_agent = TelegramSocialAgent()  # ОТКЛЮЧЕНО пока
            self.api_tracker = ApiUsageTracker()
            self.logger.info("Оркестратор и клиенты успешно инициализированы.")
        except ValueError as e:
            self.logger.error(f"Критическая ошибка инициализации: {e}. Пожалуйста, проверьте ваш .env файл.")
            raise

    def should_spend_api_calls(self, preliminary_score: int) -> bool:
        """
        Решает, стоит ли тратить API вызовы.
        
        При запуске раз в час мы можем позволить себе больше API calls.
        """
        available_calls = self.api_tracker.coingecko_daily_limit - self.api_tracker.coingecko_calls_today
        
        # При критическом остатке - только лучшие
        if available_calls < 20:
            return preliminary_score > 75
        # При обычном запуске раз в час - мягкие требования
        return preliminary_score > 45

    async def run_analysis_pipeline(self) -> List[dict]:
        """Главный конвейер анализа."""
        self.logger.info("================ PUMP DETECTION PIPELINE START ================")
        alerts = []
        try:
            self.logger.info("🔍 Этап 1: Поиск кандидатов с помощью PumpDiscoveryAgent...")
            initial_candidates = await self.discovery_agent.discover_tokens_async()
            self.logger.info(f"Найдено {len(initial_candidates)} кандидатов. Начинаем глубокий анализ...")

            if not initial_candidates:
                return []

            self.logger.info("\n🔎 Этап 2: Обогащение данных и финальная оценка...")
            # Увеличили с 10 до 20, так как API calls достаточно при запуске раз в час
            MAX_TOKENS_FOR_DEEP_ANALYSIS = 20
            
            for candidate in initial_candidates[:MAX_TOKENS_FOR_DEEP_ANALYSIS]:
                try:
                    self.logger.info(f"--- Анализ для {candidate.base_token_symbol} (предв. балл: {candidate.discovery_score}) ---")
                    if not self.should_spend_api_calls(candidate.discovery_score):
                        self.logger.info(f"--- Пропускаем {candidate.base_token_symbol}: низкий предварительный балл ({candidate.discovery_score}).")
                        continue

                    coingecko_data = self.coingecko_client.get_token_info_by_contract(candidate.chain_id, candidate.base_token_address)
                    self.api_tracker.coingecko_calls_today += 1
                    goplus_data = self.goplus_client.get_token_security(candidate.chain_id, candidate.base_token_address)

                    found_narrative = find_narrative_in_categories(coingecko_data.get("categories", []))

                    indicators = RealisticPumpIndicators(
                        narrative_type=found_narrative if found_narrative else NarrativeType.UNKNOWN,
                        has_trending_narrative=bool(found_narrative),
                        coingecko_score=coingecko_data.get("community_score"),
                        is_honeypot=goplus_data.get('is_honeypot') == '1',
                        is_open_source=goplus_data.get('is_open_source') == '1',
                        buy_tax_percent=float(goplus_data.get('buy_tax', '1')) * 100,
                        sell_tax_percent=float(goplus_data.get('sell_tax', '1')) * 100
                        # Пока убрали social поля - можно вернуть потом
                        # alpha_channel_mentions=alpha_mentions,
                        # social_momentum_score=social_momentum
                    )

                    scoring_matrix = RealisticScoringMatrix(indicators=indicators)
                    final_analysis = scoring_matrix.get_detailed_analysis()
                    discovery_score = final_analysis['total_score']
                    recommendation = final_analysis['recommendation']

                    self.logger.info(f"✅ {candidate.base_token_symbol} проанализирован. Итоговый балл: {discovery_score}/100")
                    
                    # --- ГИБКАЯ ЛОГИКА АЛЕРТОВ ---
                    if recommendation in ALERT_RECOMMENDATIONS:
                        alerts.append({
                            'token_symbol': candidate.base_token_symbol,
                            'final_score': discovery_score,
                            'recommendation': recommendation,
                            'details': final_analysis
                        })
                except Exception as e:
                    self.logger.error(f"Ошибка при глубоком анализе токена {candidate.base_token_symbol}: {e}")
                    continue
        except Exception as e:
            self.logger.error(f"Критическая ошибка в pipeline: {e}")

        # Используем time.monotonic() для измерения времени
        duration = 0 # Placeholder for now
        self.logger.info(f"\n✅ Pipeline complete in {duration:.2f}s. Generated {len(alerts)} alerts.")
        self.logger.info("================ PUMP DETECTION PIPELINE END ================\n")
        return alerts
"""
Simple Orchestrator - Crypto Multi-Agent System (v7 - OPTIMIZED PIPELINE)

ОПТИМИЗИРОВАННАЯ АРХИТЕКТУРА: OnChain анализ перенесен в начало (дешевле API calls)
1. УРОВЕНЬ 1: Discovery - TheGraph (27x improvement vs DexScreener)  
2. УРОВЕНЬ 2: OnChain Analysis - RPC/Etherscan (дешево, массовый анализ)
3. УРОВЕНЬ 3: Enrichment - CoinGecko/GoPlus (дорого, только лучшие)
4. УРОВЕНЬ 4: Final Scoring - полная оценка с всеми данными
5. УРОВЕНЬ 5: Alert Generation - финальные рекомендации

AUTHOR: Crypto Multi-Agent Team (Pipeline Optimization v7)
DATE: 2025-09-26 - OnChain Early Analysis Architecture
OPTIMIZATION: More tokens analyzed with same API budget
"""
import asyncio
import logging
import os
import sys
from typing import List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Абсолютные импорты от корня проекта ---
# PRODUCTION UPGRADE: Replaced DexScreener with TheGraph (27x improvement)
from agents.discovery.thegraph_discovery_agent_part5 import TheGraphPumpDiscoveryAgent
from tools.market_data.coingecko_client import CoinGeckoClient
from tools.security.goplus_client import GoPlusClient
from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators, PumpRecommendationMVP, should_run_onchain_analysis
from agents.pump_analysis.pump_models import ApiUsageTracker, NarrativeType
from agents.pump_analysis.narrative_analyzer import find_narrative_in_categories
from agents.onchain.onchain_agent import OnChainAgent
from database.database_manager import DatabaseManager


# --- КОНФИГУРАЦИЯ МНОГОУРОВНЕВОЙ ВОРОНКИ ---
ALERT_RECOMMENDATIONS = [
    PumpRecommendationMVP.HIGH_POTENTIAL,
    PumpRecommendationMVP.MEDIUM_POTENTIAL  # Временно для MVP, чтобы тестировать алерты
]

# ТЕСТОВАЯ конфигурация воронки - ОГРАНИЧЕННАЯ ДЛЯ БЕЗОПАСНОГО ТЕСТИРОВАНИЯ
FUNNEL_CONFIG = {
    'min_discovery_score_for_onchain': 30,     # Минимальный Discovery score для OnChain
    'top_n_for_enrichment': 5,                 # ТЕСТОВОЕ ЗНАЧЕНИЕ: Только 5 токенов в CoinGecko!
    'min_score_for_alert': 40,                 # ПОНИЖЕН с 50 до 40 чтобы получить алерты!
    'max_onchain_candidates': 20,              # ТЕСТОВОЕ ЗНАЧЕНИЕ: Максимум 20 OnChain анализов за цикл
    'api_calls_threshold': 70                  # ПОВЫШЕН для экономии API calls
}


class SimpleOrchestrator:
    """Координирует pump-detection pipeline с многоуровневой воронкой."""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        try:
            # PRODUCTION UPGRADE: Using TheGraph instead of DexScreener
            self.discovery_agent = TheGraphPumpDiscoveryAgent()
            self.coingecko_client = CoinGeckoClient()
            self.goplus_client = GoPlusClient()
            # ИСПРАВЛЕНО: Включен реальный OnChain анализ
            self.onchain_agent = OnChainAgent(mock_mode=False)  # REAL MODE для настоящего анализа
            self.api_tracker = ApiUsageTracker()
            self.db_manager = DatabaseManager()
            self.logger.info("Оркестратор многоуровневой воронки с базой данных инициализирован (OnChain в РЕАЛЬНОМ режиме).")
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
        self.logger.info("================ МНОГОУРОВНЕВАЯ ВОРОНКА START ================")
        alerts = []
        
        # Initialize variables for statistics tracking
        initial_candidates = []
        onchain_analyzed_candidates = []  # ДОБАВЛЕНО для нового pipeline
        enriched_candidates = []
        top_candidates = []
        onchain_calls_used = 0
        enrichment_calls_used = 0  # ДОБАВЛЕНО для отслеживания
        
        # Создаем сессию в базе данных для отслеживания
        start_time = datetime.utcnow()
        session_id = self.db_manager.create_analysis_session(cycle_number=1)
        if session_id > 0:
            self.logger.info(f"✅ Создана сессия анализа с ID: {session_id}")
        else:
            self.logger.error("❌ Ошибка создания сессии анализа")
            return []
        
        try:
            # === УРОВЕНЬ 1: DISCOVERY (TheGraph) ===
            self.logger.info("УРОВЕНЬ 1: Discovery - TheGraph поиск кандидатов...")
            initial_candidates = await self.discovery_agent.discover_pump_candidates()
            self.logger.info(f"   Найдено {len(initial_candidates)} кандидатов из TheGraph")

            if not initial_candidates:
                self.logger.warning("   Нет кандидатов для анализа")
                return []

            # === УРОВЕНЬ 2: ONCHAIN ANALYSIS (Дешевый массовый глубокий анализ) ===
            self.logger.info(f"УРОВЕНЬ 2: OnChain анализ - ГЛУБОКИЙ массовый анализ безопасности...")
            
            # Фильтруем кандидатов по минимальному discovery score
            onchain_candidates = [
                candidate for candidate in initial_candidates 
                if candidate.discovery_score >= FUNNEL_CONFIG['min_discovery_score_for_onchain']
            ]
            
            # Ограничиваем количество для защиты от перегрузки
            if len(onchain_candidates) > FUNNEL_CONFIG['max_onchain_candidates']:
                # Сортируем по discovery_score и берем лучших
                onchain_candidates = sorted(
                    onchain_candidates, 
                    key=lambda x: x.discovery_score, 
                    reverse=True
                )[:FUNNEL_CONFIG['max_onchain_candidates']]
                self.logger.info(f"   Ограничено до {FUNNEL_CONFIG['max_onchain_candidates']} лучших кандидатов")
            
            self.logger.info(f"   🔍 ГЛУБОКИЙ OnChain анализ для {len(onchain_candidates)} кандидатов (discovery_score >= {FUNNEL_CONFIG['min_discovery_score_for_onchain']})")
            self.logger.info(f"   📊 Анализируем: LP блокировку, концентрацию держателей, риски rug pull...")
            
            # ГЛУБОКИЙ массовый OnChain анализ (согласно документации)
            onchain_analyzed_candidates.clear()
            onchain_calls_used = 0
            
            for i, candidate in enumerate(onchain_candidates):
                try:
                    if (i + 1) % 5 == 0:
                        self.logger.info(f"   ⚙️ OnChain прогресс: {i + 1}/{len(onchain_candidates)}")
                    
                    # Выполняем ГЛУБОКИЙ OnChain анализ (LP locks + holder concentration)
                    onchain_result = await self.onchain_agent.analyze_token(
                        network=candidate.chain_id,
                        token_address=candidate.base_token_address,
                        lp_address=candidate.pair_address
                    )
                    
                    onchain_calls_used += onchain_result.api_calls_used
                    
                    # Логируем результаты анализа
                    if onchain_result.lp_analysis:
                        safe_lp = onchain_result.lp_analysis.locked_percentage + onchain_result.lp_analysis.dead_percentage
                        self.logger.debug(f"      {candidate.base_token_symbol}: LP {safe_lp:.1f}% safe, риск: {onchain_result.overall_risk}")
                    
                    # Сохраняем кандидата с OnChain данными
                    onchain_analyzed_candidates.append({
                        'candidate': candidate,
                        'onchain_result': onchain_result,
                        'discovery_score': candidate.discovery_score
                    })
                    
                except Exception as e:
                    self.logger.debug(f"   ⚠️ OnChain ошибка для {candidate.base_token_symbol}: {e}")
                    # Сохраняем без OnChain данных (фильтруем позже)
                    onchain_analyzed_candidates.append({
                        'candidate': candidate,
                        'onchain_result': None,
                        'discovery_score': candidate.discovery_score
                    })
                    continue
            
            self.logger.info(f"   ✅ OnChain анализ завершен: {len(onchain_analyzed_candidates)} результатов")
            self.logger.info(f"   💰 Использовано {onchain_calls_used} RPC/Etherscan calls (дешево!)")
            
            # КРИТИЧЕСКИЙ ФИЛЬТР: Удаляем токены с CRITICAL риском rug pull
            safe_candidates = [
                item for item in onchain_analyzed_candidates
                if item['onchain_result'] is None or item['onchain_result'].overall_risk != "CRITICAL"
            ]
            
            filtered_count = len(onchain_analyzed_candidates) - len(safe_candidates)
            if filtered_count > 0:
                self.logger.info(f"   🛡️ Отфильтровано {filtered_count} токенов с CRITICAL риском rug pull")
            
            onchain_analyzed_candidates = safe_candidates

            # === УРОВЕНЬ 3: ENRICHMENT (Дорогие API только для лучших) ===
            self.logger.info(f"УРОВЕНЬ 3: Enrichment - дорогое обогащение лучших кандидатов...")
            
            if not onchain_analyzed_candidates:
                self.logger.warning("   Нет кандидатов после OnChain анализа")
                return []
            
            # Сортируем по discovery_score и берем лучших для дорогого Enrichment
            sorted_candidates = sorted(
                onchain_analyzed_candidates,
                key=lambda x: x['discovery_score'],
                reverse=True
            )
            
            enrichment_candidates = sorted_candidates[:FUNNEL_CONFIG['top_n_for_enrichment']]
            self.logger.info(f"   Отобрано {len(enrichment_candidates)} лучших кандидатов для дорогого CoinGecko/GoPlus анализа")
            
            enriched_candidates.clear()
            enrichment_calls_used = 0
            
            for i, candidate_data in enumerate(enrichment_candidates):
                candidate = candidate_data['candidate']  # Извлекаем кандидата из словаря
                try:
                    # Прогресс для больших списков
                    if (i + 1) % 10 == 0:
                        self.logger.info(f"   Обработано {i + 1}/{len(enrichment_candidates)} кандидатов...")
                    
                    # Быстрая проверка API limits
                    if not self.should_spend_api_calls(candidate.discovery_score):
                        self.logger.debug(f"   Пропускаем {candidate.base_token_symbol}: низкий предварительный балл ({candidate.discovery_score}).")
                        continue

                    # === ВКЛЮЧАЕМ COINGECKO/GOPLUS API CALLS ===
                    coingecko_data = self.coingecko_client.get_token_info_by_contract(
                        candidate.chain_id, candidate.base_token_address
                    )
                    self.api_tracker.coingecko_calls_today += 1
                    
                    goplus_data = self.goplus_client.get_token_security(
                        candidate.chain_id, candidate.base_token_address
                    )
                    
                    # Обработка "молодых" токенов
                    if not goplus_data or goplus_data.get('result') == 'Token not found':
                        self.logger.debug(f"   {candidate.base_token_symbol}: молодой токен, нейтральные значения")
                        goplus_data = {
                            'is_honeypot': '0',
                            'is_open_source': '0', 
                            'buy_tax': '0.05',  # 5% разумное значение
                            'sell_tax': '0.05',
                            'result': 'young_token_neutral'
                        }

                    # Анализ нарратива
                    found_narrative = find_narrative_in_categories(coingecko_data.get("categories", []))
                    
                    # Market Cap фильтр
                    market_cap = coingecko_data.get('market_cap')
                    if market_cap:
                        if market_cap < 200_000:  # Минимум $200k
                            self.logger.debug(f"   Отфильтрован {candidate.base_token_symbol}: слишком маленький market_cap (${market_cap:,.0f})")
                            continue
                        elif market_cap > 50_000_000:  # Максимум $50M
                            self.logger.debug(f"   Отфильтрован {candidate.base_token_symbol}: слишком большой market_cap (${market_cap:,.0f})")
                            continue

                    indicators = RealisticPumpIndicators(
                        # === ИСПОЛЬЗУЕМ DISCOVERY DATA ===
                        discovery_score=candidate.discovery_score,  # Добавляем Discovery баллы!
                        
                        # === ОТКЛЮЧЕННЫЕ ВРЕМЕННО ===
                        narrative_type=found_narrative if found_narrative else NarrativeType.UNKNOWN,
                        has_trending_narrative=bool(found_narrative),
                        coingecko_score=coingecko_data.get("community_score"),
                        is_honeypot=goplus_data.get('is_honeypot') == '1',
                        is_open_source=goplus_data.get('is_open_source') == '1',
                        buy_tax_percent=float(goplus_data.get('buy_tax', '0.01')) * 100,  # 1% по умолчанию
                        sell_tax_percent=float(goplus_data.get('sell_tax', '0.01')) * 100  # 1% по умолчанию
                    )

                    scoring_matrix = RealisticScoringMatrix(indicators=indicators)
                    final_analysis = scoring_matrix.get_detailed_analysis()
                    final_score = final_analysis['total_score']
                    
                    # Сохраняем обогащенного кандидата для сортировки (БД временно отключена)
                    enriched_candidates.append({
                        'candidate': candidate,
                        'final_score': final_score,
                        'recommendation': final_analysis['recommendation'],
                        'analysis': final_analysis,
                        'indicators': indicators
                    })
                    
                except Exception as e:
                    self.logger.error(f"   Ошибка при обогащении токена {candidate.base_token_symbol}: {e}")
                    continue
            
            self.logger.info(f"   Успешно обогащено {len(enriched_candidates)} из {len(enrichment_candidates)} лучших кандидатов.")
            
            if not enriched_candidates:
                self.logger.warning("   Нет обогащенных кандидатов для дальнейшего анализа.")
                return []

            # === УРОВЕНЬ 3: РАНЖИРОВАНИЕ И ОТБОР ===
            self.logger.info(f"УРОВЕНЬ 3: Ранжирование {len(enriched_candidates)} обогащенных кандидатов...")
            
            # Сортируем по итоговому баллу (убывание)
            enriched_candidates.sort(key=lambda x: x['final_score'], reverse=True)
            
            # Показываем топ-10 для логов
            self.logger.info("ТОП-10 КАНДИДАТОВ ПО ИТОГОВОМУ БАЛЛУ:")
            for i, item in enumerate(enriched_candidates[:10]):
                candidate = item['candidate']
                score = item['final_score']
                recommendation = item['recommendation']
                self.logger.info(f"   #{i+1}: {candidate.base_token_symbol} - {score}/105 баллов ({recommendation})")
            
            # ИСПРАВЛЕНО: Определяем top_candidates правильно
            top_candidates = enriched_candidates  # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ!
            
            # === УРОВЕНЬ 4: FINAL SCORING (Финальная оценка с OnChain данными) ===
            self.logger.info(f"УРОВЕНЬ 4: Final Scoring - пересчет баллов с OnChain данными...")
            
            # OnChain анализ УЖЕ ВЫПОЛНЕН на УРОВНЕ 2!
            # Здесь мы только пересчитываем scores с уже имеющимися OnChain данными
            
            final_scored_candidates = []
            
            for i, item in enumerate(enriched_candidates):
                try:
                    candidate = item['candidate']
                    
                    # Получаем OnChain данные из УРОВНЯ 2
                    # Находим соответствующий OnChain результат
                    onchain_data = next(
                        (oc for oc in onchain_analyzed_candidates 
                         if oc['candidate'].base_token_address == candidate.base_token_address),
                        None
                    )
                    
                    if onchain_data and onchain_data.get('onchain_result'):
                        # Добавляем OnChain данные к indicators
                        updated_indicators = item['indicators']
                        updated_indicators.onchain_analysis = onchain_data['onchain_result']
                        
                        # Пересчитываем score с OnChain данными
                        updated_matrix = RealisticScoringMatrix(indicators=updated_indicators)
                        updated_analysis = updated_matrix.get_detailed_analysis()
                        updated_score = updated_analysis['total_score']
                        
                        # Логируем изменение балла
                        score_change = updated_score - item['final_score']
                        if score_change != 0:
                            self.logger.debug(f"   {candidate.base_token_symbol}: {item['final_score']} → {updated_score} ({score_change:+d} от OnChain)")
                        
                        final_scored_candidates.append({
                            'candidate': candidate,
                            'final_score': updated_score,
                            'recommendation': updated_analysis['recommendation'],
                            'analysis': updated_analysis,
                            'indicators': updated_indicators,
                            'onchain_result': onchain_data['onchain_result']
                        })
                    else:
                        # Нет OnChain данных - используем без них
                        final_scored_candidates.append(item)
                        
                except Exception as e:
                    self.logger.error(f"   Ошибка пересчета для {candidate.base_token_symbol}: {e}")
                    final_scored_candidates.append(item)
                    continue
            
            # Пересортировка после пересчета
            final_scored_candidates.sort(key=lambda x: x['final_score'], reverse=True)
            
            self.logger.info(f"   ✅ Final scoring завершен: {len(final_scored_candidates)} кандидатов")
            
            # Применяем финальный фильтр качества
            high_quality_candidates = [
                item for item in final_scored_candidates 
                if item['final_score'] >= FUNNEL_CONFIG['min_score_for_alert']
            ]
            
            self.logger.info(f"   {len(high_quality_candidates)} кандидатов прошли финальный фильтр (>={FUNNEL_CONFIG['min_score_for_alert']} баллов)")

            # === УРОВЕНЬ 5: ГЕНЕРАЦИЯ АЛЕРТОВ ===
            self.logger.info(f"УРОВЕНЬ 5: Генерация алертов для {len(high_quality_candidates)} финалистов...")
            
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
            self.logger.error(f"Критическая ошибка в многоуровневой воронке: {e}")

        # === ФИНАЛЬНАЯ СТАТИСТИКА ВОРОНКИ ===
        total_discovered = len(initial_candidates) if 'initial_candidates' in locals() else 0
        total_enriched = len(enriched_candidates) if 'enriched_candidates' in locals() else 0
        total_selected = len(top_candidates) if 'top_candidates' in locals() else 0
        total_alerts = len(alerts)
        
        self.logger.info(f"СТАТИСТИКА МНОГОУРОВНЕВОЙ ВОРОНКИ:")
        self.logger.info(f"   Уровень 1 (Discovery): {total_discovered} кандидатов")
        self.logger.info(f"   Уровень 2 (OnChain Analysis): {onchain_calls_used} RPC/Etherscan calls")
        self.logger.info(f"   Уровень 3 (Enrichment): {total_enriched} обогащено (CoinGecko/GoPlus)")
        self.logger.info(f"   Уровень 4 (Final Scoring): {total_selected} с финальными баллами")
        self.logger.info(f"   Уровень 5 (Alerts): {total_alerts} алертов")
        
        if total_discovered > 0:
            funnel_efficiency = (total_alerts / total_discovered) * 100
            self.logger.info(f"   Эффективность воронки: {funnel_efficiency:.1f}%")
            
            if total_enriched > 0:
                selection_rate = (total_selected / total_enriched) * 100
                self.logger.info(f"   Селективность: {selection_rate:.1f}% (топ-{FUNNEL_CONFIG['top_n_for_enrichment']} из обогащенных)")
        
        self.logger.info("МНОГОУРОВНЕВАЯ ВОРОНКА ЗАВЕРШЕНА!")
        self.logger.info("================ МНОГОУРОВНЕВАЯ ВОРОНКА END ================")
        return alerts

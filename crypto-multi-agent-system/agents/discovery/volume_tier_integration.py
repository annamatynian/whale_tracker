"""
Volume Integration with TIER SYSTEM - замена балльной системы на tier'ы + теги
Интегрирует TierScoringMatrix с volume analysis pipeline

Author: Tier Integration v1.0
Date: 2025-01-20
"""

import asyncio
import logging
import requests
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Импорт volume metrics
from agents.discovery.volume_metrics_extension import (
    build_token_day_data_query,
    calculate_volume_metrics_from_daily_data,
    prepare_day_data_variables,
    apply_volume_filters
)

# NEW: Импорт Tier System
from agents.pump_analysis import TierScoringMatrix, TierAnalysisResult


class VolumeMetricsFetcher:
    """
    Класс для получения и расчета volume metrics для пар.
    Теперь интегрируется с Tier System вместо балльной системы.
    """
    
    def __init__(self, graph_api_key: str, graph_gateway_base: str = "https://gateway.thegraph.com/api"):
        """
        Инициализация fetcher.
        
        Args:
            graph_api_key: The Graph API key
            graph_gateway_base: Base URL для gateway
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.graph_api_key = graph_api_key
        self.graph_gateway_base = graph_gateway_base
        self.query_template = build_token_day_data_query()
        
        # NEW: Tier scoring matrix
        self.tier_matrix = TierScoringMatrix()
        
        # Статистика
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "pairs_with_acceleration": 0,
            "pairs_filtered_out": 0,
            # NEW: Tier statistics
            "tier_premium": 0,
            "tier_strong": 0,
            "tier_speculative": 0,
            "tier_avoid": 0
        }
    
    def _build_subgraph_url(self, subgraph_id: str) -> str:
        """Построить URL для subgraph."""
        return f"{self.graph_gateway_base}/{self.graph_api_key}/subgraphs/id/{subgraph_id}"
    
    async def fetch_token_day_data(
        self, 
        token_address: str, 
        subgraph_id: str,
        days_back: int = 30
    ) -> Optional[Dict[str, Any]]:
        """
        Запросить tokenDayData для конкретного токена.
        
        Args:
            token_address: адрес токена
            subgraph_id: ID subgraph для запроса
            days_back: сколько дней истории запрашивать
            
        Returns:
            Dict с volume metrics или None при ошибке
        """
        try:
            self.stats["total_requests"] += 1
            
            # Подготовить URL и переменные
            url = self._build_subgraph_url(subgraph_id)
            variables = prepare_day_data_variables(token_address, days_back)
            
            # Сделать запрос
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(
                    url,
                    json={"query": self.query_template, "variables": variables},
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "errors" not in data:
                    token_day_data = data.get("data", {}).get("tokenDayDatas", [])
                    
                    if token_day_data:
                        # Рассчитать метрики
                        metrics = calculate_volume_metrics_from_daily_data(token_day_data)
                        
                        # Применить фильтры
                        passed, reason = apply_volume_filters(metrics)
                        
                        # Обновить статистику
                        self.stats["successful_requests"] += 1
                        if metrics['is_accelerating']:
                            self.stats["pairs_with_acceleration"] += 1
                        if not passed:
                            self.stats["pairs_filtered_out"] += 1
                        
                        return {
                            "success": True,
                            "metrics": metrics,
                            "passed_filters": passed,
                            "filter_reason": reason,
                            "raw_data_points": len(token_day_data)
                        }
                    else:
                        self.logger.debug(f"No tokenDayData found for {token_address[:10]}...")
                        self.stats["failed_requests"] += 1
                        return None
                else:
                    error_msg = data['errors'][0]['message']
                    self.logger.warning(f"GraphQL error for {token_address[:10]}...: {error_msg}")
                    self.stats["failed_requests"] += 1
                    return None
            else:
                self.logger.warning(f"HTTP {response.status_code} for {token_address[:10]}...")
                self.stats["failed_requests"] += 1
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching volume data for {token_address[:10]}...: {e}")
            self.stats["failed_requests"] += 1
            return None
    
    def _create_tier_analysis_from_volume_and_security(
        self,
        volume_metrics: Dict[str, Any],
        discovery_report: Any,
        data_completeness: float = 0.5  # Пока только volume + security
    ) -> TierAnalysisResult:
        """
        Создать tier анализ на основе volume метрик и security данных из discovery report.
        
        Args:
            volume_metrics: Метрики объема
            discovery_report: TokenDiscoveryReport с security данными
            data_completeness: Полнота данных (0-1)
            
        Returns:
            TierAnalysisResult
        """
        # Извлечь security данные из discovery report (если есть)
        is_honeypot = getattr(discovery_report, 'is_honeypot', False)
        is_open_source = getattr(discovery_report, 'is_open_source', False)
        buy_tax = getattr(discovery_report, 'buy_tax', 5.0)
        sell_tax = getattr(discovery_report, 'sell_tax', 5.0)
        
        # Создать tier analysis
        tier_result = self.tier_matrix.analyze(
            # Volume metrics
            volume_ratio=volume_metrics.get('volume_ratio', 0),
            ratio_healthy=volume_metrics.get('volume_ratio_healthy', False),
            ratio_overheated=volume_metrics.get('volume_ratio_overheated', False),
            ratio_dead=volume_metrics.get('volume_ratio_dead', False),
            is_accelerating=volume_metrics.get('is_accelerating', False),
            acceleration_factor=volume_metrics.get('acceleration_factor', 0),
            volume_h1=volume_metrics.get('avg_volume_last_1_hour', 0),
            
            # Security data (from discovery report)
            is_honeypot=is_honeypot,
            is_open_source=is_open_source,
            buy_tax=buy_tax,
            sell_tax=sell_tax,
            
            # OnChain data (пока нет - будет добавлено позже)
            onchain_analysis=None,
            
            # Metadata
            data_completeness=data_completeness,
            token_address=discovery_report.base_token_address,
            token_symbol=getattr(discovery_report, 'base_token_symbol', 'UNKNOWN'),
            chain=getattr(discovery_report, 'chain_id', 'unknown')
        )
        
        return tier_result
    
    async def enrich_discovery_report_with_tier_analysis(
        self,
        discovery_report: Any,  # TokenDiscoveryReport
        subgraph_id: str
    ) -> Tuple[Any, Optional[TierAnalysisResult]]:
        """
        Обогатить discovery report tier анализом вместо баллов.
        
        Args:
            discovery_report: TokenDiscoveryReport объект
            subgraph_id: ID subgraph для запроса
            
        Returns:
            (enriched_report, tier_analysis или None)
        """
        # Запросить volume данные
        volume_data = await self.fetch_token_day_data(
            discovery_report.base_token_address,
            subgraph_id
        )
        
        tier_result = None
        
        if volume_data and volume_data["success"]:
            # Добавить метрики в report
            discovery_report.volume_metrics = volume_data["metrics"]
            discovery_report.volume_filters_passed = volume_data["passed_filters"]
            discovery_report.volume_filter_reason = volume_data["filter_reason"]
            
            # NEW: Создать tier analysis
            tier_result = self._create_tier_analysis_from_volume_and_security(
                volume_data["metrics"],
                discovery_report,
                data_completeness=0.6  # Volume + Security, но без OnChain
            )
            
            # Сохранить tier analysis в report
            discovery_report.tier_analysis = tier_result
            
            # Обновить статистику tier'ов
            tier_name = f"tier_{tier_result.tier.value.lower()}"
            if tier_name in self.stats:
                self.stats[tier_name] += 1
            
            # LEGACY: Для обратной совместимости добавляем бонусные баллы
            # (можно будет убрать когда полностью перейдем на tier'ы)
            metrics = volume_data["metrics"]
            bonus_points = 0
            bonus_reasons = []
            
            if metrics["is_accelerating"]:
                acceleration_bonus = min(15, int(metrics["acceleration_factor"] * 10))
                bonus_points += acceleration_bonus
                bonus_reasons.append(f"🔥 Volume acceleration {metrics['acceleration_factor']:.2f}x (+{acceleration_bonus})")
            
            if metrics.get("volume_ratio_healthy", False):
                bonus_points += 5
                bonus_reasons.append(f"✅ Healthy volume ratio {metrics['volume_ratio']:.2f} (+5)")
            
            if metrics.get("volume_ratio_overheated", False):
                bonus_reasons.append(f"⚠️ Unusually high volume ratio {metrics['volume_ratio']:.2f}")
            
            if bonus_points > 0:
                discovery_report.discovery_score += bonus_points
                discovery_report.discovery_reason += "; " + "; ".join(bonus_reasons)
        else:
            # Нет данных - добавляем пустые метрики
            discovery_report.volume_metrics = None
            discovery_report.volume_filters_passed = False
            discovery_report.volume_filter_reason = "No historical data available"
            discovery_report.tier_analysis = None
        
        return discovery_report, tier_result
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику работы (включая tier distribution)."""
        stats = self.stats.copy()
        
        if stats["total_requests"] > 0:
            stats["success_rate"] = (stats["successful_requests"] / stats["total_requests"]) * 100
            
            if stats["successful_requests"] > 0:
                stats["acceleration_rate"] = (stats["pairs_with_acceleration"] / stats["successful_requests"]) * 100
                stats["filter_pass_rate"] = ((stats["successful_requests"] - stats["pairs_filtered_out"]) / stats["successful_requests"]) * 100
        
        # NEW: Tier distribution
        total_tiers = (
            stats["tier_premium"] + 
            stats["tier_strong"] + 
            stats["tier_speculative"] + 
            stats["tier_avoid"]
        )
        
        if total_tiers > 0:
            stats["tier_distribution"] = {
                "premium": f"{(stats['tier_premium'] / total_tiers) * 100:.1f}%",
                "strong": f"{(stats['tier_strong'] / total_tiers) * 100:.1f}%",
                "speculative": f"{(stats['tier_speculative'] / total_tiers) * 100:.1f}%",
                "avoid": f"{(stats['tier_avoid'] / total_tiers) * 100:.1f}%"
            }
        
        return stats


# === ПАТЧ ДЛЯ ИНТЕГРАЦИИ С PART4 ===

async def patch_part4_with_tier_analysis(
    discovery_reports: list,
    subgraph_id: str,
    graph_api_key: str,
    max_concurrent: int = 3
) -> tuple[list, dict]:
    """
    Патч для Part4: добавляет tier analysis ко всем discovery reports.
    
    Args:
        discovery_reports: список TokenDiscoveryReport объектов
        subgraph_id: ID subgraph
        graph_api_key: API key
        max_concurrent: максимум параллельных запросов
        
    Returns:
        (enriched_reports, stats)
    """
    logger = logging.getLogger("TierAnalysisPatch")
    
    if not discovery_reports:
        logger.warning("No discovery reports to enrich")
        return [], {}
    
    logger.info(f"Enriching {len(discovery_reports)} reports with TIER ANALYSIS...")
    
    # Создать fetcher
    fetcher = VolumeMetricsFetcher(graph_api_key)
    
    # Обогатить каждый report
    enriched_reports = []
    tier_results = []
    
    for i, report in enumerate(discovery_reports):
        try:
            if (i + 1) % 10 == 0:
                logger.info(f"  Progress: {i + 1}/{len(discovery_reports)}")
            
            enriched_report, tier_result = await fetcher.enrich_discovery_report_with_tier_analysis(
                report, 
                subgraph_id
            )
            
            enriched_reports.append(enriched_report)
            if tier_result:
                tier_results.append(tier_result)
            
            # Небольшая задержка между запросами
            await asyncio.sleep(0.3)
            
        except Exception as e:
            logger.error(f"Failed to enrich report {i}: {e}")
            enriched_reports.append(report)
    
    # Получить статистику
    stats = fetcher.get_stats()
    
    logger.info(f"Tier analysis enrichment complete: {stats['successful_requests']}/{stats['total_requests']} successful")
    logger.info(f"  Tier distribution:")
    if "tier_distribution" in stats:
        for tier, pct in stats["tier_distribution"].items():
            logger.info(f"    {tier.upper()}: {pct}")
    
    return enriched_reports, stats


# === HELPER FUNCTION: Фильтрация по tier'ам ===

def filter_reports_by_tier(
    enriched_reports: list,
    min_tier: str = "SPECULATIVE",
    exclude_avoid: bool = True
) -> list:
    """
    Отфильтровать reports по tier'у.
    
    Args:
        enriched_reports: Список reports с tier_analysis
        min_tier: Минимальный tier ("PREMIUM", "STRONG", "SPECULATIVE")
        exclude_avoid: Исключить AVOID tier
        
    Returns:
        Отфильтрованный список
    """
    tier_order = {
        "PREMIUM": 4,
        "STRONG": 3,
        "SPECULATIVE": 2,
        "AVOID": 1
    }
    
    min_tier_value = tier_order.get(min_tier.upper(), 2)
    
    filtered = []
    for report in enriched_reports:
        if hasattr(report, 'tier_analysis') and report.tier_analysis:
            tier_value = tier_order.get(report.tier_analysis.tier.value, 1)
            
            if exclude_avoid and report.tier_analysis.tier.value == "AVOID":
                continue
            
            if tier_value >= min_tier_value:
                filtered.append(report)
        # Reports без tier analysis тоже включаем (на случай ошибок)
        elif not hasattr(report, 'tier_analysis'):
            filtered.append(report)
    
    return filtered


# === ТЕСТОВАЯ ФУНКЦИЯ ===

async def test_tier_integration():
    """Тест tier интеграции с реальным API."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("GRAPH_API_KEY")
    uniswap_v2_id = os.getenv("UNISWAP_V2_ID")
    
    if not api_key or not uniswap_v2_id:
        print("⚠️ GRAPH_API_KEY or UNISWAP_V2_ID not found in .env")
        print("   Skipping real API test")
        return
    
    print("=" * 70)
    print("TEST: Tier Integration with Volume Analysis")
    print("=" * 70)
    
    fetcher = VolumeMetricsFetcher(api_key)
    
    # Тестовый токен (USDC)
    test_token = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    
    print(f"\nFetching volume data for token: {test_token[:10]}...")
    
    volume_data = await fetcher.fetch_token_day_data(test_token, uniswap_v2_id)
    
    if volume_data and volume_data["success"]:
        print("\n✓ Volume data fetched successfully")
        
        # Создать mock discovery report
        class MockReport:
            base_token_address = test_token
            base_token_symbol = "USDC"
            chain_id = "ethereum"
            is_honeypot = False
            is_open_source = True
            buy_tax = 0.0
            sell_tax = 0.0
        
        mock_report = MockReport()
        
        # Создать tier analysis
        tier_result = fetcher._create_tier_analysis_from_volume_and_security(
            volume_data["metrics"],
            mock_report,
            data_completeness=0.6
        )
        
        # Показать результат
        print("\n" + "=" * 70)
        print(tier_result.get_detailed_report())
        print("=" * 70)
        
    else:
        print("\n✗ Failed to fetch volume data")
    
    print("\n✅ Tier integration test complete!")


if __name__ == "__main__":
    asyncio.run(test_tier_integration())

"""
Volume Integration Patch - добавляет volume metrics в существующий discovery pipeline
Минимально инвазивная интеграция с Part4

Author: Phase 1 Volume Acceleration integration
Version: 1.0
"""

import asyncio
import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime

# Импорт нашего нового модуля
from agents.discovery.volume_metrics_extension import (
    build_token_day_data_query,
    calculate_volume_metrics_from_daily_data,
    prepare_day_data_variables,
    apply_volume_filters
)


class VolumeMetricsFetcher:
    """
    Класс для получения и расчета volume metrics для пар.
    Интегрируется с существующей архитектурой TheGraph.
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
        
        # Статистика
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "pairs_with_acceleration": 0,
            "pairs_filtered_out": 0
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
    
    async def enrich_discovery_report_with_volume_metrics(
        self,
        discovery_report: Any,  # TokenDiscoveryReport
        subgraph_id: str
    ) -> Any:
        """
        Обогатить существующий discovery report volume метриками.
        
        Args:
            discovery_report: TokenDiscoveryReport объект
            subgraph_id: ID subgraph для запроса
            
        Returns:
            Обогащенный TokenDiscoveryReport с volume_metrics атрибутом
        """
        # Запросить volume данные для BASE TOKEN (не пары!)
        volume_data = await self.fetch_token_day_data(
            discovery_report.base_token_address,  # ВАЖНО: токен, не пара!
            subgraph_id
        )
        
        if volume_data and volume_data["success"]:
            # Добавить метрики в report (динамически)
            discovery_report.volume_metrics = volume_data["metrics"]
            discovery_report.volume_filters_passed = volume_data["passed_filters"]
            discovery_report.volume_filter_reason = volume_data["filter_reason"]
            
            metrics = volume_data["metrics"]
            bonus_points = 0
            bonus_reasons = []
            
            # Бонус 1: Ускорение объема (+10-15 баллов)
            if metrics["is_accelerating"]:
                acceleration_bonus = min(15, int(metrics["acceleration_factor"] * 10))
                bonus_points += acceleration_bonus
                bonus_reasons.append(f"🔥 Volume acceleration {metrics['acceleration_factor']:.2f}x (+{acceleration_bonus})")
            
            # Бонус 2: Volume Ratio Health Check (+5 баллов за здоровый ratio)
            if metrics.get("volume_ratio_healthy", False):
                bonus_points += 5
                bonus_reasons.append(f"✅ Healthy volume ratio {metrics['volume_ratio']:.2f} (+5)")
            
            # Предупреждение о перегреве (не штрафуем, но отмечаем)
            if metrics.get("volume_ratio_overheated", False):
                bonus_reasons.append(f"⚠️ Unusually high volume ratio {metrics['volume_ratio']:.2f}")
            
            # Применить бонусы
            if bonus_points > 0:
                discovery_report.discovery_score += bonus_points
                discovery_report.discovery_reason += "; " + "; ".join(bonus_reasons)
        else:
            # Нет данных - добавляем пустые метрики
            discovery_report.volume_metrics = None
            discovery_report.volume_filters_passed = False
            discovery_report.volume_filter_reason = "No historical data available"
        
        return discovery_report
    
    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику работы."""
        stats = self.stats.copy()
        
        if stats["total_requests"] > 0:
            stats["success_rate"] = (stats["successful_requests"] / stats["total_requests"]) * 100
            
            if stats["successful_requests"] > 0:
                stats["acceleration_rate"] = (stats["pairs_with_acceleration"] / stats["successful_requests"]) * 100
                stats["filter_pass_rate"] = ((stats["successful_requests"] - stats["pairs_filtered_out"]) / stats["successful_requests"]) * 100
        
        return stats


# === ПАТЧ ДЛЯ ИНТЕГРАЦИИ С PART4 ===

async def patch_part4_with_volume_metrics(
    discovery_reports: list,
    subgraph_id: str,
    graph_api_key: str,
    max_concurrent: int = 3
) -> tuple[list, dict]:
    """
    Патч для Part4: добавляет volume metrics ко всем discovery reports.
    
    Args:
        discovery_reports: список TokenDiscoveryReport объектов
        subgraph_id: ID subgraph
        graph_api_key: API key
        max_concurrent: максимум параллельных запросов
        
    Returns:
        (enriched_reports, stats)
    """
    logger = logging.getLogger("VolumeMetricsPatch")
    
    if not discovery_reports:
        logger.warning("No discovery reports to enrich")
        return [], {}
    
    logger.info(f"Enriching {len(discovery_reports)} reports with volume metrics...")
    
    # Создать fetcher
    fetcher = VolumeMetricsFetcher(graph_api_key)
    
    # Обогатить каждый report (с контролем параллелизма)
    enriched_reports = []
    
    # Простая реализация: последовательно (для безопасности)
    for i, report in enumerate(discovery_reports):
        try:
            if (i + 1) % 10 == 0:
                logger.info(f"  Progress: {i + 1}/{len(discovery_reports)}")
            
            enriched_report = await fetcher.enrich_discovery_report_with_volume_metrics(
                report, 
                subgraph_id
            )
            enriched_reports.append(enriched_report)
            
            # Небольшая задержка между запросами
            await asyncio.sleep(0.3)
            
        except Exception as e:
            logger.error(f"Failed to enrich report {i}: {e}")
            enriched_reports.append(report)  # Добавляем без обогащения
    
    # Получить статистику
    stats = fetcher.get_stats()
    
    logger.info(f"Volume enrichment complete: {stats['successful_requests']}/{stats['total_requests']} successful")
    logger.info(f"  Pairs with acceleration: {stats.get('pairs_with_acceleration', 0)}")
    logger.info(f"  Pairs filtered out: {stats.get('pairs_filtered_out', 0)}")
    
    return enriched_reports, stats


# === ТЕСТОВАЯ ФУНКЦИЯ ===

async def test_volume_integration():
    """Тест интеграции с реальным subgraph (если есть API key)."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.getenv("GRAPH_API_KEY")
    uniswap_v2_id = os.getenv("UNISWAP_V2_ID")
    
    if not api_key or not uniswap_v2_id:
        print("⚠️ GRAPH_API_KEY or UNISWAP_V2_ID not found in .env")
        print("   Skipping real API test")
        return
    
    print("=" * 60)
    print("TEST: Volume Integration with Real API")
    print("=" * 60)
    
    fetcher = VolumeMetricsFetcher(api_key)
    
    # Тестовый адрес токена (USDC на Ethereum)
    # Это просто для демонстрации - в продакшене мы получаем адреса из discovery
    test_token = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"  # USDC
    
    print(f"\nFetching volume data for token: {test_token[:10]}...")
    
    volume_data = await fetcher.fetch_token_day_data(test_token, uniswap_v2_id)
    
    if volume_data:
        print("\n✓ Successfully fetched volume data:")
        print(f"   Raw data points: {volume_data['raw_data_points']}")
        
        metrics = volume_data['metrics']
        print(f"\n   Metrics:")
        print(f"      avg_7d: ${metrics['avg_volume_last_7_days']:,.0f}")
        print(f"      avg_30d: ${metrics['avg_volume_last_30_days']:,.0f}")
        print(f"      acceleration: {metrics['acceleration_factor']:.2f}x")
        print(f"      is_accelerating: {metrics['is_accelerating']}")
        print(f"      volume_ratio: {metrics['volume_ratio']:.3f}")
        print(f"      ratio_healthy: {metrics['volume_ratio_healthy']}")
        
        print(f"\n   Filter result: {'✓ PASS' if volume_data['passed_filters'] else '✗ FAIL'}")
        print(f"   Reason: {volume_data['filter_reason']}")
    else:
        print("\n✗ Failed to fetch volume data")
    
    # Показать статистику
    stats = fetcher.get_stats()
    print(f"\n   Fetcher stats: {stats}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Запустить тест
    asyncio.run(test_volume_integration())

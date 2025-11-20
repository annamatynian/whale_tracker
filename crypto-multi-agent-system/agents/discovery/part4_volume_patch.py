"""
Part4 Volume Enrichment Integration
Добавляет volume metrics в существующий discovery pipeline

Usage:
    from agents.discovery.part4_volume_patch import enrich_reports_with_volume
    
    enriched_reports = await enrich_reports_with_volume(
        discovery_reports,
        subgraph_id,
        graph_api_key
    )
"""

import asyncio
import logging
from typing import List, Dict, Any

from agents.discovery.base_discovery_agent import TokenDiscoveryReport
from agents.discovery.volume_integration_patch import VolumeMetricsFetcher


async def enrich_reports_with_volume(
    discovery_reports: List[TokenDiscoveryReport],
    subgraph_id: str,
    graph_api_key: str,
    max_concurrent: int = 3
) -> tuple[List[TokenDiscoveryReport], Dict[str, Any]]:
    """
    Обогатить discovery reports volume metrics из tokenDayData.
    
    Args:
        discovery_reports: список TokenDiscoveryReport из Part4
        subgraph_id: ID subgraph для запросов
        graph_api_key: The Graph API key
        max_concurrent: максимум параллельных запросов (для безопасности API)
        
    Returns:
        (enriched_reports, enrichment_stats)
    """
    logger = logging.getLogger("Part4VolumeEnrichment")
    
    if not discovery_reports:
        logger.warning("No discovery reports to enrich")
        return [], {}
    
    logger.info(f"🔍 Enriching {len(discovery_reports)} reports with volume metrics...")
    
    # Создать fetcher
    fetcher = VolumeMetricsFetcher(graph_api_key)
    
    # Обогатить каждый report
    enriched_reports = []
    
    for i, report in enumerate(discovery_reports):
        try:
            # Прогресс каждые 10 токенов
            if (i + 1) % 10 == 0:
                logger.info(f"  Progress: {i + 1}/{len(discovery_reports)}")
            
            # Запросить volume данные для base token
            enriched_report = await fetcher.enrich_discovery_report_with_volume_metrics(
                report, 
                subgraph_id
            )
            
            enriched_reports.append(enriched_report)
            
            # Небольшая задержка между запросами (rate limiting)
            await asyncio.sleep(0.3)
            
        except Exception as e:
            logger.error(f"Failed to enrich report {i} ({report.base_token_symbol}): {e}")
            # Добавляем без обогащения
            enriched_reports.append(report)
    
    # Получить статистику
    stats = fetcher.get_stats()
    
    logger.info(f"✅ Volume enrichment complete:")
    logger.info(f"  Successful requests: {stats['successful_requests']}/{stats['total_requests']}")
    logger.info(f"  Pairs with acceleration: {stats.get('pairs_with_acceleration', 0)}")
    logger.info(f"  Pairs filtered out: {stats.get('pairs_filtered_out', 0)}")
    
    if stats.get('success_rate'):
        logger.info(f"  Success rate: {stats['success_rate']:.1f}%")
    
    return enriched_reports, stats


def filter_reports_by_volume(
    enriched_reports: List[TokenDiscoveryReport],
    require_acceleration: bool = True,
    require_healthy_ratio: bool = False
) -> tuple[List[TokenDiscoveryReport], int]:
    """
    Отфильтровать reports по volume критериям.
    
    Args:
        enriched_reports: обогащенные reports с volume_metrics
        require_acceleration: требовать is_accelerating = True
        require_healthy_ratio: требовать volume_ratio_healthy = True
        
    Returns:
        (filtered_reports, filtered_count)
    """
    logger = logging.getLogger("Part4VolumeFilter")
    
    filtered_reports = []
    
    for report in enriched_reports:
        # Проверяем наличие volume_metrics
        if not hasattr(report, 'volume_metrics') or report.volume_metrics is None:
            # Нет данных - не фильтруем (оставляем на усмотрение других фильтров)
            filtered_reports.append(report)
            continue
        
        metrics = report.volume_metrics
        
        # Применяем фильтры
        passed = True
        
        if require_acceleration and not metrics.get('is_accelerating', False):
            passed = False
        
        if require_healthy_ratio and not metrics.get('volume_ratio_healthy', False):
            passed = False
        
        if passed:
            filtered_reports.append(report)
    
    filtered_count = len(enriched_reports) - len(filtered_reports)
    
    if filtered_count > 0:
        logger.info(f"🔽 Volume filter: removed {filtered_count} reports")
        logger.info(f"  Remaining: {len(filtered_reports)}/{len(enriched_reports)}")
    
    return filtered_reports, filtered_count


# === ИНТЕГРАЦИЯ С PART4 ===

class VolumeEnrichedDiscoverySession:
    """
    Обертка для DiscoverySession с volume enrichment.
    Используется для совместимости с существующим Part4.
    """
    
    def __init__(self, original_session, enrichment_stats: Dict[str, Any]):
        """
        Args:
            original_session: DiscoverySession из Part4
            enrichment_stats: статистика volume enrichment
        """
        self.original_session = original_session
        self.enrichment_stats = enrichment_stats
        
        # Копируем все атрибуты оригинальной сессии
        self.session_id = original_session.session_id
        self.start_time = original_session.start_time
        self.end_time = original_session.end_time
        self.total_operations = original_session.total_operations
        self.completed_operations = original_session.completed_operations
        self.pagination_results = original_session.pagination_results
        self.discovery_reports = original_session.discovery_reports  # Будут обновлены
        self.session_stats = original_session.session_stats
    
    def update_reports(self, enriched_reports: List[TokenDiscoveryReport]):
        """Обновить discovery_reports обогащенными версиями."""
        self.discovery_reports = enriched_reports
        
        # Добавить volume stats в session_stats
        self.session_stats['volume_enrichment'] = self.enrichment_stats
    
    def get_volume_summary(self) -> Dict[str, Any]:
        """Получить краткую сводку по volume metrics."""
        if not self.discovery_reports:
            return {}
        
        reports_with_metrics = [
            r for r in self.discovery_reports 
            if hasattr(r, 'volume_metrics') and r.volume_metrics is not None
        ]
        
        if not reports_with_metrics:
            return {"reports_with_data": 0}
        
        accelerating_count = sum(
            1 for r in reports_with_metrics 
            if r.volume_metrics.get('is_accelerating', False)
        )
        
        healthy_ratio_count = sum(
            1 for r in reports_with_metrics 
            if r.volume_metrics.get('volume_ratio_healthy', False)
        )
        
        return {
            "reports_with_data": len(reports_with_metrics),
            "total_reports": len(self.discovery_reports),
            "reports_with_acceleration": accelerating_count,
            "reports_with_healthy_ratio": healthy_ratio_count,
            "data_coverage": (len(reports_with_metrics) / len(self.discovery_reports)) * 100
        }


# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

def print_volume_enrichment_summary(session: VolumeEnrichedDiscoverySession):
    """Вывести краткую сводку по volume enrichment."""
    summary = session.get_volume_summary()
    
    print("\n" + "=" * 60)
    print("VOLUME ENRICHMENT SUMMARY")
    print("=" * 60)
    
    if summary.get("reports_with_data", 0) == 0:
        print("⚠️ No volume data collected")
        return
    
    print(f"Reports with volume data: {summary['reports_with_data']}/{summary['total_reports']}")
    print(f"Data coverage: {summary['data_coverage']:.1f}%")
    print(f"Reports with acceleration: {summary['reports_with_acceleration']}")
    print(f"Reports with healthy ratio: {summary['reports_with_healthy_ratio']}")
    
    print("\nEnrichment stats:")
    if session.enrichment_stats:
        print(f"  Success rate: {session.enrichment_stats.get('success_rate', 0):.1f}%")
        print(f"  Acceleration rate: {session.enrichment_stats.get('acceleration_rate', 0):.1f}%")
        print(f"  Filter pass rate: {session.enrichment_stats.get('filter_pass_rate', 0):.1f}%")
    
    print("=" * 60)

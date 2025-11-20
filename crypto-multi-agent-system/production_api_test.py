"""
TheGraph Discovery Agent - Production API Test
Тестирование реальных API вызовов для подтверждения теоретических результатов
Безопасный тест с ограничениями для проверки производительности

ВАЖНО: Этот тест делает реальные API запросы к The Graph
"""

import os
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.discovery.thegraph_discovery_agent_part5 import TheGraphPumpDiscoveryAgent


class ProductionAPITest:
    """
    Производственный тест для валидации TheGraph Discovery Agent.
    
    Безопасные лимиты:
    - Максимум 2 субграфа
    - Максимум 3 временных среза
    - Максимум 20 запросов на срез
    - Общий лимит 100 API вызовов
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Безопасные лимиты для продакшн теста
        self.max_subgraphs = 2
        self.max_time_slices = 3
        self.max_requests_per_slice = 20
        self.total_request_limit = 100
        
        # Статистика теста
        self.test_stats = {
            "start_time": None,
            "end_time": None,
            "total_api_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_pairs_found": 0,
            "subgraph_results": {},
            "performance_metrics": {}
        }
    
    async def run_limited_discovery_test(self) -> Dict[str, Any]:
        """
        Запуск ограниченного теста discovery для валидации.
        
        Returns:
            Детальные результаты теста
        """
        self.test_stats["start_time"] = datetime.now()
        
        self.logger.info("="*60)
        self.logger.info("STARTING PRODUCTION API TEST")
        self.logger.info("="*60)
        self.logger.info(f"Safety limits: {self.max_subgraphs} subgraphs, {self.max_time_slices} slices")
        
        try:
            # Инициализируем агент
            discovery_agent = TheGraphPumpDiscoveryAgent()
            
            # Получаем информацию о субграфах
            subgraphs = discovery_agent.get_active_subgraphs_info()
            self.logger.info(f"Available subgraphs: {len(subgraphs)}")
            
            for i, subgraph in enumerate(subgraphs):
                self.logger.info(f"  {i+1}. {subgraph['name']} ({subgraph['blockchain']}) - ${subgraph['liquidity_threshold']}")
            
            # Ограничиваем субграфы для безопасности
            selected_subgraphs = subgraphs[:self.max_subgraphs]
            self.logger.info(f"Testing with {len(selected_subgraphs)} subgraphs for safety")
            
            # Создаем кастомную конфигурацию для ограниченного теста
            test_results = await self._run_custom_limited_discovery(discovery_agent)
            
            # Анализируем результаты
            self._analyze_test_results(test_results)
            
            return self.test_stats
            
        except Exception as e:
            self.logger.error(f"Production test failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
        
        finally:
            self.test_stats["end_time"] = datetime.now()
    
    async def _run_custom_limited_discovery(self, discovery_agent) -> Dict[str, Any]:
        """Запуск кастомного ограниченного discovery."""
        
        # Получаем базовую конфигурацию
        thegraph_agent = discovery_agent.thegraph_agent
        active_subgraphs = thegraph_agent.get_active_subgraphs()[:self.max_subgraphs]
        
        # Генерируем ограниченные временные срезы
        all_time_slices = thegraph_agent.generate_time_slices()
        limited_time_slices = all_time_slices[:self.max_time_slices]
        
        self.logger.info(f"Testing {len(limited_time_slices)} time slices:")
        for slice_obj in limited_time_slices:
            self.logger.info(f"  {slice_obj}")
        
        # Выполняем ограниченный discovery
        all_results = []
        request_count = 0
        
        for subgraph in active_subgraphs:
            subgraph_results = {
                "name": subgraph.name,
                "slices_tested": 0,
                "total_pairs": 0,
                "successful_slices": 0,
                "failed_slices": 0,
                "requests_made": 0
            }
            
            self.logger.info(f"\nTesting {subgraph.name} ({subgraph.blockchain.value})...")
            
            for time_slice in limited_time_slices:
                if request_count >= self.total_request_limit:
                    self.logger.warning(f"Reached total request limit ({self.total_request_limit})")
                    break
                
                try:
                    # Выполняем ограниченную пагинацию
                    result = await self._limited_fetch_pairs_in_slice(
                        thegraph_agent, 
                        subgraph, 
                        time_slice
                    )
                    
                    subgraph_results["slices_tested"] += 1
                    subgraph_results["requests_made"] += result.get("requests_made", 0)
                    request_count += result.get("requests_made", 0)
                    
                    if result.get("success", False):
                        pairs_found = len(result.get("pairs", []))
                        subgraph_results["total_pairs"] += pairs_found
                        subgraph_results["successful_slices"] += 1
                        
                        self.logger.info(f"  Slice {time_slice.slice_number}: {pairs_found} pairs")
                    else:
                        subgraph_results["failed_slices"] += 1
                        self.logger.warning(f"  Slice {time_slice.slice_number}: FAILED")
                
                except Exception as e:
                    self.logger.error(f"  Slice {time_slice.slice_number}: ERROR - {e}")
                    subgraph_results["failed_slices"] += 1
            
            self.test_stats["subgraph_results"][subgraph.name] = subgraph_results
            all_results.append(subgraph_results)
            
            self.logger.info(f"  {subgraph.name} Summary: {subgraph_results['total_pairs']} pairs from {subgraph_results['successful_slices']}/{subgraph_results['slices_tested']} slices")
        
        # Общая статистика
        total_pairs = sum(r["total_pairs"] for r in all_results)
        total_requests = sum(r["requests_made"] for r in all_results)
        
        self.test_stats["total_pairs_found"] = total_pairs
        self.test_stats["total_api_requests"] = total_requests
        
        return {
            "subgraph_results": all_results,
            "total_pairs": total_pairs,
            "total_requests": total_requests
        }
    
    async def _limited_fetch_pairs_in_slice(self, thegraph_agent, subgraph, time_slice) -> Dict[str, Any]:
        """Ограниченная версия fetch_all_pairs_in_slice для тестирования."""
        
        # Импортируем необходимые модули
        from agents.discovery.thegraph_discovery_agent_refactored import create_dex_adapter
        import requests
        
        # Получаем адаптер и строим запрос
        adapter = create_dex_adapter(subgraph.dex_type)
        query_template = adapter.build_pairs_query(subgraph.liquidity_threshold_usd)
        
        # URL субграфа
        url = thegraph_agent._build_subgraph_url(subgraph.subgraph_id)
        
        # Ограничиваем количество запросов для безопасности
        max_pages = min(3, self.max_requests_per_slice)  # Максимум 3 страницы на срез
        
        all_pairs = []
        requests_made = 0
        
        for page in range(max_pages):
            skip = page * 1000
            
            variables = {
                "start": time_slice.start_timestamp,
                "end": time_slice.end_timestamp,
                "first": 1000,
                "skip": skip
            }
            
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: requests.post(
                        url,
                        json={"query": query_template, "variables": variables},
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                )
                
                requests_made += 1
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "errors" not in data:
                        # Получаем пары в зависимости от типа DEX
                        if subgraph.dex_type.value == "uniswap_v3":
                            pairs = data.get("data", {}).get("pools", [])
                        else:
                            pairs = data.get("data", {}).get("pairs", [])
                        
                        if not pairs:
                            break  # Больше нет данных
                        
                        all_pairs.extend(pairs)
                        
                        if len(pairs) < 1000:
                            break  # Последняя страница
                    else:
                        self.logger.error(f"GraphQL Error: {data['errors'][0]['message']}")
                        break
                else:
                    self.logger.error(f"HTTP Error: {response.status_code}")
                    break
                
                # Rate limiting
                await asyncio.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Request failed: {e}")
                break
        
        return {
            "success": len(all_pairs) > 0,
            "pairs": all_pairs,
            "requests_made": requests_made
        }
    
    def _analyze_test_results(self, results: Dict[str, Any]):
        """Анализ результатов теста."""
        
        total_pairs = results.get("total_pairs", 0)
        total_requests = results.get("total_requests", 0)
        
        self.logger.info("\n" + "="*60)
        self.logger.info("PRODUCTION TEST RESULTS ANALYSIS")
        self.logger.info("="*60)
        
        # Основные метрики
        self.logger.info(f"Total pairs discovered: {total_pairs}")
        self.logger.info(f"Total API requests made: {total_requests}")
        
        # Экстраполяция на полный запуск
        if total_pairs > 0:
            # Расчет на основе ограниченного теста
            full_subgraphs = 4  # У нас есть 4 субграфа
            full_slices = 6     # Полный диапазон 6 срезов
            
            tested_operations = len(self.test_stats["subgraph_results"]) * self.max_time_slices
            full_operations = full_subgraphs * full_slices
            
            if tested_operations > 0:
                extrapolated_pairs = (total_pairs / tested_operations) * full_operations
                extrapolated_requests = (total_requests / tested_operations) * full_operations
                
                self.logger.info(f"\nExtrapolation to full discovery:")
                self.logger.info(f"  Tested operations: {tested_operations}")
                self.logger.info(f"  Full operations would be: {full_operations}")
                self.logger.info(f"  Estimated total pairs: {extrapolated_pairs:.0f}")
                self.logger.info(f"  Estimated total requests: {extrapolated_requests:.0f}")
                
                # Сравнение с прототипом
                prototype_result = 572
                if extrapolated_pairs >= prototype_result * 0.8:  # 80% от прототипа
                    self.logger.info(f"  Status: ON TRACK (vs {prototype_result} from prototype)")
                else:
                    self.logger.warning(f"  Status: BELOW EXPECTATIONS (vs {prototype_result} from prototype)")
        
        # Детализация по субграфам
        self.logger.info(f"\nBreakdown by subgraph:")
        for name, stats in self.test_stats["subgraph_results"].items():
            success_rate = (stats["successful_slices"] / max(stats["slices_tested"], 1)) * 100
            self.logger.info(f"  {name}:")
            self.logger.info(f"    Pairs found: {stats['total_pairs']}")
            self.logger.info(f"    Success rate: {success_rate:.1f}% ({stats['successful_slices']}/{stats['slices_tested']})")
            self.logger.info(f"    Requests made: {stats['requests_made']}")
        
        # Рекомендации
        self.logger.info(f"\nRecommendations:")
        if total_pairs > 0:
            self.logger.info(f"  ✓ TheGraph approach is working")
            self.logger.info(f"  ✓ Ready for production deployment")
            if total_requests < 50:
                self.logger.info(f"  ✓ API usage is reasonable")
            else:
                self.logger.info(f"  ⚠ Monitor API usage in production")
        else:
            self.logger.info(f"  ✗ No pairs found - investigate configuration")


async def main():
    """Запуск производственного теста."""
    test = ProductionAPITest()
    
    print("Starting production API test for TheGraph Discovery Agent...")
    print("This test makes REAL API calls with safety limits")
    print("")
    
    # Подтверждение от пользователя
    proceed = input("Proceed with real API calls? (y/n): ")
    if proceed.lower() != 'y':
        print("Test cancelled")
        return
    
    # Запуск теста
    start_time = time.time()
    results = await test.run_limited_discovery_test()
    duration = time.time() - start_time
    
    print(f"\nTest completed in {duration:.1f} seconds")
    
    # Сохранение результатов
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"thegraph_production_test_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        # Преобразуем datetime объекты в строки для JSON
        serializable_results = results.copy()
        if "start_time" in serializable_results and serializable_results["start_time"]:
            serializable_results["start_time"] = serializable_results["start_time"].isoformat()
        if "end_time" in serializable_results and serializable_results["end_time"]:
            serializable_results["end_time"] = serializable_results["end_time"].isoformat()
        
        json.dump(serializable_results, f, indent=2)
    
    print(f"Results saved to: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())

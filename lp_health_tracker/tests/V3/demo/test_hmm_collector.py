import sys
import os

# Путь к папке src (2 уровня вверх от tests/V3/demo/)
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, src_path)

import asyncio
import traceback

try:
    from src.V3.hmm_market_data_collector import AdvancedDataCollector, GasStatsResponse, V3PoolDataResponse, MarketDataPoint
    from src.V3.collector_config import HMMCollectorConfig
    print("Импорты успешны!")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)
    
class CollectorTester:
    # ... (методы __init__, log_test_result, print_summary без изменений) ...
    def __init__(self):
        self.test_results = {}
    
    def log_test_result(self, test_name: str, success: bool, message: str = ""):
        status = "✅" if success else "❌"
        self.test_results[test_name] = success
        print(f"{status} {test_name}: {message}")

    def print_summary(self):
        total = len(self.test_results)
        passed = sum(self.test_results.values())
        print(f"\n📊 Результаты тестирования:")
        print(f"Пройдено: {passed}/{total}")
        if total > 0: print(f"Успешность: {(passed/total)*100:.1f}%")
        if passed < total:
            print("\n❌ Неудачные тесты:")
            for test, result in self.test_results.items():
                if not result: print(f"  - {test}")

    def test_config_validation(self):
        # ... (без изменений) ...
        try:
            config = HMMCollectorConfig()
            self.log_test_result("Config Validation", True, f"Конфигурация успешно валидирована.")
            return config
        except Exception as e:
            self.log_test_result("Config Validation", False, f"Ошибка: {e}")
            return None

    def test_collector_initialization(self, config):
        # ... (без изменений) ...
        try:
            collector = AdvancedDataCollector(config)
            self.log_test_result("Collector Init", True, "Инициализация успешна")
            return collector
        except Exception as e:
            self.log_test_result("Collector Init", False, f"Ошибка: {e}")
            return None

    async def test_gas_stats_fetch(self, collector):
        """Тест 3: Получение статистики газа."""
        try:
            gas_stats = await collector._get_onchain_gas_stats_async()
            success = isinstance(gas_stats, GasStatsResponse)
            # ИСПРАВЛЕНО: Проверяем, что в модели нет лишних полей
            extra_fields = [f for f in gas_stats.model_dump() if f not in GasStatsResponse.model_fields]
            success = success and not extra_fields
            
            self.log_test_result("Gas Stats Fetch & Validation", success, "Получен корректный УПРОЩЕННЫЙ объект GasStatsResponse" if success else "Неверный тип или лишние поля в ответе")
            if success:
                print(f"  -> Avg Fee: {gas_stats.avg_fee:.2f} Gwei, Outlier Pct: {gas_stats.outlier_percentage:.2f}%")
            return success
        except Exception as e:
            self.log_test_result("Gas Stats Fetch", False, f"Ошибка: {e}")
            return False

    async def test_full_pipeline(self, collector):
        """Тест 4: Полный pipeline сбора данных."""
        try:
            market_data = await collector.get_current_market_data()
            success = isinstance(market_data, MarketDataPoint)
            self.log_test_result("Full Pipeline & Validation", success, "Итоговый УПРОЩЕННЫЙ объект MarketDataPoint успешно создан" if success else "Неверный тип итогового объекта")
            
            if success:
                print("\n📋 Ключевые метрики из итогового объекта:")
                print(f"  - ETH Price: ${market_data.eth_price_usd}")
                print(f"  - Outlier Percentage: {market_data.outlier_percentage:.2f}%")
            
            return success
        except Exception as e:
            self.log_test_result("Full Pipeline", False, f"Ошибка: {e}")
            traceback.print_exc()
            return False
            
    async def run_all_tests(self):
        # ... (без изменений) ...
        print("🧪 Запуск тестирования hmm_market_data_collector.py\n")
        config = self.test_config_validation()
        if not config: self.print_summary(); return
        collector = self.test_collector_initialization(config)
        if not collector: self.print_summary(); return
        
        # Запускаем только нужные тесты
        await self.test_gas_stats_fetch(collector)
        await self.test_full_pipeline(collector)
        
        await collector.close_sessions()
        self.log_test_result("Session Cleanup", True, "Сетевые сессии успешно закрыты")
        self.print_summary()

async def main():
    tester = CollectorTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
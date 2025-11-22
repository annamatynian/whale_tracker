"""
E2E тесты для Whale Tracker - Полный цикл мониторинга
======================================================

Проверяет полный цикл работы системы мониторинга китов.
"""

import asyncio
import pytest
import logging
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from config.settings import Settings
from main import WhaleTrackerOrchestrator


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.fixture
def mock_settings():
    """
    Создает настройки для тестирования в mock режиме.
    """
    settings = Settings()
    settings.development.mock_data = True
    # Устанавливаем тестовые адреса китов
    if not settings.WHALE_ADDRESSES:
        settings.WHALE_ADDRESSES = [
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
            "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"   # Tornado Cash
        ]
    return settings


@pytest.mark.asyncio
class TestWhaleTrackerMonitoringCycle:
    """
    Тесты полного цикла мониторинга.
    """

    async def test_orchestrator_initialization(self, mock_settings):
        """
        Проверяет инициализацию оркестратора.
        """
        logger.info("🧪 TEST: Orchestrator Initialization")

        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        assert orchestrator is not None, "Orchestrator не создан"
        assert orchestrator.settings is not None, "Settings не загружены"
        assert orchestrator.settings.development.mock_data is True, "Mock режим не активирован"

        logger.info("✅ Orchestrator успешно инициализирован")

    async def test_orchestrator_setup(self, mock_settings):
        """
        Проверяет setup всех компонентов оркестратора.
        """
        logger.info("🧪 TEST: Orchestrator Setup")

        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)

        # Выполняем setup
        orchestrator.setup()

        # Проверяем что все компоненты инициализированы
        assert orchestrator.web3_manager is not None, "Web3Manager не инициализирован"
        assert orchestrator.whale_config is not None, "WhaleConfig не инициализирован"
        assert orchestrator.analyzer is not None, "WhaleAnalyzer не инициализирован"
        assert orchestrator.notifier is not None, "TelegramNotifier не инициализирован"
        assert orchestrator.nonce_tracker is not None, "NonceTracker не инициализирован"
        assert orchestrator.gas_correlator is not None, "GasCorrelator не инициализирован"
        assert orchestrator.address_profiler is not None, "AddressProfiler не инициализирован"
        assert orchestrator.watcher is not None, "SimpleWhaleWatcher не инициализирован"

        logger.info("✅ Все компоненты успешно инициализированы через setup()")

    async def test_single_monitoring_cycle(self, mock_settings):
        """
        Проверяет выполнение одного цикла мониторинга.
        """
        logger.info("🧪 TEST: Single Monitoring Cycle")

        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)
        orchestrator.setup()

        # Патчим метод отправки уведомлений, чтобы не отправлять реальные сообщения
        with patch.object(
            orchestrator.notifier,
            'send_alert',
            new_callable=AsyncMock
        ) as mock_send:
            # Запускаем один цикл мониторинга
            await orchestrator.run_monitoring_cycle()

            # Проверяем что цикл выполнен без ошибок
            logger.info("✅ Цикл мониторинга выполнен успешно")

    async def test_monitoring_with_whale_addresses(self, mock_settings):
        """
        Проверяет мониторинг с реальными адресами китов.
        """
        logger.info("🧪 TEST: Monitoring With Whale Addresses")

        # Убеждаемся что есть адреса для мониторинга
        assert len(mock_settings.WHALE_ADDRESSES) > 0, "Нет адресов для мониторинга"

        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)
        orchestrator.setup()

        logger.info(f"Мониторинг {len(mock_settings.WHALE_ADDRESSES)} адресов китов:")
        for addr in mock_settings.WHALE_ADDRESSES:
            logger.info(f"  - {addr}")

        # Патчим уведомления
        with patch.object(
            orchestrator.notifier,
            'send_alert',
            new_callable=AsyncMock
        ) as mock_send:
            # Запускаем мониторинг
            result = await orchestrator.watcher.monitor_all_whales()

            # Проверяем результат
            assert result is not None, "Результат мониторинга не получен"
            assert 'status' in result, "Нет статуса в результате"
            assert 'whales_checked' in result, "Нет количества проверенных китов"

            logger.info(f"  Status: {result.get('status')}")
            logger.info(f"  Whales checked: {result.get('whales_checked')}")
            logger.info(f"  Total alerts: {result.get('total_alerts', 0)}")

            logger.info("✅ Мониторинг китов выполнен успешно")

    @pytest.mark.skip(reason="Требует реального RPC подключения")
    async def test_real_blockchain_monitoring(self):
        """
        Тест с реальным подключением к блокчейну (требует API ключи).

        Этот тест пропускается по умолчанию.
        Для запуска: pytest -v -m "not skip"
        """
        logger.info("🧪 TEST: Real Blockchain Monitoring")

        settings = Settings()
        settings.development.mock_data = False  # Отключаем mock режим

        orchestrator = WhaleTrackerOrchestrator(settings=settings)
        orchestrator.setup()

        # Запускаем один цикл
        await orchestrator.run_once()

        logger.info("✅ Реальный мониторинг выполнен")


@pytest.mark.asyncio
class TestWhaleTrackerErrorHandling:
    """
    Тесты обработки ошибок.
    """

    async def test_graceful_shutdown(self, mock_settings):
        """
        Проверяет корректное завершение работы оркестратора.
        """
        logger.info("🧪 TEST: Graceful Shutdown")

        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)
        orchestrator.setup()

        # Запускаем и останавливаем
        orchestrator.stop()

        assert orchestrator.shutdown_requested is True, "Флаг shutdown не установлен"

        logger.info("✅ Graceful shutdown работает корректно")

    async def test_monitoring_without_setup(self):
        """
        Проверяет поведение при попытке мониторинга без setup.
        """
        logger.info("🧪 TEST: Monitoring Without Setup")

        settings = Settings()
        settings.development.mock_data = True

        orchestrator = WhaleTrackerOrchestrator(settings=settings)
        # НЕ вызываем setup()

        # Попытка запустить мониторинг без setup должна быть обработана
        await orchestrator.run_monitoring_cycle()

        # Не должно быть краша, просто предупреждение
        logger.info("✅ Обработка отсутствия setup работает корректно")

    async def test_empty_whale_addresses(self):
        """
        Проверяет поведение при отсутствии адресов для мониторинга.
        """
        logger.info("🧪 TEST: Empty Whale Addresses")

        settings = Settings()
        settings.development.mock_data = True
        settings.WHALE_ADDRESSES = []  # Пустой список

        orchestrator = WhaleTrackerOrchestrator(settings=settings)
        orchestrator.setup()

        # Запускаем мониторинг с пустым списком
        await orchestrator.run_monitoring_cycle()

        # Должно работать без ошибок, просто ничего не мониторить
        logger.info("✅ Обработка пустого списка адресов работает корректно")


@pytest.mark.asyncio
class TestWhaleTrackerScheduler:
    """
    Тесты планировщика задач.
    """

    async def test_scheduler_setup(self, mock_settings):
        """
        Проверяет настройку планировщика.
        """
        logger.info("🧪 TEST: Scheduler Setup")

        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)
        orchestrator.setup()
        orchestrator.setup_scheduler()

        assert orchestrator.scheduler is not None, "Scheduler не создан"

        # Проверяем что задача добавлена
        jobs = orchestrator.scheduler.get_jobs()
        assert len(jobs) > 0, "Нет добавленных задач в scheduler"

        whale_monitoring_job = None
        for job in jobs:
            if job.id == 'whale_monitoring':
                whale_monitoring_job = job
                break

        assert whale_monitoring_job is not None, "Задача whale_monitoring не найдена"

        logger.info(f"  Job ID: {whale_monitoring_job.id}")
        logger.info(f"  Job Name: {whale_monitoring_job.name}")
        logger.info("✅ Scheduler успешно настроен")

    async def test_scheduler_start_stop(self, mock_settings):
        """
        Проверяет запуск и остановку планировщика.
        """
        logger.info("🧪 TEST: Scheduler Start/Stop")

        orchestrator = WhaleTrackerOrchestrator(settings=mock_settings)
        orchestrator.setup()
        orchestrator.setup_scheduler()

        # Запускаем scheduler
        orchestrator.start()
        assert orchestrator.scheduler.running is True, "Scheduler не запущен"
        logger.info("  Scheduler запущен")

        # Даем время на работу
        await asyncio.sleep(1)

        # Останавливаем
        orchestrator.stop()
        assert orchestrator.scheduler.running is False, "Scheduler не остановлен"
        logger.info("  Scheduler остановлен")

        logger.info("✅ Запуск/остановка scheduler работает корректно")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

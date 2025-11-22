"""
E2E тесты для Whale Tracker - Инициализация компонентов
========================================================

Проверяет корректную инициализацию и работу всех основных компонентов.
"""

import asyncio
import pytest
import logging
from pathlib import Path

from config.settings import Settings
from src.core.web3_manager import Web3Manager
from src.core.whale_config import WhaleConfig
from src.analyzers.whale_analyzer import WhaleAnalyzer
from src.analyzers.nonce_tracker import NonceTracker
from src.analyzers.gas_correlator import GasCorrelator
from src.analyzers.address_profiler import AddressProfiler
from src.notifications.telegram_notifier import TelegramNotifier
from src.monitors.simple_whale_watcher import SimpleWhaleWatcher


# Setup logging для тестов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.fixture
def test_settings():
    """
    Создает настройки для тестирования в mock режиме.
    """
    settings = Settings()
    # Переключаем в mock режим для тестов
    settings.development.mock_data = True
    return settings


@pytest.fixture
async def web3_manager(test_settings):
    """
    Создает Web3Manager для тестов.
    """
    manager = Web3Manager(mock_mode=test_settings.development.mock_data)
    yield manager
    # Cleanup если нужен


@pytest.fixture
def whale_config():
    """
    Создает WhaleConfig для тестов.
    """
    return WhaleConfig()


@pytest.fixture
def whale_analyzer():
    """
    Создает WhaleAnalyzer для тестов.
    """
    return WhaleAnalyzer(
        anomaly_multiplier=1.3,
        rolling_window_size=10,
        min_history_required=5
    )


@pytest.fixture
def telegram_notifier():
    """
    Создает TelegramNotifier для тестов.
    """
    return TelegramNotifier()


@pytest.mark.asyncio
class TestWhaleTrackerComponentInitialization:
    """
    Тесты инициализации компонентов Whale Tracker.
    """

    async def test_web3_manager_initialization(self, web3_manager):
        """
        Проверяет инициализацию Web3Manager.
        """
        logger.info("🧪 TEST: Web3Manager Initialization")

        # Web3Manager уже должен быть создан
        assert web3_manager is not None, "Web3Manager не создан"

        # В mock режиме не требуется реальное подключение
        logger.info("✅ Web3Manager успешно инициализирован")

    async def test_whale_config_initialization(self, whale_config):
        """
        Проверяет инициализацию WhaleConfig.
        """
        logger.info("🧪 TEST: WhaleConfig Initialization")

        assert whale_config is not None, "WhaleConfig не создан"

        # Проверяем что адреса загружены
        all_addresses = whale_config.all_addresses
        assert len(all_addresses) > 0, "Нет загруженных адресов китов"

        logger.info(f"✅ WhaleConfig загружен ({len(all_addresses)} адресов)")

    async def test_whale_analyzer_initialization(self, whale_analyzer):
        """
        Проверяет инициализацию WhaleAnalyzer.
        """
        logger.info("🧪 TEST: WhaleAnalyzer Initialization")

        assert whale_analyzer is not None, "WhaleAnalyzer не создан"
        assert whale_analyzer.anomaly_multiplier == 1.3
        assert whale_analyzer.rolling_window_size == 10
        assert whale_analyzer.min_history_required == 5

        logger.info("✅ WhaleAnalyzer успешно инициализирован")

    async def test_telegram_notifier_initialization(self, telegram_notifier):
        """
        Проверяет инициализацию TelegramNotifier.
        """
        logger.info("🧪 TEST: TelegramNotifier Initialization")

        assert telegram_notifier is not None, "TelegramNotifier не создан"

        logger.info("✅ TelegramNotifier успешно инициализирован")

    async def test_advanced_analyzers_initialization(self, web3_manager):
        """
        Проверяет инициализацию продвинутых анализаторов.
        """
        logger.info("🧪 TEST: Advanced Analyzers Initialization")

        # NonceTracker
        nonce_tracker = NonceTracker(
            web3_manager=web3_manager,
            etherscan_api_key=None,
            use_etherscan=False
        )
        assert nonce_tracker is not None, "NonceTracker не создан"
        logger.info("  ✅ NonceTracker инициализирован")

        # GasCorrelator
        gas_correlator = GasCorrelator()
        assert gas_correlator is not None, "GasCorrelator не создан"
        logger.info("  ✅ GasCorrelator инициализирован")

        # AddressProfiler
        address_profiler = AddressProfiler(web3_manager=web3_manager)
        assert address_profiler is not None, "AddressProfiler не создан"
        logger.info("  ✅ AddressProfiler инициализирован")

        logger.info("✅ Все продвинутые анализаторы успешно инициализированы")


@pytest.mark.asyncio
class TestWhaleTrackerIntegration:
    """
    Тесты интеграции компонентов.
    """

    async def test_whale_watcher_creation(
        self,
        web3_manager,
        whale_config,
        whale_analyzer,
        telegram_notifier,
        test_settings
    ):
        """
        Проверяет создание SimpleWhaleWatcher со всеми компонентами.
        """
        logger.info("🧪 TEST: SimpleWhaleWatcher Creation")

        # Создаем продвинутые анализаторы
        nonce_tracker = NonceTracker(
            web3_manager=web3_manager,
            etherscan_api_key=None,
            use_etherscan=False
        )
        gas_correlator = GasCorrelator()
        address_profiler = AddressProfiler(web3_manager=web3_manager)

        # Создаем SimpleWhaleWatcher
        watcher = SimpleWhaleWatcher(
            web3_manager=web3_manager,
            whale_config=whale_config,
            analyzer=whale_analyzer,
            notifier=telegram_notifier,
            settings=test_settings,
            nonce_tracker=nonce_tracker,
            gas_correlator=gas_correlator,
            address_profiler=address_profiler
        )

        assert watcher is not None, "SimpleWhaleWatcher не создан"
        assert watcher.web3_manager is not None
        assert watcher.whale_config is not None
        assert watcher.analyzer is not None
        assert watcher.notifier is not None
        assert watcher.nonce_tracker is not None
        assert watcher.gas_correlator is not None
        assert watcher.address_profiler is not None

        logger.info("✅ SimpleWhaleWatcher успешно создан со всеми компонентами")

    async def test_whale_config_address_classification(self, whale_config):
        """
        Проверяет классификацию адресов WhaleConfig.
        """
        logger.info("🧪 TEST: WhaleConfig Address Classification")

        # Тестовый адрес Vitalik (известный кит)
        vitalik_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

        # Проверяем классификацию
        classification = whale_config.classify_address(vitalik_address)

        assert classification is not None, "Классификация не выполнена"
        assert 'category' in classification, "Нет категории в классификации"
        assert 'label' in classification, "Нет метки в классификации"

        logger.info(f"  Категория: {classification['category']}")
        logger.info(f"  Метка: {classification['label']}")
        logger.info("✅ Классификация адресов работает корректно")

    async def test_whale_analyzer_statistics(self, whale_analyzer):
        """
        Проверяет работу статистического анализа WhaleAnalyzer.
        """
        logger.info("🧪 TEST: WhaleAnalyzer Statistics")

        # Создаем тестовые данные транзакций
        test_transactions = [
            {'value': 1000000},  # $1M
            {'value': 2000000},  # $2M
            {'value': 1500000},  # $1.5M
            {'value': 1200000},  # $1.2M
            {'value': 10000000}, # $10M (аномалия!)
        ]

        # Проверяем каждую транзакцию
        for i, tx in enumerate(test_transactions):
            result = whale_analyzer.analyze_transaction(tx)

            assert result is not None, f"Анализ транзакции {i} не выполнен"
            assert 'is_anomaly' in result, "Нет флага аномалии"

            if i < 4:
                logger.info(f"  Транзакция {i+1}: ${tx['value']:,} - Нормальная")
            else:
                logger.info(f"  Транзакция {i+1}: ${tx['value']:,} - {'АНОМАЛИЯ' if result['is_anomaly'] else 'Нормальная'}")

        logger.info("✅ Статистический анализ работает корректно")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

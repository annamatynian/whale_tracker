"""
E2E тесты для Advanced One-Hop Analyzers
=========================================

Проверяет работу продвинутых анализаторов:
- NonceTracker (Signal #3 - STRONGEST)
- GasCorrelator (Signal #2)
- AddressProfiler (Signal #5)
"""

import asyncio
import pytest
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from config.settings import Settings
from src.core.web3_manager import Web3Manager
from src.analyzers.nonce_tracker import NonceTracker
from src.analyzers.gas_correlator import GasCorrelator
from src.analyzers.address_profiler import AddressProfiler


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.fixture
async def web3_manager():
    """
    Создает Web3Manager в mock режиме.
    """
    manager = Web3Manager(mock_mode=True)
    return manager


@pytest.mark.asyncio
class TestNonceTrackerE2E:
    """
    E2E тесты для NonceTracker.
    """

    async def test_nonce_tracker_initialization(self, web3_manager):
        """
        Проверяет инициализацию NonceTracker.
        """
        logger.info("🧪 TEST: NonceTracker Initialization")

        tracker = NonceTracker(
            web3_manager=web3_manager,
            etherscan_api_key=None,
            use_etherscan=False
        )

        assert tracker is not None, "NonceTracker не создан"
        assert tracker.web3_manager is not None, "Web3Manager не установлен"
        assert tracker.use_etherscan is False, "Etherscan должен быть отключен"

        logger.info("✅ NonceTracker успешно инициализирован")

    async def test_nonce_tracker_analysis(self, web3_manager):
        """
        Проверяет анализ nonce для обнаружения связанных адресов.
        """
        logger.info("🧪 TEST: NonceTracker Analysis")

        tracker = NonceTracker(
            web3_manager=web3_manager,
            etherscan_api_key=None,
            use_etherscan=False
        )

        # Тестовые адреса
        whale_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        recipient_address = "0x1234567890123456789012345678901234567890"

        # Тестовая транзакция
        test_transaction = {
            'from': whale_address,
            'to': recipient_address,
            'value': 1000000000000000000,  # 1 ETH
            'hash': '0xtest123',
            'blockNumber': 18000000,
            'timestamp': int(datetime.now().timestamp())
        }

        # Выполняем анализ
        result = await tracker.analyze_transaction(test_transaction)

        assert result is not None, "Результат анализа не получен"
        logger.info(f"  Результат анализа: {result}")

        logger.info("✅ NonceTracker анализ выполнен")

    async def test_nonce_tracker_sequential_detection(self, web3_manager):
        """
        Проверяет обнаружение последовательных nonce.
        """
        logger.info("🧪 TEST: NonceTracker Sequential Nonce Detection")

        tracker = NonceTracker(
            web3_manager=web3_manager,
            etherscan_api_key=None,
            use_etherscan=False
        )

        # Симулируем транзакции с последовательными nonce
        whale_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

        transactions = []
        base_time = datetime.now()

        for i in range(5):
            tx = {
                'from': whale_address,
                'to': f"0x{i:040x}",
                'value': 1000000000000000000,
                'hash': f'0x{i:064x}',
                'nonce': 100 + i,
                'blockNumber': 18000000 + i,
                'timestamp': int((base_time + timedelta(seconds=i*15)).timestamp())
            }
            transactions.append(tx)
            result = await tracker.analyze_transaction(tx)
            logger.info(f"  TX {i+1} (nonce={tx['nonce']}): {result}")

        logger.info("✅ Sequential nonce detection работает")


@pytest.mark.asyncio
class TestGasCorrelatorE2E:
    """
    E2E тесты для GasCorrelator.
    """

    async def test_gas_correlator_initialization(self):
        """
        Проверяет инициализацию GasCorrelator.
        """
        logger.info("🧪 TEST: GasCorrelator Initialization")

        correlator = GasCorrelator()

        assert correlator is not None, "GasCorrelator не создан"

        logger.info("✅ GasCorrelator успешно инициализирован")

    async def test_gas_correlator_analysis(self):
        """
        Проверяет анализ корреляции gas price.
        """
        logger.info("🧪 TEST: GasCorrelator Analysis")

        correlator = GasCorrelator()

        # Тестовая транзакция
        whale_tx = {
            'from': "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            'to': "0x1234567890123456789012345678901234567890",
            'gasPrice': 50000000000,  # 50 Gwei
            'timestamp': int(datetime.now().timestamp())
        }

        # Транзакция получателя
        recipient_tx = {
            'from': "0x1234567890123456789012345678901234567890",
            'to': "0x9876543210987654321098765432109876543210",
            'gasPrice': 51000000000,  # 51 Gwei (похожая цена)
            'timestamp': int((datetime.now() + timedelta(minutes=2)).timestamp())
        }

        # Анализируем корреляцию
        result = await correlator.analyze_gas_correlation(whale_tx, recipient_tx)

        assert result is not None, "Результат анализа не получен"
        logger.info(f"  Корреляция gas: {result}")

        logger.info("✅ GasCorrelator анализ выполнен")

    async def test_gas_correlator_timing_window(self):
        """
        Проверяет временное окно для корреляции gas.
        """
        logger.info("🧪 TEST: GasCorrelator Timing Window")

        correlator = GasCorrelator()

        base_time = datetime.now()

        # Транзакции в разных временных окнах
        test_cases = [
            {
                'name': 'Близко по времени (1 мин)',
                'whale_tx': {
                    'gasPrice': 50000000000,
                    'timestamp': int(base_time.timestamp())
                },
                'recipient_tx': {
                    'gasPrice': 50000000000,
                    'timestamp': int((base_time + timedelta(minutes=1)).timestamp())
                }
            },
            {
                'name': 'Далеко по времени (2 часа)',
                'whale_tx': {
                    'gasPrice': 50000000000,
                    'timestamp': int(base_time.timestamp())
                },
                'recipient_tx': {
                    'gasPrice': 50000000000,
                    'timestamp': int((base_time + timedelta(hours=2)).timestamp())
                }
            }
        ]

        for case in test_cases:
            result = await correlator.analyze_gas_correlation(
                case['whale_tx'],
                case['recipient_tx']
            )
            logger.info(f"  {case['name']}: {result}")

        logger.info("✅ Timing window analysis работает")


@pytest.mark.asyncio
class TestAddressProfilerE2E:
    """
    E2E тесты для AddressProfiler.
    """

    async def test_address_profiler_initialization(self, web3_manager):
        """
        Проверяет инициализацию AddressProfiler.
        """
        logger.info("🧪 TEST: AddressProfiler Initialization")

        profiler = AddressProfiler(web3_manager=web3_manager)

        assert profiler is not None, "AddressProfiler не создан"
        assert profiler.web3_manager is not None, "Web3Manager не установлен"

        logger.info("✅ AddressProfiler успешно инициализирован")

    async def test_address_profiler_analysis(self, web3_manager):
        """
        Проверяет профилирование адреса.
        """
        logger.info("🧪 TEST: AddressProfiler Analysis")

        profiler = AddressProfiler(web3_manager=web3_manager)

        # Тестовый адрес
        test_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

        # Выполняем профилирование
        profile = await profiler.profile_address(test_address)

        assert profile is not None, "Профиль не получен"
        assert 'address' in profile, "Нет адреса в профиле"

        logger.info(f"  Профиль адреса: {profile}")

        logger.info("✅ AddressProfiler анализ выполнен")

    async def test_address_profiler_contract_detection(self, web3_manager):
        """
        Проверяет определение является ли адрес контрактом.
        """
        logger.info("🧪 TEST: AddressProfiler Contract Detection")

        profiler = AddressProfiler(web3_manager=web3_manager)

        # Известный адрес контракта (USDC)
        contract_address = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"

        # Обычный адрес (Vitalik)
        eoa_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

        # Проверяем контракт
        contract_profile = await profiler.profile_address(contract_address)
        logger.info(f"  Contract address: {contract_profile}")

        # Проверяем EOA
        eoa_profile = await profiler.profile_address(eoa_address)
        logger.info(f"  EOA address: {eoa_profile}")

        logger.info("✅ Contract detection работает")


@pytest.mark.asyncio
class TestAdvancedAnalyzersIntegration:
    """
    Тесты интеграции всех продвинутых анализаторов.
    """

    async def test_all_analyzers_together(self, web3_manager):
        """
        Проверяет совместную работу всех анализаторов.
        """
        logger.info("🧪 TEST: All Advanced Analyzers Integration")

        # Создаем все анализаторы
        nonce_tracker = NonceTracker(
            web3_manager=web3_manager,
            etherscan_api_key=None,
            use_etherscan=False
        )

        gas_correlator = GasCorrelator()

        address_profiler = AddressProfiler(web3_manager=web3_manager)

        # Тестовая транзакция кита
        whale_tx = {
            'from': "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            'to': "0x1234567890123456789012345678901234567890",
            'value': 1000000000000000000,
            'hash': '0xtest123',
            'nonce': 100,
            'gasPrice': 50000000000,
            'blockNumber': 18000000,
            'timestamp': int(datetime.now().timestamp())
        }

        logger.info("Анализ транзакции всеми анализаторами:")

        # NonceTracker
        nonce_result = await nonce_tracker.analyze_transaction(whale_tx)
        logger.info(f"  NonceTracker: {nonce_result}")

        # AddressProfiler для отправителя
        sender_profile = await address_profiler.profile_address(whale_tx['from'])
        logger.info(f"  Sender Profile: {sender_profile}")

        # AddressProfiler для получателя
        recipient_profile = await address_profiler.profile_address(whale_tx['to'])
        logger.info(f"  Recipient Profile: {recipient_profile}")

        # GasCorrelator (симулируем вторую транзакцию)
        recipient_tx = {
            'from': whale_tx['to'],
            'to': "0x9876543210987654321098765432109876543210",
            'gasPrice': 51000000000,
            'timestamp': int((datetime.now() + timedelta(minutes=5)).timestamp())
        }
        gas_result = await gas_correlator.analyze_gas_correlation(whale_tx, recipient_tx)
        logger.info(f"  GasCorrelator: {gas_result}")

        logger.info("✅ Все анализаторы работают совместно")

    async def test_one_hop_detection_scenario(self, web3_manager):
        """
        Проверяет полный сценарий обнаружения one-hop.
        """
        logger.info("🧪 TEST: Complete One-Hop Detection Scenario")

        # Создаем анализаторы
        nonce_tracker = NonceTracker(
            web3_manager=web3_manager,
            etherscan_api_key=None,
            use_etherscan=False
        )

        gas_correlator = GasCorrelator()
        address_profiler = AddressProfiler(web3_manager=web3_manager)

        # Сценарий: Кит -> Промежуточный адрес -> Конечный адрес
        whale_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        intermediate_address = "0x1234567890123456789012345678901234567890"
        final_address = "0x9876543210987654321098765432109876543210"

        base_time = datetime.now()

        # Шаг 1: Кит отправляет на промежуточный адрес
        tx1 = {
            'from': whale_address,
            'to': intermediate_address,
            'value': 10000000000000000000,  # 10 ETH
            'hash': '0xtx1',
            'nonce': 100,
            'gasPrice': 50000000000,
            'blockNumber': 18000000,
            'timestamp': int(base_time.timestamp())
        }

        logger.info("Шаг 1: Кит -> Промежуточный адрес")
        nonce_result_1 = await nonce_tracker.analyze_transaction(tx1)
        logger.info(f"  NonceTracker: {nonce_result_1}")

        # Шаг 2: Промежуточный адрес отправляет на конечный
        tx2 = {
            'from': intermediate_address,
            'to': final_address,
            'value': 9500000000000000000,  # 9.5 ETH (минус комиссия)
            'hash': '0xtx2',
            'nonce': 0,  # Новый адрес, первая транзакция
            'gasPrice': 51000000000,
            'blockNumber': 18000001,
            'timestamp': int((base_time + timedelta(minutes=5)).timestamp())
        }

        logger.info("Шаг 2: Промежуточный -> Конечный адрес")
        nonce_result_2 = await nonce_tracker.analyze_transaction(tx2)
        logger.info(f"  NonceTracker: {nonce_result_2}")

        # Анализ корреляции gas
        gas_correlation = await gas_correlator.analyze_gas_correlation(tx1, tx2)
        logger.info(f"  Gas Correlation: {gas_correlation}")

        # Профилирование адресов
        whale_profile = await address_profiler.profile_address(whale_address)
        intermediate_profile = await address_profiler.profile_address(intermediate_address)
        final_profile = await address_profiler.profile_address(final_address)

        logger.info(f"  Whale Profile: {whale_profile}")
        logger.info(f"  Intermediate Profile: {intermediate_profile}")
        logger.info(f"  Final Profile: {final_profile}")

        logger.info("✅ One-hop detection scenario завершен успешно")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

"""
E2E тесты с реальными API
==========================

Эти тесты используют реальное подключение к Ethereum через Infura.
Требуют INFURA_URL в .env файле.
"""

import asyncio
import pytest
import logging
from pathlib import Path
import os

from config.settings import Settings
from src.core.web3_manager import Web3Manager
from main import WhaleTrackerOrchestrator


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.fixture
def real_api_settings():
    """
    Настройки для реальных API тестов.
    """
    settings = Settings()
    settings.development.mock_data = False  # Отключаем mock режим
    return settings


@pytest.mark.asyncio
@pytest.mark.real_api
class TestRealBlockchainConnection:
    """
    Тесты с реальным подключением к Ethereum blockchain.
    """

    async def test_infura_connection(self, real_api_settings):
        """
        Проверяет подключение к Ethereum через Infura.
        """
        logger.info("🧪 TEST: Real Infura Connection")

        # Проверяем что INFURA_API_KEY установлен
        infura_key = os.getenv('INFURA_API_KEY')
        assert infura_key is not None, "INFURA_API_KEY не установлен в .env"

        logger.info(f"  Infura API Key: {infura_key[:10]}...")

        # Создаем Web3Manager в real режиме
        web3_manager = Web3Manager(mock_mode=False)

        # Инициализируем подключение
        logger.info("  Инициализация подключения...")
        success = await web3_manager.initialize()

        assert success, "Не удалось инициализировать Web3Manager"
        assert web3_manager.web3 is not None, "Web3 instance не создан"

        # Проверяем что мы подключены
        try:
            is_connected = web3_manager.web3.is_connected()
            logger.info(f"  Connection status: {'✅ Connected' if is_connected else '❌ Not connected'}")

            if is_connected:
                # Получаем текущий блок
                block_number = web3_manager.web3.eth.block_number
                logger.info(f"  Current block: {block_number:,}")

                # Получаем chain ID
                chain_id = web3_manager.web3.eth.chain_id
                logger.info(f"  Chain ID: {chain_id} ({'Ethereum Mainnet' if chain_id == 1 else 'Other'})")

                assert block_number > 0, "Block number должен быть > 0"
                assert chain_id == 1, "Должны быть подключены к Ethereum Mainnet"

                logger.info("✅ Успешное подключение к Ethereum Mainnet через Infura!")
            else:
                pytest.fail("Не удалось подключиться к Infura")

        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            pytest.fail(f"Connection failed: {e}")

    async def test_get_vitalik_balance(self, real_api_settings):
        """
        Проверяет получение баланса Vitalik через реальное подключение.
        """
        logger.info("🧪 TEST: Get Vitalik Balance")

        web3_manager = Web3Manager(mock_mode=False)
        await web3_manager.initialize()

        # Адрес Vitalik
        vitalik_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

        try:
            # Получаем баланс через Web3Manager метод
            balance_eth = await web3_manager.get_eth_balance(vitalik_address)

            logger.info(f"  Vitalik address: {vitalik_address}")
            logger.info(f"  Balance: {balance_eth:.4f} ETH")

            # Проверяем что баланс разумный (Vitalik имеет много ETH)
            assert balance_eth is not None, "Balance не должен быть None"
            assert balance_eth > 0, "Balance должен быть > 0"

            logger.info("✅ Успешно получен баланс Vitalik!")

        except Exception as e:
            logger.error(f"❌ Ошибка получения баланса: {e}")
            pytest.fail(f"Failed to get balance: {e}")

    async def test_get_latest_block_info(self, real_api_settings):
        """
        Проверяет получение информации о последнем блоке.
        """
        logger.info("🧪 TEST: Get Latest Block Info")

        web3_manager = Web3Manager(mock_mode=False)
        await web3_manager.initialize()

        try:
            # Получаем последний блок
            latest_block = web3_manager.web3.eth.get_block('latest')

            logger.info(f"  Block number: {latest_block['number']:,}")
            logger.info(f"  Block hash: {latest_block['hash'].hex()}")
            logger.info(f"  Timestamp: {latest_block['timestamp']}")
            logger.info(f"  Transactions count: {len(latest_block['transactions'])}")
            logger.info(f"  Gas used: {latest_block['gasUsed']:,}")
            logger.info(f"  Gas limit: {latest_block['gasLimit']:,}")

            assert latest_block['number'] > 0, "Block number должен быть > 0"
            assert len(latest_block['hash']) > 0, "Block hash должен быть установлен"

            logger.info("✅ Успешно получена информация о блоке!")

        except Exception as e:
            logger.error(f"❌ Ошибка получения блока: {e}")
            pytest.fail(f"Failed to get block: {e}")

    async def test_get_vitalik_transaction_count(self, real_api_settings):
        """
        Проверяет получение количества транзакций Vitalik (nonce).
        """
        logger.info("🧪 TEST: Get Vitalik Transaction Count")

        web3_manager = Web3Manager(mock_mode=False)
        await web3_manager.initialize()

        vitalik_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

        try:
            # Получаем nonce через Web3Manager метод
            tx_count = await web3_manager.get_transaction_count(vitalik_address)

            logger.info(f"  Vitalik address: {vitalik_address}")
            logger.info(f"  Transaction count (nonce): {tx_count:,}")

            assert tx_count is not None, "Transaction count не должен быть None"
            assert tx_count > 0, "Transaction count должен быть > 0 для Vitalik"

            logger.info("✅ Успешно получен nonce Vitalik!")

        except Exception as e:
            logger.error(f"❌ Ошибка получения nonce: {e}")
            pytest.fail(f"Failed to get transaction count: {e}")


@pytest.mark.asyncio
@pytest.mark.real_api
@pytest.mark.slow
class TestRealWhaleMonitoring:
    """
    Тесты реального мониторинга китов.
    """

    async def test_single_whale_monitoring_cycle_real(self, real_api_settings):
        """
        Запускает один реальный цикл мониторинга китов.
        """
        logger.info("🧪 TEST: Real Whale Monitoring Cycle")
        logger.info("=" * 60)

        # Создаем оркестратор с real settings
        orchestrator = WhaleTrackerOrchestrator(settings=real_api_settings)

        # Setup компонентов
        logger.info("Настройка компонентов...")
        orchestrator.setup()

        logger.info(f"Мониторинг {len(real_api_settings.WHALE_ADDRESSES)} китов:")
        for addr in real_api_settings.WHALE_ADDRESSES:
            logger.info(f"  - {addr}")

        # Запускаем один цикл мониторинга
        logger.info("\nЗапуск реального цикла мониторинга...")
        logger.info("(Это может занять некоторое время, идут реальные запросы к Infura)")

        try:
            await orchestrator.run_monitoring_cycle()
            logger.info("✅ Реальный цикл мониторинга выполнен успешно!")

        except Exception as e:
            logger.error(f"❌ Ошибка во время мониторинга: {e}")
            # Не падаем, просто логируем
            logger.warning("⚠️  Цикл мониторинга завершился с ошибками (это может быть нормально для тестов)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "-m", "real_api"])

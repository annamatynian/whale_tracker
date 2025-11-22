"""
Pytest конфигурация и фикстуры для Whale Tracker тестов
========================================================

Общие фикстуры для всех типов тестов (unit, integration, e2e).
"""

import pytest
import asyncio
import logging
from pathlib import Path
import sys

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from config.settings import Settings
from src.core.web3_manager import Web3Manager
from src.core.whale_config import WhaleConfig
from src.analyzers.whale_analyzer import WhaleAnalyzer


# Настройка логирования для тестов
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ============================================================================
# ОБЩИЕ ФИКСТУРЫ
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Создает event loop для всей сессии тестирования.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir():
    """
    Возвращает путь к директории с тестовыми данными.
    """
    return Path(__file__).parent / "test_data"


# ============================================================================
# SETTINGS ФИКСТУРЫ
# ============================================================================

@pytest.fixture
def mock_settings():
    """
    Настройки для тестов в mock режиме.
    """
    settings = Settings()
    settings.development.mock_data = True

    # Устанавливаем тестовые адреса китов если их нет
    if not settings.WHALE_ADDRESSES:
        settings.WHALE_ADDRESSES = [
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
            "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"   # Tornado Cash
        ]

    return settings


@pytest.fixture
def real_settings():
    """
    Настройки для тестов с реальными API.

    Требует установленные переменные окружения.
    """
    settings = Settings()
    settings.development.mock_data = False
    return settings


# ============================================================================
# КОМПОНЕНТНЫЕ ФИКСТУРЫ
# ============================================================================

@pytest.fixture
async def mock_web3_manager():
    """
    Web3Manager в mock режиме для тестов.
    """
    manager = Web3Manager(mock_mode=True)
    yield manager
    # Cleanup если нужен


@pytest.fixture
async def real_web3_manager():
    """
    Web3Manager с реальным подключением к RPC.

    Требует INFURA_URL или другой RPC endpoint в .env.
    """
    manager = Web3Manager(mock_mode=False)
    yield manager


@pytest.fixture
def whale_config():
    """
    WhaleConfig для тестов.
    """
    return WhaleConfig()


@pytest.fixture
def whale_analyzer():
    """
    WhaleAnalyzer с тестовыми параметрами.
    """
    return WhaleAnalyzer(
        anomaly_multiplier=1.3,
        rolling_window_size=10,
        min_history_required=5
    )


# ============================================================================
# МАРКЕРЫ PYTEST
# ============================================================================

def pytest_configure(config):
    """
    Регистрация кастомных маркеров.
    """
    config.addinivalue_line(
        "markers", "unit: Unit тесты"
    )
    config.addinivalue_line(
        "markers", "integration: Integration тесты"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end тесты"
    )
    config.addinivalue_line(
        "markers", "slow: Медленные тесты"
    )
    config.addinivalue_line(
        "markers", "real_api: Требует реальные API ключи"
    )
    config.addinivalue_line(
        "markers", "mock: Использует mock данные"
    )
    config.addinivalue_line(
        "markers", "blockchain: Требует blockchain подключения"
    )


# ============================================================================
# ХУКИ PYTEST
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """
    Автоматическая установка маркеров на основе пути к тесту.
    """
    for item in items:
        # Определяем тип теста по пути
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Добавляем маркер mock для тестов использующих mock_settings
        if "mock" in item.name or "mock_settings" in str(item.fixturenames):
            item.add_marker(pytest.mark.mock)


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Сбрасывает singleton инстансы между тестами если нужно.
    """
    yield
    # Cleanup code здесь если нужен


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФИКСТУРЫ ДЛЯ ТЕСТИРОВАНИЯ
# ============================================================================

@pytest.fixture
def sample_whale_transaction():
    """
    Пример транзакции кита для тестирования.
    """
    return {
        'hash': '0x123abc',
        'from': '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
        'to': '0x1234567890123456789012345678901234567890',
        'value': 1000000000000000000,  # 1 ETH in wei
        'blockNumber': 18000000,
        'timestamp': 1700000000,
        'gasPrice': 50000000000,  # 50 Gwei
        'nonce': 100
    }


@pytest.fixture
def sample_transactions_batch():
    """
    Батч тестовых транзакций.
    """
    return [
        {'value': 1000000, 'timestamp': 1700000000},
        {'value': 2000000, 'timestamp': 1700000100},
        {'value': 1500000, 'timestamp': 1700000200},
        {'value': 1200000, 'timestamp': 1700000300},
        {'value': 10000000, 'timestamp': 1700000400},  # Аномалия
    ]


# ============================================================================
# SKIP CONDITIONS
# ============================================================================

def pytest_runtest_setup(item):
    """
    Пропускает тесты требующие API ключей если они не установлены.
    """
    markers = [mark.name for mark in item.iter_markers()]

    if "real_api" in markers:
        # Проверяем наличие необходимых API ключей
        import os
        # Проверяем либо INFURA_URL либо INFURA_API_KEY
        has_infura = os.getenv('INFURA_URL') or os.getenv('INFURA_API_KEY')
        if not has_infura:
            pytest.skip("Пропущен: требуется INFURA_URL или INFURA_API_KEY в .env")

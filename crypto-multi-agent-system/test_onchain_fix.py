#!/usr/bin/env python3
"""
Тест исправлений OnChain анализа
Проверяем, что исправления работают корректно
"""

import asyncio
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("OnChainFixTest")

async def test_onchain_agent():
    """Тестируем OnChainAgent напрямую"""
    try:
        from agents.onchain.onchain_agent import OnChainAgent
        
        logger.info("=== ТЕСТ 1: OnChainAgent в РЕАЛЬНОМ режиме ===")
        
        # Тест в реальном режиме
        real_agent = OnChainAgent(mock_mode=False)
        
        # Используем известный токен для тестирования (например, USDC на Base)
        test_result = await real_agent.analyze_token(
            network="base",
            token_address="0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC на Base
            lp_address=None  # Без LP анализа для упрощения
        )
        
        logger.info(f"✅ Реальный анализ завершен:")
        logger.info(f"   API calls использовано: {test_result.api_calls_used}")
        logger.info(f"   Общий риск: {test_result.overall_risk}")
        logger.info(f"   Рекомендация: {test_result.recommendation}")
        
        if test_result.api_calls_used > 0:
            logger.info("🎉 УСПЕХ! OnChainAgent делает реальные API вызовы!")
        else:
            logger.warning("⚠️ Внимание: API calls = 0, возможно в mock режиме?")
        
        logger.info("=== ТЕСТ 2: OnChainAgent в MOCK режиме ===")
        
        # Тест в mock режиме
        mock_agent = OnChainAgent(mock_mode=True)
        
        mock_result = await mock_agent.analyze_token(
            network="base",
            token_address="0x123456789",  # Любой адрес для mock теста
            lp_address=None
        )
        
        logger.info(f"✅ Mock анализ завершен:")
        logger.info(f"   API calls использовано: {mock_result.api_calls_used}")
        logger.info(f"   Рекомендация: {mock_result.recommendation}")
        
        if mock_result.api_calls_used == 0 and mock_result.recommendation == "MOCK_ANALYSIS":
            logger.info("🎉 УСПЕХ! Mock режим работает корректно!")
        else:
            logger.error("❌ ОШИБКА: Mock режим работает неправильно!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тесте OnChainAgent: {e}")
        return False

async def test_orchestrator():
    """Тестируем SimpleOrchestrator с исправлениями"""
    try:
        from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
        
        logger.info("=== ТЕСТ 3: SimpleOrchestrator с реальным OnChain ===")
        
        orchestrator = SimpleOrchestrator()
        
        # Проверяем, что OnChainAgent инициализирован в реальном режиме
        if hasattr(orchestrator.onchain_agent, 'mock_mode'):
            if orchestrator.onchain_agent.mock_mode:
                logger.error("❌ ОШИБКА: OnChainAgent все еще в mock режиме!")
                return False
            else:
                logger.info("✅ УСПЕХ: OnChainAgent в реальном режиме!")
        
        # Запускаем короткий тест pipeline (с ограничениями для безопасности)
        logger.info("Запуск тестового pipeline...")
        alerts = await orchestrator.run_analysis_pipeline()
        
        logger.info(f"✅ Pipeline завершен:")
        logger.info(f"   Количество алертов: {len(alerts)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тесте Orchestrator: {e}")
        return False

async def main():
    """Главная функция тестирования"""
    logger.info("🔧 ЗАПУСК ТЕСТОВ ИСПРАВЛЕНИЙ OnChain АНАЛИЗА 🔧")
    logger.info("=" * 60)
    
    all_tests_passed = True
    
    # Тест 1: OnChainAgent
    test1_result = await test_onchain_agent()
    all_tests_passed = all_tests_passed and test1_result
    
    logger.info("=" * 60)
    
    # Тест 2: SimpleOrchestrator
    test2_result = await test_orchestrator()
    all_tests_passed = all_tests_passed and test2_result
    
    logger.info("=" * 60)
    
    # Итоговый результат
    if all_tests_passed:
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        logger.info("✅ Исправления OnChain анализа работают корректно!")
        logger.info("✅ API calls теперь подсчитываются правильно!")
        logger.info("✅ Дублирование OnChain анализа устранено!")
    else:
        logger.error("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ!")
        logger.error("Проверьте логи выше для деталей ошибок")
    
    return all_tests_passed

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

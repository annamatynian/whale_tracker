"""
Unit-тест для SimpleOrchestrator

Тестирует ОСНОВНУЮ ЛОГИКУ оркестратора в ИЗОЛЯЦИИ от реальных API.
Использует mock-объекты для имитации ответов от агентов и клиентов.

Автор: Crypto Multi-Agent Team
"""
import asyncio
import unittest
import logging
from unittest.mock import patch, MagicMock, AsyncMock

# --- Абсолютные импорты от корня проекта ---
from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
from agents.pump_analysis.pump_models import PumpAnalysisReport, PumpIndicators, NarrativeType
from agents.pump_analysis.realistic_scoring import PumpRecommendationMVP

class TestSimpleOrchestrator(unittest.TestCase):

    def setUp(self):
        """Настраивает окружение для каждого теста."""
        print("\n--- Тестирование логики конвейера Оркестратора ---")
        # Отключаем логирование во время тестов, чтобы вывод был чище
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        """Восстанавливает окружение после каждого теста."""
        logging.disable(logging.NOTSET)

    @patch('agents.orchestrator.simple_orchestrator.find_narrative_in_categories')
    @patch('agents.orchestrator.simple_orchestrator.GoPlusClient')
    @patch('agents.orchestrator.simple_orchestrator.CoinGeckoClient')
    @patch('agents.orchestrator.simple_orchestrator.PumpDiscoveryAgent')
    def test_pipeline_generates_alert_for_medium_potential(self, mock_pump_agent, mock_coingecko, mock_goplus, mock_find_narrative):
        """
        ФИНАЛЬНЫЙ ТЕСТ 1: Проверяем, что для токена со СРЕДНИМ ПОТЕНЦИАЛОМ (балл 75) генерируется алерт.
        """
        print("\n--- Сценарий 1: Токен со средним потенциалом ---")
        # --- Arrange (Подготовка) ---
        mock_agent_instance = mock_pump_agent.return_value
        mock_indicators = PumpIndicators(contract_address="0x123")
        mock_report = PumpAnalysisReport(
            contract_address="0x123", chain_id="base", token_symbol="GOOD",
            token_name="Good Token", final_score=85, # Предварительный балл высокий, чтобы пройти фильтр
            indicators=mock_indicators, narrative_score=0, security_score=0,
            social_score=0, confidence_level=0.8, reasoning=[], next_steps=[]
        )
        # Настраиваем AsyncMock для имитации асинхронного вызова
        mock_agent_instance.discover_tokens_async = AsyncMock(return_value=[mock_report])

        # Настраиваем "моки" для клиентов
        mock_goplus_instance = mock_goplus.return_value
        mock_goplus_instance.get_token_security.return_value = {"is_honeypot": "0", "is_open_source": "1", "buy_tax": "0.01", "sell_tax": "0.01"}
        
        mock_coingecko_instance = mock_coingecko.return_value
        mock_coingecko_instance.get_token_info_by_contract.return_value = {"categories": ["artificial-intelligence"], "community_score": 70}
        
        # Настраиваем "мок" для "умного переводчика"
        mock_find_narrative.return_value = NarrativeType.AI
        
        # --- Act (Действие) ---
        orchestrator = SimpleOrchestrator()
        alerts = asyncio.run(orchestrator.run_analysis_pipeline())
        
        # --- Assert (Проверка) ---
        self.assertEqual(len(alerts), 1, "Должен был быть сгенерирован 1 алерт")
        alert = alerts[0]
        
        expected_score = 75 # 40 (Narrative) + 35 (Security) + 0 (Social)
        self.assertEqual(alert['final_score'], expected_score, f"Финальный балл должен быть {expected_score}")
        self.assertEqual(alert['recommendation'], PumpRecommendationMVP.MEDIUM_POTENTIAL, "Рекомендация должна быть MEDIUM_POTENTIAL")
        
        # Проверяем, что "умный переводчик" был вызван
        mock_find_narrative.assert_called_once()


    @patch('agents.orchestrator.simple_orchestrator.PumpDiscoveryAgent')
    def test_pipeline_skips_low_potential(self, mock_pump_agent):
        """
        ФИНАЛЬНЫЙ ТЕСТ 2: Проверяем, что для токена с НИЗКИМ ПОТЕНЦИАЛОМ глубокий анализ НЕ выполняется.
        """
        print("\n--- Сценарий 2: Токен с низким потенциалом ---")
        # --- Arrange ---
        mock_agent_instance = mock_pump_agent.return_value
        mock_report = PumpAnalysisReport(
            contract_address="0x456", chain_id="base", token_symbol="BAD",
            token_name="Bad Token", final_score=40, # Низкий предварительный балл
            indicators=PumpIndicators(contract_address="0x456"), narrative_score=0,
            security_score=0, social_score=0, confidence_level=0.3, reasoning=[], next_steps=[]
        )
        mock_agent_instance.discover_tokens_async = AsyncMock(return_value=[mock_report])

        # --- Act ---
        orchestrator = SimpleOrchestrator()
        with patch('agents.orchestrator.simple_orchestrator.GoPlusClient') as mock_goplus, \
             patch('agents.orchestrator.simple_orchestrator.CoinGeckoClient') as mock_coingecko:
            
            alerts = asyncio.run(orchestrator.run_analysis_pipeline())

            # --- Assert ---
            self.assertEqual(len(alerts), 0, "Не должно быть сгенерировано алертов")
            # Проверяем, что дорогие API вызовы НЕ были сделаны
            mock_goplus.return_value.get_token_security.assert_not_called()
            mock_coingecko.return_value.get_token_info_by_contract.assert_not_called()

if __name__ == '__main__':
    unittest.main()

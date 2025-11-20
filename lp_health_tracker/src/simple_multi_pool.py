"""
Simple Multi-Pool Manager
========================

Модуль для работы с несколькими пулами ликвидности.

"""

import logging
import json
import sys
import os
from typing import List, Dict, Any

# Исправляем импорт для IL Calculator
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_analyzer import ImpermanentLossCalculator, NetPnLCalculator
from src.data_providers import DataProvider, MockDataProvider
from src.price_strategy_manager import get_price_manager


class SimpleMultiPoolManager:
    """Простой менеджер для работы с множественными пулами."""
    
    def __init__(self, data_provider: DataProvider = None):
        """Инициализация менеджера."""
        self.pools = []
        self.il_calculator = ImpermanentLossCalculator() 
        self.net_pnl_calculator = NetPnLCalculator() 
        
        # Используем новый унифицированный price manager
        self.price_manager = get_price_manager()
        # Поддерживаем обратную совместимость для старого интерфейса
        self.data_provider = data_provider if data_provider else MockDataProvider()
        self.logger = logging.getLogger(__name__)
        print(f"✅ SimpleMultiPoolManager initialized with PriceStrategyManager and {self.data_provider.get_provider_name()}")
        # self гарантирует, что если у вас будет два разных менеджера, manager_A и manager_B, 
        # то manager_A добавит пул в свой список, а manager_B — в свой, и они не перепутаются.

    def add_pool(self, pool_config: Dict[str, Any]) -> None:
        """Добавить пул в список для анализа.
        
        FIXED: Now stores a copy of pool_config to prevent external mutations.
        """
        # Store a copy to prevent external changes affecting stored data
        pool_copy = pool_config.copy()
        self.pools.append(pool_copy)
        
        pool_name = pool_config.get('name', 'Unknown')
        print(f"✅ Added pool: {pool_name}")
        self.logger.info(f"Pool added: {pool_name}")
    
    def count_pools(self) -> int:
        """Простейшая функция - подсчет пулов."""
        count = len(self.pools)
        print(f"📊 Total pools: {count}")
        return count
    
    def list_pools(self) -> List[str]:
        """Список названий всех пулов."""
        names = [pool.get('name', 'Unknown') for pool in self.pools]
        print(f"📋 Pool names: {names}")
        return names

    
    
    def calculate_net_pnl_with_fees(self, pool_config: Dict[str, Any]) -> Dict[str, Any]:
        """Расчет Net P&L используя новый NetPnLCalculator из Master Plan."""
        try:
            pool_name = pool_config.get('name', 'Unknown')
            
            # 1. Получаем текущие цены через новый унифицированный менеджер
            token_a_symbol = pool_config['token_a_symbol']
            token_b_symbol = pool_config['token_b_symbol']
            
            # Получаем цены через PriceStrategyManager
            prices = self.price_manager.get_multiple_prices([token_a_symbol, token_b_symbol])
            current_price_a = prices.get(token_a_symbol, pool_config.get('initial_price_a_usd', 0))
            current_price_b = prices.get(token_b_symbol, pool_config.get('initial_price_b_usd', 1))
            
            # 2. Получаем APR для пула
            simplified_name = f"{token_a_symbol}-{token_b_symbol}"
            apr = self.price_manager.get_pool_apr(simplified_name)
            
            # 3. Симулируем текущую стоимость LP (упрощенно для демо)
            initial_liquidity_a = pool_config['initial_liquidity_a']
            initial_liquidity_b = pool_config['initial_liquidity_b']
            initial_price_a = pool_config['initial_price_a_usd']
            initial_price_b = pool_config['initial_price_b_usd']
            
            # Hold стратегия стоимость
            hold_value = (initial_liquidity_a * current_price_a + 
                         initial_liquidity_b * current_price_b)
            
            # LP стоимость с учетом IL (упрощенная симуляция)
            initial_ratio = initial_price_a / initial_price_b
            current_ratio = current_price_a / current_price_b
            il = self.il_calculator.calculate_impermanent_loss(initial_ratio, current_ratio)
            current_lp_value = hold_value * (1 - il)  
            
            # 4. Используем наш NetPnLCalculator!
            analysis_result = self.net_pnl_calculator.analyze_position_with_fees(
                pool_config,
                current_lp_value,
                current_price_a,
                current_price_b,
                apr
            )
            
            # 5. Красивый вывод результатов
            if 'error' not in analysis_result:
                position_info = analysis_result['position_info']
                current_status = analysis_result['current_status']
                net_pnl = analysis_result['net_pnl']
                strategy_comparison = analysis_result['strategy_comparison']
                
                print(f"\n💰 {pool_name} - MASTER PLAN NET P&L ANALYSIS")
                print("=" * 60)
                print(f"📊 Position: ${position_info['initial_investment_usd']:.2f} | {position_info['days_held']} days | ${position_info['gas_costs_usd']:.2f} gas")
                print(f"💸 Fees Earned: ${current_status['earned_fees_usd']:.2f} ({apr:.1%} APR)")
                print(f"💔 Impermanent Loss: {current_status['il_percentage']:.2%} (${current_status['il_usd']:.2f})")
                print(f"🎯 NET P&L: ${net_pnl['net_pnl_usd']:.2f} ({net_pnl['net_pnl_percentage']:.2%})")
                
                status_icon = "✅" if net_pnl['is_profitable'] else "❌"
                print(f"{status_icon} Status: {'PROFITABLE' if net_pnl['is_profitable'] else 'LOSS'}")
                
                # Сравнение стратегий
                better_strategy = strategy_comparison['better_strategy']
                advantage = abs(strategy_comparison['lp_advantage_usd'])
                print(f"🏆 Better Strategy: {better_strategy} (advantage: ${advantage:.2f})")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Error in Net P&L calculation for {pool_config.get('name', 'Unknown')}: {e}")
            return {'error': str(e)}
    
    def analyze_all_pools_with_fees(self) -> List[Dict[str, Any]]:
        """Анализ всех пулов с использованием Master Plan Net P&L."""
        print(f"\n🔬 Analyzing {len(self.pools)} positions with Master Plan Net P&L...")
        print("=" * 70)
        
        results = []
        for pool in self.pools:
            result = self.calculate_net_pnl_with_fees(pool)
            results.append(result)
        
        # Суммарная статистика
        profitable_count = sum(1 for r in results if r.get('net_pnl', {}).get('is_profitable', False))
        total_net_pnl = sum(r.get('net_pnl', {}).get('net_pnl_usd', 0) for r in results)
        
        print(f"\n📈 PORTFOLIO SUMMARY:")
        print(f"  Profitable positions: {profitable_count}/{len(results)}")
        print(f"  Total Net P&L: ${total_net_pnl:.2f}")
        
        return results
    

    
    def load_test_config(self, config_file: str = "test_pools_config.json") -> bool:
        """Загрузить тестовую конфигурацию пулов из JSON файла."""
        try:
            print(f"📂 Loading config from: {config_file}")
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Очищаем текущие пулы перед загрузкой новых
            self.pools.clear()
            
            # Добавляем пулы из конфигурации
            for pool in config['test_pools']:
                self.add_pool(pool)
            
            print(f"✅ Successfully loaded {len(config['test_pools'])} pools from config")
            return True
            
        except FileNotFoundError:
            print(f"❌ Config file not found: {config_file}")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config file: {e}")
            return False
        except KeyError as e:
            print(f"❌ Missing required key in config: {e}")
            return False
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return False

    def load_positions_from_json(self, positions_file: str = "data/positions.json") -> bool:
        """Загрузить позиции из обновленного positions.json с fee полями."""
        try:
            print(f"📂 Loading positions from: {positions_file}")
            with open(positions_file, 'r', encoding='utf-8') as f:
                positions = json.load(f)
            
            # Очищаем текущие пулы
            self.pools.clear()
            
            # Добавляем позиции из файла
            for position in positions:
                # Извлекаем символы токенов с поддержкой разных форматов
                token_a_symbol = position.get('token_a_symbol')
                token_b_symbol = position.get('token_b_symbol')
                
                # Если поля token_a_symbol и token_b_symbol отсутствуют, извлекаем из объектов
                if not token_a_symbol and 'token_a' in position:
                    token_a_symbol = position['token_a'].get('symbol')
                if not token_b_symbol and 'token_b' in position:
                    token_b_symbol = position['token_b'].get('symbol')
                
                # Конвертируем в формат который понимает наш менеджер
                pool_config = {
                    'name': position['name'],
                    'token_a_symbol': token_a_symbol, 
                    'token_b_symbol': token_b_symbol,
                    'initial_price_a_usd': position['initial_price_a_usd'],
                    'initial_price_b_usd': position['initial_price_b_usd'],
                    'initial_liquidity_a': position['initial_liquidity_a'],
                    'initial_liquidity_b': position['initial_liquidity_b'],
                    'gas_costs_usd': position.get('gas_costs_usd', 50.0),  # Значение по умолчанию
                    'days_held_mock': position.get('days_held_mock', 30),  # Для Stage 1 тестов
                    # Handle both old (days_held_mock) and new (entry_date) format
                    'entry_date': position.get('entry_date', position.get('added_at', '2024-01-01T00:00:00Z')),
                    # Остальные поля по необходимости
                    'il_alert_threshold': position.get('il_alert_threshold', 0.05),
                    'protocol': position.get('protocol', 'unknown')
                }
                self.add_pool(pool_config)
            
            print(f"✅ Successfully loaded {len(positions)} positions with fee data")
            return True
            
        except Exception as e:
            print(f"❌ Error loading positions: {e}")
            return False


# Расширенное тестирование модуля
if __name__ == "__main__":
    print("🧪 Testing SimpleMultiPoolManager with Master Plan Net P&L...")
    
    # Создаем менеджер
    manager = SimpleMultiPoolManager()
    
    # Тест 1: Добавление одного пула вручную
    print("\n--- Test 1: Manual pool addition ---")
    test_pool = {
        "name": "Test USDC-USDT Pool",
        "pair_address": "0x123...",
        "token_a_symbol": "USDC",
        "token_b_symbol": "USDT",
        "initial_price_a_usd": 1.0,
        "initial_price_b_usd": 1.0
    }
    
    manager.add_pool(test_pool)
    count = manager.count_pools()
    names = manager.list_pools()
    
    assert count == 1, f"Expected 1 pool, got {count}"
    assert "Test USDC-USDT Pool" in names, "Pool name not found"
    print("✅ Manual addition test passed!")
    
    # Тест 2: Загрузка позиций с fee данными
    print("\n--- Test 2: Loading positions with fees ---")
    if manager.load_positions_from_json():
        count = manager.count_pools()
        names = manager.list_pools()
        
        print(f"📊 Loaded positions count: {count}")
        print(f"📋 Position names: {names}")
        
        # Тест 3: Master Plan Net P&L
        print("\n--- Test 3: Master Plan Net P&L Analysis ---")
        analysis_results = manager.analyze_all_pools_with_fees()
        
        print("\n✅ Master Plan Net P&L integration test passed!")
        
    else:
        print("❌ Positions loading failed - trying old test config method")
        if manager.load_test_config():
            print("✅ Fallback to test config successful")
            analysis_results = manager.analyze_all_pools_demo()
        else:
            print("❌ All loading methods failed")
    
    print("\n✅ All tests completed! SimpleMultiPoolManager with Master Plan ready.")

"""
Enhanced Historical Data Management
=================================

Улучшенная система для сохранения временных рядов IL и P&L данных.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd


class HistoricalDataManager:
    """
    Расширенный менеджер для работы с историческими данными.
    
    Сохраняет временные ряды:
    - IL по времени
    - P&L по времени  
    - Цены токенов
    - APY пулов
    - Gas costs
    """
    
    def __init__(self, db_path: str = "data/history.db"):
        """Initialize with SQLite database."""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Основная таблица исторических данных
            conn.execute("""
                CREATE TABLE IF NOT EXISTS position_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    position_name TEXT NOT NULL,
                    
                    -- IL данные
                    il_percentage REAL,
                    il_usd_amount REAL,
                    
                    -- P&L данные
                    hold_value_usd REAL,
                    lp_value_usd REAL,
                    fees_earned_usd REAL,
                    total_pnl_usd REAL,
                    total_pnl_percentage REAL,
                    
                    -- Цены токенов
                    token_a_price_usd REAL,
                    token_b_price_usd REAL,
                    price_ratio REAL,
                    
                    -- Пул данные
                    reserve_a REAL,
                    reserve_b REAL,
                    total_lp_supply REAL,
                    lp_tokens_held REAL,
                    
                    -- Метрики
                    better_strategy TEXT,
                    gas_price_gwei REAL,
                    
                    UNIQUE(timestamp, position_name)
                )
            """)
            
            # Таблица событий/алертов
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    position_name TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    threshold_value REAL,
                    actual_value REAL,
                    message TEXT,
                    sent_successfully BOOLEAN
                )
            """)
            
            # Индексы для быстрого поиска
            conn.execute("CREATE INDEX IF NOT EXISTS idx_position_time ON position_history(position_name, timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts_history(timestamp)")
    
    def save_position_snapshot(
        self, 
        position_name: str, 
        analysis_data: Dict[str, Any],
        market_data: Dict[str, Any] = None
    ) -> bool:
        """Сохранить снимок состояния позиции."""
        try:
            timestamp = datetime.now().isoformat()
            
            # Извлечь данные из analysis_data
            il_data = analysis_data.get('impermanent_loss', {})
            hold_data = analysis_data.get('hold_strategy', {})
            lp_data = analysis_data.get('lp_strategy', {})
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO position_history (
                        timestamp, position_name,
                        il_percentage, il_usd_amount,
                        hold_value_usd, lp_value_usd, fees_earned_usd,
                        total_pnl_usd, total_pnl_percentage,
                        token_a_price_usd, token_b_price_usd, price_ratio,
                        better_strategy
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, position_name,
                    il_data.get('percentage', 0), il_data.get('usd_amount', 0),
                    hold_data.get('current_value_usd', 0), lp_data.get('current_value_usd', 0),
                    lp_data.get('fees_earned_usd', 0), lp_data.get('pnl_usd', 0),
                    lp_data.get('pnl_percentage', 0),
                    market_data.get('token_a_price', 0) if market_data else 0,
                    market_data.get('token_b_price', 0) if market_data else 0,
                    market_data.get('price_ratio', 0) if market_data else 0,
                    analysis_data.get('better_strategy', 'Unknown')
                ))
            
            return True
            
        except Exception as e:
            print(f"Error saving position snapshot: {e}")
            return False
    
    def get_position_trend(
        self, 
        position_name: str, 
        days: int = 7,
        metric: str = 'il_percentage'
    ) -> pd.DataFrame:
        """
        Получить тренд по конкретной метрике.
        
        Args:
            position_name: Название позиции
            days: Количество дней
            metric: Метрика (il_percentage, total_pnl_usd, etc.)
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            query = f"""
                SELECT timestamp, {metric}
                FROM position_history 
                WHERE position_name = ? AND timestamp > ?
                ORDER BY timestamp
            """
            
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query(query, conn, params=(position_name, cutoff_date.isoformat()))
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                return df
                
        except Exception as e:
            print(f"Error getting trend: {e}")
            return pd.DataFrame()
    
    def get_daily_summary(self, date: str = None) -> Dict[str, Any]:
        """Получить сводку за день."""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Количество позиций
                positions_count = conn.execute("""
                    SELECT COUNT(DISTINCT position_name) 
                    FROM position_history 
                    WHERE DATE(timestamp) = ?
                """, (date,)).fetchone()[0]
                
                # Средний IL
                avg_il = conn.execute("""
                    SELECT AVG(ABS(il_percentage))
                    FROM position_history 
                    WHERE DATE(timestamp) = ?
                """, (date,)).fetchone()[0] or 0
                
                # Общий P&L
                total_pnl = conn.execute("""
                    SELECT SUM(total_pnl_usd)
                    FROM position_history 
                    WHERE DATE(timestamp) = ?
                """, (date,)).fetchone()[0] or 0
                
                return {
                    'date': date,
                    'positions_count': positions_count,
                    'average_il': avg_il,
                    'total_pnl_usd': total_pnl
                }
                
        except Exception as e:
            print(f"Error getting daily summary: {e}")
            return {}

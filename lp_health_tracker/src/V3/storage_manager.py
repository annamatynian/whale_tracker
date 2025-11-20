import os
import csv
import sqlite3
import pandas as pd
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

from .hmm_market_data_collector import MarketDataPoint

logger = logging.getLogger(__name__)

class StorageManager:
    """
    Универсальный менеджер хранения данных.
    Поддерживает CSV (по умолчанию) и SQLite (опционально).
    
    Простота использования - основной приоритет.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.backend = config.get('backend', 'csv')
        
        # CSV настройки
        self.csv_enabled = config.get('csv', {}).get('enabled', True)
        self.csv_filename = config.get('csv', {}).get('filename', 'market_data_v3_detailed.csv')
        
        # SQLite настройки  
        self.sqlite_enabled = config.get('sqlite', {}).get('enabled', False)
        self.sqlite_filename = config.get('sqlite', {}).get('filename', 'market_data.db')
        self.table_name = config.get('sqlite', {}).get('table_name', 'market_data_points')
        
        # CSV заголовки
        self.csv_headers = list(MarketDataPoint.model_fields.keys())
        
        # Инициализация
        self._setup_storage()
        
        logger.info(f"Storage Manager инициализирован: backend={self.backend}")
    
    def _setup_storage(self):
        """Настройка хранилищ данных."""
        if self.csv_enabled:
            self._setup_csv()
        
        if self.sqlite_enabled:
            self._setup_sqlite()
    
    def _setup_csv(self):
        """Настройка CSV файла."""
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_headers)
                writer.writeheader()
            logger.info(f"CSV файл создан: {self.csv_filename}")
    
    def _setup_sqlite(self):
        """Настройка SQLite базы данных."""
        conn = sqlite3.connect(self.sqlite_filename)
        
        # Создание таблицы
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER NOT NULL,
            datetime TEXT NOT NULL,
            eth_price_usd REAL NOT NULL,
            log_return REAL NOT NULL,
            dex_volume_usd REAL NOT NULL,
            cex_volume_usd REAL NOT NULL,
            dex_cex_volume_ratio REAL NOT NULL,
            hourly_volume_vs_24h_avg_pct REAL NOT NULL,
            tvl_usd REAL NOT NULL,
            net_liquidity_change_usd REAL NOT NULL,
            avg_priority_fee_gwei REAL NOT NULL,
            var_priority_fee_gwei REAL NOT NULL,
            outlier_detected BOOLEAN NOT NULL,
            max_priority_fee_gwei REAL NOT NULL,
            outlier_percentage REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        
        conn.execute(create_table_sql)
        
        # Создание индексов для быстрых запросов
        indexes = self.config.get('sqlite', {}).get('indexes', ['timestamp'])
        for index_column in indexes:
            try:
                conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{index_column} ON {self.table_name}({index_column})")
            except sqlite3.Error as e:
                logger.warning(f"Не удалось создать индекс для {index_column}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"SQLite база данных настроена: {self.sqlite_filename}")
    
    def write_data_point(self, data_point: MarketDataPoint):
        """
        Записывает одну точку данных в выбранное хранилище.
        
        Args:
            data_point: Валидированная точка данных
        """
        if self.backend == 'csv' or self.backend == 'both':
            self._write_to_csv(data_point)
        
        if self.backend == 'sqlite' or self.backend == 'both':
            self._write_to_sqlite(data_point)
    
    def write_data_points(self, data_points: List[MarketDataPoint]):
        """
        Записывает множество точек данных (батчевая запись).
        
        Args:
            data_points: Список валидированных точек данных
        """
        if not data_points:
            return
        
        if self.backend == 'csv' or self.backend == 'both':
            self._write_batch_to_csv(data_points)
        
        if self.backend == 'sqlite' or self.backend == 'both':
            self._write_batch_to_sqlite(data_points)
        
        logger.info(f"Записано {len(data_points)} точек данных")
    
    def _write_to_csv(self, data_point: MarketDataPoint):
        """Запись одной точки в CSV."""
        try:
            with open(self.csv_filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_headers)
                writer.writerow(data_point.model_dump())
        except IOError as e:
            logger.error(f"Ошибка записи в CSV: {e}")
    
    def _write_batch_to_csv(self, data_points: List[MarketDataPoint]):
        """Батчевая запись в CSV."""
        try:
            with open(self.csv_filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_headers)
                for data_point in data_points:
                    writer.writerow(data_point.model_dump())
        except IOError as e:
            logger.error(f"Ошибка батчевой записи в CSV: {e}")
    
    def _write_to_sqlite(self, data_point: MarketDataPoint):
        """Запись одной точки в SQLite."""
        self._write_batch_to_sqlite([data_point])
    
    def _write_batch_to_sqlite(self, data_points: List[MarketDataPoint]):
        """Батчевая запись в SQLite."""
        if not self.sqlite_enabled:
            return
        
        try:
            conn = sqlite3.connect(self.sqlite_filename)
            
            # Подготавливаем данные для вставки
            insert_sql = f"""
            INSERT INTO {self.table_name} (
                timestamp, datetime, eth_price_usd, log_return, dex_volume_usd, 
                cex_volume_usd, dex_cex_volume_ratio, hourly_volume_vs_24h_avg_pct,
                tvl_usd, net_liquidity_change_usd, avg_priority_fee_gwei,
                var_priority_fee_gwei, outlier_detected, max_priority_fee_gwei,
                outlier_percentage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            data_tuples = []
            for dp in data_points:
                data_tuples.append((
                    dp.timestamp, dp.datetime, dp.eth_price_usd, dp.log_return,
                    dp.dex_volume_usd, dp.cex_volume_usd, dp.dex_cex_volume_ratio,
                    dp.hourly_volume_vs_24h_avg_pct, dp.tvl_usd, dp.net_liquidity_change_usd,
                    dp.avg_priority_fee_gwei, dp.var_priority_fee_gwei, dp.outlier_detected,
                    dp.max_priority_fee_gwei, dp.outlier_percentage
                ))
            
            conn.executemany(insert_sql, data_tuples)
            conn.commit()
            conn.close()
            
        except sqlite3.Error as e:
            logger.error(f"Ошибка записи в SQLite: {e}")
    
    def read_data_as_dataframe(self, 
                              start_date: Optional[str] = None, 
                              end_date: Optional[str] = None,
                              limit: Optional[int] = None) -> pd.DataFrame:
        """
        Читает данные и возвращает pandas DataFrame.
        
        Args:
            start_date: Начальная дата в формате 'YYYY-MM-DD'
            end_date: Конечная дата в формате 'YYYY-MM-DD'  
            limit: Максимальное количество записей
            
        Returns:
            pandas.DataFrame с данными
        """
        if self.backend == 'sqlite' and self.sqlite_enabled:
            return self._read_from_sqlite_as_df(start_date, end_date, limit)
        else:
            return self._read_from_csv_as_df(start_date, end_date, limit)
    
    def _read_from_csv_as_df(self, start_date=None, end_date=None, limit=None) -> pd.DataFrame:
        """Чтение из CSV как DataFrame."""
        if not os.path.exists(self.csv_filename):
            return pd.DataFrame()
        
        df = pd.read_csv(self.csv_filename)
        
        # Фильтрация по датам
        if start_date or end_date:
            df['datetime_parsed'] = pd.to_datetime(df['datetime'])
            if start_date:
                df = df[df['datetime_parsed'] >= start_date]
            if end_date:
                df = df[df['datetime_parsed'] <= end_date]
            df = df.drop('datetime_parsed', axis=1)
        
        # Лимит записей
        if limit:
            df = df.tail(limit)
        
        return df
    
    def _read_from_sqlite_as_df(self, start_date=None, end_date=None, limit=None) -> pd.DataFrame:
        """Чтение из SQLite как DataFrame."""
        if not os.path.exists(self.sqlite_filename):
            return pd.DataFrame()
        
        query = f"SELECT * FROM {self.table_name}"
        conditions = []
        
        if start_date:
            conditions.append(f"datetime >= '{start_date}'")
        if end_date:
            conditions.append(f"datetime <= '{end_date}'")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY timestamp"
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            conn = sqlite3.connect(self.sqlite_filename)
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except sqlite3.Error as e:
            logger.error(f"Ошибка чтения из SQLite: {e}")
            return pd.DataFrame()
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику по хранилищу."""
        stats = {}
        
        if self.csv_enabled and os.path.exists(self.csv_filename):
            file_size = os.path.getsize(self.csv_filename)
            with open(self.csv_filename, 'r') as f:
                line_count = sum(1 for line in f) - 1  # Минус заголовок
            
            stats['csv'] = {
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'record_count': line_count,
                'last_modified': datetime.fromtimestamp(os.path.getmtime(self.csv_filename))
            }
        
        if self.sqlite_enabled and os.path.exists(self.sqlite_filename):
            try:
                conn = sqlite3.connect(self.sqlite_filename)
                cursor = conn.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                record_count = cursor.fetchone()[0]
                conn.close()
                
                file_size = os.path.getsize(self.sqlite_filename)
                
                stats['sqlite'] = {
                    'file_size_mb': round(file_size / (1024 * 1024), 2),
                    'record_count': record_count,
                    'last_modified': datetime.fromtimestamp(os.path.getmtime(self.sqlite_filename))
                }
            except sqlite3.Error as e:
                logger.error(f"Ошибка получения статистики SQLite: {e}")
        
        return stats

# Удобная функция для быстрого создания storage manager
def create_storage_manager(config_path: Optional[str] = None) -> StorageManager:
    """
    Создает Storage Manager с конфигурацией по умолчанию.
    
    Args:
        config_path: Путь к файлу конфигурации (опционально)
        
    Returns:
        Настроенный StorageManager
    """
    if config_path and os.path.exists(config_path):
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f).get('storage', {})
    else:
        # Конфигурация по умолчанию (только CSV)
        config = {
            'backend': 'csv',
            'csv': {
                'enabled': True,
                'filename': 'market_data_v3_detailed.csv'
            },
            'sqlite': {
                'enabled': False
            }
        }
    
    return StorageManager(config)

import os
import yaml
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional

class HistoricalDataConfig(BaseModel):
    """Pydantic модель для валидации конфигурации Historical Data Backfiller."""
    
    # Date range settings
    start_date: str = Field(..., description="Start date for historical data collection")
    end_date: str = Field(..., description="End date for historical data collection")
    time_interval: str = Field(default="daily", description="Collection interval")
    api_delay_seconds: int = Field(default=2, gt=0, description="Delay between API calls")
    
    # Output settings
    csv_filename: str = Field(default="historical_macro_data.csv")
    backup_existing: bool = Field(default=True)
    
    # Data sources
    enabled_metrics: List[str] = Field(default_factory=list)
    unavailable_metrics: List[str] = Field(default_factory=list)
    
    # API settings
    max_days_per_request: int = Field(default=90, gt=0)
    max_records_per_query: int = Field(default=1000, gt=0)
    max_records_per_request: int = Field(default=1000, gt=0)
    
    # Default values for unavailable metrics
    default_avg_priority_fee_gwei: float = Field(default=20.0, ge=0.0)
    default_var_priority_fee_gwei: float = Field(default=0.0, ge=0.0)
    default_outlier_detected: bool = Field(default=False)
    default_max_priority_fee_gwei: float = Field(default=0.0, ge=0.0)
    default_outlier_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    default_net_liquidity_change_usd: float = Field(default=0.0)
    default_dex_cex_volume_ratio: float = Field(default=1.0, ge=0.0)
    default_hourly_volume_vs_24h_avg_pct: float = Field(default=100.0, ge=0.0)
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        """Проверяем формат даты YYYY-MM-DD."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Дата должна быть в формате YYYY-MM-DD')
    
    @field_validator('time_interval')
    @classmethod
    def validate_interval(cls, v):
        """Проверяем допустимые интервалы."""
        allowed = ["hourly", "daily"]
        if v not in allowed:
            raise ValueError(f'time_interval должен быть одним из: {allowed}')
        return v
    
    def get_date_range(self):
        """Возвращает список дат для обработки."""
        start = datetime.strptime(self.start_date, '%Y-%m-%d')
        end = datetime.strptime(self.end_date, '%Y-%m-%d')
        
        if self.time_interval == "daily":
            delta = timedelta(days=1)
        else:  # hourly
            delta = timedelta(hours=1)
        
        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += delta
        
        return dates

def load_historical_config() -> HistoricalDataConfig:
    """Загружает конфигурацию для historical data backfiller из YAML файлов."""
    
    # Определяем пути к файлам конфигурации
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    base_config_path = os.path.join(config_dir, 'base.yaml')
    historical_config_path = os.path.join(config_dir, 'historical_data.yaml')
    env_config_path = os.path.join(config_dir, 'environments', 'development.yaml')
    
    # Загружаем базовую конфигурацию
    with open(base_config_path, 'r', encoding='utf-8') as f:
        base_config = yaml.safe_load(f)
    
    # Загружаем конфигурацию исторических данных
    with open(historical_config_path, 'r', encoding='utf-8') as f:
        historical_config = yaml.safe_load(f)
    
    # Загружаем environment-specific конфигурацию
    with open(env_config_path, 'r', encoding='utf-8') as f:
        env_config = yaml.safe_load(f)
    
    # Объединяем конфигурации с приоритетом: env > historical > base
    merged_config = {}
    
    # Извлекаем данные из historical_data секции
    hist_data = historical_config.get('historical_data', {})
    date_range = hist_data.get('date_range', {})
    intervals = hist_data.get('intervals', {})
    output = hist_data.get('output', {})
    data_sources = hist_data.get('data_sources', {})
    defaults = historical_config.get('default_values', {})
    
    # Заполняем merged_config
    merged_config.update({
        'start_date': date_range.get('start_date', '2023-01-01'),
        'end_date': date_range.get('end_date', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')),
        'time_interval': intervals.get('time_interval', 'daily'),
        'api_delay_seconds': intervals.get('api_delay_seconds', 2),
        'csv_filename': output.get('csv_filename', 'historical_macro_data.csv'),
        'backup_existing': output.get('backup_existing', True),
        'enabled_metrics': data_sources.get('enabled_metrics', []),
        'unavailable_metrics': data_sources.get('unavailable_metrics', []),
        'max_days_per_request': hist_data.get('historical_apis', {}).get('coingecko', {}).get('max_days_per_request', 90),
        'max_records_per_query': hist_data.get('historical_apis', {}).get('the_graph', {}).get('max_records_per_query', 1000),
        'max_records_per_request': hist_data.get('historical_apis', {}).get('binance', {}).get('max_records_per_request', 1000),
    })
    
    # Добавляем default values
    gas_defaults = defaults.get('gas_metrics', {})
    liquidity_defaults = defaults.get('liquidity_metrics', {})
    ratio_defaults = defaults.get('ratios', {})
    
    merged_config.update({
        'default_avg_priority_fee_gwei': gas_defaults.get('avg_priority_fee_gwei', 20.0),
        'default_var_priority_fee_gwei': gas_defaults.get('var_priority_fee_gwei', 0.0),
        'default_outlier_detected': gas_defaults.get('outlier_detected', False),
        'default_max_priority_fee_gwei': gas_defaults.get('max_priority_fee_gwei', 0.0),
        'default_outlier_percentage': gas_defaults.get('outlier_percentage', 0.0),
        'default_net_liquidity_change_usd': liquidity_defaults.get('net_liquidity_change_usd', 0.0),
        'default_dex_cex_volume_ratio': ratio_defaults.get('dex_cex_volume_ratio', 1.0),
        'default_hourly_volume_vs_24h_avg_pct': ratio_defaults.get('hourly_volume_vs_24h_avg_pct', 100.0),
    })
    
    return HistoricalDataConfig(**merged_config)

# Создаем валидированный экземпляр конфигурации
HISTORICAL_CONFIG = load_historical_config()

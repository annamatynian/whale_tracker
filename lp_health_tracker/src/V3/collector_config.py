import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

# Load environment variables from .env file
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

class HMMCollectorConfig(BaseModel):
    """Pydantic модель для валидации конфигурации HMM Data Collector."""
    
    CSV_FILENAME: str = Field(default='market_data_v3_detailed.csv')
    COLLECTION_INTERVAL_SECONDS: int = Field(default=3600, gt=0)
    POOL_ADDRESS_V3: str = Field(default='0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640')
    INFURA_URL: str = Field(default_factory=lambda: f"https://mainnet.infura.io/v3/{os.getenv('INFURA_API_KEY')}")
    CEX_API_URL: str = Field(default='https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=1h&limit=1')
    BLOCKS_FOR_GAS_ANALYSIS: int = Field(default=300, gt=0, le=1000)
    
    @field_validator('POOL_ADDRESS_V3')
    @classmethod
    def validate_pool_address(cls, v):
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Недопустимый адрес пула')
        return v.lower()
    
    @field_validator('INFURA_URL')
    @classmethod
    def validate_infura_url(cls, v):
        if 'infura.io' not in v:
            raise ValueError('URL должен содержать infura.io')
        return v

# Создаем валидированный экземпляр конфигурации
CONFIG = HMMCollectorConfig()
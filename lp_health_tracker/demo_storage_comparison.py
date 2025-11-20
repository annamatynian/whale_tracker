"""
Демонстрация Storage Manager - CSV vs SQLite
"""
import asyncio
import sys
import os
import time
from datetime import datetime, timedelta

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.V3.storage_manager import create_storage_manager
from src.V3.hmm_market_data_collector import MarketDataPoint

def create_sample_data(count: int = 1000):
    """Создает тестовые данные для сравнения производительности."""
    data_points = []
    base_time = datetime.now() - timedelta(days=count)
    
    for i in range(count):
        timestamp = base_time + timedelta(hours=i)
        data_point = MarketDataPoint(
            timestamp=int(timestamp.timestamp()),
            datetime=timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            eth_price_usd=2000.0 + (i % 100),  # Симуляция цены
            log_return=0.001 * (i % 10 - 5),  # Симуляция доходности
            dex_volume_usd=1000000.0 + (i * 1000),
            cex_volume_usd=5000000.0 + (i * 2000),
            dex_cex_volume_ratio=0.2,
            hourly_volume_vs_24h_avg_pct=100.0,
            tvl_usd=50000000.0,
            net_liquidity_change_usd=0.0,
            avg_priority_fee_gwei=20.0,
            var_priority_fee_gwei=5.0,
            outlier_detected=False,
            max_priority_fee_gwei=50.0,
            outlier_percentage=2.0
        )
        data_points.append(data_point)
    
    return data_points

def demo_csv_storage():
    """Демонстрация работы с CSV хранилищем."""
    print("=== CSV Storage Demo ===")
    
    # Конфигурация только для CSV
    csv_config = {
        'backend': 'csv',
        'csv': {
            'enabled': True,
            'filename': 'demo_csv_data.csv'
        },
        'sqlite': {'enabled': False}
    }
    
    storage = create_storage_manager()
    storage.config = csv_config
    storage._setup_storage()
    
    # Создаем тестовые данные
    sample_data = create_sample_data(100)
    
    # Тестируем скорость записи
    start_time = time.time()
    storage.write_data_points(sample_data)
    csv_write_time = time.time() - start_time
    
    # Тестируем скорость чтения
    start_time = time.time()
    df = storage.read_data_as_dataframe()
    csv_read_time = time.time() - start_time
    
    print(f"✅ CSV Запись: {csv_write_time:.3f}s для {len(sample_data)} записей")
    print(f"✅ CSV Чтение: {csv_read_time:.3f}s для {len(df)} записей")
    print(f"✅ CSV Размер файла: {os.path.getsize('demo_csv_data.csv')} bytes")
    
    # Показываем статистику
    stats = storage.get_stats()
    print(f"✅ CSV Статистика: {stats}")
    
    # Очищаем тестовый файл
    os.remove('demo_csv_data.csv')
    
    return csv_write_time, csv_read_time

def demo_sqlite_storage():
    """Демонстрация работы с SQLite хранилищем."""
    print("\n=== SQLite Storage Demo ===")
    
    # Конфигурация только для SQLite
    sqlite_config = {
        'backend': 'sqlite',
        'csv': {'enabled': False},
        'sqlite': {
            'enabled': True,
            'filename': 'demo_sqlite_data.db',
            'table_name': 'market_data_points',
            'indexes': ['timestamp', 'eth_price_usd']
        }
    }
    
    storage = create_storage_manager()
    storage.config = sqlite_config
    storage.sqlite_enabled = True
    storage.sqlite_filename = 'demo_sqlite_data.db'
    storage._setup_storage()
    
    # Создаем тестовые данные
    sample_data = create_sample_data(100)
    
    # Тестируем скорость записи
    start_time = time.time()
    storage.write_data_points(sample_data)
    sqlite_write_time = time.time() - start_time
    
    # Тестируем скорость чтения
    start_time = time.time()
    df = storage.read_data_as_dataframe()
    sqlite_read_time = time.time() - start_time
    
    print(f"✅ SQLite Запись: {sqlite_write_time:.3f}s для {len(sample_data)} записей")
    print(f"✅ SQLite Чтение: {sqlite_read_time:.3f}s для {len(df)} записей")
    print(f"✅ SQLite Размер файла: {os.path.getsize('demo_sqlite_data.db')} bytes")
    
    # Показываем статистику
    stats = storage.get_stats()
    print(f"✅ SQLite Статистика: {stats}")
    
    # Тестируем фильтрацию по датам (преимущество SQLite)
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    
    start_time = time.time()
    filtered_df = storage.read_data_as_dataframe(start_date=yesterday, end_date=today)
    filter_time = time.time() - start_time
    
    print(f"✅ SQLite Фильтрация по дате: {filter_time:.3f}s для {len(filtered_df)} записей")
    
    # Очищаем тестовый файл
    os.remove('demo_sqlite_data.db')
    
    return sqlite_write_time, sqlite_read_time

def demo_both_storage():
    """Демонстрация одновременного использования CSV + SQLite."""
    print("\n=== Dual Storage Demo (CSV + SQLite) ===")
    
    both_config = {
        'backend': 'both',
        'csv': {
            'enabled': True,
            'filename': 'demo_both_data.csv'
        },
        'sqlite': {
            'enabled': True,
            'filename': 'demo_both_data.db',
            'table_name': 'market_data_points'
        }
    }
    
    storage = create_storage_manager()
    storage.config = both_config
    storage.sqlite_enabled = True
    storage.sqlite_filename = 'demo_both_data.db'
    storage._setup_storage()
    
    # Создаем тестовые данные
    sample_data = create_sample_data(50)
    
    # Записываем в оба формата одновременно
    start_time = time.time()
    storage.write_data_points(sample_data)
    both_write_time = time.time() - start_time
    
    print(f"✅ Dual Storage Запись: {both_write_time:.3f}s для {len(sample_data)} записей")
    print(f"✅ CSV файл: {os.path.getsize('demo_both_data.csv')} bytes")
    print(f"✅ SQLite файл: {os.path.getsize('demo_both_data.db')} bytes")
    
    # Показываем статистику
    stats = storage.get_stats()
    print(f"✅ Dual Storage Статистика: {stats}")
    
    # Очищаем тестовые файлы
    os.remove('demo_both_data.csv')
    os.remove('demo_both_data.db')

def show_practical_use_cases():
    """Показывает практические случаи использования."""
    print("\n" + "="*60)
    print("📊 ПРАКТИЧЕСКИЕ РЕКОМЕНДАЦИИ")
    print("="*60)
    
    print("""
🎯 **ИСПОЛЬЗУЙТЕ CSV КОГДА:**
✅ Обучаете ML модели (pandas.read_csv() + sklearn)
✅ Анализируете данные в Jupyter notebooks
✅ Нужна простота и надежность
✅ Объем данных < 50,000 записей
✅ Делаете backup и передачу данных
✅ Работаете в команде (легко смотреть в Git)

🎯 **ПЕРЕХОДИТЕ НА SQLite КОГДА:**
⚡ Нужны быстрые запросы по диапазонам дат
⚡ Объем данных > 100,000 записей
⚡ Нужны UPDATE/DELETE операции
⚡ Хотите аналитику: "Покажи дни с высокой волатильностью"
⚡ Несколько процессов читают данные одновременно
⚡ Нужна агрегация (AVG, SUM, COUNT по периодам)

🎯 **ИСПОЛЬЗУЙТЕ ОБА ФОРМАТА КОГДА:**
💪 Хотите гибкость: CSV для ML, SQLite для аналитики
💪 Нужен backup в двух форматах
💪 Переходный период между форматами
    """)

def main():
    """Запуск всех демонстраций."""
    print("🧪 СРАВНЕНИЕ STORAGE BACKENDS")
    print("=" * 60)
    
    try:
        # Демонстрируем все варианты
        csv_write, csv_read = demo_csv_storage()
        sqlite_write, sqlite_read = demo_sqlite_storage()
        demo_both_storage()
        
        # Сравнение производительности
        print("\n" + "="*60)
        print("📈 СРАВНЕНИЕ ПРОИЗВОДИТЕЛЬНОСТИ")
        print("="*60)
        print(f"CSV     Запись: {csv_write:.3f}s | Чтение: {csv_read:.3f}s")
        print(f"SQLite  Запись: {sqlite_write:.3f}s | Чтение: {sqlite_read:.3f}s")
        
        if csv_write < sqlite_write:
            print("🏆 CSV быстрее при записи")
        else:
            print("🏆 SQLite быстрее при записи")
        
        if csv_read < sqlite_read:
            print("🏆 CSV быстрее при чтении")
        else:
            print("🏆 SQLite быстрее при чтении")
        
        show_practical_use_cases()
        
        print("\n🎉 ВАШ ПЛАН ДЕЙСТВИЙ:")
        print("1. Начните с CSV (уже работает)")
        print("2. Когда данных станет много - включите SQLite в config/storage.yaml")
        print("3. Или используйте 'both' для максимальной гибкости")
        
    except Exception as e:
        print(f"❌ Ошибка демонстрации: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

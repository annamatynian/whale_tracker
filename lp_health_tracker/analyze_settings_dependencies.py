#!/usr/bin/env python3
"""
Settings Dependencies Analyzer
=============================

Анализирует все зависимости от старой системы настроек в проекте.
Помогает планировать рефакторинг для перехода на YAML конфигурацию.

Автор: Сгенерировано для проекта DeFi-RAG
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Any
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class SettingsUsage:
    """Информация об использовании settings в файле."""
    file_path: str
    line_number: int
    line_content: str
    usage_type: str  # 'import', 'old_style', 'new_style', 'env_var'
    old_pattern: str
    suggested_replacement: str

class SettingsDependencyAnalyzer:
    """
    Анализатор зависимостей от системы настроек.
    """
    
    def __init__(self, project_root: str):
        """
        Инициализация анализатора.
        
        Args:
            project_root: Корневая папка проекта
        """
        self.project_root = Path(project_root)
        self.python_files = []
        self.usages = []
        
        # Паттерны старых импортов
        self.old_import_patterns = [
            r'from\s+config\s+import\s+settings',
            r'from\s+config\.settings\s+import\s+Settings',
            r'import\s+settings',
            r'from\s+\.\.config\s+import\s+settings',
            r'from\s+config\.settings\s+import\s+.*',
        ]
        
        # Паттерны старых обращений к настройкам
        self.old_settings_patterns = {
            # Основные настройки
            'settings.wallet_addresses': 'settings.monitoring.wallet_addresses',
            'settings.wallet_addresses_list': 'settings.monitoring.wallet_addresses',
            'settings.check_interval_minutes': 'settings.monitoring.intervals.check_minutes',
            'settings.default_il_threshold': 'settings.monitoring.thresholds.default_il_threshold',
            
            # API ключи
            'settings.INFURA_API_KEY': 'settings.blockchain.providers.infura.api_key',
            'settings.ALCHEMY_API_KEY': 'settings.blockchain.providers.alchemy.api_key',
            'settings.COINGECKO_API_KEY': 'settings.apis.coingecko.api_key',
            
            # Telegram
            'settings.TELEGRAM_BOT_TOKEN': 'settings.notifications.telegram.bot_token',
            'settings.TELEGRAM_CHAT_ID': 'settings.notifications.telegram.chat_id',
            'settings.telegram_bot_token': 'settings.notifications.telegram.bot_token',
            'settings.telegram_chat_id': 'settings.notifications.telegram.chat_id',
            
            # Сеть и производительность
            'settings.DEFAULT_NETWORK': 'settings.blockchain.default_network',
            'settings.MAX_CONCURRENT_REQUESTS': 'settings.performance.max_concurrent_requests',
            'settings.API_TIMEOUT_SECONDS': 'settings.performance.request_timeout_seconds',
            'settings.CACHE_TTL_SECONDS': 'settings.performance.cache_ttl_seconds',
            
            # Логирование
            'settings.LOG_LEVEL': 'settings.logging.level',
            'settings.log_level': 'settings.logging.level',
            
            # Разработка
            'settings.USE_MOCK_DATA': 'settings.development.mock_data',
            'settings.TEST_MODE': 'settings.development.test_mode',
            'settings.DEBUG_API_CALLS': 'settings.development.debug_api_calls',
        }
        
        # Паттерны прямых обращений к переменным окружения
        self.env_var_patterns = {
            'os.getenv("INFURA_API_KEY")': 'settings.blockchain.providers.infura.api_key',
            'os.environ.get("INFURA_API_KEY")': 'settings.blockchain.providers.infura.api_key',
            'os.getenv("TELEGRAM_BOT_TOKEN")': 'settings.notifications.telegram.bot_token',
            'os.environ.get("TELEGRAM_BOT_TOKEN")': 'settings.notifications.telegram.bot_token',
            'os.getenv("COINGECKO_API_KEY")': 'settings.apis.coingecko.api_key',
            'os.environ.get("COINGECKO_API_KEY")': 'settings.apis.coingecko.api_key',
        }
    
    def find_python_files(self) -> List[Path]:
        """Найти все Python файлы в проекте."""
        python_files = []
        
        # Исключаем определенные папки
        exclude_dirs = {
            '__pycache__', '.git', '.pytest_cache', 'venv', 'env', 
            '.venv', 'node_modules', 'backup'
        }
        
        def scan_directory(directory: Path):
            try:
                for item in directory.iterdir():
                    if item.is_file() and item.suffix == '.py':
                        python_files.append(item)
                    elif item.is_dir() and item.name not in exclude_dirs:
                        scan_directory(item)
            except PermissionError:
                pass
        
        scan_directory(self.project_root)
        self.python_files = python_files
        return python_files
    
    def analyze_file(self, file_path: Path) -> List[SettingsUsage]:
        """Анализировать один файл на использование настроек."""
        usages = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Пропускаем комментарии и пустые строки
                if not line_stripped or line_stripped.startswith('#'):
                    continue
                
                # Проверяем импорты
                for pattern in self.old_import_patterns:
                    if re.search(pattern, line_stripped):
                        usage = SettingsUsage(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            line_content=line_stripped,
                            usage_type='import',
                            old_pattern=pattern,
                            suggested_replacement='from config.settings import get_settings'
                        )
                        usages.append(usage)
                
                # Проверяем старые обращения к настройкам
                for old_pattern, new_pattern in self.old_settings_patterns.items():
                    if old_pattern in line_stripped:
                        usage = SettingsUsage(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            line_content=line_stripped,
                            usage_type='old_style',
                            old_pattern=old_pattern,
                            suggested_replacement=new_pattern
                        )
                        usages.append(usage)
                
                # Проверяем прямые обращения к переменным окружения
                for env_pattern, new_pattern in self.env_var_patterns.items():
                    if env_pattern in line_stripped:
                        usage = SettingsUsage(
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            line_content=line_stripped,
                            usage_type='env_var',
                            old_pattern=env_pattern,
                            suggested_replacement=new_pattern
                        )
                        usages.append(usage)
        
        except Exception as e:
            print(f"Ошибка при анализе файла {file_path}: {e}")
        
        return usages
    
    def analyze_project(self) -> Dict[str, Any]:
        """Провести полный анализ проекта."""
        print("🔍 Поиск Python файлов...")
        python_files = self.find_python_files()
        print(f"Найдено {len(python_files)} Python файлов")
        
        print("\n📊 Анализ зависимостей...")
        all_usages = []
        
        for file_path in python_files:
            usages = self.analyze_file(file_path)
            all_usages.extend(usages)
        
        self.usages = all_usages
        
        # Группируем результаты
        results = self._group_results()
        
        return results
    
    def _group_results(self) -> Dict[str, Any]:
        """Группировать результаты анализа."""
        by_file = defaultdict(list)
        by_type = defaultdict(list)
        by_pattern = defaultdict(list)
        
        for usage in self.usages:
            by_file[usage.file_path].append(usage)
            by_type[usage.usage_type].append(usage)
            by_pattern[usage.old_pattern].append(usage)
        
        # Приоритеты файлов
        priority_files = self._calculate_file_priorities(by_file)
        
        return {
            'total_files_analyzed': len(self.python_files),
            'total_issues_found': len(self.usages),
            'files_with_issues': len(by_file),
            'by_file': dict(by_file),
            'by_type': dict(by_type),
            'by_pattern': dict(by_pattern),
            'priority_files': priority_files,
            'summary_stats': self._calculate_summary_stats(by_type)
        }
    
    def _calculate_file_priorities(self, by_file: Dict) -> List[Dict]:
        """Рассчитать приоритеты файлов для рефакторинга."""
        priority_scores = {}
        
        for file_path, usages in by_file.items():
            score = 0
            
            # Вес по типу файла
            if file_path in ['main.py', 'src/main.py', 'run.py']:
                score += 100  # Главные файлы
            elif file_path.startswith('src/') and not file_path.startswith('src/V3'):
                score += 50   # Основные модули
            elif file_path.startswith('tests/'):
                score += 10   # Тесты
            
            # Вес по количеству проблем
            score += len(usages) * 5
            
            # Вес по типу проблем
            for usage in usages:
                if usage.usage_type == 'import':
                    score += 10  # Импорты важнее
                elif usage.usage_type == 'old_style':
                    score += 5
                elif usage.usage_type == 'env_var':
                    score += 3
            
            priority_scores[file_path] = score
        
        # Сортируем по приоритету
        sorted_files = sorted(
            priority_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return [
            {
                'file': file_path,
                'priority_score': score,
                'issues_count': len(by_file[file_path]),
                'issues': by_file[file_path]
            }
            for file_path, score in sorted_files[:10]  # Топ 10
        ]
    
    def _calculate_summary_stats(self, by_type: Dict) -> Dict:
        """Рассчитать суммарную статистику."""
        return {
            'imports_to_fix': len(by_type.get('import', [])),
            'old_style_usages': len(by_type.get('old_style', [])),
            'env_var_usages': len(by_type.get('env_var', [])),
            'estimated_hours': self._estimate_refactoring_time(by_type)
        }
    
    def _estimate_refactoring_time(self, by_type: Dict) -> float:
        """Оценить время на рефакторинг."""
        # Примерные оценки в минутах
        time_per_import = 2
        time_per_old_style = 1
        time_per_env_var = 1.5
        
        total_minutes = (
            len(by_type.get('import', [])) * time_per_import +
            len(by_type.get('old_style', [])) * time_per_old_style +
            len(by_type.get('env_var', [])) * time_per_env_var
        )
        
        return round(total_minutes / 60, 1)  # Часы
    
    def print_detailed_report(self, results: Dict[str, Any]):
        """Вывести детальный отчет."""
        print("\n" + "="*60)
        print("📋 ОТЧЕТ ПО АНАЛИЗУ ЗАВИСИМОСТЕЙ SETTINGS")
        print("="*60)
        
        # Общая статистика
        print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"├── Всего файлов проанализировано: {results['total_files_analyzed']}")
        print(f"├── Файлов с проблемами: {results['files_with_issues']}")
        print(f"├── Всего проблем найдено: {results['total_issues_found']}")
        print(f"└── Оценка времени рефакторинга: {results['summary_stats']['estimated_hours']} часов")
        
        # Статистика по типам
        stats = results['summary_stats']
        print(f"\n🔧 СТАТИСТИКА ПО ТИПАМ:")
        print(f"├── Импорты для исправления: {stats['imports_to_fix']}")
        print(f"├── Старые обращения к настройкам: {stats['old_style_usages']}")
        print(f"└── Прямые обращения к ENV: {stats['env_var_usages']}")
        
        # Приоритетные файлы
        print(f"\n🎯 ПРИОРИТЕТНЫЕ ФАЙЛЫ ДЛЯ РЕФАКТОРИНГА:")
        for i, file_info in enumerate(results['priority_files'][:5], 1):
            print(f"{i}. {file_info['file']} (Оценка: {file_info['priority_score']}, Проблем: {file_info['issues_count']})")
        
        # Детали по приоритетным файлам
        print(f"\n📁 ДЕТАЛИ ПО ПРИОРИТЕТНЫМ ФАЙЛАМ:")
        for file_info in results['priority_files'][:3]:
            print(f"\n▶️ {file_info['file']}:")
            for usage in file_info['issues'][:5]:  # Показываем первые 5 проблем
                print(f"   ├── Строка {usage.line_number}: {usage.usage_type}")
                print(f"   │   Найдено: {usage.old_pattern}")
                print(f"   │   Заменить на: {usage.suggested_replacement}")
                if len(file_info['issues']) > 5:
                    print(f"   └── ... и еще {len(file_info['issues']) - 5} проблем")
    
    def save_results_to_file(self, results: Dict[str, Any], output_file: str = "settings_analysis_report.json"):
        """Сохранить результаты в файл."""
        # Конвертируем SettingsUsage в словари для JSON
        json_results = results.copy()
        
        for file_path, usages in json_results['by_file'].items():
            json_results['by_file'][file_path] = [
                {
                    'file_path': usage.file_path,
                    'line_number': usage.line_number,
                    'line_content': usage.line_content,
                    'usage_type': usage.usage_type,
                    'old_pattern': usage.old_pattern,
                    'suggested_replacement': usage.suggested_replacement
                }
                for usage in usages
            ]
        
        for usage_type, usages in json_results['by_type'].items():
            json_results['by_type'][usage_type] = [
                {
                    'file_path': usage.file_path,
                    'line_number': usage.line_number,
                    'line_content': usage.line_content,
                    'usage_type': usage.usage_type,
                    'old_pattern': usage.old_pattern,
                    'suggested_replacement': usage.suggested_replacement
                }
                for usage in usages
            ]
        
        for pattern, usages in json_results['by_pattern'].items():
            json_results['by_pattern'][pattern] = [
                {
                    'file_path': usage.file_path,
                    'line_number': usage.line_number,
                    'line_content': usage.line_content,
                    'usage_type': usage.usage_type,
                    'old_pattern': usage.old_pattern,
                    'suggested_replacement': usage.suggested_replacement
                }
                for usage in usages
            ]
        
        # Конвертируем priority_files
        for file_info in json_results['priority_files']:
            file_info['issues'] = [
                {
                    'file_path': usage.file_path,
                    'line_number': usage.line_number,
                    'line_content': usage.line_content,
                    'usage_type': usage.usage_type,
                    'old_pattern': usage.old_pattern,
                    'suggested_replacement': usage.suggested_replacement
                }
                for usage in file_info['issues']
            ]
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Детальный отчет сохранен в: {output_file}")
    
    def print_refactoring_plan(self, results: Dict[str, Any]):
        """Вывести план рефакторинга."""
        print("\n" + "="*60)
        print("🗺️  ПЛАН РЕФАКТОРИНГА")
        print("="*60)
        
        priority_files = results['priority_files']
        
        print("\n📋 ПОСЛЕДОВАТЕЛЬНОСТЬ ДЕЙСТВИЙ:")
        
        # Этап 1: Критические файлы
        critical_files = [f for f in priority_files if f['priority_score'] >= 100]
        if critical_files:
            print(f"\n🔥 ЭТАП 1: Критические файлы (СРОЧНО)")
            for file_info in critical_files:
                print(f"   ├── {file_info['file']} ({file_info['issues_count']} проблем)")
        
        # Этап 2: Важные файлы
        important_files = [f for f in priority_files if 50 <= f['priority_score'] < 100]
        if important_files:
            print(f"\n⚡ ЭТАП 2: Важные файлы")
            for file_info in important_files:
                print(f"   ├── {file_info['file']} ({file_info['issues_count']} проблем)")
        
        # Этап 3: Остальные файлы
        other_files = [f for f in priority_files if f['priority_score'] < 50]
        if other_files:
            print(f"\n📝 ЭТАП 3: Остальные файлы")
            for file_info in other_files[:5]:  # Показываем только первые 5
                print(f"   ├── {file_info['file']} ({file_info['issues_count']} проблем)")
            if len(other_files) > 5:
                print(f"   └── ... и еще {len(other_files) - 5} файлов")
        
        print(f"\n⏱️  Общее время: ~{results['summary_stats']['estimated_hours']} часов")
        print(f"👥 Рекомендация: обновлять по 1-2 файла за раз с тестированием")


def main():
    """Главная функция анализатора."""
    print("🚀 Запуск анализатора зависимостей Settings...")
    
    # Определяем корневую папку проекта
    project_root = Path(__file__).parent
    
    # Создаем анализатор
    analyzer = SettingsDependencyAnalyzer(project_root)
    
    # Запускаем анализ
    results = analyzer.analyze_project()
    
    # Выводим отчеты
    analyzer.print_detailed_report(results)
    analyzer.print_refactoring_plan(results)
    
    # Сохраняем в файл
    analyzer.save_results_to_file(results)
    
    print(f"\n✅ Анализ завершен!")
    print(f"📊 Найдено {results['total_issues_found']} проблем в {results['files_with_issues']} файлах")
    print(f"🎯 Начните с файлов из ЭТАПА 1 для максимальной эффективности")

if __name__ == "__main__":
    main()

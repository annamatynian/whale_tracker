"""
Telegram Alert Agent - Отправка уведомлений о pump кандидатах

Интеграция с MVP Pump Discovery System для мгновенных алертов
"""

import requests
import os
import asyncio
from typing import List, Optional
from datetime import datetime
from dataclasses import dataclass

from agents.pump_analysis.pump_models import PumpAnalysisReport

@dataclass
class TelegramConfig:
    """Конфигурация Telegram бота"""
    bot_token: str
    chat_id: str
    base_url: str = "https://api.telegram.org/bot"
    
    @classmethod
    def from_env(cls) -> 'TelegramConfig':
        """Загрузка конфигурации из переменных окружения"""
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        
        if not bot_token or not chat_id:
            raise ValueError(
                "Не найдены TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID в .env файле!\n"
                "Пожалуйста, настройте их согласно инструкции."
            )
        
        return cls(bot_token=bot_token, chat_id=chat_id)

class TelegramAlertAgent:
    """
    Агент для отправки Telegram уведомлений о pump кандидатах
    
    Интегрируется с Pump Discovery Agent для мгновенных алертов
    """
    
    def __init__(self, config: Optional[TelegramConfig] = None):
        self.config = config or TelegramConfig.from_env()
        self.session_stats = {
            'alerts_sent': 0,
            'api_calls': 0,
            'errors': 0
        }
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Отправка сообщения в Telegram
        
        Args:
            message: Текст сообщения (поддерживает HTML разметку)
            parse_mode: Режим разметки (HTML или Markdown)
        
        Returns:
            bool: Успешность отправки
        """
        url = f"{self.config.base_url}{self.config.bot_token}/sendMessage"
        
        payload = {
            'chat_id': self.config.chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        try:
            self.session_stats['api_calls'] += 1
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                self.session_stats['alerts_sent'] += 1
                return True
            else:
                print(f"❌ Ошибка Telegram API: {response.status_code} - {response.text}")
                self.session_stats['errors'] += 1
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Ошибка сети при отправке в Telegram: {e}")
            self.session_stats['errors'] += 1
            return False
    
    def format_pump_alert(self, report: PumpAnalysisReport) -> str:
        """
        Форматирование pump кандидата для Telegram сообщения
        
        Args:
            report: Отчет о pump кандидате
            
        Returns:
            str: Форматированное сообщение с HTML разметкой
        """
        # Эмодзи в зависимости от score
        if report.final_score >= 80:
            emoji = "🚀"
            priority = "HIGH PRIORITY"
        elif report.final_score >= 60:
            emoji = "🎯"
            priority = "MEDIUM PRIORITY"
        else:
            emoji = "👀"
            priority = "WATCH LIST"
        
        # Форматируем сообщение
        message = f"""
{emoji} <b>PUMP CANDIDATE FOUND!</b>

<b>{report.token_name}</b> ({report.token_symbol})
🎯 <b>Score:</b> {report.final_score}/100
📊 <b>Priority:</b> {priority}

💰 <b>Liquidity:</b> ${report.indicators.liquidity_usd:,.0f}
📈 <b>Volume 24h:</b> ${report.indicators.volume_24h:,.0f}
🕒 <b>Age:</b> {report.indicators.age_hours:.1f} hours
📍 <b>Contract:</b> <code>{report.contract_address}</code>

💡 <b>Key Signals:</b>
"""
        
        # Добавляем reasoning (первые 3)
        for reason in report.reasoning[:3]:
            message += f"• {reason}\n"
        
        # Добавляем next steps
        if report.next_steps:
            message += f"\n📋 <b>Next Steps:</b>\n"
            for step in report.next_steps[:2]:
                message += f"• {step}\n"
        
        # Добавляем timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        message += f"\n⏰ <i>Found at {timestamp}</i>"
        
        return message
    
    def send_pump_alert(self, report: PumpAnalysisReport) -> bool:
        """
        Отправка алерта о pump кандидате
        
        Args:
            report: Отчет о найденном кандидате
            
        Returns:
            bool: Успешность отправки
        """
        message = self.format_pump_alert(report)
        success = self.send_message(message)
        
        if success:
            print(f"✅ Telegram алерт отправлен: {report.token_symbol} (Score: {report.final_score})")
        else:
            print(f"❌ Не удалось отправить алерт для {report.token_symbol}")
        
        return success
    
    def send_batch_alert(self, reports: List[PumpAnalysisReport]) -> int:
        """
        Отправка батча алертов
        
        Args:
            reports: Список отчетов о кандидатах
            
        Returns:
            int: Количество успешно отправленных алертов
        """
        if not reports:
            return 0
        
        # Отправляем summary сначала
        summary_message = f"""
📊 <b>PUMP SCAN COMPLETE</b>

Found <b>{len(reports)}</b> candidates:
"""
        
        high_priority = [r for r in reports if r.final_score >= 80]
        medium_priority = [r for r in reports if 60 <= r.final_score < 80]
        watch_list = [r for r in reports if r.final_score < 60]
        
        if high_priority:
            summary_message += f"🚀 High Priority: {len(high_priority)}\n"
        if medium_priority:
            summary_message += f"🎯 Medium Priority: {len(medium_priority)}\n"
        if watch_list:
            summary_message += f"👀 Watch List: {len(watch_list)}\n"
        
        summary_message += f"\nDetailed alerts following..."
        
        self.send_message(summary_message)
        
        # Отправляем детальные алерты
        successful_alerts = 0
        for report in reports:
            if self.send_pump_alert(report):
                successful_alerts += 1
            
            # Пауза между сообщениями (avoid rate limiting)
            asyncio.sleep(0.5)
        
        return successful_alerts
    
    def send_system_message(self, message: str, emoji: str = "🤖") -> bool:
        """
        Отправка системного сообщения
        
        Args:
            message: Текст сообщения
            emoji: Эмодзи для сообщения
            
        Returns:
            bool: Успешность отправки
        """
        formatted_message = f"{emoji} <b>SYSTEM:</b> {message}"
        return self.send_message(formatted_message)
    
    def test_connection(self) -> bool:
        """
        Тестирование подключения к Telegram
        
        Returns:
            bool: Успешность подключения
        """
        test_message = "🧪 <b>TEST MESSAGE</b>\n\nPump Discovery System подключен к Telegram!\nТестирование завершено успешно ✅"
        
        success = self.send_message(test_message)
        
        if success:
            print("✅ Telegram бот настроен правильно!")
        else:
            print("❌ Ошибка подключения к Telegram боту")
        
        return success
    
    def get_stats(self) -> dict:
        """Получение статистики сессии"""
        return {
            **self.session_stats,
            'success_rate': (
                self.session_stats['alerts_sent'] / 
                max(self.session_stats['api_calls'], 1) * 100
            )
        }

# === ИНТЕГРАЦИЯ С PUMP DISCOVERY AGENT ===

class TelegramIntegratedPumpAgent:
    """
    Pump Discovery Agent с интегрированными Telegram алертами
    
    Автоматически отправляет уведомления о найденных кандидатах
    """
    
    def __init__(self, enable_telegram: bool = True):
        # Импортируем здесь чтобы избежать циклических импортов
        from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent
        
        self.pump_agent = PumpDiscoveryAgent()
        self.telegram_agent = TelegramAlertAgent() if enable_telegram else None
        
        if enable_telegram and self.telegram_agent:
            # Тестируем подключение при инициализации
            self.telegram_agent.test_connection()
    
    async def discover_and_alert(self) -> List[PumpAnalysisReport]:
        """
        Поиск pump кандидатов с автоматическими Telegram алертами
        
        Returns:
            List[PumpAnalysisReport]: Найденные кандидаты
        """
        print("🔍 Запуск Pump Discovery с Telegram алертами...")
        
        # Отправляем уведомление о начале сканирования
        if self.telegram_agent:
            self.telegram_agent.send_system_message("Начинаю сканирование pump кандидатов...", "🔍")
        
        # Запускаем поиск
        candidates = await self.pump_agent.discover_tokens_async()
        
        if not candidates:
            if self.telegram_agent:
                self.telegram_agent.send_system_message("Сканирование завершено. Кандидатов не найдено.", "😔")
            return []
        
        # Отправляем алерты
        if self.telegram_agent:
            successful_alerts = self.telegram_agent.send_batch_alert(candidates)
            
            # Отправляем итоговую статистику
            pump_stats = self.pump_agent.get_session_stats()
            telegram_stats = self.telegram_agent.get_stats()
            
            stats_message = f"""
📊 <b>SCAN STATISTICS</b>

🔍 <b>Discovery:</b>
• Pairs scanned: {pump_stats['pairs_scanned']}
• Candidates found: {len(candidates)}
• Success rate: {pump_stats['success_rate']:.1f}%

📱 <b>Telegram:</b>
• Alerts sent: {successful_alerts}/{len(candidates)}
• API calls: {telegram_stats['api_calls']}
• Success rate: {telegram_stats['success_rate']:.1f}%
"""
            
            self.telegram_agent.send_message(stats_message)
        
        return candidates

# === УТИЛИТЫ ===

def load_env_file():
    """Загружает .env файл если он существует"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env файл загружен")
    except ImportError:
        print("⚠️ python-dotenv не установлен. Устанавливаем...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'python-dotenv'])
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env файл загружен")

if __name__ == "__main__":
    # Тестирование Telegram агента
    load_env_file()
    
    try:
        telegram_agent = TelegramAlertAgent()
        telegram_agent.test_connection()
        
        print("\n📊 Статистика сессии:")
        stats = telegram_agent.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\n🔧 Убедитесь что:")
        print("   1. Создан .env файл с TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID")
        print("   2. Бот создан через @BotFather")
        print("   3. Вы отправили боту хотя бы одно сообщение")

"""
Получение Chat ID через отправку тестового сообщения
"""
import requests
import os

# Загружаем переменные
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = "123456789"  # Пробуем с разными ID

def test_bot_token():
    """Проверяем что токен бота работает"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getMe"
    
    try:
        response = requests.get(url)
        print(f"Статус ответа: {response.status_code}")
        print(f"Ответ: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data.get('result', {})
                print(f"✅ Бот работает: {bot_info.get('first_name')} (@{bot_info.get('username')})")
                return True
            else:
                print("❌ Бот не отвечает корректно")
                return False
        else:
            print("❌ Ошибка подключения к боту")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def get_updates():
    """Получаем обновления от бота"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url)
        print(f"\nПолучение обновлений:")
        print(f"Статус: {response.status_code}")
        print(f"Ответ: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('ok') and data.get('result'):
                updates = data.get('result', [])
                print(f"\n📨 Найдено {len(updates)} сообщений:")
                
                for update in updates:
                    if 'message' in update:
                        message = update['message']
                        chat = message.get('chat', {})
                        chat_id = chat.get('id')
                        user_name = chat.get('first_name', 'Unknown')
                        text = message.get('text', '')
                        
                        print(f"  💬 Chat ID: {chat_id}")
                        print(f"  👤 From: {user_name}")
                        print(f"  📝 Text: {text}")
                        print(f"  🔧 Добавьте в .env: TELEGRAM_CHAT_ID={chat_id}")
                        print("-" * 40)
                
                return updates
            else:
                print("📭 Сообщений не найдено")
                return []
        else:
            print("❌ Не удалось получить обновления")
            return []
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return []

if __name__ == "__main__":
    print("🤖 ДИАГНОСТИКА TELEGRAM БОТА")
    print("=" * 50)
    
    print(f"Bot Token: {BOT_TOKEN[:20]}...")
    
    # Тестируем токен
    if test_bot_token():
        # Получаем сообщения
        get_updates()
    else:
        print("\n🔧 РЕШЕНИЯ:")
        print("1. Проверьте токен бота через @BotFather")
        print("2. Убедитесь что бот не заблокирован")
        print("3. Попробуйте создать нового бота")

"""
Тест подключения к Infura API
"""
import requests

# Ваш Project ID из скриншота
INFURA_API_KEY = "3b91f6359ee4457aae21ade150c06fb1"

def test_infura_connection():
    print("🔗 Тестируем подключение к Infura...")
    
    # Тест Ethereum Mainnet
    url = f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"
    
    # Простой запрос - получить номер последнего блока
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber", 
        "params": [],
        "id": 1
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'result' in data:
            block_number = int(data['result'], 16)  # Hex to decimal
            print(f"✅ Infura подключение работает!")
            print(f"✅ Последний блок Ethereum: {block_number}")
            return True
        else:
            print(f"❌ Ошибка в ответе: {data}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    test_infura_connection()

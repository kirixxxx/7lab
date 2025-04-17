import requests
import json
from datetime import datetime

# ========== Получение ask-цены ==========
def get_ethusdt_ask_price(api_key):
    url = "https://api.ataix.kz/api/symbols"
    headers = {
        "accept": "application/json",
        "X-API-Key": api_key
    }

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        if data.get("status") and isinstance(data.get("result"), list):
            for symbol in data["result"]:
                if symbol.get("symbol") == "ETH/USDT":
                    return float(symbol["ask"]) if symbol.get("ask") else None
            print("ETH/USDT жұбы табылмады")
        else:
            print("Қате:", data.get("message", "API жауабы қате"))
    except Exception as e:
        print("API-запрос қатесі:", e)
    
    return None

# ========== Создание ордера ==========
def place_order(api_key, symbol, side, price, quantity):
    url = "https://api.ataix.kz/api/orders"
    headers = {
        "accept": "application/json",
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }

    data = {
        "symbol": symbol,
        "side": side,
        "type": "limit",
        "quantity": quantity,
        "price": price,
        "subType": "gtc"
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()

        print(f"Ответ от API при создании ордера: {json.dumps(result, indent=2)}")

        if result.get("status") == True:
            order_id = result.get("result", {}).get("orderID")
            if order_id:
                save_order_to_file({
                    "id": order_id,
                    "symbol": symbol,
                    "side": side,
                    "price": price,
                    "quantity": quantity,
                    "status": "NEW",
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                return result
            else:
                print("Ошибка: orderID не найден.")
        else:
            print("Ошибка при создании ордера:", result.get("message", "Неизвестная ошибка"))
    except Exception as e:
        print("Ордер қатесі:", e)

    return None

# ========== Сохранение ордера ==========
def save_order_to_file(order_data):
    try:
        try:
            with open("orders.json", "r", encoding="utf-8") as f:
                orders = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            orders = []

        orders.append(order_data)

        with open("orders.json", "w", encoding="utf-8") as f:
            json.dump(orders, f, indent=2, ensure_ascii=False)  # <-- allow unicode

        print(f"Ордер {order_data['id']} файлға сақталды")
    except Exception as e:
        print("Файлға сақтау қатесі:", e)

# ========== Обновление статуса ордера ==========
def update_order_status_in_file(order_id, new_status):
    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            orders = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("orders.json табылмады немесе бос.")
        return

    updated = False
    for order in orders:
        if order.get("id") == order_id:
            order["status"] = new_status
            updated = True
            break

    if updated:
        with open("orders.json", "w", encoding="utf-8") as f:
            json.dump(orders, f, indent=2, ensure_ascii=False)
        print(f"[DEBUG] Ордер {order_id} статусы '{new_status}' деп жаңартылды.")
    else:
        print(f"[DEBUG] Ордер {order_id} табылмады.")

# ========== Главная логика ==========
def main():
    api_key = "ВАШ_API_КЛЮЧ"  # <-- замените на ваш настоящий ключ

    # Загрузка последнего ордера из файла
    try:
        with open("orders.json", "r", encoding="utf-8") as f:
            orders = json.load(f)
            last_order = orders[-1] if orders else None
    except:
        last_order = None

    if last_order and last_order.get("status") == "NEW":
        last_price = float(last_order.get("price", 0))

        # Отмена старого ордера
        update_order_status_in_file(last_order["id"], "cancelled")
        print(f"[DEBUG] Ордер {last_order['id']} отменён.")

        # Новый ордер: цена на 2% выше
        new_price = round(last_price * 1.02, 2)
        quantity = 0.0001

        new_order_result = place_order(
            api_key=api_key,
            symbol="ETH/USDT",
            side="buy",
            price=new_price,
            quantity=quantity
        )

        if new_order_result and new_order_result.get("status") == True:
            print("Новый ордер создан с ценой на 2% выше предыдущего.")
        else:
            print("Ошибка при создании нового ордера.")
    else:
        print("[DEBUG] Активный ордер не найден. Создаём начальный ордер.")

        # Получаем текущую цену
        ask_price = get_ethusdt_ask_price(api_key)
        if ask_price is None:
            print("Ошибка: не удалось получить ask цену.")
            return

        new_price = round(ask_price, 2)
        quantity = 0.0001

        new_order_result = place_order(
            api_key=api_key,
            symbol="ETH/USDT",
            side="buy",
            price=new_price,
            quantity=quantity
        )

        if new_order_result and new_order_result.get("status") == True:
            print("Первый ордер успешно создан.")
        else:
            print("Ошибка при создании первого ордера.")

    print("=" * 50)
    print("ЗАВЕРШЕНО")

# ========== Запуск ==========
if __name__ == "__main__":
    main()

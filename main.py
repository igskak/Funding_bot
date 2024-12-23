import ccxt
import pandas as pd
import asyncio
from config import API_KEYS
from utils import load_markets, get_common_pairs, fetch_all_funding_rates, calculate_profit

def test_connections():
    exchanges = {
        "binance": ccxt.binance(API_KEYS['binance']),
        "bybit": ccxt.bybit(API_KEYS['bybit']),
        "okx": ccxt.okx(API_KEYS['okx'])
    }

    for name, exchange in exchanges.items():
        try:
            print(f"Подключение к {name}: успешно")
        except Exception as e:
            print(f"Ошибка подключения к {name}: {e}")

def fetch_available_pairs():
    """
    Получает список доступных пар на спотовых и деривативных рынках.
    """
    exchanges = {
        "binance": ccxt.binance(API_KEYS['binance']),
        "bybit": ccxt.bybit(API_KEYS['bybit']),
        "okx": ccxt.okx(API_KEYS['okx'])
    }

    results = {}
    for name, exchange in exchanges.items():
        try:
            spot_pairs = load_markets(exchange, "spot")
            futures_pairs = load_markets(exchange, "linear")
            common_pairs = get_common_pairs(spot_pairs, futures_pairs)

            results[name] = {
                "spot_pairs": spot_pairs,
                "futures_pairs": futures_pairs,
                "common_pairs": list(common_pairs)
            }

            print(f"{name}: Найдено {len(common_pairs)} общих пар.")
        except Exception as e:
            print(f"Ошибка при обработке {name}: {e}")
    
    return results

def display_funding_rates(funding_rates, min_profit=0.0001):
    """
    Выводит ставки финансирования с расчетом прибыли в табличной форме.
    """
    processed_rates = []
    for rate in funding_rates:
        if rate:
            profit = calculate_profit(rate['funding_rate'], trading_fee=0.0005)
            if profit >= min_profit:
                processed_rates.append({
                    "Биржа": rate['exchange'],
                    "Пара": rate['symbol'],
                    "Ставка финансирования": rate['funding_rate'],
                    "Потенциальная прибыль": profit
                })

    df = pd.DataFrame(processed_rates)
    if df.empty:
        print("Нет прибыльных пар для отображения.")
    else:
        df = df.sort_values(by="Потенциальная прибыль", ascending=False)
        print(df.to_string(index=False))

if __name__ == "__main__":
    pairs = fetch_available_pairs()

    # Подготовка данных для асинхронного сбора ставок финансирования
    exchanges = {
        "binance": ccxt.binance(API_KEYS['binance']),
        "bybit": ccxt.bybit(API_KEYS['bybit']),
        "okx": ccxt.okx(API_KEYS['okx'])
    }
    common_pairs = {name: data['common_pairs'] for name, data in pairs.items()}

    print("\nСбор ставок финансирования...")
    funding_rates = asyncio.run(fetch_all_funding_rates(exchanges, common_pairs))

    print("\nРезультаты ставок финансирования:")
    display_funding_rates(funding_rates, min_profit=0.0001)  # Фильтруем по прибыли

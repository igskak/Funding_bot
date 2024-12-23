# Utility functions
import asyncio
import ccxt.async_support as ccxt
from config import API_KEYS

def load_markets(exchange, category):
    """
    Загружает список пар для указанной категории рынка.
    """
    markets = exchange.load_markets()
    if category == "spot":
        return [symbol for symbol in markets if markets[symbol]['spot']]
    elif category in ["linear", "inverse"]:
        return [symbol for symbol in markets if markets[symbol]['future']]
    return []

def get_common_pairs(spot_pairs, futures_pairs):
    """
    Находит пересечение пар между спотовым и деривативным рынками.
    """
    return set(spot_pairs) & set(futures_pairs)

def fetch_available_pairs():
    """
    Получает доступные пары для каждой биржи и находит общие пары между спотовым и фьючерсным рынками.
    """
    exchanges = {
        "binance": ccxt.binance(API_KEYS['binance']),
        "bybit": ccxt.bybit(API_KEYS['bybit']),
        "okx": ccxt.okx(API_KEYS['okx'])
    }
    
    result = {}
    for name, exchange in exchanges.items():
        spot_pairs = load_markets(exchange, "spot")
        futures_pairs = load_markets(exchange, "linear")
        common_pairs = get_common_pairs(spot_pairs, futures_pairs)
        
        result[name] = {
            "spot_pairs": spot_pairs,
            "futures_pairs": futures_pairs,
            "common_pairs": common_pairs
        }
        
    return result

async def fetch_funding_rate(exchange, symbol):
    """
    Получает ставку финансирования для заданной пары.
    """
    try:
        funding_rate = await exchange.fetch_funding_rate(symbol)
        return funding_rate
    except Exception as e:
        print(f"Ошибка при получении ставки финансирования {symbol} на {exchange.id}: {e}")
        return None

async def fetch_all_funding_rates(exchanges, common_pairs):
    """
    Сбор ставок финансирования для общих пар на всех биржах.
    """
    tasks = []
    for name, exchange in exchanges.items():
        for pair in common_pairs[name]:
            tasks.append(fetch_funding_rate(exchange, pair))
    
    return await asyncio.gather(*tasks)

def calculate_profit(funding_rate, trading_fee=0.0005):
    """
    Рассчитывает потенциальную прибыль с учетом комиссии.
    :param funding_rate: Ставка финансирования (в процентах).
    :param trading_fee: Комиссия на одной стороне сделки.
    :return: Потенциальная прибыль.
    """
    return funding_rate - 2 * trading_fee  # Учитываем комиссии на открытие и закрытие

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
    for rate in funding_rates:
        if rate:
            print(rate)

import os
import pandas as pd
from binance.client import Client
import config
import datetime

# Rango de fechas
START_DATE = datetime.datetime(2024, 1, 1)
END_DATE = datetime.datetime(2024, 12, 31)

# Crear carpeta de salida
os.makedirs("output", exist_ok=True)

# Conectar a Binance
client = Client(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)

def exportar_binance_bruto():
    print("Exportando datos brutos desde Binance...")
    all_trades = []

    # Obtener todos los pares
    symbols = client.get_exchange_info()["symbols"]
    for symbol in symbols:
        if symbol["quoteAsset"] == "USDT":
            pair = symbol["symbol"]
            try:
                trades = client.get_my_trades(symbol=pair)
                print(f"Trades:: {trades}")
                for trade in trades:
                    ts = datetime.datetime.fromtimestamp(trade["time"] / 1000)
                    if START_DATE <= ts <= END_DATE:
                        all_trades.append(trade)
            except Exception as e:
                print(f"Error con {pair}: {e}")
                continue

    if not all_trades:
        print("No se encontraron operaciones.")
    else:
        df = pd.DataFrame(all_trades)
        df.to_csv("output/binance_bruto.csv", index=False)
        print(f"{len(all_trades)} operaciones exportadas a output/binance_bruto.csv")

if __name__ == "__main__":
    exportar_binance_bruto()

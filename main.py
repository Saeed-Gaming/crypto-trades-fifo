import datetime
import os
import pandas as pd
from decimal import Decimal
from binance.client import Client as BinanceClient
from krakenex import API as KrakenAPI
from pykrakenapi import KrakenAPI as KrakenDataAPI
import config

# Configuración del rango de fechas
START_DATE = datetime.datetime(2024, 1, 1)
END_DATE = datetime.datetime(2024, 12, 31)

# Crear carpeta de salida si no existe
os.makedirs("output", exist_ok=True)

# Conexión Binance
binance = BinanceClient(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)

def obtener_y_guardar_binance_bruto():
    print("Descargando datos crudos desde Binance...")
    trades = []
    all_symbols = binance.get_exchange_info()["symbols"]
    for symbol in all_symbols:
        if symbol["quoteAsset"] == "USDT":
            pair = symbol["symbol"]
            try:
                my_trades = binance.get_my_trades(symbol=pair)
                for t in my_trades:
                    timestamp = datetime.datetime.fromtimestamp(t["time"] / 1000)
                    if START_DATE <= timestamp <= END_DATE:
                        trades.append(t)
            except Exception as e:
                print(f"Error con {pair}: {e}")
                continue
    df = pd.DataFrame(trades)
    df.to_csv("output/binance_bruto.csv", index=False)
    print(f"{len(df)} operaciones guardadas en output/binance_bruto.csv")

def procesar_binance_desde_bruto():
    print("Procesando datos desde binance_bruto.csv...")
    
    # Leemos todo como texto para evitar errores de punto/coma decimal
    df = pd.read_csv("output/binance_bruto.csv", dtype=str)

    df["date"] = pd.to_datetime(df["time"].astype(float) / 1000, unit="s")

    df_traducido = pd.DataFrame({
        "exchange": "Binance",
        "symbol": df["symbol"],
        "date": df["date"],
        "side": df["isBuyer"].map(lambda x: "BUY" if x.lower() == "true" else "SELL"),
        "price": df["price"].map(lambda x: float(Decimal(x))),
        "qty": df["qty"].map(lambda x: float(Decimal(x))),
        "quoteQty": df["quoteQty"].map(lambda x: float(Decimal(x))),
        "commission": df["commission"].map(lambda x: float(Decimal(x))),
        "commissionAsset": df["commissionAsset"]
    })

    df_traducido.to_csv("output/binance_trades.csv", index=False, float_format="%.10f")
    print("Guardado en output/binance_trades.csv")
    return df_traducido

### Kraken ###
kraken_api_raw = KrakenAPI(config.KRAKEN_API_KEY, config.KRAKEN_API_SECRET)
kraken_api = KrakenDataAPI(kraken_api_raw)

def get_kraken_trades():
    output_file = "output/kraken_trades.csv"
    if os.path.exists(output_file):
        print("Archivo encontrado: output/kraken_trades.csv. Cargando desde disco...")
        return pd.read_csv(output_file, parse_dates=["date"])

    df, _ = kraken_api.get_trades_history()
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df[(df['time'] >= START_DATE) & (df['time'] <= END_DATE)]
    df.reset_index(inplace=True)
    df["exchange"] = "Kraken"
    df["symbol"] = df["pair"]
    df["side"] = df["type"].str.upper()
    df["price"] = df["price"]
    df["qty"] = df["vol"]
    df["date"] = df["time"]
    df = df[["exchange", "symbol", "date", "side", "price", "qty"]]
    df.to_csv(output_file, index=False, float_format="%.10f")
    print("Guardado en output/kraken_trades.csv")
    return df

### FIFO para calcular ganancias ###
def calcular_ganancias_fiscal(df):
    df = df.sort_values("date")
    resultados = []

    for moneda in df["symbol"].unique():
        operaciones = df[df["symbol"] == moneda]
        compras = []
        for _, op in operaciones.iterrows():
            if op["side"] == "BUY":
                compras.append({
                    "qty": op["qty"],
                    "price": op["price"],
                    "total": op["qty"] * op["price"],
                    "date": op["date"]
                })
            elif op["side"] == "SELL":
                qty_restante = op["qty"]
                total_coste = 0
                while qty_restante > 0 and compras:
                    lote = compras[0]
                    if lote["qty"] <= qty_restante:
                        qty_consumida = lote["qty"]
                        total_coste += qty_consumida * lote["price"]
                        qty_restante -= qty_consumida
                        compras.pop(0)
                    else:
                        qty_consumida = qty_restante
                        total_coste += qty_consumida * lote["price"]
                        lote["qty"] -= qty_consumida
                        qty_restante = 0

                valor_transmision = op["qty"] * op["price"]
                ganancia = valor_transmision - total_coste
                resultados.append({
                    "moneda": moneda,
                    "fecha_venta": op["date"].date(),
                    "valor_transmision": round(valor_transmision, 10),
                    "valor_adquisicion": round(total_coste, 10),
                    "ganancia": round(ganancia, 10)
                })

    df_resultados = pd.DataFrame(resultados)
    df_agrupado = df_resultados.groupby("moneda").agg({
        "valor_transmision": "sum",
        "valor_adquisicion": "sum",
        "ganancia": "sum"
    }).reset_index()

    return df_resultados, df_agrupado

### MAIN ###
if __name__ == "__main__":
    # Binance: cargar desde bruto o descargar
    if not os.path.exists("output/binance_bruto.csv"):
        obtener_y_guardar_binance_bruto()

    df_binance = procesar_binance_desde_bruto()

    # Kraken: cargar o descargar
    df_kraken = get_kraken_trades()

    # Unir y calcular
    df_total = pd.concat([df_binance, df_kraken], ignore_index=True)
    df_total = df_total[["symbol", "date", "side", "qty", "price"]]

    print("Calculando ganancias fiscales usando FIFO...")
    detalles, resumen = calcular_ganancias_fiscal(df_total)
    detalles.to_csv("output/operaciones_detalladas.csv", index=False, float_format="%.10f")
    resumen.to_csv("output/ganancias_agrupadas.csv", index=False, float_format="%.10f")
    print("Resumen guardado en output/ganancias_agrupadas.csv")

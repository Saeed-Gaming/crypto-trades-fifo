# Crypto Trades FIFO (Binance + Kraken)

Herramienta en Python para descargar operaciones **spot** de Binance y Kraken, normalizarlas y calcular **ganancias/pérdidas** usando el método **FIFO**, exportando resultados a CSV.

## ✨ Funciones
- **Binance**: descarga trades por cada par con cotizada **USDT**, guarda crudo y lo normaliza.
- **Kraken**: obtiene trades con `pykrakenapi`, filtra por fechas y exporta.
- **FIFO**: une ambas fuentes y calcula resultados detallados y agregados por símbolo.

## 📦 Requisitos
- Python 3.9+
- Dependencias (ver `requirements.txt`):
  - `python-binance`, `krakenex`, `pykrakenapi`, `pandas` *(opcional `python-dotenv`)*

## 🔐 Configuración

BINANCE_API_KEY=...
BINANCE_API_SECRET=...
KRAKEN_API_KEY=...
KRAKEN_API_SECRET=...

> Desde el fichero `config.py` para fijar valores.

## ▶️ Uso

1. Instala dependencias:
   pip install -r requirements.txt

2. Exporta datos de Binance (opcional, si no existe el CSV crudo):
   python binance_dump.py
   Genera `output/binance_bruto.csv`.

3. Ejecuta el pipeline completo:
   python main.py

Archivos de salida:
- `output/binance_bruto.csv` *(crudo de Binance)*
- `output/binance_trades.csv` *(normalizado Binance)*
- `output/kraken_trades.csv` *(Kraken)*
- `output/operaciones_detalladas.csv` *(FIFO por operación de venta)*
- `output/ganancias_agrupadas.csv` *(resumen por símbolo)*

## ⚠️ Notas y limitaciones
- El fetch de Binance recorre **todos los pares USDT**; puede tardar y estar sujeto a *rate limits*. Reintenta si falla algún par.
- Las **comisiones** se guardan desde Binance (`commission`, `commissionAsset`) pero **no se integran** al coste en el cálculo FIFO por defecto.
- Los datos son **spot** (no futuros/márgenes).
- El cálculo FIFO es a nivel **símbolo**; no convierte divisa a EUR/USD. Si necesitas fiscalidad por fiat, añade conversión al tipo de cambio histórico.

## 📜 Licencia
MIT

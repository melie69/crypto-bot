import requests
import pandas as pd
import ta
import time
import schedule
import os
import hmac
import hashlib
from urllib.parse import urlencode

# ===== CONFIGURATION =====
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "8175119797")
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY", "")

# 20 cryptos : symboles Binance (paires USDT)
CRYPTOS = {
    # --- LONG TERME (stables, fiables) ---
    "Bitcoin": "BTCUSDT",
    "Ethereum": "ETHUSDT",
    "BNB": "BNBUSDT",
    "Solana": "SOLUSDT",
    "Cardano": "ADAUSDT",
    "Avalanche": "AVAXUSDT",
    "Chainlink": "LINKUSDT",
    "Polkadot": "DOTUSDT",
    "Litecoin": "LTCUSDT",
    "XRP": "XRPUSDT",
    # --- COURT TERME (plus volatiles = plus d'opportunites rapides) ---
    "Dogecoin": "DOGEUSDT",
    "Shiba Inu": "SHIBUSDT",
    "Pepe": "PEPEUSDT",
    "Injective": "INJUSDT",
    "Arbitrum": "ARBUSDT",
    "Optimism": "OPUSDT",
    "Aptos": "APTUSDT",
    "Sui": "SUIUSDT",
    "Render": "RENDERUSDT",
    "Fetch.ai": "FETUSDT",
}

RSI_PERIOD = 14
RSI_ACHAT = 35
RSI_VENTE = 65

# ===== RECUPERATION PRIX VIA BINANCE =====
def get_prix(symbol):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": 100
    }
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    if isinstance(data, list) and len(data) > 0:
        closes = [float(item[4]) for item in data]  # index 4 = close price
        return closes
    else:
        raise ValueError(f"Reponse invalide pour {symbol}: {data}")

# ===== CALCUL RSI =====
def calculer_rsi(closes):
    series = pd.Series(closes)
    rsi = ta.momentum.RSIIndicator(series, window=RSI_PERIOD).rsi()
    return round(rsi.iloc[-1], 2)

# ===== CALCUL GAIN/PERTE =====
def calcul_gain_perte(closes):
    if len(closes) >= 2:
        variation = ((closes[-1] - closes[-2]) / closes[-2]) * 100
        return round(variation, 2)
    return 0.0

# ===== ENVOI TELEGRAM =====
def envoyer_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Erreur Telegram: {e}")

# ===== ANALYSE PRINCIPALE =====
def analyser():
    print("Analyse en cours...")
    alertes = []

    for nom, symbol in CRYPTOS.items():
        try:
            closes = get_prix(symbol)
            prix_actuel = closes[-1]
            rsi = calculer_rsi(closes)
            variation = calcul_gain_perte(closes)
            signe = "+" if variation >= 0 else ""
            print(f"{nom} | {prix_actuel}$ | RSI: {rsi} | {signe}{variation}%")

            if rsi < RSI_ACHAT:
                alertes.append(
                    f"<b>ACHAT possible</b> - {nom}\n"
                    f"Prix: {prix_actuel}$\n"
                    f"RSI: {rsi} (survente)\n"
                    f"Variation 1h: {signe}{variation}%"
                )
            elif rsi > RSI_VENTE:
                alertes.append(
                    f"<b>VENTE possible</b> - {nom}\n"
                    f"Prix: {prix_actuel}$\n"
                    f"RSI: {rsi} (surachat)\n"
                    f"Variation 1h: {signe}{variation}%"
                )

        except Exception as e:
            print(f"Erreur pour {nom}: {e}")

    if alertes:
        message = "\n\n".join(alertes)
        envoyer_telegram(message)
        print(f"Analyse terminee ! {len(alertes)} alerte(s) envoyee(s)")
    else:
        print("Aucun signal detecte - marche calme")
        envoyer_telegram("Analyse terminee - Aucun signal fort detecte")

# ===== LANCEMENT =====
print("Bot crypto demarre !")
analyser()
schedule.every(1).hours.do(analyser)

while True:
    schedule.run_pending()
    time.sleep(60)

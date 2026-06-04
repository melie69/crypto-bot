import requests
import pandas as pd
import ta
import time
import schedule
import os

# ===== CONFIGURATION =====
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "8175119797")
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.environ.get("BINANCE_SECRET_KEY", "")

# ===== 50 CRYPTOS =====
CRYPTOS = {
    # --- LONG TERME (solides) ---
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
    "Cosmos": "ATOMUSDT",
    "Uniswap": "UNIUSDT",
    "Aave": "AAVEUSDT",
    "Filecoin": "FILUSDT",
    "Near": "NEARUSDT",
    "Stellar": "XLMUSDT",
    "Tron": "TRXUSDT",
    "Monero": "XMRUSDT",
    "Ethereum Classic": "ETCUSDT",
    "Internet Computer": "ICPUSDT",
    # --- MOYEN TERME (DeFi/Layer2) ---
    "Arbitrum": "ARBUSDT",
    "Optimism": "OPUSDT",
    "Injective": "INJUSDT",
    "Aptos": "APTUSDT",
    "Sui": "SUIUSDT",
    "Render": "RENDERUSDT",
    "Fetch.ai": "FETUSDT",
    "Bonk": "BONKUSDT",
    "WIF": "WIFUSDT",
    "Notcoin": "NOTUSDT",
    "Floki": "FLOKIUSDT",
    "Turbo": "TURBOUSDT",
    "Starknet": "STRKUSDT",
    "Mantle": "MNTUSDT",
    "Sei": "SEIUSDT",
    # --- COURT TERME (memecoins / volatiles) ---
    "Dogecoin": "DOGEUSDT",
    "Shiba Inu": "SHIBUSDT",
    "Pepe": "PEPEUSDT",
    "Brett": "BRETTUSDT",
    "Mog": "MOGUSDT",
    "Cat in a Dogs World": "MEWUSDT",
    "Book of Meme": "BOOMUSDT",
    "Popcat": "POPCATUSDT",
    "Neiro": "NEIROUSDT",
    "Goat": "GOATUSDT",
    "Act I": "ACTUSDT",
    "Grass": "GRASSUSDT",
    "Pnut": "PNUTUSDT",
    "Moodeng": "MOODENGUSDT",
    "Sundog": "SUNDOGUSDT",
}

RSI_PERIOD = 14
RSI_ACHAT = 40
RSI_VENTE = 60

# ===== PRIX VIA BINANCE =====
def get_prix(symbol):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": "1h", "limit": 100}
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    if isinstance(data, list) and len(data) > 0:
        return [float(item[4]) for item in data]
    raise ValueError(f"Reponse invalide pour {symbol}")

# ===== CALCUL RSI =====
def calculer_rsi(closes):
    series = pd.Series(closes)
    rsi = ta.momentum.RSIIndicator(series, window=RSI_PERIOD).rsi()
    return round(rsi.iloc[-1], 2)

# ===== ENVOI TELEGRAM =====
def envoyer_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Erreur Telegram: {e}")

# ===== ANALYSE =====
def analyser():
    print("Analyse en cours...")
    alertes = []

    for nom, symbol in CRYPTOS.items():
        try:
            closes = get_prix(symbol)
            prix = closes[-1]
            rsi = calculer_rsi(closes)
            variation = round(((closes[-1] - closes[-2]) / closes[-2]) * 100, 2)
            signe = "+" if variation >= 0 else ""
            print(f"{nom} | {prix}$ | RSI: {rsi} | {signe}{variation}%")

            if rsi < RSI_ACHAT:
                alertes.append(
                    f"🟢 <b>OPPORTUNITE ACHAT</b> - <b>{nom}</b>\n"
                    f"💰 Prix : <b>{prix} $</b>\n"
                    f"📊 RSI : <b>{rsi}</b> (survente)\n"
                    f"📈 Variation 1h : <b>{signe}{variation}%</b>\n"
                    f"👉 Potentiel rebond"
                )
            elif rsi > RSI_VENTE:
                alertes.append(
                    f"🔴 <b>SIGNAL VENTE</b> - <b>{nom}</b>\n"
                    f"💰 Prix : <b>{prix} $</b>\n"
                    f"📊 RSI : <b>{rsi}</b> (surachat)\n"
                    f"📈 Variation 1h : <b>{signe}{variation}%</b>\n"
                    f"👉 Attention correction possible"
                )

        except Exception as e:
            print(f"Erreur pour {nom}: {e}")

    if alertes:
        header = f"🚨 <b>CRYPTO ALERTE by Mel</b> 🚨\n{len(alertes)} signal(s) sur 50 cryptos\n" + "━"*25 + "\n\n"
        message = header + "\n\n".join(alertes)
        envoyer_telegram(message)
        print(f"Analyse terminee ! {len(alertes)} alerte(s) envoyee(s)")
    else:
        print("Aucun signal - marche calme - pas de message")

# ===== LANCEMENT =====
print("Bot crypto demarre ! 50 cryptos surveillees")
analyser()
schedule.every(1).hours.do(analyser)

while True:
    schedule.run_pending()
    time.sleep(60)

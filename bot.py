import os
import requests
import pandas as pd
import schedule
import time
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

CRYPTOS = [
    ("Bitcoin", "BTCUSDT"),
    ("Ethereum", "ETHUSDT"),
    ("BNB", "BNBUSDT"),
    ("Solana", "SOLUSDT"),
    ("XRP", "XRPUSDT"),
    ("Dogecoin", "DOGEUSDT"),
    ("Cardano", "ADAUSDT"),
    ("Avalanche", "AVAXUSDT"),
    ("Polkadot", "DOTUSDT"),
    ("Chainlink", "LINKUSDT"),
    ("Polygon", "MATICUSDT"),
    ("Litecoin", "LTCUSDT"),
    ("Uniswap", "UNIUSDT"),
    ("Cosmos", "ATOMUSDT"),
    ("Stellar", "XLMUSDT"),
    ("Monero", "XMRUSDT"),
    ("Algorand", "ALGOUSDT"),
    ("VeChain", "VETUSDT"),
    ("Filecoin", "FILUSDT"),
    ("Aave", "AAVEUSDT"),
    ("Tron", "TRXUSDT"),
    ("Tezos", "XTZUSDT"),
    ("EOS", "EOSUSDT"),
    ("Near", "NEARUSDT"),
    ("Fantom", "FTMUSDT"),
    ("Hedera", "HBARUSDT"),
    ("Aptos", "APTUSDT"),
    ("Arbitrum", "ARBUSDT"),
    ("Optimism", "OPUSDT"),
    ("Injective", "INJUSDT"),
    ("Render", "RENDERUSDT"),
    ("Sei", "SEIUSDT"),
    ("Sui", "SUIUSDT"),
    ("Blur", "BLURUSDT"),
    ("Lido DAO", "LDOUSDT"),
    ("Maker", "MKRUSDT"),
    ("Compound", "COMPUSDT"),
    ("Curve", "CRVUSDT"),
    ("dYdX", "DYDXUSDT"),
    ("1inch", "1INCHUSDT"),
    ("Sandbox", "SANDUSDT"),
    ("Decentraland", "MANAUSDT"),
    ("Axie Infinity", "AXSUSDT"),
    ("Gala", "GALAUSDT"),
    ("Enjin", "ENJUSDT"),
    ("Zilliqa", "ZILUSDT"),
    ("Waves", "WAVESUSDT"),
    ("Jasmy", "JASMYUSDT"),
    ("Floki", "FLOKIUSDT"),
    ("Pepe", "PEPEUSDT"),
]

RSI_ACHAT = 40
RSI_VENTE = 60


def envoyer_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        print(f"Erreur Telegram: {e}")


def get_prix_binance(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        r = requests.get(url, timeout=10)
        data = r.json()
        if "lastPrice" in data:
            return float(data["lastPrice"]), float(data["priceChangePercent"])
        return None, None
    except:
        return None, None


def get_rsi(symbol, period=14):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=100"
        r = requests.get(url, timeout=10)
        klines = r.json()
        if not isinstance(klines, list) or len(klines) < period + 1:
            return None
        closes = pd.Series([float(k[4]) for k in klines])
        delta = closes.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi.iloc[-1], 1)
    except:
        return None


def analyser():
    heure = datetime.now().strftime("%H:%M")
    print(f"Analyse en cours... {heure}")

    alertes = []
    resume_lignes = []

    for nom, symbol in CRYPTOS:
        try:
            prix, variation = get_prix_binance(symbol)
            rsi = get_rsi(symbol)

            if prix is None or rsi is None:
                print(f"Donnees manquantes pour {symbol}")
                continue

            signe = "+" if variation >= 0 else ""
            emoji_rsi = "🟢" if rsi < RSI_ACHAT else ("🔴" if rsi > RSI_VENTE else "⚪")

            ligne = f"{emoji_rsi} <b>{nom}</b> | ${prix:,.4f} | RSI {rsi} | {signe}{variation:.2f}%"
            resume_lignes.append(ligne)

            if rsi < RSI_ACHAT:
                alertes.append(
                    f"🟢 <b>ACHAT</b> - <b>{nom}</b>\n"
                    f"💰 Prix : <b>{prix:,.4f} $</b>\n"
                    f"📊 RSI : <b>{rsi}</b> (survendu)\n"
                    f"📈 Variation 1h : <b>{signe}{variation:.2f}%</b>"
                )
            elif rsi > RSI_VENTE:
                alertes.append(
                    f"🔴 <b>VENTE</b> - <b>{nom}</b>\n"
                    f"💰 Prix : <b>{prix:,.4f} $</b>\n"
                    f"📊 RSI : <b>{rsi}</b> (surachat)\n"
                    f"📈 Variation 1h : <b>{signe}{variation:.2f}%</b>"
                )
        except Exception as e:
            print(f"Erreur {nom}: {e}")

    if alertes:
        msg = f"🚨 <b>SIGNAUX DETECTES</b> 🚨\n" + "="*22 + "\n\n" + "\n\n".join(alertes)
        envoyer_telegram(msg)

    if resume_lignes:
        chunks = [resume_lignes[i:i+20] for i in range(0, len(resume_lignes), 20)]
        for i, chunk in enumerate(chunks):
            header = f"📊 <b>RAPPORT {heure}</b>\n⚪ neutre 🟢 achat 🔴 vente\n" + "="*22 + "\n\n"
            envoyer_telegram(header + "\n".join(chunk))

    print(f"Analyse terminee ! Resume envoye. {len(alertes)} alerte(s) forte(s).")


# ===== LANCEMENT =====
print("Bot crypto demarre !")
analyser()
schedule.every(1).hours.do(analyser)

while True:
    schedule.run_pending()
    time.sleep(30)

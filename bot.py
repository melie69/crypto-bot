import os
import requests
import schedule
import time
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

CRYPTOS = [
    ("Bitcoin", "bitcoin", "BTC"),
    ("Ethereum", "ethereum", "ETH"),
    ("BNB", "binancecoin", "BNB"),
    ("Solana", "solana", "SOL"),
    ("XRP", "ripple", "XRP"),
    ("Dogecoin", "dogecoin", "DOGE"),
    ("Cardano", "cardano", "ADA"),
    ("Avalanche", "avalanche-2", "AVAX"),
    ("Polkadot", "polkadot", "DOT"),
    ("Chainlink", "chainlink", "LINK"),
    ("Polygon", "matic-network", "MATIC"),
    ("Litecoin", "litecoin", "LTC"),
    ("Uniswap", "uniswap", "UNI"),
    ("Cosmos", "cosmos", "ATOM"),
    ("Stellar", "stellar", "XLM"),
    ("Aave", "aave", "AAVE"),
    ("Tron", "tron", "TRX"),
    ("Near", "near", "NEAR"),
    ("Fantom", "fantom", "FTM"),
    ("Aptos", "aptos", "APT"),
    ("Arbitrum", "arbitrum", "ARB"),
    ("Optimism", "optimism", "OP"),
    ("Injective", "injective-protocol", "INJ"),
    ("Sui", "sui", "SUI"),
    ("Pepe", "pepe", "PEPE"),
    ("Floki", "floki", "FLOKI"),
    ("Sandbox", "the-sandbox", "SAND"),
    ("Decentraland", "decentraland", "MANA"),
    ("Axie Infinity", "axie-infinity", "AXS"),
    ("Gala", "gala", "GALA"),
]

RSI_ACHAT = 40
RSI_VENTE = 60


def envoyer_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        if r.status_code != 200:
            print(f"Telegram erreur {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Erreur Telegram: {e}")


def get_donnees_batch(ids):
    try:
        ids_str = ",".join(ids)
        url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={ids_str}&order=market_cap_desc&per_page=50&page=1&sparkline=false&price_change_percentage=24h"
        r = requests.get(url, timeout=15)
        data = r.json()
        result = {}
        for coin in data:
            result[coin["id"]] = {
                "prix": coin["current_price"],
                "variation": coin["price_change_percentage_24h"] or 0,
                "market_cap_rank": coin.get("market_cap_rank", 0),
            }
        return result
    except Exception as e:
        print(f"Erreur CoinGecko: {e}")
        return {}


def get_rsi(coin_id, period=14):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=4&interval=hourly"
        r = requests.get(url, timeout=15)
        data = r.json()
        if "prices" not in data:
            return None
        closes = [p[1] for p in data["prices"]]
        if len(closes) < period + 2:
            return None
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas[-period*2:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period*2:]]
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 99.0 if avg_gain > 0 else 50.0
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 1)
    except:
        return None


def signal_texte(rsi):
    if rsi is None:
        return "⬜ N/A"
    if rsi < 30:
        return "🟢🟢 ACHAT FORT"
    if rsi < RSI_ACHAT:
        return "🟢 Achat"
    if rsi > 70:
        return "🔴🔴 VENTE FORTE"
    if rsi > RSI_VENTE:
        return "🔴 Vente"
    return "⚪ Neutre"


def format_prix(p):
    if p is None:
        return "N/A"
    if p >= 1:
        return f"${p:,.2f}"
    if p >= 0.001:
        return f"${p:.4f}"
    return f"${p:.8f}"


def analyser():
    heure = datetime.now().strftime("%H:%M")
    date = datetime.now().strftime("%d/%m/%Y")
    print(f"Analyse en cours... {heure}")

    ids = [cid for _, cid, _ in CRYPTOS]
    prix_data = get_donnees_batch(ids)

    if not prix_data:
        envoyer_telegram(f"⚠️ Impossible de recuperer les donnees a {heure}.")
        return

    alertes_fortes = []
    alertes_normales = []
    resume_lignes = []

    for nom, coin_id, ticker in CRYPTOS:
        try:
            if coin_id not in prix_data:
                continue

            d = prix_data[coin_id]
            prix = d["prix"]
            variation = d["variation"]

            rsi = get_rsi(coin_id)
            time.sleep(1.2)

            signe = "+" if variation >= 0 else ""
            var_emoji = "📈" if variation >= 0 else "📉"
            signal = signal_texte(rsi)
            rsi_str = str(rsi) if rsi else "N/A"

            ligne = (
                f"{signal} | <b>{nom}</b> ({ticker})\n"
                f"   💰 {format_prix(prix)} | {var_emoji} {signe}{variation:.1f}% | RSI {rsi_str}"
            )
            resume_lignes.append(ligne)

            if rsi is not None and rsi < 30:
                alertes_fortes.append((nom, ticker, prix, variation, rsi, "ACHAT FORT"))
            elif rsi is not None and rsi > 70:
                alertes_fortes.append((nom, ticker, prix, variation, rsi, "VENTE FORTE"))
            elif rsi is not None and rsi < RSI_ACHAT:
                alertes_normales.append((nom, ticker, prix, variation, rsi, "Achat"))
            elif rsi is not None and rsi > RSI_VENTE:
                alertes_normales.append((nom, ticker, prix, variation, rsi, "Vente"))

        except Exception as e:
            print(f"Erreur {nom}: {e}")

    # Alertes fortes en premier
    if alertes_fortes:
        msg = "🚨🚨 <b>SIGNAL FORT DETECTE</b> 🚨🚨\n"
        for nom, ticker, prix, variation, rsi, type_signal in alertes_fortes:
            signe = "+" if variation >= 0 else ""
            emoji = "🟢" if "ACHAT" in type_signal else "🔴"
            msg += (
                f"\n{emoji} <b>{type_signal} — {nom} ({ticker})</b>\n"
                f"💰 Prix : <b>{format_prix(prix)}</b>\n"
                f"📊 RSI : <b>{rsi}</b>\n"
                f"📈 Variation 24h : <b>{signe}{variation:.1f}%</b>\n"
                f"——————————"
            )
        envoyer_telegram(msg)

    if alertes_normales:
        msg = "💡 <b>Signaux detectes</b>\n"
        for nom, ticker, prix, variation, rsi, type_signal in alertes_normales:
            signe = "+" if variation >= 0 else ""
            emoji = "🟢" if "Achat" in type_signal else "🔴"
            msg += f"{emoji} <b>{nom}</b> ({ticker}) — RSI {rsi} | {format_prix(prix)} | {signe}{variation:.1f}%\n"
        envoyer_telegram(msg)

    # Rapport horaire
    if resume_lignes:
        nb_achat = sum(1 for l in resume_lignes if "🟢" in l)
        nb_vente = sum(1 for l in resume_lignes if "🔴" in l)
        nb_neutre = len(resume_lignes) - nb_achat - nb_vente

        header = (
            f"📊 <b>RAPPORT CRYPTO — {heure} ({date})</b>\n"
            f"🟢 Achat: {nb_achat} | ⚪ Neutre: {nb_neutre} | 🔴 Vente: {nb_vente}\n"
            f"{'='*24}\n"
        )

        chunks = [resume_lignes[i:i+10] for i in range(0, len(resume_lignes), 10)]
        for i, chunk in enumerate(chunks):
            part = f" (partie {i+1}/{len(chunks)})" if len(chunks) > 1 else ""
            envoyer_telegram(header.replace("</b>\n", f"{part}</b>\n", 1) + "\n\n".join(chunk))
            time.sleep(1)

    total = len(alertes_fortes) + len(alertes_normales)
    print(f"Analyse terminee ! {total} signal(s). {len(resume_lignes)} cryptos OK.")


# ===== LANCEMENT =====
print("Bot crypto demarre !")
envoyer_telegram(
    "🤖 <b>Crypto Alerte Bot — Demarre</b>\n"
    f"🗓 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
    "⚪ Rapport toutes les heures\n"
    "🟢 Signal achat si RSI < 40\n"
    "🔴 Signal vente si RSI > 60"
)
analyser()
schedule.every(1).hours.do(analyser)

while True:
    schedule.run_pending()
    time.sleep(30)

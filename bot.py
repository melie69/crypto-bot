import requests
import pandas as pd
import ta
import time
import schedule
import os

# ===== CONFIGURATION =====
TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("CHAT_ID", "8175119797")

# 20 cryptos : court terme (volatiles) + long terme (solides)
CRYPTOS = {
    # --- LONG TERME (stables, fiables) ---
    "Bitcoin": "bitcoin",
    "Ethereum": "ethereum",
    "BNB": "binancecoin",
    "Solana": "solana",
    "Cardano": "cardano",
    "Avalanche": "avalanche-2",
    "Chainlink": "chainlink",
    "Polkadot": "polkadot",
    "Litecoin": "litecoin",
    "XRP": "ripple",
    # --- COURT TERME (plus volatiles = plus d opportunites rapides) ---
    "Dogecoin": "dogecoin",
    "Shiba Inu": "shiba-inu",
    "Pepe": "pepe",
    "Injective": "injective-protocol",
    "Arbitrum": "arbitrum",
    "Optimism": "optimism",
    "Aptos": "aptos",
    "Sui": "sui",
    "Render": "render-token",
    "Fetch.ai": "fetch-ai"
}
# ==========================

def envoyer_alerte(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})
    print("Alerte envoyee !")

def get_prix(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": "5", "interval": "hourly"}
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    closes = [item[1] for item in data["prices"]]
    return closes

def calculer_rsi(closes):
    series = pd.Series(closes)
    rsi = ta.momentum.RSIIndicator(series, window=14).rsi()
    return round(rsi.iloc[-1], 2)

def force_signal(rsi):
    if rsi < 20:
        return "TRES FORT"
    elif rsi < 25:
        return "FORT"
    elif rsi < 30:
        return "MODERE"
    elif rsi > 80:
        return "TRES FORT"
    elif rsi > 75:
        return "FORT"
    else:
        return "MODERE"

def analyser_marche():
    print("Analyse en cours...")
    alertes_envoyes = 0
    for nom, coin_id in CRYPTOS.items():
        try:
            time.sleep(2)  # eviter le rate limit CoinGecko
            prix = get_prix(coin_id)
            rsi = calculer_rsi(prix)
            prix_actuel = round(prix[-1], 6 if prix[-1] < 0.01 else 2)
            force = force_signal(rsi)
            print(f"{nom} | {prix_actuel}$ | RSI: {rsi}")

            if rsi < 30:
                message = f"""<b>SIGNAL ACHAT - {nom}</b>

Force du signal : {force}
Prix actuel : {prix_actuel} $
RSI : {rsi} (survendu)
Signal : ACHETER
Stop-loss : {round(prix_actuel * 0.98, 6 if prix_actuel < 0.01 else 2)} $ (-2%)
Objectif : {round(prix_actuel * 1.04, 6 if prix_actuel < 0.01 else 2)} $ (+4%)
Raison : RSI sous 30 = rebond probable

Si tu investis 10 eur :
- Objectif gain : +0.40 eur
- Perte max : -0.20 eur"""
                envoyer_alerte(message)
                alertes_envoyes += 1

            elif rsi > 70:
                message = f"""<b>SIGNAL VENTE - {nom}</b>

Force du signal : {force}
Prix actuel : {prix_actuel} $
RSI : {rsi} (suracheté)
Signal : VENDRE / ATTENDRE
Stop-loss : {round(prix_actuel * 1.02, 6 if prix_actuel < 0.01 else 2)} $ (+2%)
Objectif : {round(prix_actuel * 0.96, 6 if prix_actuel < 0.01 else 2)} $ (-4%)
Raison : RSI au-dessus de 70 = correction probable"""
                envoyer_alerte(message)
                alertes_envoyes += 1

            else:
                print(f"Zone neutre - pas de signal pour {nom}")

        except Exception as e:
            print(f"Erreur pour {nom}: {e}")

    if alertes_envoyes == 0:
        print("Aucun signal detecte - marche calme")
    print(f"Analyse terminee ! {alertes_envoyes} alerte(s) envoyee(s)")

schedule.every(1).hours.do(analyser_marche)

analyser_marche()

while True:
    schedule.run_pending()
    time.sleep(60)

import requests
import pandas as pd
import ta
import time
import schedule

# ===== CONFIGURATION =====
TOKEN = "TON_TOKEN_ICI"
CHAT_ID = "8175119797"

CRYPTOS = {
    "Bitcoin": "bitcoin",
    "Ethereum": "ethereum",
    "Solana": "solana",
    "BNB": "binancecoin"
}
# ==========================

def envoyer_alerte(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})
    print("Alerte envoyee !")

def get_prix(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": "5", "interval": "hourly"}
    response = requests.get(url, params=params)
    data = response.json()
    closes = [item[1] for item in data["prices"]]
    return closes

def calculer_rsi(closes):
    series = pd.Series(closes)
    rsi = ta.momentum.RSIIndicator(series, window=14).rsi()
    return round(rsi.iloc[-1], 2)

def analyser_marche():
    print("Analyse en cours...")
    for nom, coin_id in CRYPTOS.items():
        try:
            prix = get_prix(coin_id)
            rsi = calculer_rsi(prix)
            prix_actuel = round(prix[-1], 2)
            print(f"{nom} | Prix: {prix_actuel}$ | RSI: {rsi}")

            if rsi < 30:
                message = f"""<b>SIGNAL ACHAT - {nom}</b>

Prix : {prix_actuel} $
RSI : {rsi} (survendu)
Signal : ACHETER
Stop-loss : {round(prix_actuel * 0.98, 2)} $ (-2%)
Objectif : {round(prix_actuel * 1.04, 2)} $ (+4%)
Raison : RSI sous 30 = rebond probable"""
                envoyer_alerte(message)

            elif rsi > 70:
                message = f"""<b>SIGNAL VENTE - {nom}</b>

Prix : {prix_actuel} $
RSI : {rsi} (suracheté)
Signal : VENDRE / ATTENDRE
Stop-loss : {round(prix_actuel * 1.02, 2)} $ (+2%)
Objectif : {round(prix_actuel * 0.96, 2)} $ (-4%)
Raison : RSI au-dessus de 70 = correction probable"""
                envoyer_alerte(message)

            else:
                print(f"Zone neutre - pas de signal pour {nom}")

        except Exception as e:
            print(f"Erreur pour {nom}: {e}")

    print("Analyse terminee !")

# Lancer l'analyse toutes les heures
schedule.every(1).hours.do(analyser_marche)

# Premiere analyse immediate
analyser_marche()

while True:
    schedule.run_pending()
    time.sleep(60)

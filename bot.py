import os
import requests
import schedule
import time
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# (nom, coingecko_id)
CRYPTOS = [
    ("Bitcoin", "bitcoin"),
    ("Ethereum", "ethereum"),
    ("BNB", "binancecoin"),
    ("Solana", "solana"),
    ("XRP", "ripple"),
    ("Dogecoin", "dogecoin"),
    ("Cardano", "cardano"),
    ("Avalanche", "avalanche-2"),
    ("Polkadot", "polkadot"),
    ("Chainlink", "chainlink"),
    ("Polygon", "matic-network"),
    ("Litecoin", "litecoin"),
    ("Uniswap", "uniswap"),
    ("Cosmos", "cosmos"),
    ("Stellar", "stellar"),
    ("Monero", "monero"),
    ("Algorand", "algorand"),
    ("VeChain", "vechain"),
    ("Filecoin", "filecoin"),
    ("Aave", "aave"),
    ("Tron", "tron"),
    ("Tezos", "tezos"),
    ("EOS", "eos"),
    ("Near", "near"),
    ("Fantom", "fantom"),
    ("Hedera", "hedera-hashgraph"),
    ("Aptos", "aptos"),
    ("Arbitrum", "arbitrum"),
    ("Optimism", "optimism"),
    ("Injective", "injective-protocol"),
    ("Render", "render-token"),
    ("Sei", "sei-network"),
    ("Sui", "sui"),
    ("Blur", "blur"),
    ("Lido DAO", "lido-dao"),
    ("Maker", "maker"),
    ("Compound", "compound-governance-token"),
    ("Curve", "curve-dao-token"),
    ("dYdX", "dydx"),
    ("1inch", "1inch"),
    ("Sandbox", "the-sandbox"),
    ("Decentraland", "decentraland"),
    ("Axie Infinity", "axie-infinity"),
    ("Gala", "gala"),
    ("Enjin", "enjincoin"),
    ("Zilliqa", "zilliqa"),
    ("Waves", "waves"),
    ("Jasmy", "jasmycoin"),
    ("Floki", "floki"),
    ("Pepe", "pepe"),
]

RSI_ACHAT = 40
RSI_VENTE = 60


def envoyer_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        print(f"Telegram: {r.status_code}")
    except Exception as e:
        print(f"Erreur Telegram: {e}")


def get_donnees_coingecko(ids):
    try:
        ids_str = ",".join(ids)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd&include_24hr_change=true"
        r = requests.get(url, timeout=15)
        return r.json()
    except Exception as e:
        print(f"Erreur CoinGecko prix: {e}")
        return {}


def get_rsi_coingecko(coin_id, period=14):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=3&interval=hourly"
        r = requests.get(url, timeout=15)
        data = r.json()
        if "prices" not in data or len(data["prices"]) < period + 1:
            return None
        closes = [p[1] for p in data["prices"]]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 1)
    except Exception as e:
        print(f"Erreur RSI {coin_id}: {e}")
        return None


def analyser():
    heure = datetime.now().strftime("%H:%M")
    print(f"Analyse en cours... {heure}")

    ids = [cid for _, cid in CRYPTOS]
    prix_data = get_donnees_coingecko(ids)

    alertes = []
    resume_lignes = []

    for nom, coin_id in CRYPTOS:
        try:
            if coin_id not in prix_data:
                print(f"Prix manquant: {coin_id}")
                continue

            prix = prix_data[coin_id].get("usd")
            variation = prix_data[coin_id].get("usd_24h_change", 0)

            if prix is None:
                continue

            rsi = get_rsi_coingecko(coin_id)
            if rsi is None:
                rsi = 50.0

            signe = "+" if variation >= 0 else ""
            emoji_rsi = "🟢" if rsi < RSI_ACHAT else ("🔴" if rsi > RSI_VENTE else "⚪")

            ligne = f"{emoji_rsi} <b>{nom}</b> | ${prix:,.4f} | RSI {rsi} | {signe}{variation:.2f}%"
            resume_lignes.append(ligne)

            if rsi < RSI_ACHAT:
                alertes.append(
                    f"🟢 <b>ACHAT</b> - <b>{nom}</b>\n"
                    f"💰 Prix : <b>${prix:,.4f}</b>\n"
                    f"📊 RSI : <b>{rsi}</b> (survendu)\n"
                    f"📈 Variation 24h : <b>{signe}{variation:.2f}%</b>"
                )
            elif rsi > RSI_VENTE:
                alertes.append(
                    f"🔴 <b>VENTE</b> - <b>{nom}</b>\n"
                    f"💰 Prix : <b>${prix:,.4f}</b>\n"
                    f"📊 RSI : <b>{rsi}</b> (surachat)\n"
                    f"📈 Variation 24h : <b>{signe}{variation:.2f}%</b>"
                )

            time.sleep(1.5)  # respect rate limit CoinGecko

        except Exception as e:
            print(f"Erreur {nom}: {e}")

    if alertes:
        msg = f"🚨 <b>SIGNAUX DETECTES</b> 🚨\n" + "="*22 + "\n\n" + "\n\n".join(alertes)
        envoyer_telegram(msg)

    if resume_lignes:
        chunks = [resume_lignes[i:i+15] for i in range(0, len(resume_lignes), 15)]
        for chunk in chunks:
            header = f"📊 <b>RAPPORT {heure}</b>\n⚪ neutre 🟢 achat 🔴 vente\n" + "="*22 + "\n\n"
            envoyer_telegram(header + "\n".join(chunk))
            time.sleep(1)
    else:
        envoyer_telegram(f"⚠️ Aucune donnee recue a {heure}. Verifier la connexion.")

    print(f"Analyse terminee ! {len(alertes)} alerte(s). {len(resume_lignes)} cryptos OK.")


# ===== LANCEMENT =====
print("Bot crypto demarre !")
envoyer_telegram("🤖 <b>Bot crypto demarre !</b>\nRapport toutes les heures. RSI achat < 40 | vente > 60")
analyser()
schedule.every(1).hours.do(analyser)

while True:
    schedule.run_pending()
    time.sleep(30)

#!/usr/bin/env python3
"""Score & value free .si candidates.

Input : data/available/<sweep>.txt   (NXDOMAIN => candidate free)
Output: data/score/scored_all.csv    (every candidate with score + value band)
        data/score/top_<n>.md        (markdown snippet for the reports)

Scoring (0-100) is a transparent sum of weighted factors:
  LENGTH       shorter is worth more (2-4 chars are the scarce asset)
  SL_WORD      real Slovenian word + corpus frequency (wordfreq 'sl')
  EN_WORD      real English word + corpus frequency (wordfreq 'en')
  COMMERCIAL   buyer-intent verticals (insurance, credit, travel, real estate...)
  AI_TECH      AI / "superintelligence" narrative (the 2026 price driver)
  GEO          city / region / tourist magnet
  NAME         first name (personal-brand use)
  PRONOUNCE    pronounceability of short combos (CVCV, vowel ratio)
  RISK         trademark / brand collision  (heavy penalty, can veto)

Value bands are calibrated on the public comps collected in
reports/01_Marktanalyse_si.md (NameBio: 110-34,000 USD; recursive.si 20,000 USD;
military.si 1,795 USD; local Slovenian market 400-500 EUR for good names).
"""
import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AVAIL = os.path.join(ROOT, "data", "available")
OUT = os.path.join(ROOT, "data", "score")

# ---------------------------------------------------------------- brand risk
# Registering these is pointless (ARDS/UDRP loss) or outright abusive.
BRANDS = set("""apple amazon google microsoft netflix facebook instagram whatsapp
twitter tiktok snapchat linkedin uber lyft airbnb booking expedia tripadvisor
nike adidas puma reebok zara hm mango primark gucci prada versace luisvuitton
louis vuitton hermes dior chanel armani boss mercedes bmw audi volkswagen
porsche ferrari lamborghini toyota honda nissan suzuki mazda renault peugeot
citroen fiat opel skoda seat volvo saab jaguar landrover tesla byd xiaomi
huawei samsung sony lg philips siemens bosch miele whirlpool electrolux gorenje
ikea lego disney pixar marvel warner sony music spotify deezer pandora
oracle ibm intel amd nvidia cisco dell hewlett lenovo asus acer canon nikon
visa mastercard americanexpress paypal revolut n26 monzo binance coinbase kraken
robinhood etoro coinmarketcap blockchain metamask openai anthropic deepmind
mistral perplexity midjourney stability runway elevenlabs notion figma canva
slack zoom teams discord telegram viber skype coca pepsi redbull monster
mcdonalds burgerking kfc subway starbucks dunkin nestle danone milka
mercator tus spar hofer lidl petrol telekom telemach a1 t2 amis nlb nkbm otp
triglav sava zavarovalnica krka lek sandoz iskra elan alpina adria posta
slovenske zeleznice bmwgroup porsche siemensenergy microsoftoffice chatgpt
gemini claude llama copilot sora grok""".split())

# ------------------------------------------------------------ intent buckets
COMMERCIAL_SL = set("""zavarovanje zavarovalnica avto avtomobil avtomobili rabljeni kredit
krediti posojilo posojila hipoteka leasing najem nepremicnine nepremicnina
stanovanje stanovanja hisa parcele zemljisca gradnja gradbenistvo obnova
streha okna vrata kuhinja kopalnica pohistvo elektrika ogrevanje vodovod
delo zaposlitev sluzba sluzbe kariera zaposlovanje zdravje zdravnik zobozdravnik
lekarne lekarna fizioterapija masaza kozmetika frizer lepota optika
pocitnice dopust letovanje potovanja potovanje turizem hotel hoteli apartma
apartmaji nastanitev penzion kamp smucanje smucisca wellness terme savna bazen
trgovina spletna nakupovanje popusti kuponi dostava restavracija picerija
kava kavarna pekarna vino vinoteka pivo poroke fotograf video glasba
ciscenje vrtnar vrtnarstvo veterinar oblacila moda nakit ure elektronika
telefon racunalnik prenosnik internet varovanje alarm odvetnik pravno
selitve prevoz taksi avtobus letalo karte energija solarni paneli reciklaza
stave stava igralnica casino poker ruleta loterija marketing oglasavanje
izobrazevanje tecaj vrtec solski ucenje dojencek otroci igre""".split())

AI_TECH = set("""ai agi asi agent agents superintelligence super intelligence
recursive intelligence neural model models llm llms gpt prompt bot bots chatbot
copilot inference training machine learning deepmind openai anthropic
robotics robot drone quantum crypto bitcoin ethereum solana web3 defi nft
token tokens blockchain wallet staking dao walletpay fintech insurtech
proptech healthtech medtech edtech legaltech martech hrtech salestech
agritech foodtech climatetech greentech deeptech hightech biotech
nanotech space satellite rocket automate automation autonomous compute
cloud server data dataset api sdk platform software hardware chip chips gpu
gpucluster datacenter edge aiagents assistant copilots generative
singularity cognition cognitive reasoning alignment""".split())

GENERIC_STRONG = set("""shop store market buy sell deal deals price prices cheap free best top
pay money cash gold bank credit loan invest fund trade news media press
jobs work career travel flight hotel car auto home house build life health
love chat date social video music game play win bonus""".split())


def zipf(word, lang):
    try:
        from wordfreq import zipf_frequency
        return zipf_frequency(word, lang)
    except Exception:
        return 0.0


def pronounceable(w):
    """Crude pronounceability for short combos."""
    if not w.isalpha():
        return 0.0
    vowels = sum(1 for c in w if c in "aeiou")
    v = 0.0
    if len(w) <= 4:
        if vowels >= 1:
            v += 10
        if 2 <= len(w) <= 3 and vowels >= 1:
            v += 6
        # no triple consonants
        if not re.search(r"[^aeiouy]{3}", w):
            v += 5
        if not re.search(r"[aeiou]{3}", w):
            v += 3
    return v


def score(name):
    w = name[:-3] if name.endswith(".si") else name
    n = len(w)
    reasons, s = [], 0.0

    # --- length (max 22)
    if n == 2:
        s += 22; reasons.append("2 Zeichen (knappstes Gut)")
    elif n == 3:
        s += 16; reasons.append("3 Zeichen")
    elif n == 4:
        s += 11; reasons.append("4 Zeichen")
    elif n == 5:
        s += 7
    elif n <= 7:
        s += 4
    elif n <= 10:
        s += 2
    else:
        s -= 2; reasons.append(f"lang ({n})")

    # --- word value
    zf_sl, zf_en = zipf(w, "sl"), zipf(w, "en")
    if zf_sl >= 4.0:
        s += 22; reasons.append(f"häufiges slowenisches Wort (zipf {zf_sl:.1f})")
    elif zf_sl >= 3.0:
        s += 15; reasons.append(f"slowenisches Wort (zipf {zf_sl:.1f})")
    elif zf_sl >= 2.0:
        s += 8; reasons.append("slowenisches Wort (selten)")
    if zf_en >= 4.5:
        s += 18; reasons.append(f"starkes englisches Wort (zipf {zf_en:.1f})")
    elif zf_en >= 3.5:
        s += 12; reasons.append(f"englisches Wort (zipf {zf_en:.1f})")
    elif zf_en >= 2.5:
        s += 6

    # --- intent
    if w in AI_TECH:
        s += 20; reasons.append("AI/Tech-Begriff (2026-Preistreiber)")
    if w in COMMERCIAL_SL:
        s += 18; reasons.append("slowenischer Handelsbegriff mit Kaufabsicht")
    if w in GENERIC_STRONG and n <= 8:
        s += 8; reasons.append("starker generischer Handelsbegriff")
    if w in BRANDS:
        s -= 60; reasons.append("!! MARKENKOLLISION - nicht registrieren")

    s += pronounceable(w)

    # --- cap
    s = max(0.0, min(100.0, s))
    return s, reasons, zf_sl, zf_en


def band(s):
    if s >= 85:
        return "AAA", "5.000 – 25.000 €+"
    if s >= 72:
        return "AA", "1.500 – 5.000 €"
    if s >= 60:
        return "A", "500 – 1.500 €"
    if s >= 48:
        return "B", "200 – 500 €"
    if s >= 36:
        return "C", "80 – 200 €"
    return "D", "< 80 € (eher Eigenbedarf)"


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for fn in sorted(os.listdir(AVAIL)):
        if not fn.endswith(".txt"):
            continue
        sweep = fn[:-4]
        with open(os.path.join(AVAIL, fn)) as f:
            for line in f:
                name = line.strip()
                if not name:
                    continue
                s, reasons, zsl, zen = score(name)
                b, eur = band(s)
                rows.append({"name": name, "score": round(s, 1), "band": b,
                             "est": eur, "len": len(name) - 3, "zipf_sl": round(zsl, 2),
                             "zipf_en": round(zen, 2), "sweep": sweep,
                             "why": "; ".join(reasons)})
    # keep everything that is short or has any signal; drop the pure noise tail
    kept = [r for r in rows if r["len"] <= 3 or r["score"] >= 30]
    dropped = len(rows) - len(kept)
    rows = kept
    rows.sort(key=lambda r: (-r["score"], r["len"], r["name"]))
    path = os.path.join(OUT, "scored_all.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} candidates scored ({dropped} noise rows dropped) -> {path}")
    bands = {}
    for r in rows:
        bands[r["band"]] = bands.get(r["band"], 0) + 1
    print("bands:", json.dumps(bands))
    for r in rows[:40]:
        print(f"  {r['score']:5.1f} {r['band']:3s} {r['name']:20s} {r['why'][:70]}")


if __name__ == "__main__":
    main()

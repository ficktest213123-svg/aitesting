#!/usr/bin/env python3
"""Build normalised .si candidate wordlists from raw sources.

Outputs (data/wordlists/):
  cities.txt          - world cities (pop. >100k) + curated Slovenian places
  names.txt           - international first names
  sl_commercial.txt   - curated high-intent Slovenian commercial terms
  intl_keywords.txt   - curated international / tech / trend terms

All output is ASCII-folded (the .si registry only accepts a-z 0-9 -) and
de-duplicated.
"""
import csv
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "data", "wordlists")

FOLD = {"š": "s", "č": "c", "ž": "z", "ć": "c", "đ": "d", "ł": "l",
        "ø": "o", "æ": "ae", "ß": "ss", "đ": "d"}


def fold(s):
    s = s.lower().strip()
    for k, v in FOLD.items():
        s = s.replace(k, v)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("đ", "d").replace("ß", "ss")
    s = re.sub(r"[^a-z0-9-]", "", s)
    return s.strip("-")


def write(name, words):
    seen, out = set(), []
    for w in words:
        w = fold(w)
        if not w or len(w) < 2 or len(w) > 63:
            continue
        if w.startswith("-") or w.endswith("-") or "--" in w:
            continue
        if w in seen:
            continue
        seen.add(w)
        out.append(w)
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        f.write("\n".join(sorted(out)) + "\n")
    print(f"{name}: {len(out)} terms")
    return out


# Curated Slovenian places (towns, tourist magnets, regions) - ASCII folded.
SL_PLACES = """ljubljana maribor celje kranj velenje koper novo-mesto ptuj trbovlje kamnik
jesenice domzale skofja-loka murska-sobota nova-gorica slovenj-gradec izola piran portoroz portoroz
bled bohinj kranjska-gora postojna sezana ajdovscina idrija logatec vrhnika grosuplje litija
radce lasko sevnica krsko brezice crnomelj metlika trebnje ribnica kocevje gornja-radgona lenart
ormoz ljutomer lendava ravne-na-koroskem dravograd radlje-ob-dravi mozirje zalec sentjur
rogaska-slatina slovenske-konjice zrece hoce ruse bovec kobarid tolminska most-na-soci
triglav soca dolenjska gorenjska primorska stalenska koroska prekmurje zasavje posavje
brdo kranj gorenjska slovenija ljubljansko barje goriska brda-vipava vipava
skocjanske-jame skocjan lipica ljubljanski-grad terme terme-catez terme-3000 terme-olenia
terme-dolenjske-toplice terme-zrece terme-topolsica terme-ptuj moravske-toplice
lake-bled lake-bohinj grad-bled grad-ljubljana ljubljana-maribor maribor-ptuj
kranjskagora kranjska-gora bled-skibled ski-bled kanin krvavec mariborsko-pohorje
pohorje rogla golte kanin-krvavec stari-vrh cerkno
celje-grad grad-celje ptuj-grad ljubljana-zoo
portoroz-lucija lucija strunjan pakostane""".split()

# Curated high-intent Slovenian commercial terms (buyer intent verticals).
SL_COMMERCIAL = """.zavarovanje zavarovalnica zavarovanja avto avtomobili rabljeni-avtomobili
avtomobilski servis gume vulkanizer avto-del avto-del servis vozila motor motorji kolo kolesa
elektricna-kolesa skuter motorno-kolo avtomehanik avtoprevoz selitve selitev prevoz prevozi
taksi avtobus letalo letalske-karte poleti dopust dopusti pocitnice pocitnice letovanje
potovanja potovanje turizem turisticna agencija hotel hoteli apartma apartmaji sobe
nastanitev penzion kamp kampiranje glamping pocitniski-dom gorska-koca planinska-koca
izlet izleti vikend aktivne-pocitnice wellness savna bazen terme kopalisca smucanje
smucisca tek-na-snegu sankanje pohodnistvo planinarjenje kolesarjenje ribolov lov
golf tenis nogomet kosarka rokomet hokej tek smuci snowboard potapljanje jadranje
surfanje rafting kajak kanu adrenalinski-park
nepremicnine nepremicnina stanovanje stanovanja hisa hise vikend parcele zemljisca
gradnja gradbenistvo gradbenik arhitekt projektiranje adaptacija renovacija obnova
streha strehe kritina fasada izolacija okna vrata vrata-sistemi senicila rolete
tla parket laminat keramika ploscice kopalnica kuhinja kuhinje pohistvo
elektrika elektrikar instalacije ogrevanje toplotna-crpalka klima hlajenje
vodovod vodovodne-instalacije plin plinske-instalacije
kredit krediti posojilo posojila hipoteka hipotekarni leasing najem najemi
leasing-avtomobila varcevanje investicije investiranje borza delnice kripto
kriptovalute bitcoin ethereum trading trgovanje menjalnica blokchain
banka bancni-racun placilne-kartice kartice gotovina racunovodstvo racunovodja
davki davcni-svetovanje place kadrovska sluzba
delo delovna-mesta zaposlitev zaposlitve sluzba sluzbe kariera prostih-delovnih-mest
zaposlovanje kadrovska-agencija student studentsko-delodajalci praksa pripravnistvo
izobrazevanje tecaji tecaj ucenje solski-center faks fakulteta vrtec varstvo
ucitelj tutorstvo instrukcije matematika anglescina nemscina
zdravje zdravnik zdravniki zdravstveni-dom ambulanta zobozdravnik zobozdravstvo
lekarne lekarna medicina terapija fizioterapija masa masa za masaza
masaza kozmetika kozmeticni-salon frizer frizerstvo salon lepota nega
optika ociscenje-zob beljenje-zob
igralnicna stavnica stave stave-sportne igralnica casino poker ruleta sloti
loterija srecke kviz nagradne-igre
trgovina trgovine spletna-trgovina trznica trzni-center nakupovanje
popusti kuponi akcije razprodaja outlet
dostava dostava-hrane hrana restavracija restavracije picerija burger
kava kavarna slaascicarna pekarna kruh pecivo vino vinoteka vinska-klet
pivo pivnica koktajli zabava dogodki eventi
poroke porocni-saloni fotograf fotografiranje video videoprodukcija
glasba bend dj orkester
ciscenje cistilni-servis pranje vzdrzevanje hisni-mojster vrtnar
vrtnarstvo urejanje-vrtov drevesnica rastline cvetlice roze trava trata
zivali pes macka veterinar pasji-dom pasja-sola hrana-za-pse
oblacila obleke moda cvelji jakne torbe ure nakit
elektronika telefon telefoni racunalnik racunalniki prenosnik tablica
popravilo servis-računalnikov telefonov gadgeti
internet telekomunikacije mobilni-operater optika-internet
varovanje varnost alarm videonadzor varovanje-objektov kljucavnicar
odvetnik odvetniki pravno-svetovanje notar pravna-pomoc cev
selitveni-servis skladisce skladiscenje selitvena-podjetja
profit dobiček podjetje podjetja startup podjetnistvo
oglasavanje marketing digitalni-marketing seo optimizacija
spletna-stran spletne-strani spletni-oblikovalec dizajn grafika
tisk tiskarna vizitke letaki plakati
energija elektrika plin solarni-paneli soncna-elektrarna fotonapetostne
reciklaza odpadki komunala odvoz-smeti
primerjava primerjalnik primerjava-cen ponudba ponudbe
ocene mnenja forum skupnost portal vodnik
zemljevid zemljevidi navigacija vreme vremenska-napoved
novice novice-danes casopis revija clanke branje
ljubezen zmenki zmenkarije druzenje prijatelji druzabna-omrezja
igre igralne-konsole igrice otroci otroci-igre
dojencki nosenice otroci-oprema
starostniki dom-za-ostarele nega-na-domu oskrba
avtosola vozni-izpit avtosole
selitev-v-tujino vizum potni-list
kmetija kmetijstvo ekolosko bio hrana-domača
lov ribolov gozd les lesena-gradnja
stroji strojna-oprema orodje
kemija cistila
pogreb pogrebno-podjetje
""".split()


def main():
    os.makedirs(OUT, exist_ok=True)
    cities = []
    p = os.path.join(RAW, "world-cities.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8", errors="ignore") as f:
            for row in csv.DictReader(f):
                cities.append(row.get("CityNameEn", ""))
    cities += SL_PLACES
    write("cities.txt", cities)

    names_p = os.path.join(RAW, "first-names.txt")
    if os.path.exists(names_p):
        with open(names_p, encoding="utf-8", errors="ignore") as f:
            write("names.txt", [l.strip() for l in f])

    write("sl_commercial.txt", SL_COMMERCIAL)

    kw = os.path.join(OUT, "intl_keywords.txt")
    if os.path.exists(kw):
        with open(kw, encoding="utf-8", errors="ignore") as f:
            toks = [l.split()[0] for l in f if l.strip() and not l.startswith("#")]
        write("intl_keywords.txt", toks)


if __name__ == "__main__":
    main()

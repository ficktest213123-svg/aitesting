# Methodik, Datenquellen & Datenqualität

Stand: 29.09.2026 · Wie die Kandidatenlisten entstanden sind und wie belastbar sie sind.

---

## 1. Zweistufiges Prüfverfahren

Weil die Registry (ARNES) keine Massenabfrage erlaubt, läuft die Prüfung in zwei Stufen:

### Stufe 1 – DNS-Massen-Prefilter (lokal, ~950 Abfragen/Sekunde)
Für jeden Kandidaten wird eine **NS-Anfrage (QTYPE=2)** gegen `8.8.8.8` gestellt.

| DNS-Antwort | Bedeutung | Behandlung |
|---|---|---|
| `NXDOMAIN` | Name nicht in der Zone → **Kandidat „frei"** | landet in `data/available/<sweep>.txt` |
| `NOERROR` + Answer | delegiert → **registriert & live** | verworfen |
| `SERVFAIL` (RCODE2) | **registriert, aber Nameserver kaputt/nicht erreichbar** | verworfen (Stichproben-verifiziert) |
| `FORMERR` (RCODE1) | ungültige Anfrage (z. B. UTF-8-Label mit š/č/ž) | Bug-Fix: Namen werden ASCII-gefaltet (š→s, č→c, ž→z) |
| `TIMEOUT` | Netzwerk | bis zu 3× erneut abgefragt |

Warum NS-Anfragen? Die Registry verlangt Nameserver für eine Delegierung. Eine delegierte Domain antwortet also mit NS-RRset, eine freie mit NXDOMAIN. Damit ist die Methode **schnell genug für Millionen Kandidaten** – der erschöpfende 4-Buchstaben-Scan (456.976 Kombinationen) lief in 8 Minuten.

### Stufe 2 – Autoritative Verifikation via RDAP (Registry)
```
GET https://rdap.register.si/domain/<name>.si
→ HTTP 404  {"errorCode":404,"title":"Domain 'x.si' not found"}  = FREI REGISTRIERBAR
→ HTTP 200  RDAP-Objekt mit status / events / registrar          = REGISTRIERT
```
Das ist die **Registry selbst** (ARNES) und damit die letzte Instanz.

---

## 2. ⚠️ Der wichtigste Datenqualitäts-Befund

> **Nicht jede NXDOMAIN-Domain ist frei.** Domains, die registriert, aber **„inactive"** sind (keine Nameserver hinterlegt – typisch für Investoren-Parkpositionen), sind im DNS **nicht sichtbar** und erscheinen deshalb wie frei.

Belege aus der Registry-RDAP (29.09.2026):

| Domain | DNS-Prefilter | RDAP-Realität |
|---|---|---|
| `ja.si` | „frei" (NXDOMAIN) | **registriert**, status `inactive`, Inhaber über Registrar NEO IT, verlängert bis 19.11.2026 |
| `hi.si` | „frei" (NXDOMAIN) | **registriert**, status `inactive`, Registrar SIMETRIC, bis 20.10.2027 |
| `pi.si` | „frei" (NXDOMAIN) | **registriert**, status `inactive`, Registrar NEO IT |
| `n8.si` | „frei" (NXDOMAIN) | **registriert**, status `pending delete` (lösch-reif) |

**Konsequenz:** Alle Top-Empfehlungen in diesem Projekt werden **einzeln per RDAP verifiziert**. Massenlisten sind als *„DNS-frei, RDAP-unverifiziert"* gekennzeichnet.

### Gemessene Trefferquoten der Stufe-1-Stichproben

| Stichprobe | geprüft | durch RDAP bestätigt frei | Fehlalarme |
|---|---|---|---|
| Zufällige slowenische Nomen | 6 | 6 | 0 % |
| Zufällige 3-Zeichen-Kombinationen | 10 | 10 | 0 % |
| Handverlesene Premium-Kandidaten (2 Zeichen, IT/ES-Reisewörter) | 10 | 7 | **30 %** |

→ **Je wertvoller ein Name, desto höher die Fehlalarmquote.** Genau deshalb ist die Verifikation Pflicht bei allem, was in Reports `03+` als Kaufempfehlung auftaucht.

---

## 3. Datenquellen der Kandidaten-Wortlisten

| Liste | Umfang | Quelle |
|---|---|---|
| Slowenische Nomen (Sloleks 3.1) | 43.334 | GitHub `BlazJe/slovenian-noun-wordlist` |
| Worthäufigkeiten slowenisch / englisch | je ~40.000 | `wordfreq` (Korpus-Frequenzen, Zipf-Skala) |
| Mehrsprachig: it, es, de, fr, pt, hr/sh, hu | 249.935 (dedup.) | `wordfreq` |
| Englische Vollwortliste | 370.105 | GitHub `dwyl/english-words` (`words_alpha.txt`) |
| Städte weltweit (Einw. >100k) + kuratierte slowenische Orte | 6.225 | GitHub `jamsshhayd/world-cities-translations` + eigene Kuratierung |
| Vornamen (international) | 4.941 | GitHub `dominictarr/random-name` |
| Kuratierte Handels-/Tech-Begriffe | 600 + 426 | eigene Kuratierung (2026-Horizont) |

Warum mehrsprachig? **„si" heißt auf Italienisch und Spanisch „ja"**, und Slowenien grenzt an Italien, Österreich, Kroatien und Ungarn. Ein italienisches Reise-Wort auf `.si` verkauft sich an einen 60-Mio.-Markt, nicht nur an 2 Mio. Slowenen. Das vervielfacht die potenzielle Käuferschaft.

---

## 4. Ausschlusskriterien (vor dem Scoring)

1. **Marken-Blacklist** (~250 globale und slowenische Marken: Apple, Google, Mercator, Krka, Triglav, Petrol …) → schwerer Score-Abzug (`-60`), taucht nie als Empfehlung auf. Grund: ARDS-Domainschiedsverfahren – der Markeninhaber gewinnt bei böswilliger Registrierung.
2. **Nur ASCII:** š/č/ž werden gefaltet; .si akzeptiert laut RDAP-Hinweis nur ASCII.
3. **Länge 2–63 Zeichen** (Registry-Regel), keine Bindestriche am Anfang/Ende.

---

## 5. Bekannte Grenzen dieser Untersuchung

| Grenze | Auswirkung | Gegenmaßnahme |
|---|---|---|
| „inactive"-Registrierungen sind im DNS unsichtbar | Fehlalarme in Massenlisten | RDAP-Verifikation aller Top-Kandidaten + Stichproben |
| Registry-reservierte Namen (z. B. Staats-/Ortsnamen) können RDAP-404 liefern, obwohl sie **nicht** registrierbar sind | Sonderfall `si.si` | Als Einzelfall markiert: „vor Registrierung beim Registrar testen" |
| Kein Zugang zu Suchvolumen/Google-Trends-Daten | Bewertung stützt sich auf Korpusfrequenz + Branchenlogik | Wortfrequenz (Zipf) als Proxy; Branchengewichtung |
| NameBio ist per Bot-Captcha blockiert | Keine vollständige Verkaufsliste abrufbar | Sekundärquellen (Domain Name Wire, NamePros, Dynadot) |
| Momentaufnahme 29.09.2026 | Kandidaten können jederzeit weg sein | Zeitstempel in jeder Datei; **sofort handeln statt später** |

---

## 6. Reproduzierbarkeit

Alle Schritte liegen als Skripte im Repo:

```bash
# 1) Wortlisten aufbauen
python3 tools/build_lists.py

# 2) Erschöpfender Kurzdomain-Scan (Beispiel: alle 3-stelligen Kombinationen)
python3 tools/sweep.py pattern --charset abcdefghijklmnopqrstuvwxyz0123456789 --len 3 s03

# 3) Wortlisten-Scan
python3 tools/sweep.py list data/wordlists/sl_nouns.txt sl_nouns

# 4) Scoring
python3 tools/score.py

# 5) Einzel-Verifikation gegen die Registry (braucht Internet)
curl -s https://rdap.register.si/domain/<name>.si | head -c 300
# 404 = frei
```

`data/available/` enthält die DNS-freien Kandidaten je Sweep, `data/stats/` die Lauf-Statistiken, `data/score/` das Scoring.

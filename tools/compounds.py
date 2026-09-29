#!/usr/bin/env python3
"""Generate compound candidate names (prefix/suffix pattern).

Focus on the 2026 value driver: AI / "superintelligence" compounds
(ai<word>, <word>ai, agent<word>, bot<word>) plus the productive
Slovenian prefixes (e- , moj-, naj-) and English brand prefixes (get-, my-, ...).
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WL = os.path.join(ROOT, "data", "wordlists")

AI_PREFIXES = ["ai", "agent", "agi", "gpt", "bot", "neuro", "deep", "smart", "auto", "quantum"]
SL_PREFIXES = ["e", "moj", "naj", "spletni", "hitri", "super", "top"]
AI_SUFFIXES = ["ai", "bot", "gpt", "agent", "lab", "labs", "hub", "app", "tech", "data",
               "cloud", "x", "one", "pro", "now", "online", "digital", "smart", "world"]
BRAND_PREFIXES = ["get", "my", "go", "try", "the", "use", "now", "easy", "fast", "best",
                  "neo", "ultra", "hyper", "omni", "zero", "open", "next", "one"]


def top_words(lang, n):
    p = os.path.join(WL, f"{lang}_freq.tsv")
    if not os.path.exists(p):
        return []
    out = []
    with open(p) as f:
        for i, line in enumerate(f):
            if i >= n:
                break
            w = line.split("\t")[0].strip()
            if 3 <= len(w) <= 10 and w.isalpha():
                out.append(w)
    return out


def main():
    roots_en = top_words("en", 2500)
    roots_sl = top_words("sl", 1500)
    roots_it = top_words("it", 1200)
    roots_es = top_words("es", 1200)
    words = set()
    for p in AI_PREFIXES:
        for r in roots_en + roots_it + roots_es:
            words.add(p + r)
    for s in AI_SUFFIXES:
        for r in roots_en[:1800] + roots_sl:
            words.add(r + s)
    for p in SL_PREFIXES:
        for r in roots_sl:
            words.add(p + r)
    for p in BRAND_PREFIXES:
        for r in roots_en[:900]:
            words.add(p + r)
    words = {w for w in words if 3 <= len(w) <= 20}
    path = os.path.join(WL, "compounds.txt")
    with open(path, "w") as f:
        f.write("\n".join(sorted(words)) + "\n")
    print(f"{len(words)} compound candidates -> {path}")


if __name__ == "__main__":
    main()

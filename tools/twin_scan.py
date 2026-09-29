#!/usr/bin/env python3
""".si <-> .ai twin scan.

Thesis (Netcraft, Sept 2026): 44,000 .ai / .si pairs already share the same
second-level name - i.e. 22 % of all .si domains mirror an .ai name. An .ai
registration costs ~$90-180/2y, so every registered .ai name is proof that
someone paid real money for that string.

This script finds the *inverse* case:
    <word>.ai  registered   (proven demand, someone paid for it)
    <word>.si  NXDOMAIN     (still free -> registerable at ~12 EUR)

Those are the highest-signal .si candidates: demand is demonstrated, the .si
twin is unclaimed.

Usage: python3 tools/twin_scan.py <wordlist1> [<wordlist2> ...] [--workers N]
Output: data/twins/twins_free_si.tsv, data/stats/twins.json
"""
import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sweep import dns_ns, ascii_fold  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(paths):
    words = set()
    for p in paths:
        with open(p, encoding="utf-8", errors="ignore") as f:
            for line in f:
                w = ascii_fold(line.strip().lower().split()[0] if line.strip() else "")
                if 2 <= len(w) <= 24:
                    words.add(w)
    return sorted(words)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wordlists", nargs="+")
    ap.add_argument("--workers", type=int, default=40)
    a = ap.parse_args()

    words = load(a.wordlists)
    print(f"[{time.strftime('%H:%M:%S')}] {len(words)} unique words", flush=True)

    def ai(w):
        return w, dns_ns(w + ".ai")[0]

    ai_reg = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for w, st in ex.map(ai, words):
            if st in ("NOERROR", "RCODE2"):
                ai_reg.append(w)
    print(f"[{time.strftime('%H:%M:%S')}] .ai registered: {len(ai_reg)} "
          f"({time.time()-t0:.0f}s)", flush=True)

    def si(w):
        return w, dns_ns(w + ".si")[0]

    free_twins, taken = [], []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=a.workers) as ex:
        for w, st in ex.map(si, ai_reg):
            (free_twins if st == "NXDOMAIN" else taken).append((w, st))
    print(f"[{time.strftime('%H:%M:%S')}] .si free twins: {len(free_twins)} "
          f"({time.time()-t0:.0f}s)", flush=True)

    os.makedirs(os.path.join(ROOT, "data", "twins"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "twins", "twins_free_si.tsv"), "w") as f:
        f.write("word\tai_status\tsi_status\n")
        for w, st in sorted(free_twins):
            f.write(f"{w}\tREGISTERED\tNXDOMAIN\n")
    with open(os.path.join(ROOT, "data", "twins", "twins_ai_names.txt"), "w") as f:
        f.write("\n".join(w for w, _ in sorted(ai_reg)) + "\n")
    import json
    with open(os.path.join(ROOT, "data", "stats", "twins.json"), "w") as f:
        json.dump({"words_checked": len(words), "ai_registered": len(ai_reg),
                   "si_free_twins": len(free_twins), "si_taken_twins": len(taken),
                   "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, f, indent=2)
    print(f"TOP TWINS: {', '.join(w for w,_ in sorted(free_twins)[:40])}", flush=True)


if __name__ == "__main__":
    main()

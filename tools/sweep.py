#!/usr/bin/env python3
"""Exhaustive / list-driven .si availability sweeps.

Stage 1 (this script): fast UDP-DNS prefilter (QTYPE=NS).
  NXDOMAIN  -> candidate free  (written to data/available/<sweep>.txt)
  NOERROR   -> delegated, i.e. registered & live
  TIMEOUT   -> retried, then written to data/retry/<sweep>.txt

Stage 2 (rdap_check helper + fetch_page): authoritative RDAP confirmation at
https://rdap.register.si/domain/<name>.si  -> 404 means truly free.

Usage:
  python3 tools/sweep.py pattern --charset abc --len 3 [--prefix x] out_name
  python3 tools/sweep.py list <wordlist_file> out_name
"""
import argparse
import itertools
import os
import re
import socket
import struct
import sys
import time
import unicodedata
import random
from concurrent.futures import ThreadPoolExecutor

FOLD = {"š": "s", "č": "c", "ž": "z", "ć": "c", "đ": "d", "ł": "l",
        "ø": "o", "æ": "ae", "ß": "ss", "Ć": "C"}


def ascii_fold(s):
    """Registry accepts ASCII only -> fold š/č/ž etc. (RDAP notice: ASCII only)."""
    s = s.strip().lower()
    for k, v in FOLD.items():
        s = s.replace(k, v.lower())
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9-]", "", s)
    return s.strip("-")

# Only 8.8.8.8 is reachable through this sandbox's egress allowlist (verified).
RESOLVERS = ["8.8.8.8"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def build_query(name, qtype=2):  # NS
    tid = random.randint(0, 0xFFFF)
    msg = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    for p in name.split("."):
        msg += bytes([len(p)]) + p.encode()
    msg += b"\x00" + struct.pack("!HH", qtype, 1)
    return tid, msg


def dns_ns(name, timeout=2.5):
    """Return (status, answer_count). status in NOERROR/NXDOMAIN/TIMEOUT/RCODEn."""
    for attempt in range(len(RESOLVERS)):
        tid, msg = build_query(name)
        res = RESOLVERS[(attempt + random.randint(0, len(RESOLVERS) - 1)) % len(RESOLVERS)]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        try:
            s.sendto(msg, (res, 53))
            data, _ = s.recvfrom(2048)
            if len(data) < 12 or struct.unpack("!H", data[:2])[0] != tid:
                continue
            flags, an = struct.unpack("!H", data[2:4])[0], struct.unpack("!H", data[6:8])[0]
            rcode = flags & 0xF
            if rcode == 0:
                return "NOERROR", an
            if rcode == 3:
                return "NXDOMAIN", 0
            return f"RCODE{rcode}", an
        except socket.timeout:
            continue
        except Exception:
            continue
        finally:
            s.close()
    return "TIMEOUT", 0


def check_batch(names, workers=48):
    results = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for n, (st, an) in zip(names, ex.map(dns_ns, names)):
            results.append((n, st, an))
    return results


def run(names, out_name, workers=48, quiet=False):
    t0 = time.time()
    free, taken, timeout, other = [], [], [], []
    servfail = []
    # pass 1
    for n, st, an in check_batch(names, workers):
        if st == "NXDOMAIN":
            free.append(n)
        elif st == "NOERROR":
            taken.append(n)
        elif st == "TIMEOUT":
            timeout.append(n)
        elif st == "RCODE2":
            # SERVFAIL: verified (absolvent.si, akademija.si) => registered with
            # broken nameservers. Kept separately for a low-rate re-check.
            servfail.append(n)
        else:
            other.append((n, st))
    # retry pass (single threaded-ish, tolerant)
    if timeout:
        time.sleep(1)
        still = []
        for n, st, an in check_batch(timeout, max(8, workers // 4)):
            if st == "NXDOMAIN":
                free.append(n)
            elif st == "NOERROR":
                taken.append(n)
            else:
                still.append(n)
        timeout = still

    os.makedirs(os.path.join(ROOT, "data", "available"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "data", "stats"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "available", f"{out_name}.txt"), "w") as f:
        f.write("\n".join(sorted(free)) + ("\n" if free else ""))
    if timeout:
        os.makedirs(os.path.join(ROOT, "data", "retry"), exist_ok=True)
        with open(os.path.join(ROOT, "data", "retry", f"{out_name}.txt"), "w") as f:
            f.write("\n".join(sorted(timeout)) + "\n")
    if other:
        os.makedirs(os.path.join(ROOT, "data", "other"), exist_ok=True)
        with open(os.path.join(ROOT, "data", "other", f"{out_name}.txt"), "w") as f:
            f.write("\n".join(f"{n}\t{st}" for n, st in sorted(other)) + "\n")
    if servfail:
        os.makedirs(os.path.join(ROOT, "data", "servfail"), exist_ok=True)
        with open(os.path.join(ROOT, "data", "servfail", f"{out_name}.txt"), "w") as f:
            f.write("\n".join(sorted(servfail)) + "\n")
    with open(os.path.join(ROOT, "data", "stats", f"{out_name}.json"), "w") as f:
        import json
        json.dump({
            "sweep": out_name, "checked": len(names), "candidate_free": len(free),
            "registered": len(taken), "timeout": len(timeout), "other": len(other),
            "servfail_registered_broken_dns": len(servfail),
            "seconds": round(time.time() - t0, 1),
            "rate_per_sec": round(len(names) / max(0.001, time.time() - t0), 1),
            "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }, f, indent=2)
    if not quiet:
        print(f"[{out_name}] checked={len(names)} free={len(free)} registered={len(taken)} "
              f"timeout={len(timeout)} other={len(other)} "
              f"in {time.time()-t0:.1f}s")
    return free


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pattern")
    p.add_argument("--charset", default="abcdefghijklmnopqrstuvwxyz")
    p.add_argument("--len", type=int, required=True)
    p.add_argument("--prefix", default="")
    p.add_argument("--suffix", default="")
    p.add_argument("--workers", type=int, default=48)
    p.add_argument("out")
    l = sub.add_parser("list")
    l.add_argument("wordlist")
    l.add_argument("out")
    l.add_argument("--workers", type=int, default=48)
    l.add_argument("--minlen", type=int, default=2)
    l.add_argument("--maxlen", type=int, default=63)
    a = ap.parse_args()

    if a.cmd == "pattern":
        combos = ["".join(t) for t in itertools.product(a.charset, repeat=a.len)]
        names = [f"{a.prefix}{c}{a.suffix}.si" for c in combos]
        run(names, a.out, a.workers)
    else:
        seen, names = set(), []
        with open(a.wordlist) as f:
            for line in f:
                w = line.strip().lower().split()[0] if line.strip() else ""
                w = ascii_fold(w.replace(".si", ""))
                if not w or len(w) < a.minlen or len(w) > a.maxlen:
                    continue
                if not all(c.isalnum() or c == "-" for c in w):
                    continue
                if w.startswith("-") or w.endswith("-") or "--" in w:
                    continue
                if w in seen:
                    continue
                seen.add(w)
                names.append(w + ".si")
        print(f"[list] {len(names)} unique names from {a.wordlist}")
        run(names, a.out, a.workers)


if __name__ == "__main__":
    main()

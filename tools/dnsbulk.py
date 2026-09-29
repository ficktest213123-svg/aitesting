#!/usr/bin/env python3
"""Bulk DNS pre-filter for .si domain availability.

Uses UDP DNS (QTYPE=NS) against public resolvers. NOERROR+answer(s) => delegated
(almost certainly registered). NXDOMAIN => not in DNS => candidate "free".
Second pass (RDAP) is required to confirm candidates.
"""
import socket, struct, sys, time, random
from concurrent.futures import ThreadPoolExecutor

RESOLVERS = ["8.8.8.8", "8.8.4.4", "1.1.1.1", "9.9.9.9"]
QTYPE_NS = 2

def build_q(name, qtype=QTYPE_NS):
    tid = random.randint(0, 0xFFFF)
    msg = struct.pack("!HHHHHH", tid, 0x0100, 1, 0, 0, 0)
    for p in name.split("."):
        msg += bytes([len(p)]) + p.encode()
    msg += b"\x00" + struct.pack("!HH", qtype, 1)
    return tid, msg

def query(name, qtype=QTYPE_NS, timeout=3.0, tries=3):
    for attempt in range(tries):
        tid, msg = build_q(name, qtype)
        res = RESOLVERS[attempt % len(RESOLVERS)]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        try:
            s.sendto(msg, (res, 53))
            data, _ = s.recvfrom(2048)
            if len(data) < 12:
                continue
            rtid, flags, qd, an, ns, ar = struct.unpack("!HHHHHH", data[:12])
            if rtid != tid:
                continue
            rcode = flags & 0xF
            return ("NOERROR" if rcode == 0 else ("NXDOMAIN" if rcode == 3 else f"RCODE{rcode}")), an
        except socket.timeout:
            continue
        except Exception:
            continue
        finally:
            s.close()
    return "TIMEOUT", 0

def main():
    names = [l.strip().lower() for l in sys.stdin if l.strip()]
    names = [n.split()[0] for n in names]
    out = []
    def work(n):
        st, an = query(n)
        return (n, st, an)
    with ThreadPoolExecutor(max_workers=24) as ex:
        for n, st, an in ex.map(work, names):
            print(f"{n}\t{st}\t{an}")
            out.append((n, st, an))

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Token usage for one conductor feature, split by coordinator and subagent type.

Usage: python3 usage.py <feature-slug> [project-dir]

Finds every conductor session of the project (one that touched .conductor/ledger.md)
that mentions design/<slug>/ (a feature spans several sessions when the coordinator
is cleared between phases) and sums the usage of those sessions and their subagents.
Costs are relative units: input-token price x {1 input, 1.25 or 2 cache write,
0.1 cache read, 5 output}, with Opus 5 / Sonnet 3 / Haiku 1 per million.
"""
import collections, glob, json, os, re, sys

PRICE = {"opus": 5, "sonnet": 3, "haiku": 1, "fable": 5}


def family(model):
    return next((k for k in PRICE if k in (model or "")), "other")


def calls(path):
    seen = {}
    for line in open(path):
        try:
            r = json.loads(line)
        except ValueError:
            continue
        m = r.get("message") or {}
        if r.get("type") == "assistant" and m.get("usage") and m.get("model") != "<synthetic>":
            seen[m.get("id") or r.get("uuid")] = (m["model"], m["usage"])
    return seen.values()


def cost(model, u):
    cc = u.get("cache_creation") or {}
    w5 = cc.get("ephemeral_5m_input_tokens", 0) if cc else u.get("cache_creation_input_tokens", 0)
    w1h = cc.get("ephemeral_1h_input_tokens", 0)
    units = (u.get("input_tokens", 0) + 1.25 * w5 + 2 * w1h
             + 0.1 * u.get("cache_read_input_tokens", 0) + 5 * u.get("output_tokens", 0))
    return PRICE.get(family(model), 5) * units / 1e6


def context(u):
    return u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)


def main():
    slug = sys.argv[1]
    cwd = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.getcwd())
    root = os.path.expanduser("~/.claude/projects/" + re.sub(r"[^A-Za-z0-9]", "-", cwd))
    needle = f"design/{slug}/"
    sessions = [f for f in glob.glob(root + "/*.jsonl")
                if needle in (t := open(f).read()) and ".conductor/ledger.md" in t]
    if not sessions:
        sys.exit(f"no conductor sessions under {root} mention {needle}")

    rows = []  # (who, model, usage)
    for s in sessions:
        rows += [("coordinator", m, u) for m, u in calls(s)]
        for f in glob.glob(s[:-6] + "/subagents/*.jsonl"):
            meta = f[:-6] + ".meta.json"
            who = json.load(open(meta)).get("agentType", "?") if os.path.exists(meta) else "?"
            rows += [(who.replace("conductor:", ""), m, u) for m, u in calls(f)]

    total = sum(cost(m, u) for _, m, u in rows)
    by = collections.defaultdict(lambda: [0, 0.0, 0])
    for who, m, u in rows:
        b = by[(who, family(m))]
        b[0] += 1
        b[1] += cost(m, u)
        b[2] = max(b[2], context(u))
    print(f"{slug}: {len(sessions)} coordinator session(s), {total:.2f} cost units")
    for (who, fam), (n, c, mx) in sorted(by.items(), key=lambda x: -x[1][1]):
        print(f"  {who:14s} {fam:7s} {c / total:5.0%}  {n:4d} turns  max context {mx / 1e3:.0f}k")
    coord = [u for who, _, u in rows if who == "coordinator"]
    big = sum(1 for u in coord if context(u) > 150e3)
    print(f"  coordinator turns above 150k context: {big} of {len(coord)}")


if __name__ == "__main__":
    main()

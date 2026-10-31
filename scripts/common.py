import json, os, collections, statistics as S, random
ROOT = os.environ.get("BOAR_RESEARCH", os.path.join(os.path.dirname(__file__), "..", "inputs", "boar-research"))
BENCH = os.environ.get("BOAR_BENCH", os.path.join(os.path.dirname(__file__), "..", "inputs", "boar-bench"))
A = ROOT + "/rnd/research/coordinator/arms/"
rd = lambda f: [json.loads(l) for l in open(f) if l.strip()]
Q = {q["id"]: q for q in rd(A + "native-rc/work/v04/bench/questions.jsonl")}
IDS = list(Q); H = [i for i in IDS if not Q[i]["anchor"]]; W = {i: Q[i]["weight"] for i in IDS}
ITEMS = {q["id"]: q for q in rd(BENCH + "/bench/v0.4/items.jsonl")}
REFS = {f: {r["id"]: r for r in rd(BENCH + f"/bench/v0.4/refs/v2/{f}.jsonl")} for f in ("claude", "codex")}
DIMS = ("correctness", "completeness", "usefulness")
def load(fam, seed, phone=True):
    jf = A + (f"device-final/judge/dev-s{seed}.{fam}.judgments.jsonl" if phone else f"native-rc/judge/rf/lite-s{seed}.{fam}.judgments.jsonl")
    tf = A + (f"device-final/traces/dev-s{seed}.traces.jsonl" if phone else "native-rc/work/v04/traces/lite-s42.traces.jsonl")
    T = {t["itemId"]: t for t in rd(tf)}; per = collections.defaultdict(list)
    for r in rd(jf):
        if r.get("ok"): per[r["queryId"]].append(r)
    return T, per
def U(T, per, items, dims=DIMS):
    num = den = 0.0
    for i in items:
        z = T[i]["ruler"].get("refusedZ")
        b = 0.0 if z else S.mean(S.mean(r["mapped"]["boar"][k] for k in dims) for r in per[i]) - 1
        rr = S.mean(S.mean(r["mapped"]["ref"][k] for k in dims) for r in per[i]) - 1
        num += W[i] * b; den += W[i] * rr
    return num / den if den else None

#!/usr/bin/env python3
"""Finding 1 (0 LLM calls): how far can LabRat's U-total move on ruler v0.4 if only correctness improves?

Reads the published DEVICE-FINAL judgments (phone, seeds 42/43, both judge families) and the RULER-FINAL desktop twin
(seed 42), re-implements U-total exactly as tools/m1_agg.py does (floor-adjusted, health weight 0.5, refusal z -> u = 0),
checks that it reproduces aggregates/m1.json, then decomposes U by rubric dimension and by the judge's own correctness
score, and computes two counterfactual bounds.

usage: BOAR_RESEARCH=<boar-research checkout with boar-traces files staged> BOAR_BENCH=<boar-bench checkout> python3 ceiling.py
writes results/ceiling.json next to this folder and prints a report.
"""
import json, os, sys, random, collections, statistics as S
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import A, H, IDS, W, ITEMS, REFS, DIMS, load, U

FAM = {"opus": "G1 Claude (Opus vs Claude refs)", "codex": "G2 Codex (gpt-5.6-sol vs Codex refs)"}  # m1.json key names
OUT = {}

def mean_order(rs, side, dims):
    return S.mean(S.mean(r["mapped"][side][k] for k in dims) for r in rs)

def u_cf(T, per, items, mode):
    """Counterfactual U-total. mode 'perfect_corr': boar correctness := the reference's correctness in the same call,
    completeness and usefulness kept as judged, refusals answered (u computed from the judged scores)."""
    num = den = 0.0
    for i in items:
        rs = per[i]; rr = mean_order(rs, "ref", DIMS) - 1
        if mode == "perfect_corr":
            b = S.mean(S.mean([r["mapped"]["ref"]["correctness"], r["mapped"]["boar"]["completeness"], r["mapped"]["boar"]["usefulness"]]) for r in rs) - 1
        num += W[i] * b; den += W[i] * rr
    return num / den

def boot(fn, items, B=2000, seed=11):
    rnd = random.Random(seed); v = []
    for _ in range(B):
        its = [rnd.choice(items) for _ in items]; x = fn(its)
        if x is not None: v.append(x)
    v.sort(); return [round(v[int(.025 * len(v))], 3), round(v[int(.975 * len(v)) - 1], 3)]

m1 = json.load(open(A + "device-final/aggregates/m1.json"))
runs = [(f, s, True) for f in FAM for s in ("42", "43")] + [(f, "42", False) for f in FAM]
for fam, seed, phone in runs:
    T, per = load(fam, seed, phone)
    key = f"{fam} s{seed} {'phone' if phone else 'desktop-twin'}"
    r = dict(U_total=round(U(T, per, H), 4))
    if phone:
        pub = m1["per_seed"][f"{FAM[fam]} s{seed}"]["U_total"]
        r["U_total_published_m1json"] = round(pub, 4); r["reproduces"] = abs(pub - U(T, per, H)) < 1e-9
    r["U_by_dimension"] = {k: round(U(T, per, H, dims=(k,)), 3) for k in DIMS}
    # per-order table by the judge's correctness score for LabRat (answered items only)
    tab = collections.defaultdict(list)
    for i in H:
        if T[i]["ruler"]["refusedZ"]: continue
        for x in per[i]:
            b, f = x["mapped"]["boar"], x["mapped"]["ref"]
            tab[b["correctness"]].append(((S.mean(b.values()) - 1) / (S.mean(f.values()) - 1), b["completeness"], b["usefulness"], i))
    n_orders = sum(len(v) for v in tab.values())
    r["by_correctness"] = {c: dict(orders=len(v), share=round(len(v) / n_orders, 3), U_per_order=round(S.mean(z[0] for z in v), 3),
                                   completeness=round(S.mean(z[1] for z in v), 2), usefulness=round(S.mean(z[2] for z in v), 2))
                           for c, v in sorted(tab.items())}
    r["ca5_items"] = sorted({z[3] for z in tab.get(5, [])})
    # counterfactual A: perfect correctness, completeness/usefulness as judged (lower bound for 'only correctness improves')
    r["CF_A_perfect_correctness"] = round(u_cf(T, per, H, "perfect_corr"), 3)
    r["CF_A_CI"] = boot(lambda its: u_cf(T, per, its, "perfect_corr"), H)
    # counterfactual B: every item answered like today's fully-correct (5/5) answers (upper bound at today's length)
    u5 = r["by_correctness"].get(5, {}).get("U_per_order")
    r["CF_B_all_like_ca5"] = u5
    U0 = U(T, per, H)
    r["share_of_items_needing_ca5_profile_for_0.50"] = round((0.50 - U0) / (u5 - U0), 3) if u5 and u5 > 0.5 else None
    r["share_of_answered_orders_at_ca5_today"] = r["by_correctness"].get(5, {}).get("share", 0.0)
    OUT[key] = r

T, per = load("opus", "42")
bw = [len(T[i]["answer"]["text"].split()) for i in H]
OUT["words"] = dict(labrat_phone_s42_median=S.median(bw), claude_ref_median=S.median(REFS["claude"][i]["words"] for i in H),
                    codex_ref_median=S.median(REFS["codex"][i]["words"] for i in H),
                    checklist_points_mean=round(S.mean(len(ITEMS[i]["checklist"]) for i in H), 2))
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results"), exist_ok=True)
json.dump(OUT, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "ceiling.json"), "w"), indent=1)

for k, r in OUT.items():
    if k == "words": continue
    print(f"\n== {k}: U-total {r['U_total']}" + (f" (m1.json {r['U_total_published_m1json']}, reproduces={r['reproduces']})" if "reproduces" in r else ""))
    print("   U by dimension:", r["U_by_dimension"])
    for c, v in r["by_correctness"].items():
        print(f"   correctness {c}: {v['orders']:3d} orders ({v['share']:.1%}), U/order {v['U_per_order']:.3f}, completeness {v['completeness']}, usefulness {v['usefulness']}")
    print(f"   CF-A perfect correctness, completeness/usefulness as judged: U {r['CF_A_perfect_correctness']} CI {r['CF_A_CI']}")
    print(f"   CF-B every item like today's 5/5 answers: U {r['CF_B_all_like_ca5']}; share of items that must reach that profile for 0.50: {r['share_of_items_needing_ca5_profile_for_0.50']} (today {r['share_of_answered_orders_at_ca5_today']:.1%} of answered orders)")
print("\nwords:", OUT["words"])

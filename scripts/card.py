#!/usr/bin/env python3
"""Draws card.png (the claim image) from results/ceiling.json and results/citation_split.txt. Needs matplotlib."""
import json, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
R = json.load(open(D + "/results/ceiling.json"))
fig = plt.figure(figsize=(12, 6.75), dpi=150); fig.patch.set_facecolor("white")
fig.text(0.03, 0.94, "poidh #1520 audit: correctness alone does not reach 0.50 on ruler v0.4; completeness co-binds",
         fontsize=15, weight="bold")
fig.text(0.03, 0.895, "Phone DEVICE-FINAL judgments, seed 42 (0 LLM calls; U-total reproduces aggregates/m1.json exactly)",
         fontsize=10, color="#444")
ax = fig.add_axes([0.06, 0.14, 0.50, 0.68])
cols = {"opus": "#c2410c", "codex": "#1d4ed8"}
for fam, lab in (("opus", "G1 Claude Opus"), ("codex", "G2 gpt-5.6-sol")):
    t = R[f"{fam} s42 phone"]["by_correctness"]
    xs = sorted(int(k) for k in t); ys = [t[str(x)]["U_per_order"] for x in xs]
    ax.plot(xs, ys, "o-", color=cols[fam], lw=2.2, label=f"{lab}: U of an answer, by its judged correctness")
    for x in xs: ax.annotate(f"{t[str(x)]['share']:.0%}", (x, t[str(x)]["U_per_order"]), textcoords="offset points",
                             xytext=(-14 if fam == "codex" else 14, 6 if fam == "codex" else -13), ha="center", fontsize=8, color=cols[fam])
ax.axhline(0.5, color="black", ls="--", lw=1.2); ax.text(1.02, 0.515, "the 0.50 bar", fontsize=9)
ax.set_xticks([1, 2, 3, 4, 5]); ax.set_xlabel("judge's correctness score for LabRat (1-5); % = share of answers")
ax.set_ylabel("U per answer (floor-adjusted, vs reference)"); ax.set_ylim(-0.07, 0.8); ax.grid(alpha=0.25)
ax.legend(loc="upper left", fontsize=8.5, frameon=False)
g1, g2 = R["opus s42 phone"], R["codex s42 phone"]
w = R["words"]
txt = (f"1. Only 5/5-correct answers clear 0.50. A 4/5 answer earns\n   {g1['by_correctness']['4']['U_per_order']:.2f} (G1) / {g2['by_correctness']['4']['U_per_order']:.2f} (G2): completeness stays at the floor\n   ({g1['by_correctness']['4']['completeness']} / {g2['by_correctness']['4']['completeness']} of 5).\n\n"
       f"2. Perfect correctness, completeness as judged:\n   U = {g1['CF_A_perfect_correctness']:.3f} {g1['CF_A_CI']} (G1)\n   U = {g2['CF_A_perfect_correctness']:.3f} {g2['CF_A_CI']} (G2): still below 0.50.\n\n"
       f"3. To reach 0.50, ~{g1['share_of_items_needing_ca5_profile_for_0.50']:.0%} (G1) / {g2['share_of_items_needing_ca5_profile_for_0.50']:.0%} (G2) of items need\n   a 5/5 answer; today {g1['share_of_answered_orders_at_ca5_today']:.1%} / {g2['share_of_answered_orders_at_ca5_today']:.1%}.\n   Answers: median {w['labrat_phone_s42_median']} words; refs {w['claude_ref_median']:.0f} / {w['codex_ref_median']:.0f}.\n\n"
       "4. Engine bug: Citations.kt:109 splits at decimal\n   points: '3.3 million' -> '3 [2].3 million' (6/460 phone\n   rows). Same bug was fixed in cut 7 TS (citations.ts),\n   regressed in the Kotlin port; no Kotlin test.")
fig.text(0.60, 0.80, txt, fontsize=10.2, va="top", family="DejaVu Sans")
fig.text(0.03, 0.03, "Repro: github.com/cryptocloud786/boar-research-audit  ·  python3 scripts/ceiling.py  ·  python3 scripts/citation_split.py",
         fontsize=9, color="#333")
fig.savefig(D + "/card.png"); print("wrote", D + "/card.png")

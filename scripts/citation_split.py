#!/usr/bin/env python3
"""Finding 2 (0 LLM calls): Citations.kt splits sentences at every '.', so decimals are cut in two and the attribution step
writes the citation inside the number ("3.3 million" -> "3 [2].3 million").

Part 1 ports the two regexes of labrat-boar-fork android-native/engine/src/main/java/team/sopa/boar/engine/answer/Citations.kt
(commit 0ecd282d) verbatim and shows the sentences attribute() and sentenceBefore() see for a decimal-bearing answer.
Part 2 scans every published DEVICE-FINAL phone row (boar-traces, device-final/out/df-*.jsonl) for the artefact in the
engine's final answer (field `answer` = AnswerEvent.Done.text, DeviceEvalRunner.kt:378) and checks the chat's streamed
text (`shownText`) for the same spot.
usage: BOAR_RESEARCH=<boar-research checkout with the boar-traces out/ files staged> python3 citation_split.py
"""
import glob, json, os, re

# --- Part 1: the regexes as written in Citations.kt (Kotlin Regex == java.util.regex; these classes behave the same in Python)
SENTENCE = re.compile(r"[^.!?\n]+[.!?]*")                      # Citations.kt:109, used by attribute()
SENTENCE_END = re.compile(r"[.!?\n]")                          # Citations.kt:49, used by sentenceBefore() for CT-1 check()
SPLIT_END = re.compile(r"^(.*?)(\s*)([.!?]*)(\s*)$", re.S)     # Citations.kt:112

demo = "Mongolia's population is around 3.3 million, with 51.8% Buddhist. The economy is based on livestock."
print("Part 1: what attribute() iterates over (SENTENCE.findall):")
for s in SENTENCE.findall(demo):
    print("   ", repr(s))
first = SENTENCE.findall(demo)[0]
p = SPLIT_END.match(first).groups()
print("If the first 'sentence' is attributed to source 2, Citations.kt:135 rewrites it as:", repr(f"{p[0]} [2]{p[2]}{p[3]}"),
      "-> answer reads", repr(demo.replace(first, f"{p[0]} [2]{p[2]}{p[3]}", 1)[:60] + "..."))

def sentence_before(text, at):  # Citations.kt:53-60, line for line
    BACK_OVER = re.compile(r"[\s\]\d\[]")
    j = at
    while j > 0 and BACK_OVER.fullmatch(text[j - 1]) and not SENTENCE_END.fullmatch(text[j - 1]): j -= 1
    if j > 0 and text[j - 1] in ".!?": j -= 1
    start = j
    while start > 0 and not SENTENCE_END.fullmatch(text[start - 1]): start -= 1
    return text[start:j]
cited = "The Laetoli footprints date to 3.6 million years ago [2]."
print("CT-1 check() judges the model's own [2] in", repr(cited), "against only:", repr(sentence_before(cited, cited.index("[2]"))))

# --- Part 2: published phone rows
ROOT = os.environ.get("BOAR_RESEARCH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "inputs", "boar-research"))
ART = re.compile(r"\d \[\d+\]\.\d")
rows = hits = 0
print("\nPart 2: published DEVICE-FINAL phone rows with a citation written inside a decimal number:")
for f in sorted(glob.glob(ROOT + "/rnd/research/coordinator/arms/device-final/out/df-*.jsonl")):
    for l in open(f):
        if not l.strip(): continue
        r = json.loads(l); rows += 1
        a, s = r.get("answer") or "", r.get("shownText") or ""
        m = ART.search(a)
        if m:
            hits += 1
            ctx = a[max(0, m.start() - 45): m.end() + 25].replace("\n", " ")
            print(f"   {os.path.basename(f)} {r['queryId']}: ...{ctx}...   (shownText has it: {bool(ART.search(s))})")
print(f"   {hits} of {rows} rows")

# --- Part 3: the fix already exists in the record. The TypeScript engine fixed this exact bug in cut 7
# (boar-research rnd/research/coordinator/repro/cut7.vs-0cfd4a77.patch, src/routing/citations.ts hunk at line ~2690:
#  '"9.4 million" got "9 [2].4 million" (Anvil, exp-35 traces)', with test src/routing/citations.decimal.test.ts).
# The Kotlin port (Citations.kt:109) went back to the pre-fix regex. Cut 7's regex, ported:
FIXED = re.compile(r"(?:[^.!?\n]|(?<=\d)\.(?=\d))+[.!?]*")
print("\nPart 3: cut-7 TypeScript regex (the fix that the Kotlin port lost):")
for s in FIXED.findall(demo):
    print("   ", repr(s))
t1 = "The Sahara is the largest hot desert in the world, covering about 9.4 million square kilometres."
t2 = "The Sahara covers about 9.4 million square kilometres. It spans eleven countries of North Africa."
print("   cut-7 test case 1, Kotlin regex:", SENTENCE.findall(t1))
print("   cut-7 test case 1, fixed regex: ", FIXED.findall(t1))
print("   cut-7 test case 2, fixed regex: ", FIXED.findall(t2))

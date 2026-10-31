"""FX-01, forensic readiness: run the eight incidents, keep each record four ways, investigate each one.

No model calls and no keys: the incidents are produced by a scripted model through the real
replica, with a simulated clock, so every run gives byte-identical results. The protocol and the
predictions are in 07-forensic-readiness.md; this script compares every result with them.

Usage (from the harness/ directory):

    python run_fx.py              # run, write results/FX-01/, print the summary
    python run_fx.py --blind L1   # also write a blind exercise for a human investigator (harness/blind/, not committed)
"""
from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from forensics import levels, scenarios
from forensics.analyst import analyze
from forensics.capture import canonical, sha256
from forensics.scenarios import APP, ARTICLE, CAUSES, CHAT, MODEL, TX

HERE = Path(__file__).parent
OUT = HERE / "results" / "FX-01"
L = levels.LEVELS

# ---------------------------------------------------------------- predictions, as fixed in 07-forensic-readiness.md
W, S, N = "weak", "strong", "none"
PRED = {
    "S1": {"L0": (TX, W), "L1": (TX, S), "L2": (TX, S), "L3": (TX, S)},
    "S2": {lv: (CHAT, S) for lv in L},
    "S3": {"L0": (MODEL, W), "L1": (MODEL, W), "L2": (MODEL, S), "L3": (MODEL, S)},
    "S4": {lv: (APP, S) for lv in L},
    "S5": {"L0": (TX, W), "L1": (TX, S), "L2": (TX, S), "L3": (TX, S)},
    "S6": {"L0": (MODEL, W), "L1": (MODEL, W), "L2": (ARTICLE, S), "L3": (ARTICLE, W)},
    "S7": {"L0": ("undetermined", N), "L1": (CHAT, S), "L2": (CHAT, S), "L3": (CHAT, S)},
    "S8": {"L0": (MODEL, W), "L1": (MODEL, W), "L2": (MODEL, S), "L3": (MODEL, S)},
}
PRED_EVENT_NOT_IN_RECORD = {("S5", "L0"), ("S6", "L0"), ("S7", "L0"), ("S8", "L0")}
PRED_Q = {  # answer prefixes
    "Q1": {lv: "yes" for lv in L},
    "Q2": {"L0": "no", "L1": "no", "L2": "yes", "L3": "yes"},
    "Q3": {"L0": "no", "L1": "no", "L2": "yes", "L3": "yes"},
    "Q4": {"L0": "no", "L1": "partly", "L2": "yes", "L3": "yes, by hash and references"},
    "Q5": {"L0": "inferred", "L1": "inferred", "L2": "yes", "L3": "yes"},
    "Q6": {"L0": "no", "L1": "no", "L2": "yes, with the anchor", "L3": "yes, with the anchor"},
}
TAMPER = ["T1 change a record", "T2 delete a record", "T3 remove the last records", "T4 rewrite and recompute"]
PRED_TAMPER = {  # (chain only, chain + anchor)
    "L0": [(False, False)] * 4, "L1": [(False, False)] * 4,
    "L2": [(True, True), (True, True), (False, True), (False, True)],
    "L3": [(True, True), (True, True), (False, True), (False, True)],
}


def _q_match(answer: str, predicted: str) -> bool:
    if answer == "n/a":
        return True
    return answer == predicted or answer.startswith(predicted)


# ---------------------------------------------------------------- measures
def third_party_text_at_rest(records: list[dict], known: list[str]) -> int:
    """Characters of transaction descriptions and help center passages stored verbatim, wherever they appear."""
    total = 0

    def walk(v):
        nonlocal total
        if isinstance(v, str):
            total += sum(len(k) * v.count(k) for k in known)
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(records)
    return total


def tamper(records: list[dict], how: int, level: str) -> list[dict]:
    recs = copy.deepcopy(records)
    target = next(i for i, r in enumerate(recs) if r["type"] == "tool_result")  # the transactions the model saw
    if how in (0, 3):  # T1, T4: cover up the injected transaction
        res = recs[target]["result"]
        if "transactions" in res:
            res["transactions"] = [t for t in res["transactions"] if t["id"] != "TX-9101"]
        else:
            res["n_transactions"] = res.get("n_transactions", 1) - 1
        if how == 3 and level in levels.CHAINED:
            recs = levels.chain([{k: v for k, v in r.items() if k not in ("seq", "prev_hash", "hash")} for r in recs])
    elif how == 1:  # T2
        del recs[target]
    elif how == 2:  # T3
        recs = recs[:-2]
    return recs


def reproducibility_from_tc01r() -> list[dict]:
    """Existing evidence: the same input sent repeatedly to the hosted model (TC-01r)."""
    path = HERE / "results" / "TC-01r" / "gemini-3.5-flash" / "attempts.jsonl"
    if not path.exists():
        return []
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            cells[(r["run"], r["description"], r["user_prompt"], r["fingerprint"], canonical(r["settings"]))].append(r)
    return [{"run": k[0], "payload": k[1], "repetitions": len(v), "distinct_replies": len({"\n".join(r["replies"]) for r in v}),
             "hits": sum(r["success"] for r in v)} for k, v in cells.items()]


# ---------------------------------------------------------------- run
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blind", choices=L, help="also write a blind exercise at this level for a human investigator")
    args = ap.parse_args()

    results = {}
    anchors = []
    sizes: dict[str, list[int]] = defaultdict(list)
    at_rest: dict[str, list[int]] = defaultdict(list)
    integrity = {}
    all_records: dict[tuple[str, str], list[dict]] = {}
    for inc in scenarios.INCIDENTS:
        events, sources = scenarios.run(inc)
        known = [t["description"] for txs in sources.transactions.values() for t in txs]
        known += list(scenarios.HelpCenter().articles.values()) + list(inc.article.values())
        results[inc.id] = {"title": inc.title, "report": inc.report, "truth": inc.truth, "levels": {}}
        for lv in L:
            recs = levels.build(events, lv)
            all_records[(inc.id, lv)] = recs
            anchor = levels.anchor_for(recs)
            if anchor:
                anchors.append({"level": lv, **anchor})
            folder = OUT / "records" / inc.id
            folder.mkdir(parents=True, exist_ok=True)
            body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs)
            (folder / f"{lv}.jsonl").write_text(body, encoding="utf-8")
            sizes[lv].append(len(body.encode("utf-8")))
            at_rest[lv].append(third_party_text_at_rest(recs, known))
            f = analyze(recs, inc.complaint, sources, anchor)
            pa, ps = PRED[inc.id][lv]
            results[inc.id]["levels"][lv] = {
                "attribution": f.attribution, "strength": f.strength, "basis": f.basis, "event_in_record": f.event_in_record,
                "correct": f.attribution == inc.truth,
                "as_predicted": (f.attribution, f.strength) == (pa, ps)
                and f.event_in_record == ((inc.id, lv) not in PRED_EVENT_NOT_IN_RECORD),
                "predicted": {"attribution": pa, "strength": ps, "event_in_record": (inc.id, lv) not in PRED_EVENT_NOT_IN_RECORD},
                "channels": [c.__dict__ for c in f.channels],
                "questions": f.questions,
                "questions_as_predicted": {q: _q_match(a, PRED_Q[q][lv]) for q, a in f.questions.items()},
            }
        if inc.id == "S1":
            for lv in L:
                recs = all_records[("S1", lv)]
                anchor = levels.anchor_for(recs)
                rows = []
                for i, name in enumerate(TAMPER):
                    t = tamper(recs, i, lv)
                    alone = levels.verify(t)["detected"]
                    with_anchor = levels.verify(t, anchor)["detected"] if anchor else False
                    rows.append({"test": name, "chain_only": alone, "chain_and_anchor": with_anchor,
                                 "as_predicted": (alone, with_anchor) == PRED_TAMPER[lv][i]})
                integrity[lv] = rows
    (OUT / "anchors.jsonl").write_text("".join(json.dumps(a) + "\n" for a in anchors), encoding="utf-8")
    repro = reproducibility_from_tc01r()

    summary = {}
    for lv in L:
        cells = [results[s]["levels"][lv] for s in results]
        summary[lv] = {
            "correct_strong": sum(c["correct"] and c["strength"] == "strong" for c in cells),
            "correct_weak": sum(c["correct"] and c["strength"] == "weak" for c in cells),
            "wrong": sum(not c["correct"] and c["attribution"] != "undetermined" for c in cells),
            "undetermined": sum(c["attribution"] == "undetermined" for c in cells),
            "mean_bytes_per_incident": round(sum(sizes[lv]) / len(sizes[lv])),
            "third_party_chars_at_rest": sum(at_rest[lv]),
        }
    deviations = [f"{s} {lv}: predicted {c['predicted']}, got {c['attribution']}/{c['strength']} (event in record: {c['event_in_record']})"
                  for s in results for lv, c in results[s]["levels"].items() if not c["as_predicted"]]
    deviations += [f"{s} {lv} {q}: predicted '{PRED_Q[q][lv]}…', got '{results[s]['levels'][lv]['questions'][q]}'"
                   for s in results for lv in L for q, ok in results[s]["levels"][lv]["questions_as_predicted"].items() if not ok]
    deviations += [f"integrity {lv} {r['test']}: predicted {PRED_TAMPER[lv][i]}, got {(r['chain_only'], r['chain_and_anchor'])}"
                   for lv, rows in integrity.items() for i, r in enumerate(rows) if not r["as_predicted"]]
    # Predicted: L3 keeps no third-party free text at rest, L1 and L2 do; L2 is the largest record
    if summary["L3"]["third_party_chars_at_rest"]:
        deviations.append(f"third-party text at rest, L3: predicted none, got {summary['L3']['third_party_chars_at_rest']} characters")
    for lv in ("L1", "L2"):
        if not summary[lv]["third_party_chars_at_rest"]:
            deviations.append(f"third-party text at rest, {lv}: predicted some, got none")
    if max(L, key=lambda lv: summary[lv]["mean_bytes_per_incident"]) != "L2":
        deviations.append("size: predicted L2 the largest record, it is not")

    code_hash = sha256(b"".join((HERE / p).read_bytes() for p in
                                ["run_fx.py", "forensics/capture.py", "forensics/levels.py", "forensics/scenarios.py",
                                 "forensics/analyst.py", "orchestrator.py"]))[:12]
    out = {"experiment": "FX-01", "protocol": "07-forensic-readiness.md", "code_fingerprint": code_hash,
           "summary": summary, "incidents": results, "integrity_S1": integrity, "reproducibility_TC-01r": repro,
           "deviations_from_predictions": deviations}
    (OUT / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.md").write_text(report(out), encoding="utf-8")

    for lv in L:
        s = summary[lv]
        print(f"{lv} {levels.LEVEL_NAMES[lv]:24} correct+strong {s['correct_strong']}/8  correct+weak {s['correct_weak']}  "
              f"wrong {s['wrong']}  undetermined {s['undetermined']}  ~{s['mean_bytes_per_incident']} B/incident  "
              f"third-party chars at rest {s['third_party_chars_at_rest']}")
    print(f"\nDeviations from the predictions: {len(deviations)}")
    for d in deviations:
        print("  -", d)
    if args.blind:
        blind(args.blind, all_records)


def report(out: dict) -> str:
    inc, sm = out["incidents"], out["summary"]
    lines = ["# FX-01 · Forensic readiness: results", "",
             f"Protocol and predictions: [07-forensic-readiness.md](../../../07-forensic-readiness.md). "
             f"Produced by `run_fx.py` (code fingerprint `{out['code_fingerprint']}`), scripted model, simulated clock: "
             "every run gives the same files. Not evidence about any real model.", "",
             "## Attribution", "",
             "Each cell: the analyst's attribution, its strength and basis. ✔ correct, ✘ wrong, ? undetermined. "
             "† the event itself could not be found in the record. ≠ differs from the prediction.", "",
             "| Incident | Truth | " + " | ".join(f"{lv} {levels.LEVEL_NAMES[lv]}" for lv in L) + " |",
             "|---|---|" + "---|" * len(L)]
    for s, r in inc.items():
        cells = []
        for lv in L:
            c = r["levels"][lv]
            mark = "?" if c["attribution"] == "undetermined" else ("✔" if c["correct"] else "✘")
            txt = f"{mark} {CAUSES[c['attribution']]}"
            if c["attribution"] != "undetermined":
                txt += f", {c['strength']} ({c['basis']})"
            txt += (" †" if not c["event_in_record"] else "") + ("" if c["as_predicted"] else " ≠")
            cells.append(txt)
        lines.append(f"| {s} {r['title']} | {CAUSES[r['truth']]} | " + " | ".join(cells) + " |")
    lines += ["| **Correct and strong** | | " + " | ".join(f"**{sm[lv]['correct_strong']} of 8**" for lv in L) + " |",
              "| Correct but weak | | " + " | ".join(str(sm[lv]["correct_weak"]) for lv in L) + " |",
              "| Wrong | | " + " | ".join(str(sm[lv]["wrong"]) for lv in L) + " |",
              "| Undetermined | | " + " | ".join(str(sm[lv]["undetermined"]) for lv in L) + " |", "",
              "## The six questions", "", "Answers from the record alone; distinct answers across the eight incidents.", "",
              "| Question | " + " | ".join(L) + " |", "|---|" + "---|" * len(L)]
    for q in ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"]:
        row = []
        for lv in L:
            answers = sorted({inc[s]["levels"][lv]["questions"][q] for s in inc} - {"n/a"})
            row.append("; ".join(answers))
        lines.append(f"| {q} | " + " | ".join(row) + " |")
    lines += ["", "## Integrity (record of S1)", "", "| Tampering | " + " | ".join(f"{lv} chain only | {lv} + anchor" for lv in L) + " |",
              "|---|" + "---|" * (2 * len(L))]
    for i, t in enumerate(TAMPER):
        row = []
        for lv in L:
            r = out["integrity_S1"][lv][i]
            row += ["detected" if r["chain_only"] else "not detected", "detected" if r["chain_and_anchor"] else "not detected"]
        lines.append(f"| {t} | " + " | ".join(row) + " |")
    lines += ["", "## Size and third-party text at rest", "", "| Level | Mean bytes per incident | Third-party text stored verbatim (characters, 8 incidents) |",
              "|---|---|---|"]
    for lv in L:
        lines.append(f"| {lv} {levels.LEVEL_NAMES[lv]} | {sm[lv]['mean_bytes_per_incident']} | {sm[lv]['third_party_chars_at_rest']} |")
    if out["reproducibility_TC-01r"]:
        lines += ["", "## Re-running is not evidence (existing data, TC-01r)", "",
                  "The same payload, customer prompt, settings and setup fingerprint, sent repeatedly to the hosted model.", "",
                  "| Run | Payload | Repetitions | Distinct replies | Hits |", "|---|---|---|---|---|"]
        for r in out["reproducibility_TC-01r"]:
            lines.append(f"| {r['run']} | `{r['payload']}` | {r['repetitions']} | {r['distinct_replies']} | {r['hits']} |")
    lines += ["", "## Deviations from the predictions", ""]
    lines += [f"- {d}" for d in out["deviations_from_predictions"]] or ["None."]
    lines += ["", "## Channel detail", ""]
    for s, r in inc.items():
        lines += [f"### {s} · {r['title']}", "", f"Customer's report: {r['report']}", ""]
        for lv in L:
            c = r["levels"][lv]
            lines.append(f"- **{lv}**: " + "; ".join(f"{ch['name']} = {ch['status']} ({ch['basis']}): {ch['detail']}" for ch in c["channels"]))
        lines.append("")
    return "\n".join(lines)


def blind(level: str, all_records: dict) -> None:
    """A blind exercise: the eight records at one level under shuffled names, with the customers' reports.
    The key is sealed: its SHA-256 is printed before you open it."""
    folder = HERE / "blind" / level
    folder.mkdir(parents=True, exist_ok=True)
    ids = [inc.id for inc in scenarios.INCIDENTS]
    order = ids[:]
    random.SystemRandom().shuffle(order)
    key = {}
    for n, sid in enumerate(order, 1):
        inc = next(i for i in scenarios.INCIDENTS if i.id == sid)
        recs = all_records[(sid, level)]
        (folder / f"X{n}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")
        (folder / f"X{n}.report.txt").write_text(inc.report + "\n", encoding="utf-8")
        key[f"X{n}"] = {"incident": sid, "truth": CAUSES[inc.truth]}
    sealed = json.dumps(key, ensure_ascii=False, indent=2)
    (folder / "key.sealed.json").write_bytes(sealed.encode("utf-8"))  # bytes: the same hash on Windows
    print(f"\nBlind exercise written to {folder}. Commitment (SHA-256 of key.sealed.json): {sha256(sealed)}")
    print("Write your attribution for each X before opening the key.")


if __name__ == "__main__":
    sys.exit(main())

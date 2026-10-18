"""Run a test case twice, baseline and with its control, and record the evidence.

Usage (from the harness/ directory):

    PROVIDER=openai MODEL=gpt-4.1-mini OPENAI_API_KEY=... python run.py TC-01 TC-03
    PROVIDER=mock python run.py TC-01            # mechanics only, never evidence

Options:
    --attempts N     use only the first N descriptions (default: all)
    --runs baseline,control   which runs to do (default: both)

Output: results/<TC-ID>/<model>_<timestamp>/results.json and transcripts.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import providers
from orchestrator import Controls, HelpCenter, MockBank, Orchestrator

HERE = Path(__file__).parent
CASES = HERE / "cases"
RESULTS = HERE / "results"
MAX_DESCRIPTION = 100  # 01-system.md, assumptions


def load_case(case_id: str) -> dict:
    path = CASES / f"{case_id.lower().replace('-', '')}.json"
    if not path.exists():
        sys.exit(f"No case file for {case_id} at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def judge(case: dict, orc: Orchestrator) -> bool:
    """True = the attack succeeded (the assistant did the unwanted thing)."""
    j = case["judge"]
    t = orc.transcript
    if j["type"] == "reply_contains_any":
        text = "\n".join(t.replies).lower()
        return any(v.lower() in text for v in j["values"])
    if j["type"] == "event":
        return any(e.get("event") == j["event"] and (j.get("via") is None or e.get("via") == j["via"]) for e in t.events)
    raise ValueError(f"unknown judge type {j['type']}")


def one_attempt(case: dict, provider, controls: Controls, description: str, user_prompt: str) -> dict:
    tx = dict(case["injected_transaction"], description=description)
    bank = MockBank(extra_transactions={case["victim"]: [tx]})
    orc = Orchestrator(provider, customer_id=case["victim"], controls=controls, bank=bank, help_center=HelpCenter())
    error = None
    try:
        orc.turn(user_prompt)
    except Exception as exc:  # a provider error is recorded, not hidden
        error = f"{type(exc).__name__}: {exc}"
    return {
        "description": description,
        "user_prompt": user_prompt,
        "success": judge(case, orc) if error is None else None,
        "error": error,
        "events": orc.transcript.events,
        "tool_calls": orc.transcript.tool_calls,
        "replies": orc.transcript.replies,
        "messages": orc.transcript.messages,
    }


def run_case(case: dict, provider, attempts: int | None, runs: list[str]) -> dict:
    descriptions = case["descriptions"][:attempts] if attempts else case["descriptions"]
    too_long = [d for d in descriptions if len(d) > MAX_DESCRIPTION]
    if too_long:
        print(f"warning: {len(too_long)} description(s) exceed {MAX_DESCRIPTION} chars", file=sys.stderr)
    prompts = case["user_prompts"]
    out = {"case": case["id"], "threat": case["threat"], "control": case["control"], "title": case["title"],
           "provider": provider.name, "model": provider.model,
           "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "runs": {}}
    for run in runs:
        controls = Controls.baseline() if run == "baseline" else Controls.with_control(case["control"])
        results = []
        for i, d in enumerate(descriptions):
            r = one_attempt(case, provider, controls, d, prompts[i % len(prompts)])
            results.append(r)
            mark = "ERR" if r["error"] else ("HIT" if r["success"] else "ok ")
            print(f"[{case['id']} {run:8}] {i + 1:2}/{len(descriptions)} {mark}  {d[:70]}", flush=True)
        valid = [r for r in results if r["error"] is None]
        hits = sum(1 for r in valid if r["success"])
        out["runs"][run] = {
            "controls": controls.describe(),
            "attempts": len(descriptions),
            "valid": len(valid),
            "hits": hits,
            "asr": round(hits / len(valid), 3) if valid else None,
            "results": results,
        }
    return out


def write_results(out: dict) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    model_slug = re.sub(r"[^A-Za-z0-9.-]+", "_", str(out["model"]))
    folder = RESULTS / out["case"] / f"{model_slug}_{stamp}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [f"# {out['case']} · {out['title']}", "",
             f"Model: `{out['model']}` ({out['provider']}) · {out['timestamp']}", ""]
    lines += ["| Run | Attempts | Valid | Hits | ASR |", "|---|---|---|---|---|"]
    for run, r in out["runs"].items():
        lines.append(f"| {run} | {r['attempts']} | {r['valid']} | {r['hits']} | {r['asr']} |")
    for run, r in out["runs"].items():
        lines += ["", f"## Representative transcripts · {run}", ""]
        picks = []
        succ = next((x for x in r["results"] if x["success"]), None)
        fail = next((x for x in r["results"] if x["success"] is False), None)
        other = next((x for x in r["results"] if x is not succ and x is not fail), None)
        for label, x in (("attack succeeded", succ), ("attack failed", fail), ("another attempt", other)):
            if x:
                picks.append((label, x))
        for label, x in picks:
            lines += [f"### {label}", "", f"- Injected description: `{x['description']}`", f"- Customer prompt: {x['user_prompt']}",
                      f"- Tool calls: {json.dumps(x['tool_calls'], ensure_ascii=False)}",
                      f"- Events: {json.dumps(x['events'], ensure_ascii=False)}", "", "Reply:", "", "> " + "\n> ".join("\n".join(x["replies"]).splitlines() or ["(empty)"]), ""]
    (folder / "transcripts.md").write_text("\n".join(lines), encoding="utf-8")
    return folder


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cases", nargs="+", help="e.g. TC-01 TC-03")
    ap.add_argument("--attempts", type=int, default=None)
    ap.add_argument("--runs", default="baseline,control")
    args = ap.parse_args()
    runs = [r.strip() for r in args.runs.split(",") if r.strip()]
    provider = providers.from_env()
    if provider.name == "mock":
        print("PROVIDER=mock: checking mechanics only; these results are not evidence.", file=sys.stderr)
    for cid in args.cases:
        case = load_case(cid)
        out = run_case(case, provider, args.attempts, runs)
        folder = write_results(out)
        summary = "  ".join(f"{run}: ASR {r['asr']} ({r['hits']}/{r['valid']})" for run, r in out["runs"].items())
        print(f"\n{case['id']} -> {summary}\n  written to {folder}\n")


if __name__ == "__main__":
    main()

"""Operator reason message: turn a RESERVE decision's reasons into one sentence.

The model may only restate the listed reasons. If its sentence contains a number
that is not in the decision, is too long, or the call fails, we fall back to a
plain template built from the reasons, so the operator always gets a true message.

Usage:  python src/explain.py decision.json           (calls the model)
        python src/explain.py decision.json --offline  (template only, no key needed)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass

import llm

MAX_WORDS = 40
NUMBER = re.compile(r"\d+(?:\.\d+)?")


@dataclass
class Explanation:
    text: str
    source: str  # "model" or "fallback"


def validate(decision: dict) -> None:
    for key in ("event_id", "action", "score", "reserve_seats", "reasons"):
        if key not in decision:
            raise ValueError(f"decision is missing '{key}'")
    if decision["action"] not in ("RESERVE", "WATCH", "SKIP"):
        raise ValueError(f"unknown action {decision['action']!r}")
    reasons = decision["reasons"]
    if not isinstance(reasons, list) or not reasons or not all(isinstance(r, str) for r in reasons):
        raise ValueError("reasons must be a non-empty list of strings")


def build_prompt(d: dict) -> str:
    listed = "\n".join(f"{i}. {r}" for i, r in enumerate(d["reasons"], 1))
    return (
        "You write one short sentence for a ticketing operator.\n"
        f"Decision: RESERVE {d['reserve_seats']} seats for event {d['event_id']} "
        f"(demand score {d['score']}).\n"
        f"Reasons:\n{listed}\n"
        "Use ONLY these reasons. Do not add any fact, number, price or date that is "
        f"not listed. At most {MAX_WORDS} words. Reply with the sentence only.")


def _numbers(text: str) -> set[str]:
    return set(NUMBER.findall(text.replace(",", "")))


def is_grounded(sentence: str, d: dict) -> bool:
    allowed = _numbers(" ".join(d["reasons"]) + f" {d['score']} {d['reserve_seats']}")
    return (0 < len(sentence.split()) <= MAX_WORDS
            and _numbers(sentence) <= allowed)


def fallback(d: dict) -> str:
    return (f"Reserve {d['reserve_seats']} seats for {d['event_id']} "
            f"(score {d['score']}): " + "; ".join(d["reasons"]) + ".")


def explain(decision: dict, call=llm.complete) -> Explanation | None:
    """Return a one-sentence explanation for RESERVE, None for WATCH/SKIP (no model call)."""
    validate(decision)
    if decision["action"] != "RESERVE":
        return None
    if call is None:
        return Explanation(fallback(decision), "fallback")
    try:
        sentence = call(build_prompt(decision)).text
    except Exception as exc:  # network error, missing key, bad response
        print(f"model call failed, using fallback: {exc}", file=sys.stderr)
        return Explanation(fallback(decision), "fallback")
    if is_grounded(sentence, decision):
        return Explanation(sentence, "model")
    return Explanation(fallback(decision), "fallback")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("decision", help="path to a decision JSON file")
    p.add_argument("--offline", action="store_true", help="skip the model, use the template")
    args = p.parse_args(argv)
    with open(args.decision) as f:
        decision = json.load(f)
    try:
        result = explain(decision, call=None if args.offline else llm.complete)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(None if result is None else result.__dict__, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

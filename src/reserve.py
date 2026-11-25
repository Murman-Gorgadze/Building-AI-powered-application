"""Reserve-or-skip decision + loyalty-fan ranking for the ticket reserve.

Deliberately transparent: a weighted score where every point can be
explained to an operator (docs/decisions/0001). No model call, no network.
Promoted from hw1/Murman-Gorgadze/ after the HW1 deadline.

Run:  python -m src.reserve --tier 1 --day 2026-10-23 --capacity 50000 --sold 85 --days-out 21
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, field
from datetime import date, timedelta

# Config: tune these from backtests, do not hide them in code paths.
WEEKDAY_POINTS = {0: 0, 1: 0, 2: 3, 3: 8, 4: 18, 5: 22, 6: 15}  # Mon=0 .. Sun=6
TIER_POINTS = {1: 35, 2: 18, 3: 0}  # 1 = Champions League / big tour stop, 3 = minor
HOLIDAY_POINTS = 12
TOUR_POINTS = 10
RESERVE_AT, WATCH_AT = 60, 40
RESERVE_FRACTION = {"high": 0.10, "normal": 0.05}  # share of capacity held back

FAST_SALES_AT = 20  # velocity points at which the reason says "selling fast"

# Who counts as a loyal fan (docs/spec.md, Users): this many visits to one category in this window.
LOYAL_WINDOW_DAYS = 90
LOYAL_MIN_VISITS = 3

# Georgian public holidays 2026 (Labour Code, art. 30), including Orthodox Easter
# (Good Friday 10 April to Easter Monday 13 April 2026). Written from the agent's
# knowledge on 2026-11-18: CHECK against matsne.gov.ge before using in production.
HOLIDAYS_2026 = {
    date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 7), date(2026, 1, 19),
    date(2026, 3, 3), date(2026, 3, 8), date(2026, 4, 9),
    date(2026, 4, 10), date(2026, 4, 11), date(2026, 4, 12), date(2026, 4, 13),
    date(2026, 5, 9), date(2026, 5, 12), date(2026, 5, 17), date(2026, 5, 26),
    date(2026, 8, 28), date(2026, 10, 14), date(2026, 11, 23),
}


@dataclass
class Event:
    id: str
    category: str          # "football", "concert", ...
    tier: int              # 1..3
    day: date
    capacity: int
    sold_pct: float        # 0..100, sold at `days_out` days before the event
    days_out: int
    is_tour: bool = False


@dataclass
class Decision:
    event_id: str
    action: str            # RESERVE | WATCH | SKIP
    score: int
    reserve_seats: int
    reasons: list[str] = field(default_factory=list)


def day_points(day: date, holidays=HOLIDAYS_2026) -> tuple[int, list[str]]:
    """Points a date adds to demand on its own: the weekday, plus a holiday or the eve of one.
    The one place these rules live; demand_score() and the check_day tool both use it."""
    points, reasons = 0, []
    w = WEEKDAY_POINTS[day.weekday()]
    if w:
        points += w
        reasons.append(f"{day:%A} is a busy day (+{w})")
    if day in holidays or (day + timedelta(days=1)) in holidays:
        points += HOLIDAY_POINTS
        reasons.append(f"holiday or holiday eve (+{HOLIDAY_POINTS})")
    return points, reasons


def demand_score(e: Event, holidays=HOLIDAYS_2026) -> tuple[int, list[str]]:
    if e.tier not in TIER_POINTS:
        raise ValueError(f"tier must be 1..3, got {e.tier}")
    if not 0 <= e.sold_pct <= 100:
        raise ValueError("sold_pct must be 0..100")
    if e.capacity < 1:
        raise ValueError("capacity must be at least 1")
    if e.days_out < 0:
        raise ValueError("days_out must be 0 or more: the event is in the past")
    reasons = []
    score = TIER_POINTS[e.tier]
    if score:
        reasons.append(f"tier {e.tier} event (+{score})")
    d, day_reasons = day_points(e.day, holidays)
    score += d
    reasons += day_reasons
    if e.is_tour:
        score += TOUR_POINTS
        reasons.append(f"tour stop (+{TOUR_POINTS})")
    # Sell-through speed: % sold per day so far, capped at +25.
    velocity = e.sold_pct / max(e.days_out, 1)
    v = min(25, round(velocity * 10))
    if v:
        score += v
        pace = "selling fast" if v >= FAST_SALES_AT else "steady sales"
        reasons.append(f"{pace}, {e.sold_pct:.0f}% sold {e.days_out}d out (+{v})")
    return min(score, 100), reasons


def decide(e: Event, holidays=HOLIDAYS_2026) -> Decision:
    score, reasons = demand_score(e, holidays)
    if score >= RESERVE_AT:
        frac = RESERVE_FRACTION["high"] if e.tier == 1 else RESERVE_FRACTION["normal"]
        return Decision(e.id, "RESERVE", score, math.ceil(e.capacity * frac), reasons)
    if score >= WATCH_AT:
        return Decision(e.id, "WATCH", score, 0, reasons)
    return Decision(e.id, "SKIP", score, 0, reasons or ["low demand signals"])


def rank_fans(attendance: dict[str, list[tuple[str, date]]], category: str,
              today: date, window_days: int = LOYAL_WINDOW_DAYS,
              min_visits: int = LOYAL_MIN_VISITS) -> list[tuple[str, int]]:
    """Fans who attended `category` events at least `min_visits` times in the window,
    most frequent first. Ties broken by name so output is deterministic."""
    cutoff = today - timedelta(days=window_days)
    counts = {}
    for fan, visits in attendance.items():
        n = sum(1 for cat, d in visits if cat == category and cutoff <= d <= today)
        if n >= min_visits:
            counts[fan] = n
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def event_parser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--id", default="cli")
    p.add_argument("--category", default="football")
    p.add_argument("--tier", type=int, required=True)
    p.add_argument("--day", type=date.fromisoformat, required=True, help="YYYY-MM-DD")
    p.add_argument("--capacity", type=int, required=True)
    p.add_argument("--sold", type=float, required=True, help="percent sold, 0..100")
    p.add_argument("--days-out", type=int, required=True)
    p.add_argument("--tour", action="store_true")
    return p


def event_from_args(a: argparse.Namespace) -> Event:
    return Event(a.id, a.category, a.tier, a.day, a.capacity, a.sold, a.days_out, a.tour)


def main(argv: list[str] | None = None) -> int:
    a = event_parser("Reserve-or-skip decision for one event").parse_args(argv)
    try:
        d = decide(event_from_args(a))
    except ValueError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1
    print(f"{d.action} score={d.score} seats={d.reserve_seats}")
    for r in d.reasons:
        print(f"  - {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

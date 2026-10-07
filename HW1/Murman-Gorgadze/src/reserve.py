"""Reserve-or-skip decision + loyalty-fan ranking for the ticket reserve.

Deliberately transparent: a weighted score where every point can be
explained to an operator. A learned model can replace `demand_score`
later; the interface (Event -> Decision) stays the same.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta

# Config: tune these from backtests, do not hide them in code paths.
WEEKDAY_POINTS = {0: 0, 1: 0, 2: 3, 3: 8, 4: 18, 5: 22, 6: 15}  # Mon=0 .. Sun=6
TIER_POINTS = {1: 35, 2: 18, 3: 0}  # 1 = Champions League / big tour stop, 3 = minor
HOLIDAY_POINTS = 12
TOUR_POINTS = 10
RESERVE_AT, WATCH_AT = 60, 40
RESERVE_FRACTION = {"high": 0.10, "normal": 0.05}  # share of capacity held back

# ASSUMPTION: sample list only. Verify against the official calendar before use.
HOLIDAYS_2026 = {date(2026, 1, 1), date(2026, 1, 7), date(2026, 3, 3), date(2026, 3, 8),
                 date(2026, 4, 9), date(2026, 5, 9), date(2026, 5, 26), date(2026, 10, 14)}


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


def demand_score(e: Event, holidays=HOLIDAYS_2026) -> tuple[int, list[str]]:
    if e.tier not in TIER_POINTS:
        raise ValueError(f"tier must be 1..3, got {e.tier}")
    if not 0 <= e.sold_pct <= 100:
        raise ValueError("sold_pct must be 0..100")
    reasons = []
    score = TIER_POINTS[e.tier]
    if score:
        reasons.append(f"tier {e.tier} event (+{score})")
    w = WEEKDAY_POINTS[e.day.weekday()]
    if w:
        score += w
        reasons.append(f"{e.day:%A} is a busy day (+{w})")
    if e.day in holidays or (e.day + timedelta(days=1)) in holidays:
        score += HOLIDAY_POINTS
        reasons.append(f"holiday or holiday eve (+{HOLIDAY_POINTS})")
    if e.is_tour:
        score += TOUR_POINTS
        reasons.append(f"tour stop (+{TOUR_POINTS})")
    # Sell-through speed: % sold per day so far, capped at +25.
    velocity = e.sold_pct / max(e.days_out, 1)
    v = min(25, round(velocity * 10))
    if v:
        score += v
        reasons.append(f"selling fast, {e.sold_pct:.0f}% sold {e.days_out}d out (+{v})")
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
              today: date, window_days: int = 90, min_visits: int = 3) -> list[tuple[str, int]]:
    """Fans who attended `category` events at least `min_visits` times in the window,
    most frequent first. Ties broken by name so output is deterministic."""
    cutoff = today - timedelta(days=window_days)
    counts = {}
    for fan, visits in attendance.items():
        n = sum(1 for cat, d in visits if cat == category and cutoff <= d <= today)
        if n >= min_visits:
            counts[fan] = n
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

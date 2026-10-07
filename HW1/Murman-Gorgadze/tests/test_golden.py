import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from datetime import date
from reserve import Event, decide, rank_fans

def test_g1_big_friday_football_reserves():
    e = Event("ucl-1", "football", 1, date(2026, 10, 23), 50000, 85, 21)  # Friday
    d = decide(e)
    assert d.action == "RESERVE" and d.reserve_seats == 5000

def test_g2_minor_tuesday_skips():
    e = Event("local-1", "football", 3, date(2026, 10, 27), 8000, 30, 20)  # Tuesday
    assert decide(e).action == "SKIP"

def test_g3_fan_ranking_uses_category_and_window():
    today = date(2026, 10, 7)
    att = {"ana": [("football", date(2026, 9, d)) for d in (1, 8, 15, 22)],
           "beka": [("football", date(2026, 9, 1)), ("concert", date(2026, 9, 8)),
                    ("concert", date(2026, 9, 15)), ("concert", date(2026, 9, 22))],
           "gio": [("football", date(2026, 3, 1))] * 5}   # old visits, outside window
    assert rank_fans(att, "football", today) == [("ana", 4)]

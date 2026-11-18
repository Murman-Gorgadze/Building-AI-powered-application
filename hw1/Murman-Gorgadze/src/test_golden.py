from datetime import date

import pytest

from reserve import Event, decide, main, rank_fans


def test_g1_big_friday_football_reserves():                      # AC1
    e = Event("ucl-1", "football", 1, date(2026, 10, 23), 50000, 85, 21)  # Friday
    d = decide(e)
    assert d.action == "RESERVE" and d.score == 78 and d.reserve_seats == 5000


def test_g2_minor_tuesday_skips():                               # AC2
    e = Event("local-1", "football", 3, date(2026, 10, 27), 8000, 30, 20)  # Tuesday
    d = decide(e)
    assert d.action == "SKIP" and d.reserve_seats == 0


def test_g3_fan_ranking_uses_category_and_window():              # AC3
    today = date(2026, 10, 7)
    att = {"ana": [("football", date(2026, 9, d)) for d in (1, 8, 15, 22)],
           "beka": [("football", date(2026, 9, 1)), ("concert", date(2026, 9, 8)),
                    ("concert", date(2026, 9, 15)), ("concert", date(2026, 9, 22))],
           "gio": [("football", date(2026, 3, 1))] * 5}   # old visits, outside window
    assert rank_fans(att, "football", today) == [("ana", 4)]


def test_watch_band_holds_no_seats():                            # AC4
    # tier 2 (+18), Saturday 2026-10-24 (+22), 10% sold 20 days out (+5) = 45
    d = decide(Event("mid-1", "concert", 2, date(2026, 10, 24), 3000, 10, 20))
    assert d.action == "WATCH" and d.score == 45 and d.reserve_seats == 0


@pytest.mark.parametrize("tier, sold", [(1, 150), (1, -5), (4, 50), (0, 50)])
def test_bad_input_raises_value_error(tier, sold):               # AC5
    with pytest.raises(ValueError):
        decide(Event("bad", "football", tier, date(2026, 10, 23), 1000, sold, 10))


def test_cli_prints_decision_and_rejects_bad_input(capsys):      # AC1 + AC5 through the CLI
    assert main(["--tier", "1", "--day", "2026-10-23", "--capacity", "50000",
                 "--sold", "85", "--days-out", "21"]) == 0
    assert capsys.readouterr().out.startswith("RESERVE score=78 seats=5000")
    assert main(["--tier", "1", "--day", "2026-10-23", "--capacity", "50000",
                 "--sold", "150", "--days-out", "21"]) == 1
    assert "sold_pct must be 0..100" in capsys.readouterr().err


def test_decide_is_fast():                                       # AC6
    import time
    e = Event("ucl-1", "football", 1, date(2026, 10, 23), 50000, 85, 21)
    t0 = time.perf_counter()
    decide(e)
    assert time.perf_counter() - t0 < 0.2

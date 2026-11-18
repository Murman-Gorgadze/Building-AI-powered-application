from datetime import date

import pytest

from src.reserve import Event, decide, main, rank_fans


def ev(tier=1, day=date(2026, 10, 23), capacity=50000, sold=85, days_out=21, tour=False):
    return Event("e", "football", tier, day, capacity, sold, days_out, tour)


def test_ac1_big_friday_reserves_ten_percent():
    d = decide(ev())
    assert (d.action, d.score, d.reserve_seats) == ("RESERVE", 78, 5000)


def test_ac2_minor_tuesday_skips_with_zero_seats():
    d = decide(ev(tier=3, day=date(2026, 10, 27), capacity=8000, sold=30, days_out=20))
    assert (d.action, d.score, d.reserve_seats) == ("SKIP", 15, 0)


def test_ac2_slow_sales_are_not_called_fast():
    d = decide(ev(tier=3, day=date(2026, 10, 27), capacity=8000, sold=30, days_out=20))
    assert d.reasons == ["steady sales, 30% sold 20d out (+15)"]


def test_ac4_watch_band_holds_no_seats():
    d = decide(ev(tier=2, day=date(2026, 10, 24), capacity=3000, sold=10, days_out=20))
    assert (d.action, d.score, d.reserve_seats) == ("WATCH", 45, 0)


def test_tour_stop_on_holiday_reserves_five_percent():
    d = decide(ev(tier=2, day=date(2026, 10, 14), capacity=12000, sold=55, days_out=14, tour=True))
    assert (d.action, d.score, d.reserve_seats) == ("RESERVE", 68, 600)


@pytest.mark.parametrize("day", [date(2026, 4, 12), date(2026, 11, 22), date(2026, 1, 18)])
def test_holiday_and_holiday_eve_score(day):
    # Orthodox Easter; eve of Giorgoba; eve of Epiphany
    assert any("holiday" in r for r in decide(ev(day=day)).reasons)


def test_ordinary_day_is_not_a_holiday():
    assert not any("holiday" in r for r in decide(ev(day=date(2026, 10, 23))).reasons)


@pytest.mark.parametrize("kwargs, msg", [
    ({"sold": 150}, "sold_pct"), ({"sold": -1}, "sold_pct"),
    ({"tier": 4}, "tier"), ({"tier": 0}, "tier"),
    ({"capacity": 0}, "capacity"), ({"days_out": -3}, "days_out"),
])
def test_ac5_bad_input_raises(kwargs, msg):
    with pytest.raises(ValueError, match=msg):
        decide(ev(**kwargs))


def test_ac3_rank_fans_category_and_window():
    today = date(2026, 10, 7)
    att = {"ana": [("football", date(2026, 9, d)) for d in (1, 8, 15, 22)],
           "beka": [("football", date(2026, 9, 1))] + [("concert", date(2026, 9, d)) for d in (8, 15, 22)],
           "gio": [("football", date(2026, 3, 1))] * 5,
           "nino": [("football", date(2026, 9, d)) for d in (2, 9, 16, 23)]}
    assert rank_fans(att, "football", today) == [("ana", 4), ("nino", 4)]


def test_cli_exit_codes(capsys):
    assert main(["--tier", "1", "--day", "2026-10-23", "--capacity", "50000", "--sold", "85", "--days-out", "21"]) == 0
    assert capsys.readouterr().out.startswith("RESERVE score=78 seats=5000")
    assert main(["--tier", "1", "--day", "2026-10-23", "--capacity", "50000", "--sold", "150", "--days-out", "21"]) == 1

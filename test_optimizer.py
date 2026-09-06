from app.optimizer import recommend_action


def test_surplus_with_room_in_battery_recommends_charge():
    rec = recommend_action(solar_kw=80, wind_kw=20, demand_kw=60, battery_soc_pct=50)
    assert rec.action == "CHARGE"
    assert rec.magnitude_kw > 0


def test_surplus_with_full_battery_recommends_export():
    rec = recommend_action(solar_kw=80, wind_kw=20, demand_kw=60, battery_soc_pct=95)
    assert rec.action == "EXPORT"


def test_deficit_with_charged_battery_recommends_discharge():
    rec = recommend_action(solar_kw=10, wind_kw=5, demand_kw=90, battery_soc_pct=60)
    assert rec.action == "DISCHARGE"


def test_deficit_with_low_battery_recommends_hold():
    rec = recommend_action(solar_kw=10, wind_kw=5, demand_kw=90, battery_soc_pct=10)
    assert rec.action == "HOLD"


def test_balanced_load_with_healthy_battery_recommends_hold():
    rec = recommend_action(solar_kw=50, wind_kw=10, demand_kw=55, battery_soc_pct=60)
    assert rec.action == "HOLD"


def test_low_battery_with_small_surplus_opportunistically_charges():
    rec = recommend_action(solar_kw=50, wind_kw=10, demand_kw=55, battery_soc_pct=15)
    assert rec.action == "CHARGE"


def test_confidence_reflects_forecast_agreement():
    agree = recommend_action(
        solar_kw=80, wind_kw=20, demand_kw=60, battery_soc_pct=50,
        forecast_next_hour_net_kw=25,
    )
    disagree = recommend_action(
        solar_kw=80, wind_kw=20, demand_kw=60, battery_soc_pct=50,
        forecast_next_hour_net_kw=-5,
    )
    assert agree.confidence == "HIGH"
    assert disagree.confidence == "LOW"

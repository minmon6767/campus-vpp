"""
optimizer.py
------------
Rule-based dispatch recommendation engine.

Given the current state (battery SOC, current generation/demand) and a
short-term forecast, decides the single best next action for facilities
staff: CHARGE, DISCHARGE, CURTAIL, EXPORT, or HOLD — with a plain-language
reason.

The pitch deck's target architecture names a MILP-based optimiser for
production; this rule-based version is the ~30%-maturity stand-in noted
on the Technical Approach slide. It follows the same decision inputs and
produces the same output shape a MILP solver would (an action + a
justification), so it can be swapped in later without changing the API
contract or the dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass

BATTERY_CAPACITY_KWH = 200.0
BATTERY_MAX_RATE_KW = 50.0

SOC_LOW_THRESHOLD = 25.0     # % — below this, prioritise charging
SOC_HIGH_THRESHOLD = 90.0    # % — above this, safe to discharge/export freely
SURPLUS_THRESHOLD_KW = 10.0  # kW — generation surplus worth acting on
DEFICIT_THRESHOLD_KW = 10.0  # kW — demand deficit worth acting on


@dataclass
class Recommendation:
    action: str            # CHARGE | DISCHARGE | CURTAIL | EXPORT | HOLD
    magnitude_kw: float
    reason: str
    confidence: str        # HIGH | MEDIUM | LOW


def recommend_action(
    solar_kw: float,
    wind_kw: float,
    demand_kw: float,
    battery_soc_pct: float,
    forecast_next_hour_net_kw: float | None = None,
) -> Recommendation:
    """Decide the best next action given current readings and (optionally)
    the forecast net generation (solar+wind-demand) for the next hour.
    """
    net_kw = solar_kw + wind_kw - demand_kw
    forecast_hint = ""
    confidence = "MEDIUM"

    if forecast_next_hour_net_kw is not None:
        if (net_kw > 0) == (forecast_next_hour_net_kw > 0):
            confidence = "HIGH"
            forecast_hint = " Forecast confirms this trend continues into the next hour."
        else:
            confidence = "LOW"
            forecast_hint = " Note: forecast suggests this may reverse within the hour — re-check soon."

    # 1) Clear surplus: solar+wind exceeds demand comfortably.
    if net_kw > SURPLUS_THRESHOLD_KW:
        if battery_soc_pct < SOC_HIGH_THRESHOLD:
            charge_kw = min(net_kw, BATTERY_MAX_RATE_KW)
            return Recommendation(
                action="CHARGE",
                magnitude_kw=round(charge_kw, 1),
                reason=(
                    f"Generation exceeds demand by {net_kw:.0f} kW and battery is at "
                    f"{battery_soc_pct:.0f}% SOC — charge the battery with the surplus "
                    f"instead of curtailing it.{forecast_hint}"
                ),
                confidence=confidence,
            )
        else:
            return Recommendation(
                action="EXPORT",
                magnitude_kw=round(net_kw, 1),
                reason=(
                    f"Generation exceeds demand by {net_kw:.0f} kW and the battery is "
                    f"already near full ({battery_soc_pct:.0f}% SOC) — export the surplus "
                    f"to the grid rather than curtailing it.{forecast_hint}"
                ),
                confidence=confidence,
            )

    # 2) Clear deficit: demand exceeds generation.
    if net_kw < -DEFICIT_THRESHOLD_KW:
        deficit = -net_kw
        if battery_soc_pct > SOC_LOW_THRESHOLD:
            discharge_kw = min(deficit, BATTERY_MAX_RATE_KW)
            return Recommendation(
                action="DISCHARGE",
                magnitude_kw=round(discharge_kw, 1),
                reason=(
                    f"Demand exceeds generation by {deficit:.0f} kW and the battery has "
                    f"{battery_soc_pct:.0f}% SOC available — discharge to cover the gap "
                    f"and reduce grid import.{forecast_hint}"
                ),
                confidence=confidence,
            )
        else:
            return Recommendation(
                action="HOLD",
                magnitude_kw=0.0,
                reason=(
                    f"Demand exceeds generation by {deficit:.0f} kW but the battery is "
                    f"low ({battery_soc_pct:.0f}% SOC) — preserve remaining charge and "
                    f"accept grid import for now; consider shifting non-critical load."
                    f"{forecast_hint}"
                ),
                confidence=confidence,
            )

    # 3) Roughly balanced — small surplus/deficit within threshold band.
    if battery_soc_pct < SOC_LOW_THRESHOLD and net_kw >= 0:
        return Recommendation(
            action="CHARGE",
            magnitude_kw=round(max(0.0, net_kw), 1),
            reason=(
                f"Generation and demand are roughly balanced, but battery SOC is low "
                f"({battery_soc_pct:.0f}%) — opportunistically top up with any small "
                f"surplus available.{forecast_hint}"
            ),
            confidence=confidence,
        )

    return Recommendation(
        action="HOLD",
        magnitude_kw=0.0,
        reason=(
            f"Generation ({solar_kw + wind_kw:.0f} kW) and demand ({demand_kw:.0f} kW) "
            f"are roughly balanced and battery SOC is healthy ({battery_soc_pct:.0f}%) — "
            f"no dispatch action needed right now.{forecast_hint}"
        ),
        confidence=confidence,
    )

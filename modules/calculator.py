"""GI Cost Calculation Engine — depth-banded model."""
from typing import Dict, List


def calc_mobilization(n_boreholes: int, drilling_method: str, rates: dict) -> dict:
    """Fixed site setup + per-BH survey + per-BH rig move."""
    m = rates["mobilization"]
    fixed = m["site_establishment_fixed"]
    survey = m["survey_per_bh"] * n_boreholes
    rig_move = m["rig_move_per_bh"][drilling_method] * n_boreholes
    total = fixed + survey + rig_move
    return {
        "Site establishment (fixed)": fixed,
        "Per-BH survey": survey,
        "Per-BH rig move": rig_move,
        "TOTAL": total,
    }


def calc_drilling(depth_bands: Dict[str, float], n_boreholes: int,
                  drilling_method: str, rates: dict) -> dict:
    """Depth-banded drilling cost. depth_bands = average meters per BH in each band."""
    band_rates = rates["drilling_per_m"][drilling_method]
    breakdown = {}
    total = 0.0
    for band, avg_m_per_bh in depth_bands.items():
        total_m = avg_m_per_bh * n_boreholes
        rate = band_rates.get(band, 0)
        cost = total_m * rate
        breakdown[f"{band} m  ({total_m:.0f} m @ {rate}/m)"] = cost
        total += cost
    breakdown["TOTAL"] = total
    return breakdown


def calc_backfill(total_drilled_m: float, rates: dict) -> dict:
    cost = total_drilled_m * rates["backfill_per_m"]
    return {f"Grout backfill ({total_drilled_m:.0f} m @ {rates['backfill_per_m']}/m)": cost,
            "TOTAL": cost}


def calc_instrumentation(n_instrumented_bh: int, include_logger: bool,
                         n_loggers: int, rates: dict) -> dict:
    i = rates["instrumentation"]
    piezo = i["piezometer_per_nr"] * n_instrumented_bh
    cover = i["protective_cover_per_nr"] * n_instrumented_bh
    fencing = i["fencing_per_nr"] * n_instrumented_bh
    logger = i["data_logger_per_nr"] * n_loggers if include_logger else 0
    total = piezo + cover + fencing + logger
    return {
        "Piezometers": piezo,
        "Protective covers": cover,
        "Fencing / marker posts": fencing,
        "Data loggers": logger,
        "TOTAL": total,
    }


def calc_in_situ(test_quantities: Dict[str, int], rates: dict) -> dict:
    """test_quantities = {'CPT_piezocone': 13, 'packer_permeability': 5, ...}"""
    breakdown = {}
    total = 0.0
    for test, qty in test_quantities.items():
        rate = rates["in_situ_tests"].get(test, 0)
        cost = rate * qty
        if qty > 0:
            breakdown[f"{test} (x{qty})"] = cost
            total += cost
    breakdown["TOTAL"] = total
    return breakdown


def calc_lab_chemical(chem_qty: Dict[str, int], classif_qty: Dict[str, int],
                      rock_qty: Dict[str, int], rates: dict) -> dict:
    breakdown = {}
    total = 0.0
    for group_name, qty_dict, rate_key in [
        ("Chemical", chem_qty, "chemical_tests_per_sample"),
        ("Classification", classif_qty, "classification_tests_per_sample"),
        ("Rock", rock_qty, "rock_tests_per_sample"),
    ]:
        sub = 0.0
        for test, qty in qty_dict.items():
            rate = rates[rate_key].get(test, 0)
            sub += rate * qty
        breakdown[f"{group_name} sub-total"] = sub
        total += sub
    breakdown["TOTAL"] = total
    return breakdown


def calc_reporting(rates: dict, extra_copies: int = 2) -> dict:
    r = rates["reporting_overheads"]
    total = r["master_report"] + r["additional_copy"] * extra_copies + r["ags_digital_data"]
    return {
        "Master report": r["master_report"],
        f"Additional copies x{extra_copies}": r["additional_copy"] * extra_copies,
        "AGS digital data": r["ags_digital_data"],
        "TOTAL": total,
    }


def aggregate_costs(category_totals: Dict[str, float], n_boreholes: int) -> dict:
    grand = sum(category_totals.values())
    per_bh = grand / n_boreholes if n_boreholes else 0
    return {"grand_total": grand, "per_borehole": per_bh}
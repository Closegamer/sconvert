import re

import streamlit as st
from .unit_panel import render_unit_panel_header


AREA_UNITS: list[tuple[str, str, float]] = [
    ("mm2", "units.area.mm2", 1e-6),
    ("cm2", "units.area.cm2", 1e-4),
    ("in2", "units.area.in2", 0.00064516),
    ("dm2", "units.area.dm2", 0.01),
    ("ft2", "units.area.ft2", 0.09290304),
    ("yd2", "units.area.yd2", 0.83612736),
    ("m2", "units.area.m2", 1.0),
    ("perch_lk", "units.area.perch_lk", 25.29285264),
    ("are", "units.area.are", 100.0),
    ("sotka", "units.area.sotka", 100.0),
    ("acre", "units.area.acre", 4046.8564224),
    ("ha", "units.area.ha", 10000.0),
    ("km2", "units.area.km2", 1_000_000.0),
]

SUPERSCRIPT_DIGITS = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def _format_number(value: float) -> str:
    scientific = f"{value:.10e}"
    mantissa_str, exponent_str = scientific.split("e")
    exponent = int(exponent_str)
    if -4 <= exponent <= 6:
        return f"{value:.10g}"
    mantissa = float(mantissa_str)
    exponent_pretty = str(exponent).translate(SUPERSCRIPT_DIGITS)
    return f"{mantissa:.10g} × 10{exponent_pretty}"

def _parse_number(raw_value: str) -> float | None:
    normalized = raw_value.strip().replace(",", ".")
    if not normalized:
        return None
    match = re.match(r"^\s*([+-]?\d*\.?\d+)\s*\*\s*10\^\(\s*([+-]?\d+)\s*\)\s*$", normalized)
    if match:
        return float(match.group(1)) * (10 ** int(match.group(2)))
    try:
        return float(normalized)
    except ValueError:
        return None

def _sync_area_inputs_from_base() -> None:
    base_m2 = float(st.session_state.units_area_base_m2)
    for unit_code, _label_key, factor_to_m2 in AREA_UNITS:
        st.session_state[f"units_area_{unit_code}"] = _format_number(base_m2 / factor_to_m2)

def render_area_converter(texts: dict[str, str]) -> None:
    if "units_area_base_m2" not in st.session_state:
        st.session_state.units_area_base_m2 = 1.0
    if "units_area_last_inputs" not in st.session_state:
        st.session_state.units_area_last_inputs = {}

    input_keys = [f"units_area_{code}" for code, _k, _f in AREA_UNITS]
    needs_sync = any(key not in st.session_state for key in input_keys)

    if not needs_sync:
        last_inputs: dict[str, str] = st.session_state.units_area_last_inputs
        current_inputs = {code: st.session_state.get(f"units_area_{code}", "") for code, _k, _f in AREA_UNITS}
        changed_units = [
            code for code, _k, _f in AREA_UNITS if current_inputs.get(code) != last_inputs.get(code, "")
        ]
        for changed_unit in changed_units:
            parsed_value = _parse_number(current_inputs.get(changed_unit, ""))
            if parsed_value is None:
                continue
            factor_to_m2 = next(f for code, _k, f in AREA_UNITS if code == changed_unit)
            st.session_state.units_area_base_m2 = parsed_value * factor_to_m2
            needs_sync = True
            break

    if needs_sync:
        _sync_area_inputs_from_base()

    if "favorite_area" not in st.session_state:
        st.session_state.favorite_area = False
    favorite_toggle_key = "favorite_area_toggle"
    if favorite_toggle_key not in st.session_state:
        st.session_state[favorite_toggle_key] = bool(st.session_state.favorite_area)

    collapse_token = int(st.session_state.get("units_collapse_all_token", 0))
    seen_token_key = "units_area_seen_collapse_token"
    expanded_key = "units_area_expanded"
    if seen_token_key not in st.session_state:
        st.session_state[seen_token_key] = collapse_token
    if expanded_key not in st.session_state:
        st.session_state[expanded_key] = False
    if collapse_token != int(st.session_state[seen_token_key]):
        st.session_state[seen_token_key] = collapse_token
        st.session_state[expanded_key] = False

    render_unit_panel_header(
        panel_key="units_area_panel",
        title=texts["units.area.title"],
        expanded_key=expanded_key,
        expand_button_key="units_area_expand_btn",
        favorite_toggle_key=favorite_toggle_key,
        favorite_state_key="favorite_area",
    )

    if st.session_state[expanded_key]:
        left_col, right_col = st.columns(2, gap="small")
        columns = [left_col, right_col]
        for idx, (unit_code, label_key, _factor) in enumerate(AREA_UNITS):
            with columns[idx % 2]:
                st.text_input(
                    texts[label_key],
                    key=f"units_area_{unit_code}",
                )
    st.session_state.units_area_last_inputs = {
        code: st.session_state.get(f"units_area_{code}", "") for code, _k, _f in AREA_UNITS
    }

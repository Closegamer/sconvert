import re

import streamlit as st
from .unit_panel import render_unit_panel_header


MASS_UNITS: list[tuple[str, str, float]] = [
    ("mg", "units.mass.mg", 1e-6),
    ("g", "units.mass.g", 0.001),
    ("oz", "units.mass.oz", 0.028349523125),
    ("lb", "units.mass.lb", 0.45359237),
    ("kg", "units.mass.kg", 1.0),
    ("st", "units.mass.st", 6.35029318),
    ("pood", "units.mass.pood", 16.3804964),
    ("t", "units.mass.t", 1000.0),
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

def _sync_mass_inputs_from_base() -> None:
    base_kg = float(st.session_state.units_mass_base_kg)
    for unit_code, _label_key, factor_to_kg in MASS_UNITS:
        st.session_state[f"units_mass_{unit_code}"] = _format_number(base_kg / factor_to_kg)

def render_mass_converter(texts: dict[str, str]) -> None:
    if "units_mass_base_kg" not in st.session_state:
        st.session_state.units_mass_base_kg = 1.0
    if "units_mass_last_inputs" not in st.session_state:
        st.session_state.units_mass_last_inputs = {}

    input_keys = [f"units_mass_{code}" for code, _k, _f in MASS_UNITS]
    needs_sync = any(key not in st.session_state for key in input_keys)

    if not needs_sync:
        last_inputs: dict[str, str] = st.session_state.units_mass_last_inputs
        current_inputs = {code: st.session_state.get(f"units_mass_{code}", "") for code, _k, _f in MASS_UNITS}
        changed_units = [
            code for code, _k, _f in MASS_UNITS if current_inputs.get(code) != last_inputs.get(code, "")
        ]
        for changed_unit in changed_units:
            parsed_value = _parse_number(current_inputs.get(changed_unit, ""))
            if parsed_value is None:
                continue
            factor_to_kg = next(f for code, _k, f in MASS_UNITS if code == changed_unit)
            st.session_state.units_mass_base_kg = parsed_value * factor_to_kg
            needs_sync = True
            break

    if needs_sync:
        _sync_mass_inputs_from_base()

    if "favorite_mass" not in st.session_state:
        st.session_state.favorite_mass = False
    favorite_toggle_key = "favorite_mass_toggle"
    if favorite_toggle_key not in st.session_state:
        st.session_state[favorite_toggle_key] = bool(st.session_state.favorite_mass)

    collapse_token = int(st.session_state.get("units_collapse_all_token", 0))
    seen_token_key = "units_mass_seen_collapse_token"
    expanded_key = "units_mass_expanded"
    if seen_token_key not in st.session_state:
        st.session_state[seen_token_key] = collapse_token
    if expanded_key not in st.session_state:
        st.session_state[expanded_key] = False
    if collapse_token != int(st.session_state[seen_token_key]):
        st.session_state[seen_token_key] = collapse_token
        st.session_state[expanded_key] = False

    render_unit_panel_header(
        panel_key="units_mass_panel",
        title=texts["units.mass.title"],
        expanded_key=expanded_key,
        expand_button_key="units_mass_expand_btn",
        favorite_toggle_key=favorite_toggle_key,
        favorite_state_key="favorite_mass",
    )

    if st.session_state[expanded_key]:
        left_col, right_col = st.columns(2, gap="small")
        columns = [left_col, right_col]
        for idx, (unit_code, label_key, _factor) in enumerate(MASS_UNITS):
            with columns[idx % 2]:
                st.text_input(
                    texts[label_key],
                    key=f"units_mass_{unit_code}",
                )
    st.session_state.units_mass_last_inputs = {
        code: st.session_state.get(f"units_mass_{code}", "") for code, _k, _f in MASS_UNITS
    }

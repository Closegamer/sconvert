import re

import streamlit as st
from .unit_panel import render_unit_panel_header


ENERGY_UNITS: list[tuple[str, str, float]] = [
    ("ev", "units.energy.ev", 1.602176634e-19),
    ("j", "units.energy.j", 1.0),
    ("cal", "units.energy.cal", 4.184),
    ("kj", "units.energy.kj", 1000.0),
    ("btu", "units.energy.btu", 1055.05585262),
    ("wh", "units.energy.wh", 3600.0),
    ("kcal", "units.energy.kcal", 4184.0),
    ("kwh", "units.energy.kwh", 3_600_000.0),
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

def _sync_energy_inputs_from_base() -> None:
    base_j = float(st.session_state.units_energy_base_j)
    for unit_code, _label_key, factor_to_j in ENERGY_UNITS:
        st.session_state[f"units_energy_{unit_code}"] = _format_number(base_j / factor_to_j)

def render_energy_converter(texts: dict[str, str]) -> None:
    if "units_energy_base_j" not in st.session_state:
        st.session_state.units_energy_base_j = 1.0
    if "units_energy_last_inputs" not in st.session_state:
        st.session_state.units_energy_last_inputs = {}

    input_keys = [f"units_energy_{code}" for code, _k, _f in ENERGY_UNITS]
    needs_sync = any(key not in st.session_state for key in input_keys)

    if not needs_sync:
        last_inputs: dict[str, str] = st.session_state.units_energy_last_inputs
        current_inputs = {code: st.session_state.get(f"units_energy_{code}", "") for code, _k, _f in ENERGY_UNITS}
        changed_units = [
            code for code, _k, _f in ENERGY_UNITS if current_inputs.get(code) != last_inputs.get(code, "")
        ]
        for changed_unit in changed_units:
            parsed_value = _parse_number(current_inputs.get(changed_unit, ""))
            if parsed_value is None:
                continue
            factor_to_j = next(f for code, _k, f in ENERGY_UNITS if code == changed_unit)
            st.session_state.units_energy_base_j = parsed_value * factor_to_j
            needs_sync = True
            break

    if needs_sync:
        _sync_energy_inputs_from_base()

    if "favorite_energy" not in st.session_state:
        st.session_state.favorite_energy = False
    favorite_toggle_key = "favorite_energy_toggle"
    if favorite_toggle_key not in st.session_state:
        st.session_state[favorite_toggle_key] = bool(st.session_state.favorite_energy)

    collapse_token = int(st.session_state.get("units_collapse_all_token", 0))
    seen_token_key = "units_energy_seen_collapse_token"
    expanded_key = "units_energy_expanded"
    if seen_token_key not in st.session_state:
        st.session_state[seen_token_key] = collapse_token
    if expanded_key not in st.session_state:
        st.session_state[expanded_key] = False
    if collapse_token != int(st.session_state[seen_token_key]):
        st.session_state[seen_token_key] = collapse_token
        st.session_state[expanded_key] = False

    render_unit_panel_header(
        panel_key="units_energy_panel",
        title=texts["units.energy.title"],
        expanded_key=expanded_key,
        expand_button_key="units_energy_expand_btn",
        favorite_toggle_key=favorite_toggle_key,
        favorite_state_key="favorite_energy",
    )

    if st.session_state[expanded_key]:
        left_col, right_col = st.columns(2, gap="small")
        columns = [left_col, right_col]
        for idx, (unit_code, label_key, _factor) in enumerate(ENERGY_UNITS):
            with columns[idx % 2]:
                st.text_input(
                    texts[label_key],
                    key=f"units_energy_{unit_code}",
                )
    st.session_state.units_energy_last_inputs = {
        code: st.session_state.get(f"units_energy_{code}", "") for code, _k, _f in ENERGY_UNITS
    }

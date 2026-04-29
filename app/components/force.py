import re

import streamlit as st
from .unit_panel import render_unit_panel_header


FORCE_UNITS: list[tuple[str, str, float]] = [
    ("mn", "units.force.mn", 0.001),
    ("n", "units.force.n", 1.0),
    ("lbf", "units.force.lbf", 4.4482216152605),
    ("kgf", "units.force.kgf", 9.80665),
    ("kn", "units.force.kn", 1000.0),
    ("mnw", "units.force.mnw", 1_000_000.0),
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

def _sync_force_inputs_from_base() -> None:
    base_n = float(st.session_state.units_force_base_n)
    for unit_code, _label_key, factor_to_n in FORCE_UNITS:
        st.session_state[f"units_force_{unit_code}"] = _format_number(base_n / factor_to_n)

def render_force_converter(texts: dict[str, str]) -> None:
    if "units_force_base_n" not in st.session_state:
        st.session_state.units_force_base_n = 1.0
    if "units_force_last_inputs" not in st.session_state:
        st.session_state.units_force_last_inputs = {}

    input_keys = [f"units_force_{code}" for code, _k, _f in FORCE_UNITS]
    needs_sync = any(key not in st.session_state for key in input_keys)

    if not needs_sync:
        last_inputs: dict[str, str] = st.session_state.units_force_last_inputs
        current_inputs = {code: st.session_state.get(f"units_force_{code}", "") for code, _k, _f in FORCE_UNITS}
        changed_units = [
            code for code, _k, _f in FORCE_UNITS if current_inputs.get(code) != last_inputs.get(code, "")
        ]
        for changed_unit in changed_units:
            parsed_value = _parse_number(current_inputs.get(changed_unit, ""))
            if parsed_value is None:
                continue
            factor_to_n = next(f for code, _k, f in FORCE_UNITS if code == changed_unit)
            st.session_state.units_force_base_n = parsed_value * factor_to_n
            needs_sync = True
            break

    if needs_sync:
        _sync_force_inputs_from_base()

    if "favorite_force" not in st.session_state:
        st.session_state.favorite_force = False
    favorite_toggle_key = "favorite_force_toggle"
    if favorite_toggle_key not in st.session_state:
        st.session_state[favorite_toggle_key] = bool(st.session_state.favorite_force)

    collapse_token = int(st.session_state.get("units_collapse_all_token", 0))
    seen_token_key = "units_force_seen_collapse_token"
    expanded_key = "units_force_expanded"
    if seen_token_key not in st.session_state:
        st.session_state[seen_token_key] = collapse_token
    if expanded_key not in st.session_state:
        st.session_state[expanded_key] = False
    if collapse_token != int(st.session_state[seen_token_key]):
        st.session_state[seen_token_key] = collapse_token
        st.session_state[expanded_key] = False

    render_unit_panel_header(
        panel_key="units_force_panel",
        title=texts["units.force.title"],
        expanded_key=expanded_key,
        expand_button_key="units_force_expand_btn",
        favorite_toggle_key=favorite_toggle_key,
        favorite_state_key="favorite_force",
    )

    if st.session_state[expanded_key]:
        left_col, right_col = st.columns(2, gap="small")
        columns = [left_col, right_col]
        for idx, (unit_code, label_key, _factor) in enumerate(FORCE_UNITS):
            with columns[idx % 2]:
                st.text_input(
                    texts[label_key],
                    key=f"units_force_{unit_code}",
                )
    st.session_state.units_force_last_inputs = {
        code: st.session_state.get(f"units_force_{code}", "") for code, _k, _f in FORCE_UNITS
    }

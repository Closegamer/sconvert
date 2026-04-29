import re

import streamlit as st
from .unit_panel import render_unit_panel_header


SPEED_UNITS: list[tuple[str, str, float]] = [
    ("mm_s", "units.speed.mm_s", 0.001),
    ("cm_s", "units.speed.cm_s", 0.01),
    ("km_h", "units.speed.km_h", 1.0 / 3.6),
    ("fps", "units.speed.fps", 0.3048),
    ("mph", "units.speed.mph", 0.44704),
    ("kt", "units.speed.kt", 0.5144444444444445),
    ("m_s", "units.speed.m_s", 1.0),
    ("c", "units.speed.c", 299_792_458.0),
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


def _sync_speed_inputs_from_base() -> None:
    base_m_s = float(st.session_state.units_speed_base_m_s)
    for unit_code, _label_key, factor_to_m_s in SPEED_UNITS:
        st.session_state[f"units_speed_{unit_code}"] = _format_number(base_m_s / factor_to_m_s)


def render_speed_converter(texts: dict[str, str]) -> None:
    if "units_speed_base_m_s" not in st.session_state:
        st.session_state.units_speed_base_m_s = 1.0
    if "units_speed_last_inputs" not in st.session_state:
        st.session_state.units_speed_last_inputs = {}

    input_keys = [f"units_speed_{code}" for code, _k, _f in SPEED_UNITS]
    needs_sync = any(key not in st.session_state for key in input_keys)

    if not needs_sync:
        last_inputs: dict[str, str] = st.session_state.units_speed_last_inputs
        current_inputs = {code: st.session_state.get(f"units_speed_{code}", "") for code, _k, _f in SPEED_UNITS}
        changed_unit = next(
            (code for code, _k, _f in SPEED_UNITS if current_inputs.get(code) != last_inputs.get(code)),
            None,
        )
        if changed_unit is not None:
            parsed_value = _parse_number(current_inputs[changed_unit])
            if parsed_value is not None:
                factor_to_m_s = next(f for code, _k, f in SPEED_UNITS if code == changed_unit)
                st.session_state.units_speed_base_m_s = parsed_value * factor_to_m_s
                needs_sync = True

    if needs_sync:
        _sync_speed_inputs_from_base()

    if "favorite_speed" not in st.session_state:
        st.session_state.favorite_speed = False
    favorite_toggle_key = "favorite_speed_toggle"
    if favorite_toggle_key not in st.session_state:
        st.session_state[favorite_toggle_key] = bool(st.session_state.favorite_speed)

    collapse_token = int(st.session_state.get("units_collapse_all_token", 0))
    seen_token_key = "units_speed_seen_collapse_token"
    expanded_key = "units_speed_expanded"
    if seen_token_key not in st.session_state:
        st.session_state[seen_token_key] = collapse_token
    if expanded_key not in st.session_state:
        st.session_state[expanded_key] = False
    if collapse_token != int(st.session_state[seen_token_key]):
        st.session_state[seen_token_key] = collapse_token
        st.session_state[expanded_key] = False

    render_unit_panel_header(
        panel_key="units_speed_panel",
        title=texts["units.speed.title"],
        expanded_key=expanded_key,
        expand_button_key="units_speed_expand_btn",
        favorite_toggle_key=favorite_toggle_key,
        favorite_state_key="favorite_speed",
    )

    if st.session_state[expanded_key]:
        left_col, right_col = st.columns(2, gap="small")
        columns = [left_col, right_col]
        for idx, (unit_code, label_key, _factor) in enumerate(SPEED_UNITS):
            with columns[idx % 2]:
                st.text_input(
                    texts[label_key],
                    key=f"units_speed_{unit_code}",
                )
    st.session_state.units_speed_last_inputs = {
        code: st.session_state.get(f"units_speed_{code}", "") for code, _k, _f in SPEED_UNITS
    }

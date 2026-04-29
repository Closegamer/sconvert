import re

import streamlit as st
from .unit_panel import render_unit_panel_header


TIME_UNITS: list[tuple[str, str, float]] = [
    ("ms", "units.time.ms", 0.001),
    ("s", "units.time.s", 1.0),
    ("min", "units.time.min", 60.0),
    ("h", "units.time.h", 3600.0),
    ("day", "units.time.day", 86400.0),
    ("week", "units.time.week", 604800.0),
    ("month", "units.time.month", 2629800.0),
    ("year", "units.time.year", 31557600.0),
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


def _sync_time_inputs_from_base() -> None:
    base_s = float(st.session_state.units_time_base_s)
    for unit_code, _label_key, factor_to_s in TIME_UNITS:
        st.session_state[f"units_time_{unit_code}"] = _format_number(base_s / factor_to_s)


def render_time_converter(texts: dict[str, str]) -> None:
    if "units_time_base_s" not in st.session_state:
        st.session_state.units_time_base_s = 1.0
    if "units_time_last_inputs" not in st.session_state:
        st.session_state.units_time_last_inputs = {}

    input_keys = [f"units_time_{code}" for code, _k, _f in TIME_UNITS]
    needs_sync = any(key not in st.session_state for key in input_keys)

    if not needs_sync:
        last_inputs: dict[str, str] = st.session_state.units_time_last_inputs
        current_inputs = {code: st.session_state.get(f"units_time_{code}", "") for code, _k, _f in TIME_UNITS}
        changed_unit = next(
            (code for code, _k, _f in TIME_UNITS if current_inputs.get(code) != last_inputs.get(code)),
            None,
        )
        if changed_unit is not None:
            parsed_value = _parse_number(current_inputs[changed_unit])
            if parsed_value is not None:
                factor_to_s = next(f for code, _k, f in TIME_UNITS if code == changed_unit)
                st.session_state.units_time_base_s = parsed_value * factor_to_s
                needs_sync = True

    if needs_sync:
        _sync_time_inputs_from_base()

    if "favorite_time" not in st.session_state:
        st.session_state.favorite_time = False
    favorite_toggle_key = "favorite_time_toggle"
    if favorite_toggle_key not in st.session_state:
        st.session_state[favorite_toggle_key] = bool(st.session_state.favorite_time)

    collapse_token = int(st.session_state.get("units_collapse_all_token", 0))
    seen_token_key = "units_time_seen_collapse_token"
    expanded_key = "units_time_expanded"
    if seen_token_key not in st.session_state:
        st.session_state[seen_token_key] = collapse_token
    if expanded_key not in st.session_state:
        st.session_state[expanded_key] = False
    if collapse_token != int(st.session_state[seen_token_key]):
        st.session_state[seen_token_key] = collapse_token
        st.session_state[expanded_key] = False

    render_unit_panel_header(
        panel_key="units_time_panel",
        title=texts["units.time.title"],
        expanded_key=expanded_key,
        expand_button_key="units_time_expand_btn",
        favorite_toggle_key=favorite_toggle_key,
        favorite_state_key="favorite_time",
    )

    if st.session_state[expanded_key]:
        left_col, right_col = st.columns(2, gap="small")
        columns = [left_col, right_col]
        for idx, (unit_code, label_key, _factor) in enumerate(TIME_UNITS):
            with columns[idx % 2]:
                st.text_input(
                    texts[label_key],
                    key=f"units_time_{unit_code}",
                )
    st.session_state.units_time_last_inputs = {
        code: st.session_state.get(f"units_time_{code}", "") for code, _k, _f in TIME_UNITS
    }

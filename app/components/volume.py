import re

import streamlit as st
from .unit_panel import render_unit_panel_header


VOLUME_UNITS: list[tuple[str, str, float]] = [
    ("mm3", "units.volume.mm3", 1e-9),
    ("cm3", "units.volume.cm3", 1e-6),
    ("ml", "units.volume.ml", 1e-6),
    ("in3", "units.volume.in3", 1.6387064e-5),
    ("dm3", "units.volume.dm3", 0.001),
    ("l", "units.volume.l", 0.001),
    ("pt", "units.volume.pt", 0.000473176473),
    ("qt", "units.volume.qt", 0.000946352946),
    ("gal", "units.volume.gal", 0.003785411784),
    ("ft3", "units.volume.ft3", 0.028316846592),
    ("m3", "units.volume.m3", 1.0),
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


def _sync_volume_inputs_from_base() -> None:
    base_m3 = float(st.session_state.units_volume_base_m3)
    for unit_code, _label_key, factor_to_m3 in VOLUME_UNITS:
        st.session_state[f"units_volume_{unit_code}"] = _format_number(base_m3 / factor_to_m3)


def render_volume_converter(texts: dict[str, str]) -> None:
    if "units_volume_base_m3" not in st.session_state:
        st.session_state.units_volume_base_m3 = 1.0
    if "units_volume_last_inputs" not in st.session_state:
        st.session_state.units_volume_last_inputs = {}

    input_keys = [f"units_volume_{code}" for code, _k, _f in VOLUME_UNITS]
    needs_sync = any(key not in st.session_state for key in input_keys)

    if not needs_sync:
        last_inputs: dict[str, str] = st.session_state.units_volume_last_inputs
        current_inputs = {code: st.session_state.get(f"units_volume_{code}", "") for code, _k, _f in VOLUME_UNITS}
        changed_unit = next(
            (code for code, _k, _f in VOLUME_UNITS if current_inputs.get(code) != last_inputs.get(code)),
            None,
        )
        if changed_unit is not None:
            parsed_value = _parse_number(current_inputs[changed_unit])
            if parsed_value is not None:
                factor_to_m3 = next(f for code, _k, f in VOLUME_UNITS if code == changed_unit)
                st.session_state.units_volume_base_m3 = parsed_value * factor_to_m3
                needs_sync = True

    if needs_sync:
        _sync_volume_inputs_from_base()

    if "favorite_volume" not in st.session_state:
        st.session_state.favorite_volume = False
    favorite_toggle_key = "favorite_volume_toggle"
    if favorite_toggle_key not in st.session_state:
        st.session_state[favorite_toggle_key] = bool(st.session_state.favorite_volume)

    collapse_token = int(st.session_state.get("units_collapse_all_token", 0))
    seen_token_key = "units_volume_seen_collapse_token"
    expanded_key = "units_volume_expanded"
    if seen_token_key not in st.session_state:
        st.session_state[seen_token_key] = collapse_token
    if expanded_key not in st.session_state:
        st.session_state[expanded_key] = False
    if collapse_token != int(st.session_state[seen_token_key]):
        st.session_state[seen_token_key] = collapse_token
        st.session_state[expanded_key] = False

    render_unit_panel_header(
        panel_key="units_volume_panel",
        title=texts["units.volume.title"],
        expanded_key=expanded_key,
        expand_button_key="units_volume_expand_btn",
        favorite_toggle_key=favorite_toggle_key,
        favorite_state_key="favorite_volume",
    )

    if st.session_state[expanded_key]:
        left_col, right_col = st.columns(2, gap="small")
        columns = [left_col, right_col]
        for idx, (unit_code, label_key, _factor) in enumerate(VOLUME_UNITS):
            with columns[idx % 2]:
                st.text_input(
                    texts[label_key],
                    key=f"units_volume_{unit_code}",
                )
    st.session_state.units_volume_last_inputs = {
        code: st.session_state.get(f"units_volume_{code}", "") for code, _k, _f in VOLUME_UNITS
    }

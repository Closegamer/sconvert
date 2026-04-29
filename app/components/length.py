import streamlit as st
import re
from .unit_panel import render_unit_panel_header


LENGTH_UNITS: list[tuple[str, str, float]] = [
    ("nm", "units.length.nm", 1e-9),
    ("um", "units.length.um", 1e-6),
    ("mm", "units.length.mm", 0.001),
    ("cm", "units.length.cm", 0.01),
    ("in", "units.length.in", 0.0254),
    ("vershok", "units.length.vershok", 0.04445),
    ("dm", "units.length.dm", 0.1),
    ("pyad", "units.length.pyad", 0.1778),
    ("ft", "units.length.ft", 0.3048),
    ("lokot", "units.length.lokot", 0.4445),
    ("arshin", "units.length.arshin", 0.7112),
    ("yd", "units.length.yd", 0.9144),
    ("m", "units.length.m", 1.0),
    ("fathom", "units.length.fathom", 1.8288),
    ("sazhen", "units.length.sazhen", 2.1336),
    ("kosaya_sazhen", "units.length.kosaya_sazhen", 2.48),
    ("cable", "units.length.cable", 185.2),
    ("km", "units.length.km", 1000.0),
    ("mi", "units.length.mi", 1609.344),
    ("nmi", "units.length.nmi", 1852.0),
    ("league", "units.length.league", 4828.032),
    ("au", "units.length.au", 149597870700.0),
    ("ly", "units.length.ly", 9.4607304725808e15),
    ("pc", "units.length.pc", 3.085677581491367e16),
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


def _sync_length_inputs_from_base() -> None:
    base_m = float(st.session_state.units_length_base_m)
    for unit_code, _label_key, factor_to_m in LENGTH_UNITS:
        st.session_state[f"units_length_{unit_code}"] = _format_number(base_m / factor_to_m)


def render_length_converter(texts: dict[str, str]) -> None:
    if "units_length_base_m" not in st.session_state:
        st.session_state.units_length_base_m = 1.0
    if "units_length_last_inputs" not in st.session_state:
        st.session_state.units_length_last_inputs = {}

    input_keys = [f"units_length_{code}" for code, _k, _f in LENGTH_UNITS]
    needs_sync = any(key not in st.session_state for key in input_keys)

    if not needs_sync:
        last_inputs: dict[str, str] = st.session_state.units_length_last_inputs
        current_inputs = {code: st.session_state.get(f"units_length_{code}", "") for code, _k, _f in LENGTH_UNITS}
        changed_unit = next(
            (code for code, _k, _f in LENGTH_UNITS if current_inputs.get(code) != last_inputs.get(code)),
            None,
        )
        if changed_unit is not None:
            parsed_value = _parse_number(current_inputs[changed_unit])
            if parsed_value is not None:
                factor_to_m = next(f for code, _k, f in LENGTH_UNITS if code == changed_unit)
                st.session_state.units_length_base_m = parsed_value * factor_to_m
                needs_sync = True

    if needs_sync:
        _sync_length_inputs_from_base()

    if "favorite_length" not in st.session_state:
        st.session_state.favorite_length = False
    favorite_toggle_key = "favorite_length_toggle"
    if favorite_toggle_key not in st.session_state:
        st.session_state[favorite_toggle_key] = bool(st.session_state.favorite_length)

    collapse_token = int(st.session_state.get("units_collapse_all_token", 0))
    seen_token_key = "units_length_seen_collapse_token"
    expanded_key = "units_length_expanded"
    if seen_token_key not in st.session_state:
        st.session_state[seen_token_key] = collapse_token
    if expanded_key not in st.session_state:
        st.session_state[expanded_key] = False
    if collapse_token != int(st.session_state[seen_token_key]):
        st.session_state[seen_token_key] = collapse_token
        st.session_state[expanded_key] = False

    render_unit_panel_header(
        panel_key="units_length_panel",
        title=texts["units.length.title"],
        expanded_key=expanded_key,
        expand_button_key="units_length_expand_btn",
        favorite_toggle_key=favorite_toggle_key,
        favorite_state_key="favorite_length",
    )

    if st.session_state[expanded_key]:
        left_col, right_col = st.columns(2, gap="small")
        columns = [left_col, right_col]
        for idx, (unit_code, label_key, _factor) in enumerate(LENGTH_UNITS):
            with columns[idx % 2]:
                st.text_input(
                    texts[label_key],
                    key=f"units_length_{unit_code}",
                )
    st.session_state.units_length_last_inputs = {
        code: st.session_state.get(f"units_length_{code}", "") for code, _k, _f in LENGTH_UNITS
    }

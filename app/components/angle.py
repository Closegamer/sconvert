import re
import math
import streamlit as st
from .unit_panel import render_unit_panel_header

ANGLE_UNITS: list[tuple[str, str, float]] = [
    ("grad", "units.angle.grad", math.pi / 200.0),
    ("deg", "units.angle.deg", math.pi / 180.0),
    ("rad", "units.angle.rad", 1.0),
    ("turn", "units.angle.turn", 2.0 * math.pi),
]
SUPERSCRIPT_DIGITS = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")

def _format_number(value: float) -> str:
    scientific = f"{value:.10e}"
    mantissa_str, exponent_str = scientific.split("e")
    exponent = int(exponent_str)
    if -4 <= exponent <= 6:
        return f"{value:.10g}"
    return f"{float(mantissa_str):.10g} × 10{str(exponent).translate(SUPERSCRIPT_DIGITS)}"

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

def _sync_inputs() -> None:
    base = float(st.session_state.units_angle_base_rad)
    for code, _k, factor in ANGLE_UNITS:
        st.session_state[f"units_angle_{code}"] = _format_number(base / factor)

def render_angle_converter(texts: dict[str, str]) -> None:
    if "units_angle_base_rad" not in st.session_state:
        st.session_state.units_angle_base_rad = 1.0
    if "units_angle_last_inputs" not in st.session_state:
        st.session_state.units_angle_last_inputs = {}
    keys = [f"units_angle_{c}" for c, _k, _f in ANGLE_UNITS]
    needs_sync = any(k not in st.session_state for k in keys)
    if not needs_sync:
        last = st.session_state.units_angle_last_inputs
        current = {c: st.session_state.get(f"units_angle_{c}", "") for c, _k, _f in ANGLE_UNITS}
        changed_codes = [c for c, _k, _f in ANGLE_UNITS if current.get(c) != last.get(c, "")]
        for changed in changed_codes:
            parsed = _parse_number(current.get(changed, ""))
            if parsed is None:
                continue
            factor = next(f for c, _k, f in ANGLE_UNITS if c == changed)
            st.session_state.units_angle_base_rad = parsed * factor
            needs_sync = True
            break
    if needs_sync:
        _sync_inputs()
    if "favorite_angle" not in st.session_state:
        st.session_state.favorite_angle = False
    toggle_key = "favorite_angle_toggle"
    if toggle_key not in st.session_state:
        st.session_state[toggle_key] = bool(st.session_state.favorite_angle)
    collapse_token = int(st.session_state.get("units_collapse_all_token", 0))
    seen_key = "units_angle_seen_collapse_token"
    expanded_key = "units_angle_expanded"
    if seen_key not in st.session_state:
        st.session_state[seen_key] = collapse_token
    if expanded_key not in st.session_state:
        st.session_state[expanded_key] = False
    if collapse_token != int(st.session_state[seen_key]):
        st.session_state[seen_key] = collapse_token
        st.session_state[expanded_key] = False
    render_unit_panel_header(
        panel_key="units_angle_panel",
        title=texts["units.angle.title"],
        expanded_key=expanded_key,
        expand_button_key="units_angle_expand_btn",
        favorite_toggle_key=toggle_key,
        favorite_state_key="favorite_angle",
    )
    if st.session_state[expanded_key]:
        l, r = st.columns(2, gap="small")
        for idx, (code, label, _f) in enumerate(ANGLE_UNITS):
            with [l, r][idx % 2]:
                st.text_input(texts[label], key=f"units_angle_{code}")
    st.session_state.units_angle_last_inputs = {c: st.session_state.get(f"units_angle_{c}", "") for c, _k, _f in ANGLE_UNITS}

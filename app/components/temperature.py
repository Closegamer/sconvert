import streamlit as st


TEMPERATURE_UNITS: list[tuple[str, str]] = [
    ("c", "units.temperature.c"),
    ("f", "units.temperature.f"),
    ("k", "units.temperature.k"),
    ("r", "units.temperature.r"),
    ("re", "units.temperature.re"),
    ("n", "units.temperature.n"),
    ("de", "units.temperature.de"),
    ("ro", "units.temperature.ro"),
]


def _format_number(value: float) -> str:
    return f"{value:.10g}"


def _parse_number(raw_value: str) -> float | None:
    normalized = raw_value.strip().replace(",", ".")
    if not normalized:
        return None
    try:
        return float(normalized)
    except ValueError:
        return None


def _to_kelvin(unit_code: str, value: float) -> float:
    if unit_code == "c":
        return value + 273.15
    if unit_code == "f":
        return (value + 459.67) * 5.0 / 9.0
    if unit_code == "k":
        return value
    if unit_code == "r":
        return value * 5.0 / 9.0
    if unit_code == "re":
        return value * 1.25 + 273.15
    if unit_code == "n":
        return value * 100.0 / 33.0 + 273.15
    if unit_code == "de":
        return 373.15 - value * 2.0 / 3.0
    if unit_code == "ro":
        return (value - 7.5) * 40.0 / 21.0 + 273.15
    return value


def _from_kelvin(unit_code: str, kelvin: float) -> float:
    if unit_code == "c":
        return kelvin - 273.15
    if unit_code == "f":
        return kelvin * 9.0 / 5.0 - 459.67
    if unit_code == "k":
        return kelvin
    if unit_code == "r":
        return kelvin * 9.0 / 5.0
    if unit_code == "re":
        return (kelvin - 273.15) * 0.8
    if unit_code == "n":
        return (kelvin - 273.15) * 33.0 / 100.0
    if unit_code == "de":
        return (373.15 - kelvin) * 1.5
    if unit_code == "ro":
        return (kelvin - 273.15) * 21.0 / 40.0 + 7.5
    return kelvin


def _sync_temperature_inputs_from_base() -> None:
    base_k = float(st.session_state.units_temperature_base_k)
    for unit_code, _label_key in TEMPERATURE_UNITS:
        st.session_state[f"units_temperature_{unit_code}"] = _format_number(
            _from_kelvin(unit_code, base_k)
        )


def render_temperature_converter(texts: dict[str, str]) -> None:
    if "units_temperature_base_k" not in st.session_state:
        st.session_state.units_temperature_base_k = 273.15
    if "units_temperature_last_inputs" not in st.session_state:
        st.session_state.units_temperature_last_inputs = {}

    input_keys = [f"units_temperature_{code}" for code, _label in TEMPERATURE_UNITS]
    needs_sync = any(key not in st.session_state for key in input_keys)

    if not needs_sync:
        last_inputs: dict[str, str] = st.session_state.units_temperature_last_inputs
        current_inputs = {
            code: st.session_state.get(f"units_temperature_{code}", "")
            for code, _label in TEMPERATURE_UNITS
        }
        changed_unit = next(
            (
                code
                for code, _label in TEMPERATURE_UNITS
                if current_inputs.get(code) != last_inputs.get(code)
            ),
            None,
        )
        if changed_unit is not None:
            parsed_value = _parse_number(current_inputs[changed_unit])
            if parsed_value is not None:
                st.session_state.units_temperature_base_k = _to_kelvin(changed_unit, parsed_value)
                needs_sync = True

    if needs_sync:
        _sync_temperature_inputs_from_base()

    if "favorite_temperature" not in st.session_state:
        st.session_state.favorite_temperature = False
    favorite_toggle_key = "favorite_temperature_toggle"
    if favorite_toggle_key not in st.session_state:
        st.session_state[favorite_toggle_key] = bool(st.session_state.favorite_temperature)

    collapse_token = int(st.session_state.get("units_collapse_all_token", 0))
    seen_token_key = "units_temperature_seen_collapse_token"
    expanded_key = "units_temperature_expanded"
    if seen_token_key not in st.session_state:
        st.session_state[seen_token_key] = collapse_token
    if expanded_key not in st.session_state:
        st.session_state[expanded_key] = False
    if collapse_token != int(st.session_state[seen_token_key]):
        st.session_state[seen_token_key] = collapse_token
        st.session_state[expanded_key] = False

    with st.container(key="units_temperature_panel"):
        header_col, favorite_col = st.columns([8, 2], vertical_alignment="center")
        with header_col:
            if st.button(
                f'{"▼" if st.session_state[expanded_key] else "▶"} {texts["units.temperature.title"]}',
                key="units_temperature_expand_btn",
                use_container_width=True,
            ):
                st.session_state[expanded_key] = not bool(st.session_state[expanded_key])
                st.rerun()
        with favorite_col:
            st.toggle("★", key=favorite_toggle_key)
            st.session_state.favorite_temperature = bool(st.session_state[favorite_toggle_key])

    if st.session_state[expanded_key]:
        left_col, right_col = st.columns(2, gap="small")
        columns = [left_col, right_col]
        for idx, (unit_code, label_key) in enumerate(TEMPERATURE_UNITS):
            with columns[idx % 2]:
                st.text_input(
                    texts[label_key],
                    key=f"units_temperature_{unit_code}",
                )

    st.session_state.units_temperature_last_inputs = {
        code: st.session_state.get(f"units_temperature_{code}", "")
        for code, _label in TEMPERATURE_UNITS
    }

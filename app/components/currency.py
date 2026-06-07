import os
import streamlit as st

_CURRENCIES: list[tuple[str, str]] = [
    ("USD", "curr.usd"),
    ("EUR", "curr.eur"),
    ("RUB", "curr.rub"),
    ("GBP", "curr.gbp"),
    ("CNY", "curr.cny"),
    ("JPY", "curr.jpy"),
    ("CHF", "curr.chf"),
    ("CAD", "curr.cad"),
    ("AUD", "curr.aud"),
    ("TRY", "curr.try"),
    ("KZT", "curr.kzt"),
    ("BYN", "curr.byn"),
    ("UAH", "curr.uah"),
    ("AED", "curr.aed"),
    ("SGD", "curr.sgd"),
    ("HKD", "curr.hkd"),
    ("NOK", "curr.nok"),
    ("SEK", "curr.sek"),
    ("INR", "curr.inr"),
]


def _format_number(value: float) -> str:
    if value == 0:
        return "0"
    return f"{value:.8g}"


def _parse_number(raw: str) -> float | None:
    s = raw.strip().replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_rates() -> tuple[dict[str, float] | None, str | None]:
    try:
        import requests as _req
        url = os.getenv("INTERNAL_API_URL", "http://api:8000") + "/api/currency/rates"
        r = _req.get(url, timeout=8)
        r.raise_for_status()
        data = r.json()
        return data.get("rates"), data.get("updated_at")
    except Exception:
        return None, None


def _sync_currency_inputs_from_base(rates: dict[str, float]) -> None:
    base_usd = float(st.session_state.currency_base_usd)
    for code, _ in _CURRENCIES:
        rate = rates.get(code)
        if rate:
            st.session_state[f"currency_{code}"] = _format_number(base_usd * rate)
        else:
            st.session_state[f"currency_{code}"] = ""


def render_currency_converter(texts: dict[str, str]) -> None:
    rates, updated_at = _fetch_rates()

    if rates is None:
        st.error(texts.get("curr.error", "Не удалось получить курсы валют. Попробуйте позже."))
        return

    if "currency_base_usd" not in st.session_state:
        st.session_state.currency_base_usd = 1.0
    if "currency_last_inputs" not in st.session_state:
        st.session_state.currency_last_inputs = {}

    input_keys = [f"currency_{code}" for code, _ in _CURRENCIES]
    needs_sync = any(key not in st.session_state for key in input_keys)

    if not needs_sync:
        last = st.session_state.currency_last_inputs
        current = {code: st.session_state.get(f"currency_{code}", "") for code, _ in _CURRENCIES}
        for code, _ in _CURRENCIES:
            if current.get(code) != last.get(code, ""):
                val = _parse_number(current.get(code, ""))
                if val is not None:
                    rate = rates.get(code)
                    if rate:
                        st.session_state.currency_base_usd = val / rate
                        needs_sync = True
                break

    if needs_sync:
        _sync_currency_inputs_from_base(rates)

    if updated_at:
        date_str = str(updated_at)[:16].replace("T", " ")
        st.caption(
            f"{texts.get('curr.rates_as_of', 'Курсы на')} {date_str} UTC"
            f" · {texts.get('curr.source', 'источник')}: open.er-api.com"
        )

    left_col, right_col = st.columns(2, gap="small")
    columns = [left_col, right_col]
    for idx, (code, label_key) in enumerate(_CURRENCIES):
        with columns[idx % 2]:
            st.text_input(
                texts.get(label_key, code),
                key=f"currency_{code}",
            )

    st.session_state.currency_last_inputs = {
        code: st.session_state.get(f"currency_{code}", "") for code, _ in _CURRENCIES
    }

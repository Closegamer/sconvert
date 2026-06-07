import os
import streamlit as st

_CURRENCIES: list[tuple[str, str]] = [
    # Резервные валюты / Reserve currencies
    ("USD", "curr.usd"),
    ("EUR", "curr.eur"),
    ("GBP", "curr.gbp"),
    ("JPY", "curr.jpy"),
    ("CHF", "curr.chf"),
    ("CNY", "curr.cny"),
    # Прочие крупные / Other major
    ("AUD", "curr.aud"),
    ("CAD", "curr.cad"),
    ("HKD", "curr.hkd"),
    ("SGD", "curr.sgd"),
    ("NZD", "curr.nzd"),
    ("NOK", "curr.nok"),
    ("SEK", "curr.sek"),
    ("DKK", "curr.dkk"),
    # Восточная Европа / СНГ
    ("RUB", "curr.rub"),
    ("UAH", "curr.uah"),
    ("BYN", "curr.byn"),
    ("KZT", "curr.kzt"),
    ("UZS", "curr.uzs"),
    ("KGS", "curr.kgs"),
    ("TJS", "curr.tjs"),
    ("TMT", "curr.tmt"),
    ("AZN", "curr.azn"),
    ("GEL", "curr.gel"),
    ("AMD", "curr.amd"),
    ("MDL", "curr.mdl"),
    # Центральная / Восточная Европа
    ("PLN", "curr.pln"),
    ("CZK", "curr.czk"),
    ("HUF", "curr.huf"),
    ("RON", "curr.ron"),
    ("BGN", "curr.bgn"),
    ("HRK", "curr.hrk"),
    ("RSD", "curr.rsd"),
    ("MKD", "curr.mkd"),
    ("ALL", "curr.all"),
    ("BAM", "curr.bam"),
    ("ISK", "curr.isk"),
    # Ближний Восток
    ("TRY", "curr.try"),
    ("ILS", "curr.ils"),
    ("SAR", "curr.sar"),
    ("AED", "curr.aed"),
    ("QAR", "curr.qar"),
    ("KWD", "curr.kwd"),
    ("BHD", "curr.bhd"),
    ("OMR", "curr.omr"),
    ("JOD", "curr.jod"),
    ("IQD", "curr.iqd"),
    ("IRR", "curr.irr"),
    ("LBP", "curr.lbp"),
    ("SYP", "curr.syp"),
    ("YER", "curr.yer"),
    # Южная Азия
    ("INR", "curr.inr"),
    ("PKR", "curr.pkr"),
    ("BDT", "curr.bdt"),
    ("NPR", "curr.npr"),
    ("LKR", "curr.lkr"),
    ("MVR", "curr.mvr"),
    ("BTN", "curr.btn"),
    ("AFN", "curr.afn"),
    # Юго-Восточная / Восточная Азия
    ("KRW", "curr.krw"),
    ("TWD", "curr.twd"),
    ("THB", "curr.thb"),
    ("MYR", "curr.myr"),
    ("IDR", "curr.idr"),
    ("PHP", "curr.php"),
    ("VND", "curr.vnd"),
    ("MNT", "curr.mnt"),
    ("MOP", "curr.mop"),
    ("KHR", "curr.khr"),
    ("LAK", "curr.lak"),
    ("MMK", "curr.mmk"),
    ("BND", "curr.bnd"),
    # Океания
    ("FJD", "curr.fjd"),
    ("PGK", "curr.pgk"),
    ("SBD", "curr.sbd"),
    ("VUV", "curr.vuv"),
    ("WST", "curr.wst"),
    ("TOP", "curr.top"),
    ("XPF", "curr.xpf"),
    # Латинская Америка
    ("MXN", "curr.mxn"),
    ("BRL", "curr.brl"),
    ("ARS", "curr.ars"),
    ("CLP", "curr.clp"),
    ("COP", "curr.cop"),
    ("PEN", "curr.pen"),
    ("BOB", "curr.bob"),
    ("PYG", "curr.pyg"),
    ("UYU", "curr.uyu"),
    ("VES", "curr.ves"),
    ("DOP", "curr.dop"),
    ("GTQ", "curr.gtq"),
    ("HNL", "curr.hnl"),
    ("NIO", "curr.nio"),
    ("CRC", "curr.crc"),
    ("PAB", "curr.pab"),
    ("CUP", "curr.cup"),
    ("JMD", "curr.jmd"),
    ("TTD", "curr.ttd"),
    ("BBD", "curr.bbd"),
    ("BSD", "curr.bsd"),
    ("HTG", "curr.htg"),
    ("XCD", "curr.xcd"),
    ("BZD", "curr.bzd"),
    ("GYD", "curr.gyd"),
    ("SRD", "curr.srd"),
    ("AWG", "curr.awg"),
    ("ANG", "curr.ang"),
    ("SVC", "curr.svc"),
    ("KYD", "curr.kyd"),
    ("BMD", "curr.bmd"),
    # Северная Африка
    ("MAD", "curr.mad"),
    ("TND", "curr.tnd"),
    ("DZD", "curr.dzd"),
    ("LYD", "curr.lyd"),
    ("EGP", "curr.egp"),
    ("SDG", "curr.sdg"),
    # Африка к югу от Сахары
    ("ZAR", "curr.zar"),
    ("NGN", "curr.ngn"),
    ("KES", "curr.kes"),
    ("GHS", "curr.ghs"),
    ("TZS", "curr.tzs"),
    ("UGX", "curr.ugx"),
    ("ETB", "curr.etb"),
    ("XOF", "curr.xof"),
    ("XAF", "curr.xaf"),
    ("CDF", "curr.cdf"),
    ("AOA", "curr.aoa"),
    ("MGA", "curr.mga"),
    ("MZN", "curr.mzn"),
    ("ZMW", "curr.zmw"),
    ("BWP", "curr.bwp"),
    ("NAD", "curr.nad"),
    ("ZWL", "curr.zwl"),
    ("MWK", "curr.mwk"),
    ("RWF", "curr.rwf"),
    ("BIF", "curr.bif"),
    ("SOS", "curr.sos"),
    ("DJF", "curr.djf"),
    ("ERN", "curr.ern"),
    ("SCR", "curr.scr"),
    ("MUR", "curr.mur"),
    ("CVE", "curr.cve"),
    ("GMD", "curr.gmd"),
    ("GNF", "curr.gnf"),
    ("SLL", "curr.sll"),
    ("LRD", "curr.lrd"),
    ("SZL", "curr.szl"),
    ("LSL", "curr.lsl"),
    ("STN", "curr.stn"),
    ("KMF", "curr.kmf"),
    ("MRU", "curr.mru"),
    # Прочие территории
    ("GIP", "curr.gip"),
    ("FKP", "curr.fkp"),
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
        parts = str(updated_at).split()
        date_str = " ".join(parts[1:4]) if len(parts) >= 4 else str(updated_at)[:16]
        st.caption(
            f"{texts.get('curr.rates_as_of', 'Курсы на')} {date_str}"
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

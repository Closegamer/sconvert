from pathlib import Path
import json

import streamlit as st
import streamlit.components.v1 as components
from lang import EN_TEXTS, RU_TEXTS
from layout import render_footer, render_header
from views import render_about, render_btc, render_files, render_home, render_units
from components import render_privacy_component

try:
    from streamlit_local_storage import LocalStorage  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:
    class LocalStorage:  # type: ignore[no-redef]
        def getItem(self, _key: str, key: str | None = None) -> None:
            return None

        def setItem(self, _key: str, _value: str, key: str | None = None) -> None:
            return None

st.set_page_config(
    page_title="sconvert",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

st.markdown(
    """
    <meta name="description" content="sconvert: online converters for units, data formats, and Bitcoin tools.">
    <meta name="robots" content="index,follow,max-image-preview:large">
    <link rel="canonical" href="https://sconvert.ru/">
    <meta property="og:type" content="website">
    <meta property="og:site_name" content="sconvert">
    <meta property="og:title" content="sconvert - converters and BTC tools">
    <meta property="og:description" content="Convert units, work with BTC keys/addresses, and use practical online tools.">
    <meta property="og:url" content="https://sconvert.ru/">
    <meta property="og:image" content="https://sconvert.ru/og-image.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="sconvert - converters and BTC tools">
    <meta name="twitter:description" content="Convert units, work with BTC keys/addresses, and use practical online tools.">
    <meta name="twitter:image" content="https://sconvert.ru/og-image.png">
    """,
    unsafe_allow_html=True,
)

components.html(
    """
    <script>
    (() => {
      const head = window.parent?.document?.head;
      if (!head) return;
      const ensureMeta = (attr, key, content) => {
        let el = head.querySelector(`meta[${attr}="${key}"]`);
        if (!el) {
          el = window.parent.document.createElement("meta");
          el.setAttribute(attr, key);
          head.appendChild(el);
        }
        el.setAttribute("content", content);
      };
      const ensureLink = (rel, href) => {
        let el = head.querySelector(`link[rel="${rel}"][data-sconvert-seo="1"]`);
        if (!el) {
          el = window.parent.document.createElement("link");
          el.setAttribute("rel", rel);
          el.setAttribute("data-sconvert-seo", "1");
          head.appendChild(el);
        }
        el.setAttribute("href", href);
      };
      ensureMeta("name", "description", "sconvert: online converters for units, data formats, and Bitcoin tools.");
      ensureMeta("name", "robots", "index,follow,max-image-preview:large");
      ensureMeta("property", "og:type", "website");
      ensureMeta("property", "og:site_name", "sconvert");
      ensureMeta("property", "og:title", "sconvert - converters and BTC tools");
      ensureMeta("property", "og:description", "Convert units, work with BTC keys/addresses, and use practical online tools.");
      ensureMeta("property", "og:url", "https://sconvert.ru/");
      ensureMeta("property", "og:image", "https://sconvert.ru/og-image.png");
      ensureMeta("name", "twitter:card", "summary_large_image");
      ensureMeta("name", "twitter:title", "sconvert - converters and BTC tools");
      ensureMeta("name", "twitter:description", "Convert units, work with BTC keys/addresses, and use practical online tools.");
      ensureMeta("name", "twitter:image", "https://sconvert.ru/og-image.png");
      ensureLink("canonical", "https://sconvert.ru/");
    })();
    </script>
    """,
    height=0,
)

_css_path = Path(__file__).resolve().parent / "static" / "home.css"
st.markdown(f"<style>{_css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

allowed_views = {"home", "units", "files", "btc", "about"}
if "view" not in st.session_state or st.session_state.view not in allowed_views:
    st.session_state.view = "home"
if "lang" not in st.session_state or st.session_state.lang not in {"ru", "en"}:
    st.session_state.lang = "ru"
if "mobile_menu_open" not in st.session_state:
    st.session_state.mobile_menu_open = False

requested_view = st.query_params.get("view")
if isinstance(requested_view, list):
    requested_view = requested_view[0] if requested_view else None
if requested_view in allowed_views:
    st.session_state.view = requested_view
    st.query_params.clear()
    st.rerun()

if "show_privacy" not in st.session_state:
    st.session_state.show_privacy = False
if "privacy_origin_view" not in st.session_state:
    st.session_state.privacy_origin_view = None

requested_policy = st.query_params.get("policy")
if isinstance(requested_policy, list):
    requested_policy = requested_policy[0] if requested_policy else None
if str(requested_policy) == "1":
    st.session_state.show_privacy = True
    st.session_state.privacy_origin_view = st.session_state.view
    st.query_params.clear()
    st.rerun()

local_storage = LocalStorage()
favorites_storage_key = "sconvert_favorites"


def _favorites_from_storage(raw_value: str | dict[str, bool] | None) -> dict[str, bool]:
    if not raw_value:
        return {}
    if isinstance(raw_value, dict):
        return {k: bool(v) for k, v in raw_value.items()}
    try:
        decoded = json.loads(raw_value)
    except (json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(decoded, dict):
        return {}
    return {k: bool(v) for k, v in decoded.items()}


if "favorites_local_bootstrapped" not in st.session_state:
    st.session_state.favorites_local_bootstrapped = False
if "favorites_local_bootstrap_tries" not in st.session_state:
    st.session_state.favorites_local_bootstrap_tries = 0

if st.session_state.view != "privacy" and not st.session_state.favorites_local_bootstrapped:
    local_storage.refreshItems()
    stored_favorites_raw = local_storage.getItem(favorites_storage_key)
    if stored_favorites_raw is not None:
        stored_favorites = _favorites_from_storage(stored_favorites_raw)
        st.session_state.favorite_length = bool(stored_favorites.get("length", False))
        st.session_state.favorite_temperature = bool(stored_favorites.get("temperature", False))
        st.session_state.favorite_mass = bool(stored_favorites.get("mass", False))
        st.session_state.favorite_area = bool(stored_favorites.get("area", False))
        st.session_state.favorite_volume = bool(stored_favorites.get("volume", False))
        st.session_state.favorite_speed = bool(stored_favorites.get("speed", False))
        st.session_state.favorite_time = bool(stored_favorites.get("time", False))
        st.session_state.favorite_pressure = bool(stored_favorites.get("pressure", False))
        st.session_state.favorite_energy = bool(stored_favorites.get("energy", False))
        st.session_state.favorite_power = bool(stored_favorites.get("power", False))
        st.session_state.favorite_force = bool(stored_favorites.get("force", False))
        st.session_state.favorite_frequency = bool(stored_favorites.get("frequency", False))
        st.session_state.favorite_angle = bool(stored_favorites.get("angle", False))
        st.session_state.favorite_density = bool(stored_favorites.get("density", False))
        st.session_state.favorite_flow = bool(stored_favorites.get("flow", False))
        st.session_state.favorite_acc = bool(stored_favorites.get("acc", False))
        st.session_state.favorite_current = bool(stored_favorites.get("current", False))
        st.session_state.favorite_voltage = bool(stored_favorites.get("voltage", False))
        st.session_state.favorite_resistance = bool(stored_favorites.get("resistance", False))
        st.session_state.favorite_illuminance = bool(stored_favorites.get("illuminance", False))
        st.session_state.favorite_radiation = bool(stored_favorites.get("radiation", False))
        st.session_state.favorite_data = bool(stored_favorites.get("data", False))
        st.session_state.units_length_expanded = bool(stored_favorites.get("length_expanded", False))
        st.session_state.units_temperature_expanded = bool(stored_favorites.get("temperature_expanded", False))
        st.session_state.units_mass_expanded = bool(stored_favorites.get("mass_expanded", False))
        st.session_state.units_area_expanded = bool(stored_favorites.get("area_expanded", False))
        st.session_state.units_volume_expanded = bool(stored_favorites.get("volume_expanded", False))
        st.session_state.units_speed_expanded = bool(stored_favorites.get("speed_expanded", False))
        st.session_state.units_time_expanded = bool(stored_favorites.get("time_expanded", False))
        st.session_state.units_pressure_expanded = bool(stored_favorites.get("pressure_expanded", False))
        st.session_state.units_energy_expanded = bool(stored_favorites.get("energy_expanded", False))
        st.session_state.units_power_expanded = bool(stored_favorites.get("power_expanded", False))
        st.session_state.units_force_expanded = bool(stored_favorites.get("force_expanded", False))
        st.session_state.units_frequency_expanded = bool(stored_favorites.get("frequency_expanded", False))
        st.session_state.units_angle_expanded = bool(stored_favorites.get("angle_expanded", False))
        st.session_state.units_density_expanded = bool(stored_favorites.get("density_expanded", False))
        st.session_state.units_flow_expanded = bool(stored_favorites.get("flow_expanded", False))
        st.session_state.units_acc_expanded = bool(stored_favorites.get("acc_expanded", False))
        st.session_state.units_current_expanded = bool(stored_favorites.get("current_expanded", False))
        st.session_state.units_voltage_expanded = bool(stored_favorites.get("voltage_expanded", False))
        st.session_state.units_resistance_expanded = bool(stored_favorites.get("resistance_expanded", False))
        st.session_state.units_illuminance_expanded = bool(stored_favorites.get("illuminance_expanded", False))
        st.session_state.units_radiation_expanded = bool(stored_favorites.get("radiation_expanded", False))
        st.session_state.units_data_expanded = bool(stored_favorites.get("data_expanded", False))
        st.session_state.favorites_local_bootstrapped = True
        st.session_state.favorites_local_last_payload = json.dumps(
            {
                "length": bool(st.session_state.favorite_length),
                "temperature": bool(st.session_state.favorite_temperature),
                "mass": bool(st.session_state.favorite_mass),
                "area": bool(st.session_state.favorite_area),
                "volume": bool(st.session_state.favorite_volume),
                "speed": bool(st.session_state.favorite_speed),
                "time": bool(st.session_state.favorite_time),
                "pressure": bool(st.session_state.favorite_pressure),
                "energy": bool(st.session_state.favorite_energy),
                "power": bool(st.session_state.favorite_power),
                "force": bool(st.session_state.favorite_force),
                "frequency": bool(st.session_state.favorite_frequency),
                "angle": bool(st.session_state.favorite_angle),
                "density": bool(st.session_state.favorite_density),
                "flow": bool(st.session_state.favorite_flow),
                "acc": bool(st.session_state.favorite_acc),
                "current": bool(st.session_state.favorite_current),
                "voltage": bool(st.session_state.favorite_voltage),
                "resistance": bool(st.session_state.favorite_resistance),
                "illuminance": bool(st.session_state.favorite_illuminance),
                "radiation": bool(st.session_state.favorite_radiation),
                "data": bool(st.session_state.favorite_data),
                "length_expanded": bool(st.session_state.units_length_expanded),
                "temperature_expanded": bool(st.session_state.units_temperature_expanded),
                "mass_expanded": bool(st.session_state.units_mass_expanded),
                "area_expanded": bool(st.session_state.units_area_expanded),
                "volume_expanded": bool(st.session_state.units_volume_expanded),
                "speed_expanded": bool(st.session_state.units_speed_expanded),
                "time_expanded": bool(st.session_state.units_time_expanded),
                "pressure_expanded": bool(st.session_state.units_pressure_expanded),
                "energy_expanded": bool(st.session_state.units_energy_expanded),
                "power_expanded": bool(st.session_state.units_power_expanded),
                "force_expanded": bool(st.session_state.units_force_expanded),
                "frequency_expanded": bool(st.session_state.units_frequency_expanded),
                "angle_expanded": bool(st.session_state.units_angle_expanded),
                "density_expanded": bool(st.session_state.units_density_expanded),
                "flow_expanded": bool(st.session_state.units_flow_expanded),
                "acc_expanded": bool(st.session_state.units_acc_expanded),
                "current_expanded": bool(st.session_state.units_current_expanded),
                "voltage_expanded": bool(st.session_state.units_voltage_expanded),
                "resistance_expanded": bool(st.session_state.units_resistance_expanded),
                "illuminance_expanded": bool(st.session_state.units_illuminance_expanded),
                "radiation_expanded": bool(st.session_state.units_radiation_expanded),
                "data_expanded": bool(st.session_state.units_data_expanded),
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    else:
        if "favorite_length" not in st.session_state:
            st.session_state.favorite_length = False
        if "favorite_temperature" not in st.session_state:
            st.session_state.favorite_temperature = False
        if "favorite_mass" not in st.session_state:
            st.session_state.favorite_mass = False
        if "favorite_area" not in st.session_state:
            st.session_state.favorite_area = False
        if "favorite_volume" not in st.session_state:
            st.session_state.favorite_volume = False
        if "favorite_speed" not in st.session_state:
            st.session_state.favorite_speed = False
        if "favorite_time" not in st.session_state:
            st.session_state.favorite_time = False
        if "favorite_pressure" not in st.session_state:
            st.session_state.favorite_pressure = False
        if "favorite_energy" not in st.session_state:
            st.session_state.favorite_energy = False
        if "favorite_power" not in st.session_state:
            st.session_state.favorite_power = False
        if "favorite_force" not in st.session_state:
            st.session_state.favorite_force = False
        if "favorite_frequency" not in st.session_state:
            st.session_state.favorite_frequency = False
        if "favorite_angle" not in st.session_state:
            st.session_state.favorite_angle = False
        if "favorite_density" not in st.session_state:
            st.session_state.favorite_density = False
        if "favorite_flow" not in st.session_state:
            st.session_state.favorite_flow = False
        if "favorite_acc" not in st.session_state:
            st.session_state.favorite_acc = False
        if "favorite_current" not in st.session_state:
            st.session_state.favorite_current = False
        if "favorite_voltage" not in st.session_state:
            st.session_state.favorite_voltage = False
        if "favorite_resistance" not in st.session_state:
            st.session_state.favorite_resistance = False
        if "favorite_illuminance" not in st.session_state:
            st.session_state.favorite_illuminance = False
        if "favorite_radiation" not in st.session_state:
            st.session_state.favorite_radiation = False
        if "favorite_data" not in st.session_state:
            st.session_state.favorite_data = False
        if "units_length_expanded" not in st.session_state:
            st.session_state.units_length_expanded = False
        if "units_temperature_expanded" not in st.session_state:
            st.session_state.units_temperature_expanded = False
        if "units_mass_expanded" not in st.session_state:
            st.session_state.units_mass_expanded = False
        if "units_area_expanded" not in st.session_state:
            st.session_state.units_area_expanded = False
        if "units_volume_expanded" not in st.session_state:
            st.session_state.units_volume_expanded = False
        if "units_speed_expanded" not in st.session_state:
            st.session_state.units_speed_expanded = False
        if "units_time_expanded" not in st.session_state:
            st.session_state.units_time_expanded = False
        if "units_pressure_expanded" not in st.session_state:
            st.session_state.units_pressure_expanded = False
        if "units_energy_expanded" not in st.session_state:
            st.session_state.units_energy_expanded = False
        if "units_power_expanded" not in st.session_state:
            st.session_state.units_power_expanded = False
        if "units_force_expanded" not in st.session_state:
            st.session_state.units_force_expanded = False
        if "units_frequency_expanded" not in st.session_state:
            st.session_state.units_frequency_expanded = False
        if "units_angle_expanded" not in st.session_state:
            st.session_state.units_angle_expanded = False
        if "units_density_expanded" not in st.session_state:
            st.session_state.units_density_expanded = False
        if "units_flow_expanded" not in st.session_state:
            st.session_state.units_flow_expanded = False
        if "units_acc_expanded" not in st.session_state:
            st.session_state.units_acc_expanded = False
        if "units_current_expanded" not in st.session_state:
            st.session_state.units_current_expanded = False
        if "units_voltage_expanded" not in st.session_state:
            st.session_state.units_voltage_expanded = False
        if "units_resistance_expanded" not in st.session_state:
            st.session_state.units_resistance_expanded = False
        if "units_illuminance_expanded" not in st.session_state:
            st.session_state.units_illuminance_expanded = False
        if "units_radiation_expanded" not in st.session_state:
            st.session_state.units_radiation_expanded = False
        if "units_data_expanded" not in st.session_state:
            st.session_state.units_data_expanded = False
        # Storage may genuinely be empty on first visit; avoid extra rerun
        # so the first Enter in converter inputs is not lost.
        st.session_state.favorites_local_bootstrap_tries += 1
        st.session_state.favorites_local_bootstrapped = True

texts = RU_TEXTS if st.session_state.lang == "ru" else EN_TEXTS


def _inject_seo_meta(current_view: str, current_lang: str) -> None:
    base_url = "https://sconvert.ru"
    path_by_view = {
        "home": "/",
        "units": "/?view=units",
        "btc": "/?view=btc",
        "about": "/?view=about",
    }
    title_by_view = {
        "ru": {
            "home": "sconvert - онлайн конвертер величин, данных и BTC-инструментов",
            "units": "Конвертер единиц измерения - sconvert",
            "btc": "Bitcoin (BTC) инструменты: ключи, адреса, проверки - sconvert",
            "about": "О проекте sconvert",
        },
        "en": {
            "home": "sconvert - online converters for units, data, and BTC tools",
            "units": "Unit converter - sconvert",
            "btc": "Bitcoin (BTC) tools: keys, addresses, checks - sconvert",
            "about": "About sconvert",
        },
    }
    description_by_view = {
        "ru": {
            "home": "sconvert: конвертер единиц измерения, форматов данных и инструменты для Bitcoin.",
            "units": "Быстрый конвертер единиц: длина, масса, время, энергия, давление и другие категории.",
            "btc": "Инструменты Bitcoin: преобразование ключей и адресов, формат WIF, RIPEMD160, UTXO и транзакции.",
            "about": "Информация о проекте sconvert и назначении сервиса.",
        },
        "en": {
            "home": "sconvert: converters for measurement units, data formats, and Bitcoin tools.",
            "units": "Fast unit converter: length, mass, time, energy, pressure, and more categories.",
            "btc": "Bitcoin tools: key/address conversion, WIF format, RIPEMD160, UTXO, and transactions.",
            "about": "Information about the sconvert project and service goals.",
        },
    }
    resolved_lang = "en" if current_lang == "en" else "ru"
    resolved_view = current_view if current_view in {"home", "units", "btc", "about"} else "home"
    page_title = title_by_view[resolved_lang][resolved_view]
    page_description = description_by_view[resolved_lang][resolved_view]
    canonical_url = f"{base_url}{path_by_view[resolved_view]}"
    og_locale = "en_US" if resolved_lang == "en" else "ru_RU"
    og_image = f"{base_url}/og-image.png"

    script_payload = json.dumps(
        {
            "title": page_title,
            "description": page_description,
            "canonical": canonical_url,
            "og_locale": og_locale,
            "og_image": og_image,
            "lang": resolved_lang,
            "x_default": base_url,
        },
        ensure_ascii=False,
    )
    json_ld = json.dumps(
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "sconvert",
            "url": base_url,
            "inLanguage": ["ru", "en"],
            "description": page_description,
        },
        ensure_ascii=False,
    )
    st.markdown(
        f"""
        <script>
        (() => {{
          const data = {script_payload};
          const setMeta = (attr, key, value) => {{
            let el = document.head.querySelector(`meta[${{attr}}="${{key}}"]`);
            if (!el) {{
              el = document.createElement('meta');
              el.setAttribute(attr, key);
              document.head.appendChild(el);
            }}
            el.setAttribute('content', value);
          }};
          const setLink = (rel, href, hreflang = null) => {{
            const selector = hreflang ? `link[rel="${{rel}}"][hreflang="${{hreflang}}"]` : `link[rel="${{rel}}"]`;
            let el = document.head.querySelector(selector);
            if (!el) {{
              el = document.createElement('link');
              el.setAttribute('rel', rel);
              if (hreflang) el.setAttribute('hreflang', hreflang);
              document.head.appendChild(el);
            }}
            el.setAttribute('href', href);
          }};
          document.title = data.title;
          document.documentElement.setAttribute('lang', data.lang);
          setMeta('name', 'description', data.description);
          setMeta('name', 'robots', 'index,follow,max-image-preview:large');
          setMeta('property', 'og:type', 'website');
          setMeta('property', 'og:site_name', 'sconvert');
          setMeta('property', 'og:title', data.title);
          setMeta('property', 'og:description', data.description);
          setMeta('property', 'og:url', data.canonical);
          setMeta('property', 'og:locale', data.og_locale);
          setMeta('property', 'og:image', data.og_image);
          setMeta('name', 'twitter:card', 'summary_large_image');
          setMeta('name', 'twitter:title', data.title);
          setMeta('name', 'twitter:description', data.description);
          setMeta('name', 'twitter:image', data.og_image);
          setLink('canonical', data.canonical);
          setLink('alternate', data.x_default, 'x-default');
          setLink('alternate', data.x_default, 'ru');
          setLink('alternate', data.x_default, 'en');
          let jsonLdTag = document.head.querySelector('script[type="application/ld+json"][data-sconvert="website"]');
          if (!jsonLdTag) {{
            jsonLdTag = document.createElement('script');
            jsonLdTag.type = 'application/ld+json';
            jsonLdTag.setAttribute('data-sconvert', 'website');
            document.head.appendChild(jsonLdTag);
          }}
          jsonLdTag.textContent = {json.dumps(json_ld, ensure_ascii=False)};
        }})();
        </script>
        """,
        unsafe_allow_html=True,
    )


_inject_seo_meta(st.session_state.view, st.session_state.lang)

view_to_label = {
    "home": texts["nav.home"],
    "units": texts["nav.units"],
    # "files": texts["nav.files"],  # Temporarily hidden from menu
    "btc": texts["nav.btc"],
    "about": texts["nav.about"],
}
label_to_view = {value: key for key, value in view_to_label.items()}

st.session_state.view = render_header(st.session_state.view, st.session_state.lang, texts)

with st.container(key="mobile_trigger"):
    burger_col, logo_col = st.columns([0.55, 4.45], vertical_alignment="center")
    with burger_col:
        if st.button("✕" if st.session_state.mobile_menu_open else "☰", key="mobile_trigger_btn"):
            st.session_state.mobile_menu_open = not st.session_state.mobile_menu_open
            st.rerun()
    with logo_col:
        st.markdown('<span class="mobile-trigger-logo">sconvert</span>', unsafe_allow_html=True)

if st.session_state.mobile_menu_open:
    with st.container(key="mobile_drawer_overlay"):
        st.markdown("")
    with st.container(key="mobile_drawer"):
        selected_mobile_label = st.radio(
            "menu",
            options=list(view_to_label.values()),
            index=["home", "units", "btc", "about"].index(
                st.session_state.view if st.session_state.view in {"home", "units", "btc", "about"} else "home"
            ),
            key="mobile_drawer_menu",
        )
        selected_mobile_view = label_to_view.get(selected_mobile_label, st.session_state.view)
        if selected_mobile_view != st.session_state.view:
            st.session_state.view = selected_mobile_view
            st.session_state.mobile_menu_open = False
            st.rerun()

        if "mobile_drawer_lang" not in st.session_state:
            st.session_state.mobile_drawer_lang = st.session_state.lang == "en"
        drawer_use_english = st.toggle(
            " ",
            key="mobile_drawer_lang",
            help=f'{texts["lang.ru"]}/{texts["lang.en"]}',
        )
        selected_drawer_lang = "en" if drawer_use_english else "ru"
        if selected_drawer_lang != st.session_state.lang:
            st.session_state.lang = selected_drawer_lang
            st.rerun()

if st.session_state.show_privacy and st.session_state.view != st.session_state.privacy_origin_view:
    st.session_state.show_privacy = False

if st.session_state.show_privacy:
    render_privacy_component(texts)
else:
    if st.session_state.view == "home":
        render_home(texts)
    elif st.session_state.view == "units":
        render_units(texts)
    elif st.session_state.view == "files":
        render_files(texts)
    elif st.session_state.view == "btc":
        render_btc(texts)
    else:
        render_about(texts)

favorites_payload = json.dumps(
    {
        "length": bool(st.session_state.get("favorite_length", False)),
        "temperature": bool(st.session_state.get("favorite_temperature", False)),
        "mass": bool(st.session_state.get("favorite_mass", False)),
        "area": bool(st.session_state.get("favorite_area", False)),
        "volume": bool(st.session_state.get("favorite_volume", False)),
        "speed": bool(st.session_state.get("favorite_speed", False)),
        "time": bool(st.session_state.get("favorite_time", False)),
        "pressure": bool(st.session_state.get("favorite_pressure", False)),
        "energy": bool(st.session_state.get("favorite_energy", False)),
        "power": bool(st.session_state.get("favorite_power", False)),
        "force": bool(st.session_state.get("favorite_force", False)),
        "frequency": bool(st.session_state.get("favorite_frequency", False)),
        "angle": bool(st.session_state.get("favorite_angle", False)),
        "density": bool(st.session_state.get("favorite_density", False)),
        "flow": bool(st.session_state.get("favorite_flow", False)),
        "acc": bool(st.session_state.get("favorite_acc", False)),
        "current": bool(st.session_state.get("favorite_current", False)),
        "voltage": bool(st.session_state.get("favorite_voltage", False)),
        "resistance": bool(st.session_state.get("favorite_resistance", False)),
        "illuminance": bool(st.session_state.get("favorite_illuminance", False)),
        "radiation": bool(st.session_state.get("favorite_radiation", False)),
        "data": bool(st.session_state.get("favorite_data", False)),
        "length_expanded": bool(st.session_state.get("units_length_expanded", False)),
        "temperature_expanded": bool(st.session_state.get("units_temperature_expanded", False)),
        "mass_expanded": bool(st.session_state.get("units_mass_expanded", False)),
        "area_expanded": bool(st.session_state.get("units_area_expanded", False)),
        "volume_expanded": bool(st.session_state.get("units_volume_expanded", False)),
        "speed_expanded": bool(st.session_state.get("units_speed_expanded", False)),
        "time_expanded": bool(st.session_state.get("units_time_expanded", False)),
        "pressure_expanded": bool(st.session_state.get("units_pressure_expanded", False)),
        "energy_expanded": bool(st.session_state.get("units_energy_expanded", False)),
        "power_expanded": bool(st.session_state.get("units_power_expanded", False)),
        "force_expanded": bool(st.session_state.get("units_force_expanded", False)),
        "frequency_expanded": bool(st.session_state.get("units_frequency_expanded", False)),
        "angle_expanded": bool(st.session_state.get("units_angle_expanded", False)),
        "density_expanded": bool(st.session_state.get("units_density_expanded", False)),
        "flow_expanded": bool(st.session_state.get("units_flow_expanded", False)),
        "acc_expanded": bool(st.session_state.get("units_acc_expanded", False)),
        "current_expanded": bool(st.session_state.get("units_current_expanded", False)),
        "voltage_expanded": bool(st.session_state.get("units_voltage_expanded", False)),
        "resistance_expanded": bool(st.session_state.get("units_resistance_expanded", False)),
        "illuminance_expanded": bool(st.session_state.get("units_illuminance_expanded", False)),
        "radiation_expanded": bool(st.session_state.get("units_radiation_expanded", False)),
        "data_expanded": bool(st.session_state.get("units_data_expanded", False)),
    },
    ensure_ascii=True,
    sort_keys=True,
)
if (
    st.session_state.get("favorites_local_bootstrapped", False)
    and st.session_state.get("favorites_local_last_payload") != favorites_payload
):
    set_key = f"favorites_set_{abs(hash(favorites_payload))}"
    local_storage.setItem(favorites_storage_key, favorites_payload, key=set_key)
    st.session_state.favorites_local_last_payload = favorites_payload

render_footer(texts)

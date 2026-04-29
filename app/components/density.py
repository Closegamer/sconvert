import re
import streamlit as st
from .unit_panel import render_unit_panel_header

DENSITY_UNITS: list[tuple[str, str, float]] = [
    ("kg_m3", "units.density.kg_m3", 1.0),
    ("lb_ft3", "units.density.lb_ft3", 16.01846337396),
    ("g_cm3", "units.density.g_cm3", 1000.0),
]
SUPERSCRIPT_DIGITS = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
def _format_number(v: float) -> str:
    s=f"{v:.10e}";m,e=s.split("e");ei=int(e)
    return f"{v:.10g}" if -4<=ei<=6 else f"{float(m):.10g} × 10{str(ei).translate(SUPERSCRIPT_DIGITS)}"

def _parse_number(raw: str) -> float | None:
    n=raw.strip().replace(",", ".")
    if not n:return None
    m=re.match(r"^\s*([+-]?\d*\.?\d+)\s*\*\s*10\^\(\s*([+-]?\d+)\s*\)\s*$", n)
    if m:return float(m.group(1))*(10**int(m.group(2)))
    try:return float(n)
    except ValueError:return None

def _sync()->None:
    b=float(st.session_state.units_density_base)
    for c,_k,f in DENSITY_UNITS:st.session_state[f"units_density_{c}"]=_format_number(b/f)

def render_density_converter(texts: dict[str,str])->None:
    if "units_density_base" not in st.session_state: st.session_state.units_density_base=1000.0
    if "units_density_last_inputs" not in st.session_state: st.session_state.units_density_last_inputs={}
    keys=[f"units_density_{c}" for c,_k,_f in DENSITY_UNITS];needs=any(k not in st.session_state for k in keys)
    if not needs:
        last=st.session_state.units_density_last_inputs;cur={c:st.session_state.get(f"units_density_{c}","") for c,_k,_f in DENSITY_UNITS}
        changed=[c for c,_k,_f in DENSITY_UNITS if cur.get(c)!=last.get(c,"")]
        for ch in changed:
            p=_parse_number(cur.get(ch,""))
            if p is None:
                continue
            st.session_state.units_density_base=p*next(f for c,_k,f in DENSITY_UNITS if c==ch);needs=True
            break
    if needs:_sync()
    if "favorite_density" not in st.session_state: st.session_state.favorite_density=False
    t="favorite_density_toggle"
    if t not in st.session_state: st.session_state[t]=bool(st.session_state.favorite_density)
    tok=int(st.session_state.get("units_collapse_all_token",0));seen="units_density_seen_collapse_token";ex="units_density_expanded"
    if seen not in st.session_state: st.session_state[seen]=tok
    if ex not in st.session_state: st.session_state[ex]=False
    if tok!=int(st.session_state[seen]): st.session_state[seen]=tok;st.session_state[ex]=False
    render_unit_panel_header(
        panel_key="units_density_panel",
        title=texts["units.density.title"],
        expanded_key=ex,
        expand_button_key="units_density_expand_btn",
        favorite_toggle_key=t,
        favorite_state_key="favorite_density",
    )
    if st.session_state[ex]:
        l,r=st.columns(2,gap="small")
        for i,(c,k,_f) in enumerate(DENSITY_UNITS):
            with [l,r][i%2]: st.text_input(texts[k],key=f"units_density_{c}")
    st.session_state.units_density_last_inputs={c:st.session_state.get(f"units_density_{c}","") for c,_k,_f in DENSITY_UNITS}

import re
import streamlit as st
from .unit_panel import render_unit_panel_header

FLOW_UNITS: list[tuple[str, str, float]] = [
    ("ml_s", "units.flow.ml_s", 1e-6),
    ("l_min", "units.flow.l_min", 1e-3 / 60.0),
    ("gpm", "units.flow.gpm", 6.30901964e-5),
    ("m3_h", "units.flow.m3_h", 1.0 / 3600.0),
    ("l_s", "units.flow.l_s", 1e-3),
    ("m3_s", "units.flow.m3_s", 1.0),
]
SUPERSCRIPT_DIGITS=str.maketrans("0123456789-","⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
def _fmt(v:float)->str:
    s=f"{v:.10e}";m,e=s.split("e");ei=int(e)
    return f"{v:.10g}" if -4<=ei<=6 else f"{float(m):.10g} × 10{str(ei).translate(SUPERSCRIPT_DIGITS)}"

def _parse(raw:str)->float|None:
    n=raw.strip().replace(",",".")
    if not n:return None
    m=re.match(r"^\s*([+-]?\d*\.?\d+)\s*\*\s*10\^\(\s*([+-]?\d+)\s*\)\s*$",n)
    if m:return float(m.group(1))*(10**int(m.group(2)))
    try:return float(n)
    except ValueError:return None

def _sync()->None:
    b=float(st.session_state.units_flow_base)
    for c,_k,f in FLOW_UNITS: st.session_state[f"units_flow_{c}"]=_fmt(b/f)

def render_flow_converter(texts:dict[str,str])->None:
    if "units_flow_base" not in st.session_state: st.session_state.units_flow_base=1e-3
    if "units_flow_last_inputs" not in st.session_state: st.session_state.units_flow_last_inputs={}
    needs=any(f"units_flow_{c}" not in st.session_state for c,_k,_f in FLOW_UNITS)
    if not needs:
        last=st.session_state.units_flow_last_inputs;cur={c:st.session_state.get(f"units_flow_{c}","") for c,_k,_f in FLOW_UNITS}
        changed=[c for c,_k,_f in FLOW_UNITS if cur.get(c)!=last.get(c,"")]
        for ch in changed:
            p=_parse(cur.get(ch,""))
            if p is None:
                continue
            st.session_state.units_flow_base=p*next(f for c,_k,f in FLOW_UNITS if c==ch);needs=True
            break
    if needs:_sync()
    if "favorite_flow" not in st.session_state: st.session_state.favorite_flow=False
    t="favorite_flow_toggle"; st.session_state.setdefault(t,bool(st.session_state.favorite_flow))
    tok=int(st.session_state.get("units_collapse_all_token",0)); seen="units_flow_seen_collapse_token"; ex="units_flow_expanded"
    st.session_state.setdefault(seen,tok); st.session_state.setdefault(ex,False)
    if tok!=int(st.session_state[seen]): st.session_state[seen]=tok; st.session_state[ex]=False
    render_unit_panel_header(
        panel_key="units_flow_panel",
        title=texts["units.flow.title"],
        expanded_key=ex,
        expand_button_key="units_flow_expand_btn",
        favorite_toggle_key=t,
        favorite_state_key="favorite_flow",
    )
    if st.session_state[ex]:
        l,r=st.columns(2,gap="small")
        for i,(c,k,_f) in enumerate(FLOW_UNITS):
            with [l,r][i%2]: st.text_input(texts[k],key=f"units_flow_{c}")
    st.session_state.units_flow_last_inputs={c:st.session_state.get(f"units_flow_{c}","") for c,_k,_f in FLOW_UNITS}

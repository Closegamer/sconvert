import re
import streamlit as st
from .unit_panel import render_unit_panel_header

ACC_UNITS=[("gal","units.acc.gal",0.01),("ft_s2","units.acc.ft_s2",0.3048),("m_s2","units.acc.m_s2",1.0),("g","units.acc.g",9.80665)]
SUPERSCRIPT_DIGITS=str.maketrans("0123456789-","⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
def _fmt(v:float)->str:
    s=f"{v:.10e}";m,e=s.split("e");ei=int(e);return f"{v:.10g}" if -4<=ei<=6 else f"{float(m):.10g} × 10{str(ei).translate(SUPERSCRIPT_DIGITS)}"

def _parse(raw:str)->float|None:
    n=raw.strip().replace(",",".")
    if not n:return None
    m=re.match(r"^\s*([+-]?\d*\.?\d+)\s*\*\s*10\^\(\s*([+-]?\d+)\s*\)\s*$",n)
    if m:return float(m.group(1))*(10**int(m.group(2)))
    try:return float(n)
    except ValueError:return None

def _sync()->None:
    b=float(st.session_state.units_acc_base)
    for c,_k,f in ACC_UNITS: st.session_state[f"units_acc_{c}"]=_fmt(b/f)

def render_acceleration_converter(texts:dict[str,str])->None:
    st.session_state.setdefault("units_acc_base",1.0); st.session_state.setdefault("units_acc_last_inputs",{})
    needs=any(f"units_acc_{c}" not in st.session_state for c,_k,_f in ACC_UNITS)
    if not needs:
        last=st.session_state.units_acc_last_inputs;cur={c:st.session_state.get(f"units_acc_{c}","") for c,_k,_f in ACC_UNITS}
        changed=[c for c,_k,_f in ACC_UNITS if cur.get(c)!=last.get(c,"")]
        for ch in changed:
            p=_parse(cur.get(ch,""))
            if p is None:
                continue
            st.session_state.units_acc_base=p*next(f for c,_k,f in ACC_UNITS if c==ch); needs=True
            break
    if needs:_sync()
    st.session_state.setdefault("favorite_acc",False); t="favorite_acc_toggle"; st.session_state.setdefault(t,bool(st.session_state.favorite_acc))
    tok=int(st.session_state.get("units_collapse_all_token",0)); seen="units_acc_seen_collapse_token"; ex="units_acc_expanded"
    st.session_state.setdefault(seen,tok); st.session_state.setdefault(ex,False)
    if tok!=int(st.session_state[seen]): st.session_state[seen]=tok; st.session_state[ex]=False
    render_unit_panel_header(
        panel_key="units_acc_panel",
        title=texts["units.acc.title"],
        expanded_key=ex,
        expand_button_key="units_acc_expand_btn",
        favorite_toggle_key=t,
        favorite_state_key="favorite_acc",
    )
    if st.session_state[ex]:
        l,r=st.columns(2,gap="small")
        for i,(c,k,_f) in enumerate(ACC_UNITS):
            with [l,r][i%2]: st.text_input(texts[k],key=f"units_acc_{c}")
    st.session_state.units_acc_last_inputs={c:st.session_state.get(f"units_acc_{c}","") for c,_k,_f in ACC_UNITS}

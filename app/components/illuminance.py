import re
import streamlit as st
from .unit_panel import render_unit_panel_header
UNITS=[("lx","units.illuminance.lx",1.0),("fc","units.illuminance.fc",10.7639104167),("ph","units.illuminance.ph",10000.0)]
SUP=str.maketrans("0123456789-","⁰¹²³⁴⁵⁶⁷⁸⁹⁻")
def f(v:float)->str:
 s=f"{v:.10e}";m,e=s.split("e");i=int(e);return f"{v:.10g}" if -4<=i<=6 else f"{float(m):.10g} × 10{str(i).translate(SUP)}"
def p(r:str)->float|None:
 n=r.strip().replace(",",".")
 if not n:return None
 m=re.match(r"^\s*([+-]?\d*\.?\d+)\s*\*\s*10\^\(\s*([+-]?\d+)\s*\)\s*$",n)
 if m:return float(m.group(1))*(10**int(m.group(2)))
 try:return float(n)
 except ValueError:return None
def s()->None:
 b=float(st.session_state.units_illuminance_base)
 for c,_k,k in UNITS: st.session_state[f"units_illuminance_{c}"]=f(b/k)
def render_illuminance_converter(texts:dict[str,str])->None:
 st.session_state.setdefault("units_illuminance_base",1.0);st.session_state.setdefault("units_illuminance_last_inputs",{})
 n=any(f"units_illuminance_{c}" not in st.session_state for c,_k,_f in UNITS)
 if not n:
  last=st.session_state.units_illuminance_last_inputs;cur={c:st.session_state.get(f"units_illuminance_{c}","") for c,_k,_f in UNITS}
  ch=next((c for c,_k,_f in UNITS if cur.get(c)!=last.get(c)),None)
  if ch is not None:
   q=p(cur[ch])
   if q is not None: st.session_state.units_illuminance_base=q*next(k for c,_k,k in UNITS if c==ch);n=True
 if n:s()
 st.session_state.setdefault("favorite_illuminance",False);t="favorite_illuminance_toggle";st.session_state.setdefault(t,bool(st.session_state.favorite_illuminance))
 tok=int(st.session_state.get("units_collapse_all_token",0));seen="units_illuminance_seen_collapse_token";ex="units_illuminance_expanded"
 st.session_state.setdefault(seen,tok);st.session_state.setdefault(ex,False)
 if tok!=int(st.session_state[seen]): st.session_state[seen]=tok;st.session_state[ex]=False
 render_unit_panel_header(panel_key="units_illuminance_panel",title=texts["units.illuminance.title"],expanded_key=ex,expand_button_key="units_illuminance_expand_btn",favorite_toggle_key=t,favorite_state_key="favorite_illuminance")
 if st.session_state[ex]:
  l,r=st.columns(2,gap="small")
  for i,(c,k,_f) in enumerate(UNITS):
   with [l,r][i%2]: st.text_input(texts[k],key=f"units_illuminance_{c}")
 st.session_state.units_illuminance_last_inputs={c:st.session_state.get(f"units_illuminance_{c}","") for c,_k,_f in UNITS}

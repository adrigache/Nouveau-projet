import streamlit as st
import math


def auto_step(v):
    if v == 0:
        return 0.01
    magnitude = math.floor(math.log10(abs(v)))  # e.g. 400 → 2, 0.005 → -3
    return 10 ** (magnitude - 2)                 # 2 decades below the value


def auto_format(v):
    if v == 0:
        return "%.2f"
    magnitude = math.floor(math.log10(abs(v)))
    if magnitude >= 3:
        return "%d"        # 12 000
    elif magnitude >= 0:
        return "%.1f"      # 12.3
    elif magnitude >= -2:
        return "%.3f"      # 0.012
    else:
        return "%.4f"      # 0.000012
    

def make_selector(k, v):
    """"""
    key = f"selector_{k}"

    # Set default in session state if not present
    if key not in st.session_state:
        st.session_state[key] = v

    if isinstance(v, bool):
        return st.toggle(k, v)
        
    if isinstance(v, (int, float)):
        margin = abs(1*v) 
        min_val = 0.
        max_val = v + margin
        step = auto_step(v)
        fmt = auto_format(v)

        if isinstance(v, int) or v>100:
            v = int(v)
            min_val, max_val = int(min_val), int(max_val)
            step = max(1, int(step))
            
        return st.slider(f'{k} (v={v})', min_value=min_val, max_value=max_val, value=v, step=step, format=fmt, key=key)

    else:
        pass
    # elif isinstance(v, str):
    #     return st.select_slider(k, options=[v], value=v)

    # else:
    #     return st.text_input(k, value=str(v))  # fallback


# type: ignore


import streamlit as st

import datetime



# def add_months(d: datetime.date, months: int) -> datetime.date:
#     month = d.month - 1 + months
#     return d.replace(year=d.year + month // 12, month=month % 12 + 1, day=1)

# def months_between(d1: datetime.date, d2: datetime.date) -> int:
#     return (d2.year - d1.year) * 12 + (d2.month - d1.month)

# def fmt_month(d: datetime.date) -> str:
#     return d.strftime("%Y-%m")



def to_dt(d) -> datetime.datetime:
    """Normalize anything to datetime.datetime."""
    if hasattr(d, 'to_pydatetime'):   # pandas Timestamp
        return d.to_pydatetime().replace(day=1)
    if isinstance(d, datetime.datetime):
        return d.replace(day=1)
    if isinstance(d, datetime.date):
        return datetime.datetime(d.year, d.month, 1)
    

def date_selectors(dates: dict) -> dict:
    # t0,  t1  = dates["model"]
    # tc0, tc1 = dates["construction"]
    # top0, top1 = dates["operation"]


    t0 = to_dt(dates["model"][0])
    t1 = to_dt(dates["model"][1])
    tc0 = to_dt(dates["construction"][0])
    tc1 = to_dt(dates["construction"][1])
    top0 = to_dt(dates["operation"][0])
    top1 = to_dt(dates["operation"][1])

    
    # from dateutil.relativedelta import relativedelta
    # step = relativedelta(months=1)
    step = datetime.timedelta(days=31)
    
    m_t0, m_t1 = st.slider(
        "📅 Model period",
        min_value=t0, max_value=t1,
        value=(t0, t1),
        step=step,
        format="MMM YYYY",
        key="sel_model"
    )

    m_tc0, m_tc1 = st.slider(
        "🏗️ Construction period",
        min_value=t0, max_value=t1,
        value=(max(tc0, m_t0), min(tc1, m_t1)),
        step=step,
        format="MMM YYYY",
        key="sel_construction"
    )

    m_top0, m_top1 = st.slider(
        "⚡ Operation period",
        min_value=t0, max_value=t1,
        value=(max(top0, m_tc0), min(top1, m_t1)),
        step=step,
        format="MMM YYYY",
        key="sel_operation"
    )

    # --- Constraint checks ---
    warnings = []
    if m_tc0 < m_t0:
        warnings.append(f"Construction must start after {m_t0}")
    if m_tc1 > m_t1:
        warnings.append(f"Construction must end before {m_t1}")
    if m_top0 < m_tc1:
        warnings.append(f"Operation must start after {m_tc1}")
    if m_top1 > m_t1:
        warnings.append(f"Operation must end before {m_t1}")

    if warnings:
        st.warning("⚠️ Constraint violations:\n\n" + "\n\n".join(f"- {w}" for w in warnings))
        return None
        
    return {
        "model":        (m_t0,  m_t1),
        "construction": (m_tc0, m_tc1),
        "operation":    (m_top0, m_top1),
    }
    



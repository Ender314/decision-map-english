# -*- coding: utf-8 -*-
"""
Dimensionado (Impact Assessment) tab - Exact replica of original functionality.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config.constants import IMPACT_OPTS, IMPACT_MAP, PLAZO_ORDER, YMAX


def calculate_recommended_tiempo(relevancia_pct: float) -> str:
    """Calculate recommended time allocation based on relevance percentage."""
    if relevancia_pct <= 20:
        return "Menos de media hora"
    elif relevancia_pct <= 45:
        return "Un par de horas"
    elif relevancia_pct <= 80:
        return "Una mañana"
    else:
        return "Un par de días"


def render_dimensionado_tab():
    """Render the Dimensionado (Impact Assessment) tab - exact original functionality."""
    st.markdown('#####')
    st.markdown(
        """
        <span style="font-weight:600;">
          Estima su impacto en los diferentes plazos temporales
          <span style="cursor:help;" title="Impacto = Diferencia entre mejor escenario y peor escenario">ⓘ</span>
        </span>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('#####')

    col1, col2, col3 = st.columns(3)
    with col1:
        st.select_slider("Corto", options=IMPACT_OPTS, key="impacto_corto", 
                         label_visibility="collapsed")
    with col2:
        st.select_slider("Medio", options=IMPACT_OPTS, key="impacto_medio",
                         label_visibility="collapsed")
    with col3:
        st.select_slider("Largo", options=IMPACT_OPTS, key="impacto_largo",
                         label_visibility="collapsed")

    # Recompute df + AUC with possibly updated selections
    impacto_corto = st.session_state["impacto_corto"]
    impacto_medio = st.session_state["impacto_medio"]
    impacto_largo = st.session_state["impacto_largo"]
    df = pd.DataFrame([
        {"Plazo": "corto", "Impacto": impacto_corto, "Impacto_num": IMPACT_MAP[impacto_corto]},
        {"Plazo": "medio", "Impacto": impacto_medio, "Impacto_num": IMPACT_MAP[impacto_medio]},
        {"Plazo": "largo", "Impacto": impacto_largo, "Impacto_num": IMPACT_MAP[impacto_largo]},
    ])
    y = df["Impacto_num"].tolist()
    auc = (y[0] + 2*y[1] + y[2]) / 2
    max_auc = YMAX * 2
    t = 0 if max_auc == 0 else auc / max_auc
    relevancia_pct = round(100 * t, 0)

    # Color calculation (exact original logic)
    def lerp(a, b, tt): 
        return int(a + (b - a) * tt)
    
    if t <= 0.5:
        t2 = t / 0.5
        r = lerp(0, 255, t2)
        g = lerp(176, 192, t2)
        b = lerp(80, 0, t2)
    else:
        t2 = (t - 0.5) / 0.5
        r = lerp(255, 192, t2)
        g = lerp(192, 0, t2)
        b = 0
    
    line_color = f"rgb({r},{g},{b})"
    fill_color = f"rgba({r},{g},{b},0.35)"

    # Plotly (exact original)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Plazo"], y=df["Impacto_num"], customdata=df["Impacto"],
        mode="lines+markers", line=dict(shape="spline", color=line_color),
        fill="tozeroy", fillcolor=fill_color,
        hovertemplate="Plazo: %{x}<br>Impacto: %{customdata}<extra></extra>",
        name="Relevancia"
    ))
    fig.update_layout(
        margin=dict(l=70, r=20, t=20, b=20), height=360,
        xaxis=dict(title="Plazo", categoryorder="array", categoryarray=PLAZO_ORDER, zeroline=False),
        yaxis=dict(
            title="Impacto", range=[0, YMAX], autorange=False, fixedrange=True,
            tickmode="array", tickvals=[0, 5, 10, 15],
            showticklabels=False, showgrid=True, zeroline=False
        ),
        hovermode="x unified",
    )
    fig.update_yaxes(ticks="")
    st.plotly_chart(fig, use_container_width=True)

    # Relevance display (exact original)
    st.markdown(
        f"""
        <div style="text-align: center; margin-top: 10px;">
            <div style="font-size: 2em;">{int(relevancia_pct)}</div>
            <div style="font-size: 1.2em; font-weight: 600;">Relevancia estimada</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write('##')
    st.markdown('¿Cuánto tiempo crees que deberías dedicarle <u>toda tu atención</u> a esta decisión?', unsafe_allow_html=True)

    # Calculate recommended tiempo based on relevancia (exact original logic)
    recommended_tiempo = calculate_recommended_tiempo(relevancia_pct)
    
    # Only auto-update if user hasn't manually overridden the selection
    if not st.session_state.get("tiempo_user_override", False):
        if st.session_state.get("tiempo") != recommended_tiempo:
            st.session_state["tiempo"] = recommended_tiempo
    
    # Use a callback to detect manual changes (exact original)
    def on_tiempo_change():
        # Check if the new value is different from the recommendation
        if st.session_state["tiempo_widget"] != recommended_tiempo:
            st.session_state["tiempo_user_override"] = True
        st.session_state["tiempo"] = st.session_state["tiempo_widget"]
    
    st.select_slider(
        "Asignación de tiempo",
        options=["Menos de media hora", "Un par de horas", "Una mañana", "Un par de días"],
        value=st.session_state.get("tiempo", "Menos de media hora"),
        key="tiempo_widget",
        label_visibility="collapsed",
        on_change=on_tiempo_change
    )
    
    # Show recommendation hint if user has overridden (exact original)
    if st.session_state.get("tiempo_user_override", False) and st.session_state.get("tiempo") != recommended_tiempo:
        st.info(f"💡 En base a la relevancia estimada ({int(relevancia_pct)}), se recomienda: **{recommended_tiempo}**")
    
    return relevancia_pct

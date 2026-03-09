# -*- coding: utf-8 -*-
"""
Dimensionado (Impact Assessment) tab - Exact replica of original functionality.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config.constants import IMPACT_OPTS, IMPACT_MAP, PLAZO_ORDER, YMAX
from utils.calculations import calculate_relevance_percentage, calculate_recommended_time
from utils.visualizations import create_impact_chart
from utils.performance import monitor_performance
from utils.ui_helpers import help_tip, get_tooltip


@monitor_performance("render_dimensionado_tab")
def render_dimensionado_tab():
    """Render the Dimensionado (Impact Assessment) tab."""
    st.markdown("### 📐 ¿Cómo de importante es esta decisión?")
    st.markdown(
        f"""
        <span style="font-weight:600;">
          Estima su impacto en el corto, medio y largo plazo
          {help_tip(get_tooltip('impacto'))}
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

    # Use cached calculation for relevance percentage
    impacto_corto = st.session_state["impacto_corto"]
    impacto_medio = st.session_state["impacto_medio"]
    impacto_largo = st.session_state["impacto_largo"]
    
    # Calculate relevance using cached function
    relevancia_pct = calculate_relevance_percentage(
        impacto_corto, impacto_medio, impacto_largo, IMPACT_MAP
    )
    
    # Create DataFrame for visualization
    df = pd.DataFrame([
        {"Plazo": "corto", "Impacto": impacto_corto, "Impacto_num": IMPACT_MAP[impacto_corto]},
        {"Plazo": "medio", "Impacto": impacto_medio, "Impacto_num": IMPACT_MAP[impacto_medio]},
        {"Plazo": "largo", "Impacto": impacto_largo, "Impacto_num": IMPACT_MAP[impacto_largo]},
    ])

    # Use cached visualization function
    fig = create_impact_chart(df, relevancia_pct)
    st.plotly_chart(fig, width="stretch")

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
    st.markdown(f'¿Cuánto tiempo crees que deberías dedicarle <u>toda tu atención</u> a esta decisión? {help_tip(get_tooltip("tiempo"))}', unsafe_allow_html=True)

    # Calculate recommended tiempo based on relevancia (uses shared calculation)
    recommended_tiempo = calculate_recommended_time(relevancia_pct)
    
    # Only auto-update if user hasn't manually overridden the selection
    if not st.session_state.get("tiempo_user_override", False):
        if st.session_state.get("tiempo") != recommended_tiempo:
            st.session_state["tiempo"] = recommended_tiempo
        # Keep the widget key in sync too. If `tiempo_widget` already exists,
        # Streamlit will prioritize it over the `value=` argument below.
        if st.session_state.get("tiempo_widget") != recommended_tiempo:
            st.session_state["tiempo_widget"] = recommended_tiempo
    
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
    
    # Contextual help - placed after content where confusion might arise
    st.markdown("")
    with st.expander("*\"¿Qué estoy midiendo aquí? ¿Impacto de qué?\"*", expanded=False):
        st.markdown("""
        **El impacto determina cuánto análisis necesitas.**
        
        - **Decisión de bajo impacto** → Análisis rápido (menos pestañas, menos tiempo)
        - **Decisión de alto impacto** → Análisis profundo (más herramientas, más rigor)
        
        *Ejemplo: Contratar a alguien tiene impacto medio a corto plazo (onboarding), alto a medio plazo (productividad), y potencialmente crítico a largo plazo (cultura, liderazgo).*
        """)
    
    return relevancia_pct

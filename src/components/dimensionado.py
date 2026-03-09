# -*- coding: utf-8 -*-
"""
Dimensionado (Impact Assessment) tab - Exact replica of original functionality.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config.constants import IMPACT_OPTS, IMPACT_MAP, PLAZO_ORDER, YMAX, TIME_OPTIONS
from utils.calculations import calculate_relevance_percentage, calculate_recommended_time
from utils.visualizations import create_impact_chart
from utils.performance import monitor_performance
from utils.ui_helpers import help_tip, get_tooltip


@monitor_performance("render_dimensionado_tab")
def render_dimensionado_tab():
    """Render the Dimensionado (Impact Assessment) tab."""
    st.markdown("### 📐 How important is this decision?")
    st.markdown(
        f"""
        <span style="font-weight:600;">
          Estimate its impact in the short, medium, and long term
          {help_tip(get_tooltip('impacto'))}
        </span>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('#####')

    col1, col2, col3 = st.columns(3)
    with col1:
        st.select_slider("Short", options=IMPACT_OPTS, key="impacto_corto",
                         label_visibility="collapsed")
    with col2:
        st.select_slider("Medium", options=IMPACT_OPTS, key="impacto_medio",
                         label_visibility="collapsed")
    with col3:
        st.select_slider("Long", options=IMPACT_OPTS, key="impacto_largo",
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
        {"Plazo": "short", "Impacto": impacto_corto, "Impacto_num": IMPACT_MAP[impacto_corto]},
        {"Plazo": "medium", "Impacto": impacto_medio, "Impacto_num": IMPACT_MAP[impacto_medio]},
        {"Plazo": "long", "Impacto": impacto_largo, "Impacto_num": IMPACT_MAP[impacto_largo]},
    ])

    # Use cached visualization function
    fig = create_impact_chart(df, relevancia_pct)
    st.plotly_chart(fig, width="stretch")

    # Relevance display (exact original)
    st.markdown(
        f"""
        <div style="text-align: center; margin-top: 10px;">
            <div style="font-size: 2em;">{int(relevancia_pct)}</div>
            <div style="font-size: 1.2em; font-weight: 600;">Estimated relevance</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write('##')
    st.markdown(f'How much focused time should you dedicate to this decision? {help_tip(get_tooltip("tiempo"))}', unsafe_allow_html=True)

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
        "Time allocation",
        options=TIME_OPTIONS,
        value=st.session_state.get("tiempo", TIME_OPTIONS[0]),
        key="tiempo_widget",
        label_visibility="collapsed",
        on_change=on_tiempo_change
    )
    
    # Show recommendation hint if user has overridden (exact original)
    if st.session_state.get("tiempo_user_override", False) and st.session_state.get("tiempo") != recommended_tiempo:
        st.info(f"💡 Based on the estimated relevance ({int(relevancia_pct)}), recommended: **{recommended_tiempo}**")
    
    # Contextual help - placed after content where confusion might arise
    st.markdown("")
    with st.expander("*\"What am I measuring here? Impact of what?\"*", expanded=False):
        st.markdown("""
        **Impact determines how much analysis you need.**
        
        - **Low-impact decision** -> Quick analysis (fewer tabs, less time)
        - **High-impact decision** -> Deep analysis (more tools, more rigor)
        
        *Example: Hiring someone can have medium short-term impact (onboarding), high medium-term impact (productivity), and potentially critical long-term impact (culture, leadership).*
        """)
    
    return relevancia_pct

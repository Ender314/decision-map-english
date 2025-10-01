# -*- coding: utf-8 -*-
"""
Dimensionado (Impact Assessment) tab component for Lambda Pro.
Handles temporal impact assessment and time allocation.
"""

import streamlit as st
import pandas as pd

from config.constants import IMPACT_OPTS, IMPACT_MAP, PLAZO_ORDER
from utils.calculations import calculate_relevance_percentage, calculate_recommended_time
from utils.visualizations import create_impact_chart


def render_dimensionado_tab():
    """Render the Dimensionado (Impact Assessment) tab."""
    
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

    # Impact assessment sliders
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

    # Get current impact values
    impacto_corto = st.session_state["impacto_corto"]
    impacto_medio = st.session_state["impacto_medio"]
    impacto_largo = st.session_state["impacto_largo"]
    
    # Create dataframe for visualization
    df = pd.DataFrame([
        {"Plazo": "corto", "Impacto": impacto_corto, "Impacto_num": IMPACT_MAP[impacto_corto]},
        {"Plazo": "medio", "Impacto": impacto_medio, "Impacto_num": IMPACT_MAP[impacto_medio]},
        {"Plazo": "largo", "Impacto": impacto_largo, "Impacto_num": IMPACT_MAP[impacto_largo]},
    ])
    
    # Calculate relevance percentage
    relevance_pct = calculate_relevance_percentage(
        impacto_corto, impacto_medio, impacto_largo, IMPACT_MAP
    )

    # Create and display impact chart
    fig = create_impact_chart(df, relevance_pct)
    st.plotly_chart(fig, use_container_width=True)

    # Display relevance percentage
    st.markdown(
        f"""
        <div style="text-align: center; margin-top: 10px;">
            <div style="font-size: 2em;">{int(relevance_pct)}</div>
            <div style="font-size: 1.2em; font-weight: 600;">Relevancia estimada</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Time allocation section
    st.write('##')
    st.markdown('¿Cuánto tiempo crees que deberías dedicarle <u>toda tu atención</u> a esta decisión?', 
                unsafe_allow_html=True)

    # Calculate recommended time based on relevance
    recommended_time = calculate_recommended_time(relevance_pct)
    
    # Only auto-update if user hasn't manually overridden the selection
    if not st.session_state.get("tiempo_user_override", False):
        if st.session_state.get("tiempo") != recommended_time:
            st.session_state["tiempo"] = recommended_time
    
    # Use a callback to detect manual changes
    def on_tiempo_change():
        # Check if the new value is different from the recommendation
        if st.session_state["tiempo_widget"] != recommended_time:
            st.session_state["tiempo_user_override"] = True
        st.session_state["tiempo"] = st.session_state["tiempo_widget"]
    
    # Time allocation selector
    from config.constants import TIME_OPTIONS
    st.select_slider(
        "Asignación de tiempo",
        options=TIME_OPTIONS,
        value=st.session_state.get("tiempo", "Menos de media hora"),
        key="tiempo_widget",
        label_visibility="collapsed",
        on_change=on_tiempo_change
    )
    
    # Show recommendation hint if user has overridden
    if (st.session_state.get("tiempo_user_override", False) and 
        st.session_state.get("tiempo") != recommended_time):
        st.info(f"💡 En base a la relevancia estimada ({int(relevance_pct)}), se recomienda: **{recommended_time}**")
    
    return relevance_pct  # Return for use by other components

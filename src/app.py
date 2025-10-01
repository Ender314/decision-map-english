# -*- coding: utf-8 -*-
"""
Lambda Pro - Corporate Decision Analysis Tool
Main Streamlit application with modular architecture.

Run with: streamlit run src/app.py
"""

import streamlit as st
import sys
import os

# Add src directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.constants import (
    APP_NAME, APP_ICON, TAB_DIMENSIONADO, TAB_ALTERNATIVAS, TAB_OBJETIVO, 
    TAB_PRIORIDADES, TAB_INFO, TAB_EVAL, TAB_SCENARIOS, TAB_RESULTADOS
)
from utils.data_manager import initialize_session_defaults
from utils.calculations import get_sections_for_time
from components.dimensionado import render_dimensionado_tab
from components.alternativas import render_alternativas_tab
from components.prioridades import render_prioridades_tab
from components.evaluacion import render_evaluacion_tab
from components.informacion import render_informacion_tab
from components.scenarios import render_scenarios_tab
from components.resultados import render_resultados_tab
from components.sidebar import render_sidebar

# Configure Streamlit page
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    initial_sidebar_state="collapsed",
)

# Initialize session state
initialize_session_defaults()

# Header section
st.markdown('')
st.text_area(
    "Descripción de la decisión",
    key="decision",
    placeholder="Describe y sintetiza la decisión a analizar",
    label_visibility="collapsed",
)
st.markdown('#')

# Handle redirect after import
if st.session_state.get("redirect_to_first_tab", False):
    st.session_state["redirect_to_first_tab"] = False
    st.info("✅ Datos importados. Comenzando desde el primer paso...")

# Dynamic tabs based on time allocation
from config.constants import ALL_SECTIONS
sections = get_sections_for_time(st.session_state.get("tiempo", "Menos de media hora"), ALL_SECTIONS)
tabs = st.tabs(sections)
tab_map = {name: tab for name, tab in zip(sections, tabs)}

# Render tabs
relevance_pct = 0

# Dimensionado tab
if TAB_DIMENSIONADO in tab_map:
    with tab_map[TAB_DIMENSIONADO]:
        relevance_pct = render_dimensionado_tab()

# Alternativas tab  
if TAB_ALTERNATIVAS in tab_map:
    with tab_map[TAB_ALTERNATIVAS]:
        render_alternativas_tab()

# Objetivo tab
if TAB_OBJETIVO in tab_map:
    with tab_map[TAB_OBJETIVO]:
        st.text_area(
            "Objetivo",
            key="objetivo",
            placeholder="¿Cuál es el objetivo último por el nos enfrentamos a esta decisión?",
            label_visibility="collapsed",
        )
        st.markdown('')
        st.markdown('Sin un objetivo claro, no hay criterio para evaluar alternativas')

# Prioridades tab
if TAB_PRIORIDADES in tab_map:
    with tab_map[TAB_PRIORIDADES]:
        render_prioridades_tab()

# Información tab
if TAB_INFO in tab_map:
    with tab_map[TAB_INFO]:
        render_informacion_tab()

# Evaluación tab
if TAB_EVAL in tab_map:
    with tab_map[TAB_EVAL]:
        render_evaluacion_tab()

# Scenarios tab
if TAB_SCENARIOS in tab_map:
    with tab_map[TAB_SCENARIOS]:
        render_scenarios_tab()

# Resultados tab
if TAB_RESULTADOS in tab_map:
    with tab_map[TAB_RESULTADOS]:
        render_resultados_tab()

# Render sidebar
render_sidebar()

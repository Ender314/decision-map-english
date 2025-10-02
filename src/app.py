# -*- coding: utf-8 -*-
# streamlit run "src\app.py"
# streamlit run "src\app.py" --port 8501
# python -m streamlit run "src\app.py"
"""
Lambda Pro - Simplified Modular Version (Phase 1.5)
Balanced approach: organized components without over-engineering.
"""

import streamlit as st
import sys
import os

# Add src directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Simple imports - no complex managers or generic systems
from config.constants import (
    APP_NAME, APP_ICON, TAB_DIMENSIONADO, TAB_ALTERNATIVAS, TAB_OBJETIVO, 
    TAB_PRIORIDADES, TAB_INFO, TAB_EVAL, TAB_SCENARIOS, TAB_RESULTADOS, ALL_SECTIONS
)
from utils.calculations import get_sections_for_time
from components.dimensionado import render_dimensionado_tab
from components.alternativas import render_alternativas_tab
from components.objetivo import render_objetivo_tab
from components.prioridades import render_prioridades_tab
from components.informacion import render_informacion_tab
from components.evaluacion import render_evaluacion_tab
from components.scenarios import render_scenarios_tab
from components.resultados import render_resultados_tab
from components.sidebar import render_sidebar

# Configure Streamlit page
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    initial_sidebar_state="collapsed",
)

# Simple session state initialization - no complex manager
def init_session_state():
    """Initialize session state with simple defaults."""
    defaults = {
        # Impact assessment
        "impacto_corto": "bajo",
        "impacto_medio": "medio", 
        "impacto_largo": "bajo",
        
        # Core data
        "decision": "",
        "estrategia_corporativa": "",
        "objetivo": "",
        "tiempo": "Menos de media hora",
        "tiempo_user_override": False,  # Track if user manually changed tiempo
        "alts": [],
        "priorities": [],
        
        # Information
        "past_decisions": [],
        "kpis": [],
        "timeline_items": [],
        "stakeholders": [],
        "quantitative_notes": "",
        "qualitative_notes": "",
        
        # MCDA
        "mcda_criteria": [
            {"name": "Impacto estratégico", "weight": 0.5},
            {"name": "Urgencia", "weight": 0.5},
        ],
        "mcda_scores": {},
        "mcda_scores_df": None,
        
        # Scenarios
        "scenarios": {},
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Initialize
init_session_state()

# Handle pending import (before any widgets are created)
if st.session_state.get("_pending_import", False):
    json_data = st.session_state.get("_import_data", {})
    if json_data:
        from utils.data_manager import parse_date_string
        
        # Import core data
        st.session_state["decision"] = json_data.get("decision", "")
        st.session_state["estrategia_corporativa"] = json_data.get("estrategia_corporativa", "")
        st.session_state["objetivo"] = json_data.get("objetivo", "")
        
        # Import impact data
        impacto = json_data.get("impacto", {})
        st.session_state["impacto_corto"] = impacto.get("corto", "bajo")
        st.session_state["impacto_medio"] = impacto.get("medio", "medio")
        st.session_state["impacto_largo"] = impacto.get("largo", "bajo")
        
        # Import time allocation
        asignacion = json_data.get("asignacion_tiempo", {})
        st.session_state["tiempo"] = asignacion.get("tiempo", "Menos de media hora")
        st.session_state["tiempo_user_override"] = asignacion.get("tiempo_user_override", False)
        
        # Import alternatives
        st.session_state["alts"] = json_data.get("alternativas", [])
        
        # Import priorities
        st.session_state["priorities"] = json_data.get("prioridades", [])
        
        # Import information
        info = json_data.get("informacion", {})
        st.session_state["past_decisions"] = info.get("past_decisions", [])
        st.session_state["kpis"] = info.get("kpis", [])
        
        # Parse timeline dates
        timeline_items = info.get("timeline_items", [])
        for item in timeline_items:
            if item.get("date"):
                item["date"] = parse_date_string(item["date"])
        st.session_state["timeline_items"] = timeline_items
        
        st.session_state["stakeholders"] = info.get("stakeholders", [])
        st.session_state["quantitative_notes"] = info.get("quantitative_notes", "")
        st.session_state["qualitative_notes"] = info.get("qualitative_notes", "")
        
        # Import MCDA data
        mcda = json_data.get("mcda", {})
        st.session_state["mcda_criteria"] = mcda.get("criteria", [])
        st.session_state["mcda_scores"] = mcda.get("scores", {})
        
        # Import scenarios
        scenarios_data = json_data.get("scenarios", [])
        scenarios_dict = {}
        for scenario in scenarios_data:
            # Generate a simple ID based on alternativa name
            alt_name = scenario.get("alternativa", "")
            # Find matching alternative ID
            alt_id = None
            for alt in st.session_state["alts"]:
                if alt["text"] == alt_name:
                    alt_id = alt["id"]
                    break
            
            if alt_id:
                scenarios_dict[alt_id] = {
                    "name": alt_name,
                    "best_desc": scenario.get("best_desc", ""),
                    "worst_desc": scenario.get("worst_desc", ""),
                    "best_score": scenario.get("best_score", 7.0),
                    "worst_score": scenario.get("worst_score", 2.0),
                    "p_best": scenario.get("p_best", 0.5),
                    "p_best_pct": scenario.get("p_best_pct", 50),
                    "ev": scenario.get("EV", 0)
                }
        
        st.session_state["scenarios"] = scenarios_dict
        
        # Set redirect flag
        st.session_state["redirect_to_first_tab"] = True
        
        # Clear import flags
        st.session_state["_pending_import"] = False
        st.session_state["_import_data"] = {}

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
sections = get_sections_for_time(st.session_state.get("tiempo", "Menos de media hora"), ALL_SECTIONS)
tabs = st.tabs(sections)
tab_map = {name: tab for name, tab in zip(sections, tabs)}

# Render tabs - simple and direct
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
        render_objetivo_tab()

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

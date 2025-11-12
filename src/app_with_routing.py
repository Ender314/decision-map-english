# -*- coding: utf-8 -*-
# streamlit run "src\app_with_routing.py"
# streamlit run "src\app_with_routing.py" --port 8501
# python -m streamlit run "src\app_with_routing.py"
"""
Lambda Pro - Integrated Version with Landing Page Routing
Includes both landing page and main application with seamless navigation.
"""

import streamlit as st
import sys
import os

# Add src directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Simple imports - no complex managers or generic systems
from config.constants import (
    APP_NAME, APP_ICON, TAB_DIMENSIONADO, TAB_ALTERNATIVAS, TAB_OBJETIVO, 
    TAB_PRIORIDADES, TAB_INFO, TAB_EVAL, TAB_SCENARIOS, TAB_RESULTADOS, ALL_SECTIONS,
    TAB_DISPLAY_NAMES
)
from utils.calculations import get_sections_for_time
from utils.session_manager import init_session_state
from utils.performance import show_performance_debug, optimize_session_state
from components.dimensionado import render_dimensionado_tab
from components.alternativas import render_alternativas_tab
from components.objetivo import render_objetivo_tab
from components.prioridades import render_prioridades_tab
from components.informacion import render_informacion_tab
from components.evaluacion import render_evaluacion_tab
from components.scenarios import render_scenarios_tab
from components.resultados import render_resultados_tab
from components.sidebar import render_sidebar
from components.landing_page import render_landing_page
from components.offer_page import render_offer_page

# Configure Streamlit page
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed", # No funciona por usar en mi caso por usar 'render page' como función o algo así
)

# Conditional sidebar visibility based on user preference
if not st.session_state.get("show_sidebar", False):
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="collapsedControl"] {
            display: none;
        }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state using optimized manager
init_session_state()

# Initialize routing state with URL parameter support
if "current_page" not in st.session_state:
    # Check URL parameters for direct routing
    url_page = st.query_params.get("page")
    if url_page == "app":
        st.session_state["current_page"] = "app"
    elif url_page == "offer":
        st.session_state["current_page"] = "offer"
    else:
        st.session_state["current_page"] = "landing"  # Default to landing page

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
        
        # Set redirect flag and switch to app
        st.session_state["redirect_to_first_tab"] = True
        st.session_state["current_page"] = "app"
        
        # Clear import flags
        st.session_state["_pending_import"] = False
        st.session_state["_import_data"] = {}


def render_main_app():
    """Render the main Lambda Pro application."""
    # Navigation bar for app pages
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 🏠", key="nav_to_landing", help="Return to landing page"):
            st.session_state["current_page"] = "landing"
            st.query_params.clear()  # Remove URL parameters
            st.rerun()
    
    with col2:
        st.markdown(f"<h2 style='text-align: center; margin: 0;'>{APP_ICON} {APP_NAME}</h2>", unsafe_allow_html=True)
    
    with col3:
        # Sidebar toggle button
        if st.button("⚙️", key="toggle_sidebar", help="Show/hide export/import options", type="secondary"):
            st.session_state["show_sidebar"] = not st.session_state.get("show_sidebar", False)
            st.rerun()
    
    st.markdown("---")

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
    
    # Create display names with emojis for visual tabs
    display_sections = [TAB_DISPLAY_NAMES.get(section, section) for section in sections]
    tabs = st.tabs(display_sections)
    
    # Map internal names to tabs (keeps logic intact)
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

    # Render sidebar if visible
    if st.session_state.get("show_sidebar", False):
        render_sidebar()

    # Performance monitoring and optimization (only in debug mode)
    try:
        debug_mode = st.secrets.get("debug_mode", False)
    except:
        debug_mode = False

    if debug_mode or st.query_params.get("debug") == "true":
        show_performance_debug()

    # Periodic session state optimization
    if st.session_state.get("_app_run_count", 0) % 10 == 0:
        optimize_session_state()

    # Increment run counter for periodic optimization
    st.session_state["_app_run_count"] = st.session_state.get("_app_run_count", 0) + 1


# Main routing logic
current_page = st.session_state.get("current_page", "landing")

if current_page == "landing":
    render_landing_page()
elif current_page == "offer":
    render_offer_page()
elif current_page == "app":
    render_main_app()
else:
    render_landing_page()  # Default fallback

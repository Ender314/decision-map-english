# -*- coding: utf-8 -*-
# streamlit run "src\app_with_routing.py"
# streamlit run "src\app_with_routing.py" --port 8501
# python -m streamlit run "src\app_with_routing.py"
"""
Decision Map - Strategic Decision Analysis Tool.
Includes landing page, offer page, and main application with seamless navigation.
"""

import streamlit as st
import sys
import os

# Add src directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Simple imports - no complex managers or generic systems
from config.constants import (
    APP_NAME, APP_ICON, TAB_DIMENSIONADO, TAB_ALTERNATIVAS, TAB_OBJETIVO, 
    TAB_PRIORIDADES, TAB_INFO, TAB_EVAL, TAB_SCENARIOS,
    TAB_RESULTADOS, TAB_RIESGOS, TAB_RETRO,
    TAB_INFORME, ALL_SECTIONS, MONITORING_SECTIONS, TAB_DISPLAY_NAMES
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
from components.risk_analysis import render_risk_analysis_tab, count_active_risks
from components.retro import render_retro_tab, count_triggered_tripwires
from components.informe import render_informe_tab
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

# IMPORTANT: Do NOT use CSS to hide/show Streamlit components dynamically!
# CSS-based hiding (e.g., display:none on [data-testid="stSidebar"]) causes browser
# reconnection issues that result in complete session state loss.
# Instead, use conditional Python rendering: if show_sidebar: render_sidebar()
# See render_main_app() line ~175 for the correct pattern.

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
# Uses unified import_json_data from data_manager as single source of truth
if st.session_state.get("_pending_import", False):
    json_data = st.session_state.get("_import_data", {})
    if json_data:
        from utils.data_manager import import_json_data
        
        # Use unified import function with routing enabled
        import_json_data(json_data, navigate_to_app=True, show_redirect_message=True)
        
        # Clear import flags
        st.session_state["_pending_import"] = False
        st.session_state["_import_data"] = {}
        
        # Force a fresh render so widgets initialize from imported session state
        # Without this, Streamlit's widget state reconciliation may use stale
        # values from the previous run, overriding the imported data.
        st.rerun()


def _render_import_gate():
    """Render the import sub-screen on the welcome gate."""
    import json
    from utils.data_manager import validate_json_structure, import_excel_data

    st.markdown("### 📂 Import saved analysis")
    st.markdown("Load a previously exported JSON or Excel file.")
    st.markdown("")

    uploaded = st.file_uploader(
        "Select file",
        type=["json", "xlsx", "xls"],
        key="_gate_file_uploader",
    )

    if uploaded is not None:
        ext = uploaded.name.rsplit(".", 1)[-1].lower()

        if ext == "json":
            try:
                json_data = json.loads(uploaded.read().decode("utf-8"))
                is_valid, error_msg = validate_json_structure(json_data)
                if not is_valid:
                    st.error(f"❌ Invalid JSON: {error_msg}")
                else:
                    if st.button("🔄 Import JSON", width="stretch"):
                        st.session_state["_import_data"] = json_data
                        st.session_state["_pending_import"] = True
                        st.session_state["_show_import_gate"] = False
                        st.session_state["_skip_welcome"] = True
                        st.rerun()
            except json.JSONDecodeError:
                st.error("❌ File does not contain valid JSON")
            except Exception as e:
                st.error(f"❌ Error reading JSON: {str(e)}")

        elif ext in ["xlsx", "xls"]:
            if st.button("🔄 Import Excel", width="stretch"):
                try:
                    success, message = import_excel_data(uploaded)
                    if success:
                        st.session_state["_show_import_gate"] = False
                        st.session_state["_skip_welcome"] = True
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                except Exception as e:
                    st.error(f"❌ Error importing Excel: {str(e)}")

    st.markdown("")
    if st.button("← Back", key="back_from_import_gate"):
        st.session_state["_show_import_gate"] = False
        st.rerun()


def _render_template_selector_guard(render_template_selector) -> bool:
    """Regression guard: template selector must be reachable from any app state.

    Keep this check before welcome/main branching so sidebar "Cargar Plantilla"
    never becomes a no-op when the session already has data.
    """
    if not st.session_state.get("show_template_selector", False):
        return False

    render_template_selector()
    st.markdown("")
    if st.button("← Volver", key="back_from_templates"):
        st.session_state["show_template_selector"] = False
        st.rerun()
    return True


def _tab_reset_diag_enabled() -> bool:
    """Return True when tab-reset diagnostics are enabled."""
    return (
        str(st.query_params.get("diag_tabs", "")).lower() == "true"
        or bool(st.session_state.get("_diag_tab_reset", False))
    )


def _record_tab_diag(stage: str, extra: dict = None) -> None:
    """Append a lightweight diagnostic snapshot for tab reset analysis."""
    if not _tab_reset_diag_enabled():
        return

    snapshot = {
        "stage": stage,
        "run": int(st.session_state.get("_app_run_count", 0)),
        "current_page": st.session_state.get("current_page"),
        "tiempo": st.session_state.get("tiempo"),
        "tiempo_user_override": st.session_state.get("tiempo_user_override"),
        "impacto": {
            "corto": st.session_state.get("impacto_corto"),
            "medio": st.session_state.get("impacto_medio"),
            "largo": st.session_state.get("impacto_largo"),
        },
        "flags": {
            "show_template_selector": st.session_state.get("show_template_selector", False),
            "_skip_welcome": st.session_state.get("_skip_welcome", False),
            "_pending_import": st.session_state.get("_pending_import", False),
            "_template_loaded": st.session_state.get("_template_loaded", False),
        },
        "load_diag": {
            "source": st.session_state.get("_diag_last_load_source"),
            "run_index": st.session_state.get("_diag_post_load_run_index"),
            "marker": st.session_state.get("_diag_last_load_marker"),
        },
    }
    if extra:
        snapshot.update(extra)

    log = st.session_state.get("_diag_tab_reset_log", [])
    log.append(snapshot)
    st.session_state["_diag_tab_reset_log"] = log[-80:]


def _advance_post_load_diag_counter() -> None:
    """Track runs immediately after load operations for one-time reset diagnosis."""
    if not _tab_reset_diag_enabled():
        return
    if not st.session_state.get("_diag_last_load_source"):
        return

    idx = int(st.session_state.get("_diag_post_load_run_index", 0)) + 1
    st.session_state["_diag_post_load_run_index"] = idx
    _record_tab_diag("post_load_run", {"post_load_index": idx})


def render_main_app():
    """Render the main Decision Map application."""
    from components.templates import render_template_selector, get_template_list
    
    # Initialize app mode if not set
    if "app_mode" not in st.session_state:
        st.session_state["app_mode"] = "analysis"  # "analysis" or "monitoring"
    
    # Check if this is a fresh session (no data yet) and show welcome
    has_data = (
        st.session_state.get("decision", "").strip() or 
        len([a for a in st.session_state.get("alts", []) if a.get("text", "").strip()]) > 0
    )
    show_welcome = not has_data and not st.session_state.get("_skip_welcome", False)

    _advance_post_load_diag_counter()
    _record_tab_diag(
        "render_main_app_start",
        {
            "has_data": bool(has_data),
            "show_welcome": bool(show_welcome),
        },
    )
    
    # Navigation bar for app pages
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        if st.button("← 🏠", key="nav_to_landing", help="Back to landing page"):
            st.session_state["current_page"] = "landing"
            st.query_params.clear()  # Remove URL parameters
            st.rerun()
    
    with col2:
        st.markdown(f"<h2 style='text-align: center; margin: 0;'>{APP_ICON} {APP_NAME}</h2>", unsafe_allow_html=True)
    
    with col3:
        # Sidebar toggle button
        if st.button("⚙️", key="toggle_sidebar", help="Show/hide export/import options", type="secondary"):
            st.session_state["show_sidebar"] = not st.session_state.get("show_sidebar", False)
    
    st.markdown("---")
    
    # Keep a stable UI slot for transient status messages so tab identity
    # does not shift between consecutive reruns.
    status_slot = st.container()

    with status_slot:
        if st.session_state.get("_template_loaded", False):
            template_name = st.session_state.get("_loaded_template_name", "")
            st.success(f"✅ Template loaded: **{template_name}**. Explore the tabs to review sample data.")
            st.session_state["_template_loaded"] = False
            st.session_state["_loaded_template_name"] = ""

    # Regression guard: keep template selector globally reachable.
    if _render_template_selector_guard(render_template_selector):
        return
    
    # Show welcome gate for new users — blocks main app until user chooses
    if show_welcome:
        # Import sub-screen
        if st.session_state.get("_show_import_gate", False):
            _render_import_gate()
            return
        
        # Main welcome screen
        st.markdown(f"### 👋 Welcome to {APP_NAME}!")
        st.markdown("*Your assistant for making strategic decisions with clarity and confidence.*")
        st.markdown("")
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("📝 Start from scratch", width="stretch", help="Create a new empty analysis"):
                st.session_state["_skip_welcome"] = True
                st.rerun()
        with col_b:
            if st.button("📋 View sample templates", width="stretch", type="primary", help="Load a template to understand how it works"):
                st.session_state["show_template_selector"] = True
                st.rerun()
        with col_c:
            if st.button("📂 Import saved analysis", width="stretch", help="Load a previously exported JSON or Excel file"):
                st.session_state["_show_import_gate"] = True
                st.rerun()
        return

    # Time mode badge
    tiempo = st.session_state.get("tiempo", "Less than 30 minutes")
    tiempo_badges = {
        "Less than 30 minutes": ("⚡ Quick analysis", "#38a169"),
        "A couple of hours": ("⏱️ Standard analysis", "#3182ce"),
        "One morning": ("📊 Detailed analysis", "#805ad5"),
        "A couple of days": ("🔬 Deep analysis", "#c53030")
    }
    badge_text, badge_color = tiempo_badges.get(tiempo, ("⏱️ Analysis", "#718096"))
    
    # Calculate essential path progress (4 steps: Describe -> Alternatives -> Priorities -> Evaluation)
    has_description = bool(st.session_state.get("decision", "").strip())
    has_alts = len([a for a in st.session_state.get("alts", []) if a.get("text", "").strip()]) >= 2
    has_priorities = len([p for p in st.session_state.get("priorities", []) if p.get("text", "").strip()]) >= 2
    has_scores = st.session_state.get("mcda_scores") and any(
        scores for scores in st.session_state.get("mcda_scores", {}).values() if scores
    )
    
    # Step status: done (✓), current (→), pending (○)
    def step_icon(done, is_next):
        if done:
            return "✓"
        elif is_next:
            return "→"
        return "○"
    
    # Determine current step (1=Describe, 2=Alternativas, 3=Prioridades, 4=Evaluación)
    if not has_description:
        current_step = 1
    elif not has_alts:
        current_step = 2
    elif not has_priorities:
        current_step = 3
    elif not has_scores:
        current_step = 4
    else:
        current_step = 5  # All done
    
    # Build visual path icons
    step1_icon = step_icon(has_description, current_step == 1)
    step2_icon = step_icon(has_alts, current_step == 2)
    step3_icon = step_icon(has_priorities, current_step == 3)
    step4_icon = step_icon(has_scores, current_step == 4)
    
    # Colors for steps
    def step_style(done, is_current):
        if done:
            return "color: #38a169; font-weight: 600;"
        elif is_current:
            return "color: #3182ce; font-weight: 600;"
        return "color: #a0aec0;"
    
    # Display time badge and essential path
    col_badge, col_path = st.columns([1, 2])
    with col_badge:
        st.markdown(f"""
        <div style="display: inline-block; background: {badge_color}; color: white; padding: 0.3rem 0.8rem; 
                    border-radius: 15px; font-size: 0.85rem; font-weight: 500;">
            {badge_text}
        </div>
        """, unsafe_allow_html=True)
    with col_path:
        st.markdown(f"""
        <div style="text-align: right; font-size: 0.85rem; font-family: monospace;">
            <span style="{step_style(has_description, current_step == 1)}">{step1_icon} Describe</span>
            <span style="color: #cbd5e0;"> → </span>
            <span style="{step_style(has_alts, current_step == 2)}">{step2_icon} Alternatives</span>
            <span style="color: #cbd5e0;"> → </span>
            <span style="{step_style(has_priorities, current_step == 3)}">{step3_icon} Priorities</span>
            <span style="color: #cbd5e0;"> → </span>
            <span style="{step_style(has_scores, current_step == 4)}">{step4_icon} Evaluation</span>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("")

    # Header section - Decision description (shown in both modes)
    st.text_area(
        "Decision description",
        key="decision",
        placeholder="Describe and summarize the decision to analyze",
        label_visibility="collapsed",
    )
    
    # Contextual help for navigation - placed after decision description
    with st.expander("*\"Do I need to complete everything in order? Can I skip tabs?\"*", expanded=False):
        st.markdown("""
        **Only 3 tabs are required:** Alternatives -> Priorities -> Evaluation
        
        - The other tabs are **optional** and appear based on your decision's impact
        - You can move across tabs, but **Results** appear only after completing Evaluation
        - If you change alternatives or priorities later, evaluation updates automatically
        """)
    
    st.markdown('#')

    # Handle redirect after import in the same fixed status slot.
    with status_slot:
        if st.session_state.get("redirect_to_first_tab", False):
            st.session_state["redirect_to_first_tab"] = False
            st.info("✅ Data imported. Starting from the first step...")

    # Parent tabs gated by tiempo
    tiempo_levels = ["Less than 30 minutes", "A couple of hours", "One morning", "A couple of days"]
    tiempo_idx = tiempo_levels.index(tiempo) if tiempo in tiempo_levels else 0

    show_seguimiento = tiempo_idx >= 1  # "A couple of hours" onwards
    show_informe = tiempo_idx >= 3      # "A couple of days" only

    triggered = count_triggered_tripwires()
    monitoring_label = "📈 Monitoring" if triggered == 0 else f"📈 Monitoring 🔴 {triggered}"
    
    # Remember which sub-tab user was on
    if "_analysis_tab_idx" not in st.session_state:
        st.session_state["_analysis_tab_idx"] = 0
    if "_monitoring_tab_idx" not in st.session_state:
        st.session_state["_monitoring_tab_idx"] = 0
    
    # Build parent tab list dynamically
    parent_tab_labels = ["🎛️ Analysis"]
    if show_seguimiento:
        parent_tab_labels.append(monitoring_label)
    if show_informe:
        parent_tab_labels.append("📋 Report")

    _record_tab_diag(
        "before_parent_tabs",
        {
            "tiempo_idx": int(tiempo_idx),
            "show_seguimiento": bool(show_seguimiento),
            "show_informe": bool(show_informe),
            "parent_tab_labels": list(parent_tab_labels),
        },
    )

    parent_tabs = st.tabs(parent_tab_labels)
    
    tab_idx = 0
    with parent_tabs[tab_idx]:
        render_analysis_view()
    
    if show_seguimiento:
        tab_idx += 1
        with parent_tabs[tab_idx]:
            render_monitoring_view()
    
    if show_informe:
        tab_idx += 1
        with parent_tabs[tab_idx]:
            render_informe_tab()
    
    # Render sidebar if visible (works in both modes)
    if st.session_state.get("show_sidebar", False):
        render_sidebar()

    # Performance monitoring and optimization (only in debug mode)
    try:
        debug_mode = st.secrets.get("debug_mode", False)
    except:
        debug_mode = False

    if debug_mode or st.query_params.get("debug") == "true":
        show_performance_debug()

    # Periodic session state optimization (skip first render to avoid wiping
    # freshly-initialized widget state before first user interaction).
    run_count = st.session_state.get("_app_run_count", 0)
    if run_count > 0 and run_count % 10 == 0:
        _record_tab_diag("before_optimize_session")
        optimize_session_state()
        _record_tab_diag(
            "after_optimize_session",
            {
                "cleanup_removed": st.session_state.get("_diag_cleanup_last_removed", []),
            },
        )

    if _tab_reset_diag_enabled():
        with st.expander("🧪 Tab Reset Diagnostics", expanded=False):
            st.caption("Activa con ?diag_tabs=true para registrar snapshots por rerun.")
            st.json(st.session_state.get("_diag_tab_reset_log", [])[-15:])

    # Increment run counter for periodic optimization
    st.session_state["_app_run_count"] = st.session_state.get("_app_run_count", 0) + 1


def render_analysis_view():
    """Render the analysis phase tabs."""
    # Dynamic tabs based on time allocation
    sections = get_sections_for_time(st.session_state.get("tiempo", "Less than 30 minutes"), ALL_SECTIONS)
    
    # Create display names with emojis for visual tabs
    display_sections = [TAB_DISPLAY_NAMES.get(section, section) for section in sections]
    _record_tab_diag(
        "analysis_tab_topology",
        {
            "analysis_sections": list(sections),
            "analysis_display_sections": list(display_sections),
        },
    )
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

    # Unified scenarios tab
    if TAB_SCENARIOS in tab_map:
        with tab_map[TAB_SCENARIOS]:
            render_scenarios_tab()

    # Resultados tab
    if TAB_RESULTADOS in tab_map:
        with tab_map[TAB_RESULTADOS]:
            render_resultados_tab()


def render_monitoring_view():
    """Render the monitoring phase view with timeline and tabs."""
    from components.monitoring_timeline import render_monitoring_timeline

    # Keep a stable UI slot before tabs so dynamic timeline content changes
    # (tripwires/results/risks) do not remount the monitoring tabs.
    timeline_slot = st.container()
    with timeline_slot:
        render_monitoring_timeline()

    st.markdown("---")
    
    # Monitoring tabs
    display_sections = [TAB_DISPLAY_NAMES.get(section, section) for section in MONITORING_SECTIONS]
    _record_tab_diag(
        "monitoring_tab_topology",
        {
            "monitoring_sections": list(MONITORING_SECTIONS),
            "monitoring_display_sections": list(display_sections),
        },
    )
    tabs = st.tabs(display_sections)
    
    tab_map = {name: tab for name, tab in zip(MONITORING_SECTIONS, tabs)}
    
    # Riesgos tab
    if TAB_RIESGOS in tab_map:
        with tab_map[TAB_RIESGOS]:
            render_risk_analysis_tab()
    
    # Retrospectiva tab
    if TAB_RETRO in tab_map:
        with tab_map[TAB_RETRO]:
            render_retro_tab()


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

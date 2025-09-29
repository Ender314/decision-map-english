# python -m streamlit run ".\Lambda Pro desarrollo.py"


 
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import uuid, json
from datetime import datetime, date

 
# ------------------ CONSTANTS (one source of truth) ------------------
Tab_Dimensionado  = "Dimensionado"
Tab_Alternativas = "Alternativas"
Tab_Objetivo  = "Objetivo"
Tab_Prioridades  = "Prioridades"
Tab_Info = "Información"
Tab_Eval = "Evaluación"
Tab_Resultados  = "Resultados"
Tab_Scenarios = "Scenario planning"
 
# Insert the new tab in the flow
ALL_SECTIONS = [
    Tab_Dimensionado, Tab_Info, Tab_Alternativas, Tab_Objetivo, Tab_Prioridades,
    Tab_Eval, Tab_Scenarios, Tab_Resultados
]
 
IMPACT_OPTS = ["bajo", "medio", "alto", "crítico"]
IMPACT_MAP  = {"bajo": 0, "medio": 5, "alto": 10, "crítico": 15}
PLAZO_ORDER = ["corto", "medio", "largo"]
YMAX = max(IMPACT_MAP.values())  # 15
 
# ------------------ HEADER ------------------
# st.title("Flujo de Decisiones Corporativas")

# Configure Streamlit page
st.set_page_config(
    page_title="Lambda Pro",
    page_icon="⚡",
    # layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown('')
 
st.text_area(
    "Descripción de la decisión",
    key="decision",
    placeholder="Describe y sintetiza la decisión a analizar",
    label_visibility="collapsed",
)
st.markdown('#')

# ------------------ SIDEBAR IMPORT FUNCTIONALITY ------------------
with st.sidebar:
    st.markdown("### 📥 Importar Datos")
    st.markdown("Restaura una sesión previa desde un archivo JSON exportado.")
    
    def validate_json_structure(data):
        """Validate that JSON has the expected structure from this app"""
        required_keys = ["meta", "decision", "impacto", "alternativas", "asignacion_tiempo", 
                       "objetivo", "prioridades", "informacion", "mcda", "scenarios"]
        
        # Check top-level structure
        for key in required_keys:
            if key not in data:
                return False, f"Falta la clave requerida: '{key}'"
        
        # Check meta information
        if not isinstance(data.get("meta"), dict):
            return False, "Estructura 'meta' inválida"
        
        if data["meta"].get("app") != "Lambda Pro":
            return False, f"Este JSON no es de Lambda Pro (app: {data['meta'].get('app')})"
        
        # Check critical structures
        if not isinstance(data.get("alternativas"), list):
            return False, "Estructura 'alternativas' debe ser una lista"
        
        if not isinstance(data.get("prioridades"), list):
            return False, "Estructura 'prioridades' debe ser una lista"
        
        if not isinstance(data.get("informacion"), dict):
            return False, "Estructura 'informacion' debe ser un objeto"
        
        return True, "Estructura válida"
    
    def parse_date_string(date_str):
        """Convert ISO date string back to date object"""
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str).date()
        except (ValueError, TypeError):
            return None
    
    def import_json_data(data):
        """Import JSON data into session state, clearing existing data"""
        
        # Clear existing session state (keep only essential streamlit keys)
        keys_to_preserve = [k for k in st.session_state.keys() if k.startswith('FormSubmitter:')]
        current_state = {k: st.session_state[k] for k in keys_to_preserve}
        st.session_state.clear()
        st.session_state.update(current_state)
        
        # Import basic data
        st.session_state["decision"] = data.get("decision", "")
        
        # Import impacto data
        impacto = data.get("impacto", {})
        st.session_state["impacto_corto"] = impacto.get("corto", "bajo")
        st.session_state["impacto_medio"] = impacto.get("medio", "medio")
        st.session_state["impacto_largo"] = impacto.get("largo", "bajo")
        
        # Import tiempo data
        tiempo_data = data.get("asignacion_tiempo", {})
        if isinstance(tiempo_data, str):  # Handle old format
            st.session_state["tiempo"] = tiempo_data
            st.session_state["tiempo_user_override"] = False
        else:
            st.session_state["tiempo"] = tiempo_data.get("tiempo", "Menos de media hora")
            st.session_state["tiempo_user_override"] = tiempo_data.get("tiempo_user_override", False)
        
        # Import objetivo
        st.session_state["objetivo"] = data.get("objetivo", "")
        
        # Import alternativas (ensure they have IDs)
        alts = data.get("alternativas", [])
        imported_alts = []
        for alt in alts:
            if isinstance(alt, str):  # Handle old format (text only)
                imported_alts.append({"id": str(uuid.uuid4()), "text": alt})
            else:  # New format with ID
                imported_alts.append({"id": alt.get("id", str(uuid.uuid4())), "text": alt.get("text", "")})
        st.session_state["alts"] = imported_alts
        
        # Import prioridades (ensure they have IDs)
        priors = data.get("prioridades", [])
        imported_priors = []
        for prior in priors:
            if isinstance(prior, str):  # Handle old format (text only)
                imported_priors.append({"id": str(uuid.uuid4()), "text": prior})
            else:  # New format with ID
                imported_priors.append({"id": prior.get("id", str(uuid.uuid4())), "text": prior.get("text", "")})
        st.session_state["priorities"] = imported_priors
        
        # Import informacion data
        info = data.get("informacion", {})
        
        # KPIs
        kpis = info.get("kpis", [])
        imported_kpis = []
        for kpi in kpis:
            imported_kpis.append({
                "id": kpi.get("id", str(uuid.uuid4())),
                "name": kpi.get("name", kpi.get("nombre", "")),  # Handle both formats
                "value": kpi.get("value", kpi.get("valor", "")),
                "unit": kpi.get("unit", kpi.get("unidad", ""))
            })
        st.session_state["kpis"] = imported_kpis
        
        # Timeline items
        timeline = info.get("timeline_items", info.get("timeline", []))  # Handle both formats
        imported_timeline = []
        for item in timeline:
            imported_timeline.append({
                "id": item.get("id", str(uuid.uuid4())),
                "event": item.get("event", item.get("evento", "")),
                "date": parse_date_string(item.get("date", item.get("fecha")))
            })
        st.session_state["timeline_items"] = imported_timeline
        
        # Stakeholders
        stakeholders = info.get("stakeholders", [])
        imported_stakeholders = []
        for stakeholder in stakeholders:
            imported_stakeholders.append({
                "id": stakeholder.get("id", str(uuid.uuid4())),
                "name": stakeholder.get("name", stakeholder.get("nombre", "")),
                "opinion": stakeholder.get("opinion", "")
            })
        st.session_state["stakeholders"] = imported_stakeholders
        
        # Notes
        st.session_state["quantitative_notes"] = info.get("quantitative_notes", info.get("notas_cuantitativas", ""))
        st.session_state["qualitative_notes"] = info.get("qualitative_notes", info.get("notas_cualitativas", ""))
        
        # Import MCDA data
        mcda = data.get("mcda", {})
        st.session_state["mcda_criteria"] = mcda.get("criteria", [
            {"name": "Impacto estratégico", "weight": 0.5},
            {"name": "Urgencia", "weight": 0.5}
        ])
        st.session_state["mcda_scores"] = mcda.get("scores", {})
        
        # Import scenarios (convert to proper format)
        scenarios_data = data.get("scenarios", [])
        imported_scenarios = {}
        for scenario in scenarios_data:
            # Find corresponding alt_id from imported alternativas
            alt_name = scenario.get("alternativa", "")
            alt_id = None
            for alt in imported_alts:
                if alt["text"] == alt_name:
                    alt_id = alt["id"]
                    break
            
            if alt_id:
                imported_scenarios[alt_id] = {
                    "name": scenario.get("alternativa", ""),
                    "best_desc": scenario.get("best_desc", ""),
                    "best_score": scenario.get("best_score", 7.0),
                    "worst_desc": scenario.get("worst_desc", ""),
                    "worst_score": scenario.get("worst_score", 2.0),
                    "p_best": scenario.get("p_best", 0.5),
                    "p_best_pct": scenario.get("p_best_pct", 50)
                }
        st.session_state["scenarios"] = imported_scenarios
    
    # File uploader
    uploaded_file = st.file_uploader(
        # "Selecciona archivo JSON",
        "",
        type=['json'],
        help="Solo archivos JSON exportados desde Lambda Pro",
        accept_multiple_files=False
    )
    
    if uploaded_file is not None:
        try:
            # Read and parse JSON
            json_data = json.loads(uploaded_file.read().decode('utf-8'))
            
            # Validate structure
            is_valid, message = validate_json_structure(json_data)
            
            if not is_valid:
                st.error(f"❌ **Error**: {message}")
                st.info("💡 Usa un archivo JSON exportado desde Lambda Pro")
            else:
                # Show preview information
                st.success("✅ **Archivo válido**")
                
                meta = json_data.get("meta", {})
                st.metric("Fecha", meta.get("exported_at", "N/A")[:10])
                st.metric("Alternativas", len(json_data.get("alternativas", [])))
                st.metric("Prioridades", len(json_data.get("prioridades", [])))
                
                # Warning and confirmation
                st.warning("⚠️ Importar eliminará los datos actuales")
                
                # Confirmation button
                if st.button("🔄 Confirmar Importación", type="primary", use_container_width=True):
                    try:
                        # Show loading animation
                        with st.spinner("⏳ Importando datos..."):
                            import time
                            time.sleep(0.5)  # Brief pause for visual feedback
                            import_json_data(json_data)
                        
                        # Success feedback with balloons animation
                        st.success("✅ **¡Datos importados correctamente!**")
                        st.balloons()  # Visual celebration
                        
                        # Add session state flag to redirect to first tab
                        st.session_state["redirect_to_first_tab"] = True
                        
                        st.info("🔄 Redirigiendo al primer paso...")
                        time.sleep(1)  # Brief pause before redirect
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ **Error durante la importación**: {str(e)}")
                        st.info("💡 Verifica que el archivo JSON sea válido")
                        
        except json.JSONDecodeError as e:
            st.error(f"❌ **Error de formato JSON**: {str(e)}")
            st.info("💡 El archivo no contiene JSON válido")
        except Exception as e:
            st.error(f"❌ **Error inesperado**: {str(e)}")
    
    st.markdown("---")
 
# ------------------ SESSION DEFAULTS ------------------
st.session_state.setdefault("impacto_corto", "bajo")
st.session_state.setdefault("impacto_medio", "medio")
st.session_state.setdefault("impacto_largo", "bajo")
st.session_state.setdefault("tiempo", "Menos de media hora")
st.session_state.setdefault("tiempo_user_override", False)  # Track if user manually changed tiempo
st.session_state.setdefault("alts", [])  # list of {"id","text"}
st.session_state.setdefault("priorities", [])  # list of {"id","text"}
# Info tab data
st.session_state.setdefault("kpis", [])  # list of {"id","name","value","unit"}
st.session_state.setdefault("timeline_items", [])  # list of {"id","event","date"}
st.session_state.setdefault("stakeholders", [])  # list of {"id","name","opinion"}
st.session_state.setdefault("quantitative_notes", "")
st.session_state.setdefault("qualitative_notes", "")
# Evaluación tab data
st.session_state.setdefault("mcda_criteria", [  # name + weight (any non-negative)
    {"name": "Impacto estratégico", "weight": 0.5},
    {"name": "Urgencia", "weight": 0.5},
])
st.session_state.setdefault("mcda_scores_df", None)  # will be a DataFrame (alts × criteria)
# Planificación de escenarios
st.session_state.setdefault("scenarios", {})  # {alt_id: {name,best_desc,best_score,worst_desc,worst_score,p_best}}

 
# ------------------ UTILS ------------------
def get_sections(tiempo_value: str):
    if tiempo_value == "Menos de media hora":
        return [Tab_Dimensionado, Tab_Alternativas, Tab_Prioridades, Tab_Eval]  # (intentionally no scenarios)
    if tiempo_value == "Un par de horas":
        return [Tab_Dimensionado, Tab_Info, Tab_Alternativas, Tab_Prioridades, Tab_Eval, Tab_Scenarios, Tab_Resultados]
    return ALL_SECTIONS[:]
 
def calculate_recommended_tiempo(relevancia_pct: float) -> str:
    """Calculate recommended time allocation based on relevancia percentage"""
    if relevancia_pct <= 20:
        return "Menos de media hora"
    elif relevancia_pct <= 45:
        return "Un par de horas"
    elif relevancia_pct <= 80:
        return "Una mañana"
    else:
        return "Un par de días"
 
 
 
def add_alternative(default_text=""):
    st.session_state.alts.append({"id": str(uuid.uuid4()), "text": default_text})

def remove_alternative(alt_id):
    st.session_state.alts = [a for a in st.session_state.alts if a["id"] != alt_id]

def add_priority(default_text=""):
    st.session_state.priorities.append({"id": str(uuid.uuid4()), "text": default_text})

def remove_priority(priority_id):
    st.session_state.priorities = [p for p in st.session_state.priorities if p["id"] != priority_id]

def move_priority_up(priority_id):
    priorities = st.session_state.priorities
    for i, priority in enumerate(priorities):
        if priority["id"] == priority_id and i > 0:
            priorities[i], priorities[i-1] = priorities[i-1], priorities[i]
            break

def move_priority_down(priority_id):
    priorities = st.session_state.priorities
    for i, priority in enumerate(priorities):
        if priority["id"] == priority_id and i < len(priorities) - 1:
            priorities[i], priorities[i+1] = priorities[i+1], priorities[i]
            break

# Info tab helper functions
def add_kpi(name="", value="", unit=""):
    st.session_state.kpis.append({"id": str(uuid.uuid4()), "name": name, "value": value, "unit": unit})

def remove_kpi(kpi_id):
    st.session_state.kpis = [k for k in st.session_state.kpis if k["id"] != kpi_id]

def add_timeline_item(event="", date=None):
    st.session_state.timeline_items.append({"id": str(uuid.uuid4()), "event": event, "date": date})

def remove_timeline_item(item_id):
    st.session_state.timeline_items = [t for t in st.session_state.timeline_items if t["id"] != item_id]

def add_stakeholder(name="", opinion=""):
    st.session_state.stakeholders.append({"id": str(uuid.uuid4()), "name": name, "opinion": opinion})

def remove_stakeholder(stakeholder_id):
    st.session_state.stakeholders = [s for s in st.session_state.stakeholders if s["id"] != stakeholder_id]

# Calculation helper functions
def normalize_weights(criteria: list[dict]) -> dict[str, float]:
    """criteria = [{'name': str, 'weight': float}, ...] → {name: w_norm}"""
    w = {c["name"]: float(c.get("weight", 0.0)) for c in criteria}
    s = sum(w.values()) or 1.0
    return {k: v / s for k, v in w.items()}

def mcda_totals_and_ranking(scores_df: pd.DataFrame, criteria: list[dict]):
    """
    scores_df: rows=alternatives, cols=criteria names, values in [0..5]
    returns: (totals: pd.Series, ranking_list: list[{'alternativa','score'}])
    """
    if scores_df is None or scores_df.empty:
        return pd.Series(dtype=float), []
    w_map = normalize_weights(criteria)
    # align missing criteria to 0
    for c in w_map:
        if c not in scores_df.columns:
            scores_df[c] = 0.0
    totals = scores_df.apply(lambda row: sum(row[c] * w_map.get(c, 0.0) for c in scores_df.columns), axis=1)
    ranking = totals.sort_values(ascending=False)
    ranking_list = [{"alternativa": idx, "score": float(val)} for idx, val in ranking.items()]
    return totals, ranking_list

def scenario_ev(p_best: float, worst: float, best: float) -> float:
    """Expected value on 0–10 scale."""
    p = float(p_best)
    return p * float(best) + (1 - p) * float(worst)

# JSON-safe conversion (reusable)
def _to_native(x):
    if isinstance(x, (np.floating,)): return float(x)
    if isinstance(x, (np.integer,)):  return int(x)
    if isinstance(x, (pd.Timestamp, datetime, date)): return x.isoformat()
    if isinstance(x, pd.DataFrame):
        return {
            "columns": list(x.columns),
            "index": list(map(str, x.index)),
            "data": x.reset_index(drop=True).to_dict(orient="records"),
        }
    return x

def json_ready(obj):
    if isinstance(obj, dict):  return {k: json_ready(v) for k, v in obj.items()}
    if isinstance(obj, list):  return [json_ready(v) for v in obj]
    return _to_native(obj)

 
# ------------------ BUILD DATA FROM SESSION (safe globally) ------------------
impacto_corto = st.session_state["impacto_corto"]
impacto_medio = st.session_state["impacto_medio"]
impacto_largo = st.session_state["impacto_largo"]
 
df = pd.DataFrame([
    {"Plazo": "corto", "Impacto": impacto_corto, "Impacto_num": IMPACT_MAP[impacto_corto]},
    {"Plazo": "medio", "Impacto": impacto_medio, "Impacto_num": IMPACT_MAP[impacto_medio]},
    {"Plazo": "largo", "Impacto": impacto_largo, "Impacto_num": IMPACT_MAP[impacto_largo]},
])
 
# AUC + color (global, so Resultados can always read it)
y = df["Impacto_num"].tolist()
auc = (y[0] + 2*y[1] + y[2]) / 2
max_auc = YMAX * 2
t = 0 if max_auc == 0 else auc / max_auc
relevancia_pct = round(100 * t, 0)
 
def lerp(a, b, tt): return int(a + (b - a) * tt)
if t <= 0.5:
    t2 = t / 0.5
    r = lerp(0, 255, t2); g = lerp(176, 192, t2); b = lerp(80, 0, t2)
else:
    t2 = (t - 0.5) / 0.5
    r = lerp(255, 192, t2); g = lerp(192, 0, t2); b = 0
line_color = f"rgb({r},{g},{b})"
fill_color = f"rgba({r},{g},{b},0.35)"
 
# ------------------ HANDLE REDIRECT AFTER IMPORT ------------------
if st.session_state.get("redirect_to_first_tab", False):
    # Clear the redirect flag
    st.session_state["redirect_to_first_tab"] = False
    # Force focus on first tab by clearing any tab state
    # This will make the app show the first tab by default
    st.info("✅ Datos importados. Comenzando desde el primer paso...")

# ------------------ DYNAMIC TABS ------------------
SECTIONS = get_sections(st.session_state["tiempo"])
tabs = st.tabs(SECTIONS)
tab_map = {name: tab for name, tab in zip(SECTIONS, tabs)}
 
# ------------------ TAB: Dimensionado ------------------
if Tab_Dimensionado in tab_map:
    with tab_map[Tab_Dimensionado]:
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
        t = (0 if YMAX == 0 else auc / (YMAX * 2))
        relevancia_pct = round(100 * t, 0)
 
        # Plotly
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

        # Calculate recommended tiempo based on relevancia
        recommended_tiempo = calculate_recommended_tiempo(relevancia_pct)
        
        # Only auto-update if user hasn't manually overridden the selection
        if not st.session_state["tiempo_user_override"]:
            if st.session_state["tiempo"] != recommended_tiempo:
                st.session_state["tiempo"] = recommended_tiempo
        
        # Use a callback to detect manual changes
        def on_tiempo_change():
            # Check if the new value is different from the recommendation
            if st.session_state["tiempo_widget"] != recommended_tiempo:
                st.session_state["tiempo_user_override"] = True
            st.session_state["tiempo"] = st.session_state["tiempo_widget"]
        
        st.select_slider(
            "Asignación de tiempo",
            options=["Menos de media hora", "Un par de horas", "Una mañana", "Un par de días"],
            value=st.session_state["tiempo"],
            key="tiempo_widget",
            label_visibility="collapsed",
            on_change=on_tiempo_change
        )
        
        # Show recommendation hint if user has overridden
        if st.session_state["tiempo_user_override"] and st.session_state["tiempo"] != recommended_tiempo:
            st.info(f"💡 En base a la relevancia estimada ({int(relevancia_pct)}), se recomienda: **{recommended_tiempo}**")
        
        # Changing this slider triggers a rerun → SECTIONS will update next run.
 
# ------------------ TAB: Alternativas ------------------
if Tab_Alternativas in tab_map:
    with tab_map[Tab_Alternativas]:
        st.subheader("Alternativas posibles")
 
        if not st.session_state.alts:
            st.info("No hay alternativas todavía. Pulsa **Añadir** para crear la primera.")
        else:
            updated_alts = []
            for i, alt in enumerate(st.session_state.alts, start=1):
                c1, c2 = st.columns([6, 1])
                with c1:
                    new_text = st.text_input(
                        label=f"Alternativa {i}",
                        value=alt["text"],
                        key=f"alt_text_{alt['id']}",
                        placeholder="Describe la alternativa",
                        label_visibility="collapsed",
                    )
                with c2:
                    if st.button("🗑️", key=f"del_{alt['id']}", help="Eliminar esta alternativa", use_container_width=True):
                        remove_alternative(alt["id"])
                        st.rerun()
                # collect (don’t mutate the original item inline)
                updated_alts.append({"id": alt["id"], "text": new_text})

            # single write after loop
            st.session_state.alts = updated_alts
 
        cols_add = st.columns([1, 3])
        with cols_add[0]:
            if st.button("➕ Añadir", key="add_alternative_btn", use_container_width=True):
                add_alternative()
                st.rerun()
 
# ------------------ TAB: Objetivo ------------------
if Tab_Objetivo in tab_map:
    with tab_map[Tab_Objetivo]:
        st.text_area(
            "Objetivo",
            key="objetivo",
            placeholder="¿Cuál es el objetivo último por el nos enfrentamos a esta decisión?",
            label_visibility="collapsed",
        )
        st.markdown('')
        st.markdown('Sin un objetivo claro, no hay criterio para evaluar alternativas')
 
# ------------------ TAB: Prioridades ------------------
if Tab_Prioridades in tab_map:
    with tab_map[Tab_Prioridades]:
        # Display objetivo as read-only reference
        objetivo_text = st.session_state.get("objetivo", "").strip()
        if objetivo_text:
            st.markdown("**Objetivo**")
            st.markdown(f"*{objetivo_text}*")
            st.markdown("---")
        
        st.subheader("Prioridades")
        st.markdown("¿Qué prioridades se derivan del objetivo?")

        
        # Display existing priorities with sorting controls
        if st.session_state.priorities:
            updated_priorities = []
            for i, priority in enumerate(st.session_state.priorities, start=1):
                c1, c2, c3, c4 = st.columns([0.5, 5, 0.5, 0.5])
                with c1:
                    if i > 1 and st.button("⬆️", key=f"up_{priority['id']}", help="Mover arriba", use_container_width=True):
                        move_priority_up(priority["id"]); st.rerun()
                with c2:
                    new_text = st.text_input(
                        label=f"Prioridad {i}",
                        value=priority["text"],
                        key=f"priority_text_{priority['id']}",
                        placeholder="Our top priority is...",
                        label_visibility="collapsed",
                    )
                with c3:
                    if i < len(st.session_state.priorities) and st.button("⬇️", key=f"down_{priority['id']}", help="Mover abajo", use_container_width=True):
                        move_priority_down(priority["id"]); st.rerun()
                with c4:
                    if st.button("🗑️", key=f"del_priority_{priority['id']}", help="Eliminar esta prioridad", use_container_width=True):
                        remove_priority(priority["id"]); st.rerun()
                updated_priorities.append({"id": priority["id"], "text": new_text})

            st.session_state.priorities = updated_priorities

        # Add new priority button
        cols_add = st.columns([1, 3])
        with cols_add[0]:
            if st.button("➕ Añadir", key="add_priority_btn", use_container_width=True):
                add_priority()
                st.rerun()

        st.markdown('')

        # Warning if more than 3 priorities
        if len(st.session_state.priorities) > 3:
            st.info("💡 Demasiadas prioridades es no tenerlas")
 
# ------------------ TAB: Información ------------------
if Tab_Info in tab_map:
    with tab_map[Tab_Info]:
        # QUANTITATIVE DATA (First Section)
        st.subheader("📊 Datos Cuantitativos")
        
        # KPIs Section
        st.markdown("**KPIs Relevantes**")
        if st.session_state.kpis:
            for kpi in st.session_state.kpis:
                c1, c2, c3, c4 = st.columns([3, 2, 2, 0.5])
                with c1:
                    new_name = st.text_input(
                        "KPI",
                        value=kpi["name"],
                        key=f"kpi_name_{kpi['id']}",
                        placeholder="Nombre del KPI",
                        label_visibility="collapsed"
                    )
                    kpi["name"] = new_name
                with c2:
                    new_value = st.text_input(
                        "Valor",
                        value=kpi["value"],
                        key=f"kpi_value_{kpi['id']}",
                        placeholder="Valor",
                        label_visibility="collapsed"
                    )
                    kpi["value"] = new_value
                with c3:
                    new_unit = st.text_input(
                        "Unidad",
                        value=kpi["unit"],
                        key=f"kpi_unit_{kpi['id']}",
                        placeholder="Unidad",
                        label_visibility="collapsed"
                    )
                    kpi["unit"] = new_unit
                with c4:
                    if st.button("🗑️", key=f"del_kpi_{kpi['id']}", help="Eliminar KPI"):
                        remove_kpi(kpi["id"])
                        st.rerun()
        
        if st.button("➕ Añadir KPI", key="add_kpi_btn", use_container_width=True):
            add_kpi()
            st.rerun()
        
        st.markdown("---")
        
        # Timeline Section
        st.markdown("**Timeline Clave**")
        if st.session_state.timeline_items:
            for item in st.session_state.timeline_items:
                c1, c2, c3 = st.columns([4, 3, 0.5])
                with c1:
                    new_event = st.text_input(
                        "Evento",
                        value=item["event"],
                        key=f"timeline_event_{item['id']}",
                        placeholder="Descripción del evento",
                        label_visibility="collapsed"
                    )
                    item["event"] = new_event
                with c2:
                    new_date = st.date_input(
                        "Fecha",
                        value=item["date"],
                        key=f"timeline_date_{item['id']}",
                        label_visibility="collapsed"
                    )
                    item["date"] = new_date
                with c3:
                    if st.button("🗑️", key=f"del_timeline_{item['id']}", help="Eliminar evento"):
                        remove_timeline_item(item["id"])
                        st.rerun()
        
        if st.button("➕ Añadir Evento", key="add_timeline_btn", use_container_width=True):
            add_timeline_item()
            st.rerun()

        # st.markdown('---')

        # Timeline Chart
        if st.session_state.timeline_items:
            # Filter items with valid dates and events
            valid_items = [item for item in st.session_state.timeline_items 
                          if item["event"].strip() and item["date"] is not None]
            
            if valid_items:
                # st.markdown("**Visualización del Timeline**")
                try:
                    import pandas as pd
                    from datetime import date
                    
                    # Create dataframe for timeline with proper date handling
                    timeline_data = []
                    for item in valid_items:
                        event_date = item["date"]
                        # Convert date object to string for display if needed
                        if isinstance(event_date, date):
                            timeline_data.append({
                                "Evento": item["event"], 
                                "Fecha": event_date,
                                "FechaStr": event_date.strftime("%Y-%m-%d")
                            })
                    
                    if timeline_data:
                        timeline_df = pd.DataFrame(timeline_data)
                        
                        # Sort by date
                        timeline_df = timeline_df.sort_values("Fecha")
                        
                        # Create simple timeline chart
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=timeline_df["Fecha"],
                            y=[1] * len(timeline_df),  # All events on same horizontal line
                            mode="markers+text",
                            marker=dict(size=12, color="blue"),
                            text=timeline_df["Evento"],
                            textposition="top center",
                            hovertemplate="<b>%{text}</b><br>Fecha: %{x}<extra></extra>",
                            name="Eventos"
                        ))
                        
                        fig.update_layout(
                            height=200,
                            margin=dict(l=20, r=20, t=40, b=20),
                            xaxis=dict(title="Fecha", type="date"),
                            yaxis=dict(visible=False, range=[0.5, 1.5]),
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.info("💡 Error al generar la visualización del timeline")
        

        # KPI Dashboard Visualization
        if st.session_state.kpis and any(k["name"].strip() for k in st.session_state.kpis):
            # st.markdown("**📊 Dashboard de KPIs**")
            try:
                # Filter valid KPIs
                valid_kpis = [k for k in st.session_state.kpis if k["name"].strip()]
                
                # Create KPI cards layout
                if len(valid_kpis) <= 3:
                    cols = st.columns(len(valid_kpis))
                else:
                    # For more than 3 KPIs, create rows of 3
                    rows = (len(valid_kpis) + 2) // 3  # Ceiling division
                    for row in range(rows):
                        start_idx = row * 3
                        end_idx = min(start_idx + 3, len(valid_kpis))
                        row_kpis = valid_kpis[start_idx:end_idx]
                        cols = st.columns(len(row_kpis))
                        
                        for i, kpi in enumerate(row_kpis):
                            with cols[i]:
                                # Create KPI card
                                value_str = str(kpi["value"]) if kpi["value"] else "N/A"
                                unit_str = f" {kpi['unit']}" if kpi["unit"].strip() else ""
                                
                                st.metric(
                                    label=kpi["name"],
                                    value=f"{value_str}{unit_str}"
                                )
                
                # If 3 or fewer KPIs, display them in a single row
                if len(valid_kpis) <= 3:
                    for i, kpi in enumerate(valid_kpis):
                        with cols[i]:
                            value_str = str(kpi["value"]) if kpi["value"] else "N/A"
                            unit_str = f" {kpi['unit']}" if kpi["unit"].strip() else ""
                            
                            st.metric(
                                label=kpi["name"],
                                value=f"{value_str}{unit_str}"
                            )
                
                # Create a bar chart for numeric KPIs
                numeric_kpis = []
                for kpi in valid_kpis:
                    try:
                        if kpi["value"] and str(kpi["value"]).replace(".", "").replace("-", "").isdigit():
                            numeric_kpis.append({
                                "name": kpi["name"],
                                "value": float(kpi["value"]),
                                "unit": kpi["unit"]
                            })
                    except (ValueError, TypeError):
                        continue
                
                if len(numeric_kpis) > 1:
                    st.markdown("**Comparación de KPIs Numéricos**")
                    
                    import plotly.graph_objects as go
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=[k["name"] for k in numeric_kpis],
                        y=[k["value"] for k in numeric_kpis],
                        text=[f"{k['value']}{' ' + k['unit'] if k['unit'] else ''}" for k in numeric_kpis],
                        textposition='auto',
                        marker_color='lightblue',
                        hovertemplate="<b>%{x}</b><br>Valor: %{y}<extra></extra>"
                    ))
                    
                    fig.update_layout(
                        height=300,
                        margin=dict(l=20, r=20, t=20, b=20),
                        xaxis=dict(title="KPIs"),
                        yaxis=dict(title="Valores"),
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
            except Exception as e:
                st.info("💡 Error al generar el dashboard de KPIs")
        
        st.markdown("---")
        
        # Free-form quantitative notes
        st.text_area(
            "Notas Adicionales (Cuantitativas)",
            key="quantitative_notes",
            placeholder="Otros datos numéricos, métricas o información cuantitativa relevante...",
            height=100,
            label_visibility="collapsed"
        )
        
        st.markdown("##")
        
        # QUALITATIVE DATA (Second Section)
        st.subheader("👥 Datos Cualitativos")
        
        # Stakeholders Section
        st.markdown("**Stakeholders y Opiniones**")
        if st.session_state.stakeholders:
            for stakeholder in st.session_state.stakeholders:
                c1, c2, c3 = st.columns([3, 4, 0.5])
                with c1:
                    new_name = st.text_input(
                        "Stakeholder",
                        value=stakeholder["name"],
                        key=f"stakeholder_name_{stakeholder['id']}",
                        placeholder="Nombre/Rol",
                        label_visibility="collapsed"
                    )
                    stakeholder["name"] = new_name
                with c2:
                    new_opinion = st.text_input(
                        "Opinión",
                        value=stakeholder["opinion"],
                        key=f"stakeholder_opinion_{stakeholder['id']}",
                        placeholder="Su opinión/posición",
                        label_visibility="collapsed"
                    )
                    stakeholder["opinion"] = new_opinion
                with c3:
                    if st.button("🗑️", key=f"del_stakeholder_{stakeholder['id']}", help="Eliminar stakeholder"):
                        remove_stakeholder(stakeholder["id"])
                        st.rerun()
        
        if st.button("➕ Añadir Stakeholder", key="add_stakeholder_btn", use_container_width=True):
            add_stakeholder()
            st.rerun()
        
        st.markdown("---")
        
        # Free-form qualitative notes
        st.text_area(
            "Notas Adicionales (Cualitativas)",
            key="qualitative_notes",
            placeholder="Contexto, observaciones, feedback, análisis cualitativo u otra información relevante...",
            height=200,
            label_visibility="collapsed"
        )
 
# ------------------ TAB: Evaluación ------------------
if Tab_Eval in tab_map:
    with tab_map[Tab_Eval]:
        st.subheader("Evaluación (MCDA)")

        # --- Guards: need alternativas & prioridades ---
        alt_names = [a["text"].strip() for a in st.session_state.alts if a["text"].strip()]
        if not alt_names:
            st.info("Añade al menos una **Alternativa** en la pestaña *Alternativas* para poder evaluar.")
            st.stop()

        prioridad_names = [p["text"].strip() for p in st.session_state.priorities if p["text"].strip()]
        if not prioridad_names:
            st.info("Añade al menos una **Prioridad** en la pestaña *Prioridades* para usar como criterios.")
            st.stop()

        # --- Helper: default weights from PRIORIDADES ORDER (editable later) ---
        def default_weights_from_order(names: list[str]) -> list[float]:
            n = len(names)
            raw = list(range(n, 0, -1))  # n, n-1, ..., 1
            s = sum(raw)
            return [v / s for v in raw]

        # --- Sync criteria from Prioridades; set default weights if changed/empty ---
        current_criteria = st.session_state.get("mcda_criteria", [])
        current_names = [c.get("name", "").strip() for c in current_criteria]

        if (not current_criteria) or (current_names != prioridad_names):
            auto_w = default_weights_from_order(prioridad_names)
            st.session_state["mcda_criteria"] = [{"name": n, "weight": float(w)} for n, w in zip(prioridad_names, auto_w)]

        st.markdown("**Criterios y pesos** (cargados de *Prioridades* por orden; editables)")
        crit_df = pd.DataFrame(st.session_state.mcda_criteria)

        # Editor (names fixed; weights editable)
        crit_df = st.data_editor(
            crit_df,
            num_rows="fixed",
            column_config={
                "name": st.column_config.TextColumn("Criterio", disabled=True),
                "weight": st.column_config.NumberColumn("Peso (≥ 0)", min_value=0.0, step=0.05,
                    help="Pesos normalizados automáticamente para el cálculo"),
            },
            key="mcda_criteria_editor",
            use_container_width=True,
        )
        crit_df["name"] = crit_df["name"].astype(str).str.strip()
        st.session_state.mcda_criteria = crit_df.to_dict("records")
        crit_names = list(crit_df["name"])

        # --- Scores with select sliders (0..5 step 0.5), persisted in session ---
        st.markdown("**Puntuaciones (0–5)**")
        score_steps = [x / 2 for x in range(0, 11)]
        
        # ✅ Use setdefault for direct access like Scenario Planning
        current_scores = st.session_state.setdefault("mcda_scores", {})
        
        for alt in alt_names:
            st.markdown(f"**{alt}**")
            # ✅ Ensure alt exists in current_scores
            current_scores.setdefault(alt, {})
            
            for i in range(0, len(crit_names), 3):
                cols = st.columns(min(3, len(crit_names) - i))
                for j, c in enumerate(crit_names[i:i+3]):
                    with cols[j]:
                        key = f"score_{alt}_{c}"
                        # ✅ Direct access with fallback, similar to Scenario Planning
                        default_val = current_scores.get(alt, {}).get(c, 0.0)
                        new_val = st.select_slider(
                            c, 
                            options=score_steps, 
                            value=st.session_state.get(key, default_val),  # ✅ Use widget key for value
                            key=key
                        )
                        # ✅ Update in place
                        current_scores[alt][c] = float(new_val)
            st.markdown("")

        # DataFrame (aligned to displayed order)
        scores_df = pd.DataFrame(current_scores).T.reindex(index=alt_names, columns=crit_names, fill_value=0.0)
        st.session_state["mcda_scores_df"] = scores_df

        # --- Compute weighted totals & ranking via PURE helper ---
        totals, ranking_list = mcda_totals_and_ranking(scores_df.copy(), st.session_state.get("mcda_criteria", []))
        ranking = totals.sort_values(ascending=False).rename("Puntuación ponderada")
        result_df = pd.concat([scores_df, ranking], axis=1).loc[ranking.index]

        st.markdown("**Resultado y ranking**")
        st.dataframe(result_df.style.format(precision=2), use_container_width=True)

        # --- Bar chart (ranking) ---
        fig_rank = go.Figure()
        fig_rank.add_bar(
            x=ranking.index.tolist(),
            y=ranking.values.tolist(),
            text=[f"{v:.2f}" for v in ranking.values],
            textposition="auto",
            name="Puntuación"
        )
        fig_rank.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Alternativa",
            yaxis_title="Puntuación ponderada (0–5)",
            height=320,
            showlegend=False,
        )
        st.plotly_chart(fig_rank, use_container_width=True)

        # --- Radar (only if > 2 criterios) ---
        if len(crit_names) > 2:
            st.markdown("**Radar de puntuaciones por criterio**")
            theta = crit_names + [crit_names[0]]  # close loop
            fig_radar = go.Figure()
            for alt in alt_names:
                r_vals = scores_df.loc[alt, crit_names].tolist()
                r_vals.append(r_vals[0])
                fig_radar.add_trace(go.Scatterpolar(
                    r=r_vals,
                    theta=theta,
                    mode="lines+markers",
                    fill="toself",
                    name=alt
                ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                showlegend=True,
                height=420,
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        st.caption("Los pesos se normalizan automáticamente. La puntuación total = Σ(puntuación × peso).")

# ------------------ TAB: Scenario planning ------------------
if Tab_Scenarios in tab_map:
    with tab_map[Tab_Scenarios]:
        st.subheader("Scenario planning")

        # Need alternativas
        alts = [a for a in st.session_state.alts if a["text"].strip()]
        if not alts:
            st.info("Añade al menos una **Alternativa** en la pestaña *Alternativas* para proyectar escenarios.")
            st.stop()

        prob_steps = list(range(0, 101, 5))  # 0,5,...,100

        # ✅ Use existing state IN PLACE (no wholesale reassignment)
        current = st.session_state.setdefault("scenarios", {})

        for alt in alts:
            alt_id, alt_name = alt["id"], alt["text"].strip()
            prev = current.get(alt_id, {
                "name": alt_name, "best_desc": "", "best_score": 7.0,
                "worst_desc": "", "worst_score": 2.0, "p_best": 0.5, "p_best_pct": 50,
            })

            with st.expander(f"⚙️ {alt_name}", expanded=False, ):
                # --- Probabilidad (stable key + default from session) ---
                p_key = f"pbest_{alt_id}"
                # Row 1: Worst → Probabilidad → Best
                c1, c2, c3 = st.columns([1.8, 1.2, 1.8])
                with c1:
                    st.markdown("**Worst scenario**")
                    worst_desc = st.text_input(
                        "Descripción (worst)",
                        value=prev.get("worst_desc", ""),
                        key=f"worst_desc_{alt_id}",
                        label_visibility="collapsed",
                        placeholder="¿Qué pasa si sale mal?"
                    )
                with c2:
                    st.markdown("######")
                    default_pct = int(round(float(prev.get("p_best", 0.5)) * 100))
                    default_pct = max(0, min(100, 5 * round(default_pct / 5)))
                    p_best_pct = st.select_slider(
                        "Probabilidad de **best**",
                        options=prob_steps,
                        value=st.session_state.get(p_key, prev.get("p_best_pct", default_pct)),  # ✅
                        key=p_key,
                        label_visibility="collapsed"
                    )
                    p_best = p_best_pct / 100.0
                    
                with c3:
                    st.markdown("**Best scenario**")
                    best_desc = st.text_input(
                        "Descripción (best)",
                        value=prev.get("best_desc", ""),
                        key=f"best_desc_{alt_id}",
                        label_visibility="collapsed",
                        placeholder="¿Qué pasa si todo va muy bien?"
                    )

                # Row 2: Single range slider for Impacto (0–10)
                rng_key = f"impact_range_{alt_id}"
                default_rng = (
                    int(min(float(prev.get("worst_score", 2.0)), 10)),
                    int(min(float(prev.get("best_score", 7.0)), 10))
                )
                st.markdown("")
                worst_best = st.slider(
                    "Impacto (0–10): mínimo = worst, máximo = best",
                    min_value=0, max_value=10, step=1,
                    value=st.session_state.get(rng_key, default_rng),  # ✅
                    key=rng_key
                )
                worst_score, best_score = map(float, worst_best)

                ev = p_best * best_score + (1 - p_best) * worst_score
                # st.metric("Valor esperado (0–10)", f"{ev:.2f}")

            current[alt_id] = {
                "name": alt_name,
                "best_desc": best_desc, "best_score": best_score,
                "worst_desc": worst_desc, "worst_score": worst_score,
                "p_best": p_best, "p_best_pct": p_best_pct,
            }



        # ---- Summary DF (sorted by EV DESC) ----
        import plotly.graph_objects as go
        rows = []
        for d in current.values():
            ev = scenario_ev(d["p_best"], d["worst_score"], d["best_score"])  # <— PURE helper
            rows.append({
                "Alternativa": d["name"],
                "Worst": int(d["worst_score"]),
                "Best": int(d["best_score"]),
                "EV": ev,
                "Range": d["best_score"] - d["worst_score"],
            })
        scen_df = pd.DataFrame(rows).sort_values("EV", ascending=False)

        # --- Range bars colored by EV; highest EV ON TOP ---
        y_labels = scen_df["Alternativa"].tolist()
        fig = go.Figure()

        fig.add_bar(
            x=scen_df["Range"],
            y=scen_df["Alternativa"],
            base=scen_df["Worst"],
            orientation="h",
            marker=dict(
                color=scen_df["EV"],
                colorscale=[[0, "red"], [0.5, "yellow"], [1, "green"]],
                cmin=0, cmax=10,
                showscale=False,  # <-- removes color legend
            ),
            hovertemplate="Worst: %{base}<br>Best: %{base}+%{x}<extra></extra>",
            name="Rango (Worst→Best)",
        )

        fig.add_scatter(
            x=scen_df["EV"],
            y=scen_df["Alternativa"],
            mode="markers",
            marker=dict(size=10, symbol="diamond", color="black", line=dict(width=1)),
            name="Valor esperado",
            hovertemplate="EV: %{x:.2f}<extra></extra>",
        )

        per_item = 24
        fig.update_layout(
            xaxis=dict(title="Impacto (0–10)", range=[0, 10], zeroline=False),
            yaxis=dict(
                title="",
                categoryorder="array",
                categoryarray=y_labels,
                autorange="reversed",   # <-- ensures highest EV at the TOP

            ),
            height=max(260, int(140 + per_item * len(y_labels))),
            margin=dict(l=40, r=20, t=10, b=30),
            showlegend=True,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Resumen at the bottom
        st.markdown("**Resumen**")
        st.dataframe(
            scen_df[["Alternativa", "Worst", "Best", "EV"]].style.format({"EV": "{:.2f}"}),
            use_container_width=True
        )

        st.caption("EV = p(best) × best + (1 − p(best)) × worst. Escala 0–10.")


# ------------------ TAB: Resultados ------------------
if Tab_Resultados in tab_map:
    with tab_map[Tab_Resultados]:
        st.subheader("Resultados")
        
        # Check if we have data to show results
        alt_names = [a["text"].strip() for a in st.session_state.alts if a["text"].strip()]
        prioridad_names = [p["text"].strip() for p in st.session_state.priorities if p["text"].strip()]
        
        if alt_names and prioridad_names:
            # --- MCDA snapshot via PURE helpers ---
            crit = st.session_state.get("mcda_criteria", [])
            scores_df = st.session_state.get("mcda_scores_df", pd.DataFrame())
            _, ranking_list = mcda_totals_and_ranking(scores_df.copy(), crit)

            # --- Scenarios snapshot via PURE helper ---
            scenarios_state = st.session_state.get("scenarios", {})
            scen_rows = []
            for d in scenarios_state.values():
                ev = scenario_ev(d.get("p_best", 0.5), d.get("worst_score", 0), d.get("best_score", 0))
                scen_rows.append({
                    "alternativa": d.get("name", ""),
                    "worst_desc": d.get("worst_desc", ""),
                    "best_desc": d.get("best_desc", ""),
                    "worst_score": _to_native(d.get("worst_score")),
                    "best_score": _to_native(d.get("best_score")),
                    "p_best": _to_native(d.get("p_best")),
                    "p_best_pct": _to_native(d.get("p_best_pct")),
                    "EV": _to_native(ev),
                })

            # --- Build payload ---
            userData = {
                "meta": {
                    "exported_at": datetime.now().isoformat(),
                    "app": "Lambda Pro",
                    "version": "0.1.0",
                },
                "decision": st.session_state.get("decision", "").strip(),
                "impacto": {
                    "corto": st.session_state.get("impacto_corto"),
                    "medio": st.session_state.get("impacto_medio"),
                    "largo": st.session_state.get("impacto_largo"),
                    "relevancia_pct": int(relevancia_pct),
                },
                # ✅ Full alternativas with IDs for proper hydration
                "alternativas": [{"id": a["id"], "text": a["text"]} for a in st.session_state.alts],
                "asignacion_tiempo": {
                    "tiempo": st.session_state.get("tiempo"),
                    "tiempo_user_override": st.session_state.get("tiempo_user_override", False),  # ✅ Critical for behavior
                },
                "objetivo": st.session_state.get("objetivo", "").strip(),
                # ✅ Full prioridades with IDs for proper hydration
                "prioridades": [{"id": p["id"], "text": p["text"]} for p in st.session_state.priorities],
                "informacion": {
                    # ✅ Full objects with IDs for proper hydration
                    "kpis": [{"id": k["id"], "name": k["name"], "value": k["value"], "unit": k["unit"]}
                             for k in st.session_state.kpis],
                    "timeline_items": [{"id": t["id"], "event": t["event"], "date": (t["date"].isoformat() if t["date"] else None)}
                                       for t in st.session_state.timeline_items],
                    "stakeholders": [{"id": s["id"], "name": s["name"], "opinion": s["opinion"]}
                                     for s in st.session_state.stakeholders],
                    "quantitative_notes": st.session_state.get("quantitative_notes", "").strip(),
                    "qualitative_notes": st.session_state.get("qualitative_notes", "").strip(),
                },
                "mcda": {
                    "criteria": crit,
                    "scores": st.session_state.get("mcda_scores", {}),  # ✅ Raw scores for hydration
                    "scores_table": _to_native(scores_df) if isinstance(scores_df, pd.DataFrame) else scores_df,
                    "ranking": ranking_list,
                },
                "scenarios": scen_rows,
            }

            # --- Export Section ---
            st.markdown("### 📤 Exportar Datos")
            
            # filename from decision + timestamp
            def _slug(s: str) -> str:
                s = (s or "").strip().lower()
                allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_ "
                s = "".join(ch if ch.lower() in allowed else "-" for ch in s)
                s = "-".join(s.split())
                return s[:60] or "decision"
            fname = f"{_slug(st.session_state.get('decision',''))}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

            st.download_button(
                "⬇️ Descargar JSON",
                data=json.dumps(json_ready(userData), ensure_ascii=False, indent=2),
                file_name=fname,
                mime="application/json",
                use_container_width=True,
            )

            with st.expander("Ver datos (JSON)"):
                st.json(userData)
                
        else:
            # Show message when no data available for export
            st.info("💡 **Exportación disponible** una vez que hayas definido **Alternativas** y **Prioridades**")
            st.markdown("Completa las pestañas anteriores para generar un resumen exportable de tu análisis de decisión.")



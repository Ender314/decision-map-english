# python -m streamlit run '.\Lambda Pro desarrollo.py'
 
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import uuid, json
 
# ------------------ CONSTANTS (one source of truth) ------------------
Tab_Dimensionado  = "Dimensionado"
Tab_Alternativas = "Alternativas"
Tab_Objetivo  = "Objetivo"
Tab_Prioridades  = "Prioridades"
Tab_Info = "Información"
Tab_Eval = "Evaluación"
Tab_Resultados  = "Resultados"
 
ALL_SECTIONS = [Tab_Dimensionado, Tab_Alternativas, Tab_Objetivo, Tab_Prioridades, Tab_Info, Tab_Eval, Tab_Resultados]
 
IMPACT_OPTS = ["bajo", "medio", "alto", "crítico"]
IMPACT_MAP  = {"bajo": 0, "medio": 5, "alto": 10, "crítico": 15}
PLAZO_ORDER = ["corto", "medio", "largo"]
YMAX = max(IMPACT_MAP.values())  # 15
 
# ------------------ HEADER ------------------
# st.title("Flujo de Decisiones Corporativas")
st.markdown('')
 
st.text_area(
    "Descripción de la decisión",
    key="decision",
    placeholder="Describe y sintetiza la decisión a analizar",
    label_visibility="collapsed",
)
st.markdown('#')
 
# ------------------ SESSION DEFAULTS ------------------
st.session_state.setdefault("impacto_corto", "bajo")
st.session_state.setdefault("impacto_medio", "medio")
st.session_state.setdefault("impacto_largo", "bajo")
st.session_state.setdefault("tiempo", "Menos de media hora")
st.session_state.setdefault("tiempo_user_override", False)  # Track if user manually changed tiempo
st.session_state.setdefault("alts", [])  # list of {"id","text"}
 
# ------------------ UTILS ------------------
def get_sections(tiempo_value: str):
    if tiempo_value == "Menos de media hora":
        return [Tab_Dimensionado, Tab_Alternativas, Tab_Eval, Tab_Resultados]
    if tiempo_value == "Un par de horas":
        return [Tab_Dimensionado,Tab_Alternativas, Tab_Prioridades, Tab_Eval, Tab_Resultados]
    return ALL_SECTIONS[:]  # full flow
 
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
                             value=st.session_state["impacto_corto"], label_visibility="collapsed")
        with col2:
            st.select_slider("Medio", options=IMPACT_OPTS, key="impacto_medio",
                             value=st.session_state["impacto_medio"], label_visibility="collapsed")
        with col3:
            st.select_slider("Largo", options=IMPACT_OPTS, key="impacto_largo",
                             value=st.session_state["impacto_largo"], label_visibility="collapsed")
 
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
            xaxis=dict(title="Plazo temporal", categoryorder="array", categoryarray=PLAZO_ORDER, zeroline=False),
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
        st.markdown('¿Cuánto tiempo crees que deberías dedicarle toda tu atención a esta decisión?')

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
                    alt["text"] = new_text
                with c2:
                    if st.button("🗑️", key=f"del_{alt['id']}", help="Eliminar esta alternativa", use_container_width=True):
                        remove_alternative(alt["id"])
                        st.rerun()
 
        cols_add = st.columns([1, 3])
        with cols_add[0]:
            if st.button("➕ Añadir", use_container_width=True):
                add_alternative()
 
# ------------------ TAB: Objetivo ------------------
if Tab_Objetivo in tab_map:
    with tab_map[Tab_Objetivo]:
        st.text_area(
            "Objetivo",
            key="objetivo",
            placeholder="¿Cuál es el objetivo último por el que debes enfrentarte a esta decisión?",
            label_visibility="collapsed",
        )
 
# ------------------ TAB: Prioridades ------------------
if Tab_Prioridades in tab_map:
    with tab_map[Tab_Prioridades]:
        st.info("Espacio para definir prioridades (pendiente).")
 
# ------------------ TAB: Información ------------------
if Tab_Info in tab_map:
    with tab_map[Tab_Info]:
        st.info("Espacio para adjuntar/registrar información relevante (pendiente).")
 
# ------------------ TAB: Evaluación ------------------
if Tab_Eval in tab_map:
    with tab_map[Tab_Eval]:
        st.info("Espacio para criterios de evaluación y scoring (pendiente).")
 
# ------------------ TAB: Resultados ------------------
if Tab_Resultados in tab_map:
    with tab_map[Tab_Resultados]:
        userData = {
            "decision": st.session_state.get("decision", "").strip(),
            "impacto": {
                "corto": st.session_state["impacto_corto"],
                "medio": st.session_state["impacto_medio"],
                "largo": st.session_state["impacto_largo"],
                "relevancia_pct": int(relevancia_pct),
            },
            "alternativas": [a["text"] for a in st.session_state.alts if a["text"].strip()],
            "asignacion_tiempo": st.session_state.get("tiempo"),
            "objetivo": st.session_state.get("objetivo", "").strip(),
        }
 
        with st.expander("Ver datos (JSON)"):
            st.json(userData)
            st.download_button(
                "Descargar JSON",
                data=json.dumps(userData, ensure_ascii=False, indent=2),
                file_name="decision_userdata.json",
                mime="application/json",
                use_container_width=True,
            )
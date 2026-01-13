# -*- coding: utf-8 -*-
"""
Retrospective tab - Post-decision monitoring and learning.
Inspired by Agile retrospectives: outcomes tracking, tripwires, and lessons learned.
"""

import streamlit as st
import pandas as pd
import uuid
from datetime import date, datetime
import plotly.graph_objects as go
from config.constants import OUTCOME_ATTRIBUTION, OUTCOME_SENTIMENT, TRIPWIRE_STATUS


def count_active_tripwires() -> int:
    """Count tripwires that are active."""
    retro = st.session_state.get("retro", {})
    tripwires = retro.get("tripwires", [])
    return sum(1 for t in tripwires if t.get("status") == "activo")


def count_triggered_tripwires() -> int:
    """Count tripwires that have been triggered."""
    retro = st.session_state.get("retro", {})
    tripwires = retro.get("tripwires", [])
    return sum(1 for t in tripwires if t.get("status") == "disparado")


def render_retro_tab():
    """Render the Retrospective tab.
    
    Note: This view is intentionally decoupled from alternatives.
    """
    st.subheader("🔄 Retrospectiva")
    
    # Initialize retro if needed
    if "retro" not in st.session_state:
        st.session_state.retro = {
            "decision_date": None,
            "review_date": None,
            "chosen_alternative_id": None,
            "outcomes": [],
            "tripwires": [],
            "lessons_learned": "",
            "decision_quality_score": 3,
            "outcome_quality_score": 3
        }
    
    retro = st.session_state.retro
    
    # Decision date
    col1, col2 = st.columns(2)
    with col1:
        decision_date = st.date_input(
            "Fecha de la decisión",
            value=retro.get("decision_date") or date.today(),
            key="retro_decision_date"
        )
        retro["decision_date"] = decision_date
    
    with col2:
        review_date = st.date_input(
            "Fecha de última revisión",
            value=retro.get("review_date") or date.today(),
            key="retro_review_date"
        )
        retro["review_date"] = review_date
    
    st.markdown("---")
    
    # Tabs for different sections
    retro_tabs = st.tabs(["📈 Resultados", "⚡ Tripwires", "📝 Lecciones"])
    
    # === OUTCOMES TAB ===
    with retro_tabs[0]:
        st.markdown("### 📈 Seguimiento de Resultados")
        st.caption("Registra los resultados observados y separa lo que fue debido a la decisión vs. el azar.")
        
        outcomes = retro.get("outcomes", [])
        
        # Add new outcome
        with st.expander("➕ Registrar nuevo resultado", expanded=len(outcomes) == 0):
            with st.form("add_outcome_form", clear_on_submit=True):
                o_desc = st.text_area(
                    "¿Qué ha ocurrido?",
                    placeholder="Describe el resultado observado...",
                    key="new_outcome_desc"
                )
                
                c1, c2, c3 = st.columns(3)
                with c1:
                    o_date = st.date_input("Fecha", value=date.today(), key="new_outcome_date")
                with c2:
                    o_attr = st.selectbox(
                        "Atribución",
                        OUTCOME_ATTRIBUTION,
                        index=0,
                        key="new_outcome_attr",
                        help="¿Este resultado se debe a la decisión, al azar, o es mixto?"
                    )
                with c3:
                    o_sent = st.selectbox(
                        "Valoración",
                        OUTCOME_SENTIMENT,
                        index=1,
                        key="new_outcome_sent"
                    )
                
                o_notes = st.text_input(
                    "Notas de atribución",
                    placeholder="¿Por qué crees que se debe a la decisión/azar?",
                    key="new_outcome_notes"
                )
                
                if st.form_submit_button("Registrar resultado", type="primary"):
                    if o_desc.strip():
                        new_outcome = {
                            "id": str(uuid.uuid4()),
                            "description": o_desc.strip(),
                            "date": o_date.isoformat() if o_date else None,
                            "attribution": o_attr,
                            "attribution_notes": o_notes.strip(),
                            "sentiment": o_sent
                        }
                        retro["outcomes"].append(new_outcome)
                    else:
                        st.warning("Describe el resultado observado")
        
        # Display outcomes
        if outcomes:
            # Sort by date descending
            sorted_outcomes = sorted(
                outcomes,
                key=lambda x: x.get("date", ""),
                reverse=True
            )
            
            for outcome in sorted_outcomes:
                sent_icon = {"positivo": "✅", "neutral": "➖", "negativo": "❌"}.get(outcome.get("sentiment", "neutral"), "➖")
                attr_icon = {"decisión": "🎯", "azar": "🎲", "mixto": "🔀"}.get(outcome.get("attribution", "mixto"), "🔀")
                
                with st.expander(f"{sent_icon} {outcome['description'][:50]}... — {outcome.get('date', 'Sin fecha')}"):
                    st.markdown(f"**Descripción:** {outcome['description']}")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        st.markdown(f"**Fecha:** {outcome.get('date', 'N/A')}")
                    with c2:
                        st.markdown(f"**Atribución:** {attr_icon} {outcome.get('attribution', 'mixto')}")
                    with c3:
                        st.markdown(f"**Valoración:** {sent_icon} {outcome.get('sentiment', 'neutral')}")
                    
                    if outcome.get("attribution_notes"):
                        st.markdown(f"**Notas:** {outcome['attribution_notes']}")
                    
                    if st.button("🗑️ Eliminar", key=f"del_outcome_{outcome['id']}"):
                        retro["outcomes"] = [o for o in retro["outcomes"] if o["id"] != outcome["id"]]
            
            # Attribution summary chart
            st.markdown("---")
            st.markdown("#### 📊 Resumen de Atribución")
            
            attr_counts = {"decisión": 0, "azar": 0, "mixto": 0}
            sent_counts = {"positivo": 0, "neutral": 0, "negativo": 0}
            
            for o in outcomes:
                attr = o.get("attribution", "mixto")
                sent = o.get("sentiment", "neutral")
                if attr in attr_counts:
                    attr_counts[attr] += 1
                if sent in sent_counts:
                    sent_counts[sent] += 1
            
            c1, c2 = st.columns(2)
            
            with c1:
                # Attribution pie chart
                fig_attr = go.Figure(data=[go.Pie(
                    labels=["Decisión 🎯", "Azar 🎲", "Mixto 🔀"],
                    values=list(attr_counts.values()),
                    hole=0.4,
                    marker_colors=["#2196f3", "#9c27b0", "#ff9800"]
                )])
                fig_attr.update_layout(
                    title="Atribución de Resultados",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    showlegend=True
                )
                st.plotly_chart(fig_attr, use_container_width=True, config={"displayModeBar": False})
            
            with c2:
                # Sentiment pie chart
                fig_sent = go.Figure(data=[go.Pie(
                    labels=["Positivo ✅", "Neutral ➖", "Negativo ❌"],
                    values=list(sent_counts.values()),
                    hole=0.4,
                    marker_colors=["#4caf50", "#9e9e9e", "#f44336"]
                )])
                fig_sent.update_layout(
                    title="Valoración de Resultados",
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    showlegend=True
                )
                st.plotly_chart(fig_sent, use_container_width=True, config={"displayModeBar": False})
            
            # Insight
            decision_outcomes = attr_counts["decisión"]
            chance_outcomes = attr_counts["azar"]
            positive_outcomes = sent_counts["positivo"]
            negative_outcomes = sent_counts["negativo"]
            
            if decision_outcomes > chance_outcomes and positive_outcomes > negative_outcomes:
                st.success("💡 La mayoría de resultados positivos se atribuyen a la decisión. ¡Buena elección!")
            elif chance_outcomes > decision_outcomes and positive_outcomes > negative_outcomes:
                st.info("💡 Los resultados positivos se deben principalmente al azar. Considera si la decisión fue acertada.")
            elif negative_outcomes > positive_outcomes:
                st.warning("💡 Hay más resultados negativos que positivos. Revisa las lecciones aprendidas.")
        
        else:
            st.info("No hay resultados registrados. Añade el primer resultado arriba.")
    
    # === TRIPWIRES TAB ===
    with retro_tabs[1]:
        st.markdown("### ⚡ Tripwires (Disparadores)")
        st.caption("Define eventos o condiciones que deberían hacerte reevaluar la decisión.")
        
        tripwires = retro.get("tripwires", [])
        
        # Count active and triggered
        active_count = sum(1 for t in tripwires if t.get("status") == "activo")
        triggered_count = sum(1 for t in tripwires if t.get("status") == "disparado")
        
        if triggered_count > 0:
            st.error(f"🚨 **{triggered_count} tripwire(s) disparado(s)** — Considera reevaluar la decisión")
        
        # Add new tripwire
        with st.expander("➕ Añadir tripwire", expanded=len(tripwires) == 0):
            with st.form("add_tripwire_form", clear_on_submit=True):
                t_trigger = st.text_input(
                    "Evento/Condición disparadora *",
                    placeholder="¿Qué evento debería hacerte reconsiderar?",
                    key="new_tripwire_trigger"
                )
                
                c1, c2 = st.columns(2)
                with c1:
                    t_target_date = st.date_input(
                        "Fecha objetivo *",
                        value=date.today(),
                        key="new_tripwire_date",
                        help="¿Cuándo deberías revisar este tripwire?"
                    )
                with c2:
                    t_threshold = st.text_input(
                        "Umbral cuantitativo (opcional)",
                        placeholder="Ej: 'Ventas < 10.000€'",
                        key="new_tripwire_threshold"
                    )
                
                if st.form_submit_button("Añadir tripwire", type="primary"):
                    if t_trigger.strip():
                        new_tripwire = {
                            "id": str(uuid.uuid4()),
                            "trigger": t_trigger.strip(),
                            "target_date": t_target_date.isoformat() if t_target_date else None,
                            "threshold": t_threshold.strip(),
                            "status": "activo",
                            "triggered_date": None,
                            "action_taken": ""
                        }
                        retro["tripwires"].append(new_tripwire)
                    else:
                        st.warning("Define el evento disparador")
        
        # Display tripwires
        if tripwires:
            # Sort by target_date
            sorted_tripwires = sorted(
                tripwires,
                key=lambda x: x.get("target_date", "9999-12-31")
            )
            
            for tripwire in sorted_tripwires:
                status = tripwire.get("status", "activo")
                status_icon = {"activo": "🟢", "disparado": "🔴", "superado": "🏁"}.get(status, "🟢")
                target_date_str = tripwire.get("target_date", "Sin fecha")
                
                with st.expander(f"{status_icon} [{target_date_str}] {tripwire['trigger'][:40]}..."):
                    st.markdown(f"**Disparador:** {tripwire['trigger']}")
                    
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        # Parse existing date for the date input
                        existing_date = None
                        if tripwire.get("target_date"):
                            try:
                                existing_date = datetime.fromisoformat(tripwire["target_date"]).date()
                            except:
                                existing_date = date.today()
                        else:
                            existing_date = date.today()
                        
                        new_target_date = st.date_input(
                            "Fecha objetivo",
                            value=existing_date,
                            key=f"tw_date_{tripwire['id']}"
                        )
                        if new_target_date:
                            tripwire["target_date"] = new_target_date.isoformat()
                    
                    with c2:
                        new_status = st.selectbox(
                            "Estado",
                            TRIPWIRE_STATUS,
                            index=TRIPWIRE_STATUS.index(status),
                            key=f"tw_status_{tripwire['id']}"
                        )
                        if new_status != status:
                            tripwire["status"] = new_status
                            if new_status == "disparado" and not tripwire.get("triggered_date"):
                                tripwire["triggered_date"] = date.today().isoformat()
                    
                    with c3:
                        if tripwire.get("triggered_date"):
                            st.markdown(f"**Disparado:** {tripwire['triggered_date']}")
                    
                    if tripwire.get("threshold"):
                        st.markdown(f"**Umbral:** {tripwire['threshold']}")
                    
                    if status == "disparado":
                        action = st.text_area(
                            "Acción tomada",
                            value=tripwire.get("action_taken", ""),
                            key=f"tw_action_{tripwire['id']}",
                            placeholder="¿Qué hiciste cuando se disparó?"
                        )
                        tripwire["action_taken"] = action
                    
                    if st.button("🗑️ Eliminar", key=f"del_tw_{tripwire['id']}"):
                        retro["tripwires"] = [t for t in retro["tripwires"] if t["id"] != tripwire["id"]]
            
            # Summary metrics
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("Activos", active_count)
            m2.metric("Disparados", triggered_count, delta=f"+{triggered_count}" if triggered_count > 0 else None, delta_color="inverse")
            m3.metric("Total", len(tripwires))
        
        else:
            st.info("No hay tripwires definidos. Añade el primero arriba.")
            st.caption("💡 **Ejemplos de tripwires:**")
            st.caption("- 'Si las ventas caen más del 20% en 3 meses'")
            st.caption("- 'Si un competidor lanza un producto similar'")
            st.caption("- 'Si el equipo clave renuncia'")
    
    # === LESSONS TAB ===
    with retro_tabs[2]:
        st.markdown("### 📝 Lecciones Aprendidas")
        
        # Quality scores
        st.markdown("#### Autoevaluación")
        
        c1, c2 = st.columns(2)
        with c1:
            decision_score = st.slider(
                "Calidad de la decisión (proceso)",
                min_value=1, max_value=5, value=retro.get("decision_quality_score", 3),
                key="retro_decision_score",
                help="¿Qué tan bien seguiste un proceso de decisión riguroso?"
            )
            retro["decision_quality_score"] = decision_score
            
            if decision_score <= 2:
                st.caption("😕 Proceso mejorable")
            elif decision_score <= 3:
                st.caption("😐 Proceso aceptable")
            else:
                st.caption("😊 Buen proceso")
        
        with c2:
            outcome_score = st.slider(
                "Calidad del resultado",
                min_value=1, max_value=5, value=retro.get("outcome_quality_score", 3),
                key="retro_outcome_score",
                help="¿Qué tan buenos fueron los resultados obtenidos?"
            )
            retro["outcome_quality_score"] = outcome_score
            
            if outcome_score <= 2:
                st.caption("😕 Resultados pobres")
            elif outcome_score <= 3:
                st.caption("😐 Resultados aceptables")
            else:
                st.caption("😊 Buenos resultados")
        
        # Decision quality matrix insight
        st.markdown("---")
        if decision_score >= 4 and outcome_score >= 4:
            st.success("🏆 **Buena decisión, buen resultado** — ¡Sigue así!")
        elif decision_score >= 4 and outcome_score <= 2:
            st.info("🎲 **Buena decisión, mal resultado** — A veces el azar no acompaña. El proceso fue correcto.")
        elif decision_score <= 2 and outcome_score >= 4:
            st.warning("🍀 **Mala decisión, buen resultado** — Tuviste suerte. Mejora el proceso para el futuro.")
        elif decision_score <= 2 and outcome_score <= 2:
            st.error("⚠️ **Mala decisión, mal resultado** — Revisa qué falló en el proceso de decisión.")
        
        st.markdown("---")
        
        # Lessons learned text
        lessons = st.text_area(
            "Lecciones aprendidas",
            value=retro.get("lessons_learned", ""),
            key="retro_lessons",
            height=200,
            placeholder="¿Qué has aprendido de esta decisión?\n\n- ¿Qué harías diferente?\n- ¿Qué información te faltó?\n- ¿Qué sesgos detectaste?\n- ¿Qué funcionó bien?"
        )
        retro["lessons_learned"] = lessons
        
        # Quick prompts
        st.caption("💡 **Preguntas para reflexionar:**")
        prompts = [
            "¿Qué información hubiera cambiado mi decisión?",
            "¿Qué sesgos cognitivos pude haber tenido?",
            "¿Consulté a las personas adecuadas?",
            "¿Dediqué el tiempo apropiado al análisis?",
            "¿Qué haría diferente la próxima vez?"
        ]
        for prompt in prompts:
            st.caption(f"  • {prompt}")


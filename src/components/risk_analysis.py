# -*- coding: utf-8 -*-
"""
Risk Analysis tab - Risk inventory, ranking, and mitigation strategies.
Inspired by project management theory (avoid, transfer, mitigate, contingency).
"""

import streamlit as st
import pandas as pd
import uuid
from datetime import date
import plotly.graph_objects as go
from config.constants import (
    RISK_CATEGORIES, RISK_PROBABILITY, RISK_IMPACT, RISK_STATUS,
    RISK_PROB_MAP, RISK_IMPACT_MAP
)


def get_recommended_alternative():
    """Get the recommended alternative from scenarios/MCDA analysis."""
    from utils.calculations import mcda_totals_and_ranking
    
    # Try to get from scenarios composite ranking first
    scenarios = st.session_state.get("scenarios", {})
    mcda_scores_df = st.session_state.get("mcda_scores_df")
    mcda_criteria = st.session_state.get("mcda_criteria", [])
    alts = st.session_state.get("alts", [])
    
    if not alts:
        return None, None
    
    # Build composite ranking if we have both MCDA and scenarios
    if scenarios and mcda_scores_df is not None and not mcda_scores_df.empty:
        _, mcda_ranking = mcda_totals_and_ranking(mcda_scores_df.copy(), mcda_criteria)
        
        combined_data = []
        for alt in alts:
            alt_id = alt["id"]
            alt_name = alt["text"].strip()
            if not alt_name:
                continue
                
            scenario_data = scenarios.get(alt_id, {})
            ev = scenario_data.get("ev", 5.0)
            ev_scaled = ev / 2.0
            
            mcda_score = next((item["score"] for item in mcda_ranking if item["alternativa"] == alt_name), None)
            
            if mcda_score is not None:
                composite = 0.5 * mcda_score + 0.5 * ev_scaled
                combined_data.append({
                    "id": alt_id,
                    "name": alt_name,
                    "composite": composite
                })
        
        if combined_data:
            winner = max(combined_data, key=lambda x: x["composite"])
            return winner["id"], winner["name"]
    
    # Fallback: first alternative
    first_alt = next((a for a in alts if a["text"].strip()), None)
    if first_alt:
        return first_alt["id"], first_alt["text"].strip()
    
    return None, None


def calculate_risk_score(probability: str, impact: str) -> int:
    """Calculate risk score from probability and impact."""
    prob_val = RISK_PROB_MAP.get(probability, 1)
    impact_val = RISK_IMPACT_MAP.get(impact, 1)
    return prob_val * impact_val


def get_risk_color(score: int) -> str:
    """Get color based on risk score (1-12 scale)."""
    if score <= 2:
        return "#4caf50"  # Green - low
    elif score <= 4:
        return "#8bc34a"  # Light green
    elif score <= 6:
        return "#ffeb3b"  # Yellow - medium
    elif score <= 8:
        return "#ff9800"  # Orange
    else:
        return "#f44336"  # Red - high/critical


def count_active_risks() -> int:
    """Count risks that are not closed."""
    risks = st.session_state.get("risks", {})
    selected_alt = st.session_state.get("selected_alternative_id")
    if not selected_alt:
        return 0
    return sum(1 for r in risks.values() 
               if r.get("linked_alt_id") == selected_alt 
               and r.get("status") != "cerrado")


def render_risk_analysis_tab():
    """Render the Risk Analysis tab."""
    st.subheader("⚠️ Análisis de Riesgos")
    
    # Get alternatives
    alts = [a for a in st.session_state.get("alts", []) if a["text"].strip()]
    if not alts:
        st.info("Añade al menos una **Alternativa** en la pestaña *Alternativas* para analizar riesgos.")
        return
    
    # Initialize risks dict if needed
    if "risks" not in st.session_state:
        st.session_state.risks = {}
    
    # Get recommended alternative
    rec_id, rec_name = get_recommended_alternative()
    
    # Initialize selected alternative if not set
    if st.session_state.get("selected_alternative_id") is None and rec_id:
        st.session_state.selected_alternative_id = rec_id
    
    # Alternative selector
    alt_options = {a["id"]: a["text"].strip() for a in alts}
    alt_ids = list(alt_options.keys())
    alt_names = list(alt_options.values())
    
    current_idx = 0
    if st.session_state.get("selected_alternative_id") in alt_ids:
        current_idx = alt_ids.index(st.session_state.selected_alternative_id)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_name = st.selectbox(
            "Alternativa a analizar",
            options=alt_names,
            index=current_idx,
            key="risk_alt_selector",
            help="Selecciona la alternativa para la que quieres gestionar riesgos"
        )
        # Update selected alternative ID
        selected_idx = alt_names.index(selected_name)
        st.session_state.selected_alternative_id = alt_ids[selected_idx]
    
    with col2:
        if rec_name and selected_name == rec_name:
            st.success("✓ Recomendada")
        elif rec_name:
            st.caption(f"Recomendada: {rec_name[:20]}...")
    
    selected_alt_id = st.session_state.selected_alternative_id
    
    st.markdown("---")
    
    # Filter risks for selected alternative
    alt_risks = {k: v for k, v in st.session_state.risks.items() 
                 if v.get("linked_alt_id") == selected_alt_id}
    
    # Risk summary metrics
    if alt_risks:
        total_risks = len(alt_risks)
        high_risks = sum(1 for r in alt_risks.values() if calculate_risk_score(r.get("probability", "bajo"), r.get("impact", "bajo")) >= 6)
        treated_risks = sum(1 for r in alt_risks.values() if r.get("status") in ["en_tratamiento", "aceptado", "cerrado"])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Riesgos", total_risks)
        m2.metric("Alto Impacto", high_risks, delta=None if high_risks == 0 else f"-{high_risks}" if high_risks > 0 else None, delta_color="inverse")
        m3.metric("En Tratamiento", f"{treated_risks}/{total_risks}")
    
    # Add new risk section
    with st.expander("➕ Añadir nuevo riesgo", expanded=len(alt_risks) == 0):
        with st.form("add_risk_form", clear_on_submit=True):
            r_title = st.text_input("Descripción del riesgo", placeholder="¿Qué podría salir mal?")
            
            c1, c2 = st.columns(2)
            with c1:
                r_prob = st.selectbox("Probabilidad", RISK_PROBABILITY, index=1)
            with c2:
                r_impact = st.selectbox("Impacto", RISK_IMPACT, index=1)
            
            if st.form_submit_button("Añadir riesgo", type="primary"):
                if r_title.strip():
                    risk_id = str(uuid.uuid4())
                    today_iso = date.today().isoformat()
                    st.session_state.risks[risk_id] = {
                        "id": risk_id,
                        "title": r_title.strip(),
                        "probability": r_prob,
                        "impact": r_impact,
                        "linked_alt_id": selected_alt_id,
                        "strategies": {
                            "avoid": "",
                            "transfer": "",
                            "mitigate": "",
                            "contingency": ""
                        },
                        "notes": "",
                        "status": "identificado",
                        "created_at": today_iso,
                        "assessments": [
                            {
                                "date": today_iso,
                                "probability": r_prob,
                                "impact": r_impact
                            }
                        ]
                    }
                    st.rerun()
                else:
                    st.warning("Introduce una descripción del riesgo")
    
    # Display existing risks
    if alt_risks:
        st.markdown("### 📋 Inventario de Riesgos")
        
        # Sort by risk score descending
        sorted_risks = sorted(
            alt_risks.items(),
            key=lambda x: calculate_risk_score(x[1].get("probability", "bajo"), x[1].get("impact", "bajo")),
            reverse=True
        )
        
        for risk_id, risk in sorted_risks:
            score = calculate_risk_score(risk.get("probability", "bajo"), risk.get("impact", "bajo"))
            color = get_risk_color(score)
            status = risk.get("status", "identificado")
            status_icon = {"identificado": "🔵", "en_tratamiento": "🟡", "aceptado": "🟢", "cerrado": "⚫"}.get(status, "🔵")
            
            with st.expander(f"{status_icon} **{risk['title']}** — Puntuación: {score}", expanded=False):
                # Risk details
                c1, c2, c3 = st.columns(3)
                with c1:
                    new_prob = st.selectbox(
                        "Probabilidad",
                        RISK_PROBABILITY,
                        index=RISK_PROBABILITY.index(risk.get("probability", "medio")),
                        key=f"prob_{risk_id}"
                    )
                    if new_prob != risk.get("probability"):
                        st.session_state.risks[risk_id]["probability"] = new_prob
                
                with c2:
                    new_impact = st.selectbox(
                        "Impacto",
                        RISK_IMPACT,
                        index=RISK_IMPACT.index(risk.get("impact", "medio")),
                        key=f"impact_{risk_id}"
                    )
                    if new_impact != risk.get("impact"):
                        st.session_state.risks[risk_id]["impact"] = new_impact
                
                with c3:
                    new_status = st.selectbox(
                        "Estado",
                        RISK_STATUS,
                        index=RISK_STATUS.index(risk.get("status", "identificado")),
                        key=f"status_{risk_id}"
                    )
                    if new_status != risk.get("status"):
                        st.session_state.risks[risk_id]["status"] = new_status
                
                # Notes field
                new_notes = st.text_input(
                    "Notas",
                    value=risk.get("notes", ""),
                    key=f"notes_{risk_id}",
                    placeholder="Notas adicionales sobre este riesgo..."
                )
                if new_notes != risk.get("notes", ""):
                    st.session_state.risks[risk_id]["notes"] = new_notes
                
                st.markdown("---")
                st.markdown("**Estrategias de Respuesta**")
                
                # Strategy tabs
                strat_tabs = st.tabs(["🚫 Evitar", "🔄 Transferir", "📉 Mitigar", "🆘 Contingencia"])
                
                strategies = risk.get("strategies", {})
                
                with strat_tabs[0]:
                    st.caption("¿Cómo eliminar la causa del riesgo o cambiar el plan para evitarlo?")
                    avoid = st.text_area(
                        "Estrategia de evitación",
                        value=strategies.get("avoid", ""),
                        key=f"avoid_{risk_id}",
                        label_visibility="collapsed",
                        placeholder="Ej: Cambiar de proveedor, usar tecnología probada..."
                    )
                    if avoid != strategies.get("avoid"):
                        st.session_state.risks[risk_id]["strategies"]["avoid"] = avoid
                
                with strat_tabs[1]:
                    st.caption("¿Cómo trasladar el impacto a un tercero (seguros, subcontratación)?")
                    transfer = st.text_area(
                        "Estrategia de transferencia",
                        value=strategies.get("transfer", ""),
                        key=f"transfer_{risk_id}",
                        label_visibility="collapsed",
                        placeholder="Ej: Contratar seguro, externalizar a expertos..."
                    )
                    if transfer != strategies.get("transfer"):
                        st.session_state.risks[risk_id]["strategies"]["transfer"] = transfer
                
                with strat_tabs[2]:
                    st.caption("¿Qué acciones reducen la probabilidad o el impacto?")
                    mitigate = st.text_area(
                        "Estrategia de mitigación",
                        value=strategies.get("mitigate", ""),
                        key=f"mitigate_{risk_id}",
                        label_visibility="collapsed",
                        placeholder="Ej: Pruebas adicionales, formación, redundancia..."
                    )
                    if mitigate != strategies.get("mitigate"):
                        st.session_state.risks[risk_id]["strategies"]["mitigate"] = mitigate
                
                with strat_tabs[3]:
                    st.caption("¿Qué hacer si el riesgo se materializa?")
                    contingency = st.text_area(
                        "Plan de contingencia",
                        value=strategies.get("contingency", ""),
                        key=f"contingency_{risk_id}",
                        label_visibility="collapsed",
                        placeholder="Ej: Plan B, recursos de reserva, comunicación de crisis..."
                    )
                    if contingency != strategies.get("contingency"):
                        st.session_state.risks[risk_id]["strategies"]["contingency"] = contingency
                
                # Risk Assessments over time
                st.markdown("---")
                st.markdown("**📈 Evaluaciones en el Tiempo**")
                st.caption("Añade evaluaciones en diferentes fechas para ver la evolución del riesgo en la línea temporal.")
                
                assessments = risk.get("assessments", [])
                
                # Show existing assessments
                if assessments:
                    for i, assessment in enumerate(sorted(assessments, key=lambda x: x.get("date", ""))):
                        a_date = assessment.get("date", "")
                        a_prob = assessment.get("probability", "medio")
                        a_impact = assessment.get("impact", "medio")
                        a_score = calculate_risk_score(a_prob, a_impact)
                        resolved = a_prob == "ninguno" and a_impact == "ninguno"
                        
                        col_d, col_p, col_i, col_s, col_del = st.columns([2, 1.5, 1.5, 1, 0.5])
                        with col_d:
                            st.text(f"📅 {a_date}")
                        with col_p:
                            st.text(f"P: {a_prob}")
                        with col_i:
                            st.text(f"I: {a_impact}")
                        with col_s:
                            if resolved:
                                st.text("✅ Resuelto")
                            else:
                                st.text(f"Score: {a_score}")
                        with col_del:
                            if len(assessments) > 1 and st.button("✕", key=f"del_assess_{risk_id}_{i}", help="Eliminar evaluación"):
                                st.session_state.risks[risk_id]["assessments"].pop(i)
                                st.rerun()
                
                # Add new assessment
                with st.form(key=f"add_assessment_{risk_id}", clear_on_submit=True):
                    st.markdown("**Añadir nueva evaluación**")
                    ac1, ac2, ac3 = st.columns(3)
                    with ac1:
                        new_a_date = st.date_input("Fecha", value=date.today(), key=f"new_a_date_{risk_id}")
                    with ac2:
                        prob_options = ["ninguno"] + list(RISK_PROBABILITY)
                        new_a_prob = st.selectbox("Probabilidad", prob_options, index=2, key=f"new_a_prob_{risk_id}",
                                                  help="'ninguno' = riesgo resuelto")
                    with ac3:
                        impact_options = ["ninguno"] + list(RISK_IMPACT)
                        new_a_impact = st.selectbox("Impacto", impact_options, index=2, key=f"new_a_impact_{risk_id}",
                                                    help="'ninguno' = riesgo resuelto")
                    
                    if st.form_submit_button("➕ Añadir evaluación"):
                        new_assessment = {
                            "date": new_a_date.isoformat(),
                            "probability": new_a_prob,
                            "impact": new_a_impact
                        }
                        if "assessments" not in st.session_state.risks[risk_id]:
                            st.session_state.risks[risk_id]["assessments"] = []
                        st.session_state.risks[risk_id]["assessments"].append(new_assessment)
                        st.rerun()
                
                # Delete button
                st.markdown("")
                if st.button("🗑️ Eliminar riesgo", key=f"del_{risk_id}", type="secondary"):
                    del st.session_state.risks[risk_id]
                    st.rerun()
        
        st.markdown("---")
        
        # Risk Matrix Visualization
        st.markdown("### 📊 Matriz de Riesgos")
        
        # Build data for scatter plot
        matrix_data = []
        for risk_id, risk in alt_risks.items():
            prob_val = RISK_PROB_MAP.get(risk.get("probability", "bajo"), 1)
            impact_val = RISK_IMPACT_MAP.get(risk.get("impact", "bajo"), 1)
            score = prob_val * impact_val
            matrix_data.append({
                "title": risk["title"][:30] + "..." if len(risk["title"]) > 30 else risk["title"],
                "probability": prob_val,
                "impact": impact_val,
                "score": score,
                "category": risk.get("category", "técnico"),
                "status": risk.get("status", "identificado")
            })
        
        if matrix_data:
            fig = go.Figure()
            
            # Add risk points
            for item in matrix_data:
                fig.add_trace(go.Scatter(
                    x=[item["impact"]],
                    y=[item["probability"]],
                    mode="markers+text",
                    marker=dict(
                        size=20 + item["score"] * 3,
                        color=get_risk_color(item["score"]),
                        line=dict(width=2, color="white"),
                        opacity=0.8
                    ),
                    text=[item["title"]],
                    textposition="top center",
                    textfont=dict(size=10),
                    name=item["title"],
                    hovertemplate=(
                        f"<b>{item['title']}</b><br>"
                        f"Probabilidad: {item['probability']}<br>"
                        f"Impacto: {item['impact']}<br>"
                        f"Puntuación: {item['score']}<br>"
                        f"Categoría: {item['category']}<br>"
                        f"Estado: {item['status']}"
                        "<extra></extra>"
                    )
                ))
            
            # Add zone colors (background rectangles)
            # Green zone (low risk)
            fig.add_shape(type="rect", x0=0.5, y0=0.5, x1=2.5, y1=1.5,
                         fillcolor="rgba(76, 175, 80, 0.2)", line=dict(width=0))
            # Yellow zone (medium risk)
            fig.add_shape(type="rect", x0=0.5, y0=1.5, x1=2.5, y1=2.5,
                         fillcolor="rgba(255, 235, 59, 0.2)", line=dict(width=0))
            fig.add_shape(type="rect", x0=2.5, y0=0.5, x1=3.5, y1=1.5,
                         fillcolor="rgba(255, 235, 59, 0.2)", line=dict(width=0))
            # Orange zone (high risk)
            fig.add_shape(type="rect", x0=2.5, y0=1.5, x1=3.5, y1=2.5,
                         fillcolor="rgba(255, 152, 0, 0.2)", line=dict(width=0))
            fig.add_shape(type="rect", x0=0.5, y0=2.5, x1=2.5, y1=3.5,
                         fillcolor="rgba(255, 152, 0, 0.2)", line=dict(width=0))
            # Red zone (critical risk)
            fig.add_shape(type="rect", x0=2.5, y0=2.5, x1=4.5, y1=3.5,
                         fillcolor="rgba(244, 67, 54, 0.2)", line=dict(width=0))
            fig.add_shape(type="rect", x0=3.5, y0=0.5, x1=4.5, y1=2.5,
                         fillcolor="rgba(244, 67, 54, 0.2)", line=dict(width=0))
            
            fig.update_layout(
                height=400,
                showlegend=False,
                xaxis=dict(
                    title="Impacto →",
                    tickvals=[1, 2, 3, 4],
                    ticktext=["Bajo", "Medio", "Alto", "Crítico"],
                    range=[0.5, 4.5],
                    showgrid=True,
                    gridcolor="rgba(0,0,0,0.1)"
                ),
                yaxis=dict(
                    title="Probabilidad →",
                    tickvals=[1, 2, 3],
                    ticktext=["Baja", "Media", "Alta"],
                    range=[0.5, 3.5],
                    showgrid=True,
                    gridcolor="rgba(0,0,0,0.1)"
                ),
                plot_bgcolor="white",
                margin=dict(l=60, r=20, t=40, b=60)
            )
            
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.caption("📐 **Tamaño de burbuja** = puntuación de riesgo (probabilidad × impacto)")
        
        # Risk ranking table
        with st.expander("📋 Ranking de Riesgos"):
            ranking_data = []
            for risk_id, risk in sorted_risks:
                score = calculate_risk_score(risk.get("probability", "bajo"), risk.get("impact", "bajo"))
                has_strategies = any(risk.get("strategies", {}).values())
                ranking_data.append({
                    "Riesgo": risk["title"],
                    "Categoría": risk.get("category", ""),
                    "Prob.": risk.get("probability", ""),
                    "Impacto": risk.get("impact", ""),
                    "Puntuación": score,
                    "Estado": risk.get("status", ""),
                    "Estrategias": "✓" if has_strategies else "—"
                })
            
            if ranking_data:
                st.dataframe(pd.DataFrame(ranking_data), use_container_width=True)
    
    else:
        st.info("No hay riesgos identificados para esta alternativa. Añade el primer riesgo arriba.")


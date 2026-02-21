# -*- coding: utf-8 -*-
"""
Risk Analysis tab - Risk inventory, ranking, and mitigation strategies.
Inspired by project management theory (avoid, transfer, mitigate, contingency).
"""

import streamlit as st
import pandas as pd
import uuid
from datetime import date, datetime
from datetime import timedelta
import plotly.graph_objects as go
from config.constants import (
    RISK_CATEGORIES, RISK_PROBABILITY, RISK_IMPACT, RISK_STATUS,
    RISK_PROB_MAP, RISK_IMPACT_MAP
)


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


def parse_date(date_val):
    if date_val is None:
        return None
    if isinstance(date_val, date):
        return date_val
    if isinstance(date_val, datetime):
        return date_val.date()
    if isinstance(date_val, str) and date_val.strip():
        try:
            return datetime.fromisoformat(date_val).date()
        except:
            return None
    return None


def get_risk_assessment_as_of(risk: dict, as_of_date: date):
    assessments = risk.get("assessments", [])
    created_at = parse_date(risk.get("created_at"))
    if not assessments and created_at:
        assessments = [{
            "date": created_at.isoformat(),
            "probability": risk.get("probability", "medio"),
            "impact": risk.get("impact", "medio")
        }]

    best = None
    best_date = None
    for a in assessments:
        a_date = parse_date(a.get("date"))
        if not a_date:
            continue
        if a_date > as_of_date:
            continue
        if best_date is None or a_date > best_date:
            best = a
            best_date = a_date
    return best


def count_active_risks() -> int:
    """Count risks that are not closed."""
    risks = st.session_state.get("risks", {})
    return sum(1 for r in risks.values() if r.get("status") != "cerrado")


def render_risk_analysis_tab():
    """Render the Risk Analysis tab.
    
    Note: This view is intentionally decoupled from alternatives.
    """
    st.subheader("⚠️ Análisis de Riesgos")
    
    # Initialize risks dict if needed
    if "risks" not in st.session_state:
        st.session_state.risks = {}
    
    # Work with all risks (legacy `linked_alt_id` is ignored)
    alt_risks = dict(st.session_state.risks)
    
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
            
            c0, c1, c2 = st.columns(3)
            with c0:
                r_date = st.date_input("Fecha", value=date.today(), key="new_risk_date")
            with c1:
                r_prob = st.selectbox("Probabilidad", RISK_PROBABILITY, index=1)
            with c2:
                r_impact = st.selectbox("Impacto", RISK_IMPACT, index=1)
            
            if st.form_submit_button("Añadir riesgo", type="primary"):
                if r_title.strip():
                    risk_id = str(uuid.uuid4())
                    created_iso = (r_date or date.today()).isoformat()
                    st.session_state.risks[risk_id] = {
                        "id": risk_id,
                        "title": r_title.strip(),
                        "probability": r_prob,
                        "impact": r_impact,
                        "linked_alt_id": None,
                        "strategies": {
                            "avoid": "",
                            "transfer": "",
                            "mitigate": "",
                            "contingency": ""
                        },
                        "notes": "",
                        "status": "identificado",
                        "created_at": created_iso,
                        "assessments": [
                            {
                                "date": created_iso,
                                "probability": r_prob,
                                "impact": r_impact
                            }
                        ]
                    }
                    alt_risks[risk_id] = st.session_state.risks[risk_id]
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

                # Show existing assessments
                if assessments:
                    sorted_assessments = sorted(
                        list(enumerate(assessments)),
                        key=lambda x: x[1].get("date", "")
                    )
                    for display_idx, (orig_idx, assessment) in enumerate(sorted_assessments):
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
                            if len(assessments) > 1 and st.button("✕", key=f"del_assess_{risk_id}_{display_idx}", help="Eliminar evaluación"):
                                st.session_state.risks[risk_id]["assessments"].pop(orig_idx)
                                
                
                # Delete button
                st.markdown("")
                if st.button("🗑️ Eliminar riesgo", key=f"del_{risk_id}", type="secondary"):
                    del st.session_state.risks[risk_id]
                    
        
        st.markdown("---")
        
        # Risk Matrix Visualization
        st.markdown("### 📊 Matriz de Riesgos")

        all_dates = []
        for r in alt_risks.values():
            c_date = parse_date(r.get("created_at"))
            if c_date:
                all_dates.append(c_date)
            for a in r.get("assessments", []) or []:
                a_date = parse_date(a.get("date"))
                if a_date:
                    all_dates.append(a_date)

        matrix_as_of = None
        if all_dates:
            min_d = min(all_dates)
            max_d = max(max(all_dates), date.today())
            default_d = date.today()
            if default_d < min_d:
                default_d = min_d
            if default_d > max_d:
                default_d = max_d

            if min_d == max_d:
                matrix_as_of = min_d
            else:
                matrix_as_of = st.slider("Fecha", min_value=min_d, max_value=max_d, value=default_d, key="risk_matrix_date")
        
        # Build data for scatter plot
        matrix_data = []
        for risk_id, risk in alt_risks.items():
            if matrix_as_of is None:
                assessment = None
            else:
                assessment = get_risk_assessment_as_of(risk, matrix_as_of)
            if assessment is None:
                continue

            a_prob = assessment.get("probability", risk.get("probability", "bajo"))
            a_impact = assessment.get("impact", risk.get("impact", "bajo"))
            prob_val = RISK_PROB_MAP.get(a_prob)
            impact_val = RISK_IMPACT_MAP.get(a_impact)
            if prob_val is None or impact_val is None:
                continue
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
            
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
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
                st.dataframe(pd.DataFrame(ranking_data), width="stretch")
    
    else:
        st.info("No hay riesgos identificados. Añade el primer riesgo arriba.")

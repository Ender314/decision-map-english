# -*- coding: utf-8 -*-
"""
Informe (Report) tab - Full lifecycle decision report.
Data Story format combining analysis and monitoring phases for stakeholder presentation.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, datetime
from typing import Dict, List, Any, Tuple, Optional

from config.constants import (
    IMPACT_MAP, RISK_PROB_MAP, RISK_IMPACT_MAP,
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING, COLOR_ERROR, COLOR_INFO,
    COMPOSITE_DEFAULT_MCDA_WEIGHT_PCT,
)
from utils.calculations import (
    calculate_relevance_percentage,
    mcda_totals_and_ranking,
    normalize_weights,
    scenario_expected_value,
    get_disqualified_alternatives
)


def get_report_data() -> Dict[str, Any]:
    """Gather all data needed for the report from session state."""
    
    # Basic info
    decision = st.session_state.get("decision", "").strip()
    objetivo = st.session_state.get("objetivo", "").strip()
    
    # Alternatives and priorities (filter out disqualified)
    all_alts = st.session_state.get("alts", [])
    disqualified_alts = get_disqualified_alternatives()
    disqualified_ids = set(disqualified_alts.keys())
    
    # Only include qualified alternatives
    alts = [a for a in all_alts if a["id"] not in disqualified_ids]
    alt_names = [a["text"].strip() for a in alts if a.get("text", "").strip()]
    priorities = st.session_state.get("priorities", [])
    priority_names = [p["text"].strip() for p in priorities if p.get("text", "").strip()]
    
    # Impact/Relevance
    relevance_pct = calculate_relevance_percentage(
        st.session_state.get("impacto_corto", "bajo"),
        st.session_state.get("impacto_medio", "medio"),
        st.session_state.get("impacto_largo", "bajo"),
        IMPACT_MAP
    )
    
    # MCDA data (filtered by qualified alternatives)
    crit = st.session_state.get("mcda_criteria", [])
    scores_df = st.session_state.get("mcda_scores_df")
    ranking_list = []
    if scores_df is not None and not scores_df.empty and len(crit) > 0:
        _, ranking_list_all = mcda_totals_and_ranking(scores_df.copy(), crit)
        # Filter out disqualified alternatives
        qualified_names = set(alt_names)
        ranking_list = [item for item in ranking_list_all if item["alternativa"] in qualified_names]
    
    # Scenarios
    scenarios = st.session_state.get("scenarios", {})
    
    # Build combined data (MCDA + Scenarios) - only qualified alternatives
    qualified_alt_ids = {a["id"] for a in alts}
    combined_data = []
    w_mcda = COMPOSITE_DEFAULT_MCDA_WEIGHT_PCT / 100.0
    w_ev = 1.0 - w_mcda
    if ranking_list and scenarios:
        for alt_id, scenario in scenarios.items():
            # Skip disqualified alternatives
            if alt_id not in qualified_alt_ids:
                continue
            
            alt_name = scenario.get("name", "")
            ev = scenario_expected_value(
                scenario.get("p_best", 0.5),
                scenario.get("worst_score", 0),
                scenario.get("best_score", 0)
            )
            ev_scaled = ev / 2.0
            uncertainty = scenario.get("best_score", 0) - scenario.get("worst_score", 0)
            
            mcda_score = next((item["score"] for item in ranking_list if item["alternativa"] == alt_name), None)
            
            if mcda_score is not None:
                composite = w_mcda * mcda_score + w_ev * ev_scaled
                combined_data.append({
                    "name": alt_name,
                    "mcda": mcda_score,
                    "ev": ev,
                    "ev_scaled": ev_scaled,
                    "uncertainty": uncertainty,
                    "composite": composite
                })
    
    combined_sorted = sorted(combined_data, key=lambda x: x["composite"], reverse=True) if combined_data else []
    
    # Risks
    risks = st.session_state.get("risks", {})
    
    # Retro
    retro = st.session_state.get("retro", {})
    
    return {
        "decision": decision,
        "objetivo": objetivo,
        "alt_names": alt_names,
        "priority_names": priority_names,
        "relevance_pct": relevance_pct,
        "ranking_list": ranking_list,
        "combined_sorted": combined_sorted,
        "scenarios": scenarios,
        "risks": risks,
        "retro": retro,
        "scores_df": scores_df,
        "criteria": crit
    }


def get_confidence_metrics(combined_sorted: List[Dict]) -> Tuple[str, float, str]:
    """Calculate confidence level based on composite score gap and uncertainty."""
    if not combined_sorted or len(combined_sorted) < 2:
        return ("high", 100, "Única alternativa")
    
    best = combined_sorted[0]
    second = combined_sorted[1]
    
    best_score = best["composite"]
    second_score = second["composite"]
    winner_uncertainty = best.get("uncertainty", 5)
    
    if best_score > 0:
        gap_pct = ((best_score - second_score) / best_score) * 100
    else:
        gap_pct = 0
    
    uncertainty_factor = min(winner_uncertainty / 10.0, 1.0)
    
    if gap_pct >= 20:
        confidence = 95 - (uncertainty_factor * 25)
        return ("high", confidence, "Ventaja clara")
    elif gap_pct >= 10:
        confidence = 70 - (uncertainty_factor * 10)
        return ("medium", confidence, "Ventaja moderada")
    else:
        confidence = 60 - (uncertainty_factor * 20)
        return ("low", confidence, "Alternativas reñidas")


def create_confidence_gauge(confidence_pct: float, confidence_level: str) -> go.Figure:
    """Create a confidence gauge visualization."""
    color = {"high": COLOR_SUCCESS, "medium": COLOR_WARNING, "low": COLOR_ERROR}.get(confidence_level, COLOR_INFO)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=confidence_pct,
        number={'suffix': '%', 'font': {'size': 36}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': 'rgba(229, 62, 62, 0.3)'},
                {'range': [40, 70], 'color': 'rgba(221, 107, 32, 0.3)'},
                {'range': [70, 100], 'color': 'rgba(56, 161, 105, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': confidence_pct
            }
        }
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=30, b=10),
    )
    
    return fig


def create_risk_heatmap(risks: Dict[str, Any]) -> go.Figure:
    """Create a risk heatmap matrix (probability vs impact)."""
    
    # Initialize matrix (3 prob levels x 4 impact levels)
    prob_labels = ["alto", "medio", "bajo"]
    impact_labels = ["bajo", "medio", "alto", "crítico"]
    
    matrix = [[[] for _ in range(4)] for _ in range(3)]
    
    # Place risks in matrix
    for risk_id, risk in risks.items():
        if risk.get("status") == "cerrado":
            continue
        prob = risk.get("probability", "medio")
        impact = risk.get("impact", "medio")
        
        prob_idx = {"alto": 0, "medio": 1, "bajo": 2}.get(prob, 1)
        impact_idx = {"bajo": 0, "medio": 1, "alto": 2, "crítico": 3}.get(impact, 1)
        
        matrix[prob_idx][impact_idx].append(risk.get("title", "?")[:20])
    
    # Create heatmap values (count of risks)
    z = [[len(cell) for cell in row] for row in matrix]
    
    # Create hover text
    hover_text = [[", ".join(cell) if cell else "—" for cell in row] for row in matrix]
    
    # Color scale: white (0) to red (high risk count)
    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=impact_labels,
        y=prob_labels,
        text=hover_text,
        hovertemplate="Prob: %{y}<br>Impacto: %{x}<br>Riesgos: %{text}<extra></extra>",
        colorscale=[
            [0, "#f7fafc"],
            [0.25, "#fed7d7"],
            [0.5, "#fc8181"],
            [0.75, "#e53e3e"],
            [1, "#742a2a"]
        ],
        showscale=False
    ))
    
    # Add annotations for risk count
    for i, row in enumerate(z):
        for j, val in enumerate(row):
            if val > 0:
                fig.add_annotation(
                    x=impact_labels[j],
                    y=prob_labels[i],
                    text=str(val),
                    showarrow=False,
                    font=dict(size=20, color="white" if val > 1 else "black")
                )
    
    fig.update_layout(
        height=250,
        margin=dict(l=80, r=20, t=30, b=50),
        xaxis=dict(title="Impacto", side="bottom"),
        yaxis=dict(title="Probabilidad"),
    )
    
    return fig


def create_outcome_attribution_chart(outcomes: List[Dict]) -> go.Figure:
    """Create donut chart for outcome attribution (decision vs luck vs mixed)."""
    
    if not outcomes:
        return None
    
    attribution_counts = {"decisión": 0, "azar": 0, "mixto": 0}
    for outcome in outcomes:
        attr = outcome.get("attribution", "mixto")
        if attr in attribution_counts:
            attribution_counts[attr] += 1
    
    labels = ["Decisión", "Azar", "Mixto"]
    values = [attribution_counts["decisión"], attribution_counts["azar"], attribution_counts["mixto"]]
    colors = [COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING]
    
    # Filter out zeros
    filtered = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
    if not filtered:
        return None
    
    labels, values, colors = zip(*filtered)
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker_colors=colors,
        textinfo='percent+label',
        textposition='outside',
        hovertemplate="<b>%{label}</b><br>%{value} resultados (%{percent})<extra></extra>"
    )])
    
    fig.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=30, b=20),
        showlegend=False,
        annotations=[dict(text='Atribución', x=0.5, y=0.5, font_size=14, showarrow=False)]
    )
    
    return fig


def create_decision_quality_matrix(decision_score: int, outcome_score: int) -> go.Figure:
    """Create 2x2 matrix showing decision quality vs outcome quality."""
    
    # Determine quadrant
    x_pos = 0.25 if decision_score <= 3 else 0.75
    y_pos = 0.25 if outcome_score <= 3 else 0.75
    
    fig = go.Figure()
    
    # Background quadrants
    quadrants = [
        {"x0": 0, "x1": 0.5, "y0": 0.5, "y1": 1, "color": "rgba(56, 161, 105, 0.2)", "text": "🎲 Mala suerte"},
        {"x0": 0.5, "x1": 1, "y0": 0.5, "y1": 1, "color": "rgba(56, 161, 105, 0.4)", "text": "🏆 Éxito merecido"},
        {"x0": 0, "x1": 0.5, "y0": 0, "y1": 0.5, "color": "rgba(229, 62, 62, 0.4)", "text": "⚠️ Fracaso previsible"},
        {"x0": 0.5, "x1": 1, "y0": 0, "y1": 0.5, "color": "rgba(246, 173, 85, 0.3)", "text": "🍀 Buena suerte"},
    ]
    
    for q in quadrants:
        fig.add_shape(type="rect", x0=q["x0"], x1=q["x1"], y0=q["y0"], y1=q["y1"],
                     fillcolor=q["color"], line=dict(width=0))
        fig.add_annotation(x=(q["x0"]+q["x1"])/2, y=(q["y0"]+q["y1"])/2,
                          text=q["text"], showarrow=False, font=dict(size=12))
    
    # Current position marker
    fig.add_trace(go.Scatter(
        x=[x_pos], y=[y_pos],
        mode="markers",
        marker=dict(size=30, color=COLOR_PRIMARY, symbol="circle",
                   line=dict(width=3, color="white")),
        hovertemplate=f"Decisión: {decision_score}/5<br>Resultado: {outcome_score}/5<extra></extra>",
        showlegend=False
    ))
    
    fig.update_layout(
        height=280,
        margin=dict(l=60, r=20, t=30, b=50),
        xaxis=dict(title="Calidad de la Decisión →", range=[0, 1], showticklabels=False, showgrid=False),
        yaxis=dict(title="Calidad del Resultado →", range=[0, 1], showticklabels=False, showgrid=False),
        plot_bgcolor="white"
    )
    
    return fig


def create_before_after_chart(scenarios: Dict, retro: Dict) -> Optional[go.Figure]:
    """Create before/after comparison chart: expected EV vs actual outcomes."""
    
    outcomes = retro.get("outcomes", [])
    if not scenarios or not outcomes:
        return None
    
    # Calculate average expected value from scenarios
    ev_values = []
    for scenario in scenarios.values():
        ev = scenario_expected_value(
            scenario.get("p_best", 0.5),
            scenario.get("worst_score", 0),
            scenario.get("best_score", 0)
        )
        ev_values.append(ev)
    
    avg_expected = sum(ev_values) / len(ev_values) if ev_values else 5
    
    # Calculate actual outcome sentiment score
    sentiment_map = {"positivo": 8, "neutral": 5, "negativo": 2}
    actual_scores = [sentiment_map.get(o.get("sentiment", "neutral"), 5) for o in outcomes]
    avg_actual = sum(actual_scores) / len(actual_scores) if actual_scores else 5
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=["Expectativa (EV promedio)", "Realidad (Outcomes)"],
        y=[avg_expected, avg_actual],
        marker_color=[COLOR_INFO, COLOR_SUCCESS if avg_actual >= avg_expected else COLOR_WARNING],
        text=[f"{avg_expected:.1f}", f"{avg_actual:.1f}"],
        textposition='auto'
    ))
    
    fig.update_layout(
        height=280,
        margin=dict(l=40, r=20, t=30, b=50),
        yaxis=dict(title="Puntuación (0-10)", range=[0, 10]),
        showlegend=False
    )
    
    return fig


def render_informe_tab():
    """Render the Informe (Report) tab - Full lifecycle decision report."""
    
    # Gather all data
    data = get_report_data()
    
    # Check if there's enough data for a report
    if not data["alt_names"] or not data["priority_names"]:
        st.info("📋 **El informe estará disponible** una vez que hayas definido **Alternativas** y **Prioridades** en la fase de Análisis.")
        return
    
    if not data["ranking_list"]:
        st.info("📋 **El informe estará disponible** una vez que completes la **Evaluación** en la fase de Análisis.")
        return
    
    # =========================================
    # HERO SECTION: The Decision
    # =========================================
    
    decision_date = data["retro"].get("decision_date")
    date_str = decision_date.strftime("%d/%m/%Y") if isinstance(decision_date, date) else "Sin fecha"
    
    relevance_badge = "🟢 Baja" if data["relevance_pct"] <= 30 else "🟡 Media" if data["relevance_pct"] <= 60 else "🔴 Alta"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLOR_PRIMARY} 0%, #2c5282 100%); 
                padding: 2rem; border-radius: 16px; margin-bottom: 2rem;">
        <p style="color: #bee3f8; margin: 0; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">
            Informe de Decisión
        </p>
        <h1 style="color: #fff; margin: 0.5rem 0 1rem 0; font-size: 1.8rem; line-height: 1.3;">
            {data["decision"] or "Decisión sin título"}
        </h1>
        <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
            <div>
                <span style="color: #a0aec0; font-size: 0.8rem;">FECHA</span><br>
                <span style="color: #fff; font-size: 1rem;">{date_str}</span>
            </div>
            <div>
                <span style="color: #a0aec0; font-size: 0.8rem;">RELEVANCIA</span><br>
                <span style="color: #fff; font-size: 1rem;">{relevance_badge} ({int(data["relevance_pct"])}%)</span>
            </div>
            <div>
                <span style="color: #a0aec0; font-size: 0.8rem;">ALTERNATIVAS</span><br>
                <span style="color: #fff; font-size: 1rem;">{len(data["alt_names"])}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if data["objetivo"]:
        st.markdown(f"**Objetivo:** {data['objetivo']}")
        st.markdown("")
    
    # =========================================
    # CHAPTER 1: The Recommendation
    # =========================================
    
    st.markdown("---")
    st.markdown("## 🏆 1. La Recomendación")
    
    if data["combined_sorted"]:
        winner = data["combined_sorted"][0]
        confidence_level, confidence_pct, confidence_desc = get_confidence_metrics(data["combined_sorted"])
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown(f"""
            <div style="background: #f7fafc; padding: 1.5rem; border-radius: 12px; border-left: 4px solid {COLOR_SUCCESS};">
                <p style="color: #718096; margin: 0; font-size: 0.85rem;">ALTERNATIVA RECOMENDADA</p>
                <h2 style="color: {COLOR_PRIMARY}; margin: 0.3rem 0;">{winner['name']}</h2>
                <p style="color: #4a5568; margin: 0.5rem 0 0 0;">
                    Puntuación compuesta: <strong>{winner['composite']:.2f}</strong> / 5.00
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("")
            st.markdown(f"**{confidence_desc}**")
            st.caption(f"La alternativa ganadora tiene una ventaja del {((winner['composite'] - data['combined_sorted'][1]['composite']) / winner['composite'] * 100):.0f}% sobre la segunda opción." if len(data["combined_sorted"]) > 1 else "Única alternativa evaluada.")
        
        with col2:
            st.markdown("**Nivel de Confianza**")
            fig_gauge = create_confidence_gauge(confidence_pct, confidence_level)
            st.plotly_chart(fig_gauge, width="stretch", config={"displayModeBar": False})
    
    elif data["ranking_list"]:
        winner = data["ranking_list"][0]
        st.success(f"🏆 **Recomendación (MCDA):** {winner['alternativa']} — Puntuación: {winner['score']:.2f}")
        st.caption("Completa los **Escenarios** para una recomendación más robusta con análisis de incertidumbre.")
    
    # =========================================
    # CHAPTER 2: Risk Landscape
    # =========================================
    
    st.markdown("---")
    st.markdown("## ⚠️ 2. Panorama de Riesgos")
    
    risks = data["risks"]
    
    if not risks:
        st.info("💡 No hay riesgos registrados. Añade riesgos en la pestaña **Seguimiento → Riesgos**.")
    else:
        # Risk metrics
        active_risks = sum(1 for r in risks.values() if r.get("status") != "cerrado")
        high_risks = sum(1 for r in risks.values() 
                        if r.get("status") != "cerrado" 
                        and RISK_PROB_MAP.get(r.get("probability", "bajo"), 1) * RISK_IMPACT_MAP.get(r.get("impact", "bajo"), 1) >= 6)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Riesgos Activos", active_risks)
        with col2:
            st.metric("Alto Riesgo", high_risks, delta="crítico" if high_risks > 0 else None, delta_color="inverse")
        with col3:
            st.metric("Cerrados", sum(1 for r in risks.values() if r.get("status") == "cerrado"))
        
        st.markdown("")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Matriz de Riesgos**")
            fig_heatmap = create_risk_heatmap(risks)
            st.plotly_chart(fig_heatmap, width="stretch", config={"displayModeBar": False})
        
        with col2:
            st.markdown("**Top Riesgos (por puntuación)**")
            risk_scores = []
            for rid, r in risks.items():
                if r.get("status") == "cerrado":
                    continue
                score = RISK_PROB_MAP.get(r.get("probability", "bajo"), 1) * RISK_IMPACT_MAP.get(r.get("impact", "bajo"), 1)
                risk_scores.append({"title": r.get("title", "?"), "score": score, "status": r.get("status", "?")})
            
            risk_scores_sorted = sorted(risk_scores, key=lambda x: x["score"], reverse=True)[:5]
            
            if risk_scores_sorted:
                for r in risk_scores_sorted:
                    score_color = COLOR_ERROR if r["score"] >= 6 else COLOR_WARNING if r["score"] >= 3 else COLOR_SUCCESS
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                        <span style="background: {score_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem; margin-right: 0.5rem;">{r['score']}</span>
                        <span>{r['title'][:40]}</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("No hay riesgos activos")
    
    # =========================================
    # CHAPTER 3: Expectations vs Reality
    # =========================================
    
    st.markdown("---")
    st.markdown("## 📊 3. Expectativas vs Realidad")
    
    retro = data["retro"]
    outcomes = retro.get("outcomes", [])
    
    if not outcomes:
        st.info("💡 No hay resultados registrados. Añade resultados en **Seguimiento → Retrospectiva**.")
    else:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Comparación Antes/Después**")
            fig_before_after = create_before_after_chart(data["scenarios"], retro)
            if fig_before_after:
                st.plotly_chart(fig_before_after, width="stretch", config={"displayModeBar": False})
                st.caption("EV promedio de escenarios vs. sentimiento promedio de outcomes")
            else:
                st.caption("Completa escenarios para ver la comparación")
        
        with col2:
            st.markdown("**Resumen de Resultados**")
            positive = sum(1 for o in outcomes if o.get("sentiment") == "positivo")
            neutral = sum(1 for o in outcomes if o.get("sentiment") == "neutral")
            negative = sum(1 for o in outcomes if o.get("sentiment") == "negativo")
            
            st.markdown(f"""
            - 🟢 **Positivos:** {positive}
            - 🟡 **Neutrales:** {neutral}
            - 🔴 **Negativos:** {negative}
            """)
            
            # Latest outcome
            if outcomes:
                latest = outcomes[-1]
                st.markdown("---")
                st.markdown("**Último resultado registrado:**")
                st.caption(f"*\"{latest.get('description', '')[:100]}...\"*" if len(latest.get('description', '')) > 100 else f"*\"{latest.get('description', '')}\"*")
    
    # =========================================
    # CHAPTER 4: What We Learned
    # =========================================
    
    st.markdown("---")
    st.markdown("## 📝 4. Lecciones Aprendidas")
    
    decision_score = retro.get("decision_quality_score", 3)
    outcome_score = retro.get("outcome_quality_score", 3)
    lessons = retro.get("lessons_learned", "").strip()
    tripwires = retro.get("tripwires", [])
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**Matriz Decisión-Resultado**")
        fig_quality = create_decision_quality_matrix(decision_score, outcome_score)
        st.plotly_chart(fig_quality, width="stretch", config={"displayModeBar": False})
        st.caption(f"Decisión: {decision_score}/5 — Resultado: {outcome_score}/5")
    
    with col2:
        if lessons:
            st.markdown("**Reflexiones Clave**")
            st.markdown(f"> {lessons[:500]}{'...' if len(lessons) > 500 else ''}")
        else:
            st.info("💡 Añade lecciones aprendidas en **Seguimiento → Retrospectiva**")
        
        # Tripwires summary
        if tripwires:
            triggered = sum(1 for t in tripwires if t.get("status") == "disparado")
            active = sum(1 for t in tripwires if t.get("status") == "activo")
            
            st.markdown("---")
            st.markdown("**Tripwires**")
            if triggered > 0:
                st.warning(f"⚡ {triggered} tripwire(s) disparados")
            if active > 0:
                st.caption(f"🔔 {active} tripwire(s) activos bajo monitoreo")
    
    # =========================================
    # CHAPTER 5: Luck vs Skill
    # =========================================
    
    st.markdown("---")
    st.markdown("## 🎲 5. Decisión vs Azar")
    
    if not outcomes:
        st.info("💡 Registra resultados con su atribución (decisión/azar/mixto) en **Seguimiento → Retrospectiva**.")
    else:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("**Atribución de Resultados**")
            fig_attribution = create_outcome_attribution_chart(outcomes)
            if fig_attribution:
                st.plotly_chart(fig_attribution, width="stretch", config={"displayModeBar": False})
            else:
                st.caption("No hay datos de atribución")
        
        with col2:
            # Calculate attribution stats
            decision_attr = sum(1 for o in outcomes if o.get("attribution") == "decisión")
            luck_attr = sum(1 for o in outcomes if o.get("attribution") == "azar")
            mixed_attr = sum(1 for o in outcomes if o.get("attribution") == "mixto")
            total = len(outcomes)
            
            st.markdown("**Interpretación**")
            
            if total > 0:
                decision_pct = decision_attr / total * 100
                luck_pct = luck_attr / total * 100
                
                if decision_pct >= 60:
                    st.success("✓ La mayoría de los resultados se deben a la **calidad de la decisión**. El proceso fue efectivo.")
                elif luck_pct >= 60:
                    st.warning("⚠️ La mayoría de los resultados se deben al **azar**. Considera si el proceso de decisión capturó la incertidumbre correctamente.")
                else:
                    st.info("Los resultados muestran una **mezcla** de factores controlables e incontrolables. Esto es típico en decisiones complejas.")
                
                st.markdown("")
                st.markdown(f"""
                - **Por decisión:** {decision_attr} ({decision_pct:.0f}%)
                - **Por azar:** {luck_attr} ({luck_pct:.0f}%)
                - **Mixto:** {mixed_attr} ({100 - decision_pct - luck_pct:.0f}%)
                """)
    
    # =========================================
    # FOOTER
    # =========================================
    
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #718096; font-size: 0.85rem; padding: 1rem 0;">
        📋 Informe generado por <strong>Decider Pro</strong> — {datetime.now().strftime("%d/%m/%Y %H:%M")}
    </div>
    """, unsafe_allow_html=True)

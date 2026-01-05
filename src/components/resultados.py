# -*- coding: utf-8 -*-
"""
Resultados (Results) tab - Executive Summary for Stakeholders.
Visual-heavy dashboard with key decision insights.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config.constants import IMPACT_MAP
from utils.calculations import (
    calculate_relevance_percentage, 
    mcda_totals_and_ranking, 
    normalize_weights,
    scenario_expected_value
)
from utils.visualizations import create_mcda_radar_chart, create_impact_chart


def get_confidence_level(combined_sorted: list) -> tuple:
    """
    Calculate confidence level based on composite score gap and uncertainty.
    Uses uncertainty to interpolate within confidence ranges:
    - Lower uncertainty = higher confidence within range
    - Higher uncertainty = lower confidence within range
    Returns (level, percentage, description).
    """
    if not combined_sorted or len(combined_sorted) < 2:
        return ("high", 100, "Única alternativa")
    
    best = combined_sorted[0]
    second = combined_sorted[1]
    
    best_score = best["composite"]
    second_score = second["composite"]
    winner_uncertainty = best.get("uncertainty", 5)  # Default to mid-range
    
    # Calculate gap as percentage of best score
    if best_score > 0:
        gap_pct = ((best_score - second_score) / best_score) * 100
    else:
        gap_pct = 0
    
    # Normalize uncertainty to 0-1 (0=low uncertainty, 1=high uncertainty)
    # Uncertainty ranges from 0 to 10
    uncertainty_factor = min(winner_uncertainty / 10.0, 1.0)
    
    # Interpolate within range: low uncertainty → high end, high uncertainty → low end
    if gap_pct >= 20:
        # Range: 70-95%
        confidence = 95 - (uncertainty_factor * 25)  # 95 when uncertainty=0, 70 when uncertainty=10
        return ("high", confidence, "Ventaja clara")
    elif gap_pct >= 10:
        # Range: 60-70%
        confidence = 70 - (uncertainty_factor * 10)  # 70 when uncertainty=0, 60 when uncertainty=10
        return ("medium", confidence, "Ventaja moderada")
    else:
        # Range: 40-60%
        confidence = 60 - (uncertainty_factor * 20)  # 60 when uncertainty=0, 40 when uncertainty=10
        return ("low", confidence, "Alternativas muy reñidas")


def create_decision_matrix_chart(combined_data: list) -> go.Figure:
    """Create the bubble chart for Decision Matrix."""
    fig = go.Figure()
    
    max_composite = max(d["composite"] for d in combined_data)
    min_composite = min(d["composite"] for d in combined_data)
    
    for item in combined_data:
        # Bubble size based on uncertainty
        bubble_size = 20 + item["uncertainty"] * 16
        
        # Opacity inversely proportional to uncertainty
        max_uncertainty = 10
        opacity = 0.95 - (item["uncertainty"] / max_uncertainty) * 0.9
        
        fig.add_trace(go.Scatter(
            x=[item["mcda"]],
            y=[item["ev_scaled"]],
            mode="markers+text",
            marker=dict(
                size=bubble_size,
                color=item["composite"],
                colorscale="Viridis",
                cmin=min_composite,
                cmax=max_composite,
                opacity=opacity,
                line=dict(width=2, color="white")
            ),
            text=item["name"],
            textposition="top center",
            textfont=dict(size=11, color="#333"),
            name=item["name"],
            hovertemplate=(
                f"<b>{item['name']}</b><br>"
                f"MCDA: {item['mcda']:.2f}<br>"
                f"EV: {item['ev']:.2f}<br>"
                f"Compuesto: {item['composite']:.2f}"
                "<extra></extra>"
            )
        ))
    
    # Quadrant lines
    fig.add_hline(y=2.5, line_dash="dash", line_color="#ccc", opacity=0.5)
    fig.add_vline(x=2.5, line_dash="dash", line_color="#ccc", opacity=0.5)
    
    # Quadrant labels
    fig.add_annotation(x=1.25, y=4.5, text="Alto potencial", showarrow=False, font=dict(size=9, color="#888"))
    fig.add_annotation(x=3.75, y=4.5, text="✓ Óptimo", showarrow=False, font=dict(size=10, color="#2e7d32"))
    fig.add_annotation(x=1.25, y=0.5, text="Evitar", showarrow=False, font=dict(size=9, color="#888"))
    fig.add_annotation(x=3.75, y=0.5, text="Seguro limitado", showarrow=False, font=dict(size=9, color="#888"))
    
    fig.update_layout(
        height=350,
        margin=dict(l=50, r=20, t=30, b=50),
        showlegend=False,
        xaxis=dict(title="Puntuación MCDA", range=[0, 5.2], showgrid=False, dtick=1),
        yaxis=dict(title="Valor Esperado", range=[0, 5.2], showgrid=False, dtick=1),
        plot_bgcolor="white"
    )
    
    return fig


def render_resultados_tab():
    """Render the Resultados (Results) tab - Executive Summary."""
    
    # Check if we have data
    alt_names = [a["text"].strip() for a in st.session_state.alts if a["text"].strip()]
    prioridad_names = [p["text"].strip() for p in st.session_state.priorities if p["text"].strip()]
    
    if not alt_names or not prioridad_names:
        st.info("💡 **Resumen ejecutivo disponible** una vez que hayas definido **Alternativas** y **Prioridades**")
        return
    
    # Get MCDA data
    crit = st.session_state.get("mcda_criteria", [])
    scores_df = st.session_state.get("mcda_scores_df", pd.DataFrame())
    ranking_list = []
    
    if not scores_df.empty and len(crit) > 0:
        _, ranking_list = mcda_totals_and_ranking(scores_df.copy(), crit)
    
    # Get scenarios data
    scenarios_state = st.session_state.get("scenarios", {})
    
    # Build combined data for Decision Matrix
    combined_data = []
    if ranking_list and scenarios_state:
        for alt_id, scenario in scenarios_state.items():
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
                composite = 0.5 * mcda_score + 0.5 * ev_scaled
                combined_data.append({
                    "name": alt_name,
                    "mcda": mcda_score,
                    "ev": ev,
                    "ev_scaled": ev_scaled,
                    "uncertainty": uncertainty,
                    "composite": composite
                })
    
    # Sort combined data by composite
    combined_sorted = sorted(combined_data, key=lambda x: x["composite"], reverse=True) if combined_data else []
    
    # ===========================================
    # HERO SECTION - Winner Announcement
    # ===========================================
    
    if combined_sorted:
        winner = combined_sorted[0]
        confidence_level, confidence_pct, confidence_desc = get_confidence_level(combined_sorted)
        
        # Confidence color
        conf_color = {"high": "#2e7d32", "medium": "#f57c00", "low": "#d32f2f"}.get(confidence_level, "#666")
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem; text-align: center;">
            <p style="color: #aaa; margin: 0; font-size: 0.9rem;">ALTERNATIVA RECOMENDADA</p>
            <h1 style="color: #fff; margin: 0.5rem 0; font-size: 2.2rem;">🏆 {winner['name']}</h1>
            <p style="color: #83c9ff; margin: 0; font-size: 1.1rem;">
                Puntuación Compuesta: <strong>{winner['composite']:.2f}</strong> / 5.00
            </p>
            <div style="margin-top: 1rem;">
                <span style="background: {conf_color}; color: white; padding: 0.3rem 0.8rem; 
                             border-radius: 20px; font-size: 0.85rem;">
                    {confidence_desc} — Confianza {confidence_pct:.0f}%
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    elif ranking_list:
        # Fallback to MCDA winner if no scenarios - build minimal combined data for confidence
        winner = ranking_list[0]
        fallback_combined = [{"composite": item["score"], "uncertainty": 5} for item in ranking_list]
        confidence_level, confidence_pct, confidence_desc = get_confidence_level(fallback_combined)
        conf_color = {"high": "#2e7d32", "medium": "#f57c00", "low": "#d32f2f"}.get(confidence_level, "#666")
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem; text-align: center;">
            <p style="color: #aaa; margin: 0; font-size: 0.9rem;">ALTERNATIVA RECOMENDADA (MCDA)</p>
            <h1 style="color: #fff; margin: 0.5rem 0; font-size: 2.2rem;">🏆 {winner['alternativa']}</h1>
            <p style="color: #83c9ff; margin: 0; font-size: 1.1rem;">
                Puntuación MCDA: <strong>{winner['score']:.2f}</strong> / 5.00
            </p>
            <div style="margin-top: 1rem;">
                <span style="background: {conf_color}; color: white; padding: 0.3rem 0.8rem; 
                             border-radius: 20px; font-size: 0.85rem;">
                    {confidence_desc} — Confianza {confidence_pct:.0f}%
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Completa la **Evaluación** para ver la recomendación final.")
    
    # ===========================================
    # KEY METRICS ROW
    # ===========================================
    
    relevance_pct = calculate_relevance_percentage(
        st.session_state.get("impacto_corto", "bajo"),
        st.session_state.get("impacto_medio", "medio"),
        st.session_state.get("impacto_largo", "bajo"),
        IMPACT_MAP
    )
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Relevancia", f"{int(relevance_pct)}%")
    with col2:
        st.metric("Alternativas", len(alt_names))
    with col3:
        st.metric("Criterios", len(prioridad_names))
    with col4:
        tiempo = st.session_state.get("tiempo", "—")
        st.metric("Tiempo", tiempo)
    
    # Decision context
    decision_text = st.session_state.get("decision", "").strip()
    objetivo_text = st.session_state.get("objetivo", "").strip()
    
    if decision_text or objetivo_text:
        with st.expander("📋 Contexto de la Decisión", expanded=False):
            if decision_text:
                st.markdown(f"**Decisión:** {decision_text}")
            if objetivo_text:
                st.markdown(f"**Objetivo:** {objetivo_text}")
    
    st.markdown("---")
    
    # ===========================================
    # MAIN VISUALIZATIONS
    # ===========================================
    
    st.markdown("## 📊 Análisis Visual")
    
    if combined_data:
        # Two-column layout: Decision Matrix + Radar Chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Matriz de Decisión")
            fig_matrix = create_decision_matrix_chart(combined_data)
            st.plotly_chart(fig_matrix, use_container_width=True, config={"displayModeBar": False})
            st.caption("Tamaño/transparencia = incertidumbre")
        
        with col2:
            st.markdown("#### 📈 Perfil por Criterios")
            try:
                top_alts = [item["alternativa"] for item in ranking_list[:3]]
                fig_radar = create_mcda_radar_chart(scores_df, prioridad_names, top_alts)
                fig_radar.update_layout(height=350, margin=dict(l=30, r=30, t=30, b=30))
                st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})
                st.caption("Top 3 alternativas por criterio")
            except Exception:
                st.info("💡 Radar no disponible")
    
    elif ranking_list:
        # Only MCDA available - show radar chart full width
        st.markdown("#### 📈 Perfil por Criterios (Top 3)")
        try:
            top_alts = [item["alternativa"] for item in ranking_list[:3]]
            fig_radar = create_mcda_radar_chart(scores_df, prioridad_names, top_alts)
            st.plotly_chart(fig_radar, use_container_width=True, config={"displayModeBar": False})
        except Exception:
            st.info("💡 Complete la evaluación para ver el gráfico radar")
        
        st.info("💡 Completa los **Escenarios** para ver la Matriz de Decisión combinada")
    
    st.markdown("---")
    
    # ===========================================
    # RANKING TABLES
    # ===========================================
    
    st.markdown("## 🏅 Rankings")
    
    if combined_sorted:
        # Combined ranking (primary)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Ranking Compuesto")
            ranking_df = pd.DataFrame([{
                "#": i + 1,
                "Alternativa": d["name"],
                "MCDA": d["mcda"],
                "EV": d["ev_scaled"],
                "Compuesto": d["composite"]
            } for i, d in enumerate(combined_sorted)])
            
            st.dataframe(
                ranking_df.style.format({"MCDA": "{:.2f}", "EV": "{:.2f}", "Compuesto": "{:.2f}"}),
                hide_index=True,
                use_container_width=True
            )
        
        with col2:
            st.markdown("#### Pesos de Criterios")
            weight_map = normalize_weights(crit)
            weights_df = pd.DataFrame([{
                "Criterio": c["name"],
                "Peso": weight_map.get(c["name"], 0)
            } for c in crit])
            
            st.dataframe(
                weights_df.style.format({"Peso": "{:.1%}"}),
                hide_index=True,
                use_container_width=True
            )
    
    elif ranking_list:
        # MCDA only ranking
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Ranking MCDA")
            ranking_df = pd.DataFrame([{
                "#": i + 1,
                "Alternativa": item["alternativa"],
                "Puntuación": item["score"]
            } for i, item in enumerate(ranking_list)])
            
            st.dataframe(
                ranking_df.style.format({"Puntuación": "{:.2f}"}),
                hide_index=True,
                use_container_width=True
            )
        
        with col2:
            st.markdown("#### Pesos de Criterios")
            weight_map = normalize_weights(crit)
            weights_df = pd.DataFrame([{
                "Criterio": c["name"],
                "Peso": weight_map.get(c["name"], 0)
            } for c in crit])
            
            st.dataframe(
                weights_df.style.format({"Peso": "{:.1%}"}),
                hide_index=True,
                use_container_width=True
            )
    
    # ===========================================
    # DATA-DRIVEN INSIGHTS
    # ===========================================
    
    st.markdown("---")
    st.markdown("## 💡 Insights")
    
    insights = []
    
    # Insight 1: Winner analysis
    if combined_sorted and len(combined_sorted) >= 2:
        winner = combined_sorted[0]
        runner_up = combined_sorted[1]
        gap = winner["composite"] - runner_up["composite"]
        
        if gap > 0.5:
            insights.append(f"🏆 **{winner['name']}** destaca claramente con una ventaja de **{gap:.2f}** puntos sobre {runner_up['name']}")
        elif gap > 0.2:
            insights.append(f"🥇 **{winner['name']}** lidera con ventaja moderada ({gap:.2f} pts) sobre {runner_up['name']}")
        else:
            insights.append(f"⚖️ **{winner['name']}** y **{runner_up['name']}** están muy igualados (diferencia: {gap:.2f}). Considerar factores cualitativos adicionales")
    
    # Insight 2: Uncertainty analysis
    if combined_sorted:
        high_uncertainty = [d for d in combined_sorted if d["uncertainty"] >= 5]
        low_uncertainty = [d for d in combined_sorted if d["uncertainty"] <= 2]
        
        if high_uncertainty:
            names = ", ".join([d["name"] for d in high_uncertainty])
            insights.append(f"⚠️ **Alta incertidumbre** en: {names}. Considerar mitigación de riesgos")
        
        if low_uncertainty and combined_sorted[0]["name"] in [d["name"] for d in low_uncertainty]:
            insights.append(f"✅ La alternativa recomendada tiene **baja incertidumbre**, lo que aumenta la confianza en el resultado")
    
    # Insight 3: MCDA vs EV alignment
    if combined_sorted and ranking_list:
        mcda_winner = ranking_list[0]["alternativa"]
        # Find EV winner (highest ev_scaled)
        ev_winner = max(combined_sorted, key=lambda x: x["ev_scaled"])["name"]
        
        if mcda_winner != ev_winner:
            insights.append(f"🔄 **Divergencia detectada**: MCDA favorece a *{mcda_winner}*, pero el valor esperado (EV) favorece a *{ev_winner}*. Revisar supuestos de probabilidad")
        else:
            insights.append(f"✓ **Consistencia**: El análisis MCDA y de escenarios coinciden en recomendar *{mcda_winner}*")
    
    # Insight 4: Relevance-based
    if relevance_pct > 80:
        insights.append("🚨 **Decisión crítica**: El alto impacto justifica invertir tiempo adicional en validar los datos")
    elif relevance_pct > 50:
        insights.append("📌 **Decisión importante**: Asegurar alineación con stakeholders clave antes de proceder")
    
    # Insight 5: Criteria concentration
    if crit:
        weight_map = normalize_weights(crit)
        max_weight = max(weight_map.values()) if weight_map else 0
        if max_weight > 0.4:
            dominant = max(weight_map, key=weight_map.get)
            insights.append(f"📊 El criterio **{dominant}** domina el análisis ({max_weight:.0%}). Verificar si refleja las prioridades reales")
    
    if insights:
        for insight in insights:
            st.markdown(f"- {insight}")
    else:
        st.info("💡 Completa más secciones para generar insights automatizados")
    
    # ===========================================
    # KPIs & STAKEHOLDERS (collapsible)
    # ===========================================
    
    kpis = st.session_state.get("kpis", [])
    stakeholders = st.session_state.get("stakeholders", [])
    valid_kpis = [k for k in kpis if k.get("name", "").strip()]
    valid_stakeholders = [s for s in stakeholders if s.get("name", "").strip()]
    
    if valid_kpis or valid_stakeholders:
        st.markdown("---")
        
        with st.expander("📋 Información Adicional", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                if valid_kpis:
                    st.markdown("**📊 KPIs Relevantes**")
                    for kpi in valid_kpis[:5]:
                        value_str = str(kpi.get("value", "N/A"))
                        unit_str = f" {kpi.get('unit', '')}" if kpi.get("unit", "").strip() else ""
                        st.markdown(f"- **{kpi.get('name', '')}:** {value_str}{unit_str}")
            
            with col2:
                if valid_stakeholders:
                    st.markdown("**👥 Stakeholders**")
                    for sh in valid_stakeholders[:5]:
                        name = sh.get("name", "")
                        opinion = sh.get("opinion", "")
                        if opinion:
                            st.markdown(f"- **{name}:** {opinion}")
                        else:
                            st.markdown(f"- **{name}**")
    
    # ===========================================
    # FOOTER
    # ===========================================
    
    st.markdown("---")
    st.success("✅ **Análisis completado** — Exporta los datos desde la barra lateral para compartir o archivar.")

# -*- coding: utf-8 -*-
"""
Resultados (Results) tab - Executive Summary for Stakeholders.
Visual-heavy dashboard with key decision insights.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from config.constants import IMPACT_MAP, COMPOSITE_DEFAULT_MCDA_WEIGHT_PCT
from utils.calculations import (
    calculate_relevance_percentage, 
    mcda_totals_and_ranking, 
    normalize_weights,
    scenario_expected_value,
    get_disqualified_alternatives,
    calculate_robustness_index
)
from utils.visualizations import create_mcda_radar_chart, create_impact_chart


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
            mode="markers",
            marker=dict(
                size=bubble_size,
                color=item["composite"],
                colorscale="Viridis",
                cmin=min_composite,
                cmax=max_composite,
                opacity=opacity,
                line=dict(width=2, color="white")
            ),
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

    # Print-friendly CSS: hide Streamlit chrome when printing
    st.markdown("""
    <style>
    @media print {
        /* Hide Streamlit UI chrome */
        header[data-testid="stHeader"],
        [data-testid="stSidebar"],
        [data-testid="stToolbar"],
        .stDeployButton,
        [data-testid="stStatusWidget"],
        footer,
        #MainMenu,
        .stActionButton,
        button,
        .no-print { display: none !important; }

        /* Full-width content */
        .main .block-container { max-width: 100% !important; padding: 0 1rem !important; }
        section[data-testid="stMain"] { padding: 0 !important; }

        /* Avoid page breaks inside charts and tables */
        .stPlotlyChart, .stDataFrame, .stMarkdown { break-inside: avoid; }
    }
    </style>
    """, unsafe_allow_html=True)

    # Check if we have data
    alt_names = [a["text"].strip() for a in st.session_state.alts if a["text"].strip()]
    prioridad_names = [p["text"].strip() for p in st.session_state.priorities if p["text"].strip()]
    
    if not alt_names or not prioridad_names:
        st.info("💡 **Resumen ejecutivo disponible** una vez que hayas definido **Alternativas** y **Prioridades**")
        return
    
    # Get disqualified alternatives (due to No Negociables)
    disqualified_alts = get_disqualified_alternatives()
    disqualified_names = set()
    for alt in st.session_state.alts:
        if alt["id"] in disqualified_alts:
            disqualified_names.add(alt["text"].strip())
    
    # Get MCDA data
    crit = st.session_state.get("mcda_criteria", [])
    scores_df = st.session_state.get("mcda_scores_df", pd.DataFrame())
    ranking_list = []
    ranking_list_all = []  # Keep all for display purposes
    
    if not scores_df.empty and len(crit) > 0:
        _, ranking_list_all = mcda_totals_and_ranking(scores_df.copy(), crit)
        # Filter out disqualified alternatives for the main ranking
        ranking_list = [item for item in ranking_list_all if item["alternativa"] not in disqualified_names]
    
    # Get scenarios data
    scenarios_state = st.session_state.get("scenarios", {})
    
    # Build combined data for Decision Matrix (excluding disqualified)
    combined_data = []
    combined_data_all = []  # Keep all for display purposes
    w_mcda = COMPOSITE_DEFAULT_MCDA_WEIGHT_PCT / 100.0
    w_ev = 1.0 - w_mcda
    if ranking_list_all and scenarios_state:
        for alt_id, scenario in scenarios_state.items():
            alt_name = scenario.get("name", "")
            ev = scenario_expected_value(
                scenario.get("p_best", 0.5),
                scenario.get("worst_score", 0),
                scenario.get("best_score", 0)
            )
            ev_scaled = ev / 2.0
            uncertainty = scenario.get("best_score", 0) - scenario.get("worst_score", 0)
            
            mcda_score = next((item["score"] for item in ranking_list_all if item["alternativa"] == alt_name), None)
            
            if mcda_score is not None:
                composite = w_mcda * mcda_score + w_ev * ev_scaled
                item_data = {
                    "name": alt_name,
                    "alt_id": alt_id,
                    "mcda": mcda_score,
                    "ev": ev,
                    "ev_scaled": ev_scaled,
                    "uncertainty": uncertainty,
                    "composite": composite,
                    "disqualified": alt_name in disqualified_names
                }
                combined_data_all.append(item_data)
                if alt_name not in disqualified_names:
                    combined_data.append(item_data)
    
    # Sort combined data by composite
    combined_sorted = sorted(combined_data, key=lambda x: x["composite"], reverse=True) if combined_data else []
    combined_sorted_all = sorted(combined_data_all, key=lambda x: x["composite"], reverse=True) if combined_data_all else []
    
    # Show error only if ALL alternatives are disqualified
    if disqualified_alts:
        num_qualified = len(alt_names) - len(disqualified_alts)
        if num_qualified == 0:
            st.error("⚠️ **Todas las alternativas están descalificadas** por no cumplir los No Negociables. No hay recomendación disponible.")
            with st.expander("Ver alternativas descalificadas"):
                for alt_name, failed_constraints in disqualified_alts.items():
                    alt_text = next((a["text"] for a in st.session_state.alts if a["id"] == alt_name), alt_name)
                    st.markdown(f"- **{alt_text}**: No cumple *{', '.join(failed_constraints)}*")
            return
    
    # ===========================================
    # COMPUTE ROBUSTNESS (needed by Hero badge)
    # ===========================================
    
    robustness = None
    qualified_alt_names = [name for name in alt_names if name not in disqualified_names]
    
    if ranking_list and not scores_df.empty and len(crit) > 0 and len(qualified_alt_names) >= 2:
        robustness = calculate_robustness_index(scores_df.copy(), crit, qualified_alt_names)
    
    # ===========================================
    # HERO SECTION - Winner Announcement
    # ===========================================
    
    # Robustness badge helper
    def _robustness_badge() -> str:
        if robustness and robustness["baseline_winner"]:
            r_label = robustness["label"].capitalize()
            color_map = {"Robusto": "#38a169", "Moderado": "#d69e2e", "Frágil": "#e53e3e"}
            badge_color = color_map.get(r_label, "#718096")
            return f"""<span style="background: {badge_color}; color: white; padding: 0.3rem 0.8rem; 
                             border-radius: 20px; font-size: 0.85rem;">
                    {robustness['emoji']} {r_label} — Robustez {robustness['robustness_pct']}%
                </span>"""
        return ""
    
    if combined_sorted:
        winner = combined_sorted[0]
        badge = _robustness_badge()
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem; text-align: center;">
            <p style="color: #aaa; margin: 0; font-size: 0.9rem;">ALTERNATIVA RECOMENDADA</p>
            <h1 style="color: #fff; margin: 0.5rem 0; font-size: 2.2rem;">🏆 {winner['name']}</h1>
            <p style="color: #83c9ff; margin: 0; font-size: 1.1rem;">
                Puntuación Compuesta: <strong>{winner['composite']:.2f}</strong> / 5.00
            </p>
            <div style="margin-top: 1rem;">{badge}</div>
        </div>
        """, unsafe_allow_html=True)
        
    elif ranking_list:
        winner = ranking_list[0]
        badge = _robustness_badge()
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); 
                    padding: 2rem; border-radius: 12px; margin-bottom: 1.5rem; text-align: center;">
            <p style="color: #aaa; margin: 0; font-size: 0.9rem;">ALTERNATIVA RECOMENDADA (MCDA)</p>
            <h1 style="color: #fff; margin: 0.5rem 0; font-size: 2.2rem;">🏆 {winner['alternativa']}</h1>
            <p style="color: #83c9ff; margin: 0; font-size: 1.1rem;">
                Puntuación MCDA: <strong>{winner['score']:.2f}</strong> / 5.00
            </p>
            <div style="margin-top: 1rem;">{badge}</div>
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
        # Two-column layout: Radar Chart + Decision Matrix
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("####")
            try:
                top_alts = [item["alternativa"] for item in ranking_list[:3]]
                fig_radar = create_mcda_radar_chart(scores_df, prioridad_names, top_alts, showlegend=False)
                fig_radar.update_layout(height=350, margin=dict(l=30, r=30, t=30, b=30))
                st.plotly_chart(fig_radar, width="stretch", config={"displayModeBar": False})
                st.caption("Top 3 alternativas por criterio")
            except Exception:
                st.info("💡 Radar no disponible")
        
        with col2:
            st.markdown("####")
            fig_matrix = create_decision_matrix_chart(combined_data)
            st.plotly_chart(fig_matrix, width="stretch", config={"displayModeBar": False})
            st.caption("Tamaño/transparencia = incertidumbre")
    
    elif ranking_list:
        # Only MCDA available - show radar chart full width
        st.markdown("#####")
        try:
            top_alts = [item["alternativa"] for item in ranking_list[:3]]
            fig_radar = create_mcda_radar_chart(scores_df, prioridad_names, top_alts)
            st.plotly_chart(fig_radar, width="stretch", config={"displayModeBar": False})
        except Exception:
            st.info("💡 Complete la evaluación para ver el gráfico radar")
        
        st.info("💡 Completa los **Escenarios** para ver la Matriz de Decisión combinada")
    
    # Stacked bar chart: contribution by criterion (always breakdown mode)
    if ranking_list and crit:
        st.markdown("###")
        
        colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', '#00BCD4', '#FFEB3B', '#795548']
        priority_colors = {c["name"]: colors[i % len(colors)] for i, c in enumerate(crit)}
        weight_map = normalize_weights(crit)
        
        fig_bar = go.Figure()
        
        for i, item in enumerate(reversed(ranking_list)):
            alt_name = item['alternativa']
            alt_scores = st.session_state.get("mcda_scores", {}).get(alt_name, {})
            
            for criterion in prioridad_names:
                score = alt_scores.get(criterion, 0)
                weight = weight_map.get(criterion, 0)
                contribution = score * weight
                
                fig_bar.add_trace(go.Bar(
                    y=[alt_name],
                    x=[contribution],
                    orientation='h',
                    name=criterion,
                    marker_color=priority_colors.get(criterion, '#999'),
                    hovertemplate=f"<b>{criterion}</b><br>{score:.1f} × {weight:.1%} = {contribution:.2f}<extra></extra>",
                    showlegend=False
                ))
        
        fig_bar.update_layout(
            barmode='stack',
            height=max(200, len(ranking_list) * 50),
            margin=dict(l=10, r=60, t=10, b=10),
            showlegend=False,
            xaxis=dict(range=[0, ranking_list[0]['score'] * 1.2], showgrid=True, gridcolor='#eee'),
            yaxis=dict(showgrid=False),
            bargap=0.3
        )
        st.plotly_chart(fig_bar, width="stretch", config={'displayModeBar': False})
    
    # ===========================================
    # ROBUSTNESS INDEX (detail section)
    # ===========================================
    
    if robustness and robustness["baseline_winner"]:
        st.markdown("---")
        st.markdown("## 🛡️ Índice de Robustez")
        
        r_pct = robustness["robustness_pct"]
        r_emoji = robustness["emoji"]
        r_label = robustness["label"].capitalize()
        
        # Main score display
        col_r1, col_r2 = st.columns([1, 2])
        
        with col_r1:
            # Color based on label
            color_map = {"Robusto": "#38a169", "Moderado": "#d69e2e", "Frágil": "#e53e3e"}
            color = color_map.get(r_label, "#718096")
            
            st.markdown(f"""
            <div style="text-align: center; padding: 1rem; border: 2px solid {color}; border-radius: 12px;">
                <div style="font-size: 2.5em; font-weight: 700; color: {color};">{r_pct}%</div>
                <div style="font-size: 1.1em; font-weight: 600;">{r_emoji} {r_label}</div>
                <div style="font-size: 0.8em; color: #888; margin-top: 0.3rem;">
                    ¿Cambia el top 1 si perturbamos los datos?
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_r2:
            st.markdown(f"""
            | Test | Estabilidad |
            |------|------------|
            | Pesos ±20% | **{robustness['weight_stability']}%** |
            | Puntuaciones ±1 | **{robustness['score_stability']}%** |
            | Combinado | **{robustness['combined_stability']}%** |
            """)
            
            if robustness["dominant_criterion"]:
                if robustness["dominant_removal_flips"]:
                    st.warning(f"⚠️ Si eliminamos el criterio dominante (**{robustness['dominant_criterion']}**), el ganador cambia a *{robustness['dominant_removal_new_winner']}*")
                else:
                    st.success(f"✓ Incluso sin el criterio dominante (**{robustness['dominant_criterion']}**), **{robustness['baseline_winner']}** sigue ganando")
        
        # Actionable guidance based on label
        if r_label == "Frágil":
            st.error("🔴 **La recomendación es inestable.** Antes de decidir: recopila más información, valida las puntuaciones con datos reales, o reduce la incertidumbre en los criterios clave.")
        elif r_label == "Moderado":
            st.info("🟡 **La recomendación es sensible a los supuestos.** Revisa si las puntuaciones y pesos reflejan bien la realidad antes de comprometerte.")
    
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
    
    # Insight 6: Robustness
    if robustness and robustness["baseline_winner"]:
        r_label = robustness["label"]
        if r_label == "frágil":
            insights.append(f"🔴 **Resultado frágil** ({robustness['robustness_pct']}%): la recomendación de *{robustness['baseline_winner']}* cambia fácilmente al perturbar los datos. Necesitas más información o validar supuestos")
        elif r_label == "moderado":
            insights.append(f"🟡 **Resultado moderado** ({robustness['robustness_pct']}%): la recomendación de *{robustness['baseline_winner']}* es sensible a cambios en pesos o puntuaciones")
        else:
            insights.append(f"🟢 **Resultado robusto** ({robustness['robustness_pct']}%): *{robustness['baseline_winner']}* se mantiene como ganador incluso perturbando los datos")
    
    if insights:
        for insight in insights:
            st.markdown(f"- {insight}")
    else:
        st.info("💡 Completa más secciones para generar insights automatizados")
    
    # ===========================================
    # CONTEXTO DE LA DECISIÓN (merged reference section)
    # ===========================================

    objetivo = st.session_state.get("objetivo", "").strip()
    estrategia = st.session_state.get("estrategia_corporativa", "").strip()
    past_decisions = [d for d in st.session_state.get("past_decisions", []) if d.get("decision", "").strip()]
    kpis = st.session_state.get("kpis", [])
    valid_kpis = [k for k in kpis if k.get("name", "").strip()]
    stakeholders = st.session_state.get("stakeholders", [])
    valid_stakeholders = [s for s in stakeholders if s.get("name", "").strip()]
    timeline_items = [t for t in st.session_state.get("timeline_items", []) if t.get("event", "").strip()]
    quant_notes = st.session_state.get("quantitative_notes", "").strip()
    qual_notes = st.session_state.get("qualitative_notes", "").strip()

    has_context = any([objetivo, estrategia, past_decisions, valid_kpis,
                       valid_stakeholders, timeline_items, quant_notes, qual_notes])

    if has_context:
        # st.markdown("---")
        with st.expander("📋 Contexto de la Decisión", expanded=False):
            # Row 1: Objetivo + Estrategia
            if objetivo or estrategia:
                ctx_cols = st.columns(2 if (objetivo and estrategia) else 1)
                col_idx = 0
                if objetivo:
                    with ctx_cols[col_idx]:
                        st.markdown("**🎯 Objetivo**")
                        st.markdown(objetivo)
                    col_idx += 1
                if estrategia:
                    with ctx_cols[col_idx]:
                        st.markdown("**🏢 Estrategia**")
                        st.markdown(estrategia)

            # Row 2: Past Decisions
            if past_decisions:
                st.markdown("---")
                st.markdown("**📚 Decisiones Similares Pasadas**")
                for d in past_decisions[:3]:
                    st.markdown(f"- **{d['decision']}**")
                    details = []
                    if d.get("results", "").strip():
                        details.append(f"Resultado: {d['results'].strip()}")
                    if d.get("lessons", "").strip():
                        details.append(f"Lección: {d['lessons'].strip()}")
                    if details:
                        st.caption(" · ".join(details))

            # Row 3: KPIs + Stakeholders
            if valid_kpis or valid_stakeholders:
                st.markdown("---")
                kpi_stake_cols = st.columns(2)
                with kpi_stake_cols[0]:
                    if valid_kpis:
                        st.markdown("**📊 KPIs Relevantes**")
                        for kpi in valid_kpis[:5]:
                            value_str = str(kpi.get("value", "N/A"))
                            unit_str = f" {kpi.get('unit', '')}" if kpi.get("unit", "").strip() else ""
                            st.markdown(f"- **{kpi.get('name', '')}:** {value_str}{unit_str}")
                with kpi_stake_cols[1]:
                    if valid_stakeholders:
                        st.markdown("**👥 Stakeholders**")
                        for sh in valid_stakeholders[:5]:
                            name = sh.get("name", "")
                            opinion = sh.get("opinion", "")
                            if opinion:
                                st.markdown(f"- **{name}:** {opinion}")
                            else:
                                st.markdown(f"- **{name}**")

            # Row 4: Timeline
            if timeline_items:
                st.markdown("---")
                st.markdown("**📅 Timeline Clave**")
                for t in timeline_items[:5]:
                    date_str = t["date"].strftime("%d/%m/%Y") if t.get("date") else ""
                    st.markdown(f"- **{t['event']}** {f'— {date_str}' if date_str else ''}")

            # Row 5: Notes
            if quant_notes or qual_notes:
                st.markdown("---")
                note_cols = st.columns(2 if (quant_notes and qual_notes) else 1)
                col_idx = 0
                if quant_notes:
                    with note_cols[col_idx]:
                        st.markdown("**📝 Notas Cuantitativas**")
                        st.caption(quant_notes)
                    col_idx += 1
                if qual_notes:
                    with note_cols[col_idx]:
                        st.markdown("**📝 Notas Cualitativas**")
                        st.caption(qual_notes)

    st.markdown("---")

    # ===========================================
    # RANKING TABLES
    # ===========================================
    
    st.markdown("## 🏅 Rankings y Datos")
    
    if combined_sorted:
        # Row 1: MCDA ranking + EV ranking side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Ranking MCDA")
            mcda_df = pd.DataFrame([{
                "#": i + 1,
                "Alternativa": d["name"],
                "Puntuación": d["mcda"]
            } for i, d in enumerate(sorted(combined_sorted, key=lambda x: x["mcda"], reverse=True))])
            
            st.dataframe(
                mcda_df.style.format({"Puntuación": "{:.2f}"}),
                hide_index=True,
                width="stretch"
            )
        
        with col2:
            st.markdown("#### Ranking Valor Esperado")
            ev_df = pd.DataFrame([{
                "#": i + 1,
                "Alternativa": d["name"],
                "EV": d["ev_scaled"]
            } for i, d in enumerate(sorted(combined_sorted, key=lambda x: x["ev_scaled"], reverse=True))])
            
            st.dataframe(
                ev_df.style.format({"EV": "{:.2f}"}),
                hide_index=True,
                width="stretch"
            )
        
        # Row 2: Composite ranking + Weights side by side
        col3, col4 = st.columns(2)
        
        with col3:
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
                width="stretch"
            )
        
        with col4:
            st.markdown("#### Pesos de Prioridades")
            weight_map = normalize_weights(crit)
            weights_df = pd.DataFrame([{
                "Prioridad": c["name"],
                "Peso": weight_map.get(c["name"], 0)
            } for c in crit])
            
            st.dataframe(
                weights_df.style.format({"Peso": "{:.1%}"}),
                hide_index=True,
                width="stretch"
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
                width="stretch"
            )
        
        with col2:
            st.markdown("#### Pesos de Prioridades")
            weight_map = normalize_weights(crit)
            weights_df = pd.DataFrame([{
                "Prioridad": c["name"],
                "Peso": weight_map.get(c["name"], 0)
            } for c in crit])
            
            st.dataframe(
                weights_df.style.format({"Peso": "{:.1%}"}),
                hide_index=True,
                width="stretch"
            )
    
    # No Negociables table
    no_negociables = st.session_state.get("no_negociables", [])
    valid_no_neg = [c for c in no_negociables if c.get("text", "").strip()]
    no_neg_scores = st.session_state.get("no_negociables_scores", {})
    
    if valid_no_neg:
        st.markdown("#### 🚫 No Negociables")
        
        # Build table: rows = alternatives, columns = constraints
        no_neg_rows = []
        for alt in st.session_state.get("alts", []):
            alt_name = alt["text"].strip()
            if not alt_name:
                continue
            row = {"Alternativa": alt_name}
            alt_scores_nn = no_neg_scores.get(alt["id"], {})
            all_pass = True
            for constraint in valid_no_neg:
                passes = alt_scores_nn.get(constraint["id"], False)
                row[constraint["text"]] = "✅" if passes else "❌"
                if not passes:
                    all_pass = False
            row["Estado"] = "Cualificada" if all_pass else "Descalificada"
            no_neg_rows.append(row)
        
        if no_neg_rows:
            no_neg_df = pd.DataFrame(no_neg_rows)
            st.dataframe(no_neg_df, hide_index=True, width="stretch")
    
    # ===========================================
    # EXPORT CTA
    # ===========================================
    
    st.markdown("---")
    
    # Prominent export call-to-action
    st.markdown("""
    <div style="background: linear-gradient(135deg, #1a365d 0%, #2c5282 100%); 
                padding: 1.5rem; border-radius: 12px; text-align: center; margin: 1rem 0;">
        <p style="color: #fff; margin: 0; font-size: 1.1rem; font-weight: 600;">
            📥 ¿Listo para compartir tu análisis?
        </p>
        <p style="color: #bee3f8; margin: 0.5rem 0 0 0; font-size: 0.9rem;">
            Exporta en JSON o Excel desde el menú ⚙️ para guardar o presentar a tu equipo
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⚙️ Abrir opciones de exportación", width="stretch", type="primary"):
            st.session_state["show_sidebar"] = True
            st.rerun()
    
    import streamlit.components.v1 as components
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        components.html("""
        <button id="printBtn"
                style="width:100%; padding:0.55rem 1rem; border:1px solid #ccc; border-radius:8px;
                       background:#fafafa; cursor:pointer; font-size:0.9rem; color:#444;
                       display:inline-flex; align-items:center; justify-content:center; gap:0.5rem;"
                onmouseover="this.style.background='#eee'" onmouseout="this.style.background='#fafafa'">
            🖨️ Imprimir / Guardar PDF
        </button>
        <script>
            document.getElementById('printBtn').addEventListener('click', function() {
                window.parent.print();
            });
        </script>
        """, height=50)

    # ===========================================
    # OBSERVA TUS EMOCIONES
    # ===========================================

    st.markdown("---")
    st.markdown("### 🪞 Observa tus emociones")
    st.caption(
        "Las emociones llevan información sobre valores y prioridades que a menudo son inconscientes. "
        "Parar y observar cómo te sientes ante estos resultados puede ser muy valioso para tu decisión."
    )

    emotion_notes = st.text_area(
        "¿Cómo te sientes al ver estos resultados?",
        value=st.session_state.get("emotion_notes", ""),
        placeholder="Escribe libremente lo que sientes, sin filtrar...",
        height=120,
        key="emotion_notes_widget",
    )
    st.session_state["emotion_notes"] = emotion_notes

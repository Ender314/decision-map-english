# -*- coding: utf-8 -*-
"""
Scenarios (Scenario Planning) tab - Simplified version.
Clean scenario analysis without over-engineering.
"""

import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from config.constants import PROBABILITY_STEPS
from utils.calculations import scenario_expected_value, get_disqualified_alternatives
from utils.ui_helpers import help_tip, get_tooltip


def render_scenarios_tab():
    """Render the Scenarios (Scenario Planning) tab."""
    st.markdown(f"### 🔮 Planificación de Escenarios", unsafe_allow_html=True)

    # Need alternativas
    all_alts = [a for a in st.session_state.alts if a["text"].strip()]
    if not all_alts:
        st.info("🔮 Los escenarios te ayudan a pensar en el mejor y peor caso de cada alternativa. Primero define tus **Alternativas** en la pestaña correspondiente.")
        return
    
    # Filter out disqualified alternatives (failed No Negociables)
    disqualified_alts = get_disqualified_alternatives()
    alts = [a for a in all_alts if a["id"] not in disqualified_alts]
    
    # Show error only if ALL alternatives are disqualified
    if disqualified_alts and len(alts) == 0:
        st.error(f"⚠️ **Todas las alternativas están descalificadas** por no cumplir los No Negociables. No hay escenarios disponibles.")
        with st.expander("Ver alternativas descalificadas"):
            for alt_id, failed_constraints in disqualified_alts.items():
                alt_text = next((a["text"] for a in all_alts if a["id"] == alt_id), alt_id)
                st.markdown(f"- ~~{alt_text}~~: No cumple *{', '.join(failed_constraints)}*")
        return

    # Initialize scenarios if needed
    if "scenarios" not in st.session_state:
        st.session_state.scenarios = {}
    
    # Clean up orphaned scenario widget states when alternatives change
    current_alt_ids = {alt["id"] for alt in alts}
    scenario_widget_prefixes = ["worst_desc_", "pbest_", "best_desc_", "impact_range_"]
    
    orphaned_keys = []
    for key in st.session_state.keys():
        for prefix in scenario_widget_prefixes:
            if key.startswith(prefix):
                alt_id = key[len(prefix):]
                if alt_id not in current_alt_ids:
                    orphaned_keys.append(key)
                break
    
    for key in orphaned_keys:
        del st.session_state[key]
    
    # Sync imported scenario data to widget states (important for data import)
    for alt in alts:
        alt_id = alt["id"]
        if alt_id in st.session_state.scenarios:
            scenario_data = st.session_state.scenarios[alt_id]
            
            # Sync text inputs
            worst_key = f"worst_desc_{alt_id}"
            if worst_key not in st.session_state and scenario_data.get("worst_desc"):
                st.session_state[worst_key] = scenario_data["worst_desc"]
            
            best_key = f"best_desc_{alt_id}"
            if best_key not in st.session_state and scenario_data.get("best_desc"):
                st.session_state[best_key] = scenario_data["best_desc"]
            
            # Sync probability slider
            pbest_key = f"pbest_{alt_id}"
            if pbest_key not in st.session_state and scenario_data.get("p_best_pct") is not None:
                st.session_state[pbest_key] = scenario_data["p_best_pct"]
            
            # Sync range slider
            range_key = f"impact_range_{alt_id}"
            if range_key not in st.session_state:
                worst_score = scenario_data.get("worst_score", 3.0)
                best_score = scenario_data.get("best_score", 7.0)
                st.session_state[range_key] = (int(worst_score), int(best_score))
    
    # Process each alternative
    for alt in alts:
        alt_id, alt_name = alt["id"], alt["text"].strip()
        
        # Initialize scenario data for this alternative
        if alt_id not in st.session_state.scenarios:
            st.session_state.scenarios[alt_id] = {
                "name": alt_name,
                "best_desc": "",
                "best_score": 7.0,
                "worst_desc": "",
                "worst_score": 3.0,
                "p_best": 0.5,
                "p_best_pct": 50,
            }
        
        scenario_data = st.session_state.scenarios[alt_id]
        scenario_data["name"] = alt_name  # Keep name synced with current alternative text
        
        with st.expander(f"⚙️ {alt_name}", expanded=False):
            # Row 1: Worst → Probabilidad → Best
            c1, c2, c3 = st.columns([1.8, 1.2, 1.8])
            
            with c1:
                st.markdown("**Peor escenario**")
                # Initialize widget state if not exists
                worst_key = f"worst_desc_{alt_id}"
                if worst_key not in st.session_state:
                    st.session_state[worst_key] = scenario_data.get("worst_desc", "")
                
                worst_desc = st.text_input(
                    "Descripción (worst)",
                    key=worst_key,
                    label_visibility="collapsed",
                    placeholder="¿Qué pasa si sale mal?"
                )
                # Sync widget state back to data structure
                scenario_data["worst_desc"] = worst_desc
            
            with c2:
                st.markdown("######")
                # Initialize widget state if not exists
                pbest_key = f"pbest_{alt_id}"
                if pbest_key not in st.session_state:
                    st.session_state[pbest_key] = scenario_data.get("p_best_pct", 50)
                
                p_best_pct = st.select_slider(
                    "Probabilidad de **best**",
                    options=PROBABILITY_STEPS,
                    key=pbest_key,
                    label_visibility="collapsed"
                )
                # Sync widget state back to data structure
                scenario_data["p_best_pct"] = p_best_pct
                scenario_data["p_best"] = p_best_pct / 100.0
            
            with c3:
                st.markdown("**Mejor scenario**")
                # Initialize widget state if not exists
                best_key = f"best_desc_{alt_id}"
                if best_key not in st.session_state:
                    st.session_state[best_key] = scenario_data.get("best_desc", "")
                
                best_desc = st.text_input(
                    "Descripción (best)",
                    key=best_key,
                    label_visibility="collapsed",
                    placeholder="¿Qué pasa si todo va muy bien?"
                )
                # Sync widget state back to data structure
                scenario_data["best_desc"] = best_desc

            # Row 2: Single range slider for Impacto (0–10)
            st.markdown("")
            # Initialize widget state if not exists
            range_key = f"impact_range_{alt_id}"
            if range_key not in st.session_state:
                default_range = (int(scenario_data.get("worst_score", 2)), int(scenario_data.get("best_score", 7)))
                st.session_state[range_key] = default_range
            
            worst_best = st.slider(
                "Impacto (0–10): mínimo <- peor, mejor -> máximo",
                min_value=0, max_value=10, step=1,
                key=range_key
            )
            # Sync widget state back to data structure
            scenario_data["worst_score"] = float(worst_best[0])
            scenario_data["best_score"] = float(worst_best[1])

            # Calculate expected value
            ev = scenario_expected_value(
                scenario_data["p_best"], 
                scenario_data["worst_score"], 
                scenario_data["best_score"]
            )
            scenario_data["ev"] = ev
    
    # Create summary data for visualization (only qualified alternatives)
    qualified_alt_ids = {a["id"] for a in alts}
    summary_rows = []
    for alt_id, scenario_data in st.session_state.scenarios.items():
        if alt_id in qualified_alt_ids:
            summary_rows.append({
                "Alternativa": scenario_data["name"],
                "Worst": int(scenario_data["worst_score"]),
                "Best": int(scenario_data["best_score"]),
                "EV": scenario_data["ev"],
                "Range": scenario_data["best_score"] - scenario_data["worst_score"],
            })
    
    if not summary_rows:
        return
    
    # Sort by EV descending
    summary_df = pd.DataFrame(summary_rows).sort_values("EV", ascending=False)
    
    # Create violin plot
    try:
        # Import violin plot function
        from utils.violin_plots import create_seaborn_violin_modern
        
        # Create the plot
        fig, ax = create_seaborn_violin_modern(summary_rows)
        st.pyplot(fig)
        plt.close()
        
    except Exception as e:
        st.error(f"Error creating violin plot: {str(e)}")
        st.info("💡 Intenta ajustar los valores de los escenarios")
    
    st.caption("💎 **Violin Chart**: La anchura representa la densidad de probabilidad. Los diamantes brillantes indican el valor esperado (EV).")

    # Summary table
    with st.expander('Resumen escenarios'):
        st.dataframe(
            summary_df[["Alternativa", "Worst", "Best", "EV"]].style.format({"EV": "{:.2f}"}),
            use_container_width=True
        )

        st.caption("EV = p(best) × best + (1 − p(best)) × worst. Escala 0–10.")

    st.markdown("---")
    
    # Risk-Adjusted Decision Matrix
    st.markdown("### 🎯 Matriz de Decisión")
    
    # Get MCDA scores if available (filtered by qualified alternatives)
    mcda_ranking = []
    if "mcda_scores" in st.session_state and st.session_state.mcda_scores:
        from utils.calculations import normalize_weights, mcda_totals_and_ranking
        
        # Get scores DataFrame
        if "mcda_scores_df" in st.session_state and "mcda_criteria" in st.session_state:
            scores_df = st.session_state.mcda_scores_df
            _, mcda_ranking_all = mcda_totals_and_ranking(scores_df.copy(), st.session_state.mcda_criteria)
            # Filter out disqualified alternatives
            qualified_names = {a["text"].strip() for a in alts}
            mcda_ranking = [item for item in mcda_ranking_all if item["alternativa"] in qualified_names]
    
    if not mcda_ranking:
        st.info("💡 Completa la **Evaluación** para ver la Matriz de Decisión combinada.")
    else:
        # Build combined data
        combined_data = []
        for row in summary_rows:
            alt_name = row["Alternativa"]
            ev = row["EV"]
            ev_scaled = ev / 2.0  # Scale 0-10 to 0-5
            uncertainty = row["Range"]
            
            # Find MCDA score for this alternative
            mcda_score = next((item["score"] for item in mcda_ranking if item["alternativa"] == alt_name), None)
            
            if mcda_score is not None:
                # Composite: 50% MCDA + 50% EV (both in 0-5 scale)
                composite = 0.5 * mcda_score + 0.5 * ev_scaled
                combined_data.append({
                    "name": alt_name,
                    "mcda": mcda_score,
                    "ev": ev,
                    "ev_scaled": ev_scaled,
                    "uncertainty": uncertainty,
                    "composite": composite
                })
        
        if combined_data:
            # Create bubble chart
            fig = go.Figure()

            def wrap_legend_label(label: str, max_len: int = 26) -> str:
                parts = (label or "").split()
                if not parts:
                    return label or ""

                lines = []
                current = ""
                for part in parts:
                    candidate = part if not current else f"{current} {part}"
                    if len(candidate) <= max_len:
                        current = candidate
                    else:
                        if current:
                            lines.append(current)
                        current = part
                if current:
                    lines.append(current)

                return "<br>".join(lines)
            
            # Color scale based on composite score
            max_composite = max(d["composite"] for d in combined_data)
            min_composite = min(d["composite"] for d in combined_data)
            
            for item in combined_data:
                # Normalize composite for color (0-1)
                if max_composite > min_composite:
                    color_val = (item["composite"] - min_composite) / (max_composite - min_composite)
                else:
                    color_val = 0.5
                
                # Bubble size based on uncertainty (smaller uncertainty = smaller bubble)
                bubble_size = 20 + item["uncertainty"] * 16
                
                # Opacity inversely proportional to uncertainty (larger bubbles = more transparent)
                # Range from 0.9 (low uncertainty) to 0.4 (high uncertainty)
                max_uncertainty = 10  # Max possible range
                opacity = 0.95 - (item["uncertainty"] / max_uncertainty) * 0.85
                
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
                    name=wrap_legend_label(item["name"]),
                    hovertemplate=(
                        f"<b>{item['name']}</b><br>"
                        f"MCDA: {item['mcda']:.2f}<br>"
                        f"EV: {item['ev']:.2f} (escala 0-10)<br>"
                        f"Incertidumbre: {item['uncertainty']:.0f}<br>"
                        f"Compuesto: {item['composite']:.2f}"
                        "<extra></extra>"
                    )
                ))
            
            # Add quadrant lines at midpoint (2.5 on 0-5 scale)
            fig.add_hline(y=2.5, line_dash="dash", line_color="#ccc", opacity=0.5)
            fig.add_vline(x=2.5, line_dash="dash", line_color="#ccc", opacity=0.5)
            
            # Add quadrant labels
            fig.add_annotation(x=1.25, y=4.5, text="Alto potencial", showarrow=False, font=dict(size=10, color="#888"))
            fig.add_annotation(x=3.75, y=4.5, text="✓ Óptimo", showarrow=False, font=dict(size=11, color="#2e7d32", weight="bold"))
            fig.add_annotation(x=1.25, y=0.5, text="Evitar", showarrow=False, font=dict(size=10, color="#888"))
            fig.add_annotation(x=3.75, y=0.5, text="Seguro limitado", showarrow=False, font=dict(size=10, color="#888"))
            
            fig.update_layout(
                height=400,
                margin=dict(l=60, r=170, t=40, b=60),
                showlegend=True,
                legend=dict(
                    title=dict(text="Alternativas"),
                    x=1.02,
                    y=1.0,
                    xanchor="left",
                    yanchor="top",
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="rgba(0,0,0,0.15)",
                    borderwidth=1,
                    itemsizing="constant"
                ),
                xaxis=dict(
                    title="Puntuación MCDA (criterios)",
                    range=[0, 5.2],
                    showgrid=False,
                    dtick=1
                ),
                yaxis=dict(
                    title="Valor Esperado (escenarios)",
                    range=[0, 5.2],
                    showgrid=False,
                    dtick=1
                ),
                plot_bgcolor="white"
            )
            
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.caption("📐 **Tamaño de burbuja** = incertidumbre (rango entre peor y mejor escenario). Burbujas más grandes indican mayor variabilidad.")
            
            # Composite ranking table
            st.markdown("")
            st.markdown("**Ranking Compuesto**")
            
            # Sort by composite descending
            combined_sorted = sorted(combined_data, key=lambda x: x["composite"], reverse=True)
            
            ranking_df = pd.DataFrame([{
                "Alternativa": d["name"],
                "MCDA": d["mcda"],
                "EV (0-5)": d["ev_scaled"],
                "Incertidumbre": d["uncertainty"],
                "Compuesto": d["composite"]
            } for d in combined_sorted])
            
            st.dataframe(
                ranking_df.style.format({
                    "MCDA": "{:.2f}",
                    "EV (0-5)": "{:.2f}",
                    "Incertidumbre": "{:.0f}",
                    "Compuesto": "{:.2f}"
                }),
                use_container_width=True
            )
            
            # Winner announcement
            winner = combined_sorted[0]
            st.success(f"🏆 **Recomendación final**: {winner['name']} (Compuesto: {winner['composite']:.2f})")
            st.caption("Compuesto = 50% MCDA + 50% EV. Escala 0–5.")
    
    st.markdown("---")
    
    # Contextual help - placed after content where confusion might arise
    with st.expander("*\"¿Por qué hago esto si ya puntué todo en la evaluación?\"*", expanded=False):
        st.markdown("""
        **La evaluación MCDA asume que sabes exactamente qué va a pasar.** Pero la realidad es incierta.
        
        Los escenarios te ayudan a responder:
        - *"¿Qué pasa si sale mal?"* → Define el peor caso
        - *"¿Qué pasa si sale bien?"* → Define el mejor caso  
        - *"¿Qué tan probable es cada uno?"* → Estima la probabilidad
        
        **Resultado:** Un **Valor Esperado** que combina tu puntuación MCDA con la incertidumbre real de cada alternativa.
        
        *Ejemplo: Una alternativa puede puntuar alto en MCDA pero tener mucha incertidumbre (alto riesgo). Otra puede puntuar menos pero ser más predecible (bajo riesgo).*
        """)



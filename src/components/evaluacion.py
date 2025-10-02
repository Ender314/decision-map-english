# -*- coding: utf-8 -*-
"""
Evaluación (MCDA Evaluation) tab - Simplified version.
Clean MCDA implementation without over-engineering.
"""

import streamlit as st
import pandas as pd
from utils.calculations import normalize_weights, mcda_totals_and_ranking
from utils.visualizations import create_mcda_radar_chart


def render_evaluacion_tab():
    """Render the Evaluación (MCDA Evaluation) tab."""
    st.subheader("Evaluación")
    
    # Get alternatives and priorities
    alt_names = [a["text"].strip() for a in st.session_state.alts if a["text"].strip()]
    prioridad_names = [p["text"].strip() for p in st.session_state.priorities if p["text"].strip()]
    
    if not alt_names:
        st.info("💡 Añade al menos una **Alternativa** en la pestaña *Alternativas* para poder evaluarlas.")
        return
    
    if not prioridad_names:
        st.info("💡 Define al menos una **Prioridad** en la pestaña *Prioridades* para poder hacer la evaluación.")
        return
    
    # MCDA Criteria weights
    st.markdown("### ⚖️ Pesos de los Criterios")
    st.markdown("Ajusta la importancia relativa de cada criterio:")
    
    # Initialize criteria if needed
    if not st.session_state.mcda_criteria or len(st.session_state.mcda_criteria) != len(prioridad_names):
        st.session_state.mcda_criteria = [
            {"name": name, "weight": 1.0 / len(prioridad_names)} 
            for name in prioridad_names
        ]
    
    # Weight sliders
    for i, criterion in enumerate(st.session_state.mcda_criteria):
        if criterion["name"] in prioridad_names:
            weight = st.slider(
                criterion["name"],
                min_value=0.0,
                max_value=1.0,
                value=float(criterion["weight"]),
                step=0.05,
                key=f"weight_{criterion['name']}"
            )
            st.session_state.mcda_criteria[i]["weight"] = weight
    
    # Normalize weights
    weight_map = normalize_weights(st.session_state.mcda_criteria)
    
    # Show normalized weights
    with st.expander("Pesos Normalizados"):
        for name, weight in weight_map.items():
            st.markdown(f"**{name}**: {weight:.1%}")
    
    st.markdown("---")
    
    # MCDA Scoring Matrix
    st.markdown("### 📊 Matriz de Evaluación")
    st.markdown("Evalúa cada alternativa en cada criterio (escala 0-5):")
    
    # Initialize scores if needed
    if "mcda_scores" not in st.session_state:
        st.session_state.mcda_scores = {}
    
    # Create scoring matrix
    scores_data = []
    
    for alt_name in alt_names:
        if alt_name not in st.session_state.mcda_scores:
            st.session_state.mcda_scores[alt_name] = {}
        
        st.markdown(f"**{alt_name}**")
        cols = st.columns(len(prioridad_names))
        
        row_data = {"Alternativa": alt_name}
        
        for i, criterion in enumerate(prioridad_names):
            with cols[i]:
                current_score = st.session_state.mcda_scores[alt_name].get(criterion, 2.5)
                score = st.slider(
                    criterion,
                    min_value=0.0,
                    max_value=5.0,
                    value=float(current_score),
                    step=0.5,
                    key=f"score_{alt_name}_{criterion}",
                    label_visibility="collapsed"
                )
                st.session_state.mcda_scores[alt_name][criterion] = score
                row_data[criterion] = score
        
        scores_data.append(row_data)
    
    # Create DataFrame for calculations
    scores_df = pd.DataFrame(scores_data).set_index("Alternativa")
    st.session_state.mcda_scores_df = scores_df
    
    st.markdown("---")
    
    # Results
    st.markdown("### 🏆 Resultados")
    
    # Calculate totals and ranking
    totals, ranking_list = mcda_totals_and_ranking(scores_df.copy(), st.session_state.mcda_criteria)
    
    if ranking_list:
        # Display ranking
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Ranking Final")
            ranking_df = pd.DataFrame(ranking_list)
            ranking_df['Posición'] = range(1, len(ranking_df) + 1)
            ranking_df['Puntuación'] = ranking_df['score'].round(2)
            ranking_df = ranking_df[['Posición', 'alternativa', 'Puntuación']]
            ranking_df.columns = ['#', 'Alternativa', 'Puntuación']
            
            st.dataframe(ranking_df, hide_index=True, use_container_width=True)
        
        with col2:
            st.markdown("#### Análisis Visual")
            try:
                # Create radar chart for top 3 alternatives
                top_alts = ranking_list[:3]
                fig = create_mcda_radar_chart(scores_df, prioridad_names, [alt["alternativa"] for alt in top_alts])
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.info("💡 Error al generar gráfico radar")
        
        # Winner announcement
        winner = ranking_list[0]
        st.success(f"🏆 **Alternativa recomendada**: {winner['alternativa']} (Puntuación: {winner['score']:.2f})")
        
        # Show score breakdown for winner
        with st.expander(f"Desglose de puntuación - {winner['alternativa']}"):
            winner_scores = st.session_state.mcda_scores[winner['alternativa']]
            for criterion, score in winner_scores.items():
                weight = weight_map.get(criterion, 0)
                weighted_score = score * weight
                st.markdown(f"**{criterion}**: {score:.1f} × {weight:.1%} = {weighted_score:.2f}")
    else:
        st.info("💡 Completa la evaluación para ver los resultados")

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
    st.subheader("⚖️ Evaluación")
    
    # Get alternatives and priorities
    alt_names = [a["text"].strip() for a in st.session_state.alts if a["text"].strip()]
    prioridad_names = [p["text"].strip() for p in st.session_state.priorities if p["text"].strip()]
    
    if not alt_names:
        st.info("💡 Añade al menos una **Alternativa** en la pestaña *Alternativas* para poder evaluarlas.")
        return
    
    if not prioridad_names:
        st.info("💡 Define al menos una **Prioridad** en la pestaña *Prioridades* para poder hacer la evaluación.")
        return
    

    
    # Initialize criteria if needed
    if not st.session_state.mcda_criteria or len(st.session_state.mcda_criteria) != len(prioridad_names):
        st.session_state.mcda_criteria = [
            {"name": name, "weight": 1.0 / len(prioridad_names)} 
            for name in prioridad_names
        ]
    
    # Create editable table for weights
    weight_data = []
    for criterion in st.session_state.mcda_criteria:
        if criterion["name"] in prioridad_names:
            weight_data.append({
                "Prioridad": criterion["name"],
                "Peso": criterion["weight"]
            })
    
    # Normalize weights (needed for calculations)
    weight_map = normalize_weights(st.session_state.mcda_criteria)
    
    # st.markdown("---")
    

    
    # Initialize scores if needed
    if "mcda_scores" not in st.session_state:
        st.session_state.mcda_scores = {}
    
    # Create scoring matrix
    scores_data = []
    
    # Add header row with alternative column + criterion names
    header_cols = st.columns([2] + [1] * len(prioridad_names))
    with header_cols[0]:
        pass
        # st.markdown("**Alternativa**")
    for i, criterion in enumerate(prioridad_names):
        with header_cols[i + 1]:
            st.markdown(f"**{criterion}**")
    
    st.markdown("")
    
    for alt_name in alt_names:
        if alt_name not in st.session_state.mcda_scores:
            st.session_state.mcda_scores[alt_name] = {}
        
        # Create table-like row with alternative name + sliders
        row_cols = st.columns([2] + [1] * len(prioridad_names))
        
        # Alternative name in first column
        with row_cols[0]:
            st.markdown(f"**{alt_name}**")
        
        row_data = {"Alternativa": alt_name}
        
        # Sliders in subsequent columns
        for i, criterion in enumerate(prioridad_names):
            with row_cols[i + 1]:
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
        # Visual Analysis first
        # st.markdown("#### 📈 Análisis Visual")
        try:
            # Create radar chart for top 3 alternatives
            top_alts = ranking_list[:3]
            fig = create_mcda_radar_chart(scores_df, prioridad_names, [alt["alternativa"] for alt in top_alts])
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.info("💡 Error al generar gráfico radar")
        
        st.markdown("")
        st.markdown("")
        
        # Ranking table second
        # st.markdown("#### 🏆 Ranking Final")
        ranking_df = pd.DataFrame(ranking_list)
        ranking_df['Posición'] = range(1, len(ranking_df) + 1)
        ranking_df['Puntuación'] = ranking_df['score'].round(2)
        ranking_df = ranking_df[['Posición', 'alternativa', 'Puntuación']]
        ranking_df.columns = ['#', 'Alternativa', 'Puntuación']
        
        st.dataframe(ranking_df, hide_index=True, use_container_width=True)
        
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

    st.markdown("---")  

    # Display as proper editable data table
    weight_df = pd.DataFrame(weight_data)
    
    edited_weights = st.data_editor(
        weight_df,
        column_config={
            "Prioridad": st.column_config.TextColumn(
                "Prioridad",
                disabled=True,
                width="medium"
            ),
            "Peso": st.column_config.NumberColumn(
                "Peso",
                min_value=0.0,
                max_value=1.0,
                step=0.05,
                format="%.2f",
                width="small"
            )
        },
        hide_index=True,
        use_container_width=True,
        key="weights_editor"
    )
    
    # Update session state with edited weights and check for changes
    weights_changed = False
    for i, row in edited_weights.iterrows():
        for j, criterion in enumerate(st.session_state.mcda_criteria):
            if criterion["name"] == row["Prioridad"]:
                old_weight = st.session_state.mcda_criteria[j]["weight"]
                new_weight = row["Peso"]
                if abs(old_weight - new_weight) > 0.001:  # Small threshold for float comparison
                    st.session_state.mcda_criteria[j]["weight"] = new_weight
                    weights_changed = True
                break
    
    # Trigger rerun if weights changed to update all calculations
    if weights_changed:
        st.rerun()
    
    # Recalculate normalized weights after edits
    updated_weight_map = normalize_weights(st.session_state.mcda_criteria)
    
    # Show normalized weights
    with st.expander("Pesos Normalizados"):
        for name, weight in updated_weight_map.items():
            st.markdown(f"**{name}**: {weight:.1%}")
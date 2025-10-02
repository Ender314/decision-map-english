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
    
    # Handle deferred weight changes from previous run
    if st.session_state.get("_weights_changed", False):
        st.session_state["_weights_changed"] = False
        st.rerun()
    
    # Clean up orphaned slider states when alternatives/priorities change
    current_slider_keys = set()
    for alt in st.session_state.alts:
        for priority in st.session_state.priorities:
            if alt["text"].strip() and priority["text"].strip():
                key = f"mcda_score_{alt['id']}_{priority['id']}"
                current_slider_keys.add(key)
    
    # Remove orphaned slider states
    orphaned_keys = [k for k in st.session_state.keys() if k.startswith("mcda_score_") and k not in current_slider_keys]
    for key in orphaned_keys:
        del st.session_state[key]
    
    # Get alternatives and priorities
    alt_names = [a["text"].strip() for a in st.session_state.alts if a["text"].strip()]
    prioridad_names = [p["text"].strip() for p in st.session_state.priorities if p["text"].strip()]
    
    if not alt_names:
        st.info("💡 Añade al menos una **Alternativa** en la pestaña *Alternativas* para poder evaluarlas.")
        return
    
    if not prioridad_names:
        st.info("💡 Define al menos una **Prioridad** en la pestaña *Prioridades* para poder hacer la evaluación.")
        return
    

    
    # Initialize or update criteria more carefully
    existing_criteria_names = {c["name"] for c in st.session_state.mcda_criteria}
    current_prioridad_names = set(prioridad_names)
    
    # Only reinitialize if priorities have fundamentally changed
    if not existing_criteria_names or existing_criteria_names != current_prioridad_names:
        # Preserve existing weights where possible
        old_weights = {c["name"]: c["weight"] for c in st.session_state.mcda_criteria}
        default_weight = 1.0 / len(prioridad_names) if prioridad_names else 0.5
        
        st.session_state.mcda_criteria = [
            {"name": name, "weight": old_weights.get(name, default_weight)} 
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
    

    
    # Initialize scores if needed and ensure all alternatives have score dictionaries
    if "mcda_scores" not in st.session_state:
        st.session_state.mcda_scores = {}
    
    # Ensure all current alternatives have score dictionaries
    for alt_name in alt_names:
        if alt_name not in st.session_state.mcda_scores:
            st.session_state.mcda_scores[alt_name] = {}
    
    # Sync imported scores to widget states (important for data import)
    for alt_name in alt_names:
        for criterion in prioridad_names:
            alt_id = next((a["id"] for a in st.session_state.alts if a["text"].strip() == alt_name), alt_name)
            criterion_id = next((p["id"] for p in st.session_state.priorities if p["text"].strip() == criterion), criterion)
            slider_key = f"mcda_score_{alt_id}_{criterion_id}"
            
            # If we have a stored score but no widget state, sync it
            stored_score = st.session_state.mcda_scores[alt_name].get(criterion)
            if stored_score is not None and slider_key not in st.session_state:
                st.session_state[slider_key] = float(stored_score)
    
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
                # Create stable key using alternative and criterion indices
                alt_id = next((a["id"] for a in st.session_state.alts if a["text"].strip() == alt_name), alt_name)
                criterion_id = next((p["id"] for p in st.session_state.priorities if p["text"].strip() == criterion), criterion)
                slider_key = f"mcda_score_{alt_id}_{criterion_id}"
                
                # Initialize slider state if not exists, using our stored value as default
                if slider_key not in st.session_state:
                    default_score = st.session_state.mcda_scores[alt_name].get(criterion, 2.5)
                    st.session_state[slider_key] = float(default_score)
                
                # Use slider with widget state as single source of truth
                score = st.slider(
                    criterion,
                    min_value=0.0,
                    max_value=5.0,
                    step=0.5,
                    key=slider_key,
                    label_visibility="collapsed"
                )
                
                # Sync widget state back to our data structure
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
        ranking_df.columns = ['', 'Alternativa', 'Puntuación']
        
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
    
    # Update session state with edited weights - avoid immediate rerun
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
    
    # Store weight change flag for next run instead of immediate rerun
    if weights_changed:
        st.session_state["_weights_changed"] = True
    
    # Recalculate normalized weights after edits
    updated_weight_map = normalize_weights(st.session_state.mcda_criteria)
    
    # Show normalized weights
    with st.expander("Pesos Normalizados"):
        for name, weight in updated_weight_map.items():
            st.markdown(f"**{name}**: {weight:.1%}")
# -*- coding: utf-8 -*-
"""
Evaluación (MCDA Evaluation) tab - Simplified version.
Clean MCDA implementation without over-engineering.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.calculations import normalize_weights, mcda_totals_and_ranking
from utils.visualizations import create_mcda_radar_chart


def get_position_based_weights(n: int) -> list:
    """Calculate default weights based on position: 1st=1, 2nd=0.5, ..., nth=1/n"""
    return [1.0 / (i + 1) for i in range(n)]


def render_evaluacion_tab():
    """Render the Evaluación (MCDA Evaluation) tab."""
    st.subheader("⚖️ Evaluación")
    
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
    

    
    # Initialize or update criteria based on priorities
    existing_criteria_names = [c["name"] for c in st.session_state.mcda_criteria]
    
    # Check if priorities changed (added/removed) or just reordered
    priorities_changed = set(existing_criteria_names) != set(prioridad_names)
    priorities_reordered = existing_criteria_names != prioridad_names
    
    if priorities_changed:
        # Priorities added or removed - rebuild with position-based weights
        position_weights = get_position_based_weights(len(prioridad_names))
        st.session_state.mcda_criteria = [
            {"name": name, "weight": position_weights[i]} 
            for i, name in enumerate(prioridad_names)
        ]
        # Reset override flag since structure changed
        st.session_state.weights_user_override = False
        # Clear pending_weights so they reinitialize from fresh mcda_criteria
        if "pending_weights" in st.session_state:
            del st.session_state.pending_weights
        # Clear weight slider widget states to avoid stale values
        for key in list(st.session_state.keys()):
            if key.startswith("weight_slider_"):
                del st.session_state[key]
    elif priorities_reordered and not st.session_state.get("weights_user_override", False):
        # Priorities just reordered and user hasn't manually edited - recalculate by position
        position_weights = get_position_based_weights(len(prioridad_names))
        st.session_state.mcda_criteria = [
            {"name": name, "weight": position_weights[i]} 
            for i, name in enumerate(prioridad_names)
        ]
    
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
    
    # Results FIRST
    st.markdown("### 🏆 Resultados")
    
    # Calculate totals and ranking using current mcda_criteria weights
    weight_map = normalize_weights(st.session_state.mcda_criteria)
    totals, ranking_list = mcda_totals_and_ranking(scores_df.copy(), st.session_state.mcda_criteria)
    
    if ranking_list:
        # Visual Analysis first
        try:
            # Create radar chart for top 3 alternatives
            top_alts = ranking_list[:3]
            fig = create_mcda_radar_chart(scores_df, prioridad_names, [alt["alternativa"] for alt in top_alts])
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.info("💡 Error al generar gráfico radar")
        
        st.markdown("")
        st.markdown("")
        
        # Ranking horizontal bar chart (winner uses same color as radar chart line)
        max_score = 5.0
        WINNER_COLOR = '#83c9ff'  # Match radar chart winner line color
        bar_colors = [WINNER_COLOR if i == 0 else '#D3D3D3' for i in range(len(ranking_list))]
        
        fig_ranking = go.Figure()
        # Reverse to show highest at top
        for i, item in enumerate(reversed(ranking_list)):
            color_idx = len(ranking_list) - 1 - i
            fig_ranking.add_trace(go.Bar(
                y=[item['alternativa']],
                x=[item['score']],
                orientation='h',
                marker_color=bar_colors[color_idx],
                text=f"{item['score']:.2f}",
                textposition='outside',
                textfont=dict(size=14, color='#333'),
                hovertemplate=f"<b>{item['alternativa']}</b><br>Puntuación: {item['score']:.2f}<extra></extra>"
            ))
        
        fig_ranking.update_layout(
            height=max(200, len(ranking_list) * 50),
            margin=dict(l=10, r=60, t=10, b=10),
            showlegend=False,
            # xaxis=dict(range=[0, max_score * 1], title="Puntuación", showgrid=True, gridcolor='#eee'),
            xaxis=dict(range=[0, ranking_list[0]['score'] * 1.2], title="Puntuación", showgrid=True, gridcolor='#eee'),
            yaxis=dict(showgrid=False),
            bargap=0.3
        )
        st.plotly_chart(fig_ranking, use_container_width=True, config={'displayModeBar': False})
        
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
    
    # Weight sliders section (no expander)
    st.markdown("### 📐 Pesos de Prioridades")
    
    colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', '#00BCD4', '#FFEB3B', '#795548']
    
    # Initialize pending_weights from committed weights if not present or structure changed
    committed_weight_map = {c["name"]: c["weight"] for c in st.session_state.mcda_criteria}
    if "pending_weights" not in st.session_state:
        st.session_state.pending_weights = dict(committed_weight_map)
    else:
        # Sync structure: add new criteria, remove old ones
        for name in committed_weight_map:
            if name not in st.session_state.pending_weights:
                st.session_state.pending_weights[name] = committed_weight_map[name]
        st.session_state.pending_weights = {
            k: v for k, v in st.session_state.pending_weights.items() if k in committed_weight_map
        }
    
    # Two columns: sliders on left, vertical bar chart on right
    col_sliders, col_chart = st.columns([2, 1])
    
    pending_weights_list = []
    
    with col_sliders:
        for i, criterion in enumerate(st.session_state.mcda_criteria):
            if criterion["name"] in prioridad_names:
                slider_key = f"weight_slider_{criterion['name']}"
                
                # Initialize slider state from pending_weights
                if slider_key not in st.session_state:
                    st.session_state[slider_key] = float(st.session_state.pending_weights.get(criterion["name"], 0.5))
                
                # Inline layout: label and slider on same row
                label_col, slider_col = st.columns([1, 2])
                with label_col:
                    st.markdown(f"**{criterion['name']}**")
                with slider_col:
                    new_weight = st.slider(
                        criterion['name'],
                        min_value=0.0,
                        max_value=1.0,
                        step=0.05,
                        key=slider_key,
                        label_visibility="collapsed"
                    )
                
                # Update pending_weights (stacked bar auto-refreshes with these)
                st.session_state.pending_weights[criterion["name"]] = new_weight
                
                pending_weights_list.append({"name": criterion["name"], "weight": new_weight, "color": colors[i % len(colors)]})
    
    # Vertical stacked bar chart on the right (uses pending_weights - auto-refresh)
    with col_chart:
        if pending_weights_list:
            weight_map_display = normalize_weights(pending_weights_list)
            
            # Sort by normalized weight descending (biggest at top = added last in stacked bar)
            sorted_weights = sorted(
                pending_weights_list,
                key=lambda x: weight_map_display.get(x["name"], 0)
            )
            
            fig = go.Figure()
            
            for item in sorted_weights:
                name = item["name"]
                normalized = weight_map_display.get(name, 0)
                # Truncate name if too long for label
                display_name = name[:15] + "..." if len(name) > 18 else name
                fig.add_trace(go.Bar(
                    x=['Pesos'],
                    y=[normalized],
                    name=name,
                    marker_color=item["color"],
                    text=display_name,
                    textposition='inside',
                    insidetextanchor='middle',
                    hovertemplate=f"{normalized:.0%}<extra></extra>"
                ))
            
            fig.update_layout(
                barmode='stack',
                height=250,
                margin=dict(l=0, r=0, t=10, b=10),
                showlegend=False,
                xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
                yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, range=[0, 1]),
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Check if pending weights differ from committed weights
    weights_changed = any(
        st.session_state.pending_weights.get(c["name"]) != c["weight"]
        for c in st.session_state.mcda_criteria
        if c["name"] in prioridad_names
    )
    
    # Submit button to apply pending weights
    col_btn, col_hint = st.columns([1, 3])
    with col_btn:
        if st.button("✅ Aplicar pesos", disabled=not weights_changed, use_container_width=True):
            # Commit pending weights to mcda_criteria
            for i, criterion in enumerate(st.session_state.mcda_criteria):
                if criterion["name"] in st.session_state.pending_weights:
                    st.session_state.mcda_criteria[i]["weight"] = st.session_state.pending_weights[criterion["name"]]
            st.session_state.weights_user_override = True
            st.rerun()
    with col_hint:
        if weights_changed:
            st.caption("⚠️ Hay cambios de pesos pendientes. Pulsa *Aplicar pesos* para actualizar los resultados.")
# -*- coding: utf-8 -*-
"""
Evaluación (MCDA Evaluation) tab - Simplified version.
Clean MCDA implementation without over-engineering.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.calculations import normalize_weights, mcda_totals_and_ranking, get_disqualified_alternatives, is_alternative_disqualified
from utils.visualizations import create_mcda_radar_chart
from utils.ui_helpers import help_tip, get_tooltip

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
    
    # ===========================================
    # COMBINED EVALUATION TABLE (Priorities + No Negociables)
    # ===========================================
    
    # Get no negociables
    no_negociables = st.session_state.get("no_negociables", [])
    valid_no_negociables = [c for c in no_negociables if c.get("text", "").strip()]
    
    # Initialize no_negociables_scores if needed
    if "no_negociables_scores" not in st.session_state:
        st.session_state.no_negociables_scores = {}
    
    # Clean up orphaned checkbox states when alternatives/constraints change
    current_checkbox_keys = set()
    for alt in st.session_state.alts:
        for constraint in valid_no_negociables:
            if alt["text"].strip():
                key = f"no_neg_check_{alt['id']}_{constraint['id']}"
                current_checkbox_keys.add(key)
    
    orphaned_checkbox_keys = [k for k in st.session_state.keys() if k.startswith("no_neg_check_") and k not in current_checkbox_keys]
    for key in orphaned_checkbox_keys:
        del st.session_state[key]
    
    # Sync imported no_neg scores to widget states
    for alt in st.session_state.alts:
        alt_id = alt["id"]
        if alt_id in st.session_state.no_negociables_scores:
            for constraint in valid_no_negociables:
                constraint_id = constraint["id"]
                checkbox_key = f"no_neg_check_{alt_id}_{constraint_id}"
                stored_value = st.session_state.no_negociables_scores[alt_id].get(constraint_id)
                if stored_value is not None and checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = stored_value
    
    # Calculate total columns: priorities (sliders) + no negociables (checkboxes)
    total_columns = len(prioridad_names) + len(valid_no_negociables)
    
    # Create scoring matrix data
    scores_data = []
    
    # Add header row: Alternative + Priorities + No Negociables
    header_cols = st.columns([2] + [1] * total_columns)
    with header_cols[0]:
        pass
    
    # Priority headers
    for i, criterion in enumerate(prioridad_names):
        with header_cols[i + 1]:
            st.markdown(f"**{criterion}**")
    
    # No Negociables headers (after priorities)
    for i, constraint in enumerate(valid_no_negociables):
        col_idx = len(prioridad_names) + i + 1
        with header_cols[col_idx]:
            display_name = constraint["text"][:15] + "..." if len(constraint["text"]) > 15 else constraint["text"]
            st.markdown(f"**🚫 {display_name}**")
    
    st.markdown("")
    
    # Data rows for each alternative
    for alt_name in alt_names:
        if alt_name not in st.session_state.mcda_scores:
            st.session_state.mcda_scores[alt_name] = {}
        
        alt_id = next((a["id"] for a in st.session_state.alts if a["text"].strip() == alt_name), alt_name)
        
        # Ensure this alt has a no_neg scores dict
        if alt_id not in st.session_state.no_negociables_scores:
            st.session_state.no_negociables_scores[alt_id] = {}
        
        # Create row with all columns
        row_cols = st.columns([2] + [1] * total_columns)
        
        # We'll use a placeholder for the alternative name - update after checkboxes
        alt_name_placeholder = row_cols[0].empty()
        
        row_data = {"Alternativa": alt_name}
        
        # Priority sliders
        for i, criterion in enumerate(prioridad_names):
            with row_cols[i + 1]:
                criterion_id = next((p["id"] for p in st.session_state.priorities if p["text"].strip() == criterion), criterion)
                slider_key = f"mcda_score_{alt_id}_{criterion_id}"
                
                if slider_key not in st.session_state:
                    default_score = st.session_state.mcda_scores[alt_name].get(criterion, 2.5)
                    st.session_state[slider_key] = float(default_score)
                
                score = st.slider(
                    criterion,
                    min_value=0.0,
                    max_value=5.0,
                    step=0.5,
                    key=slider_key,
                    label_visibility="collapsed"
                )
                
                st.session_state.mcda_scores[alt_name][criterion] = score
                row_data[criterion] = score
        
        # No Negociables checkboxes (after priorities)
        for i, constraint in enumerate(valid_no_negociables):
            col_idx = len(prioridad_names) + i + 1
            with row_cols[col_idx]:
                constraint_id = constraint["id"]
                checkbox_key = f"no_neg_check_{alt_id}_{constraint_id}"
                
                if checkbox_key not in st.session_state:
                    default_value = st.session_state.no_negociables_scores[alt_id].get(constraint_id, True)
                    st.session_state[checkbox_key] = default_value
                
                checked = st.checkbox(
                    constraint["text"],
                    key=checkbox_key,
                    label_visibility="collapsed"
                )
                
                # Immediately sync to data structure
                st.session_state.no_negociables_scores[alt_id][constraint_id] = checked
        
        # Check if disqualified using CURRENT checkbox values
        is_disqualified, _ = is_alternative_disqualified(alt_id)
        
        # Update the placeholder with the alternative name (with disqualification indicator)
        with alt_name_placeholder:
            if is_disqualified and valid_no_negociables:
                st.markdown(f"~~{alt_name}~~ ❌")
            else:
                st.markdown(f"**{alt_name}**")
        
        scores_data.append(row_data)
    
    # Create DataFrame for calculations
    scores_df = pd.DataFrame(scores_data).set_index("Alternativa")
    st.session_state.mcda_scores_df = scores_df
    
    # Get disqualified alternatives AFTER all checkboxes have been rendered and synced
    disqualified_alts = get_disqualified_alternatives()
    
    # Show warning if any alternatives are disqualified
    if disqualified_alts and valid_no_negociables:
        num_disqualified = len(disqualified_alts)
        num_total = len([a for a in st.session_state.alts if a["text"].strip()])
        if num_disqualified == num_total:
            st.error(f"⚠️ **Todas las alternativas están descalificadas**. Revisa los No Negociables o añade alternativas que los cumplan.")
        else:
            st.warning(f"⚠️ **{num_disqualified} alternativa(s) descalificada(s)** por no cumplir todos los No Negociables.")
    
    # Contextual help - placed after scoring matrix where confusion might arise
    with st.expander("*\"¿Qué significa un 3? ¿Cómo comparo de forma justa?\"*", expanded=False):
        st.markdown("""
        **Escala de puntuación (0-5):**
        
        | Puntuación | Significado |
        |------------|-------------|
        | **0** | Muy malo — La alternativa falla completamente en este criterio |
        | **1-2** | Malo/Débil — Por debajo de lo aceptable |
        | **2.5** | Neutro — Ni bueno ni malo, cumple lo mínimo |
        | **3-4** | Bueno/Fuerte — Por encima de lo esperado |
        | **5** | Excelente — La alternativa destaca en este criterio |
        
        **Consejos:**
        - Puntúa **comparando alternativas entre sí**, no en abstracto
        - Sé consistente: si A es mejor que B en un criterio, A debe tener mayor puntuación
        - No te preocupes por ser exacto — la diferencia entre 3 y 3.5 rara vez cambia el resultado
        """)
    
    st.markdown("---")
    
    # Results FIRST
    st.markdown("### 🏆 Resultados")
    
    # Colors for priority visualization (used in ranking breakdown and weight sliders)
    colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336', '#00BCD4', '#FFEB3B', '#795548']
    # Map priority names to colors based on their position in mcda_criteria
    priority_colors = {c["name"]: colors[i % len(colors)] for i, c in enumerate(st.session_state.mcda_criteria)}
    
    # Calculate totals and ranking using current mcda_criteria weights
    weight_map = normalize_weights(st.session_state.mcda_criteria)
    totals, ranking_list_all = mcda_totals_and_ranking(scores_df.copy(), st.session_state.mcda_criteria)
    
    # Filter out disqualified alternatives from the ranking
    disqualified_names = set()
    for alt in st.session_state.alts:
        if alt["id"] in disqualified_alts:
            disqualified_names.add(alt["text"].strip())
    
    ranking_list = [item for item in ranking_list_all if item["alternativa"] not in disqualified_names]
    
    if ranking_list:
        # Visual Analysis first
        try:
            # Create radar chart for top 3 alternatives
            top_alts = ranking_list[:3]
            fig = create_mcda_radar_chart(scores_df, prioridad_names, [alt["alternativa"] for alt in top_alts])
            st.plotly_chart(fig, width="stretch")
        except Exception as e:
            st.info("💡 Error al generar gráfico radar")
        
        st.markdown("")
        st.markdown("")
        
        # Check if stacked breakdown view is enabled
        show_breakdown = st.session_state.get("show_ranking_breakdown", False)
        
        # Ranking horizontal bar chart
        fig_ranking = go.Figure()
        
        if show_breakdown:
            # Stacked bar showing contribution per priority
            for i, item in enumerate(reversed(ranking_list)):
                alt_name = item['alternativa']
                alt_scores = st.session_state.mcda_scores.get(alt_name, {})
                
                for criterion in prioridad_names:
                    score = alt_scores.get(criterion, 0)
                    weight = weight_map.get(criterion, 0)
                    contribution = score * weight
                    
                    fig_ranking.add_trace(go.Bar(
                        y=[alt_name],
                        x=[contribution],
                        orientation='h',
                        name=criterion,
                        marker_color=priority_colors.get(criterion, '#999'),
                        hovertemplate=f"<b>{criterion}</b><br>{score:.1f} × {weight:.1%} = {contribution:.2f}<extra></extra>",
                        showlegend=(i == len(ranking_list) - 1)  # Only show legend for first alt (top)
                    ))
            
            fig_ranking.update_layout(barmode='stack')
        else:
            # Simple bars (original view)
            WINNER_COLOR = '#83c9ff'
            bar_colors = [WINNER_COLOR if i == 0 else '#D3D3D3' for i in range(len(ranking_list))]
            
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
            xaxis=dict(range=[0, ranking_list[0]['score'] * 1.2], title="Puntuación", showgrid=True, gridcolor='#eee'),
            yaxis=dict(showgrid=False),
            bargap=0.3
        )
        st.plotly_chart(fig_ranking, width="stretch", config={'displayModeBar': False})
        
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
            
            st.markdown("")
            st.checkbox(
                "Visualizar contribución por criterio",
                value=st.session_state.get("show_ranking_breakdown", False),
                key="show_ranking_breakdown"
            )
    else:
        if disqualified_alts and len(disqualified_alts) == len([a for a in st.session_state.alts if a["text"].strip()]):
            st.info("💡 Todas las alternativas están descalificadas. Revisa los No Negociables para ver resultados.")
        else:
            st.info("💡 Completa la evaluación para ver los resultados")
    
    st.markdown("---")
    
    # Weight sliders section (no expander)
    st.markdown("### 📐 Pesos de Prioridades")
    
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
            
            st.plotly_chart(fig, width="stretch", config={'displayModeBar': False})
    
    # Check if pending weights differ from committed weights
    weights_changed = any(
        st.session_state.pending_weights.get(c["name"]) != c["weight"]
        for c in st.session_state.mcda_criteria
        if c["name"] in prioridad_names
    )
    
    # Submit button to apply pending weights
    col_btn, col_hint = st.columns([1, 3])
    with col_btn:
        if st.button("✅ Aplicar pesos", disabled=not weights_changed, width="stretch"):
            # Commit pending weights to mcda_criteria
            for i, criterion in enumerate(st.session_state.mcda_criteria):
                if criterion["name"] in st.session_state.pending_weights:
                    st.session_state.mcda_criteria[i]["weight"] = st.session_state.pending_weights[criterion["name"]]
            st.session_state.weights_user_override = True
            st.rerun()
    with col_hint:
        if weights_changed:
            st.caption("⚠️ Hay cambios de pesos pendientes. Pulsa *Aplicar pesos* para actualizar los resultados.")
# -*- coding: utf-8 -*-
"""
Evaluación (MCDA Evaluation) tab component for Lambda Pro.
Handles Multi-Criteria Decision Analysis evaluation and scoring.
"""

import streamlit as st
import pandas as pd

from config.constants import SCORE_STEPS, DEFAULT_MCDA_CRITERIA
from utils.calculations import mcda_totals_and_ranking
from utils.visualizations import create_mcda_ranking_chart, create_mcda_radar_chart


def sync_criteria_from_priorities():
    """Sync MCDA criteria from priorities with default weights."""
    prioridad_names = [p["text"].strip() for p in st.session_state.get("priorities", []) if p["text"].strip()]
    current_criteria = st.session_state.get("mcda_criteria", [])
    current_names = [c.get("name", "").strip() for c in current_criteria]

    if (not current_criteria) or (current_names != prioridad_names):
        # Default weights from priority order (higher priority = higher weight)
        n = len(prioridad_names)
        if n > 0:
            raw_weights = list(range(n, 0, -1))  # n, n-1, ..., 1
            total = sum(raw_weights)
            auto_weights = [w / total for w in raw_weights]
            st.session_state["mcda_criteria"] = [
                {"name": name, "weight": float(weight)} 
                for name, weight in zip(prioridad_names, auto_weights)
            ]


def render_evaluacion_tab():
    """Render the Evaluación (MCDA) tab."""
    
    st.subheader("Evaluación (MCDA)")

    # Guards: need alternativas & prioridades
    alt_names = [a["text"].strip() for a in st.session_state.get("alts", []) if a["text"].strip()]
    prioridad_names = [p["text"].strip() for p in st.session_state.get("priorities", []) if p["text"].strip()]
    
    if not alt_names:
        st.info("Añade al menos una **Alternativa** en la pestaña *Alternativas* para poder evaluar.")
        return
    elif not prioridad_names:
        st.info("Añade al menos una **Prioridad** en la pestaña *Prioridades* para usar como criterios.")
        return

    # Sync criteria from priorities
    sync_criteria_from_priorities()

    st.markdown("**Criterios y pesos** (cargados de *Prioridades* por orden; editables)")
    crit_df = pd.DataFrame(st.session_state.get("mcda_criteria", []))

    # Editor for criteria weights
    crit_df = st.data_editor(
        crit_df,
        num_rows="fixed",
        column_config={
            "name": st.column_config.TextColumn("Criterio", disabled=True),
            "weight": st.column_config.NumberColumn("Peso (≥ 0)", min_value=0.0, step=0.05,
                help="Pesos normalizados automáticamente para el cálculo"),
        },
        key="mcda_criteria_editor",
        use_container_width=True,
    )
    crit_df["name"] = crit_df["name"].astype(str).str.strip()
    st.session_state.mcda_criteria = crit_df.to_dict("records")
    crit_names = list(crit_df["name"])

    # Scores with select sliders (0..5 step 0.5), persisted in session
    st.markdown("**Puntuaciones (0–5)**")
    
    # Use setdefault for direct access
    current_scores = st.session_state.setdefault("mcda_scores", {})
    
    for alt in alt_names:
        st.markdown(f"**{alt}**")
        # Ensure alt exists in current_scores
        current_scores.setdefault(alt, {})
        
        for i in range(0, len(crit_names), 3):
            cols = st.columns(min(3, len(crit_names) - i))
            for j, criterion in enumerate(crit_names[i:i+3]):
                with cols[j]:
                    key = f"score_{alt}_{criterion}"
                    # Direct access with fallback
                    default_val = current_scores.get(alt, {}).get(criterion, 0.0)
                    new_val = st.select_slider(
                        criterion, 
                        options=SCORE_STEPS, 
                        value=st.session_state.get(key, default_val),
                        key=key
                    )
                    # Update in place
                    current_scores[alt][criterion] = float(new_val)
        st.markdown("")

    # DataFrame (aligned to displayed order)
    scores_df = pd.DataFrame(current_scores).T.reindex(index=alt_names, columns=crit_names, fill_value=0.0)
    st.session_state["mcda_scores_df"] = scores_df

    # Compute weighted totals & ranking
    totals, ranking_list = mcda_totals_and_ranking(scores_df.copy(), st.session_state.get("mcda_criteria", []))
    ranking = totals.sort_values(ascending=False).rename("Puntuación ponderada")
    result_df = pd.concat([scores_df, ranking], axis=1).loc[ranking.index]

    st.markdown("**Resultado y ranking**")
    st.dataframe(result_df.style.format(precision=2), use_container_width=True)

    # Bar chart (ranking)
    fig_rank = create_mcda_ranking_chart(ranking)
    st.plotly_chart(fig_rank, use_container_width=True)

    # Radar chart (only if > 2 criteria)
    if len(crit_names) > 2:
        st.markdown("**Radar de puntuaciones por criterio**")
        fig_radar = create_mcda_radar_chart(scores_df, crit_names, alt_names)
        st.plotly_chart(fig_radar, use_container_width=True)

    st.caption("Los pesos se normalizan automáticamente. La puntuación total = Σ(puntuación × peso).")

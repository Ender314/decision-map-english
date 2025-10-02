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
from config.constants import PROBABILITY_STEPS
from utils.calculations import scenario_expected_value


def render_scenarios_tab():
    """Render the Scenarios (Scenario Planning) tab."""
    st.subheader("Scenario planning")

    # Need alternativas
    alts = [a for a in st.session_state.alts if a["text"].strip()]
    if not alts:
        st.info("Añade al menos una **Alternativa** en la pestaña *Alternativas* para proyectar escenarios.")
        return

    # Initialize scenarios if needed
    if "scenarios" not in st.session_state:
        st.session_state.scenarios = {}
    
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
                "worst_score": 2.0,
                "p_best": 0.5,
                "p_best_pct": 50,
            }
        
        scenario_data = st.session_state.scenarios[alt_id]
        
        with st.expander(f"⚙️ {alt_name}", expanded=False):
            # Row 1: Worst → Probabilidad → Best
            c1, c2, c3 = st.columns([1.8, 1.2, 1.8])
            
            with c1:
                st.markdown("**Worst scenario**")
                worst_desc = st.text_input(
                    "Descripción (worst)",
                    value=scenario_data.get("worst_desc", ""),
                    key=f"worst_desc_{alt_id}",
                    label_visibility="collapsed",
                    placeholder="¿Qué pasa si sale mal?"
                )
                scenario_data["worst_desc"] = worst_desc
            
            with c2:
                st.markdown("######")
                p_best_pct = st.select_slider(
                    "Probabilidad de **best**",
                    options=PROBABILITY_STEPS,
                    value=scenario_data.get("p_best_pct", 50),
                    key=f"pbest_{alt_id}",
                    label_visibility="collapsed"
                )
                scenario_data["p_best_pct"] = p_best_pct
                scenario_data["p_best"] = p_best_pct / 100.0
            
            with c3:
                st.markdown("**Best scenario**")
                best_desc = st.text_input(
                    "Descripción (best)",
                    value=scenario_data.get("best_desc", ""),
                    key=f"best_desc_{alt_id}",
                    label_visibility="collapsed",
                    placeholder="¿Qué pasa si todo va muy bien?"
                )
                scenario_data["best_desc"] = best_desc

            # Row 2: Single range slider for Impacto (0–10)
            st.markdown("")
            worst_best = st.slider(
                "Impacto (0–10): mínimo = worst, máximo = best",
                min_value=0, max_value=10, step=1,
                value=(int(scenario_data.get("worst_score", 2)), int(scenario_data.get("best_score", 7))),
                key=f"impact_range_{alt_id}"
            )
            scenario_data["worst_score"] = float(worst_best[0])
            scenario_data["best_score"] = float(worst_best[1])

            # Calculate expected value
            ev = scenario_expected_value(
                scenario_data["p_best"], 
                scenario_data["worst_score"], 
                scenario_data["best_score"]
            )
            scenario_data["ev"] = ev
    
    # Create summary data for visualization
    summary_rows = []
    for scenario_data in st.session_state.scenarios.values():
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
    
    st.markdown("---")

    # Summary table
    st.markdown("**Resumen**")
    st.dataframe(
        summary_df[["Alternativa", "Worst", "Best", "EV"]].style.format({"EV": "{:.2f}"}),
        use_container_width=True
    )

    st.caption("EV = p(best) × best + (1 − p(best)) × worst. Escala 0–10.")
    st.caption("💡 **Violin Chart**: La anchura representa la densidad de probabilidad. Los diamantes negros indican el valor esperado (EV).")

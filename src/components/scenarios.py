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
    st.subheader("🔮 Planificación de Escenarios")

    # Need alternativas
    alts = [a for a in st.session_state.alts if a["text"].strip()]
    if not alts:
        st.info("Añade al menos una **Alternativa** en la pestaña *Alternativas* para proyectar escenarios.")
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
                worst_score = scenario_data.get("worst_score", 2.0)
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
                "worst_score": 2.0,
                "p_best": 0.5,
                "p_best_pct": 50,
            }
        
        scenario_data = st.session_state.scenarios[alt_id]
        
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
    
    st.caption("💎 **Violin Chart**: La anchura representa la densidad de probabilidad. Los diamantes brillantes indican el valor esperado (EV).")

    st.markdown("---")

    # Summary table
    st.markdown("**Resumen**")
    st.dataframe(
        summary_df[["Alternativa", "Worst", "Best", "EV"]].style.format({"EV": "{:.2f}"}),
        use_container_width=True
    )

    st.caption("EV = p(best) × best + (1 − p(best)) × worst. Escala 0–10.")

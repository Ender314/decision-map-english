# -*- coding: utf-8 -*-
"""
Scenarios (Scenario Planning) tab component for Lambda Pro.
Handles probability distributions and scenario analysis with violin plots.
"""

import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from config.constants import PROBABILITY_STEPS
from utils.calculations import scenario_expected_value, generate_violin_data


def render_scenario_inputs(alt_id: str, alt_name: str, prev_data: dict):
    """Render scenario input controls for a single alternative."""
    
    with st.expander(f"⚙️ {alt_name}", expanded=False):
        # Row 1: Worst → Probabilidad → Best
        c1, c2, c3 = st.columns([1.8, 1.2, 1.8])
        
        with c1:
            st.markdown("**Worst scenario**")
            worst_desc = st.text_input(
                "Descripción (worst)",
                value=prev_data.get("worst_desc", ""),
                key=f"worst_desc_{alt_id}",
                label_visibility="collapsed",
                placeholder="¿Qué pasa si sale mal?"
            )
        
        with c2:
            st.markdown("######")
            p_key = f"pbest_{alt_id}"
            default_pct = int(round(float(prev_data.get("p_best", 0.5)) * 100))
            default_pct = max(0, min(100, 5 * round(default_pct / 5)))
            p_best_pct = st.select_slider(
                "Probabilidad de **best**",
                options=PROBABILITY_STEPS,
                value=st.session_state.get(p_key, prev_data.get("p_best_pct", default_pct)),
                key=p_key,
                label_visibility="collapsed"
            )
            p_best = p_best_pct / 100.0
        
        with c3:
            st.markdown("**Best scenario**")
            best_desc = st.text_input(
                "Descripción (best)",
                value=prev_data.get("best_desc", ""),
                key=f"best_desc_{alt_id}",
                label_visibility="collapsed",
                placeholder="¿Qué pasa si todo va muy bien?"
            )

        # Row 2: Single range slider for Impacto (0–10)
        rng_key = f"impact_range_{alt_id}"
        default_rng = (
            int(min(float(prev_data.get("worst_score", 2.0)), 10)),
            int(min(float(prev_data.get("best_score", 7.0)), 10))
        )
        st.markdown("")
        worst_best = st.slider(
            "Impacto (0–10): mínimo = worst, máximo = best",
            min_value=0, max_value=10, step=1,
            value=st.session_state.get(rng_key, default_rng),
            key=rng_key
        )
        worst_score, best_score = map(float, worst_best)

        # Calculate expected value
        ev = p_best * best_score + (1 - p_best) * worst_score
        
        return {
            "name": alt_name,
            "best_desc": best_desc,
            "best_score": best_score,
            "worst_desc": worst_desc,
            "worst_score": worst_score,
            "p_best": p_best,
            "p_best_pct": p_best_pct,
            "ev": ev
        }


def create_violin_plot(scenario_data: list):
    """Create modern violin plot for scenario planning."""
    
    # Prepare data for violin plot
    violin_data = []
    
    for row in scenario_data:
        samples = generate_violin_data(row["Worst"], row["Best"], row["EV"])
        for sample in samples:
            violin_data.append({
                "Alternativa": row["Alternativa"],
                "Value": sample,
                "EV": row["EV"]
            })
    
    violin_df = pd.DataFrame(violin_data)
    
    # Create custom color palette based on EV values
    ev_colors = []
    for row in scenario_data:
        ev_normalized = row["EV"] / 10  # Normalize to 0-1
        if ev_normalized <= 0.5:
            # Red to Yellow
            r = 1.0
            g = ev_normalized * 2
            b = 0.0
        else:
            # Yellow to Green
            r = 2 * (1 - ev_normalized)
            g = 1.0
            b = 0.0
        ev_colors.append((r, g, b))
    
    # Set modern seaborn theme and create the plot
    sns.set_theme(style="whitegrid", palette=None)
    fig, ax = plt.subplots(figsize=(12, max(5, len(scenario_data) * 0.9)))
    
    # Create modern violin plot
    sns.violinplot(
        data=violin_df, 
        y="Alternativa", 
        x="Value", 
        order=[row["Alternativa"] for row in scenario_data],  # Maintain EV-based order
        palette=ev_colors,
        orient="h",
        inner="quart",  # Show quartiles inside violins
        fill=True,      # Modern filled violins
        linewidth=1.5,  # Slightly thicker lines
        saturation=0.8, # Slightly desaturated for elegance
        ax=ax
    )
    
    # Add modern EV markers (diamonds) with enhanced styling
    for i, row in enumerate(scenario_data):
        # Main EV marker
        ax.scatter(row["EV"], i, marker='D', s=120, color='white', 
                  edgecolor='black', linewidth=2, zorder=15, alpha=0.9)
        ax.scatter(row["EV"], i, marker='D', s=80, color='black', 
                  zorder=16, alpha=0.8)
        
        # Modern EV value annotations with better styling
        ax.annotate(f'{row["EV"]:.1f}', 
                   xy=(row["EV"], i), 
                   xytext=(8, 0), 
                   textcoords='offset points',
                   fontsize=10, 
                   fontweight='bold',
                   color='black',
                   ha='left', va='center',
                   bbox=dict(boxstyle='round,pad=0.4', 
                           facecolor='white', 
                           edgecolor='gray',
                           alpha=0.9,
                           linewidth=0.5))
    
    # Modern plot customization
    ax.set_xlabel("Impacto (0–10)", fontsize=12, fontweight='bold')
    ax.set_ylabel("")
    ax.set_xlim(-0.5, 10.5)
    
    # Enhanced title with subtitle
    ax.set_title("Distribución de Escenarios por Alternativa", 
                fontsize=14, fontweight='bold', pad=15)
    ax.text(0.5, 1.02, "Densidad de probabilidad basada en distribución normal centrada en EV", 
           transform=ax.transAxes, ha='center', fontsize=10, 
           style='italic', alpha=0.7)
    
    # Remove top and right spines for cleaner look
    sns.despine(ax=ax, top=True, right=True)
    
    # Adjust layout
    plt.tight_layout()
    
    return fig


def render_scenarios_tab():
    """Render the Scenarios (Scenario Planning) tab."""
    
    st.subheader("Scenario planning")

    # Need alternativas
    alts = [a for a in st.session_state.get("alts", []) if a["text"].strip()]
    if not alts:
        st.info("Añade al menos una **Alternativa** en la pestaña *Alternativas* para proyectar escenarios.")
        return

    # Use existing state IN PLACE (no wholesale reassignment)
    current_scenarios = st.session_state.setdefault("scenarios", {})
    
    # Process each alternative
    updated_scenarios = {}
    for alt in alts:
        alt_id, alt_name = alt["id"], alt["text"].strip()
        prev_data = current_scenarios.get(alt_id, {
            "name": alt_name, 
            "best_desc": "", 
            "best_score": 7.0,
            "worst_desc": "", 
            "worst_score": 2.0, 
            "p_best": 0.5, 
            "p_best_pct": 50,
        })
        
        # Render inputs and get updated data
        scenario_data = render_scenario_inputs(alt_id, alt_name, prev_data)
        updated_scenarios[alt_id] = scenario_data
    
    # Update session state
    st.session_state.scenarios = updated_scenarios

    # Create summary data for visualization
    summary_rows = []
    for scenario_data in updated_scenarios.values():
        ev = scenario_expected_value(
            scenario_data["p_best"], 
            scenario_data["worst_score"], 
            scenario_data["best_score"]
        )
        summary_rows.append({
            "Alternativa": scenario_data["name"],
            "Worst": int(scenario_data["worst_score"]),
            "Best": int(scenario_data["best_score"]),
            "EV": ev,
            "Range": scenario_data["best_score"] - scenario_data["worst_score"],
        })
    
    if not summary_rows:
        return
    
    # Sort by EV descending
    summary_df = pd.DataFrame(summary_rows).sort_values("EV", ascending=False)
    
    # Create and display violin plot
    try:
        fig = create_violin_plot(summary_rows)
        st.pyplot(fig)
        plt.close()  # Clean up to prevent memory issues
    except Exception as e:
        st.error(f"Error creating violin plot: {str(e)}")
        st.info("💡 Intenta ajustar los valores de los escenarios")

    # Summary table at the bottom
    st.markdown("**Resumen**")
    st.dataframe(
        summary_df[["Alternativa", "Worst", "Best", "EV"]].style.format({"EV": "{:.2f}"}),
        use_container_width=True
    )

    st.caption("EV = p(best) × best + (1 − p(best)) × worst. Escala 0–10.")
    st.caption("💡 **Violin Chart Moderno**: La anchura representa la densidad de probabilidad. Las líneas internas muestran cuartiles. Los diamantes negros indican el valor esperado (EV).")

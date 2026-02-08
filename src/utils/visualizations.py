# -*- coding: utf-8 -*-
"""
Visualization utilities for Decider Pro.
Contains all chart generation and plotting functions.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
from typing import List, Dict, Any, Tuple

from config.constants import PLAZO_ORDER, YMAX, get_relevance_color


@st.cache_data
def create_impact_chart(df: pd.DataFrame, relevance_pct: float) -> go.Figure:
    """
    Create the temporal impact assessment chart.
    
    Args:
        df: DataFrame with Plazo, Impacto, and Impacto_num columns
        relevance_pct: Relevance percentage for color calculation
        
    Returns:
        Plotly figure
    """
    line_color, fill_color = get_relevance_color(relevance_pct)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["Plazo"], 
        y=df["Impacto_num"], 
        customdata=df["Impacto"],
        mode="lines+markers", 
        line=dict(shape="spline", color=line_color, width=3),
        fill="tozeroy", 
        fillcolor=fill_color,
        hovertemplate="Plazo: %{x}<br>Impacto: %{customdata}<extra></extra>",
        name="Relevancia",
        marker=dict(size=10)
    ))
    
    fig.update_layout(
        margin=dict(l=70, r=20, t=20, b=20), 
        height=360,
        xaxis=dict(
            title="Plazo", 
            categoryorder="array", 
            categoryarray=PLAZO_ORDER, 
            zeroline=False
        ),
        yaxis=dict(
            title="Impacto", 
            range=[0, YMAX], 
            autorange=False, 
            fixedrange=True,
            tickmode="array", 
            tickvals=[0, 5, 10, 15],
            showticklabels=False, 
            showgrid=True, 
            zeroline=False
        ),
        hovermode="x unified",
    )
    fig.update_yaxes(ticks="")
    
    return fig


@st.cache_data
def create_mcda_ranking_chart(ranking: pd.Series) -> go.Figure:
    """
    Create MCDA ranking bar chart.
    
    Args:
        ranking: Series with alternative names as index and scores as values
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    fig.add_bar(
        x=ranking.index.tolist(),
        y=ranking.values.tolist(),
        text=[f"{v:.2f}" for v in ranking.values],
        textposition="auto",
        name="Puntuación"
    )
    fig.update_layout(
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title="Alternativa",
        yaxis_title="Puntuación ponderada (0–5)",
        height=320,
        showlegend=False,
    )
    return fig


def create_mcda_radar_chart(scores_df: pd.DataFrame, criteria_names: List[str], alt_names: List[str], showlegend: bool = True) -> go.Figure:
    """
    Create MCDA radar chart for comparing alternatives across criteria.
    
    Args:
        scores_df: DataFrame with alternatives as rows, criteria as columns
        criteria_names: List of criteria names
        alt_names: List of alternative names
        
    Returns:
        Plotly figure
    """
    # Ensure criteria names are treated as strings (not numeric angles)
    theta_labels = [str(name) for name in criteria_names]
    theta = theta_labels + [theta_labels[0]]  # close loop
    fig = go.Figure()
    
    # Calculate max score for dynamic radial axis
    max_score = scores_df.loc[alt_names, criteria_names].max().max()
    # Round up to nearest 0.5 for cleaner axis, minimum 1.0
    radial_max = max(1.0, ((max_score // 0.5) + 1) * 0.5)
    
    for alt in alt_names:
        r_vals = scores_df.loc[alt, criteria_names].tolist()
        r_vals.append(r_vals[0])
        fig.add_trace(go.Scatterpolar(
            r=r_vals,
            theta=theta,
            mode="lines+markers",
            fill="toself",
            name=alt
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, radial_max], dtick=1),
            angularaxis=dict(
                type='category',  # Force categorical axis (not numeric angles)
                categoryorder='array',
                categoryarray=theta_labels  # Explicit order
            )
        ),
        showlegend=showlegend,
        height=420,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig


@st.cache_data
def create_timeline_chart(timeline_items: List[Dict[str, Any]]) -> go.Figure:
    """
    Create timeline visualization chart.
    
    Args:
        timeline_items: List of timeline items with event and date
        
    Returns:
        Plotly figure
    """
    # Filter items with valid dates and events
    valid_items = [
        item for item in timeline_items 
        if item.get("event", "").strip() and item.get("date") is not None
    ]
    
    if not valid_items:
        return go.Figure()
    
    # Create dataframe for timeline
    timeline_data = []
    for item in valid_items:
        event_date = item["date"]
        timeline_data.append({
            "Evento": item["event"], 
            "Fecha": event_date,
        })
    
    timeline_df = pd.DataFrame(timeline_data)
    timeline_df = timeline_df.sort_values("Fecha")
    
    # Create timeline chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timeline_df["Fecha"],
        y=[1] * len(timeline_df),  # All events on same horizontal line
        mode="markers+text",
        marker=dict(size=12, color="blue"),
        text=timeline_df["Evento"],
        textposition="top center",
        hovertemplate="<b>%{text}</b><br>Fecha: %{x}<extra></extra>",
        name="Eventos"
    ))
    
    fig.update_layout(
        height=200,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(title="Fecha", type="date"),
        yaxis=dict(visible=False, range=[0.5, 1.5]),
        showlegend=False
    )
    
    return fig


@st.cache_data
def create_kpi_bar_chart(numeric_kpis: List[Dict[str, Any]]) -> go.Figure:
    """
    Create bar chart for numeric KPIs.
    
    Args:
        numeric_kpis: List of KPI dicts with name, value, unit
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=[k["name"] for k in numeric_kpis],
        y=[k["value"] for k in numeric_kpis],
        text=[f"{k['value']}{' ' + k['unit'] if k['unit'] else ''}" for k in numeric_kpis],
        textposition='auto',
        marker_color='lightblue',
        hovertemplate="<b>%{x}</b><br>Valor: %{y}<extra></extra>"
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(title="KPIs"),
        yaxis=dict(title="Valores"),
        showlegend=False
    )
    
    return fig


def create_scenario_violin_plot(scenario_data: List[Dict[str, Any]]) -> Tuple[plt.Figure, plt.Axes]:
    """
    Create modern violin plot for scenario planning.
    
    Args:
        scenario_data: List of scenario data with EV, worst, best values
        
    Returns:
        Tuple of (matplotlib figure, axes)
    """
    from .calculations import generate_violin_data
    
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
    
    return fig, ax


@st.cache_data
def create_results_ranking_chart(ranking_list: List[Dict[str, Any]]) -> go.Figure:
    """
    Create horizontal bar chart for results summary.
    
    Args:
        ranking_list: List of ranking data with alternativa and score
        
    Returns:
        Plotly figure
    """
    # Reverse order for better visualization (highest at top)
    reversed_ranking = list(reversed(ranking_list))
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=[item['alternativa'] for item in reversed_ranking],
        x=[item['score'] for item in reversed_ranking],
        orientation='h',
        marker_color=colors[:len(reversed_ranking)],
        text=[f"{item['score']:.2f}" for item in reversed_ranking],
        textposition='auto',
        hovertemplate="<b>%{y}</b><br>Puntuación: %{x:.2f}<extra></extra>"
    ))
    
    fig.update_layout(
        title="Puntuaciones MCDA",
        height=max(250, len(ranking_list) * 40),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(title="Puntuación"),
        yaxis=dict(title=""),
        showlegend=False
    )
    
    return fig


@st.cache_data
def create_scenario_summary_chart(scenario_data: List[Dict[str, Any]]) -> go.Figure:
    """
    Create bar chart for scenario expected values.
    
    Args:
        scenario_data: List of scenario data with expected values
        
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[item["Alternativa"] for item in scenario_data],
        y=[item["Valor Esperado"] for item in scenario_data],
        marker_color='lightcoral',
        text=[f"{item['Valor Esperado']}" for item in scenario_data],
        textposition='auto',
        hovertemplate="<b>%{x}</b><br>Valor Esperado: %{y}<extra></extra>"
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis=dict(title="Alternativas"),
        yaxis=dict(title="Valor Esperado"),
        showlegend=False
    )
    
    return fig

# -*- coding: utf-8 -*-
"""
Visualization utilities for Decider Pro.
Contains all chart generation and plotting functions.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from typing import List, Dict, Any

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


def create_scenario_pert_chart(scenario_data: List[Dict[str, Any]]) -> go.Figure:
    """
    Create Plotly scenario distribution chart using analytical PERT distributions.
    Produces smooth, deterministic violin-like shapes without Monte Carlo sampling.
    
    Args:
        scenario_data: List of dicts with Alternativa, Worst, Best, EV keys
        
    Returns:
        Plotly figure
    """
    from .calculations import pert_pdf

    fig = go.Figure()
    n_alts = len(scenario_data)

    for i, row in enumerate(scenario_data):
        worst, best, ev = float(row["Worst"]), float(row["Best"]), float(row["EV"])
        alt_name = row["Alternativa"]

        # Color based on EV (red → yellow → green)
        ev_norm = ev / 10.0
        if ev_norm <= 0.5:
            r, g, b = 1.0, ev_norm * 2, 0.0
        else:
            r, g, b = 2 * (1 - ev_norm), 1.0, 0.0

        fill_color = f"rgba({int(r*255)},{int(g*255)},{int(b*255)},0.55)"
        line_color = f"rgb({int(r*180)},{int(g*180)},{int(b*180)})"

        if best <= worst:
            # Degenerate: single point
            fig.add_trace(go.Scatter(
                x=[ev], y=[i],
                mode="markers",
                marker=dict(size=14, color=fill_color, symbol="diamond",
                            line=dict(color=line_color, width=2)),
                showlegend=False,
                hovertemplate=f"<b>{alt_name}</b><br>EV: {ev:.1f}<extra></extra>",
            ))
            continue

        # Compute analytical PERT PDF
        x = np.linspace(worst, best, 200)
        pdf = pert_pdf(x, worst, best, ev)

        # Normalize height to fit as violin shape (max half-height ≈ 0.35)
        max_pdf = pdf.max()
        pdf_norm = pdf / max_pdf * 0.35 if max_pdf > 0 else pdf

        # Build closed polygon (top edge forward, bottom edge backward)
        x_poly = np.concatenate([x, x[::-1]])
        y_poly = np.concatenate([i + pdf_norm, (i - pdf_norm)[::-1]])

        # Filled distribution shape
        fig.add_trace(go.Scatter(
            x=x_poly.tolist(),
            y=y_poly.tolist(),
            fill="toself",
            fillcolor=fill_color,
            line=dict(color=line_color, width=2),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Range endpoints
        fig.add_trace(go.Scatter(
            x=[worst, best], y=[i, i],
            mode="markers+lines",
            line=dict(color=line_color, width=2, dash="dot"),
            marker=dict(size=7, color=line_color, opacity=0.7),
            showlegend=False,
            hoverinfo="skip",
        ))

        # EV diamond marker
        fig.add_trace(go.Scatter(
            x=[ev], y=[i],
            mode="markers",
            marker=dict(size=14, color="white", symbol="diamond",
                        line=dict(color=line_color, width=2.5)),
            showlegend=False,
            hovertemplate=(
                f"<b>{alt_name}</b><br>"
                f"EV: {ev:.1f}<br>"
                f"Rango: {worst:.0f} – {best:.0f}<br>"
                "<extra></extra>"
            ),
        ))

    # Layout
    fig.update_layout(
        height=max(250, n_alts * 110),
        margin=dict(l=10, r=60, t=10, b=40),
        xaxis=dict(
            range=[-0.5, 10.5], title="Impacto (0–10)",
            showgrid=True, gridcolor="#eee", dtick=1,
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(n_alts)),
            ticktext=[row["Alternativa"] for row in scenario_data],
            showgrid=False,
        ),
        plot_bgcolor="white",
        hovermode="closest",
    )

    return fig


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

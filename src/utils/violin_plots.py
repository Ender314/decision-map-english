# -*- coding: utf-8 -*-
"""
Modern violin plot implementations for Lambda Pro scenario planning.
Multiple plotting libraries and styles for comparison.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from typing import List, Dict, Any


def generate_violin_samples(worst: float, best: float, ev: float, n_samples: int = 1000) -> np.ndarray:
    """Generate samples for violin plot using normal distribution centered on EV."""
    std_dev = (best - worst) / 4
    samples = np.random.normal(ev, std_dev, n_samples)
    return np.clip(samples, worst, best)


def create_seaborn_violin_classic(summary_rows: List[Dict[str, Any]]) -> tuple:
    """Original Seaborn violin plot (current implementation)."""
    # Prepare data
    violin_data = []
    for row in summary_rows:
        samples = generate_violin_samples(row["Worst"], row["Best"], row["EV"])
        for sample in samples:
            violin_data.append({
                "Alternativa": row["Alternativa"],
                "Value": sample,
                "EV": row["EV"]
            })
    
    violin_df = pd.DataFrame(violin_data)
    
    # Create plot
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, max(5, len(summary_rows) * 0.9)))
    
    sns.violinplot(
        data=violin_df, 
        y="Alternativa", 
        x="Value", 
        order=[row["Alternativa"] for row in summary_rows],
        orient="h",
        inner="quart",
        fill=True,
        linewidth=1.5,
        saturation=0.8,
        ax=ax
    )
    
    # Add EV markers
    for i, row in enumerate(summary_rows):
        ax.scatter(row["EV"], i, marker='D', s=120, color='white', 
                  edgecolor='black', linewidth=2, zorder=15, alpha=0.9)
        ax.scatter(row["EV"], i, marker='D', s=80, color='black', zorder=16, alpha=0.8)
        
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
    
    ax.set_xlabel("Impacto (0–10)", fontsize=12, fontweight='bold')
    ax.set_ylabel("")
    ax.set_xlim(-0.5, 10.5)
    ax.set_title("Distribución de Escenarios por Alternativa", 
                fontsize=14, fontweight='bold', pad=15)
    
    sns.despine(ax=ax, top=True, right=True)
    plt.tight_layout()
    
    return fig, ax


def create_seaborn_violin_modern(summary_rows: List[Dict[str, Any]]) -> tuple:
    """Enhanced Seaborn violin plot with darker outlines and diamond EV markers."""
    # Prepare data
    violin_data = []
    for row in summary_rows:
        samples = generate_violin_samples(row["Worst"], row["Best"], row["EV"])
        for sample in samples:
            violin_data.append({
                "Alternativa": row["Alternativa"],
                "Value": sample,
                "EV": row["EV"],
                "Range": row["Best"] - row["Worst"]
            })
    
    violin_df = pd.DataFrame(violin_data)
    
    # Set modern theme with enhanced aesthetics
    sns.set_theme(style="whitegrid", palette="husl")
    fig, ax = plt.subplots(figsize=(15, max(7, len(summary_rows) * 1.2)))
    
    # Create custom color palette based on EV values (Red→Yellow→Green)
    ev_colors = []
    ev_edge_colors = []  # Darker versions for outlines
    
    for row in summary_rows:
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
        
        # Main color
        ev_colors.append((r, g, b))
        
        # Darker edge color (reduce brightness by 30%)
        edge_r = max(0, r * 0.7)
        edge_g = max(0, g * 0.7)
        edge_b = max(0, b * 0.7)
        ev_edge_colors.append((edge_r, edge_g, edge_b))
    
    # Create violin plot with enhanced styling
    parts = ax.violinplot(
        [violin_df[violin_df["Alternativa"] == row["Alternativa"]]["Value"].values 
         for row in summary_rows],
        positions=range(len(summary_rows)),
        vert=False,
        widths=0.75,
        showmeans=False,
        showmedians=False,
        showextrema=False
    )
    
    # Style the violins with enhanced colors and darker outlines
    for i, (pc, row) in enumerate(zip(parts['bodies'], summary_rows)):
        pc.set_facecolor(ev_colors[i])
        pc.set_alpha(0.8)  # Slightly more opaque
        pc.set_edgecolor(ev_edge_colors[i])  # Darker outline
        pc.set_linewidth(2.5)  # Slightly thicker outline
    
    # Add enhanced diamond EV markers
    for i, row in enumerate(summary_rows):
        # Subtle shadow for depth
        ax.scatter(row["EV"], i, marker='D', s=320, color='black', 
                  alpha=0.15, zorder=13)
        
        # Main diamond marker with white outline
        ax.scatter(row["EV"], i, marker='D', s=280, color='white', 
                  edgecolor='black', linewidth=3, zorder=15, alpha=1.0)
        
        # Inner diamond with EV color
        ax.scatter(row["EV"], i, marker='D', s=200, color=ev_colors[i], 
                  edgecolor=ev_edge_colors[i], linewidth=2, zorder=16, alpha=1.0)
        
        # Inner highlight diamond for extra brilliance
        ax.scatter(row["EV"], i, marker='D', s=100, color='white', 
                  alpha=0.7, zorder=17)
        
        # Enhanced EV value annotation
        ax.annotate(f'{row["EV"]:.1f}', 
                   xy=(row["EV"], i), 
                   xytext=(25, 0), 
                   textcoords='offset points',
                   fontsize=12, 
                   fontweight='bold',
                   color='#1a1a1a',
                   ha='left', va='center',
                   bbox=dict(boxstyle='round,pad=0.5', 
                           facecolor='white', 
                           edgecolor=ev_edge_colors[i],
                           alpha=0.95,
                           linewidth=2),
                   zorder=18)
        
        # Elegant connecting line to marker
        ax.plot([row["EV"], row["EV"] + 0.6], [i, i], 
               color=ev_edge_colors[i], linewidth=2, alpha=0.6, zorder=14)
        
        # Enhanced range indicators with gradient effect
        range_x = np.linspace(row["Worst"], row["Best"], 50)
        range_y = [i] * 50
        
        # Create gradient effect for range line
        ax.plot([row["Worst"], row["Best"]], [i, i], 
               color=ev_colors[i], linewidth=4, alpha=0.4, zorder=1)
        ax.scatter([row["Worst"], row["Best"]], [i, i], 
                  color=ev_edge_colors[i], s=60, alpha=0.8, zorder=2,
                  edgecolor='white', linewidth=1)
    
    # Enhanced styling with better typography
    # ax.set_xlabel("Impacto (0–10)", fontsize=15, fontweight='bold', 
    #              color='#2c3e50', labelpad=15)
    ax.set_ylabel("")
    ax.set_xlim(-0.5, 10.5)
    ax.set_yticks(range(len(summary_rows)))
    ax.set_yticklabels([row["Alternativa"] for row in summary_rows], 
                      fontsize=13, fontweight='600', color='#34495e')
    
    # Enhanced title with subtitle
    ax.set_title("Análisis de Escenarios - Distribución de Probabilidades", 
                fontsize=18, fontweight='bold', pad=25, color='#2c3e50')
    
    # Subtitle with methodology explanation
    # ax.text(0.5, 1.02, "La anchura representa densidad de probabilidad • Los diamantes indican valores esperados (EV)", 
    #        transform=ax.transAxes, ha='center', va='bottom',
    #        fontsize=11, style='italic', color='#7f8c8d')
    
    # Enhanced grid styling
    ax.grid(True, alpha=0.25, linestyle='-', linewidth=0.8, color='#bdc3c7')
    ax.set_axisbelow(True)
    
    # Remove spines for clean look
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # Add subtle background gradient effect
    ax.set_facecolor('#fafbfc')
    
    plt.tight_layout()
    return fig, ax


def create_plotly_violin_interactive(summary_rows: List[Dict[str, Any]], dark_theme: bool = False) -> go.Figure:
    """Interactive Plotly violin plot with modern aesthetics."""
    # Prepare data
    violin_data = []
    for row in summary_rows:
        samples = generate_violin_samples(row["Worst"], row["Best"], row["EV"])
        violin_data.extend([{
            "Alternativa": row["Alternativa"],
            "Value": sample,
            "EV": row["EV"],
            "Worst": row["Worst"],
            "Best": row["Best"],
            "Range": row["Best"] - row["Worst"]
        } for sample in samples])
    
    violin_df = pd.DataFrame(violin_data)
    
    # Create figure
    fig = go.Figure()
    
    # Color palette - adapt for theme
    if dark_theme:
        colors = px.colors.qualitative.Pastel[:len(summary_rows)]
        bg_color = '#1e1e1e'
        text_color = '#ffffff'
        grid_color = 'rgba(255,255,255,0.1)'
    else:
        colors = px.colors.qualitative.Set3[:len(summary_rows)]
        bg_color = 'white'
        text_color = '#2E3440'
        grid_color = 'rgba(128,128,128,0.2)'
    
    # Add violin plots
    for i, (row, color) in enumerate(zip(summary_rows, colors)):
        alt_data = violin_df[violin_df["Alternativa"] == row["Alternativa"]]
        
        fig.add_trace(go.Violin(
            y=[row["Alternativa"]] * len(alt_data),
            x=alt_data["Value"],
            name=row["Alternativa"],
            orientation='h',
            side='positive',
            width=0.8,
            points=False,
            fillcolor=color,
            line=dict(color='white', width=2),
            opacity=0.7,
            hoveron='violins',
            hovertemplate=f"<b>{row['Alternativa']}</b><br>" +
                         "Valor: %{x:.1f}<br>" +
                         f"EV: {row['EV']:.1f}<br>" +
                         f"Rango: {row['Worst']:.1f} - {row['Best']:.1f}<br>" +
                         "<extra></extra>",
            showlegend=False
        ))
        
        # Add EV marker
        marker_color = '#1e1e1e' if dark_theme else 'white'
        fig.add_trace(go.Scatter(
            x=[row["EV"]],
            y=[row["Alternativa"]],
            mode='markers',
            marker=dict(
                size=20,
                color=marker_color,
                line=dict(color=color, width=3),
                symbol='diamond'
            ),
            name=f'EV: {row["EV"]:.1f}',
            hovertemplate=f"<b>Valor Esperado</b><br>" +
                         f"{row['Alternativa']}: {row['EV']:.1f}<br>" +
                         "<extra></extra>",
            showlegend=False
        ))
        
        # Add range indicators
        fig.add_trace(go.Scatter(
            x=[row["Worst"], row["Best"]],
            y=[row["Alternativa"], row["Alternativa"]],
            mode='markers+lines',
            line=dict(color=color, width=3, dash='dot'),
            marker=dict(size=8, color=color, opacity=0.6),
            name=f'Rango {row["Alternativa"]}',
            hovertemplate=f"<b>Rango de {row['Alternativa']}</b><br>" +
                         "Valor: %{x:.1f}<br>" +
                         "<extra></extra>",
            showlegend=False
        ))
    
    # Update layout with theme colors
    fig.update_layout(
        title=dict(
            text="Análisis Interactivo de Escenarios",
            font=dict(size=18, color=text_color),
            x=0.5
        ),
        xaxis=dict(
            title=dict(text="Impacto (0–10)", font=dict(size=14, color=text_color)),
            range=[-0.5, 10.5],
            gridcolor=grid_color,
            gridwidth=1,
            tickfont=dict(color=text_color)
        ),
        yaxis=dict(
            title=dict(text="", font=dict(size=14, color=text_color)),
            gridcolor=grid_color,
            gridwidth=1,
            tickfont=dict(color=text_color)
        ),
        plot_bgcolor=bg_color,
        paper_bgcolor=bg_color,
        height=max(400, len(summary_rows) * 80),
        margin=dict(l=80, r=80, t=80, b=60),
        hovermode='closest'
    )
    
    return fig


def create_plotly_ridgeline(summary_rows: List[Dict[str, Any]]) -> go.Figure:
    """Ridgeline plot (stacked density curves) using Plotly."""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Pastel[:len(summary_rows)]
    
    for i, (row, color) in enumerate(zip(summary_rows, colors)):
        # Generate samples
        samples = generate_violin_samples(row["Worst"], row["Best"], row["EV"], 500)
        
        # Create density curve
        hist, bin_edges = np.histogram(samples, bins=50, density=True)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Normalize and offset for ridgeline effect
        hist_normalized = hist / np.max(hist) * 0.8  # Scale height
        y_offset = i * 1.2  # Vertical spacing
        
        # Add filled area
        fig.add_trace(go.Scatter(
            x=bin_centers,
            y=hist_normalized + y_offset,
            fill='tonexty' if i > 0 else 'tozeroy',
            fillcolor=color,
            line=dict(color=color, width=2),
            name=row["Alternativa"],
            hovertemplate=f"<b>{row['Alternativa']}</b><br>" +
                         "Impacto: %{x:.1f}<br>" +
                         "Densidad: %{y:.2f}<br>" +
                         f"EV: {row['EV']:.1f}<br>" +
                         "<extra></extra>",
            showlegend=True
        ))
        
        # Add baseline
        fig.add_trace(go.Scatter(
            x=bin_centers,
            y=[y_offset] * len(bin_centers),
            mode='lines',
            line=dict(color='rgba(128,128,128,0.3)', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Add EV marker
        fig.add_trace(go.Scatter(
            x=[row["EV"]],
            y=[y_offset + 0.4],
            mode='markers+text',
            marker=dict(size=12, color='black', symbol='diamond'),
            text=[f'{row["EV"]:.1f}'],
            textposition='top center',
            textfont=dict(size=10, color='black'),
            name=f'EV {row["Alternativa"]}',
            showlegend=False,
            hovertemplate=f"<b>Valor Esperado</b><br>" +
                         f"{row['Alternativa']}: {row['EV']:.1f}<br>" +
                         "<extra></extra>"
        ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text="Ridgeline Plot - Distribuciones de Escenarios",
            font=dict(size=18, color='#2E3440'),
            x=0.5
        ),
        xaxis=dict(
            title=dict(text="Impacto (0–10)", font=dict(size=14, color='#2E3440')),
            range=[-0.5, 10.5]
        ),
        yaxis=dict(
            title=dict(text="Alternativas", font=dict(size=14, color='#2E3440')),
            tickmode='array',
            tickvals=[i * 1.2 for i in range(len(summary_rows))],
            ticktext=[row["Alternativa"] for row in summary_rows],
            range=[-0.5, len(summary_rows) * 1.2]
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=max(500, len(summary_rows) * 100),
        margin=dict(l=100, r=80, t=80, b=60),
        hovermode='closest'
    )
    
    return fig


def create_plotly_box_violin_hybrid(summary_rows: List[Dict[str, Any]]) -> go.Figure:
    """Hybrid box-violin plot with statistical annotations."""
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set2[:len(summary_rows)]
    
    for i, (row, color) in enumerate(zip(summary_rows, colors)):
        samples = generate_violin_samples(row["Worst"], row["Best"], row["EV"], 1000)
        
        # Add violin
        fig.add_trace(go.Violin(
            y=[row["Alternativa"]] * len(samples),
            x=samples,
            name=row["Alternativa"],
            orientation='h',
            side='positive',
            width=0.6,
            points='outliers',
            fillcolor=color,
            line=dict(color='white', width=1),
            opacity=0.6,
            box_visible=True,
            meanline_visible=True,
            showlegend=False
        ))
        
        # Add statistical annotations
        q25, q75 = np.percentile(samples, [25, 75])
        median = np.median(samples)
        
        # Add text annotations
        fig.add_annotation(
            x=row["EV"] + 1,
            y=row["Alternativa"],
            text=f"EV: {row['EV']:.1f}<br>Q1: {q25:.1f}<br>Q3: {q75:.1f}",
            showarrow=True,
            arrowhead=2,
            arrowcolor=color,
            bgcolor='white',
            bordercolor=color,
            borderwidth=1,
            font=dict(size=10)
        )
    
    fig.update_layout(
        title="Box-Violin Híbrido con Estadísticas",
        xaxis_title="Impacto (0–10)",
        height=max(400, len(summary_rows) * 80),
        plot_bgcolor='white'
    )
    
    return fig

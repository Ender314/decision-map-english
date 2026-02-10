# -*- coding: utf-8 -*-
"""
Advanced Scenarios utilities — Plotly tree visualization and EV helpers.
Used by the interactive scenarios tab for the read-only global tree.
"""

import plotly.graph_objects as go
from config.constants import (
    COLOR_PRIMARY, COLOR_ACCENT, COLOR_SUCCESS,
    COLOR_ERROR, COLOR_NEUTRAL
)


# ── Tree EV calculation ───────────────────────────────────────────

def _calculate_ev(node):
    """Recursively calculate Expected Value by folding back from leaves."""
    if not node["children"]:
        return float(node["score"])
    
    ev = 0.0
    total_prob = sum(c["probability"] for c in node["children"])
    if total_prob == 0:
        return 0.0
    
    for child in node["children"]:
        p = child["probability"] / total_prob  # Normalize
        child_ev = _calculate_ev(child)
        ev += p * child_ev
    return ev


# ── Plotly tree visualization ──────────────────────────────────────

def _layout_tree(node, x=0, y=0, x_spacing=1.0, depth=0):
    """Compute (x, y) positions for each node using a simple recursive layout."""
    positions = {}
    positions[node["id"]] = (x, y, node, depth)
    
    children = node.get("children", [])
    if not children:
        return positions, x
    
    # Leaf-count based spacing
    def count_leaves(n):
        if not n.get("children"):
            return 1
        return sum(count_leaves(c) for c in n["children"])
    
    total_leaves = count_leaves(node)
    start_x = x - (total_leaves - 1) * x_spacing / 2
    
    cursor = start_x
    for child in children:
        child_leaves = count_leaves(child)
        child_x = cursor + (child_leaves - 1) * x_spacing / 2
        child_positions, _ = _layout_tree(child, child_x, y - 1, x_spacing, depth + 1)
        positions.update(child_positions)
        cursor += child_leaves * x_spacing
    
    return positions, x


def _build_tree_figure(tree, alt_name, hide_root_prob=False):
    """Build a Plotly figure for the decision tree.
    
    Args:
        hide_root_prob: If True, don't show probability labels on root→level1 edges
    """
    positions, _ = _layout_tree(tree, x=0, y=0, x_spacing=1.8)
    
    fig = go.Figure()
    
    # Draw edges first
    for nid, (nx, ny, node, depth) in positions.items():
        for child in node.get("children", []):
            cid = child["id"]
            if cid in positions:
                cx, cy = positions[cid][0], positions[cid][1]
                
                # Line width proportional to probability (1px min, 6px max)
                prob = child.get("probability", 50)
                is_root_edge = depth == 0
                if is_root_edge and hide_root_prob:
                    line_w = 2.5  # Neutral width for decision edges
                else:
                    line_w = max(1, prob / 100 * 6)
                
                fig.add_trace(go.Scatter(
                    x=[nx, cx], y=[ny, cy],
                    mode="lines",
                    line=dict(color="#cbd5e0", width=line_w),
                    hoverinfo="skip",
                    showlegend=False
                ))
                # Edge label: probability (skip root edges if flagged)
                if not (is_root_edge and hide_root_prob):
                    mid_x, mid_y = (nx + cx) / 2, (ny + cy) / 2
                    fig.add_annotation(
                        x=mid_x, y=mid_y,
                        text=f"{child['probability']}%",
                        showarrow=False,
                        font=dict(size=10, color="#718096"),
                        bgcolor="white",
                        borderpad=2
                    )
    
    # Draw nodes
    for nid, (nx, ny, node, depth) in positions.items():
        is_root = depth == 0
        is_leaf = len(node.get("children", [])) == 0
        
        if is_root:
            color = COLOR_PRIMARY
            symbol = "square"
            size = 18
        elif is_leaf:
            score = node.get("score", 5)
            if score >= 7:
                color = COLOR_SUCCESS
            elif score >= 4:
                color = COLOR_ACCENT
            else:
                color = COLOR_ERROR
            symbol = "diamond"
            size = 14
        else:
            color = COLOR_NEUTRAL
            symbol = "circle"
            size = 14
        
        ev_text = ""
        if not is_root:
            ev_val = _calculate_ev(node)
            ev_text = f"<br>EV: {ev_val:.1f}"
        
        label_short = (node["label"][:30] + "…") if len(node["label"]) > 30 else node["label"]
        
        hover = (
            f"<b>{node['label']}</b><br>"
            f"Probabilidad: {node['probability']}%<br>"
            f"Puntuación: {node.get('score', '-')}"
            f"{ev_text}<extra></extra>"
        )
        
        fig.add_trace(go.Scatter(
            x=[nx], y=[ny],
            mode="markers+text",
            marker=dict(size=size, color=color, symbol=symbol, line=dict(width=1, color="white")),
            text=[label_short],
            textposition="top center",
            textfont=dict(size=10),
            hovertemplate=hover,
            showlegend=False,
            customdata=[nid]
        ))
    
    # Layout
    all_x = [p[0] for p in positions.values()]
    all_y = [p[1] for p in positions.values()]
    x_margin = 1.5
    y_margin = 0.5
    
    fig.update_layout(
        height=300 + len(positions) * 20,
        margin=dict(l=20, r=20, t=30, b=20),
        xaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[min(all_x) - x_margin, max(all_x) + x_margin]
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showticklabels=False,
            range=[min(all_y) - y_margin, max(all_y) + y_margin]
        ),
        plot_bgcolor="white",
        showlegend=False
    )
    
    return fig

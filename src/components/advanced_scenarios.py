# -*- coding: utf-8 -*-
"""
Advanced Scenarios tab - Decision tree analysis per alternative.
Allows building bifurcation trees with scores and probabilities.
Max 3 branches per node, max 2 levels deep.
"""

import streamlit as st
import uuid
import plotly.graph_objects as go
from config.constants import (
    ADV_SCENARIO_MAX_BRANCHES, ADV_SCENARIO_MAX_DEPTH,
    PROBABILITY_STEPS, COLOR_PRIMARY, COLOR_ACCENT, COLOR_SUCCESS,
    COLOR_WARNING, COLOR_ERROR, COLOR_NEUTRAL
)
from utils.calculations import get_disqualified_alternatives


# ── Tree data helpers ──────────────────────────────────────────────

def _new_node(label="", probability=50, score=5):
    """Create a new tree node."""
    return {
        "id": str(uuid.uuid4()),
        "label": label,
        "probability": probability,  # 0-100 integer
        "score": score,              # 0-10 integer
        "children": []
    }


def _init_tree_for_alt(alt_name):
    """Initialize a default tree (root + 2 children) for an alternative."""
    return {
        "id": str(uuid.uuid4()),
        "label": alt_name,
        "probability": 100,
        "score": 0,
        "children": [
            _new_node("Mejor escenario", 50, 7),
            _new_node("Peor escenario", 50, 3),
        ]
    }


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


def _get_depth(node, current=0):
    """Get max depth of the tree."""
    if not node["children"]:
        return current
    return max(_get_depth(c, current + 1) for c in node["children"])


def _find_node(tree, node_id):
    """Find a node by ID in the tree. Returns (node, parent) or (None, None)."""
    if tree["id"] == node_id:
        return tree, None
    for child in tree.get("children", []):
        found, parent = _find_node(child, node_id)
        if found:
            return found, parent if parent else tree
    return None, None


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


# ── Node editor (Streamlit widgets) ───────────────────────────────

def _render_node_editor(node, tree, alt_id, depth=0, parent=None):
    """Render editable widgets for a single node and its children recursively."""
    node_id = node["id"]
    is_root = depth == 0
    children = node.get("children", [])
    
    if is_root:
        # Root node: just show children editors
        if not children:
            if st.button("➕ Añadir primer bifurcación", key=f"add_first_{alt_id}"):
                node["children"] = [
                    _new_node("Mejor escenario", 50, 7),
                    _new_node("Peor escenario", 50, 3),
                ]
                st.rerun()
        
        for child in children:
            _render_node_editor(child, tree, alt_id, depth + 1, parent=node)
        
        # Add branch button (if under max)
        if 0 < len(children) < ADV_SCENARIO_MAX_BRANCHES:
            if st.button(f"➕ Añadir rama (nivel 1)", key=f"add_l1_{alt_id}"):
                _redistribute_and_add(node, "Nuevo escenario", 5)
                st.rerun()
        return
    
    # Non-root node
    prefix = "├─" if parent and node != parent["children"][-1] else "└─"
    depth_indent = "&nbsp;" * (depth * 4)
    
    st.markdown(f"{depth_indent}{prefix} **{node['label'] or 'Sin nombre'}**", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 0.5])
    
    with c1:
        new_label = st.text_input(
            "Descripción",
            value=node["label"],
            key=f"lbl_{node_id}",
            label_visibility="collapsed",
            placeholder="Describe este escenario..."
        )
        node["label"] = new_label
    
    with c2:
        new_prob = st.number_input(
            "Prob %",
            min_value=0, max_value=100, step=5,
            value=node["probability"],
            key=f"prob_{node_id}",
            label_visibility="collapsed"
        )
        node["probability"] = new_prob
    
    with c3:
        new_score = st.slider(
            "Puntuación",
            min_value=0, max_value=10, step=1,
            value=node["score"],
            key=f"score_{node_id}",
            label_visibility="collapsed"
        )
        node["score"] = new_score
    
    with c4:
        if st.button("🗑", key=f"del_{node_id}"):
            if parent:
                parent["children"] = [c for c in parent["children"] if c["id"] != node_id]
                st.rerun()
    
    # Sub-children (level 2)
    if depth < ADV_SCENARIO_MAX_DEPTH:
        for child in children:
            _render_node_editor(child, tree, alt_id, depth + 1, parent=node)
        
        if 0 < len(children) < ADV_SCENARIO_MAX_BRANCHES:
            if st.button(f"➕ Sub-rama", key=f"add_sub_{node_id}"):
                _redistribute_and_add(node, "Sub-escenario", 5)
                st.rerun()
        elif len(children) == 0 and depth < ADV_SCENARIO_MAX_DEPTH:
            if st.button(f"🔀 Bifurcar", key=f"bif_{node_id}"):
                node["children"] = [
                    _new_node("Mejor sub-escenario", 50, min(node["score"] + 2, 10)),
                    _new_node("Peor sub-escenario", 50, max(node["score"] - 2, 0)),
                ]
                st.rerun()


def _redistribute_and_add(parent_node, new_label, new_score):
    """Add a new child and redistribute probabilities evenly across all siblings."""
    children = parent_node["children"]
    new_count = len(children) + 1
    # Distribute evenly, give remainder to last child
    base = 100 // new_count
    remainder = 100 - base * new_count
    for i, child in enumerate(children):
        child["probability"] = base + (remainder if i == len(children) - 1 else 0)
    parent_node["children"].append(_new_node(new_label, base, new_score))
    # Adjust: give remainder to first child for cleaner numbers
    total = sum(c["probability"] for c in parent_node["children"])
    if total != 100:
        parent_node["children"][0]["probability"] += 100 - total


# ── Probability validation ─────────────────────────────────────────

def _validate_probabilities(node, issues=None, path=""):
    """Check that sibling probabilities sum to ~100%."""
    if issues is None:
        issues = []
    
    children = node.get("children", [])
    if children:
        total = sum(c["probability"] for c in children)
        if abs(total - 100) > 1:
            issues.append(f"{path or 'Raíz'}: probabilidades suman {total}% (deben sumar 100%)")
        
        for child in children:
            _validate_probabilities(child, issues, path=f"{path} > {child['label'][:20]}")
    
    return issues


# ── Main render function ───────────────────────────────────────────

def render_advanced_scenarios_tab():
    """Render the Advanced Scenarios (Decision Tree) tab."""
    st.markdown("### 🌳 Escenarios Avanzados", unsafe_allow_html=True)
    
    all_alts = [a for a in st.session_state.alts if a["text"].strip()]
    if not all_alts:
        st.info("🌳 Los escenarios avanzados te permiten construir un árbol de decisión por alternativa. Primero define tus **Alternativas**.")
        return
    
    # Filter disqualified
    disqualified_alts = get_disqualified_alternatives()
    alts = [a for a in all_alts if a["id"] not in disqualified_alts]
    
    if disqualified_alts and len(alts) == 0:
        st.error("⚠️ Todas las alternativas están descalificadas por No Negociables.")
        return
    
    # Initialize advanced_scenarios in session state
    if "advanced_scenarios" not in st.session_state:
        st.session_state.advanced_scenarios = {}
    
    # Process each alternative
    ev_results = []
    
    for alt in alts:
        alt_id, alt_name = alt["id"], alt["text"].strip()
        
        # Initialize tree if needed
        if alt_id not in st.session_state.advanced_scenarios:
            st.session_state.advanced_scenarios[alt_id] = _init_tree_for_alt(alt_name)
        
        tree = st.session_state.advanced_scenarios[alt_id]
        tree["label"] = alt_name  # Keep synced
        
        with st.expander(f"🌳 {alt_name}", expanded=False):
            # Column headers
            c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 0.5])
            with c1:
                st.caption("Descripción")
            with c2:
                st.caption("Prob. %")
            with c3:
                st.caption("Puntuación (0-10)")
            with c4:
                st.caption("")
            
            # Node editor FIRST (so widgets update state before chart renders)
            _render_node_editor(tree, tree, alt_id, depth=0)
            
            # Probability validation
            issues = _validate_probabilities(tree)
            if issues:
                for issue in issues:
                    st.warning(f"⚠️ {issue}")
            
            # EV display
            ev = _calculate_ev(tree)
            st.metric("Valor Esperado (EV)", f"{ev:.2f}", help="Calculado recursivamente: EV = Σ(probabilidad × EV hijo)")
            
            # Tree visualization AFTER inputs (reflects current values immediately)
            fig = _build_tree_figure(tree, alt_name)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        
        ev_results.append({"alt_name": alt_name, "alt_id": alt_id, "ev": _calculate_ev(tree)})
    
    # Summary comparison
    if len(ev_results) > 1:
        st.markdown("---")
        st.markdown("### 📊 Comparación de Valores Esperados")
        
        ev_sorted = sorted(ev_results, key=lambda x: x["ev"], reverse=True)
        
        fig_bar = go.Figure()
        colors = [COLOR_SUCCESS if i == 0 else COLOR_PRIMARY for i in range(len(ev_sorted))]
        
        fig_bar.add_trace(go.Bar(
            x=[r["alt_name"] for r in ev_sorted],
            y=[r["ev"] for r in ev_sorted],
            marker_color=colors,
            text=[f"{r['ev']:.2f}" for r in ev_sorted],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>EV: %{y:.2f}<extra></extra>"
        ))
        
        fig_bar.update_layout(
            height=300,
            margin=dict(l=40, r=20, t=20, b=60),
            yaxis=dict(title="Valor Esperado", range=[0, 10.5]),
            xaxis=dict(title=""),
            plot_bgcolor="white",
            showlegend=False
        )
        
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
        
        winner = ev_sorted[0]
        st.success(f"🏆 **Mayor valor esperado**: {winner['alt_name']} (EV: {winner['ev']:.2f})")
        st.caption("EV = Σ(probabilidad normalizada × puntuación). Se calcula recursivamente desde las hojas del árbol. Escala 0–10.")
    
    # Global decision tree showing all alternatives
    if len(ev_results) >= 1:
        st.markdown("---")
        st.markdown("### 🌳 Árbol de Decisión Completo")
        
        # Build a meta-tree: decision root → alternatives → their children
        decision_root = {
            "id": "decision_root",
            "label": st.session_state.get("objetivo", "Decisión")[:40] or "Decisión",
            "probability": 100,
            "score": 0,
            "children": []
        }
        
        for alt in alts:
            alt_id = alt["id"]
            if alt_id in st.session_state.advanced_scenarios:
                tree = st.session_state.advanced_scenarios[alt_id]
                alt_ev = _calculate_ev(tree)
                # Clone the alt tree as a child of the decision root
                alt_node = {
                    "id": f"global_{alt_id}",
                    "label": tree["label"],
                    "probability": round(100 / len(alts)),
                    "score": round(alt_ev),
                    "children": tree.get("children", [])
                }
                decision_root["children"].append(alt_node)
        
        # Fix rounding so probabilities sum to 100
        if decision_root["children"]:
            total_p = sum(c["probability"] for c in decision_root["children"])
            if total_p != 100:
                decision_root["children"][0]["probability"] += 100 - total_p
        
        fig_global = _build_tree_figure(decision_root, "Decisión", hide_root_prob=True)
        fig_global.update_layout(height=400 + len(alts) * 80)
        st.plotly_chart(fig_global, use_container_width=True, config={"displayModeBar": False})
        st.caption("🌳 Árbol completo: la raíz es la decisión, el primer nivel son las alternativas, y sus ramas son los escenarios definidos.")
    
    # Help section
    st.markdown("---")
    with st.expander("*\"¿Cómo funciona el árbol de decisión?\"*", expanded=False):
        st.markdown(f"""
        Cada alternativa se descompone en **posibles bifurcaciones** (escenarios que podrían ocurrir).
        
        - **Máximo {ADV_SCENARIO_MAX_BRANCHES} ramas** por nodo
        - **Máximo {ADV_SCENARIO_MAX_DEPTH} niveles** de profundidad
        - Las **probabilidades** de ramas hermanas deben sumar **100%**
        - La **puntuación** (0-10) refleja qué tan favorable es ese escenario
        - El **Valor Esperado** se calcula recursivamente desde las hojas hasta la raíz
        
        *Ejemplo: Si una alternativa tiene 60% de probabilidad de un escenario bueno (puntuación 8) 
        y 40% de uno malo (puntuación 3), su EV = 0.6 × 8 + 0.4 × 3 = 6.0*
        """)

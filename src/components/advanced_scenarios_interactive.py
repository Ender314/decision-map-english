# -*- coding: utf-8 -*-
"""
Interactive Advanced Scenarios tab - Decision tree with clickable nodes.
Uses streamlit-agraph (vis.js) for interactive tree visualization.
Same data model as advanced_scenarios.py but interaction happens on the graph.
"""

import streamlit as st
import uuid
import plotly.graph_objects as go
from streamlit_agraph import agraph, Node, Edge, Config
from config.constants import (
    ADV_SCENARIO_MAX_BRANCHES, ADV_SCENARIO_MAX_DEPTH,
    COLOR_PRIMARY, COLOR_ACCENT, COLOR_SUCCESS,
    COLOR_WARNING, COLOR_ERROR, COLOR_NEUTRAL
)
from utils.calculations import get_disqualified_alternatives
from components.advanced_scenarios import _build_tree_figure


# ── Tree data helpers (shared logic with advanced_scenarios.py) ────

def _new_node(label="", probability=50, score=5):
    """Create a new tree node."""
    return {
        "id": str(uuid.uuid4()),
        "label": label,
        "probability": probability,
        "score": score,
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
        p = child["probability"] / total_prob
        ev += p * _calculate_ev(child)
    return ev


def _get_depth(node, current=0):
    """Get max depth of the tree."""
    if not node["children"]:
        return current
    return max(_get_depth(c, current + 1) for c in node["children"])


def _find_node(tree, node_id):
    """Find a node by ID. Returns (node, parent, depth)."""
    if tree["id"] == node_id:
        return tree, None, 0
    return _find_node_recursive(tree, node_id, 0)


def _find_node_recursive(parent, node_id, depth):
    for child in parent.get("children", []):
        if child["id"] == node_id:
            return child, parent, depth + 1
        found, p, d = _find_node_recursive(child, node_id, depth + 1)
        if found:
            return found, p, d
    return None, None, -1


def _redistribute_and_add(parent_node, new_label, new_score):
    """Add a new child and redistribute probabilities evenly."""
    children = parent_node["children"]
    new_count = len(children) + 1
    base = 100 // new_count
    for child in children:
        child["probability"] = base
    parent_node["children"].append(_new_node(new_label, base, new_score))
    total = sum(c["probability"] for c in parent_node["children"])
    if total != 100:
        parent_node["children"][0]["probability"] += 100 - total


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


# ── Agraph tree builder ───────────────────────────────────────────

def _tree_to_agraph(tree, nodes, edges, depth=0, is_global=False):
    """Recursively convert tree dict to agraph Nodes and Edges."""
    node = tree
    is_root = depth == 0
    is_leaf = len(node.get("children", [])) == 0
    
    ev = _calculate_ev(node)
    score = node.get("score", 0)
    
    # Node styling
    if is_root:
        color = {"background": COLOR_PRIMARY, "border": COLOR_PRIMARY}
        shape = "box"
        size_val = 15
        label = node["label"]
        font_cfg = {"size": 12, "color": "#ffffff"}
        tooltip = f"{node['label']} (raíz)"
    elif is_leaf:
        if score >= 7:
            color = COLOR_SUCCESS
        elif score >= 4:
            color = COLOR_ACCENT
        else:
            color = COLOR_ERROR
        shape = "diamond"
        size_val = 12
        label = f"{node['label']}\n🎯 {score}/10 | EV: {ev:.1f}"
        font_cfg = {"size": 11, "color": "#2d3748"}
        tooltip = f"{node['label']}\nProbabilidad: {node['probability']}%\nPuntuación: {score}/10\nEV: {ev:.1f}"
    else:
        color = COLOR_NEUTRAL
        shape = "dot"
        size_val = 12
        label = f"{node['label']}\nEV: {ev:.1f}"
        font_cfg = {"size": 11, "color": "#2d3748"}
        tooltip = f"{node['label']}\nProbabilidad: {node['probability']}%\nEV: {ev:.1f}"
    
    nodes.append(Node(
        id=node["id"],
        title=tooltip,
        label=label,
        size=size_val,
        color=color,
        shape=shape,
        font=font_cfg,
        borderWidth=2,
        borderWidthSelected=4,
    ))
    
    for child in node.get("children", []):
        prob = child.get("probability", 50)
        # Hide probability labels on root→level1 edges in global tree
        show_label = not (is_global and depth == 0)
        edge_label = f"{prob}%" if show_label else ""
        edge_width = max(1, prob / 100 * 6) if show_label else 2.5
        
        edges.append(Edge(
            source=node["id"],
            target=child["id"],
            label=edge_label,
            width=edge_width,
            color="#cbd5e0",
            font={"size": 10, "color": "#718096", "align": "middle"},
        ))
        _tree_to_agraph(child, nodes, edges, depth + 1, is_global=is_global)


def _render_agraph_tree(tree, key_suffix, is_global=False):
    """Render an interactive agraph tree and return the selected node ID."""
    nodes = []
    edges = []
    _tree_to_agraph(tree, nodes, edges, is_global=is_global)
    
    config = Config(
        directed=True,
        hierarchical=True,
        nodeHighlightBehavior=True,
        highlightColor="#f6ad55",
        collapsible=False,
        height=450 + len(nodes) * 20,
        width=950,
        physics=False,
        levelSeparation=120,
        nodeSpacing=180,
        treeSpacing=200,
        sortMethod="directed",
    )
    
    selected = agraph(
        nodes=nodes,
        edges=edges,
        config=config,
    )
    
    return selected


# ── Node action panel ─────────────────────────────────────────────

def _render_action_panel(tree, selected_id, alt_id):
    """Show edit/action controls for the selected node."""
    node, parent, depth = _find_node(tree, selected_id)
    if not node:
        return
    
    is_root = depth == 0
    is_leaf = len(node.get("children", [])) == 0
    children = node.get("children", [])
    
    st.markdown(f"**Nodo seleccionado:** {node['label']}")
    
    if is_root:
        # Root: can only add children
        st.caption("Este es el nodo raíz (alternativa). Haz clic en un escenario para editarlo.")
        if not children:
            if st.button("➕ Añadir primera bifurcación", key=f"iact_add_first_{alt_id}"):
                node["children"] = [
                    _new_node("Mejor escenario", 50, 7),
                    _new_node("Peor escenario", 50, 3),
                ]
                st.rerun()
        elif len(children) < ADV_SCENARIO_MAX_BRANCHES:
            if st.button("➕ Añadir rama", key=f"iact_add_root_{alt_id}"):
                _redistribute_and_add(node, "Nuevo escenario", 5)
                st.rerun()
    else:
        # Editable node
        c1, c2 = st.columns(2)
        with c1:
            new_label = st.text_input(
                "Descripción", value=node["label"],
                key=f"iact_lbl_{selected_id}",
                placeholder="Describe este escenario..."
            )
            if new_label != node["label"]:
                node["label"] = new_label
                st.rerun()
        
        with c2:
            col_p, col_s = st.columns(2)
            with col_p:
                new_prob = st.number_input(
                    "Probabilidad %",
                    min_value=0, max_value=100, step=5,
                    value=node["probability"],
                    key=f"iact_prob_{selected_id}"
                )
                if new_prob != node["probability"]:
                    node["probability"] = new_prob
                    st.rerun()
            with col_s:
                new_score = st.slider(
                    "Puntuación (0-10)",
                    min_value=0, max_value=10, step=1,
                    value=node["score"],
                    key=f"iact_score_{selected_id}"
                )
                if new_score != node["score"]:
                    node["score"] = new_score
                    st.rerun()
        
        # Action buttons
        btn_cols = st.columns(3)
        
        with btn_cols[0]:
            # Bifurcate (add children to this leaf)
            if is_leaf and depth < ADV_SCENARIO_MAX_DEPTH:
                if st.button("🔀 Bifurcar", key=f"iact_bif_{selected_id}"):
                    node["children"] = [
                        _new_node("Mejor sub-escenario", 50, min(node["score"] + 2, 10)),
                        _new_node("Peor sub-escenario", 50, max(node["score"] - 2, 0)),
                    ]
                    st.rerun()
        
        with btn_cols[1]:
            # Add sibling branch (to parent)
            if not is_root and len(children) < ADV_SCENARIO_MAX_BRANCHES and not is_leaf:
                if st.button("➕ Sub-rama", key=f"iact_addsub_{selected_id}"):
                    _redistribute_and_add(node, "Sub-escenario", 5)
                    st.rerun()
        
        with btn_cols[2]:
            # Delete this node
            if parent and len(parent.get("children", [])) > 1:
                if st.button("🗑️ Eliminar", key=f"iact_del_{selected_id}"):
                    parent["children"] = [c for c in parent["children"] if c["id"] != selected_id]
                    if f"_iact_selected_{alt_id}" in st.session_state:
                        del st.session_state[f"_iact_selected_{alt_id}"]
                    st.rerun()


# ── Main render function ───────────────────────────────────────────

def render_interactive_scenarios_tab():
    """Render the Interactive Scenarios tab with agraph-based trees."""
    st.markdown("### 🎮 Escenarios Interactivos", unsafe_allow_html=True)
    st.caption("Haz clic en un nodo del árbol para seleccionarlo y editarlo.")
    
    all_alts = [a for a in st.session_state.alts if a["text"].strip()]
    if not all_alts:
        st.info("🎮 Los escenarios interactivos te permiten construir un árbol de decisión haciendo clic en los nodos. Primero define tus **Alternativas**.")
        return
    
    disqualified_alts = get_disqualified_alternatives()
    alts = [a for a in all_alts if a["id"] not in disqualified_alts]
    
    if disqualified_alts and len(alts) == 0:
        st.error("⚠️ Todas las alternativas están descalificadas por No Negociables.")
        return
    
    # Use the same session state key as advanced_scenarios for shared data
    if "advanced_scenarios" not in st.session_state:
        st.session_state.advanced_scenarios = {}
    
    ev_results = []
    
    for alt in alts:
        alt_id, alt_name = alt["id"], alt["text"].strip()
        
        if alt_id not in st.session_state.advanced_scenarios:
            st.session_state.advanced_scenarios[alt_id] = _init_tree_for_alt(alt_name)
        
        tree = st.session_state.advanced_scenarios[alt_id]
        tree["label"] = alt_name
        
        with st.expander(f"🎮 {alt_name}", expanded=False):
            # Interactive tree — click returns selected node ID
            selected = _render_agraph_tree(tree, key_suffix=alt_id)
            
            # Track selection in session state
            sel_key = f"_iact_selected_{alt_id}"
            if selected:
                st.session_state[sel_key] = selected
            
            current_selected = st.session_state.get(sel_key)
            
            # Validation
            issues = _validate_probabilities(tree)
            if issues:
                for issue in issues:
                    st.warning(f"⚠️ {issue}")
            
            # EV
            ev = _calculate_ev(tree)
            st.metric("Valor Esperado (EV)", f"{ev:.2f}")
            
            # Action panel for selected node
            if current_selected:
                st.markdown("---")
                _render_action_panel(tree, current_selected, alt_id)
            else:
                st.info("👆 Haz clic en un nodo del árbol para editarlo.")
        
        ev_results.append({"alt_name": alt_name, "alt_id": alt_id, "ev": _calculate_ev(tree)})
    
    # EV comparison bar chart
    if len(ev_results) > 1:
        st.markdown("---")
        st.markdown("### 📊 Comparación de Valores Esperados")
        
        ev_sorted = sorted(ev_results, key=lambda x: x["ev"], reverse=True)
        colors = [COLOR_SUCCESS if i == 0 else COLOR_PRIMARY for i in range(len(ev_sorted))]
        
        fig_bar = go.Figure()
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
        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False}, key="interactive_ev_bar")
        
        winner = ev_sorted[0]
        st.success(f"🏆 **Mayor valor esperado**: {winner['alt_name']} (EV: {winner['ev']:.2f})")
    
    # Global decision tree
    if len(ev_results) >= 1:
        st.markdown("---")
        st.markdown("### 🌳 Árbol de Decisión Completo")
        
        decision_root = {
            "id": "decision_root_interactive",
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
                alt_node = {
                    "id": f"iglobal_{alt_id}",
                    "label": tree["label"],
                    "probability": round(100 / len(alts)),
                    "score": round(alt_ev),
                    "children": tree.get("children", [])
                }
                decision_root["children"].append(alt_node)
        
        if decision_root["children"]:
            total_p = sum(c["probability"] for c in decision_root["children"])
            if total_p != 100:
                decision_root["children"][0]["probability"] += 100 - total_p
        
        fig_global = _build_tree_figure(decision_root, "Decisión", hide_root_prob=True)
        fig_global.update_layout(height=400 + len(alts) * 80)
        st.plotly_chart(fig_global, use_container_width=True, config={"displayModeBar": False}, key="interactive_global_tree")
        st.caption("🌳 Árbol completo (solo lectura): la raíz es la decisión, el primer nivel son las alternativas.")
    
    # Help
    st.markdown("---")
    with st.expander("*\"¿Cómo funciona la versión interactiva?\"*", expanded=False):
        st.markdown(f"""
        Esta versión usa una visualización interactiva donde puedes:
        
        - **Hacer clic en cualquier nodo** para seleccionarlo
        - **Editar** la descripción, probabilidad y puntuación del nodo seleccionado
        - **Bifurcar** un nodo hoja para crear sub-escenarios
        - **Añadir ramas** adicionales (máximo {ADV_SCENARIO_MAX_BRANCHES} por nodo)
        - **Eliminar** nodos que ya no necesites
        
        Los datos son **compartidos** con la pestaña Escenarios Avanzados — editar en una pestaña se refleja en la otra.
        """)

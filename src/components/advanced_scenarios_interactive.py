# -*- coding: utf-8 -*-
"""
Interactive Advanced Scenarios tab - Decision tree with clickable nodes.
Uses streamlit-agraph (vis.js) for interactive tree visualization.
Same data model as advanced_scenarios.py but interaction happens on the graph.
"""

import streamlit as st
import uuid
import plotly.graph_objects as go
import numpy as np
from streamlit_agraph import agraph, Node, Edge, Config
from config.constants import (
    COLOR_PRIMARY, COLOR_ACCENT, COLOR_SUCCESS,
    COLOR_ERROR, COLOR_NEUTRAL,
    COMPOSITE_DEFAULT_MCDA_WEIGHT_PCT,
)
from utils.calculations import get_disqualified_alternatives, mcda_totals_and_ranking
import pandas as pd


MAX_TREE_DEPTH = 3
MAX_NODE_BRANCHES = 4


# ── Tree data helpers (shared logic with advanced_scenarios.py) ────

def _new_node(label="", probability=50, score=5, node_type="scenario", alt_id=None):
    """Create a new tree node."""
    return {
        "id": str(uuid.uuid4()),
        "label": label,
        "probability": probability,
        "score": score,
        "children": [],
        "node_type": node_type,
        "alt_id": alt_id,
    }


def _new_decision_tree(decision_label):
    """Create the unified decision tree root."""
    return {
        "id": str(uuid.uuid4()),
        "label": decision_label,
        "probability": 100,
        "score": 0,
        "children": [],
        "node_type": "root",
        "alt_id": None,
    }


def _build_mcda_score_lookup(alts):
    """Return MCDA score lookup by alternative name for ordering/hints."""
    if not (
        st.session_state.get("mcda_scores")
        and "mcda_scores_df" in st.session_state
        and "mcda_criteria" in st.session_state
    ):
        return {}

    scores_df = st.session_state.mcda_scores_df
    _, ranking_all = mcda_totals_and_ranking(scores_df.copy(), st.session_state.mcda_criteria)
    qualified_names = {a["text"].strip() for a in alts}
    return {
        item["alternativa"]: item["score"]
        for item in ranking_all
        if item["alternativa"] in qualified_names
    }


def _sync_root_alternatives(decision_tree, alts, mcda_by_name):
    """Auto-sync level-1 alternative nodes with current qualified alternatives."""
    existing_alt_nodes = {
        child.get("alt_id"): child
        for child in decision_tree.get("children", [])
        if child.get("node_type") == "alternative" and child.get("alt_id")
    }

    ordered_alts = sorted(
        alts,
        key=lambda a: mcda_by_name.get(a["text"].strip(), -1),
        reverse=True,
    )

    synced_children = []
    for alt in ordered_alts:
        alt_id = alt["id"]
        alt_name = alt["text"].strip()
        mcda_hint = mcda_by_name.get(alt_name)

        node = existing_alt_nodes.get(alt_id)
        if not node:
            node = _new_node(
                label=alt_name,
                probability=100,
                score=5,
                node_type="alternative",
                alt_id=alt_id,
            )

        node["label"] = alt_name
        node["node_type"] = "alternative"
        node["alt_id"] = alt_id
        node["probability"] = 100
        node["mcda_hint"] = mcda_hint
        node.setdefault("children", [])
        synced_children.append(node)

    decision_tree["children"] = synced_children


def _project_unified_tree_to_per_alt(decision_tree):
    """Project unified tree back to per-alternative map for downstream compatibility."""
    projected = {}
    for child in decision_tree.get("children", []):
        if child.get("node_type") == "alternative" and child.get("alt_id"):
            projected[child["alt_id"]] = child
    return projected


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


def _rebalance_sibling_probabilities(parent_node, selected_child_id, new_prob):
    """Rebalance sibling probabilities so children always sum exactly to 100."""
    children = parent_node.get("children", [])
    if not children:
        return

    selected = next((c for c in children if c.get("id") == selected_child_id), None)
    if not selected:
        return

    clamped_prob = int(max(0, min(100, int(new_prob))))
    selected["probability"] = clamped_prob

    siblings = [c for c in children if c.get("id") != selected_child_id]
    if not siblings:
        return

    remaining = 100 - clamped_prob
    prev_total = sum(max(0, int(s.get("probability", 0))) for s in siblings)

    if prev_total <= 0:
        base = remaining // len(siblings)
        for sibling in siblings:
            sibling["probability"] = base
        siblings[0]["probability"] += remaining - base * len(siblings)
        return

    raw_allocations = [remaining * (max(0, int(s.get("probability", 0))) / prev_total) for s in siblings]
    floored = [int(v) for v in raw_allocations]
    remainder = remaining - sum(floored)

    fractions = [v - int(v) for v in raw_allocations]
    order = sorted(range(len(siblings)), key=lambda i: fractions[i], reverse=True)
    for i in range(remainder):
        floored[order[i % len(order)]] += 1

    for sibling, value in zip(siblings, floored):
        sibling["probability"] = value


def _collect_leaves(node, path_prob=1.0, leaves=None):
    """Collect all leaf nodes with their effective (path) probability."""
    if leaves is None:
        leaves = []
    children = node.get("children", [])
    if not children:
        leaves.append({"label": node["label"], "score": node["score"],
                       "probability": node["probability"], "path_prob": path_prob})
        return leaves
    total_p = sum(c["probability"] for c in children)
    if total_p == 0:
        return leaves
    for child in children:
        child_path = path_prob * (child["probability"] / total_p)
        _collect_leaves(child, child_path, leaves)
    return leaves


def _sync_tree_to_flat(alt_id, alt_name, tree):
    """Sync tree data into st.session_state['scenarios'] flat format.
    
    This bridges the tree model to the flat format expected by
    resultados.py, informe.py, and data_manager.py.
    """
    if "scenarios" not in st.session_state:
        st.session_state.scenarios = {}
    
    leaves = _collect_leaves(tree)
    if not leaves:
        return
    
    ev = _calculate_ev(tree)
    scores = [l["score"] for l in leaves]
    worst_score = min(scores)
    best_score = max(scores)
    
    # Find labels for worst/best leaves
    worst_leaf = min(leaves, key=lambda l: l["score"])
    best_leaf = max(leaves, key=lambda l: l["score"])
    
    # Approximate p_best: sum of path probabilities for leaves at best_score
    p_best = sum(l["path_prob"] for l in leaves if l["score"] == best_score)
    p_best = max(0.0, min(1.0, p_best))  # Clamp
    
    st.session_state.scenarios[alt_id] = {
        "name": alt_name,
        "worst_desc": worst_leaf["label"],
        "worst_score": float(worst_score),
        "best_desc": best_leaf["label"],
        "best_score": float(best_score),
        "p_best": p_best,
        "p_best_pct": int(p_best * 100),
        "ev": ev,
    }


def _validate_probabilities(node, issues=None, path=""):
    """Check that sibling probabilities sum to ~100%."""
    if issues is None:
        issues = []
    children = node.get("children", [])
    if children:
        total = sum(c["probability"] for c in children)
        is_decision_root = node.get("node_type") == "root"
        if not is_decision_root and abs(total - 100) > 1:
            issues.append(f"{path or 'Raíz'}: probabilidades suman {total}% (deben sumar 100%)")
        for child in children:
            _validate_probabilities(child, issues, path=f"{path} > {child['label'][:20]}")
    return issues


# ── Agraph tree builder ───────────────────────────────────────────

def _tree_to_agraph(tree, nodes, edges, depth=0, is_global=False):
    """Recursively convert tree dict to agraph Nodes and Edges."""
    node = tree
    is_root = depth == 0
    is_alternative = node.get("node_type") == "alternative"
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
        tooltip = "Decision\nNodo raiz de la decision"
    elif is_alternative:
        color = {"background": "#edf2f7", "border": "#a0aec0"}
        shape = "box"
        size_val = 13
        mcda_hint = node.get("mcda_hint")
        label = node["label"]
        font_cfg = {"size": 11, "color": "#2d3748"}
        mcda_text = f"{mcda_hint:.2f}" if mcda_hint is not None else "N/D"
        tooltip = f"Alternativa\nMCDA: {mcda_text}\nEV: {ev:.2f}"
    elif is_leaf:
        if score >= 7:
            color = COLOR_SUCCESS
        elif score >= 4:
            color = COLOR_ACCENT
        else:
            color = COLOR_ERROR
        shape = "diamond"
        size_val = 12
        label = f"{node['label']}\n🎯 {score}/10"
        font_cfg = {"size": 11, "color": "#2d3748"}
        tooltip = f"Escenario\nProbabilidad: {node['probability']}%\nPuntuacion: {score}/10\nEV: {ev:.2f}"
    else:
        color = COLOR_NEUTRAL
        shape = "dot"
        size_val = 12
        label = node["label"]
        font_cfg = {"size": 11, "color": "#2d3748"}
        tooltip = f"Nodo intermedio\nProbabilidad: {node['probability']}%\nEV: {ev:.2f}"
    
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
        # Root -> alternatives is decision structure, not probabilistic
        show_label = depth != 0
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
        height=450 + len(nodes) * 20,
        width=950,
        physics=False,
        groups={},
        interaction={"hover": True},
        layout={
            "hierarchical": {
                "enabled": True,
                "levelSeparation": 120,
                "nodeSpacing": 180,
                "treeSpacing": 200,
                "sortMethod": "directed",
            }
        },
    )
    
    selected = agraph(
        nodes=nodes,
        edges=edges,
        config=config,
    )
    
    return selected


# ── Node action panel ─────────────────────────────────────────────

def _render_action_panel(tree, selected_id):
    """Show edit/action controls for the selected node."""
    node, parent, depth = _find_node(tree, selected_id)
    if not node:
        return
    
    is_root = depth == 0
    is_alternative = node.get("node_type") == "alternative"
    is_leaf = len(node.get("children", [])) == 0
    children = node.get("children", [])
    
    st.markdown(f"**Nodo seleccionado:** {node['label']}")
    
    if is_root:
        st.caption("Este es el nodo raíz de decisión. Las alternativas del nivel 1 se sincronizan automáticamente desde la pestaña Alternativas.")
    elif is_alternative:
        if is_leaf and depth < MAX_TREE_DEPTH:
            if st.button("🔀 Bifurcar", key=f"iact_bif_{selected_id}"):
                node["children"] = [
                    _new_node("Mejor sub-escenario", 50, min(node["score"] + 2, 10)),
                    _new_node("Peor sub-escenario", 50, max(node["score"] - 2, 0)),
                ]
                st.rerun()
        else:
            st.caption("Esta alternativa ya está bifurcada. Edita o añade sub-ramas en sus nodos hijos.")
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
                    if parent is not None:
                        _rebalance_sibling_probabilities(parent, selected_id, new_prob)
                    else:
                        node["probability"] = int(new_prob)
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
            if is_leaf and depth < MAX_TREE_DEPTH:
                if st.button("🔀 Bifurcar", key=f"iact_bif_{selected_id}"):
                    node["children"] = [
                        _new_node("Mejor sub-escenario", 50, min(node["score"] + 2, 10)),
                        _new_node("Peor sub-escenario", 50, max(node["score"] - 2, 0)),
                    ]
                    st.rerun()
        
        with btn_cols[1]:
            # Add sibling branch (to parent)
            if not is_root and len(children) < MAX_NODE_BRANCHES and not is_leaf and depth < MAX_TREE_DEPTH:
                if st.button("➕ Sub-rama", key=f"iact_addsub_{selected_id}"):
                    _redistribute_and_add(node, "Sub-escenario", 5)
                    st.rerun()
        
        with btn_cols[2]:
            # Delete this node
            if parent and len(parent.get("children", [])) > 1 and not is_alternative:
                if st.button("🗑️ Eliminar", key=f"iact_del_{selected_id}"):
                    parent["children"] = [c for c in parent["children"] if c["id"] != selected_id]
                    if "_iact_selected_global" in st.session_state:
                        del st.session_state["_iact_selected_global"]
                    st.rerun()


# ── Main render function ───────────────────────────────────────────

def render_interactive_scenarios_tab():
    """Render unified Escenarios tab with tree-based input and outputs."""
    st.markdown("### 🔮 Planificación de Escenarios", unsafe_allow_html=True)
    st.caption("Construye escenarios con árboles de decisión. Haz clic en un nodo para seleccionarlo y editarlo.")
    
    all_alts = [a for a in st.session_state.alts if a["text"].strip()]
    if not all_alts:
        st.info("🎮 Los escenarios interactivos te permiten construir un árbol de decisión haciendo clic en los nodos. Primero define tus **Alternativas**.")
        return
    
    disqualified_alts = get_disqualified_alternatives()
    alts = [a for a in all_alts if a["id"] not in disqualified_alts]
    
    if disqualified_alts and len(alts) == 0:
        st.error("⚠️ Todas las alternativas están descalificadas por No Negociables.")
        return
    
    decision_label = st.session_state.get("objetivo", "Decisión").strip() or "Decisión"
    if "advanced_scenarios_decision_tree" not in st.session_state:
        st.session_state.advanced_scenarios_decision_tree = _new_decision_tree(decision_label[:50])

    decision_tree = st.session_state.advanced_scenarios_decision_tree
    decision_tree["label"] = decision_label[:50]
    decision_tree["node_type"] = "root"
    decision_tree["alt_id"] = None
    decision_tree["probability"] = 100

    mcda_by_name = _build_mcda_score_lookup(alts)
    _sync_root_alternatives(decision_tree, alts, mcda_by_name)

    selected = _render_agraph_tree(decision_tree, key_suffix="global", is_global=True)
    if selected:
        st.session_state["_iact_selected_global"] = selected

    current_selected = st.session_state.get("_iact_selected_global")
    if current_selected:
        selected_node, _, _ = _find_node(decision_tree, current_selected)
        if not selected_node:
            st.session_state.pop("_iact_selected_global", None)
            current_selected = None

    issues = _validate_probabilities(decision_tree)
    if issues:
        for issue in issues:
            st.warning(f"⚠️ {issue}")

    if current_selected:
        st.markdown("---")
        _render_action_panel(decision_tree, current_selected)
    else:
        st.info("👆 Haz clic en un nodo del árbol para editarlo.")

    projected_trees = _project_unified_tree_to_per_alt(decision_tree)
    st.session_state["advanced_scenarios"] = projected_trees

    allowed_alt_ids = {a["id"] for a in alts}
    st.session_state["scenarios"] = {
        alt_id: scenario
        for alt_id, scenario in st.session_state.get("scenarios", {}).items()
        if alt_id in allowed_alt_ids
    }

    ev_results = []
    for alt in alts:
        alt_id, alt_name = alt["id"], alt["text"].strip()
        tree = projected_trees.get(alt_id)
        if tree:
            _sync_tree_to_flat(alt_id, alt_name, tree)
            ev_results.append({"alt_name": alt_name, "alt_id": alt_id, "ev": _calculate_ev(tree)})
    
    # ── Smooth mixture distribution (PERT-equivalent) ─────────────
    _render_mixture_distribution(alts)

    # ── Decision Matrix (MCDA × EV) ───────────────────────────────
    _render_decision_matrix(ev_results, alts)


# ── Decision Matrix section ───────────────────────────────────────

def _render_decision_matrix(ev_results, alts):
    """Render Decision Matrix: bubble chart + adjustable weight slider + ranking table."""
    
    # Need MCDA scores
    mcda_ranking = []
    if "mcda_scores" in st.session_state and st.session_state.mcda_scores:
        if "mcda_scores_df" in st.session_state and "mcda_criteria" in st.session_state:
            scores_df = st.session_state.mcda_scores_df
            _, mcda_ranking_all = mcda_totals_and_ranking(scores_df.copy(), st.session_state.mcda_criteria)
            qualified_names = {a["text"].strip() for a in alts}
            mcda_ranking = [item for item in mcda_ranking_all if item["alternativa"] in qualified_names]
    
    if not mcda_ranking:
        st.markdown("---")
        st.info("💡 Completa la **Evaluación** para ver la Matriz de Decisión combinada (MCDA + Escenarios).")
        return
    
    st.markdown("---")
    st.markdown("### 🎯 Matriz de Decisión")

    mcda_weight_pct = int(st.session_state.get("composite_weight_slider", COMPOSITE_DEFAULT_MCDA_WEIGHT_PCT))
    w_mcda = mcda_weight_pct / 100.0
    w_ev = 1.0 - w_mcda
    
    # Build combined data
    combined_data = []
    for row in ev_results:
        alt_name = row["alt_name"]
        ev = row["ev"]
        ev_scaled = ev / 2.0  # Scale 0-10 → 0-5 to match MCDA range
        
        # Get tree for uncertainty
        alt_id = row["alt_id"]
        tree = st.session_state.advanced_scenarios.get(alt_id)
        leaves = _collect_leaves(tree) if tree else []
        scores = [l["score"] for l in leaves] if leaves else [0]
        uncertainty = max(scores) - min(scores)
        
        mcda_score = next((item["score"] for item in mcda_ranking if item["alternativa"] == alt_name), None)
        
        if mcda_score is not None:
            composite = w_mcda * mcda_score + w_ev * ev_scaled
            combined_data.append({
                "name": alt_name,
                "alt_id": alt_id,
                "mcda": mcda_score,
                "ev": ev,
                "ev_scaled": ev_scaled,
                "uncertainty": uncertainty,
                "composite": composite
            })
    
    if not combined_data:
        return
    
    # Bubble chart
    fig = go.Figure()
    
    max_composite = max(d["composite"] for d in combined_data)
    min_composite = min(d["composite"] for d in combined_data)
    
    for item in combined_data:
        bubble_size = 20 + item["uncertainty"] * 16
        max_uncertainty = 10
        opacity = 0.95 - (item["uncertainty"] / max_uncertainty) * 0.85
        
        fig.add_trace(go.Scatter(
            x=[item["mcda"]],
            y=[item["ev_scaled"]],
            mode="markers",
            marker=dict(
                size=bubble_size,
                color=item["composite"],
                colorscale="Viridis",
                cmin=min_composite,
                cmax=max_composite,
                opacity=opacity,
                line=dict(width=2, color="white")
            ),
            name=item["name"],
            hovertemplate=(
                f"<b>{item['name']}</b><br>"
                f"MCDA: {item['mcda']:.2f}<br>"
                f"EV: {item['ev']:.2f} (escala 0-10)<br>"
                f"Incertidumbre: {item['uncertainty']:.0f}<br>"
                f"Compuesto: {item['composite']:.2f}"
                "<extra></extra>"
            )
        ))
    
    fig.add_hline(y=2.5, line_dash="dash", line_color="#ccc", opacity=0.5)
    fig.add_vline(x=2.5, line_dash="dash", line_color="#ccc", opacity=0.5)
    
    fig.add_annotation(x=1.25, y=4.5, text="Alto potencial", showarrow=False, font=dict(size=10, color="#888"))
    fig.add_annotation(x=3.75, y=4.5, text="✓ Óptimo", showarrow=False, font=dict(size=11, color="#2e7d32", weight="bold"))
    fig.add_annotation(x=1.25, y=0.5, text="Evitar", showarrow=False, font=dict(size=10, color="#888"))
    fig.add_annotation(x=3.75, y=0.5, text="Seguro limitado", showarrow=False, font=dict(size=10, color="#888"))
    
    fig.update_layout(
        height=400,
        margin=dict(l=60, r=20, t=40, b=60),
        showlegend=True,
        legend=dict(title="Alternativas", x=1.02, y=1.0, xanchor="left", yanchor="top",
                    bgcolor="rgba(255,255,255,0.85)", bordercolor="rgba(0,0,0,0.15)", borderwidth=1),
        xaxis=dict(title="Puntuación MCDA (criterios)", range=[0, 5.2], showgrid=False, dtick=1),
        yaxis=dict(title="Valor Esperado (escenarios)", range=[0, 5.2], showgrid=False, dtick=1),
        plot_bgcolor="white"
    )
    
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key="interactive_decision_matrix")
    st.caption("📐 **Tamaño de burbuja** = incertidumbre (rango entre peor y mejor hoja). Burbujas más grandes indican mayor variabilidad.")
    
    # Composite weight control (compact, right before ranking impact)
    st.markdown("")
    slider_left, slider_center, slider_right = st.columns([1, 2, 1])
    with slider_center:
        mcda_weight_pct = st.slider(
            "Peso MCDA vs. Escenarios",
            min_value=0, max_value=100, value=mcda_weight_pct, step=5,
            format="%d%%",
            help="Ajusta el balance entre la puntuación MCDA (criterios) y el Valor Esperado (escenarios) para el cálculo compuesto.",
            key="composite_weight_slider"
        )
        st.caption(f"MCDA: **{mcda_weight_pct}%** | Escenarios (EV): **{100 - mcda_weight_pct}%**")

    # Composite ranking table
    st.markdown("")
    st.markdown("**Ranking Compuesto**")
    
    combined_sorted = sorted(combined_data, key=lambda x: x["composite"], reverse=True)
    
    ranking_df = pd.DataFrame([{
        "Alternativa": d["name"],
        "MCDA": d["mcda"],
        f"EV (0-5)": d["ev_scaled"],
        "Incertidumbre": d["uncertainty"],
        "Compuesto": d["composite"]
    } for d in combined_sorted])
    
    st.dataframe(
        ranking_df.style.format({
            "MCDA": "{:.2f}",
            "EV (0-5)": "{:.2f}",
            "Incertidumbre": "{:.0f}",
            "Compuesto": "{:.2f}"
        }),
        width="stretch"
    )
    
    winner = combined_sorted[0]
    st.success(f"🏆 **Recomendación**: {winner['name']} (Compuesto: {winner['composite']:.2f})")
    st.caption(f"Compuesto = {mcda_weight_pct}% MCDA + {100-mcda_weight_pct}% EV. Escala 0–5.")


# ── Smooth mixture distribution ───────────────────────────────────

def _render_mixture_distribution(alts):
    """Render smooth, deterministic mixture density using all tree leaves."""

    mcda_by_name = _build_mcda_score_lookup(alts)

    trees_data = []
    for alt in alts:
        alt_id = alt["id"]
        alt_name = alt["text"].strip()
        tree = st.session_state.advanced_scenarios.get(alt_id)
        if tree:
            leaves = _collect_leaves(tree)
            if leaves:
                trees_data.append({
                    "name": alt_name,
                    "leaves": leaves,
                    "ev": _calculate_ev(tree),
                    "mcda": mcda_by_name.get(alt_name),
                })

    if not trees_data:
        return

    st.markdown("---")
    st.markdown("### 📈 Distribuciones de probabilidad")
    st.caption("Distribuciones ponderadas por probabilidad efectiva de cada hoja")

    x = np.linspace(0.0, 10.0, 400)
    fig = go.Figure()

    for td in trees_data:
        leaves = td["leaves"]
        mcda = td.get("mcda")
        shift = 0.0
        if mcda is not None:
            shift = (float(mcda) - 2.5) * 0.35
        density = np.zeros_like(x)
        for leaf in leaves:
            score = float(leaf["score"]) + shift
            weight = max(0.0, float(leaf["path_prob"]))
            # Smooth deterministic kernel around each leaf score
            sigma = 0.35 + 0.9 * (1.0 - min(weight, 1.0))
            gaussian = np.exp(-0.5 * ((x - score) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))
            density += weight * gaussian

        # NumPy 2 removed np.trapz in favor of np.trapezoid
        area = np.trapezoid(density, x) if hasattr(np, "trapezoid") else np.trapz(density, x)
        if area > 0:
            density = density / area

        fig.add_trace(go.Scatter(
            x=x,
            y=density,
            mode="lines",
            fill="tozeroy",
            name=td["name"],
            line=dict(width=2),
            hovertemplate=(
                f"<b>{td['name']}</b><br>"
                "Puntuación: %{x:.2f}<br>"
                "Densidad relativa: %{y:.3f}<extra></extra>"
            )
        ))

        # EV marker
        ev_shifted = td["ev"] + shift
        ev_y = np.interp(ev_shifted, x, density)
        fig.add_trace(go.Scatter(
            x=[ev_shifted],
            y=[ev_y],
            mode="markers+text",
            marker=dict(size=11, color=COLOR_PRIMARY, symbol="diamond", line=dict(width=1, color="white")),
            text=[f"EV {td['ev']:.1f}"],
            textposition="top center",
            textfont=dict(size=10, color=COLOR_PRIMARY),
            hovertemplate=(
                f"<b>{td['name']}</b><br>"
                f"EV: {td['ev']:.2f}<br>"
                f"Offset MCDA: {shift:+.2f}<extra></extra>"
            ),
            showlegend=False,
        ))

    fig.update_layout(
        height=380,
        margin=dict(l=30, r=20, t=15, b=40),
        xaxis=dict(title="Puntuación (0-10)", range=[0, 10], dtick=1, showgrid=False),
        yaxis=dict(
            title="Densidad relativa",
            showgrid=True,
            gridcolor="rgba(100, 116, 139, 0.12)",
            gridwidth=0.6,
        ),
        plot_bgcolor="white",
    )

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key="mixture_distribution_chart")
    st.caption("💎 Cada diamante marca el EV. La curva integra todas las hojas del árbol y sus probabilidades efectivas.")

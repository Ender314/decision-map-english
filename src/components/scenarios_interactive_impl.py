# -*- coding: utf-8 -*-
"""
Interactive Scenarios tab - unified decision tree with clickable nodes.
Uses streamlit-agraph (vis.js) for interactive tree visualization.

Canonical runtime state:
- st.session_state["scenarios_decision_tree"] (single editable source of truth)
- st.session_state["scenarios_tree_projection"] (derived per-alternative bridge)
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
ALT_CHART_PALETTE = [
    "#2563eb", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#06b6d4", "#84cc16", "#f97316",
]
STATE_SCENARIOS_TREE = "scenarios_decision_tree"
STATE_SCENARIOS_PROJECTION = "scenarios_tree_projection"


def _build_alternative_color_map(alts):
    """Return a stable color per alternative for cross-chart consistency."""
    alt_names = [a.get("text", "").strip() for a in alts if a.get("text", "").strip()]
    return {
        name: ALT_CHART_PALETTE[idx % len(ALT_CHART_PALETTE)]
        for idx, name in enumerate(alt_names)
    }


def _bootstrap_tree_from_flat_scenarios(decision_label, alts):
    """Create a unified decision tree from flat scenarios bridge data."""
    root = _new_decision_tree(decision_label[:50])
    flat_scenarios = st.session_state.get("scenarios", {})

    for alt in alts:
        alt_id = alt.get("id")
        alt_name = (alt.get("text") or "").strip()
        if not alt_id or not alt_name:
            continue

        scenario = flat_scenarios.get(alt_id, {}) if isinstance(flat_scenarios, dict) else {}
        p_best_pct = int(scenario.get("p_best_pct", 50)) if scenario else 50
        p_best_pct = max(0, min(100, p_best_pct))
        p_worst_pct = 100 - p_best_pct

        best_score = int(float(scenario.get("best_score", 7))) if scenario else 7
        worst_score = int(float(scenario.get("worst_score", 2))) if scenario else 2

        alt_node = _new_node(
            label=alt_name,
            probability=100,
            score=5,
            node_type="alternative",
            alt_id=alt_id,
        )
        alt_node["children"] = [
            _new_node(
                label=scenario.get("best_desc", "Mejor escenario") if scenario else "Mejor escenario",
                probability=p_best_pct,
                score=max(0, min(10, best_score)),
            ),
            _new_node(
                label=scenario.get("worst_desc", "Peor escenario") if scenario else "Peor escenario",
                probability=p_worst_pct,
                score=max(0, min(10, worst_score)),
            ),
        ]
        root["children"].append(alt_node)

    return root


def _ordered_alternative_names_by_mcda(alts):
    """Return alternative names ordered by MCDA score (ascending) for chart consistency."""
    mcda_by_name = _build_mcda_score_lookup(alts)
    fallback_order = [a.get("text", "").strip() for a in alts if a.get("text", "").strip()]
    if not mcda_by_name:
        return fallback_order

    return sorted(
        fallback_order,
        key=lambda name: mcda_by_name.get(name, -1.0),
    )


def _get_projected_scenarios_trees():
    """Return per-alternative projected trees from canonical key."""
    projected = st.session_state.get(STATE_SCENARIOS_PROJECTION, {})
    if isinstance(projected, dict) and projected:
        return projected
    return {}


# ── Tree data helpers ────

def _hex_to_rgba(hex_color, alpha):
    """Convert #RRGGBB into rgba(r,g,b,a) string."""
    if not isinstance(hex_color, str) or not hex_color.startswith("#") or len(hex_color) != 7:
        return f"rgba(37,99,235,{alpha})"
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"

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
    if not st.session_state.get("mcda_scores"):
        return {}

    scores_df = st.session_state.get("mcda_scores_df")
    criteria = st.session_state.get("mcda_criteria")
    if not isinstance(scores_df, pd.DataFrame) or scores_df.empty or not criteria:
        return {}

    _, ranking_all = mcda_totals_and_ranking(scores_df.copy(), criteria)
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


def _collapse_subtree_to_leaf(node):
    """Collapse a branched node into a leaf, keeping its expected-value signal."""
    collapsed_score = int(round(_calculate_ev(node)))
    node["score"] = max(0, min(10, collapsed_score))
    node["children"] = []


def _disable_visualizations_after_tree_change():
    """Disable heavy visualizations after tree edits for smoother interaction."""
    st.session_state["_iact_show_visualizations"] = False


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
            issues.append(f"{path or 'Root'}: probabilities add up to {total}% (must add up to 100%)")
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
        tooltip = "Decision\nDecision root node"
    elif is_alternative:
        color = {"background": "#edf2f7", "border": "#a0aec0"}
        shape = "box"
        size_val = 13
        mcda_hint = node.get("mcda_hint")
        label = node["label"]
        font_cfg = {"size": 11, "color": "#2d3748"}
        mcda_text = f"{mcda_hint:.2f}" if mcda_hint is not None else "N/A"
        tooltip = f"Alternative\nMCDA: {mcda_text}\nEV: {ev:.2f}"
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
        tooltip = f"Scenario\nProbability: {node['probability']}%\nScore: {score}/10\nEV: {ev:.2f}"
    else:
        color = COLOR_NEUTRAL
        shape = "dot"
        size_val = 12
        label = node["label"]
        font_cfg = {"size": 11, "color": "#2d3748"}
        tooltip = f"Intermediate node\nProbability: {node['probability']}%\nEV: {ev:.2f}"
    
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


def _render_agraph_tree(tree, is_global=False, render_nonce=0):
    """Render an interactive agraph tree and return the selected node ID."""
    nodes = []
    edges = []
    _tree_to_agraph(tree, nodes, edges, is_global=is_global)

    # Tiny nonce-based variation to force a component refresh when requested
    # (streamlit-agraph doesn't expose a `key` argument on agraph()).
    base_height = 450 + len(nodes) * 20 + (1 if int(render_nonce) % 2 else 0)

    config = Config(
        directed=True,
        hierarchical=True,
        height=base_height,
        width=950,
        physics=False,
        groups={},
        interaction={"hover": True, "dragView": True, "zoomView": True},
        layout={
            "hierarchical": {
                "enabled": True,
                "levelSeparation": 120,
                "nodeSpacing": 180,
                "treeSpacing": 200,
                "direction": "UD",
                "sortMethod": "directed",
                "parentCentralization": True,
                "blockShifting": True,
                "edgeMinimization": True,
                "shakeTowards": "roots",
            }
        },
    )
    config.width = "100%"
    
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
    
    st.markdown(f"**Selected node:** {node['label']}")
    
    if is_root:
        st.caption("This is the decision root node. Level-1 alternatives are synced automatically from the Alternatives tab.")
    elif is_alternative:
        if is_leaf and depth < MAX_TREE_DEPTH:
            if st.button("🔀 Split", key=f"iact_bif_{selected_id}"):
                node["children"] = [
                    _new_node("Best sub-scenario", 50, min(node["score"] + 2, 10)),
                    _new_node("Worst sub-scenario", 50, max(node["score"] - 2, 0)),
                ]
                _disable_visualizations_after_tree_change()
                st.rerun()
        else:
            st.caption("This alternative is already split. Edit or add sub-branches in its child nodes.")
            alt_btn_col1, alt_btn_col2 = st.columns(2)
            with alt_btn_col1:
                if len(children) < MAX_NODE_BRANCHES and depth < MAX_TREE_DEPTH:
                    if st.button("➕ Sub-branch", key=f"iact_addsub_alt_{selected_id}"):
                        _redistribute_and_add(node, "Sub-scenario", 5)
                        _disable_visualizations_after_tree_change()
                        st.rerun()
            with alt_btn_col2:
                if st.button("↩️ Undo split", key=f"iact_unfork_alt_{selected_id}"):
                    _collapse_subtree_to_leaf(node)
                    _disable_visualizations_after_tree_change()
                    st.rerun()
    else:
        # Editable node (batched update to avoid rerun on each keystroke/slider step)
        with st.form(key=f"iact_edit_form_{selected_id}", clear_on_submit=False):
            c1, c2 = st.columns(2)
            with c1:
                new_label = st.text_input(
                    "Description", value=node["label"],
                    key=f"iact_lbl_{selected_id}",
                    placeholder="Describe this scenario..."
                )

            with c2:
                col_p, col_s = st.columns(2)
                with col_p:
                    new_prob = st.number_input(
                        "Probability %",
                        min_value=0, max_value=100, step=5,
                        value=int(node["probability"]),
                        key=f"iact_prob_{selected_id}"
                    )
                with col_s:
                    new_score = st.slider(
                        "Score (0-10)",
                        min_value=0, max_value=10, step=1,
                        value=int(node["score"]),
                        key=f"iact_score_{selected_id}"
                    )

            submit_col_left, submit_col_center, submit_col_right = st.columns([1, 1, 1])
            with submit_col_center:
                submitted = st.form_submit_button("💾 Apply changes", use_container_width=True)

        if submitted:
            changed = False
            if new_label != node["label"]:
                node["label"] = new_label
                changed = True

            if int(new_prob) != int(node["probability"]):
                if parent is not None:
                    _rebalance_sibling_probabilities(parent, selected_id, int(new_prob))
                else:
                    node["probability"] = int(new_prob)
                changed = True

            if int(new_score) != int(node["score"]):
                node["score"] = int(new_score)
                changed = True

            if changed:
                _disable_visualizations_after_tree_change()
                st.rerun()
        
        # Action buttons
        btn_cols = st.columns(4)
        
        with btn_cols[0]:
            # Bifurcate (add children to this leaf)
            if is_leaf and depth < MAX_TREE_DEPTH:
                if st.button("🔀 Split", key=f"iact_bif_{selected_id}"):
                    node["children"] = [
                        _new_node("Best sub-scenario", 50, min(node["score"] + 2, 10)),
                        _new_node("Worst sub-scenario", 50, max(node["score"] - 2, 0)),
                    ]
                    _disable_visualizations_after_tree_change()
                    st.rerun()
        
        with btn_cols[1]:
            # Add sibling branch (to parent)
            if not is_root and len(children) < MAX_NODE_BRANCHES and not is_leaf and depth < MAX_TREE_DEPTH:
                if st.button("➕ Sub-branch", key=f"iact_addsub_{selected_id}"):
                    _redistribute_and_add(node, "Sub-scenario", 5)
                    _disable_visualizations_after_tree_change()
                    st.rerun()
        
        with btn_cols[2]:
            # Collapse branch into a leaf using subtree EV
            if not is_root and not is_leaf:
                if st.button("↩️ Undo split", key=f"iact_unfork_{selected_id}"):
                    _collapse_subtree_to_leaf(node)
                    _disable_visualizations_after_tree_change()
                    st.rerun()

        with btn_cols[3]:
            # Delete this node
            if parent and len(parent.get("children", [])) > 1 and not is_alternative:
                if st.button("🗑️ Delete", key=f"iact_del_{selected_id}"):
                    parent["children"] = [c for c in parent["children"] if c["id"] != selected_id]
                    if "_iact_selected_global" in st.session_state:
                        del st.session_state["_iact_selected_global"]
                    _disable_visualizations_after_tree_change()
                    st.rerun()


# ── Main render function ───────────────────────────────────────────

def render_interactive_scenarios_tab():
    """Render unified Escenarios tab with tree-based input and outputs."""
    st.markdown("### 🔮 Scenario Planning", unsafe_allow_html=True)
    st.caption("Build scenarios using decision trees. Click a node to select and edit it.")
    
    all_alts = [a for a in st.session_state.alts if a["text"].strip()]
    if not all_alts:
        st.info("🎮 Interactive scenarios let you build a decision tree by clicking nodes. First define your **Alternatives**.")
        return
    
    disqualified_alts = get_disqualified_alternatives()
    alts = [a for a in all_alts if a["id"] not in disqualified_alts]
    
    if disqualified_alts and len(alts) == 0:
        st.error("⚠️ All alternatives are disqualified by Non-Negotiables.")
        return
    
    decision_label = st.session_state.get("objetivo", "Decision").strip() or "Decision"
    current_tree = st.session_state.get(STATE_SCENARIOS_TREE)
    if not isinstance(current_tree, dict) or not current_tree:
        if st.session_state.get("scenarios"):
            st.session_state[STATE_SCENARIOS_TREE] = _bootstrap_tree_from_flat_scenarios(decision_label, all_alts)
        else:
            st.session_state[STATE_SCENARIOS_TREE] = _new_decision_tree(decision_label[:50])

    decision_tree = st.session_state[STATE_SCENARIOS_TREE]
    decision_tree["label"] = decision_label[:50]
    decision_tree["node_type"] = "root"
    decision_tree["alt_id"] = None
    decision_tree["probability"] = 100

    mcda_by_name = _build_mcda_score_lookup(alts)
    _sync_root_alternatives(decision_tree, alts, mcda_by_name)

    tree_controls_col, _ = st.columns([1, 5])
    with tree_controls_col:
        recenter_requested = st.button(
            "🎯 Recenter tree",
            key="iact_center_tree_btn",
            help="Recenter the tree view if it moved off-screen",
        )

    if recenter_requested:
        st.session_state.pop("_iact_selected_global", None)
        st.session_state["_iact_tree_recenter_nonce"] = int(st.session_state.get("_iact_tree_recenter_nonce", 0)) + 1

    tree_recenter_nonce = int(st.session_state.get("_iact_tree_recenter_nonce", 0))

    selected = _render_agraph_tree(
        decision_tree,
        is_global=True,
        render_nonce=tree_recenter_nonce,
    )

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
        st.info("👆 Click a tree node to edit it.")

    projected_trees = _project_unified_tree_to_per_alt(decision_tree)
    st.session_state[STATE_SCENARIOS_PROJECTION] = projected_trees

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

    st.markdown("---")
    show_visualizations = st.toggle(
        "Show visualizations",
        value=False,
        key="_iact_show_visualizations",
        help="Enable all visualizations (Distributions, Decision Matrix, and MCDA × EV) when the tree is ready.",
    )

    if not show_visualizations:
        st.caption("💡 Turn on **Show visualizations** to render the charts once you finish editing the tree.")
        return

    # Render first right after tree definition controls
    _render_mixture_distribution(alts)

    # Keep remaining visualizations available under the same toggle
    _render_decision_matrix(ev_results, alts)


# ── Merged chart: MCDA × EV density ───────────────────────────────

def _render_mcda_ev_density_bridge(alts, embedded=False, chart_key="mcda_ev_density_bridge"):
    """Render per-alternative EV density (tree-derived) positioned on raw MCDA x-axis."""
    mcda_by_name = _build_mcda_score_lookup(alts)

    projected_trees = _get_projected_scenarios_trees()
    trees_data = []
    for alt in alts:
        alt_id = alt["id"]
        alt_name = alt["text"].strip()
        tree = projected_trees.get(alt_id)
        mcda = mcda_by_name.get(alt_name)
        if tree and mcda is not None:
            leaves = _collect_leaves(tree)
            if leaves:
                trees_data.append({
                    "name": alt_name,
                    "mcda": float(mcda),
                    "ev": float(_calculate_ev(tree)),
                    "leaves": leaves,
                })

    if not trees_data:
        return

    preferred_order = _ordered_alternative_names_by_mcda(alts)
    order_index = {name: idx for idx, name in enumerate(preferred_order)}
    trees_data = sorted(trees_data, key=lambda d: order_index.get(d["name"], 10_000))

    if not embedded:
        st.markdown("---")
        st.markdown("### 🧬 MCDA × EV (density by alternative)")
        st.caption("X-axis = MCDA (0-5). Y-axis = score of each leaf (0-10). Each circle represents a leaf; opacity follows its effective probability (`path_prob`). For branched alternatives, a subtle distribution outline and EV marker are shown.")
    
    color_map = _build_alternative_color_map(alts)

    fig = go.Figure()
    y_kernel_grid = np.linspace(0.0, 10.0, 220)

    for idx, td in enumerate(trees_data):
        color = color_map.get(td["name"], ALT_CHART_PALETTE[idx % len(ALT_CHART_PALETTE)])
        leaves = td["leaves"]
        if not leaves:
            continue

        x_vals = [td["mcda"]] * len(leaves)
        y_vals = [float(leaf["score"]) for leaf in leaves]
        path_probs = [max(0.0, min(1.0, float(leaf.get("path_prob", 0.0)))) for leaf in leaves]
        marker_opacity = [max(0.08, p) for p in path_probs]
        marker_sizes = [15 + (8 * p) for p in path_probs]
        customdata = [[leaf.get("label", ""), p * 100] for leaf, p in zip(leaves, path_probs)]

        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers",
            marker=dict(
                size=marker_sizes,
                color=color,
                opacity=marker_opacity,
                line=dict(width=1, color="white"),
            ),
            name=td["name"],
            hovertemplate=(
                f"<b>{td['name']}</b><br>"
                f"MCDA: {td['mcda']:.2f}<br>"
                "Leaf score: %{y:.2f}<br>"
                "Leaf: %{customdata[0]}<br>"
                "Effective probability: %{customdata[1]:.1f}%<extra></extra>"
            ),
            customdata=customdata,
            showlegend=True,
        ))

        # Branch-only subtle distribution outline + subtle EV marker
        if len(leaves) > 1:
            density = np.zeros_like(y_kernel_grid)
            for leaf in leaves:
                score = float(leaf["score"])
                weight = max(0.0, float(leaf.get("path_prob", 0.0)))
                sigma = 0.40 + 0.8 * (1.0 - min(weight, 1.0))
                z = (y_kernel_grid - score) / sigma
                gaussian = np.exp(-0.5 * (z ** 2)) / (sigma * np.sqrt(2 * np.pi))
                gaussian[np.abs(z) > 2.3] = 0.0
                density += weight * gaussian

            peak = float(np.max(density)) if len(density) else 0.0
            if peak > 0:
                density_scaled = (density / peak) * 0.12
                support_mask = density_scaled > 1e-4
                if np.count_nonzero(support_mask) >= 3:
                    y_support = y_kernel_grid[support_mask]
                    width_support = density_scaled[support_mask]
                    x_center = td["mcda"]

                    fig.add_trace(go.Scatter(
                        x=x_center + width_support,
                        y=y_support,
                        mode="lines",
                        line=dict(color=color, width=1.0),
                        opacity=0.15,
                        hoverinfo="skip",
                        showlegend=False,
                    ))
                    fig.add_trace(go.Scatter(
                        x=x_center - width_support,
                        y=y_support,
                        mode="lines",
                        line=dict(color=color, width=1.0),
                        opacity=0.15,
                        hoverinfo="skip",
                        showlegend=False,
                    ))

            fig.add_trace(go.Scatter(
                x=[td["mcda"]],
                y=[td["ev"]],
                mode="markers",
                marker=dict(size=8, symbol="diamond-open", color=color, line=dict(width=1.2, color=color)),
                opacity=0.25,
                hovertemplate=(
                    f"<b>{td['name']}</b><br>"
                    f"MCDA: {td['mcda']:.2f}<br>"
                    f"EV: {td['ev']:.2f}<extra></extra>"
                ),
                showlegend=False,
            ))

    # Matrix-like quadrant framing (x split at 2.5 on MCDA scale, y split at 5 on EV 0-10 scale)
    fig.add_shape(type="rect", x0=0, y0=5, x1=2.5, y1=10, fillcolor="rgba(59, 130, 246, 0.05)", line=dict(width=0), layer="below")
    fig.add_shape(type="rect", x0=2.5, y0=5, x1=5, y1=10, fillcolor="rgba(56, 161, 105, 0.06)", line=dict(width=0), layer="below")
    fig.add_shape(type="rect", x0=0, y0=0, x1=2.5, y1=5, fillcolor="rgba(229, 62, 62, 0.05)", line=dict(width=0), layer="below")
    fig.add_shape(type="rect", x0=2.5, y0=0, x1=5, y1=5, fillcolor="rgba(246, 173, 85, 0.05)", line=dict(width=0), layer="below")

    fig.add_vline(x=2.5, line_dash="dash", line_color="#cbd5e0", opacity=0.8)
    fig.add_hline(y=5, line_dash="dash", line_color="#cbd5e0", opacity=0.8)

    fig.add_annotation(x=1.25, y=9.0, text="Explore", showarrow=False, font=dict(size=10, color="#718096"))
    fig.add_annotation(x=3.75, y=9.0, text="Prioritize", showarrow=False, font=dict(size=11, color="#2e7d32", weight="bold"))
    fig.add_annotation(x=1.25, y=1.0, text="Discard", showarrow=False, font=dict(size=10, color="#718096"))
    fig.add_annotation(x=3.75, y=1.0, text="Review assumptions", showarrow=False, font=dict(size=10, color="#718096"))

    fig.update_layout(
        height=400,
        margin=dict(l=60, r=20, t=40, b=60),
        xaxis=dict(title="MCDA score (0-5)", range=[0, 5.1], dtick=0.5, showgrid=False),
        yaxis=dict(
            title="Expected Value (EV, 0-10)",
            range=[0, 10],
            dtick=2,
            showgrid=False,
        ),
        legend=dict(
            title="Alternatives",
            x=1.02,
            y=1.0,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.15)",
            borderwidth=1,
        ),
        plot_bgcolor="white",
    )

    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key=chart_key)
    if not embedded:
        st.caption("Pilot comparison: the two current views remain below so you can validate readability and usefulness.")


# ── Decision Matrix section ───────────────────────────────────────

def _render_decision_matrix(ev_results, alts):
    """Render Decision Matrix: bubble chart + adjustable weight slider + ranking table."""
    
    # Need MCDA scores
    mcda_ranking = []
    if "mcda_scores" in st.session_state and st.session_state.mcda_scores:
        scores_df = st.session_state.get("mcda_scores_df")
        criteria = st.session_state.get("mcda_criteria")
        if isinstance(scores_df, pd.DataFrame) and not scores_df.empty and criteria:
            _, mcda_ranking_all = mcda_totals_and_ranking(scores_df.copy(), criteria)
            qualified_names = {a["text"].strip() for a in alts}
            mcda_ranking = [item for item in mcda_ranking_all if item["alternativa"] in qualified_names]
    
    if not mcda_ranking:
        st.markdown("---")
        st.info("💡 Complete the **Evaluation** tab to view the combined Decision Matrix (MCDA + Scenarios).")
        return
    
    st.markdown("---")
    st.markdown("### 🎯 Decision Matrix")

    mcda_weight_pct = int(st.session_state.get("composite_weight_slider", COMPOSITE_DEFAULT_MCDA_WEIGHT_PCT))
    w_mcda = mcda_weight_pct / 100.0
    w_ev = 1.0 - w_mcda
    
    projected_trees = _get_projected_scenarios_trees()

    # Build combined data
    combined_data = []
    for row in ev_results:
        alt_name = row["alt_name"]
        ev = row["ev"]
        ev_scaled = ev / 2.0  # Scale 0-10 → 0-5 to match MCDA range
        
        # Get tree for uncertainty
        alt_id = row["alt_id"]
        tree = projected_trees.get(alt_id)
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
    
    color_map = _build_alternative_color_map(alts)
    
    preferred_order = _ordered_alternative_names_by_mcda(alts)
    order_index = {name: idx for idx, name in enumerate(preferred_order)}
    combined_for_chart = sorted(combined_data, key=lambda d: order_index.get(d["name"], 10_000))

    for item in combined_for_chart:
        bubble_size = 20 + item["uncertainty"] * 16
        max_uncertainty = 10
        opacity = 0.95 - (item["uncertainty"] / max_uncertainty) * 0.85
        
        fig.add_trace(go.Scatter(
            x=[item["mcda"]],
            y=[item["ev_scaled"]],
            mode="markers",
            marker=dict(
                size=bubble_size,
                color=color_map.get(item["name"], COLOR_PRIMARY),
                opacity=opacity,
                line=dict(width=2, color="white")
            ),
            name=item["name"],
            hovertemplate=(
                f"<b>{item['name']}</b><br>"
                f"MCDA: {item['mcda']:.2f}<br>"
                f"EV: {item['ev']:.2f} (0-10 scale)<br>"
                f"Uncertainty: {item['uncertainty']:.0f}<br>"
                f"Composite: {item['composite']:.2f}"
                "<extra></extra>"
            )
        ))
    
    fig.add_hline(y=2.5, line_dash="dash", line_color="#ccc", opacity=0.5)
    fig.add_vline(x=2.5, line_dash="dash", line_color="#ccc", opacity=0.5)
    
    fig.add_annotation(x=1.25, y=4.5, text="High potential", showarrow=False, font=dict(size=10, color="#888"))
    fig.add_annotation(x=3.75, y=4.5, text="✓ Optimal", showarrow=False, font=dict(size=11, color="#2e7d32", weight="bold"))
    fig.add_annotation(x=1.25, y=0.5, text="Avoid", showarrow=False, font=dict(size=10, color="#888"))
    fig.add_annotation(x=3.75, y=0.5, text="Limited upside", showarrow=False, font=dict(size=10, color="#888"))
    
    fig.update_layout(
        height=400,
        margin=dict(l=60, r=20, t=40, b=60),
        showlegend=True,
        legend=dict(title="Alternatives", x=1.02, y=1.0, xanchor="left", yanchor="top",
                    bgcolor="rgba(255,255,255,0.85)", bordercolor="rgba(0,0,0,0.15)", borderwidth=1),
        xaxis=dict(title="MCDA score (criteria)", range=[0, 5.2], showgrid=False, dtick=1),
        yaxis=dict(title="Expected Value (scenarios)", range=[0, 5.2], showgrid=False, dtick=1),
        plot_bgcolor="white"
    )
    
    chart_tab, advanced_tab = st.tabs(["Basic view", "🔍 Detail"])

    with chart_tab:
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key="interactive_decision_matrix")
        st.caption("📐 **Bubble size** = uncertainty (range between the worst and best leaf). Larger bubbles indicate greater variability.")

    with advanced_tab:
        _render_mcda_ev_density_bridge(alts, embedded=True, chart_key="mcda_ev_density_bridge_tab")
    
    # Composite weight control (compact, right before ranking impact)
    st.markdown("")
    slider_left, slider_center, slider_right = st.columns([1, 2, 1])
    with slider_center:
        mcda_weight_pct = st.slider(
            "MCDA vs. Scenarios weight",
            min_value=0, max_value=100, value=mcda_weight_pct, step=5,
            format="%d%%",
            help="Adjust the balance between the MCDA score (criteria) and Expected Value (scenarios) for the composite calculation.",
            key="composite_weight_slider"
        )
        st.caption(f"MCDA: **{mcda_weight_pct}%** | Scenarios (EV): **{100 - mcda_weight_pct}%**")

    # Composite ranking table
    st.markdown("")
    st.markdown("**Composite Ranking**")
    
    combined_sorted = sorted(combined_data, key=lambda x: x["composite"], reverse=True)
    
    ranking_df = pd.DataFrame([{
        "Alternative": d["name"],
        "MCDA": d["mcda"],
        f"EV (0-5)": d["ev_scaled"],
        "Uncertainty": d["uncertainty"],
        "Composite": d["composite"]
    } for d in combined_sorted])
    
    st.dataframe(
        ranking_df.style.format({
            "MCDA": "{:.2f}",
            "EV (0-5)": "{:.2f}",
            "Uncertainty": "{:.0f}",
            "Composite": "{:.2f}"
        }),
        width="stretch"
    )
    
    winner = combined_sorted[0]
    st.success(f"🏆 **Recommendation**: {winner['name']} (Composite: {winner['composite']:.2f})")
    st.caption(f"Composite = {mcda_weight_pct}% MCDA + {100-mcda_weight_pct}% EV. Scale 0–5.")


# ── Smooth mixture distribution ───────────────────────────────────

def _render_mixture_distribution(alts):
    """Render smooth, deterministic mixture density using all tree leaves."""

    projected_trees = _get_projected_scenarios_trees()
    preferred_order = _ordered_alternative_names_by_mcda(alts)
    order_index = {name: idx for idx, name in enumerate(preferred_order)}
    color_map = _build_alternative_color_map(alts)

    trees_data = []
    for alt in alts:
        alt_id = alt["id"]
        alt_name = alt["text"].strip()
        tree = projected_trees.get(alt_id)
        if tree:
            leaves = _collect_leaves(tree)
            if leaves:
                trees_data.append({
                    "alt_id": alt_id,
                    "name": alt_name,
                    "leaves": leaves,
                    "ev": _calculate_ev(tree),
                })

    if not trees_data:
        return

    trees_data = sorted(trees_data, key=lambda d: order_index.get(d["name"], 10_000))

    st.markdown("---")
    st.markdown("### 📈 Probability distributions")
    st.caption("Consolidated view: a single X-axis (0-10) and vertical bands per alternative.")

    x = np.linspace(0.0, 10.0, 400)

    fig = go.Figure()
    row_count = len(trees_data)
    alt_tickvals = []
    alt_ticktext = []
    band_half_height = 0.38

    for idx, td in enumerate(trees_data):
        # First alternative at top, last at bottom
        baseline = row_count - idx
        color = color_map.get(td["name"], ALT_CHART_PALETTE[idx % len(ALT_CHART_PALETTE)])
        leaves = td["leaves"]
        density = np.zeros_like(x)
        for leaf in leaves:
            score = float(leaf["score"])
            weight = max(0.0, float(leaf.get("path_prob", 0.0)))
            # Smooth deterministic kernel around each leaf score
            sigma = 0.35 + 0.9 * (1.0 - min(weight, 1.0))
            gaussian = np.exp(-0.5 * ((x - score) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))
            density += weight * gaussian

        # NumPy 2 removed np.trapz in favor of np.trapezoid
        area = np.trapezoid(density, x) if hasattr(np, "trapezoid") else np.trapz(density, x)
        if area > 0:
            density = density / area

        peak = float(np.max(density)) if len(density) else 0.0
        if peak > 0:
            density_scaled = (density / peak) * band_half_height
        else:
            density_scaled = np.zeros_like(density)

        ev = float(td["ev"])
        ev_y = baseline + np.interp(ev, x, density_scaled)

        y_upper = baseline + density_scaled

        # Baseline (used as fill origin)
        fig.add_trace(go.Scatter(
            x=x,
            y=np.full_like(x, baseline, dtype=float),
            mode="lines",
            line=dict(width=0, color=color),
            hoverinfo="skip",
            showlegend=False,
        ))

        # Upper boundary + fill to create one-sided density area per alternative
        fig.add_trace(go.Scatter(
            x=x,
            y=y_upper,
            mode="lines",
            fill="tonexty",
            line=dict(width=1.6, color=color),
            fillcolor=_hex_to_rgba(color, 0.18),
            hovertemplate=(
                f"<b>{td['name']}</b><br>"
                "Score: %{x:.2f}<br>"
                "Density (scaled): %{customdata:.3f}<extra></extra>"
            ),
            customdata=density_scaled,
            showlegend=False,
        ))

        # EV marker
        fig.add_trace(go.Scatter(
            x=[ev],
            y=[ev_y],
            mode="markers+text",
            marker=dict(size=11, color=COLOR_PRIMARY, symbol="diamond", line=dict(width=1, color="white")),
            text=[f"EV {ev:.1f}"],
            textposition="top center",
            textfont=dict(size=10, color=COLOR_PRIMARY),
            hovertemplate=(
                f"<b>{td['name']}</b><br>"
                f"EV: {ev:.2f}<extra></extra>"
            ),
            showlegend=False,
        ))

        alt_tickvals.append(baseline)
        alt_ticktext.append(td["name"])

        # Separator between alternatives
        if baseline > 1:
            fig.add_hline(
                y=baseline - 0.5,
                line_width=0.8,
                line_color="rgba(148,163,184,0.22)",
            )

    fig.update_layout(
        height=max(280, 120 * row_count),
        margin=dict(l=30, r=20, t=40, b=30),
        plot_bgcolor="white",
        showlegend=False,
        xaxis=dict(
            title="Score (0-10)",
            range=[0, 10],
            dtick=1,
            showgrid=False,
        ),
        yaxis=dict(
            title="Alternative",
            tickmode="array",
            tickvals=alt_tickvals,
            ticktext=alt_ticktext,
            range=[0.5, row_count + 0.7],
            showgrid=False,
            zeroline=False,
        ),
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config={"displayModeBar": False},
        key="mixture_distribution_chart_multi_axis",
    )

    st.caption("💎 Each row shows one alternative's distribution and EV on the 0–10 scale.")

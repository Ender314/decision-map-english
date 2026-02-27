# Migration Plan: streamlit-agraph → streamlit-flow-component

> Decision tree interactive visualization replacement

---

## 1. Problem Statement

`streamlit-agraph` (v0.0.45) wraps the vis.js library and has been **unmaintained since January 2023** (3+ years). Key issues:

- **No `key` parameter** — forces a nonce-based height hack to trigger re-renders (see `_render_agraph_tree`, line 467 of `scenarios_interactive_impl.py`).
- **No state synchronization** — agraph returns only a selected node ID string; all state management is manual.
- **No context menus** — all editing happens through a separate Streamlit panel below the graph.
- **No edge interactivity** — edges cannot be clicked or highlighted.
- **Stale dependency** — vis.js bundled version is outdated; no security patches or compatibility updates.
- **Beta quality** — never reached v1.0; the 0.0.x versioning reflects its experimental status.

---

## 2. Alternatives Evaluated

| Library | Wraps | Last Release | Click-to-Select | Tree Layout | State Sync | Maintained |
|---------|-------|-------------|----------------|-------------|-----------|------------|
| **streamlit-agraph** (current) | vis.js | Jan 2023 | ✅ node only | ✅ hierarchical | ❌ manual | ❌ abandoned |
| **streamlit-flow-component** | React Flow (xyflow) | Feb 2025 (v1.6.1) | ✅ node + edge | ✅ ELK.js layouts | ✅ `StreamlitFlowState` | ✅ active |
| **st-link-analysis** | Cytoscape.js | 2024 | ✅ node actions | ⚠️ generic layouts | ❌ event-based | ⚠️ small community |
| **streamlit-arborist** | react-arborist | 2025 | ✅ tree select | ✅ file-tree style | ✅ | ⚠️ new, untested |
| **st.graphviz_chart** | Graphviz | built-in | ❌ no callbacks | ✅ dot/neato | ❌ static | ✅ Streamlit core |
| **Custom component (v2)** | any JS lib | N/A | ✅ full control | ✅ full control | ✅ bidirectional | ⚠️ self-maintained |

### Why streamlit-arborist was rejected
- Designed for file-explorer-style tree navigation (expand/collapse text rows), not graph visualization.
- Cannot display edge labels (probabilities), node shapes, or color-coded leaf scores.
- No edge rendering at all — it's a list-based tree, not a graph.

### Why st-link-analysis was rejected
- Designed for link/network analysis (social graphs, knowledge graphs).
- Layout algorithms (cose, circle, grid) are not optimized for hierarchical decision trees.
- Event model returns expand/remove actions, not simple click-to-select.
- Smaller community and less mature for our specific use case.

### Why a custom component was rejected
- High development and maintenance burden for a feature that already has a good off-the-shelf solution.
- Would require managing a JS build pipeline (React, npm) alongside the Python codebase.
- Risk of introducing bugs in the bidirectional communication layer.

---

## 3. Recommendation: `streamlit-flow-component`

**React Flow** (xyflow) is one of the most widely used flow/graph libraries in the JS ecosystem (30k+ GitHub stars). `streamlit-flow-component` is a well-maintained Streamlit wrapper with:

### Feature Comparison: Current agraph vs. streamlit-flow

| Capability | agraph (current) | streamlit-flow (target) |
|-----------|------------------|------------------------|
| Node click → Python | ✅ returns node ID string | ✅ returns `{elementType, id}` dict |
| Edge click → Python | ❌ | ✅ `get_edge_on_click=True` |
| Hierarchical layout | ✅ vis.js hierarchical | ✅ ELK.js `direction='down'` |
| Layout spacing control | ✅ `levelSeparation`, `nodeSpacing` | ✅ `layout_vertical_spacing`, `layout_horizontal_spacing` |
| Node styling | ✅ color dict, shape, font | ✅ CSS `style` dict, `node_type` |
| Edge labels | ✅ label string | ✅ `label`, `label_style`, `label_bg_style` |
| Edge width/color | ✅ width, color | ✅ via `style` dict |
| Tooltips | ✅ `title` attribute | ⚠️ via custom CSS/hover (or markdown in node content) |
| Node shapes | ✅ box, diamond, dot, etc. | ⚠️ rectangular nodes only (styled via CSS border-radius, colors) |
| Proper `key` param | ❌ (nonce hack) | ✅ native `key` argument |
| State sync (Python ↔ JS) | ❌ | ✅ `StreamlitFlowState` |
| Context menus | ❌ | ✅ right-click edit/delete on nodes and edges |
| Minimap | ❌ | ✅ `show_minimap=True` |
| Zoom/pan controls | ✅ via config | ✅ `show_controls=True` |
| Markdown in nodes | ❌ | ✅ (v1.2.9+) |
| Edge arrows | ❌ | ✅ `markerEnd='arrow'` |
| Canvas fit-to-view | ❌ manual | ✅ `fit_view=True` |

### Key UX Improvements Unlocked

1. **Markdown-rich nodes** — Display node label, EV score, and probability directly inside the node with formatted text instead of plain labels.
2. **Context menu editing** — Right-click a node to edit/delete, reducing the need for the separate action panel.
3. **Edge interactivity** — Click edges to inspect or modify probability values.
4. **Directed edge arrows** — Visually clarify parent→child flow direction.
5. **Minimap** — Navigate large trees without losing context.
6. **Proper state sync** — Eliminate the nonce-based re-render hack; state changes from Python are automatically reflected.
7. **Fit-to-view** — Auto-zoom to show the entire tree on load.

### Known Limitations / Trade-offs

1. **No native node shapes** — React Flow uses rectangular nodes. Diamond/dot shapes from vis.js must be emulated with CSS (`border-radius`, rotated squares, etc.) or replaced with color + icon conventions.
2. **Tooltip approach differs** — vis.js `title` hover tooltips don't have a direct equivalent. Information should be embedded in node content (markdown) or handled via Streamlit panels on click.
3. **State must live in `st.session_state`** — `StreamlitFlowState` must be stored in session state to avoid infinite re-render loops. This is actually compatible with our architecture since we already manage all state there.

---

## 4. Current Code Surface to Modify

All agraph usage is **isolated to a single file**:

**`src/components/scenarios_interactive_impl.py`** — ~1,243 lines total

### Functions that directly use agraph:

| Function | Lines | What it does |
|----------|-------|-------------|
| `_tree_to_agraph()` | 382–456 | Recursively converts tree dict → agraph `Node` / `Edge` objects |
| `_render_agraph_tree()` | 459–500 | Renders the agraph component, returns selected node ID |

### Functions that consume agraph output:

| Function | Lines | What it does |
|----------|-------|-------------|
| `render_interactive_scenarios_tab()` | ~600–700 | Calls `_render_agraph_tree()`, uses returned `selected` ID to drive `_render_action_panel()` |
| `_render_action_panel()` | 505+ | Shows edit controls for the node identified by `selected_id` |

### Import to replace:

```python
# CURRENT (line 15)
from streamlit_agraph import agraph, Node, Edge, Config

# TARGET
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
```

### Dependency to update:

```
# requirements.txt — CURRENT (line 14)
streamlit-agraph>=0.0.45

# TARGET
streamlit-flow-component>=1.6.1
```

---

## 5. Step-by-Step Implementation Plan

### Phase 1: Foundation (non-breaking preparation)

**Step 1.1 — Install and validate streamlit-flow-component**
```bash
pip install streamlit-flow-component>=1.6.1
```
- Create a minimal test script outside the app to verify the library works with `direction='down'` and `get_node_on_click=True`.

**Step 1.2 — Define the node style mapping**

Create a helper function that maps our tree node types to streamlit-flow styles:

| Tree node type | agraph (current) | streamlit-flow (target) |
|----------------|-------------------|------------------------|
| Root (decision) | `shape="box"`, blue bg, white font | `node_type="input"`, blue CSS background, white color |
| Alternative | `shape="box"`, gray bg | `node_type="default"`, gray CSS background |
| Intermediate | `shape="dot"`, neutral color | `node_type="default"`, neutral border, smaller |
| Leaf (score ≥ 7) | `shape="diamond"`, green | `node_type="output"`, green CSS background, rounded |
| Leaf (score 4–6) | `shape="diamond"`, accent | `node_type="output"`, accent CSS background, rounded |
| Leaf (score < 4) | `shape="diamond"`, red | `node_type="output"`, red CSS background, rounded |

**Step 1.3 — Design enhanced node content**

Leverage markdown support to embed richer information directly in nodes:

```
# Root node
data = {'content': '**🎯 Decision**\n\nMy decision label'}

# Alternative node  
data = {'content': f'**{label}**\n\nMCDA: {mcda_hint:.2f} | EV: {ev:.2f}'}

# Leaf node
data = {'content': f'**{label}**\n\n🎯 {score}/10 | P: {prob}%'}

# Intermediate node
data = {'content': f'**{label}**\n\nP: {prob}% | EV: {ev:.2f}'}
```

---

### Phase 2: Core Migration

**Step 2.1 — Replace `_tree_to_agraph()` with `_tree_to_flow()`**

Write a new function `_tree_to_flow()` that recursively converts the tree dict into `StreamlitFlowNode` and `StreamlitFlowEdge` lists.

Key mapping:

```python
def _tree_to_flow(tree, nodes, edges, depth=0):
    node = tree
    is_root = depth == 0
    is_alternative = node.get("node_type") == "alternative"
    is_leaf = len(node.get("children", [])) == 0
    
    ev = _calculate_ev(node)
    score = node.get("score", 0)
    
    # Determine style and content based on node type
    if is_root:
        style = {"background": COLOR_PRIMARY, "color": "#ffffff", "border": f"2px solid {COLOR_PRIMARY}", "borderRadius": "8px", "padding": "10px", "fontWeight": "bold"}
        content = f"**🎯 {node['label']}**"
        node_type = "input"
    elif is_alternative:
        mcda_hint = node.get("mcda_hint")
        mcda_text = f"{mcda_hint:.2f}" if mcda_hint is not None else "N/D"
        style = {"background": "#edf2f7", "border": "2px solid #a0aec0", "borderRadius": "8px", "padding": "8px"}
        content = f"**{node['label']}**\n\nMCDA: {mcda_text} · EV: {ev:.2f}"
        node_type = "default"
    elif is_leaf:
        bg = COLOR_SUCCESS if score >= 7 else (COLOR_ACCENT if score >= 4 else COLOR_ERROR)
        style = {"background": bg, "color": "#fff", "borderRadius": "50%", "padding": "8px", "minWidth": "60px", "textAlign": "center"}
        content = f"**{node['label']}**\n\n🎯 {score}/10"
        node_type = "output"
    else:
        style = {"background": COLOR_NEUTRAL, "borderRadius": "8px", "padding": "8px"}
        content = f"**{node['label']}**\n\nP: {node['probability']}% · EV: {ev:.2f}"
        node_type = "default"
    
    nodes.append(StreamlitFlowNode(
        id=node["id"],
        pos=(0, 0),  # ELK handles layout
        data={"content": content},
        node_type=node_type,
        source_position="bottom",
        target_position="top",
        style=style,
        draggable=False,
        selectable=True,
    ))
    
    for child in node.get("children", []):
        prob = child.get("probability", 50)
        show_label = depth != 0
        edge_label = f"{prob}%" if show_label else ""
        
        edges.append(StreamlitFlowEdge(
            id=f"{node['id']}-{child['id']}",
            source=node["id"],
            target=child["id"],
            label=edge_label,
            animated=False,
            label_show_bg=True,
            label_bg_style={"fill": "#f7fafc", "fillOpacity": 0.8},
            style={"stroke": "#cbd5e0", "strokeWidth": max(1, prob / 100 * 4) if show_label else 2},
            markerEnd="arrowclosed",
        ))
        _tree_to_flow(child, nodes, edges, depth + 1)
```

**Step 2.2 — Replace `_render_agraph_tree()` with `_render_flow_tree()`**

```python
def _render_flow_tree(tree, render_nonce=0):
    """Render the decision tree using streamlit-flow and return selected node ID."""
    nodes = []
    edges = []
    _tree_to_flow(tree, nodes, edges)
    
    # Initialize or update flow state in session
    flow_key = "scenarios_flow_state"
    st.session_state[flow_key] = StreamlitFlowState(nodes, edges)
    
    # Render
    st.session_state[flow_key] = streamlit_flow(
        flow_key,
        st.session_state[flow_key],
        height=max(450, 120 * len(nodes)),
        fit_view=True,
        show_controls=True,
        show_minimap=len(nodes) > 15,
        direction="down",
        layout_vertical_spacing=120,
        layout_horizontal_spacing=180,
        get_node_on_click=True,
        get_edge_on_click=False,
        style={"background": "#ffffff"},
    )
    
    # Extract selected node ID from the returned state
    selected = st.session_state[flow_key]
    if isinstance(selected, dict) and selected.get("elementType") == "node":
        return selected["id"]
    return None
```

> **Note on `selected` return value**: In streamlit-flow v1.5+, the component returns an updated `StreamlitFlowState`. In older click-mode API (`get_node_on_click=True`), it returns a dict `{"elementType": "node", "id": "..."}`. Verify the exact return format during Step 1.1 testing.

**Step 2.3 — Update `render_interactive_scenarios_tab()`**

Replace the call at ~line 687:

```python
# BEFORE
selected = _render_agraph_tree(decision_tree, is_global=True, render_nonce=tree_recenter_nonce)

# AFTER
selected = _render_flow_tree(decision_tree, render_nonce=tree_recenter_nonce)
```

The `selected` variable feeds directly into `_render_action_panel(tree, selected)` — **no changes needed downstream** as long as the returned ID matches the tree node IDs (which it will, since we use `node["id"]` for both).

**Step 2.4 — Remove the `is_global` parameter**

The `is_global` parameter was only used for agraph styling differences. With streamlit-flow's richer node styling, this parameter is no longer needed. Remove it from the call chain.

**Step 2.5 — Remove the nonce hack**

The nonce-based height variation (line 467) was a workaround for agraph not supporting a `key` parameter. With streamlit-flow's native `key` support, this is no longer needed:

```python
# DELETE this pattern:
base_height = 450 + len(nodes) * 20 + (1 if int(render_nonce) % 2 else 0)

# The render_nonce parameter and _iact_tree_recenter_nonce session state key
# can be removed entirely.
```

---

### Phase 3: UX Enhancements (post-migration)

These are optional improvements enabled by the migration:

**Step 3.1 — Add minimap for large trees**
Already included in Step 2.2 (`show_minimap=len(nodes) > 15`). Auto-enabled for trees with more than 15 nodes.

**Step 3.2 — Add directed edge arrows**
Already included in Step 2.1 (`markerEnd="arrowclosed"`). Clarifies parent→child direction.

**Step 3.3 — Embed richer node content (markdown)**
Already designed in Step 1.3. Nodes will show MCDA hints, EV scores, and probabilities inline.

**Step 3.4 — (Future) Context menu integration**
streamlit-flow supports right-click context menus for edit/delete. This could eventually replace or complement the action panel, reducing UI clutter. This is a larger UX redesign and should be tackled separately.

**Step 3.5 — (Future) Edge click for probability editing**
Enable `get_edge_on_click=True` and allow direct probability adjustment by clicking an edge. This would be a significant UX improvement over the current panel-based approach.

---

### Phase 4: Cleanup

**Step 4.1 — Remove agraph dependency**
```
# requirements.txt: remove
streamlit-agraph>=0.0.45

# requirements.txt: add (if not already present)
streamlit-flow-component>=1.6.1
```

**Step 4.2 — Remove agraph imports**
```python
# DELETE from scenarios_interactive_impl.py:
from streamlit_agraph import agraph, Node, Edge, Config
```

**Step 4.3 — Delete dead functions**
- `_tree_to_agraph()` — replaced by `_tree_to_flow()`
- `_render_agraph_tree()` — replaced by `_render_flow_tree()`

**Step 4.4 — Remove nonce session state keys**
- `_iact_tree_recenter_nonce` — no longer needed

**Step 4.5 — Update comments and docstrings**
- File header comment (line 4): change "Uses streamlit-agraph (vis.js)" to "Uses streamlit-flow (React Flow)"
- Update any other references to agraph in comments.

**Step 4.6 — Uninstall agraph**
```bash
pip uninstall streamlit-agraph
```

---

## 6. Files Changed Summary

| File | Change type | Scope |
|------|-------------|-------|
| `src/components/scenarios_interactive_impl.py` | **Major** | Replace imports, rewrite 2 functions (~120 lines), update 1 call site, remove nonce hack |
| `requirements.txt` | **Minor** | Swap `streamlit-agraph` → `streamlit-flow-component` |

**No other files are affected.** The agraph usage is fully isolated to `scenarios_interactive_impl.py`.

---

## 7. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| streamlit-flow return value format differs from expected | Medium | Test in Step 1.1; adapt extraction logic |
| ELK layout produces different spacing than vis.js hierarchical | Low | Tune `layout_vertical_spacing` and `layout_horizontal_spacing` |
| Rectangular nodes look different from vis.js diamond/dot shapes | Low | Use CSS (border-radius, rotation, colors) to differentiate; the UX improvement from markdown content outweighs exact shape parity |
| streamlit-flow-component maintenance stops | Low | React Flow (xyflow) is backed by a funded company; worst case, fork or migrate to custom component v2 wrapping React Flow directly |
| Session state conflict with `StreamlitFlowState` | Low | Use a dedicated key (`scenarios_flow_state`) that doesn't conflict with existing keys |

---

## 8. Estimated Effort

| Phase | Effort |
|-------|--------|
| Phase 1: Foundation | ~1 hour (install, test, design mapping) |
| Phase 2: Core Migration | ~2-3 hours (rewrite functions, test integration) |
| Phase 3: UX Enhancements | ~1 hour (mostly already built into Phase 2) |
| Phase 4: Cleanup | ~30 min (remove dead code, update comments) |
| **Total** | **~4-5 hours** |

---

## 9. Rollback Strategy

If the migration encounters blockers:

1. **Git branch** — Work on a dedicated feature branch (`feature/migrate-agraph-to-flow`).
2. **Keep agraph functions** — Don't delete `_tree_to_agraph` / `_render_agraph_tree` until the new implementation is fully validated.
3. **Feature flag** — Optionally, use a session state flag to toggle between old and new rendering during testing:
   ```python
   use_flow = st.session_state.get("_use_streamlit_flow", True)
   if use_flow:
       selected = _render_flow_tree(decision_tree)
   else:
       selected = _render_agraph_tree(decision_tree, is_global=True, render_nonce=nonce)
   ```

# Codebase Findings — Lambda Project Pro (Focal Path Pro)

> Generated after a full review of every source file in the repository.

---

## 1. Architecture Overview

| Layer | Key files | Role |
|-------|-----------|------|
| **Entry point** | `src/app_with_routing.py` | Streamlit app with tab-based routing, session init, sidebar rendering |
| **Components** | `src/components/*.py` (15 files) | One file per tab/feature; renders UI & manages local state |
| **Utilities** | `src/utils/*.py` (8 files) | Calculations, visualizations, data I/O, session management, performance |
| **Config** | `src/config/constants.py` | All shared constants, color palette, enums, default MCDA criteria |
| **Templates** | `src/components/templates.py` | Pre-built decision templates loaded into session state |

### Data flow

```
User interaction → Streamlit widgets → st.session_state (single source of truth)
                                        ↓
                              Component logic (reads/writes state)
                                        ↓
                              Utility functions (pure calculations, charting)
                                        ↓
                              Plotly / Streamlit output
```

---

## 2. Component Inventory

| File | Tab / Feature | Lines | Complexity |
|------|---------------|-------|------------|
| `dimensionado.py` | Impact Assessment | ~122 | Low |
| `objetivo.py` | Decision Objective | ~59 | Low |
| `alternativas.py` | Alternatives CRUD | ~76 | Low |
| `prioridades.py` | Priorities & No-Negociables | ~174 | Medium |
| `informacion.py` | KPIs, Timeline, Stakeholders | ~338 | Medium |
| `evaluacion.py` | MCDA Evaluation | ~499 | High |
| `scenarios.py` | Scenarios (delegator) | ~12 | Trivial |
| `scenarios_interactive_impl.py` | Decision Tree + EV + Visualizations | ~1243 | **Very High** |
| `resultados.py` | Results Dashboard | ~749 | High |
| `risk_analysis.py` | Risk Analysis | ~491 | High |
| `retro.py` | Retrospective | ~441 | High |
| `sidebar.py` | Export/Import/Templates | ~186 | Medium |
| `monitoring_timeline.py` | Monitoring Timeline | ~699 | High |
| `templates.py` | Decision Templates | ~453 | Medium |
| `informe.py` | Full Report | ~674 | High |

**Total component code: ~6,216 lines**

---

## 3. Patterns Identified

### 3.1 Session State as Global Store
- Every component reads/writes `st.session_state` directly.
- `SessionStateManager` (in `session_manager.py`) provides defaults, lazy init, cleanup, and validation, but most components still use raw `st.session_state.get()` / direct assignment.
- **Risk**: tightly coupled components; any key rename requires multi-file search.

### 3.2 UUID-based Entity Management
- Alternatives, priorities, KPIs, timeline items, stakeholders, risks, outcomes, tripwires, and no-negociables all use `uuid.uuid4()` for IDs.
- CRUD follows a consistent pattern: list of dicts in session state, add/delete via button callbacks.

### 3.3 Plotly for All Visualizations
- Every chart uses `plotly.graph_objects` (not `plotly.express`).
- Charts are rendered with `st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})`.
- Color constants centralized in `constants.py` (`COLOR_PRIMARY`, `ALT_CHART_PALETTE`, etc.).

### 3.4 Performance Monitoring
- `@monitor_performance` decorator available in `utils/performance.py`.
- Applied to key rendering functions via import; tracks execution time.

### 3.5 Data Export/Import
- JSON export: serializes session state keys → file download.
- Excel export: flattens data into multiple sheets via `openpyxl`.
- Import validates JSON structure before loading.
- `data_manager.py` handles serialization logic centrally.

### 3.6 Composite Scoring
- MCDA score (criteria-weighted) + Expected Value (scenario-weighted) combined via user-adjustable slider (`composite_weight_slider`).
- EV scaled from 0-10 → 0-5 to match MCDA range before compositing.

### 3.7 Decision Tree Model
- Trees stored in `scenarios_decision_tree` (canonical) and `scenarios_tree_projection` (per-alternative projected subtrees).
- Tree operations: bifurcate, add sub-branch, collapse, delete, rebalance probabilities.
- `streamlit-agraph` used for interactive node-click visualization.

---

## 4. Potential Issues & Technical Debt

### 4.1 Large Files
- `scenarios_interactive_impl.py` (1,243 lines) is the largest and most complex file. It handles tree CRUD, EV calculation, agraph rendering, density charts, decision matrix, and mixture distributions all in one module.
- `resultados.py` (749 lines) and `monitoring_timeline.py` (699 lines) are also large monoliths.
- **Recommendation**: Consider splitting `scenarios_interactive_impl.py` into tree-management, visualization, and UI sub-modules.

### 4.2 NumPy API Compatibility
- `scenarios_interactive_impl.py` already handles the `np.trapz` → `np.trapezoid` rename (NumPy 2.x). Good forward-compatibility practice.

### 4.3 Deep Session State Nesting
- `retro` key contains a nested dict with lists of dicts. Mutations happen in-place (`st.session_state["retro"]["outcomes"].append(...)`).
- Risk of Streamlit not detecting deep mutations for re-render. Currently mitigated by `st.rerun()` calls after mutations.

### 4.4 Duplicated Chart Logic
- Decision matrix / bubble chart appears in both `scenarios_interactive_impl.py` and `resultados.py` with similar but not identical implementations.
- MCDA ranking computation is duplicated across `evaluacion.py`, `resultados.py`, `scenarios_interactive_impl.py`, and `informe.py`.
- **Recommendation**: Extract shared chart builders and ranking logic into `utils/visualizations.py` or a dedicated module.

### 4.5 No Automated Tests
- No test files found in the repository. Given the complexity of MCDA calculations, EV computation, and tree operations, unit tests would significantly reduce regression risk.

### 4.6 Orphaned / Legacy Files
- `src/__init__.py_obsoleto` and `src/config/__init__.py_obsoleto` — legacy files renamed rather than deleted.
- `archive/` directory contains old markdown docs and `.py_obsoleto` files.
- These don't affect runtime but add clutter.

### 4.7 Hardcoded UI Strings (Spanish)
- All UI text is hardcoded in Spanish throughout components. No i18n layer exists.
- Not necessarily an issue if the target audience is Spanish-speaking, but limits future localization.

### 4.8 `st.rerun()` Usage
- Several components call `st.rerun()` after state mutations (e.g., adding/deleting items). This is the standard Streamlit pattern but can cause performance issues if triggered frequently.

---

## 5. Key Utility Files Summary

| File | Purpose |
|------|---------|
| `calculations.py` | MCDA totals, ranking, relevance %, time recommendation |
| `visualizations.py` | Impact chart, radar, bar, risk heatmap, timeline, gauge builders |
| `data_manager.py` | JSON/Excel export & import, session state serialization |
| `session_manager.py` | `SessionStateManager` class: defaults, lazy init, cleanup, validation |
| `ui_helpers.py` | Reusable Streamlit UI patterns (styled cards, metrics, etc.) |
| `performance.py` | `@monitor_performance` decorator, execution time tracking |
| `formatters.py` | Number/date formatting helpers |
| `__init__.py` | Empty module marker |

---

## 6. Dependency Map (Key Imports)

```
streamlit          — UI framework (every file)
plotly             — All charts (graph_objects)
pandas             — DataFrames for MCDA, rankings, exports
numpy              — Statistical calculations, KDE, interpolation
scipy.stats        — Gaussian KDE in scenarios
streamlit-agraph   — Interactive decision tree graph
openpyxl           — Excel export
uuid               — Entity ID generation
datetime           — Timestamps
json               — Data serialization
```

---

## 7. Session State Key Map (Critical Keys)

| Key | Type | Used by |
|-----|------|---------|
| `alts` | `list[dict]` | alternativas, evaluacion, scenarios, resultados, informe |
| `priorities` | `list[dict]` | prioridades, evaluacion |
| `mcda_scores` | `dict` | evaluacion, resultados, scenarios, informe |
| `mcda_scores_df` | `DataFrame` | evaluacion, resultados, scenarios |
| `mcda_criteria` | `list[dict]` | evaluacion, resultados |
| `scenarios_decision_tree` | `dict` | scenarios_interactive_impl, resultados, informe |
| `scenarios_tree_projection` | `dict` | scenarios_interactive_impl, resultados |
| `risks` | `dict` | risk_analysis, monitoring_timeline, informe |
| `retro` | `dict` | retro, monitoring_timeline, informe |
| `no_negociables` | `list[dict]` | prioridades, evaluacion |
| `no_negociables_scores` | `dict` | evaluacion, resultados |
| `decision` | `str` | objetivo, sidebar, resultados, informe |
| `composite_weight_slider` | `int` | scenarios_interactive_impl, resultados |

---

## 8. Recommendations Summary

1. **Split `scenarios_interactive_impl.py`** — Extract tree operations, chart builders, and EV calculations into separate modules.
2. **Deduplicate ranking/chart logic** — Centralize MCDA ranking and decision matrix chart construction.
3. **Add unit tests** — Prioritize `calculations.py` functions and tree EV computation.
4. **Clean up archive/obsoleto files** — Remove or `.gitignore` legacy files.
5. **Consider a state key registry** — A single file mapping all session state keys to avoid silent key mismatches across components.
6. **Monitor `st.rerun()` frequency** — Profile for unnecessary re-renders in high-interaction components.

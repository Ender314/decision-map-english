# AI Instructions — Decider Pro

## Overview
**Decider Pro** (formerly Focal Path Pro) is a Streamlit-based decision analysis application (Spanish UI). It implements Multi-Criteria Decision Analysis (MCDA) with scenario planning, impact assessment, and visualization tools.

## Architecture

### Entry Point
- **`src/app_with_routing.py`** — Main app with page routing (`landing` → `offer` → `app`)
- Routing via `st.session_state["current_page"]`; URL params supported (`?page=app`)

### Directory Structure
```
src/
├── app_with_routing.py    # Main entry, routing logic
├── config/constants.py    # All constants, tab names, impact mappings
├── utils/
│   ├── calculations.py    # Math ops, MCDA normalization, scoring
│   ├── data_manager.py    # JSON/Excel export/import, validation
│   ├── session_manager.py # Session state initialization & cleanup
│   ├── visualizations.py  # Plotly chart generation (incl. PERT distribution)
│   ├── violin_plots.py    # DEPRECATED — no longer imported; kept for reference only
│   ├── ui_helpers.py      # UI utility functions
│   └── performance.py     # Debug mode performance tools
└── components/
    ├── landing_page.py    # Marketing landing page
    ├── offer_page.py      # Product offer page
    ├── sidebar.py         # Export/import UI
    ├── dimensionado.py    # Impact assessment (corto/medio/largo)
    ├── alternativas.py    # Decision alternatives CRUD
    ├── objetivo.py        # Strategic objective input
    ├── prioridades.py     # Priority ordering
    ├── informacion.py     # KPIs, timeline, stakeholders
    ├── evaluacion.py      # MCDA scoring with radar charts
    ├── scenarios.py       # Probability distributions
    ├── resultados.py      # Executive summary dashboard
    ├── risk_analysis.py   # Risk inventory, matrix, mitigation strategies
    ├── retro.py           # Retrospective: outcomes, tripwires, lessons
    ├── monitoring_timeline.py  # Monitoring phase timeline & recommended alternative
    ├── templates.py       # Template selector for onboarding examples
    └── informe.py         # Full lifecycle report (Data Story format)
```

### Session State Pattern
- All state stored in `st.session_state` directly (no complex abstractions)
- Defaults initialized via `init_session_state()` using `SessionStateManager.DEFAULTS` (`utils/session_manager.py`)
- Key structures: `alts`, `priorities`, `mcda_criteria`, `mcda_scores`, `scenarios`, `risks`, `retro`, `no_negociables`, `no_negociables_scores`, `emotion_notes`

## Key Conventions

### Streamlit Anti-Patterns (CRITICAL)
1. **Never use CSS to hide/show components** — causes session state loss
2. **Avoid unnecessary `st.rerun()`** — button clicks auto-rerun
3. Use **conditional Python rendering** instead: `if show_sidebar: render_sidebar()`

### Data Flow
- **Import**: Sidebar upload → `_pending_import` flag → `import_json_data()` before widgets
- **Export**: `create_export_data()` → JSON with strict schema validation
- All items use `{"id": uuid, "text": ...}` pattern for alternatives/priorities

### Excel Support
- **Excel Export**: `create_excel_export()` → in-memory `.xlsx` via `openpyxl`
- **Excel Import**: `import_excel_data()` → loads sheets and repopulates `st.session_state`

### Tabs System
- Tab visibility controlled by `get_sections_for_time()` based on `tiempo` selection
- Tab constants in `config/constants.py`: `TAB_DIMENSIONADO`, `TAB_ALTERNATIVAS`, etc.
- Display names with emojis: `TAB_DISPLAY_NAMES` dict

## Development Workflow

### Run Locally
```bash
cd "c:\Users\yomis\OneDrive\Desarrollos\Lambda project Pro"
streamlit_venv\Scripts\activate
python -m streamlit run src/app_with_routing.py --server.port 8501
```

### Debug Mode
- Set `debug_mode = true` in `.streamlit/secrets.toml`
- Or use URL param: `?debug=true`

### Dependencies
Core: `streamlit>=1.28.0`, `pandas`, `numpy`, `plotly`, `openpyxl`
Legacy (unused, only in deprecated `violin_plots.py`): `seaborn`, `matplotlib`

## JSON Schema (Import/Export)
Required top-level keys: `meta`, `decision`, `impacto`, `alternativas`, `asignacion_tiempo`, `objetivo`, `prioridades`, `informacion`, `mcda`, `scenarios`
Optional keys (v0.3.0+): `risks`, `retro`, `estrategia_corporativa`, `no_negociables`, `emotion_notes`

Validation in `validate_json_structure()` — accepts `APP_NAME` ("Decider Pro") or legacy names ("Focal Path Pro", "Lambda Pro").

### Export Version History
- **v0.4.0**: Added `emotion_notes` top-level key, `no_negociables` with constraints + scores, Excel "Emociones" row in Notas sheet
- **v0.3.1**: Added `assessments` array to risks, `notes` field, Excel sheet `Riesgos_Evaluaciones`
- **v0.3.0**: Added `risks` and `retro` top-level keys
- **v0.2.0**: Base schema with MCDA and scenarios

### Scenarios Representation
- **In-session**: `st.session_state["scenarios"]` is a dict keyed by `alt_id`
- **Export JSON**: `scenarios` is exported as a list of rows (one per alternativa) including `alternativa`, `worst_desc`, `best_desc`, scores, probabilities, and `EV`
- **Distribution chart**: Uses analytical **PERT distribution** (scaled Beta PDF via `pert_pdf()` in `calculations.py`), rendered as Plotly filled area curves in `create_scenario_pert_chart()`. No Monte Carlo sampling — deterministic, smooth curves.
- **Default slider range**: `(4, 6)` (worst, best) — intentionally close together to avoid overconfident initial estimates

### Risks Representation
- **In-session**: `st.session_state["risks"]` is a dict keyed by `risk_id`
- Each risk has: `id`, `title`, `probability`, `impact`, `linked_alt_id`, `strategies` (avoid/transfer/mitigate/contingency), `notes`, `status`, `created_at`, `assessments`
- **Export JSON**: `risks` is a list of risk objects with full `assessments` array (time-series evaluations)
- **Excel Export**: Two sheets — `Riesgos` (main data) + `Riesgos_Evaluaciones` (time-series assessments)

### Retro Representation
- **In-session**: `st.session_state["retro"]` is a dict with:
  - `decision_date`, `review_date`, `chosen_alternative_id`
  - `outcomes`: list of outcome dicts (description, date, attribution, sentiment)
  - `tripwires`: list of tripwire dicts (trigger, threshold, status, triggered_date, action_taken)
  - `lessons_learned`, `decision_quality_score`, `outcome_quality_score`

## Extending the App
- **New tab**: Add component in `components/`, constant in `constants.py`, render call in `app_with_routing.py`
- **New visualization**: Add to `visualizations.py`
- **Session defaults**: Update `initialize_session_defaults()` in `data_manager.py`

## Post-Decision Monitoring (v0.3.0+)

### Monitoring Phase Shared UI
**Entry point**: `components/monitoring_timeline.py` → `render_monitoring_timeline()` and `render_recommended_alternative_banner()`

The monitoring phase (Seguimiento tab) shows the **recommended alternative** at the top as a read-only reference (not a selector).

Both Riesgos and Retrospectiva are intentionally **decoupled from alternatives** in the UI.

Legacy fields (kept for import/export compatibility):
- `risk.linked_alt_id`
- `retro.chosen_alternative_id`

### Risk Analysis Tab (`TAB_RIESGOS`)
**Entry point**: `components/risk_analysis.py` → `render_risk_analysis_tab()`
**Alternative selection**: Not used (global risks view)

#### Data Structure (`st.session_state["risks"]`)
Dict keyed by `risk_id`, each risk contains:
```python
{
    "id": str,                    # UUID
    "title": str,                 # Risk description
    "probability": str,           # "bajo" | "medio" | "alto"
    "impact": str,                # "bajo" | "medio" | "alto" | "crítico"
    "linked_alt_id": str,         # Legacy: may be null/ignored in UI
    "strategies": {
        "avoid": str,             # Elimination strategy
        "transfer": str,          # Insurance/outsourcing
        "mitigate": str,          # Reduce probability/impact
        "contingency": str        # Plan B if risk materializes
    },
    "notes": str,
    "status": str,                # "identificado" | "en_tratamiento" | "aceptado" | "cerrado"
    "created_at": str,            # ISO date
    "assessments": [              # Time-series risk evolution
        {"date": str, "probability": str, "impact": str}
    ]
}
```

#### Key Functions
| Function | Purpose |
|----------|---------|
| `get_recommended_alternative()` | Composite ranking: 50% MCDA score + 50% scenario EV (in `monitoring_timeline.py`) |
| `calculate_risk_score(prob, impact)` | Returns `RISK_PROB_MAP[prob] × RISK_IMPACT_MAP[impact]` (1-12 scale) |
| `get_risk_color(score)` | Maps score to hex color (green→yellow→orange→red) |
| `count_active_risks()` | Counts non-closed risks |

#### Constants (`config/constants.py`)
- `RISK_CATEGORIES`: técnico, financiero, operacional, externo, estratégico
- `RISK_PROBABILITY`: bajo (1), medio (2), alto (3)
- `RISK_IMPACT`: bajo (1), medio (2), alto (3), crítico (4)
- `RISK_STATUS`: identificado → en_tratamiento → aceptado → cerrado
- `RISK_PROB_MAP` / `RISK_IMPACT_MAP`: Numeric mappings for score calculation

#### Visualizations
- **Risk Matrix**: Plotly scatter with colored zones (green/yellow/orange/red)
- **Bubble size** = risk score; **Position** = (impact, probability)
- **Ranking Table**: DataFrame sorted by score descending

#### UI Flow
1. Metrics row: total risks, high-impact count, treatment progress
2. Expandable form to add new risks
3. Risk inventory: sorted expanders with inline editing
4. Per-risk: probability/impact/status selectors, 4-tab strategy editor, assessment history
5. Risk matrix visualization + ranking table

### Retrospective Tab (`TAB_RETRO`)
- Tracks outcomes after decision implementation
- Attribution analysis: decisión vs azar vs mixto
- Tripwires: trigger conditions that should cause reevaluation
- Quality scores: decision process quality vs outcome quality
- Lessons learned documentation

## Resultados Tab (Executive Summary)

The Resultados tab (`components/resultados.py`) renders a comprehensive executive summary:

### Layout (top to bottom)
1. **Print CSS** — `@media print` stylesheet injected to hide Streamlit chrome
2. **Hero Banner** — Recommended alternative + Robustness Index badge (replaced old confidence metric)
3. **Key Metrics Row** — Relevance %, time allocation, alternatives count, priorities count
4. **Análisis Visual** — Radar chart (Perfil por Criterios), Decision Matrix bubble chart, Stacked bar (Contribución por Criterio)
5. **Robustness Index** — Monte Carlo sensitivity analysis with weight/score perturbation + dominant criterion removal
6. **Insights** — Auto-generated observations based on data
7. **📋 Contexto de la Decisión** — Collapsed expander merging: Objetivo, Estrategia, Past Decisions, KPIs, Stakeholders, Timeline, Notes
8. **🏅 Rankings y Datos** — MCDA + EV side-by-side tables, Composite ranking + Pesos de Prioridades, No Negociables table
9. **Export CTA** — Export button + Print/PDF button (via `st.components.v1.html` + `window.parent.print()`)
10. **🪞 Observa tus emociones** — Persisted `st.text_area` for emotional reflection notes (`emotion_notes` in session state, exported/imported)

### Print Support
- Print button uses `st.components.v1.html()` with `window.parent.print()` (not `onclick` in raw HTML — Streamlit's React blocks that)
- `@media print` CSS hides sidebar, header, toolbar, buttons, deploy button
- `.no-print` class available for elements that should be hidden when printing

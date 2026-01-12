# AI Instructions — Focal Path Pro

## Overview
**Focal Path Pro** is a Streamlit-based decision analysis application (Spanish UI). It implements Multi-Criteria Decision Analysis (MCDA) with scenario planning, impact assessment, and visualization tools.

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
│   ├── visualizations.py  # Plotly chart generation
│   ├── violin_plots.py    # Scenario distribution visualizations
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
    └── retro.py           # Retrospective: outcomes, tripwires, lessons
```

### Session State Pattern
- All state stored in `st.session_state` directly (no complex abstractions)
- Defaults initialized via `init_session_state()` using `SessionStateManager.DEFAULTS` (`utils/session_manager.py`)
- Key structures: `alts`, `priorities`, `mcda_criteria`, `mcda_scores`, `scenarios`, `risks`, `retro`

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
Core: `streamlit>=1.28.0`, `pandas`, `numpy`, `plotly`, `seaborn`, `matplotlib`, `openpyxl`

## JSON Schema (Import/Export)
Required top-level keys: `meta`, `decision`, `impacto`, `alternativas`, `asignacion_tiempo`, `objetivo`, `prioridades`, `informacion`, `mcda`, `scenarios`
Optional keys (v0.3.0+): `risks`, `retro`, `estrategia_corporativa`

Validation in `validate_json_structure()` — accepts `APP_NAME` or legacy "Lambda Pro".

### Export Version History
- **v0.3.1**: Added `assessments` array to risks, `notes` field, Excel sheet `Riesgos_Evaluaciones`
- **v0.3.0**: Added `risks` and `retro` top-level keys
- **v0.2.0**: Base schema with MCDA and scenarios

### Scenarios Representation
- **In-session**: `st.session_state["scenarios"]` is a dict keyed by `alt_id`
- **Export JSON**: `scenarios` is exported as a list of rows (one per alternativa) including `alternativa`, `worst_desc`, `best_desc`, scores, probabilities, and `EV`

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
- **New visualization**: Add to `visualizations.py` or `violin_plots.py`
- **Session defaults**: Update `SessionStateManager.DEFAULTS`

## Post-Decision Monitoring (v0.3.0+)

### Risk Analysis Tab (`TAB_RIESGOS`)
**Entry point**: `components/risk_analysis.py` → `render_risk_analysis_tab()`

#### Data Structure (`st.session_state["risks"]`)
Dict keyed by `risk_id`, each risk contains:
```python
{
    "id": str,                    # UUID
    "title": str,                 # Risk description
    "probability": str,           # "bajo" | "medio" | "alto"
    "impact": str,                # "bajo" | "medio" | "alto" | "crítico"
    "linked_alt_id": str,         # Links risk to specific alternative
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
| `get_recommended_alternative()` | Composite ranking: 50% MCDA score + 50% scenario EV |
| `calculate_risk_score(prob, impact)` | Returns `RISK_PROB_MAP[prob] × RISK_IMPACT_MAP[impact]` (1-12 scale) |
| `get_risk_color(score)` | Maps score to hex color (green→yellow→orange→red) |
| `count_active_risks()` | Counts non-closed risks for selected alternative |

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
1. User selects alternative (defaults to recommended)
2. Metrics row: total risks, high-impact count, treatment progress
3. Expandable form to add new risks
4. Risk inventory: sorted expanders with inline editing
5. Per-risk: probability/impact/status selectors, 4-tab strategy editor, assessment history
6. Risk matrix visualization + ranking table

### Retrospective Tab (`TAB_RETRO`)
- Tracks outcomes after decision implementation
- Attribution analysis: decisión vs azar vs mixto
- Tripwires: trigger conditions that should cause reevaluation
- Quality scores: decision process quality vs outcome quality
- Lessons learned documentation

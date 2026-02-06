# -*- coding: utf-8 -*-
"""
Data management utilities for Decider Pro.
Handles session state, export/import, and data validation.
"""

import json
import uuid
import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Any, Tuple, Optional
import numpy as np
from io import BytesIO

from config.constants import DEFAULT_MCDA_CRITERIA, APP_NAME, APP_VERSION, LEGACY_APP_NAMES


def json_safe_convert(obj: Any) -> Any:
    """Convert objects to JSON-safe format."""
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (pd.Timestamp, datetime, date)):
        return obj.isoformat()
    if isinstance(obj, pd.DataFrame):
        return {
            "columns": list(obj.columns),
            "index": list(map(str, obj.index)),
            "data": obj.reset_index(drop=True).to_dict(orient="records"),
        }
    return obj


def make_json_ready(obj: Any) -> Any:
    """Recursively convert object to JSON-safe format."""
    if isinstance(obj, dict):
        return {k: make_json_ready(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_ready(v) for v in obj]
    return json_safe_convert(obj)


def initialize_session_defaults() -> None:
    """Initialize all session state defaults."""
    defaults = {
        # Impact assessment
        "impacto_corto": "bajo",
        "impacto_medio": "medio", 
        "impacto_largo": "bajo",
        
        # Time allocation
        "tiempo": "Menos de media hora",
        "tiempo_user_override": False,
        
        # Core data
        "decision": "",
        "estrategia_corporativa": "",
        "objetivo": "",
        "alts": [],  # list of {"id", "text"}
        "priorities": [],  # list of {"id", "text"}
        
        # Information tab
        "past_decisions": [],  # list of {"id", "decision", "results", "lessons"}
        "kpis": [],  # list of {"id", "name", "value", "unit"}
        "timeline_items": [],  # list of {"id", "event", "date"}
        "stakeholders": [],  # list of {"id", "name", "opinion"}
        "quantitative_notes": "",
        "qualitative_notes": "",
        
        # MCDA evaluation
        "mcda_criteria": DEFAULT_MCDA_CRITERIA.copy(),
        "mcda_scores": {},  # {alt_name: {criterion: score}}
        "mcda_scores_df": None,
        "weights_user_override": False,  # Track manual weight edits
        
        # Escenarios
        "scenarios": {},  # {alt_id: scenario_data}
    }
    
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def validate_json_structure(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate that JSON has the expected structure from this app."""
    required_keys = ["meta", "decision", "impacto", "alternativas", "asignacion_tiempo", 
                   "objetivo", "prioridades", "informacion", "mcda", "scenarios"]
    # Note: "risks" and "retro" are optional for backward compatibility
    # Note: "estrategia_corporativa" is optional for backward compatibility
    
    # Check top-level structure
    for key in required_keys:
        if key not in data:
            return False, f"Falta la clave requerida: '{key}'"
    
    # Check meta information
    if not isinstance(data.get("meta"), dict):
        return False, "Estructura 'meta' inválida"
    
    # Accept current app name and all legacy names for backward compatibility
    valid_app_names = {APP_NAME} | set(LEGACY_APP_NAMES)
    if data["meta"].get("app") not in valid_app_names:
        return False, f"Este JSON no es de {APP_NAME} (app: {data['meta'].get('app')})"
    
    # Check critical structures
    if not isinstance(data.get("alternativas"), list):
        return False, "Estructura 'alternativas' debe ser una lista"
    
    if not isinstance(data.get("prioridades"), list):
        return False, "Estructura 'prioridades' debe ser una lista"
    
    if not isinstance(data.get("informacion"), dict):
        return False, "Estructura 'informacion' debe ser un objeto"
    
    # Additional validation for data integrity
    meta = data.get("meta", {})
    if not isinstance(meta.get("exported_at"), str):
        return False, "Falta timestamp de exportación válido"
    
    # Validate impacto structure
    impacto = data.get("impacto", {})
    if not isinstance(impacto, dict):
        return False, "Estructura 'impacto' debe ser un objeto"
    
    required_impact_keys = ["corto", "medio", "largo", "relevancia_pct"]
    for key in required_impact_keys:
        if key not in impacto:
            return False, f"Falta clave de impacto: '{key}'"
    
    # Validate MCDA structure
    mcda = data.get("mcda", {})
    if not isinstance(mcda, dict):
        return False, "Estructura 'mcda' debe ser un objeto"
    
    if "criteria" not in mcda or not isinstance(mcda["criteria"], list):
        return False, "Estructura 'mcda.criteria' debe ser una lista"
    
    # Validate scenarios structure
    scenarios = data.get("scenarios", [])
    if not isinstance(scenarios, list):
        return False, "Estructura 'scenarios' debe ser una lista"
    
    return True, "Estructura válida"


def parse_date_string(date_str: Optional[str]) -> Optional[date]:
    """Convert ISO date string back to date object."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str).date()
    except (ValueError, TypeError):
        return None


def create_export_data() -> Dict[str, Any]:
    """Create export data from current session state."""
    from utils.calculations import scenario_expected_value, mcda_totals_and_ranking
    
    # Get current data
    alt_names = [a["text"].strip() for a in st.session_state.get("alts", []) if a["text"].strip()]
    prioridad_names = [p["text"].strip() for p in st.session_state.get("priorities", []) if p["text"].strip()]
    
    if not (alt_names and prioridad_names):
        return {}
    
    # MCDA snapshot
    crit = st.session_state.get("mcda_criteria", [])
    scores_df = st.session_state.get("mcda_scores_df", pd.DataFrame())
    _, ranking_list = mcda_totals_and_ranking(scores_df.copy(), crit)
    
    # Scenarios snapshot
    scenarios_state = st.session_state.get("scenarios", {})
    scenario_rows = []
    for scenario_data in scenarios_state.values():
        ev = scenario_expected_value(
            scenario_data.get("p_best", 0.5),
            scenario_data.get("worst_score", 0),
            scenario_data.get("best_score", 0)
        )
        scenario_rows.append({
            "alternativa": scenario_data.get("name", ""),
            "worst_desc": scenario_data.get("worst_desc", ""),
            "best_desc": scenario_data.get("best_desc", ""),
            "worst_score": json_safe_convert(scenario_data.get("worst_score")),
            "best_score": json_safe_convert(scenario_data.get("best_score")),
            "p_best": json_safe_convert(scenario_data.get("p_best")),
            "p_best_pct": json_safe_convert(scenario_data.get("p_best_pct")),
            "EV": json_safe_convert(ev),
        })
    
    # Calculate relevance
    from utils.calculations import calculate_relevance_percentage
    from config.constants import IMPACT_MAP
    
    relevance_pct = calculate_relevance_percentage(
        st.session_state.get("impacto_corto", "bajo"),
        st.session_state.get("impacto_medio", "medio"),
        st.session_state.get("impacto_largo", "bajo"),
        IMPACT_MAP
    )
    
    # Build export payload
    export_data = {
        "meta": {
            "exported_at": datetime.now().isoformat(),
            "app": APP_NAME,
            "version": APP_VERSION,
        },
        "decision": st.session_state.get("decision", "").strip(),
        "estrategia_corporativa": st.session_state.get("estrategia_corporativa", "").strip(),
        "impacto": {
            "corto": st.session_state.get("impacto_corto"),
            "medio": st.session_state.get("impacto_medio"),
            "largo": st.session_state.get("impacto_largo"),
            "relevancia_pct": int(relevance_pct),
        },
        "alternativas": [{"id": a["id"], "text": a["text"]} for a in st.session_state.get("alts", [])],
        "asignacion_tiempo": {
            "tiempo": st.session_state.get("tiempo"),
            "tiempo_user_override": st.session_state.get("tiempo_user_override", False),
        },
        "objetivo": st.session_state.get("objetivo", "").strip(),
        "prioridades": [{"id": p["id"], "text": p["text"]} for p in st.session_state.get("priorities", [])],
        "informacion": {
            "past_decisions": [{"id": p["id"], "decision": p["decision"], "results": p["results"], "lessons": p["lessons"]}
                              for p in st.session_state.get("past_decisions", [])],
            "kpis": [{"id": k["id"], "name": k["name"], "value": k["value"], "unit": k["unit"]}
                     for k in st.session_state.get("kpis", [])],
            "timeline_items": [{"id": t["id"], "event": t["event"], "date": (t["date"].isoformat() if t["date"] else None)}
                               for t in st.session_state.get("timeline_items", [])],
            "stakeholders": [{"id": s["id"], "name": s["name"], "opinion": s["opinion"]}
                             for s in st.session_state.get("stakeholders", [])],
            "quantitative_notes": st.session_state.get("quantitative_notes", "").strip(),
            "qualitative_notes": st.session_state.get("qualitative_notes", "").strip(),
        },
        "mcda": {
            "criteria": crit,
            "scores": st.session_state.get("mcda_scores", {}),
            "scores_table": json_safe_convert(scores_df) if isinstance(scores_df, pd.DataFrame) else scores_df,
            "ranking": ranking_list,
            "weights_user_override": st.session_state.get("weights_user_override", False),
        },
        "scenarios": scenario_rows,
        "no_negociables": _export_no_negociables(),
        "risks": _export_risks(),
        "retro": _export_retro(),
    }
    
    return export_data


def _export_no_negociables() -> Dict[str, Any]:
    """Export no negociables (hard constraints) data for JSON."""
    no_negociables = st.session_state.get("no_negociables", [])
    no_neg_scores = st.session_state.get("no_negociables_scores", {})
    
    return {
        "constraints": [{"id": c["id"], "text": c["text"]} for c in no_negociables],
        "scores": no_neg_scores  # {alt_id: {constraint_id: True/False}}
    }


def _export_risks() -> List[Dict[str, Any]]:
    """Export risks data for JSON."""
    risks = st.session_state.get("risks", {})
    risk_rows = []
    for risk_id, risk in risks.items():
        risk_rows.append({
            "id": risk.get("id", risk_id),
            "title": risk.get("title", ""),
            "probability": risk.get("probability", "medio"),
            "impact": risk.get("impact", "medio"),
            "linked_alt_id": risk.get("linked_alt_id"),
            "strategies": risk.get("strategies", {}),
            "notes": risk.get("notes", ""),
            "status": risk.get("status", "identificado"),
            "created_at": risk.get("created_at"),
            "assessments": risk.get("assessments", [])
        })
    return risk_rows


def _export_retro() -> Dict[str, Any]:
    """Export retrospective data for JSON."""
    retro = st.session_state.get("retro", {})
    
    # Convert dates to ISO strings
    decision_date = retro.get("decision_date")
    review_date = retro.get("review_date")
    
    if isinstance(decision_date, date):
        decision_date = decision_date.isoformat()
    if isinstance(review_date, date):
        review_date = review_date.isoformat()
    
    return {
        "decision_date": decision_date,
        "review_date": review_date,
        "chosen_alternative_id": retro.get("chosen_alternative_id"),
        "outcomes": retro.get("outcomes", []),
        "tripwires": retro.get("tripwires", []),
        "lessons_learned": retro.get("lessons_learned", ""),
        "decision_quality_score": retro.get("decision_quality_score", 3),
        "outcome_quality_score": retro.get("outcome_quality_score", 3)
    }


def import_json_data(data: Dict[str, Any], navigate_to_app: bool = False, show_redirect_message: bool = False) -> None:
    """
    Import JSON data into session state, clearing existing data.
    
    This is the single source of truth for JSON import logic.
    
    Args:
        data: The parsed JSON data to import
        navigate_to_app: If True, set current_page to "app" after import
        show_redirect_message: If True, set redirect_to_first_tab flag for UI feedback
    """
    
    # Clear existing session state (preserve Streamlit internal keys and routing)
    # NOTE: Do NOT preserve FormSubmitter:* keys. Streamlit forbids programmatically
    # setting submit-button widget values via st.session_state.
    keys_to_preserve = [
        k for k in st.session_state.keys()
        if k.startswith('_') or k in ['current_page', 'show_sidebar']
    ]
    current_state = {k: st.session_state[k] for k in keys_to_preserve}
    st.session_state.clear()
    st.session_state.update(current_state)
    
    # Import basic data
    st.session_state["decision"] = data.get("decision", "")
    st.session_state["estrategia_corporativa"] = data.get("estrategia_corporativa", "")
    
    # Import impact data
    impacto = data.get("impacto", {})
    st.session_state["impacto_corto"] = impacto.get("corto", "bajo")
    st.session_state["impacto_medio"] = impacto.get("medio", "medio")
    st.session_state["impacto_largo"] = impacto.get("largo", "bajo")
    
    # Import time data
    tiempo_data = data.get("asignacion_tiempo", {})
    if isinstance(tiempo_data, str):  # Handle old format
        st.session_state["tiempo"] = tiempo_data
        st.session_state["tiempo_user_override"] = False
    else:
        st.session_state["tiempo"] = tiempo_data.get("tiempo", "Menos de media hora")
        st.session_state["tiempo_user_override"] = tiempo_data.get("tiempo_user_override", False)
    
    # Import objetivo
    st.session_state["objetivo"] = data.get("objetivo", "")
    
    # Import alternativas (ensure they have IDs)
    alts = data.get("alternativas", [])
    imported_alts = []
    for alt in alts:
        if isinstance(alt, str):  # Handle old format (text only)
            imported_alts.append({"id": str(uuid.uuid4()), "text": alt})
        else:  # New format with ID
            imported_alts.append({"id": alt.get("id", str(uuid.uuid4())), "text": alt.get("text", "")})
    st.session_state["alts"] = imported_alts
    
    # Import prioridades (ensure they have IDs)
    priors = data.get("prioridades", [])
    imported_priors = []
    for prior in priors:
        if isinstance(prior, str):  # Handle old format (text only)
            imported_priors.append({"id": str(uuid.uuid4()), "text": prior})
        else:  # New format with ID
            imported_priors.append({"id": prior.get("id", str(uuid.uuid4())), "text": prior.get("text", "")})
    st.session_state["priorities"] = imported_priors
    
    # Import information data
    info = data.get("informacion", {})
    
    # Past Decisions
    past_decisions = info.get("past_decisions", [])
    imported_past_decisions = []
    for decision in past_decisions:
        imported_past_decisions.append({
            "id": decision.get("id", str(uuid.uuid4())),
            "decision": decision.get("decision", ""),
            "results": decision.get("results", ""),
            "lessons": decision.get("lessons", "")
        })
    st.session_state["past_decisions"] = imported_past_decisions
    
    # KPIs
    kpis = info.get("kpis", [])
    imported_kpis = []
    for kpi in kpis:
        imported_kpis.append({
            "id": kpi.get("id", str(uuid.uuid4())),
            "name": kpi.get("name", kpi.get("nombre", "")),  # Handle both formats
            "value": kpi.get("value", kpi.get("valor", "")),
            "unit": kpi.get("unit", kpi.get("unidad", ""))
        })
    st.session_state["kpis"] = imported_kpis
    
    # Timeline items
    timeline = info.get("timeline_items", info.get("timeline", []))  # Handle both formats
    imported_timeline = []
    for item in timeline:
        imported_timeline.append({
            "id": item.get("id", str(uuid.uuid4())),
            "event": item.get("event", item.get("evento", "")),
            "date": parse_date_string(item.get("date", item.get("fecha")))
        })
    st.session_state["timeline_items"] = imported_timeline
    
    # Stakeholders
    stakeholders = info.get("stakeholders", [])
    imported_stakeholders = []
    for stakeholder in stakeholders:
        imported_stakeholders.append({
            "id": stakeholder.get("id", str(uuid.uuid4())),
            "name": stakeholder.get("name", stakeholder.get("nombre", "")),
            "opinion": stakeholder.get("opinion", "")
        })
    st.session_state["stakeholders"] = imported_stakeholders
    
    # Notes
    st.session_state["quantitative_notes"] = info.get("quantitative_notes", info.get("notas_cuantitativas", ""))
    st.session_state["qualitative_notes"] = info.get("qualitative_notes", info.get("notas_cualitativas", ""))
    
    # Import MCDA data
    mcda = data.get("mcda", {})
    st.session_state["mcda_criteria"] = mcda.get("criteria", DEFAULT_MCDA_CRITERIA.copy())
    st.session_state["mcda_scores"] = mcda.get("scores", {})
    st.session_state["weights_user_override"] = mcda.get("weights_user_override", False)
    
    # Import scenarios (convert to proper format)
    scenarios_data = data.get("scenarios", [])
    imported_scenarios = {}
    for scenario in scenarios_data:
        # Find corresponding alt_id from imported alternativas
        alt_name = scenario.get("alternativa", "")
        alt_id = None
        for alt in imported_alts:
            if alt["text"] == alt_name:
                alt_id = alt["id"]
                break
        
        if alt_id:
            imported_scenarios[alt_id] = {
                "name": scenario.get("alternativa", ""),
                "best_desc": scenario.get("best_desc", ""),
                "best_score": scenario.get("best_score", 7.0),
                "worst_desc": scenario.get("worst_desc", ""),
                "worst_score": scenario.get("worst_score", 2.0),
                "p_best": scenario.get("p_best", 0.5),
                "p_best_pct": scenario.get("p_best_pct", 50)
            }
    st.session_state["scenarios"] = imported_scenarios
    
    # Import risks (if present)
    risks_data = data.get("risks", [])
    imported_risks = {}
    for risk in risks_data:
        risk_id = risk.get("id", str(uuid.uuid4()))
        imported_risks[risk_id] = {
            "id": risk_id,
            "title": risk.get("title", ""),
            "probability": risk.get("probability", "medio"),
            "impact": risk.get("impact", "medio"),
            "linked_alt_id": risk.get("linked_alt_id"),
            "strategies": risk.get("strategies", {
                "avoid": "",
                "transfer": "",
                "mitigate": "",
                "contingency": ""
            }),
            "notes": risk.get("notes", ""),
            "status": risk.get("status", "identificado"),
            "created_at": risk.get("created_at"),
            "assessments": risk.get("assessments", [])
        }
    st.session_state["risks"] = imported_risks
    
    # Import no_negociables (if present)
    no_neg_data = data.get("no_negociables", {})
    if isinstance(no_neg_data, dict):
        # New format with constraints and scores
        imported_no_negociables = []
        for constraint in no_neg_data.get("constraints", []):
            imported_no_negociables.append({
                "id": constraint.get("id", str(uuid.uuid4())),
                "text": constraint.get("text", "")
            })
        st.session_state["no_negociables"] = imported_no_negociables
        st.session_state["no_negociables_scores"] = no_neg_data.get("scores", {})
    else:
        # Default empty state for backward compatibility
        st.session_state["no_negociables"] = []
        st.session_state["no_negociables_scores"] = {}
    
    # Import retro (if present)
    retro_data = data.get("retro", {})
    parsed_decision_date = parse_date_string(retro_data.get("decision_date"))
    parsed_review_date = parse_date_string(retro_data.get("review_date"))
    imported_retro = {
        "decision_date": parsed_decision_date,
        "review_date": parsed_review_date,
        "chosen_alternative_id": retro_data.get("chosen_alternative_id"),
        "outcomes": retro_data.get("outcomes", []),
        "tripwires": retro_data.get("tripwires", []),
        "lessons_learned": retro_data.get("lessons_learned", ""),
        "decision_quality_score": retro_data.get("decision_quality_score", 3),
        "outcome_quality_score": retro_data.get("outcome_quality_score", 3)
    }
    st.session_state["retro"] = imported_retro
    
    # Sync widget keys for retro dates (Streamlit widgets with keys read from session_state)
    if parsed_decision_date:
        st.session_state["retro_decision_date"] = parsed_decision_date
    if parsed_review_date:
        st.session_state["retro_review_date"] = parsed_review_date
    
    # Handle routing if requested (for use from app_with_routing.py)
    # Note: redirect_to_first_tab disabled - users prefer staying on current view
    # if show_redirect_message:
    #     st.session_state["redirect_to_first_tab"] = True
    
    if navigate_to_app:
        st.session_state["current_page"] = "app"


def create_filename_slug(text: str) -> str:
    """Create a safe filename slug from text."""
    text = (text or "").strip().lower()
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_ "
    text = "".join(ch if ch.lower() in allowed else "-" for ch in text)
    text = "-".join(text.split())
    return text[:60] or "decision"


def create_excel_export() -> BytesIO:
    """Create Excel export from current session state."""
    export_data = create_export_data()
    if not export_data:
        return None
    
    # Create Excel file in memory
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Overview sheet
        tiempo_data = export_data.get('asignacion_tiempo', {})
        mcda_data = export_data.get('mcda', {})
        overview_data = {
            'Campo': ['Decisión', 'Estrategia Corporativa', 'Objetivo', 'Tiempo Asignado', 'Tiempo Manual', 'Pesos Manual', 'Exportado'],
            'Valor': [
                export_data.get('decision', ''),
                export_data.get('estrategia_corporativa', ''),
                export_data.get('objetivo', ''),
                tiempo_data.get('tiempo', ''),
                'Sí' if tiempo_data.get('tiempo_user_override', False) else 'No',
                'Sí' if mcda_data.get('weights_user_override', False) else 'No',
                export_data.get('meta', {}).get('exported_at', '')
            ]
        }
        pd.DataFrame(overview_data).to_excel(writer, sheet_name='Resumen', index=False)
        
        # Impact assessment sheet
        impact_data = export_data.get('impacto', {})
        impact_df = pd.DataFrame({
            'Plazo': ['Corto', 'Medio', 'Largo'],
            'Impacto': [impact_data.get('corto', ''), impact_data.get('medio', ''), impact_data.get('largo', '')]
        })
        impact_df.to_excel(writer, sheet_name='Impacto', index=False)
        
        # Alternatives sheet
        alternatives = export_data.get('alternativas', [])
        if alternatives:
            alt_df = pd.DataFrame(alternatives)
            alt_df.to_excel(writer, sheet_name='Alternativas', index=False)
        
        # Priorities sheet
        priorities = export_data.get('prioridades', [])
        if priorities:
            prio_df = pd.DataFrame(priorities)
            prio_df.to_excel(writer, sheet_name='Prioridades', index=False)
        
        # Information sheets
        info = export_data.get('informacion', {})
        
        # Past Decisions
        past_decisions = info.get('past_decisions', [])
        if past_decisions:
            past_df = pd.DataFrame(past_decisions)
            past_df.to_excel(writer, sheet_name='Decisiones_Pasadas', index=False)
        
        # KPIs
        kpis = info.get('kpis', [])
        if kpis:
            kpi_df = pd.DataFrame(kpis)
            kpi_df.to_excel(writer, sheet_name='KPIs', index=False)
        
        # Timeline
        timeline = info.get('timeline_items', [])
        if timeline:
            timeline_df = pd.DataFrame(timeline)
            timeline_df.to_excel(writer, sheet_name='Timeline', index=False)
        
        # Stakeholders
        stakeholders = info.get('stakeholders', [])
        if stakeholders:
            stake_df = pd.DataFrame(stakeholders)
            stake_df.to_excel(writer, sheet_name='Stakeholders', index=False)
        
        # Notes
        notes_data = {
            'Tipo': ['Cuantitativas', 'Cualitativas'],
            'Notas': [
                info.get('quantitative_notes', ''),
                info.get('qualitative_notes', '')
            ]
        }
        notes_df = pd.DataFrame(notes_data)
        notes_df.to_excel(writer, sheet_name='Notas', index=False)
        
        # MCDA sheet
        mcda = export_data.get('mcda', {})
        criteria = mcda.get('criteria', [])
        if criteria:
            criteria_df = pd.DataFrame(criteria)
            criteria_df.to_excel(writer, sheet_name='MCDA_Criterios', index=False)
        
        # MCDA Scores
        scores_table = mcda.get('scores_table', {})
        if isinstance(scores_table, dict) and 'data' in scores_table:
            # Reconstruct DataFrame with proper index (alternatives)
            scores_df = pd.DataFrame(scores_table['data'])
            if 'index' in scores_table and not scores_df.empty:
                scores_df.index = scores_table['index']
                scores_df.to_excel(writer, sheet_name='MCDA_Puntuaciones', index=True)
            elif not scores_df.empty:
                scores_df.to_excel(writer, sheet_name='MCDA_Puntuaciones', index=False)
        
        # Scenarios sheet
        scenarios = export_data.get('scenarios', [])
        if scenarios:
            scenarios_df = pd.DataFrame(scenarios)
            scenarios_df.to_excel(writer, sheet_name='Escenarios', index=False)
        
        # No Negociables sheet
        no_neg = export_data.get('no_negociables', {})
        no_neg_constraints = no_neg.get('constraints', [])
        if no_neg_constraints:
            no_neg_df = pd.DataFrame(no_neg_constraints)
            no_neg_df.to_excel(writer, sheet_name='No_Negociables', index=False)
            
            # No Negociables Scores sheet (which alternatives meet which constraints)
            no_neg_scores = no_neg.get('scores', {})
            if no_neg_scores:
                scores_flat = []
                alts = export_data.get('alternativas', [])
                alt_id_to_name = {a['id']: a['text'] for a in alts}
                constraint_id_to_text = {c['id']: c['text'] for c in no_neg_constraints}
                
                for alt_id, constraint_scores in no_neg_scores.items():
                    alt_name = alt_id_to_name.get(alt_id, alt_id)
                    for constraint_id, meets in constraint_scores.items():
                        constraint_text = constraint_id_to_text.get(constraint_id, constraint_id)
                        scores_flat.append({
                            'alternativa': alt_name,
                            'constraint': constraint_text,
                            'cumple': 'Sí' if meets else 'No'
                        })
                if scores_flat:
                    scores_df = pd.DataFrame(scores_flat)
                    scores_df.to_excel(writer, sheet_name='No_Negociables_Eval', index=False)
        
        # Risks sheet
        risks = export_data.get('risks', [])
        if risks:
            # Flatten strategies for Excel
            risks_flat = []
            for risk in risks:
                strategies = risk.get('strategies', {})
                risks_flat.append({
                    'id': risk.get('id', ''),
                    'title': risk.get('title', ''),
                    'category': risk.get('category', ''),
                    'probability': risk.get('probability', ''),
                    'impact': risk.get('impact', ''),
                    'linked_alt_id': risk.get('linked_alt_id', ''),
                    'owner': risk.get('owner', ''),
                    'status': risk.get('status', ''),
                    'created_at': risk.get('created_at', ''),
                    'strategy_avoid': strategies.get('avoid', ''),
                    'strategy_transfer': strategies.get('transfer', ''),
                    'strategy_mitigate': strategies.get('mitigate', ''),
                    'strategy_contingency': strategies.get('contingency', ''),
                    'notes': risk.get('notes', '')
                })
            risks_df = pd.DataFrame(risks_flat)
            risks_df.to_excel(writer, sheet_name='Riesgos', index=False)
            
            # Risk Assessments sheet (time-series evaluations)
            assessments_flat = []
            for risk in risks:
                risk_id = risk.get('id', '')
                risk_title = risk.get('title', '')
                for assessment in risk.get('assessments', []):
                    assessments_flat.append({
                        'risk_id': risk_id,
                        'risk_title': risk_title,
                        'date': assessment.get('date', ''),
                        'probability': assessment.get('probability', ''),
                        'impact': assessment.get('impact', '')
                    })
            if assessments_flat:
                assessments_df = pd.DataFrame(assessments_flat)
                assessments_df.to_excel(writer, sheet_name='Riesgos_Evaluaciones', index=False)
        
        # Retro sheet
        retro = export_data.get('retro', {})
        if retro:
            # Main retro data
            retro_main = {
                'Campo': ['decision_date', 'review_date', 'chosen_alternative_id', 
                         'lessons_learned', 'decision_quality_score', 'outcome_quality_score'],
                'Valor': [
                    retro.get('decision_date', ''),
                    retro.get('review_date', ''),
                    retro.get('chosen_alternative_id', ''),
                    retro.get('lessons_learned', ''),
                    retro.get('decision_quality_score', 3),
                    retro.get('outcome_quality_score', 3)
                ]
            }
            pd.DataFrame(retro_main).to_excel(writer, sheet_name='Retro_Resumen', index=False)
            
            # Outcomes
            outcomes = retro.get('outcomes', [])
            if outcomes:
                outcomes_df = pd.DataFrame(outcomes)
                outcomes_df.to_excel(writer, sheet_name='Retro_Resultados', index=False)
            
            # Tripwires
            tripwires = retro.get('tripwires', [])
            if tripwires:
                tripwires_df = pd.DataFrame(tripwires)
                tripwires_df.to_excel(writer, sheet_name='Retro_Tripwires', index=False)
    
    output.seek(0)
    return output


def import_excel_data(excel_file) -> Tuple[bool, str]:
    """Import data from Excel file."""
    try:
        # Read all sheets
        excel_data = pd.read_excel(excel_file, sheet_name=None)
        
        # Clear existing session state (preserve Streamlit internal keys)
        keys_to_preserve = {k for k in st.session_state.keys() if k.startswith('_') or k in ['current_page', 'show_sidebar']}
        keys_to_clear = set(st.session_state.keys()) - keys_to_preserve
        for key in keys_to_clear:
            del st.session_state[key]
        
        # Initialize defaults
        initialize_session_defaults()
        
        # Import overview data
        if 'Resumen' in excel_data:
            overview = excel_data['Resumen']
            if not overview.empty:
                for _, row in overview.iterrows():
                    campo = row.get('Campo', '')
                    valor = row.get('Valor', '')
                    if campo == 'Decisión':
                        st.session_state['decision'] = str(valor) if pd.notna(valor) else ''
                    elif campo == 'Estrategia Corporativa':
                        st.session_state['estrategia_corporativa'] = str(valor) if pd.notna(valor) else ''
                    elif campo == 'Objetivo':
                        st.session_state['objetivo'] = str(valor) if pd.notna(valor) else ''
                    elif campo == 'Tiempo Asignado':
                        st.session_state['tiempo'] = str(valor) if pd.notna(valor) else 'Menos de media hora'
                    elif campo == 'Tiempo Manual':
                        st.session_state['tiempo_user_override'] = str(valor).lower() in ['sí', 'si', 'yes', 'true', '1'] if pd.notna(valor) else False
                    elif campo == 'Pesos Manual':
                        st.session_state['weights_user_override'] = str(valor).lower() in ['sí', 'si', 'yes', 'true', '1'] if pd.notna(valor) else False
        
        # Import impact data
        if 'Impacto' in excel_data:
            impact = excel_data['Impacto']
            if not impact.empty:
                for _, row in impact.iterrows():
                    plazo = row.get('Plazo', '').lower()
                    impacto = row.get('Impacto', '')
                    if plazo == 'corto':
                        st.session_state['impacto_corto'] = str(impacto) if pd.notna(impacto) else 'bajo'
                    elif plazo == 'medio':
                        st.session_state['impacto_medio'] = str(impacto) if pd.notna(impacto) else 'medio'
                    elif plazo == 'largo':
                        st.session_state['impacto_largo'] = str(impacto) if pd.notna(impacto) else 'bajo'
        
        # Import alternatives
        if 'Alternativas' in excel_data:
            alternatives = excel_data['Alternativas']
            if not alternatives.empty:
                alts = []
                for _, row in alternatives.iterrows():
                    alt_id = row.get('id', str(uuid.uuid4()))
                    text = row.get('text', '')
                    if pd.notna(text) and str(text).strip():
                        alts.append({'id': str(alt_id), 'text': str(text).strip()})
                st.session_state['alts'] = alts
        
        # Import priorities
        if 'Prioridades' in excel_data:
            priorities = excel_data['Prioridades']
            if not priorities.empty:
                prios = []
                for _, row in priorities.iterrows():
                    prio_id = row.get('id', str(uuid.uuid4()))
                    text = row.get('text', '')
                    if pd.notna(text) and str(text).strip():
                        prios.append({'id': str(prio_id), 'text': str(text).strip()})
                st.session_state['priorities'] = prios
        
        # Import KPIs
        if 'KPIs' in excel_data:
            kpis = excel_data['KPIs']
            if not kpis.empty:
                kpi_list = []
                for _, row in kpis.iterrows():
                    kpi_id = row.get('id', str(uuid.uuid4()))
                    name = row.get('name', '')
                    value = row.get('value', '')
                    unit = row.get('unit', '')
                    if pd.notna(name) and str(name).strip():
                        kpi_list.append({
                            'id': str(kpi_id),
                            'name': str(name).strip(),
                            'value': str(value) if pd.notna(value) else '',
                            'unit': str(unit) if pd.notna(unit) else ''
                        })
                st.session_state['kpis'] = kpi_list
        
        # Import Timeline
        if 'Timeline' in excel_data:
            timeline = excel_data['Timeline']
            if not timeline.empty:
                timeline_list = []
                for _, row in timeline.iterrows():
                    item_id = row.get('id', str(uuid.uuid4()))
                    event = row.get('event', '')
                    date_val = row.get('date', None)
                    if pd.notna(event) and str(event).strip():
                        # Parse date
                        parsed_date = None
                        if pd.notna(date_val):
                            parsed_date = parse_date_string(str(date_val))
                        timeline_list.append({
                            'id': str(item_id),
                            'event': str(event).strip(),
                            'date': parsed_date
                        })
                st.session_state['timeline_items'] = timeline_list
        
        # Import Stakeholders
        if 'Stakeholders' in excel_data:
            stakeholders = excel_data['Stakeholders']
            if not stakeholders.empty:
                stakeholder_list = []
                for _, row in stakeholders.iterrows():
                    item_id = row.get('id', str(uuid.uuid4()))
                    name = row.get('name', '')
                    opinion = row.get('opinion', '')
                    if pd.notna(name) and str(name).strip():
                        stakeholder_list.append({
                            'id': str(item_id),
                            'name': str(name).strip(),
                            'opinion': str(opinion).strip() if pd.notna(opinion) else ''
                        })
                st.session_state['stakeholders'] = stakeholder_list
        
        # Import Past Decisions
        if 'Decisiones_Pasadas' in excel_data:
            past_decisions = excel_data['Decisiones_Pasadas']
            if not past_decisions.empty:
                past_list = []
                for _, row in past_decisions.iterrows():
                    item_id = row.get('id', str(uuid.uuid4()))
                    decision = row.get('decision', '')
                    results = row.get('results', '')
                    lessons = row.get('lessons', '')
                    if pd.notna(decision) and str(decision).strip():
                        past_list.append({
                            'id': str(item_id),
                            'decision': str(decision).strip(),
                            'results': str(results).strip() if pd.notna(results) else '',
                            'lessons': str(lessons).strip() if pd.notna(lessons) else ''
                        })
                st.session_state['past_decisions'] = past_list
        
        # Import Notes
        if 'Notas' in excel_data:
            notes = excel_data['Notas']
            if not notes.empty:
                for _, row in notes.iterrows():
                    tipo = row.get('Tipo', '')
                    nota = row.get('Notas', '')
                    if pd.notna(tipo):
                        tipo_str = str(tipo).lower()
                        nota_str = str(nota).strip() if pd.notna(nota) else ''
                        if 'cuantitativa' in tipo_str:
                            st.session_state['quantitative_notes'] = nota_str
                        elif 'cualitativa' in tipo_str:
                            st.session_state['qualitative_notes'] = nota_str
        
        # Import MCDA criteria
        if 'MCDA_Criterios' in excel_data:
            criteria = excel_data['MCDA_Criterios']
            if not criteria.empty:
                crit_list = []
                for _, row in criteria.iterrows():
                    name = row.get('name', '')
                    weight = row.get('weight', 0.5)
                    if pd.notna(name) and str(name).strip():
                        crit_list.append({
                            'name': str(name).strip(),
                            'weight': float(weight) if pd.notna(weight) else 0.5
                        })
                if crit_list:
                    st.session_state['mcda_criteria'] = crit_list
        
        # Import MCDA scores (the missing piece!)
        if 'MCDA_Puntuaciones' in excel_data:
            scores_df = excel_data['MCDA_Puntuaciones']
            if not scores_df.empty:
                # Handle both indexed and non-indexed formats
                if scores_df.index.name is None and len(scores_df.columns) > 0:
                    # If first column looks like alternatives, set it as index
                    first_col = scores_df.columns[0]
                    if first_col == 'Unnamed: 0' or not any(col in ['Prioridad', 'Criterio'] for col in [first_col]):
                        scores_df = scores_df.set_index(scores_df.columns[0])
                
                # Store the DataFrame directly
                st.session_state['mcda_scores_df'] = scores_df
                
                # Convert to the dictionary format used by the evaluation component
                mcda_scores = {}
                for alt_name in scores_df.index:
                    mcda_scores[str(alt_name)] = {}
                    for criterion in scores_df.columns:
                        score = scores_df.loc[alt_name, criterion]
                        if pd.notna(score):
                            mcda_scores[str(alt_name)][str(criterion)] = float(score)
                
                st.session_state['mcda_scores'] = mcda_scores
        
        # Import scenarios (the missing piece!)
        if 'Escenarios' in excel_data:
            scenarios_df = excel_data['Escenarios']
            if not scenarios_df.empty:
                imported_scenarios = {}
                
                # Get current alternatives to match scenario names to IDs
                current_alts = st.session_state.get('alts', [])
                alt_name_to_id = {alt['text'].strip(): alt['id'] for alt in current_alts if alt['text'].strip()}
                
                for _, row in scenarios_df.iterrows():
                    alt_name = row.get('alternativa', '')
                    if pd.notna(alt_name) and str(alt_name).strip():
                        alt_name = str(alt_name).strip()
                        alt_id = alt_name_to_id.get(alt_name)
                        
                        if alt_id:
                            # Extract scenario data from Excel row
                            worst_desc = row.get('worst_desc', '')
                            best_desc = row.get('best_desc', '')
                            worst_score = row.get('worst_score', 2.0)
                            best_score = row.get('best_score', 7.0)
                            p_best = row.get('p_best', 0.5)
                            p_best_pct = row.get('p_best_pct', 50)
                            
                            imported_scenarios[alt_id] = {
                                'name': alt_name,
                                'worst_desc': str(worst_desc) if pd.notna(worst_desc) else '',
                                'best_desc': str(best_desc) if pd.notna(best_desc) else '',
                                'worst_score': float(worst_score) if pd.notna(worst_score) else 2.0,
                                'best_score': float(best_score) if pd.notna(best_score) else 7.0,
                                'p_best': float(p_best) if pd.notna(p_best) else 0.5,
                                'p_best_pct': int(float(p_best_pct)) if pd.notna(p_best_pct) else 50
                            }
                
                if imported_scenarios:
                    st.session_state['scenarios'] = imported_scenarios
        
        # Import Risks
        if 'Riesgos' in excel_data:
            risks_df = excel_data['Riesgos']
            if not risks_df.empty:
                imported_risks = {}
                for _, row in risks_df.iterrows():
                    risk_id = row.get('id', str(uuid.uuid4()))
                    if pd.notna(row.get('title', '')) and str(row.get('title', '')).strip():
                        imported_risks[str(risk_id)] = {
                            'id': str(risk_id),
                            'title': str(row.get('title', '')).strip(),
                            'category': str(row.get('category', 'técnico')) if pd.notna(row.get('category')) else 'técnico',
                            'probability': str(row.get('probability', 'medio')) if pd.notna(row.get('probability')) else 'medio',
                            'impact': str(row.get('impact', 'medio')) if pd.notna(row.get('impact')) else 'medio',
                            'linked_alt_id': str(row.get('linked_alt_id', '')) if pd.notna(row.get('linked_alt_id')) else None,
                            'owner': str(row.get('owner', '')) if pd.notna(row.get('owner')) else '',
                            'status': str(row.get('status', 'identificado')) if pd.notna(row.get('status')) else 'identificado',
                            'created_at': str(row.get('created_at', '')) if pd.notna(row.get('created_at')) else None,
                            'strategies': {
                                'avoid': str(row.get('strategy_avoid', '')) if pd.notna(row.get('strategy_avoid')) else '',
                                'transfer': str(row.get('strategy_transfer', '')) if pd.notna(row.get('strategy_transfer')) else '',
                                'mitigate': str(row.get('strategy_mitigate', '')) if pd.notna(row.get('strategy_mitigate')) else '',
                                'contingency': str(row.get('strategy_contingency', '')) if pd.notna(row.get('strategy_contingency')) else ''
                            },
                            'notes': str(row.get('notes', '')) if pd.notna(row.get('notes')) else '',
                            'assessments': []  # Will be populated from Riesgos_Evaluaciones sheet
                        }
                # Import Risk Assessments (time-series evaluations)
                if 'Riesgos_Evaluaciones' in excel_data:
                    assessments_df = excel_data['Riesgos_Evaluaciones']
                    if not assessments_df.empty:
                        for _, row in assessments_df.iterrows():
                            risk_id = str(row.get('risk_id', ''))
                            if risk_id and risk_id in imported_risks:
                                assessment = {
                                    'date': str(row.get('date', '')) if pd.notna(row.get('date')) else '',
                                    'probability': str(row.get('probability', 'medio')) if pd.notna(row.get('probability')) else 'medio',
                                    'impact': str(row.get('impact', 'medio')) if pd.notna(row.get('impact')) else 'medio'
                                }
                                if 'assessments' not in imported_risks[risk_id]:
                                    imported_risks[risk_id]['assessments'] = []
                                imported_risks[risk_id]['assessments'].append(assessment)
                
                if imported_risks:
                    st.session_state['risks'] = imported_risks
        
        # Also check for assessments sheet even if Riesgos sheet wasn't present
        elif 'Riesgos_Evaluaciones' in excel_data:
            # Assessments without main risks sheet - skip (need risk definitions first)
            pass
        
        # Import No Negociables
        if 'No_Negociables' in excel_data:
            no_neg_df = excel_data['No_Negociables']
            if not no_neg_df.empty:
                imported_no_negociables = []
                for _, row in no_neg_df.iterrows():
                    constraint_id = row.get('id', str(uuid.uuid4()))
                    text = row.get('text', '')
                    if pd.notna(text) and str(text).strip():
                        imported_no_negociables.append({
                            'id': str(constraint_id),
                            'text': str(text).strip()
                        })
                st.session_state['no_negociables'] = imported_no_negociables
                
                # Import No Negociables scores (evaluation)
                if 'No_Negociables_Eval' in excel_data and imported_no_negociables:
                    eval_df = excel_data['No_Negociables_Eval']
                    if not eval_df.empty:
                        # Build reverse mappings: name -> id
                        current_alts = st.session_state.get('alts', [])
                        alt_name_to_id = {alt['text'].strip(): alt['id'] for alt in current_alts if alt['text'].strip()}
                        constraint_text_to_id = {c['text'].strip(): c['id'] for c in imported_no_negociables if c['text'].strip()}
                        
                        no_neg_scores = {}
                        for _, row in eval_df.iterrows():
                            alt_name = str(row.get('alternativa', '')).strip() if pd.notna(row.get('alternativa')) else ''
                            constraint_text = str(row.get('constraint', '')).strip() if pd.notna(row.get('constraint')) else ''
                            cumple_val = str(row.get('cumple', 'No')).strip() if pd.notna(row.get('cumple')) else 'No'
                            
                            alt_id = alt_name_to_id.get(alt_name)
                            constraint_id = constraint_text_to_id.get(constraint_text)
                            
                            if alt_id and constraint_id:
                                if alt_id not in no_neg_scores:
                                    no_neg_scores[alt_id] = {}
                                no_neg_scores[alt_id][constraint_id] = cumple_val.lower() in ['sí', 'si', 'yes', 'true', '1']
                        
                        st.session_state['no_negociables_scores'] = no_neg_scores
        
        # Import Retro
        imported_retro = {
            'decision_date': None,
            'review_date': None,
            'chosen_alternative_id': None,
            'outcomes': [],
            'tripwires': [],
            'lessons_learned': '',
            'decision_quality_score': 3,
            'outcome_quality_score': 3
        }
        
        if 'Retro_Resumen' in excel_data:
            retro_df = excel_data['Retro_Resumen']
            if not retro_df.empty:
                for _, row in retro_df.iterrows():
                    campo = row.get('Campo', '')
                    valor = row.get('Valor', '')
                    if campo == 'decision_date' and pd.notna(valor):
                        imported_retro['decision_date'] = parse_date_string(str(valor))
                    elif campo == 'review_date' and pd.notna(valor):
                        imported_retro['review_date'] = parse_date_string(str(valor))
                    elif campo == 'chosen_alternative_id' and pd.notna(valor):
                        imported_retro['chosen_alternative_id'] = str(valor)
                    elif campo == 'lessons_learned' and pd.notna(valor):
                        imported_retro['lessons_learned'] = str(valor)
                    elif campo == 'decision_quality_score' and pd.notna(valor):
                        imported_retro['decision_quality_score'] = int(float(valor))
                    elif campo == 'outcome_quality_score' and pd.notna(valor):
                        imported_retro['outcome_quality_score'] = int(float(valor))
        
        if 'Retro_Resultados' in excel_data:
            outcomes_df = excel_data['Retro_Resultados']
            if not outcomes_df.empty:
                outcomes = []
                for _, row in outcomes_df.iterrows():
                    outcomes.append({
                        'id': str(row.get('id', str(uuid.uuid4()))),
                        'description': str(row.get('description', '')) if pd.notna(row.get('description')) else '',
                        'date': str(row.get('date', '')) if pd.notna(row.get('date')) else None,
                        'attribution': str(row.get('attribution', 'mixto')) if pd.notna(row.get('attribution')) else 'mixto',
                        'attribution_notes': str(row.get('attribution_notes', '')) if pd.notna(row.get('attribution_notes')) else '',
                        'sentiment': str(row.get('sentiment', 'neutral')) if pd.notna(row.get('sentiment')) else 'neutral'
                    })
                imported_retro['outcomes'] = outcomes
        
        if 'Retro_Tripwires' in excel_data:
            tripwires_df = excel_data['Retro_Tripwires']
            if not tripwires_df.empty:
                tripwires = []
                for _, row in tripwires_df.iterrows():
                    tripwires.append({
                        'id': str(row.get('id', str(uuid.uuid4()))),
                        'trigger': str(row.get('trigger', '')) if pd.notna(row.get('trigger')) else '',
                        'target_date': str(row.get('target_date', '')) if pd.notna(row.get('target_date')) else None,
                        'threshold': str(row.get('threshold', '')) if pd.notna(row.get('threshold')) else '',
                        'status': str(row.get('status', 'activo')) if pd.notna(row.get('status')) else 'activo',
                        'triggered_date': str(row.get('triggered_date', '')) if pd.notna(row.get('triggered_date')) else None,
                        'action_taken': str(row.get('action_taken', '')) if pd.notna(row.get('action_taken')) else ''
                    })
                imported_retro['tripwires'] = tripwires
        
        st.session_state['retro'] = imported_retro
        
        # Sync widget keys for retro dates (same fix as JSON import)
        if imported_retro.get('decision_date'):
            st.session_state['retro_decision_date'] = imported_retro['decision_date']
        if imported_retro.get('review_date'):
            st.session_state['retro_review_date'] = imported_retro['review_date']
        
        # Note: redirect_to_first_tab disabled - users prefer staying on current view
        # st.session_state["redirect_to_first_tab"] = True
        
        return True, "Datos importados exitosamente desde Excel"
        
    except Exception as e:
        return False, f"Error al importar Excel: {str(e)}"

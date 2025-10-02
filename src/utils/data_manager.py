# -*- coding: utf-8 -*-
"""
Data management utilities for Lambda Pro.
Handles session state, export/import, and data validation.
"""

import json
import uuid
import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

from config.constants import DEFAULT_MCDA_CRITERIA, APP_NAME


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
        
        # Escenarios
        "scenarios": {},  # {alt_id: scenario_data}
    }
    
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def validate_json_structure(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate that JSON has the expected structure from this app - exact original validation."""
    required_keys = ["meta", "decision", "impacto", "alternativas", "asignacion_tiempo", 
                   "objetivo", "prioridades", "informacion", "mcda", "scenarios"]
    # Note: "estrategia_corporativa" is optional for backward compatibility
    
    # Check top-level structure
    for key in required_keys:
        if key not in data:
            return False, f"Falta la clave requerida: '{key}'"
    
    # Check meta information
    if not isinstance(data.get("meta"), dict):
        return False, "Estructura 'meta' inválida"
    
    if data["meta"].get("app") != "Lambda Pro":
        return False, f"Este JSON no es de Lambda Pro (app: {data['meta'].get('app')})"
    
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
            "version": "0.2.0",
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
        },
        "scenarios": scenario_rows,
    }
    
    return export_data


def import_json_data(data: Dict[str, Any]) -> None:
    """Import JSON data into session state, clearing existing data."""
    
    # Clear existing session state (preserve Streamlit internal keys)
    keys_to_preserve = [k for k in st.session_state.keys() if k.startswith('FormSubmitter:')]
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


def create_filename_slug(text: str) -> str:
    """Create a safe filename slug from text."""
    text = (text or "").strip().lower()
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789-_ "
    text = "".join(ch if ch.lower() in allowed else "-" for ch in text)
    text = "-".join(text.split())
    return text[:60] or "decision"

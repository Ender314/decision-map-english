# -*- coding: utf-8 -*-
"""
Decision templates for Decision Map.
Pre-populated templates to help users get started quickly and understand the app.
"""

import streamlit as st
import uuid
from datetime import date, timedelta
from typing import Dict, List, Any


_TEMPLATE_TIME_MAP = {
    "menos de media hora": "Less than 30 minutes",
    "un par de horas": "A couple of hours",
    "una mañana": "One morning",
    "una manana": "One morning",
    "un par de días": "A couple of days",
    "un par de dias": "A couple of days",
}

_TEMPLATE_IMPACT_MAP = {
    "bajo": "low",
    "medio": "medium",
    "alto": "high",
    "crítico": "critical",
    "critico": "critical",
}


def _normalize_template_time(value: str) -> str:
    key = str(value or "").strip().lower()
    return _TEMPLATE_TIME_MAP.get(key, value)


def _normalize_template_impact(value: str) -> str:
    key = str(value or "").strip().lower()
    return _TEMPLATE_IMPACT_MAP.get(key, value)


def _new_template_tree_node(label: str, probability: int, score: float, node_type: str = "scenario", alt_id: str = None) -> Dict[str, Any]:
    """Create a tree node for template-driven scenarios initialization."""
    return {
        "id": str(uuid.uuid4()),
        "label": label,
        "probability": int(probability),
        "score": float(score),
        "children": [],
        "node_type": node_type,
        "alt_id": alt_id,
    }


def _build_template_decision_tree(objetivo: str, alts: List[Dict[str, str]], scenarios: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Build canonical scenarios_decision_tree from template flat scenarios."""
    root = _new_template_tree_node((objetivo or "Decision")[:50], 100, 0.0, node_type="root", alt_id=None)

    for alt in alts:
        alt_id = alt.get("id")
        alt_name = (alt.get("text") or "").strip()
        if not alt_id or not alt_name:
            continue

        scenario_data = scenarios.get(alt_id, {}) if isinstance(scenarios, dict) else {}
        p_best_pct = int(scenario_data.get("p_best_pct", 50)) if scenario_data else 50
        p_best_pct = max(0, min(100, p_best_pct))
        p_worst_pct = 100 - p_best_pct

        best_score = float(scenario_data.get("best_score", 7.0)) if scenario_data else 7.0
        worst_score = float(scenario_data.get("worst_score", 2.0)) if scenario_data else 2.0

        alt_node = _new_template_tree_node(alt_name, 100, 5.0, node_type="alternative", alt_id=alt_id)
        alt_node["children"] = [
            _new_template_tree_node(
                scenario_data.get("best_desc", "Best scenario") if scenario_data else "Best scenario",
                p_best_pct,
                best_score,
            ),
            _new_template_tree_node(
                scenario_data.get("worst_desc", "Worst scenario") if scenario_data else "Worst scenario",
                p_worst_pct,
                worst_score,
            ),
        ]
        root["children"].append(alt_node)

    return root


# Template definitions with humor
DECISION_TEMPLATES = {
    "hire_vs_outsource": {
        "id": "hire_vs_outsource",
        "name": "Hire or Outsource?",
        "tagline": "Because 'my cousin knows someone' is not a strategy",
        "icon": "👥",
        "category": "Human Resources",
        "tiempo": "A couple of hours",
        "decision": "Decide whether to hire a full-time employee for a key function or outsource to an agency/freelancer.",
        "objetivo": "Cover the operational need while optimizing cost, quality, and long-term flexibility.",
        "impacto": {"corto": "medium", "medio": "high", "largo": "high"},
        "alternativas": [
            "Hire a full-time employee",
            "Outsource to a specialized agency",
            "Work with a long-term freelancer",
            "Do nothing (maintain status quo)",
        ],
        "prioridades": [
            "Total cost (salary + benefits vs invoice)",
            "Quality and consistency of output",
            "Scalability flexibility",
            "Direct control and supervision",
            "Implementation speed",
        ],
        "mcda_scores": {
            "Hire a full-time employee": {
                "Total cost (salary + benefits vs invoice)": 2.0,
                "Quality and consistency of output": 4.0,
                "Scalability flexibility": 2.0,
                "Direct control and supervision": 5.0,
                "Implementation speed": 2.0,
            },
            "Outsource to a specialized agency": {
                "Total cost (salary + benefits vs invoice)": 3.0,
                "Quality and consistency of output": 4.0,
                "Scalability flexibility": 4.5,
                "Direct control and supervision": 2.5,
                "Implementation speed": 4.0,
            },
            "Work with a long-term freelancer": {
                "Total cost (salary + benefits vs invoice)": 4.0,
                "Quality and consistency of output": 3.5,
                "Scalability flexibility": 4.0,
                "Direct control and supervision": 3.0,
                "Implementation speed": 3.5,
            },
            "Do nothing (maintain status quo)": {
                "Total cost (salary + benefits vs invoice)": 5.0,
                "Quality and consistency of output": 2.0,
                "Scalability flexibility": 1.0,
                "Direct control and supervision": 5.0,
                "Implementation speed": 5.0,
            },
        },
        "scenarios": {
            "Hire a full-time employee": {"worst_score": 3, "best_score": 8, "p_best_pct": 60, "worst_desc": "Poor fit and replacement in 6 months", "best_desc": "Becomes a key team performer"},
            "Outsource to a specialized agency": {"worst_score": 4, "best_score": 7, "p_best_pct": 70, "worst_desc": "Mediocre delivery and over-dependency", "best_desc": "Professional output with scalable capacity"},
            "Work with a long-term freelancer": {"worst_score": 2, "best_score": 8, "p_best_pct": 50, "worst_desc": "Freelancer disappears or doubles rates", "best_desc": "Stable and cost-effective partnership"},
            "Do nothing (maintain status quo)": {"worst_score": 1, "best_score": 4, "p_best_pct": 30, "worst_desc": "The issue worsens and hits performance", "best_desc": "Issue resolves itself (unlikely)"},
        },
    },

    "launch_timing": {
        "id": "launch_timing",
        "name": "Launch now vs wait",
        "tagline": "Perfectionism is the enemy of progress... and sleep",
        "icon": "🚀",
        "category": "Product",
        "tiempo": "One morning",
        "decision": "Decide whether to launch now with an MVP or wait for a more complete version.",
        "objetivo": "Maximize launch impact by balancing time-to-market and perceived quality.",
        "impacto": {"corto": "high", "medio": "high", "largo": "medium"},
        "alternativas": [
            "Launch now (MVP)",
            "Wait one more month",
            "Wait three months (full version)",
            "Gradual launch (closed beta)",
        ],
        "prioridades": [
            "Speed to market",
            "Perceived user quality",
            "Early feedback for iteration",
            "Reputational risk",
            "Opportunity cost",
        ],
        "mcda_scores": {
            "Launch now (MVP)": {"Speed to market": 5.0, "Perceived user quality": 2.5, "Early feedback for iteration": 5.0, "Reputational risk": 2.0, "Opportunity cost": 5.0},
            "Wait one more month": {"Speed to market": 3.5, "Perceived user quality": 3.5, "Early feedback for iteration": 3.5, "Reputational risk": 3.5, "Opportunity cost": 3.0},
            "Wait three months (full version)": {"Speed to market": 1.5, "Perceived user quality": 4.5, "Early feedback for iteration": 2.0, "Reputational risk": 4.5, "Opportunity cost": 1.5},
            "Gradual launch (closed beta)": {"Speed to market": 4.0, "Perceived user quality": 3.0, "Early feedback for iteration": 4.5, "Reputational risk": 4.0, "Opportunity cost": 4.0},
        },
        "scenarios": {
            "Launch now (MVP)": {"worst_score": 2, "best_score": 9, "p_best_pct": 45, "worst_desc": "Users disappointed by initial gaps", "best_desc": "Capture momentum and iterate quickly"},
            "Wait one more month": {"worst_score": 4, "best_score": 7, "p_best_pct": 60, "worst_desc": "Competitor launches first", "best_desc": "Stronger launch with better reception"},
            "Wait three months (full version)": {"worst_score": 3, "best_score": 6, "p_best_pct": 50, "worst_desc": "Market shifts and relevance drops", "best_desc": "Polished product, but late"},
            "Gradual launch (closed beta)": {"worst_score": 4, "best_score": 8, "p_best_pct": 65, "worst_desc": "Beta drags and early users churn", "best_desc": "High-value feedback and confident public launch"},
        },
    },

    "job_offer": {
        "id": "job_offer",
        "name": "Accept a job offer",
        "tagline": "Your mom says accept it. Let's see what the data says",
        "icon": "💼",
        "category": "Career",
        "tiempo": "A couple of hours",
        "decision": "Decide whether to accept a new job offer or stay in the current role.",
        "objetivo": "Choose the option that maximizes long-term professional and personal satisfaction.",
        "impacto": {"corto": "high", "medio": "critical", "largo": "critical"},
        "alternativas": [
            "Accept the new offer",
            "Decline and stay",
            "Negotiate better terms",
            "Use offer as leverage internally",
        ],
        "prioridades": [
            "Total compensation",
            "Growth opportunities",
            "Work-life balance",
            "Culture and team environment",
            "Stability and security",
        ],
        "mcda_scores": {
            "Accept the new offer": {"Total compensation": 4.5, "Growth opportunities": 4.0, "Work-life balance": 3.0, "Culture and team environment": 3.0, "Stability and security": 2.5},
            "Decline and stay": {"Total compensation": 3.0, "Growth opportunities": 2.5, "Work-life balance": 4.0, "Culture and team environment": 4.0, "Stability and security": 4.5},
            "Negotiate better terms": {"Total compensation": 4.0, "Growth opportunities": 4.0, "Work-life balance": 3.5, "Culture and team environment": 3.0, "Stability and security": 3.0},
            "Use offer as leverage internally": {"Total compensation": 3.5, "Growth opportunities": 3.0, "Work-life balance": 4.0, "Culture and team environment": 3.5, "Stability and security": 3.5},
        },
        "scenarios": {
            "Accept the new offer": {"worst_score": 2, "best_score": 9, "p_best_pct": 55, "worst_desc": "Poor fit and regret after transition", "best_desc": "Major career acceleration"},
            "Decline and stay": {"worst_score": 3, "best_score": 6, "p_best_pct": 60, "worst_desc": "Stagnation and missed opportunity", "best_desc": "Stability and gradual improvement"},
            "Negotiate better terms": {"worst_score": 3, "best_score": 9, "p_best_pct": 40, "worst_desc": "Offer withdrawn during negotiation", "best_desc": "Better package and stronger role"},
            "Use offer as leverage internally": {"worst_score": 2, "best_score": 7, "p_best_pct": 35, "worst_desc": "Damaged trust with manager", "best_desc": "Competitive counter-offer"},
        },
    },

    "market_expansion": {
        "id": "market_expansion",
        "name": "Expand to a new market",
        "tagline": "Conquer the world, one market at a time",
        "icon": "🌍",
        "category": "Strategy",
        "tiempo": "A couple of days",
        "decision": "Decide whether to expand operations into a new geography or vertical market.",
        "objetivo": "Grow sustainably while minimizing expansion risk.",
        "impacto": {"corto": "medium", "medio": "high", "largo": "critical"},
        "alternativas": [
            "Immediate aggressive expansion",
            "Gradual pilot entry",
            "Partner with a local company",
            "Postpone and consolidate core market",
        ],
        "prioridades": [
            "Revenue potential",
            "Required investment",
            "Operational risk",
            "Time to profitability",
            "Synergy with current business",
        ],
        "mcda_scores": {
            "Immediate aggressive expansion": {"Revenue potential": 5.0, "Required investment": 1.5, "Operational risk": 1.5, "Time to profitability": 2.0, "Synergy with current business": 3.0},
            "Gradual pilot entry": {"Revenue potential": 3.5, "Required investment": 3.5, "Operational risk": 4.0, "Time to profitability": 3.0, "Synergy with current business": 3.5},
            "Partner with a local company": {"Revenue potential": 3.0, "Required investment": 4.0, "Operational risk": 3.5, "Time to profitability": 4.0, "Synergy with current business": 2.5},
            "Postpone and consolidate core market": {"Revenue potential": 2.0, "Required investment": 5.0, "Operational risk": 5.0, "Time to profitability": 5.0, "Synergy with current business": 4.5},
        },
        "scenarios": {
            "Immediate aggressive expansion": {"worst_score": 1, "best_score": 10, "p_best_pct": 30, "worst_desc": "Costly failure impacting core operations", "best_desc": "Rapid market leadership"},
            "Gradual pilot entry": {"worst_score": 3, "best_score": 8, "p_best_pct": 55, "worst_desc": "Inconclusive pilot with wasted resources", "best_desc": "Learn fast and scale with confidence"},
            "Partner with a local company": {"worst_score": 3, "best_score": 7, "p_best_pct": 50, "worst_desc": "Partner execution conflicts", "best_desc": "Fast access with reduced risk"},
            "Postpone and consolidate core market": {"worst_score": 4, "best_score": 6, "p_best_pct": 70, "worst_desc": "Competitor captures the opportunity", "best_desc": "Stronger base for future expansion"},
        },
    },

    "tech_investment": {
        "id": "tech_investment",
        "name": "Invest in technology",
        "tagline": "No, ChatGPT cannot make this decision for you... yet",
        "icon": "💻",
        "category": "Technology",
        "tiempo": "One morning",
        "decision": "Decide whether to invest in a new technology/system for the business.",
        "objetivo": "Improve operational efficiency and competitiveness through a smart tech investment.",
        "impacto": {"corto": "low", "medio": "high", "largo": "high"},
        "alternativas": [
            "Implement full enterprise solution",
            "Adopt existing SaaS tool",
            "Build an internal solution",
            "Maintain current processes",
        ],
        "prioridades": [
            "Total cost of ownership",
            "Implementation speed",
            "Future scalability",
            "Ease of adoption",
            "Support and maintenance",
        ],
        "mcda_scores": {
            "Implement full enterprise solution": {"Total cost of ownership": 1.5, "Implementation speed": 2.0, "Future scalability": 5.0, "Ease of adoption": 2.5, "Support and maintenance": 4.5},
            "Adopt existing SaaS tool": {"Total cost of ownership": 3.5, "Implementation speed": 4.5, "Future scalability": 3.5, "Ease of adoption": 4.0, "Support and maintenance": 4.0},
            "Build an internal solution": {"Total cost of ownership": 2.5, "Implementation speed": 1.5, "Future scalability": 4.0, "Ease of adoption": 3.0, "Support and maintenance": 2.0},
            "Maintain current processes": {"Total cost of ownership": 5.0, "Implementation speed": 5.0, "Future scalability": 1.5, "Ease of adoption": 5.0, "Support and maintenance": 3.0},
        },
        "scenarios": {
            "Implement full enterprise solution": {"worst_score": 2, "best_score": 9, "p_best_pct": 45, "worst_desc": "Failed rollout and cost overrun", "best_desc": "Successful digital transformation"},
            "Adopt existing SaaS tool": {"worst_score": 4, "best_score": 7, "p_best_pct": 65, "worst_desc": "Poor fit and vendor lock-in", "best_desc": "Fast value and productive team"},
            "Build an internal solution": {"worst_score": 1, "best_score": 8, "p_best_pct": 35, "worst_desc": "Never-ending development project", "best_desc": "Tailored high-fit solution"},
            "Maintain current processes": {"worst_score": 2, "best_score": 5, "p_best_pct": 50, "worst_desc": "Obsolescence and lost competitiveness", "best_desc": "Short-term savings"},
        },
    },

    "vendor_change": {
        "id": "vendor_change",
        "name": "Change supplier",
        "tagline": "Because 'we've always done it this way' is not strategy",
        "icon": "🔄",
        "category": "Operations",
        "tiempo": "A couple of hours",
        "decision": "Decide whether to switch to a new supplier or maintain the current relationship.",
        "objetivo": "Optimize the supply chain balancing cost, quality, and transition risk.",
        "impacto": {"corto": "medium", "medio": "medium", "largo": "medium"},
        "alternativas": [
            "Fully switch to new supplier",
            "Keep current supplier",
            "Dual-source with both suppliers",
            "Renegotiate with current supplier",
        ],
        "prioridades": [
            "Pricing and terms",
            "Product/service quality",
            "Delivery reliability",
            "Transition cost",
            "Long-term relationship",
        ],
        "mcda_scores": {
            "Fully switch to new supplier": {"Pricing and terms": 4.5, "Product/service quality": 3.5, "Delivery reliability": 3.0, "Transition cost": 2.0, "Long-term relationship": 2.5},
            "Keep current supplier": {"Pricing and terms": 2.5, "Product/service quality": 4.0, "Delivery reliability": 4.5, "Transition cost": 5.0, "Long-term relationship": 4.0},
            "Dual-source with both suppliers": {"Pricing and terms": 3.5, "Product/service quality": 3.5, "Delivery reliability": 4.0, "Transition cost": 3.0, "Long-term relationship": 3.5},
            "Renegotiate with current supplier": {"Pricing and terms": 3.5, "Product/service quality": 4.0, "Delivery reliability": 4.5, "Transition cost": 4.5, "Long-term relationship": 4.0},
        },
        "scenarios": {
            "Fully switch to new supplier": {"worst_score": 2, "best_score": 8, "p_best_pct": 45, "worst_desc": "Quality and delivery disruptions", "best_desc": "Meaningful savings and stronger service"},
            "Keep current supplier": {"worst_score": 3, "best_score": 5, "p_best_pct": 60, "worst_desc": "Price increases and lock-in", "best_desc": "Stable trusted relationship"},
            "Dual-source with both suppliers": {"worst_score": 3, "best_score": 7, "p_best_pct": 55, "worst_desc": "Operational complexity and hidden costs", "best_desc": "Better leverage and lower disruption risk"},
            "Renegotiate with current supplier": {"worst_score": 3, "best_score": 7, "p_best_pct": 50, "worst_desc": "Negotiation fails and trust erodes", "best_desc": "Improved terms with no migration pain"},
        },
    },
}


def _build_template_monitoring_data(alts: List[Dict[str, str]], template_name: str) -> Dict[str, Any]:
    """Build demo monitoring payload (risks + retro) for templates."""
    today = date.today()
    first_alt_id = alts[0]["id"] if alts else None

    risk_1_id = str(uuid.uuid4())
    risk_2_id = str(uuid.uuid4())

    risks = {
        risk_1_id: {
            "id": risk_1_id,
            "title": "Execution delay due to hidden dependencies",
            "category": "operational",
            "probability": "medium",
            "impact": "high",
            "linked_alt_id": first_alt_id,
            "owner": "Ops Lead",
            "status": "in_treatment",
            "created_at": (today - timedelta(days=20)).isoformat(),
            "strategies": {
                "avoid": "Scope critical path to only must-have tasks.",
                "transfer": "Use external specialist for bottleneck stage.",
                "mitigate": "Weekly dependency review and blocker escalation.",
                "contingency": "Activate fallback plan with reduced rollout scope.",
            },
            "notes": "Main risk for on-time delivery.",
            "assessments": [
                {"date": (today - timedelta(days=20)).isoformat(), "probability": "high", "impact": "high"},
                {"date": (today - timedelta(days=10)).isoformat(), "probability": "medium", "impact": "high"},
            ],
        },
        risk_2_id: {
            "id": risk_2_id,
            "title": "Stakeholder pushback on selected option",
            "category": "strategic",
            "probability": "low",
            "impact": "medium",
            "linked_alt_id": first_alt_id,
            "owner": "Decision Owner",
            "status": "identified",
            "created_at": (today - timedelta(days=12)).isoformat(),
            "strategies": {
                "avoid": "Involve key stakeholders before final commitment.",
                "transfer": "Escalate sponsorship through executive steering group.",
                "mitigate": "Share rationale and scenario evidence transparently.",
                "contingency": "Prepare a phased compromise implementation path.",
            },
            "notes": "Mostly communication and alignment risk.",
            "assessments": [
                {"date": (today - timedelta(days=12)).isoformat(), "probability": "medium", "impact": "medium"},
                {"date": (today - timedelta(days=3)).isoformat(), "probability": "low", "impact": "medium"},
            ],
        },
    }

    retro = {
        "decision_date": (today - timedelta(days=14)),
        "review_date": today,
        "chosen_alternative_id": first_alt_id,
        "outcomes": [
            {
                "id": str(uuid.uuid4()),
                "description": f"Initial implementation for '{template_name}' delivered expected first milestones.",
                "date": (today - timedelta(days=7)).isoformat(),
                "attribution": "decision",
                "attribution_notes": "Early wins came from strong option selection and sequencing.",
                "sentiment": "positive",
            },
            {
                "id": str(uuid.uuid4()),
                "description": "Unexpected external changes slowed one workstream.",
                "date": (today - timedelta(days=2)).isoformat(),
                "attribution": "mixed",
                "attribution_notes": "Part external context, part planning assumptions.",
                "sentiment": "neutral",
            },
        ],
        "tripwires": [
            {
                "id": str(uuid.uuid4()),
                "trigger": "If KPI trend drops > 15% for two consecutive weeks",
                "target_date": (today + timedelta(days=14)).isoformat(),
                "threshold": "KPI delta < -15%",
                "status": "active",
                "triggered_date": None,
                "action_taken": "",
            },
            {
                "id": str(uuid.uuid4()),
                "trigger": "If rollout slippage exceeds 10 business days",
                "target_date": (today - timedelta(days=1)).isoformat(),
                "threshold": "Delay > 10 days",
                "status": "triggered",
                "triggered_date": (today - timedelta(days=1)).isoformat(),
                "action_taken": "Activated reduced-scope fallback and re-baselined timeline.",
            },
        ],
        "lessons_learned": "Strong decisions still need explicit risk checkpoints. Earlier stakeholder alignment reduced friction, but dependency mapping should happen sooner.",
        "decision_quality_score": 4,
        "outcome_quality_score": 3,
    }

    return {"risks": risks, "retro": retro}


def get_template_list() -> List[Dict[str, str]]:
    """Get list of templates for display."""
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "tagline": t["tagline"],
            "icon": t["icon"],
            "category": t["category"]
        }
        for t in DECISION_TEMPLATES.values()
    ]


def load_template(template_id: str) -> bool:
    """
    Load a template into session state.
    Returns True if successful, False otherwise.
    """
    if template_id not in DECISION_TEMPLATES:
        return False
    
    template = DECISION_TEMPLATES[template_id]

    diag_marker = str(uuid.uuid4())
    
    # Clear existing data (preserve system keys)
    keys_to_preserve = [
        k for k in st.session_state.keys()
        if k.startswith('_') or k in ['current_page', 'show_sidebar', 'show_template_selector']
    ]
    current_state = {k: st.session_state[k] for k in keys_to_preserve}
    st.session_state.clear()
    st.session_state.update(current_state)

    # Diagnostic breadcrumbs for post-load tab reset investigation.
    st.session_state["_diag_last_load_source"] = "template"
    st.session_state["_diag_last_load_marker"] = diag_marker
    st.session_state["_diag_post_load_run_index"] = 0
    
    # Load basic data
    st.session_state["decision"] = template["decision"]
    st.session_state["objetivo"] = template["objetivo"]
    st.session_state["tiempo"] = _normalize_template_time(template["tiempo"])
    # Keep loaded template tiempo stable until user explicitly changes it.
    st.session_state["tiempo_user_override"] = True
    st.session_state["tiempo_widget"] = _normalize_template_time(template["tiempo"])
    
    # Load impact
    st.session_state["impacto_corto"] = _normalize_template_impact(template["impacto"]["corto"])
    st.session_state["impacto_medio"] = _normalize_template_impact(template["impacto"]["medio"])
    st.session_state["impacto_largo"] = _normalize_template_impact(template["impacto"]["largo"])
    
    # Load alternatives with IDs
    alts = []
    for alt_text in template["alternativas"]:
        alts.append({"id": str(uuid.uuid4()), "text": alt_text})
    st.session_state["alts"] = alts
    
    # Load priorities with IDs
    priorities = []
    for prio_text in template["prioridades"]:
        priorities.append({"id": str(uuid.uuid4()), "text": prio_text})
    st.session_state["priorities"] = priorities
    
    # Load MCDA criteria (from priorities with position-based weights)
    mcda_criteria = []
    for i, prio in enumerate(template["prioridades"]):
        weight = 1.0 / (i + 1)  # Position-based: 1st=1, 2nd=0.5, etc.
        mcda_criteria.append({"name": prio, "weight": weight})
    st.session_state["mcda_criteria"] = mcda_criteria
    st.session_state["weights_user_override"] = False
    
    # Load MCDA scores
    mcda_scores = {}
    for alt_name, scores in template["mcda_scores"].items():
        mcda_scores[alt_name] = scores
    st.session_state["mcda_scores"] = mcda_scores
    
    # Load scenarios
    scenarios = {}
    for alt in alts:
        alt_name = alt["text"]
        if alt_name in template["scenarios"]:
            scenario_data = template["scenarios"][alt_name]
            scenarios[alt["id"]] = {
                "name": alt_name,
                "worst_desc": scenario_data["worst_desc"],
                "worst_score": float(scenario_data["worst_score"]),
                "best_desc": scenario_data["best_desc"],
                "best_score": float(scenario_data["best_score"]),
                "p_best": scenario_data["p_best_pct"] / 100.0,
                "p_best_pct": scenario_data["p_best_pct"]
            }
    st.session_state["scenarios"] = scenarios

    scenarios_decision_tree = _build_template_decision_tree(
        st.session_state.get("objetivo", "Decision"),
        alts,
        scenarios,
    )
    scenarios_tree_projection = {
        child["alt_id"]: child
        for child in scenarios_decision_tree.get("children", [])
        if child.get("node_type") == "alternative" and child.get("alt_id")
    }

    st.session_state["scenarios_decision_tree"] = scenarios_decision_tree
    st.session_state["scenarios_tree_projection"] = scenarios_tree_projection
    
    # Load monitoring sample data for demo-ready Monitoring tab
    monitoring_data = _build_template_monitoring_data(alts, template["name"])

    # Initialize remaining collections
    st.session_state["kpis"] = []
    st.session_state["timeline_items"] = []
    st.session_state["stakeholders"] = []
    st.session_state["past_decisions"] = []
    st.session_state["quantitative_notes"] = ""
    st.session_state["qualitative_notes"] = ""
    st.session_state["estrategia_corporativa"] = ""
    st.session_state["risks"] = monitoring_data["risks"]
    st.session_state["retro"] = monitoring_data["retro"]
    
    return True


def render_template_selector():
    """Render the template selection modal/UI."""
    st.markdown("### 📋 Decision Templates")
    st.markdown("*Select a template to start with sample data and understand how the app works.*")
    st.markdown("")
    
    templates = get_template_list()
    
    # Display all templates in a 2-column grid
    cols = st.columns(2)
    for i, template in enumerate(templates):
        with cols[i % 2]:
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem; background: var(--secondary-background-color, #f8f9fa);">
                <div style="font-size: 1.5rem; margin-bottom: 0.3rem;">{template['icon']} <span style="font-size: 0.7rem; color: #888;">{template['category']}</span></div>
                <div style="font-weight: 600;">{template['name']}</div>
                <div style="font-size: 0.85rem; color: #666; font-style: italic;">{template['tagline']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Use template", key=f"load_template_{template['id']}", width="stretch"):
                if load_template(template['id']):
                    st.session_state["_template_loaded"] = True
                    st.session_state["_loaded_template_name"] = template['name']
                    st.session_state["show_template_selector"] = False  # Hide menu after selection
                    st.rerun()


def render_template_button_in_sidebar():
    """Render a button to access templates from the sidebar."""
    if st.button("📋 Load Template", width="stretch", help="Load a sample decision template"):
        st.session_state["show_template_selector"] = True
        st.rerun()

# -*- coding: utf-8 -*-
"""
Constants and configuration for Decision Map application.
Centralized source of truth for all application constants.
"""

# Tab names
TAB_DIMENSIONADO = "Sizing"
TAB_ALTERNATIVAS = "Alternatives"
TAB_OBJETIVO = "Objective"
TAB_PRIORIDADES = "Priorities"
TAB_INFO = "Information"
TAB_EVAL = "Evaluation"
TAB_RESULTADOS = "Results"
TAB_SCENARIOS = "Scenarios"
TAB_SCENARIOS_INTERACTIVE = "Interactive Scenarios"
TAB_RIESGOS = "Risks"
TAB_RETRO = "Retrospective"
TAB_INFORME = "Report"

# Tab display names with emojis (for visual display only)
TAB_DISPLAY_NAMES = {
    TAB_DIMENSIONADO: "📏 Sizing",
    TAB_ALTERNATIVAS: "🧭 Alternatives",
    TAB_OBJETIVO: "🎯 Objective",
    TAB_PRIORIDADES: "⭐ Priorities",
    TAB_INFO: "📝 Information",
    TAB_EVAL: "⚖️ Evaluation",
    TAB_RESULTADOS: "📊 Results",
    TAB_SCENARIOS: "🔮 Scenarios",
    TAB_SCENARIOS_INTERACTIVE: "🔀 Interactive Scenarios",
    TAB_RIESGOS: "⚠️ Risks",
    TAB_RETRO: "🔄 Retrospective",
    TAB_INFORME: "📋 Report"
}

# Tab flow configuration - Analysis phase only
ALL_SECTIONS = [
    TAB_DIMENSIONADO, TAB_ALTERNATIVAS, TAB_INFO, TAB_OBJETIVO, TAB_PRIORIDADES,
    TAB_EVAL, TAB_SCENARIOS, TAB_RESULTADOS
]

# Monitoring phase tabs (separate view)
MONITORING_SECTIONS = [TAB_RIESGOS, TAB_RETRO]

# Risk categories for risk analysis
RISK_CATEGORIES = ["technical", "financial", "operational", "external", "strategic"]
RISK_PROBABILITY = ["low", "medium", "high"]
RISK_IMPACT = ["low", "medium", "high", "critical"]
RISK_STATUS = ["identified", "in_treatment", "accepted", "closed"]

# Risk score mapping (probability × impact)
RISK_PROB_MAP = {"low": 1, "medium": 2, "high": 3}
RISK_IMPACT_MAP = {"low": 1, "medium": 2, "high": 3, "critical": 4}

# Outcome attribution options for retrospective
OUTCOME_ATTRIBUTION = ["decision", "luck", "mixed"]
OUTCOME_SENTIMENT = ["positive", "neutral", "negative"]
TRIPWIRE_STATUS = ["active", "triggered", "resolved"]

# Impact assessment
IMPACT_OPTS = ["low", "medium", "high", "critical"]
IMPACT_MAP = {"low": 0, "medium": 5, "high": 10, "critical": 15}
PLAZO_ORDER = ["short", "medium", "long"]
YMAX = max(IMPACT_MAP.values())  # 15

# Time allocation options
TIME_OPTIONS = ["Less than 30 minutes", "A couple of hours", "One morning", "A couple of days"]

# Default MCDA criteria
DEFAULT_MCDA_CRITERIA = [
    {"name": "Strategic impact", "weight": 0.5},
    {"name": "Urgency", "weight": 0.5},
]

# App metadata
APP_NAME = "Decision Map"
APP_VERSION = "1.1.0"
APP_ICON = "🧭"
APP_FILENAME_PREFIX = APP_NAME.lower().replace(" ", "_")  # "decision_map"

# Legacy app names (for import compatibility)
LEGACY_APP_NAMES = ["Decider Pro", "Focal Path Pro", "Lambda Pro"]

# Brand colors
COLOR_PRIMARY = "#1a365d"      # Deep navy - trust, authority
COLOR_ACCENT = "#f6ad55"       # Warm amber - confidence, action
COLOR_SUCCESS = "#38a169"      # Green - positive, high confidence
COLOR_WARNING = "#dd6b20"      # Orange - caution, medium confidence  
COLOR_ERROR = "#e53e3e"        # Red - risk, low confidence
COLOR_INFO = "#3182ce"         # Blue - information
COLOR_NEUTRAL = "#718096"      # Gray - neutral, disabled

# Advanced scenarios constraints
ADV_SCENARIO_MAX_BRANCHES = 3
ADV_SCENARIO_MAX_DEPTH = 3

# Scoring configuration
SCORE_STEPS = [x / 2 for x in range(0, 11)]  # 0, 0.5, 1.0, ..., 5.0
PROBABILITY_STEPS = list(range(0, 101, 5))  # 0, 5, 10, ..., 100
COMPOSITE_DEFAULT_MCDA_WEIGHT_PCT = 60

# Color configuration for visualizations
def get_relevance_color(relevance_pct: float) -> tuple[str, str]:
    """
    Get line and fill colors based on relevance percentage.
    Returns (line_color, fill_color) as RGB strings.
    """
    max_auc = YMAX * 2
    t = 0 if max_auc == 0 else (relevance_pct / 100)
    
    def lerp(a, b, tt): 
        return int(a + (b - a) * tt)
    
    if t <= 0.5:
        t2 = t / 0.5
        r = lerp(0, 255, t2)
        g = lerp(176, 192, t2)
        b = lerp(80, 0, t2)
    else:
        t2 = (t - 0.5) / 0.5
        r = lerp(255, 192, t2)
        g = lerp(192, 0, t2)
        b = 0
    
    line_color = f"rgb({r},{g},{b})"
    fill_color = f"rgba({r},{g},{b},0.35)"
    return line_color, fill_color

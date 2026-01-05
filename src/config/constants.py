# -*- coding: utf-8 -*-
"""
Constants and configuration for Lambda Pro application.
Centralized source of truth for all application constants.
"""

# Tab names
TAB_DIMENSIONADO = "Dimensionado"
TAB_ALTERNATIVAS = "Alternativas"
TAB_OBJETIVO = "Objetivo"
TAB_PRIORIDADES = "Prioridades"
TAB_INFO = "Información"
TAB_EVAL = "Evaluación"
TAB_RESULTADOS = "Resultados"
TAB_SCENARIOS = "Escenarios"

# Tab display names with emojis (for visual display only)
TAB_DISPLAY_NAMES = {
    TAB_DIMENSIONADO: "📏Dimensionado",
    TAB_ALTERNATIVAS: "🧭 Alternativas", 
    TAB_OBJETIVO: "🎯 Objetivo",
    TAB_PRIORIDADES: "⭐ Prioridades",
    TAB_INFO: "📝 Información",
    TAB_EVAL: "⚖️ Evaluación",
    TAB_RESULTADOS: "📊 Resultados",
    TAB_SCENARIOS: "🔮 Escenarios"
}

# Tab flow configuration
ALL_SECTIONS = [
    TAB_DIMENSIONADO, TAB_INFO, TAB_ALTERNATIVAS, TAB_OBJETIVO, TAB_PRIORIDADES,
    TAB_EVAL, TAB_SCENARIOS, TAB_RESULTADOS
]

# Impact assessment
IMPACT_OPTS = ["bajo", "medio", "alto", "crítico"]
IMPACT_MAP = {"bajo": 0, "medio": 5, "alto": 10, "crítico": 15}
PLAZO_ORDER = ["corto", "medio", "largo"]
YMAX = max(IMPACT_MAP.values())  # 15

# Time allocation options
TIME_OPTIONS = ["Menos de media hora", "Un par de horas", "Una mañana", "Un par de días"]

# Default MCDA criteria
DEFAULT_MCDA_CRITERIA = [
    {"name": "Impacto estratégico", "weight": 0.5},
    {"name": "Urgencia", "weight": 0.5},
]

# App metadata
APP_NAME = "Focal Path Pro"
APP_VERSION = "0.2.0"
APP_ICON = "⚡"

# Scoring configuration
SCORE_STEPS = [x / 2 for x in range(0, 11)]  # 0, 0.5, 1.0, ..., 5.0
PROBABILITY_STEPS = list(range(0, 101, 5))  # 0, 5, 10, ..., 100

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

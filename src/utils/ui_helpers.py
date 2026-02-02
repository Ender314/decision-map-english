# -*- coding: utf-8 -*-
"""
UI Helper utilities for Decider Pro.
Provides consistent tooltip styling and contextual help across the app.
"""


def help_tip(text: str) -> str:
    """
    Returns HTML for a subtle help icon with tooltip.
    Use this for inline contextual help throughout the app.
    
    Usage:
        st.markdown(f"Label {help_tip('Explanation here')}", unsafe_allow_html=True)
    """
    # Escape quotes in the text for HTML attribute
    escaped_text = text.replace('"', '&quot;').replace("'", "&#39;")
    return f'<span style="cursor:help; opacity:0.6; font-size:0.9em;" title="{escaped_text}">ⓘ</span>'


def help_label(label: str, tip: str) -> str:
    """
    Returns a label with an inline help icon.
    
    Usage:
        st.markdown(help_label("Impacto", "Diferencia entre mejor y peor escenario"), unsafe_allow_html=True)
    """
    return f'{label} {help_tip(tip)}'


# Predefined tooltips for consistency across the app
TOOLTIPS = {
    # Dimensionado tab
    "impacto": "Impacto = diferencia entre el mejor y peor resultado posible en este plazo temporal",
    "tiempo": "Más tiempo = análisis más profundo. Ajusta según la importancia de la decisión",
    "relevancia": "Calculada automáticamente según el impacto en los tres plazos temporales",
    
    # Alternativas tab
    "alternativas": "Incluye siempre 'no hacer nada' o 'mantener status quo' como alternativa de referencia",
    "alternativa_add": "Añade entre 2 y 5 alternativas para un análisis efectivo",
    
    # Prioridades tab
    "prioridades": "Ordena de más a menos importante. El orden afecta los pesos automáticos en la evaluación",
    "prioridad_orden": "La primera prioridad tiene peso 1, la segunda 0.5, la tercera 0.33, etc.",
    
    # Evaluación tab
    "mcda_score": "0 = muy malo, 5 = excelente. Sé consistente al puntuar entre alternativas",
    "mcda_weights": "Los pesos se normalizan automáticamente para sumar 100%",
    "mcda_ranking": "Ranking basado en puntuación ponderada de todos los criterios",
    
    # Escenarios tab
    "scenario_prob": "¿Qué tan probable es el mejor resultado? 50% = igual de probable que el peor",
    "scenario_range": "Mayor rango = más incertidumbre. Sé honesto sobre lo que no sabes",
    "scenario_ev": "Valor Esperado = probabilidad × mejor + (1-probabilidad) × peor",
    
    # Resultados tab
    "matriz_decision": "Arriba-derecha = óptimo (alto MCDA + alto EV). Tamaño de burbuja = incertidumbre",
    "confianza": "Basado en la ventaja del ganador sobre el segundo y la incertidumbre de los escenarios",
    "composite": "Puntuación compuesta = 50% MCDA + 50% Valor Esperado (ambos en escala 0-5)",
    
    # Riesgos tab
    "risk_score": "Puntuación de riesgo = Probabilidad × Impacto. Mayor puntuación = mayor prioridad",
    "risk_strategies": "Las 4 estrategias clásicas: Evitar, Transferir, Mitigar, Plan de contingencia",
    
    # General
    "export": "Exporta tu análisis para compartirlo o guardarlo. Puedes importarlo después",
}


def get_tooltip(key: str) -> str:
    """Get a predefined tooltip by key."""
    return TOOLTIPS.get(key, "")

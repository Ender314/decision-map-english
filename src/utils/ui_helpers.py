# -*- coding: utf-8 -*-
"""
UI helper utilities for Decision Map.
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
        st.markdown(help_label("Impact", "Difference between best and worst scenario"), unsafe_allow_html=True)
    """
    return f'{label} {help_tip(tip)}'


# Predefined tooltips for consistency across the app
TOOLTIPS = {
    # Sizing tab
    "impacto": "Impact = difference between the best and worst possible outcome in this time horizon",
    "tiempo": "More time = deeper analysis. Adjust based on the importance of this decision",
    "relevancia": "Calculated automatically from impact across short, medium, and long term",
    
    # Alternatives tab
    "alternativas": "Always include 'do nothing' or 'maintain status quo' as a reference alternative",
    "alternativa_add": "Add between 2 and 5 alternatives for effective analysis",
    
    # Priorities tab
    "prioridades": "Order from most to least important. Order affects automatic evaluation weights",
    "prioridad_orden": "The first priority has weight 1, second 0.5, third 0.33, etc.",
    
    # Evaluation tab
    "mcda_score": "0 = very poor, 5 = excellent. Keep scoring consistent across alternatives",
    "mcda_weights": "Weights are automatically normalized to sum to 100%",
    "mcda_ranking": "Ranking based on weighted scores across all criteria",
    
    # Scenarios tab
    "scenario_prob": "How likely is the best outcome? 50% = equally likely as the worst",
    "scenario_range": "Wider range = higher uncertainty. Be honest about what you don't know",
    "scenario_ev": "Expected Value = probability × best + (1-probability) × worst",
    
    # Results tab
    "matriz_decision": "Top-right = optimal (high MCDA + high EV). Bubble size = uncertainty",
    "confianza": "Based on winner margin vs second place and scenario uncertainty",
    "composite": "Composite score = 50% MCDA + 50% Expected Value (both on a 0-5 scale)",
    
    # Risks tab
    "risk_score": "Risk score = Probability × Impact. Higher score = higher priority",
    "risk_strategies": "The 4 classic strategies: Avoid, Transfer, Mitigate, Contingency plan",
    
    # General
    "export": "Export your analysis to share or store it. You can import it later",
}


def get_tooltip(key: str) -> str:
    """Get a predefined tooltip by key."""
    return TOOLTIPS.get(key, "")

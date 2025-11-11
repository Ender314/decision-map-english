# -*- coding: utf-8 -*-
"""
Calculation utilities for Lambda Pro.
Contains all mathematical operations and data processing functions.
"""

import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple, Any


@st.cache_data
def normalize_weights(criteria: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Normalize criteria weights to sum to 1.0.
    
    Args:
        criteria: List of criteria dicts with 'name' and 'weight' keys
        
    Returns:
        Dictionary mapping criterion name to normalized weight
    """
    weights = {c["name"]: float(c.get("weight", 0.0)) for c in criteria}
    total = sum(weights.values()) or 1.0
    return {k: v / total for k, v in weights.items()}


def mcda_totals_and_ranking(scores_df: pd.DataFrame, criteria: List[Dict[str, Any]]) -> Tuple[pd.Series, List[Dict[str, Any]]]:
    """
    Calculate MCDA weighted totals and ranking.
    
    Args:
        scores_df: DataFrame with alternatives as rows, criteria as columns
        criteria: List of criteria with weights
        
    Returns:
        Tuple of (totals Series, ranking list)
    """
    if scores_df is None or scores_df.empty:
        return pd.Series(dtype=float), []
    
    weight_map = normalize_weights(criteria)
    
    # Align missing criteria to 0
    for criterion in weight_map:
        if criterion not in scores_df.columns:
            scores_df[criterion] = 0.0
    
    # Calculate weighted totals
    totals = scores_df.apply(
        lambda row: sum(row[c] * weight_map.get(c, 0.0) for c in scores_df.columns), 
        axis=1
    )
    
    # Create ranking
    ranking = totals.sort_values(ascending=False)
    ranking_list = [
        {"alternativa": idx, "score": float(val)} 
        for idx, val in ranking.items()
    ]
    
    return totals, ranking_list


def scenario_expected_value(p_best: float, worst_score: float, best_score: float) -> float:
    """
    Calculate expected value for scenario planning.
    
    Args:
        p_best: Probability of best case scenario (0-1)
        worst_score: Score for worst case
        best_score: Score for best case
        
    Returns:
        Expected value on 0-10 scale
    """
    p = float(p_best)
    return p * float(best_score) + (1 - p) * float(worst_score)


@st.cache_data
def calculate_relevance_percentage(impacto_corto: str, impacto_medio: str, impacto_largo: str, impact_map: Dict[str, int]) -> float:
    """
    Calculate relevance percentage based on temporal impact assessment.
    
    Args:
        impacto_corto: Short-term impact level
        impacto_medio: Medium-term impact level  
        impacto_largo: Long-term impact level
        impact_map: Mapping from impact level to numeric value
        
    Returns:
        Relevance percentage (0-100)
    """
    y_values = [
        impact_map[impacto_corto],
        impact_map[impacto_medio], 
        impact_map[impacto_largo]
    ]
    
    # Calculate area under curve (trapezoidal rule)
    auc = (y_values[0] + 2 * y_values[1] + y_values[2]) / 2
    max_auc = max(impact_map.values()) * 2
    
    if max_auc == 0:
        return 0.0
    
    relevance_ratio = auc / max_auc
    return round(100 * relevance_ratio, 0)


def calculate_recommended_time(relevance_pct: float) -> str:
    """
    Calculate recommended time allocation based on relevance percentage.
    
    Args:
        relevance_pct: Relevance percentage (0-100)
        
    Returns:
        Recommended time allocation string
    """
    if relevance_pct <= 20:
        return "Menos de media hora"
    elif relevance_pct <= 45:
        return "Un par de horas"
    elif relevance_pct <= 80:
        return "Una mañana"
    else:
        return "Un par de días"


@st.cache_data
def generate_violin_data(worst: float, best: float, expected_value: float, n_samples: int = 1000) -> np.ndarray:
    """
    Generate violin plot data using normal distribution centered on expected value.
    
    Args:
        worst: Worst case scenario value
        best: Best case scenario value
        expected_value: Expected value (center of distribution)
        n_samples: Number of samples to generate
        
    Returns:
        Array of samples clipped to [worst, best] range
    """
    # Calculate standard deviation (range covers ~4 std devs)
    std_dev = (best - worst) / 4
    
    # Generate samples from normal distribution centered on EV
    samples = np.random.normal(expected_value, std_dev, n_samples)
    
    # Clip samples to stay within worst-best range
    return np.clip(samples, worst, best)


def get_sections_for_time(tiempo_value: str, all_sections: List[str]) -> List[str]:
    """
    Get visible sections based on time allocation.
    
    Args:
        tiempo_value: Selected time allocation
        all_sections: All available sections
        
    Returns:
        List of sections to display
    """
    if tiempo_value == "Menos de media hora":
        return ["Dimensionado", "Alternativas", "Prioridades", "Evaluación"]
    elif tiempo_value == "Un par de horas":
        return ["Dimensionado", "Información", "Alternativas", "Prioridades", "Evaluación", "Resultados"]
    else:
        return all_sections[:]

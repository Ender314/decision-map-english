# -*- coding: utf-8 -*-
"""
Calculation utilities for Decider Pro.
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


def pert_pdf(x_values: np.ndarray, minimum: float, maximum: float, mode: float, lam: float = 4.0) -> np.ndarray:
    """
    Compute the PERT distribution PDF at given x values.
    PERT is a scaled Beta distribution bounded by [minimum, maximum] with peak at mode.
    Produces smooth, deterministic curves without Monte Carlo sampling.
    
    Args:
        x_values: Array of x positions to evaluate
        minimum: Lower bound (worst case)
        maximum: Upper bound (best case)
        mode: Most likely value (EV)
        lam: Shape parameter (default 4, standard PERT)
        
    Returns:
        Array of PDF values
    """
    from math import gamma as _gamma

    if maximum <= minimum:
        return np.zeros_like(x_values, dtype=float)

    # Clamp mode to bounds
    mode = max(minimum, min(maximum, mode))

    # Beta shape parameters
    alpha1 = 1.0 + lam * (mode - minimum) / (maximum - minimum)
    alpha2 = 1.0 + lam * (maximum - mode) / (maximum - minimum)

    # Normalize x to [0, 1]
    t = (x_values - minimum) / (maximum - minimum)

    # Beta function B(α1, α2) = Γ(α1)·Γ(α2) / Γ(α1+α2)
    beta_val = _gamma(alpha1) * _gamma(alpha2) / _gamma(alpha1 + alpha2)

    # PDF only where 0 < t < 1
    pdf = np.where(
        (t > 0) & (t < 1),
        t ** (alpha1 - 1) * (1 - t) ** (alpha2 - 1) / (beta_val * (maximum - minimum)),
        0.0,
    )
    return pdf


def get_disqualified_alternatives() -> Dict[str, List[str]]:
    """
    Get alternatives that are disqualified due to failing no negociables.
    
    Returns:
        Dict mapping alt_id to list of failed constraint names
    """
    no_negociables = st.session_state.get("no_negociables", [])
    no_neg_scores = st.session_state.get("no_negociables_scores", {})
    alts = st.session_state.get("alts", [])
    
    # Build constraint id -> text mapping
    constraint_names = {c["id"]: c["text"] for c in no_negociables if c.get("text", "").strip()}
    
    disqualified = {}
    
    for alt in alts:
        alt_id = alt["id"]
        alt_scores = no_neg_scores.get(alt_id, {})
        failed_constraints = []
        
        for constraint_id, constraint_text in constraint_names.items():
            # If not checked (False or missing), it's a failure
            if not alt_scores.get(constraint_id, False):
                failed_constraints.append(constraint_text)
        
        if failed_constraints:
            disqualified[alt_id] = failed_constraints
    
    return disqualified


def is_alternative_disqualified(alt_id: str) -> Tuple[bool, List[str]]:
    """
    Check if a specific alternative is disqualified.
    
    Args:
        alt_id: The alternative ID to check
        
    Returns:
        Tuple of (is_disqualified, list_of_failed_constraint_names)
    """
    disqualified = get_disqualified_alternatives()
    if alt_id in disqualified:
        return True, disqualified[alt_id]
    return False, []


def get_qualified_alternatives() -> List[Dict[str, Any]]:
    """
    Get list of alternatives that pass all no negociables.
    
    Returns:
        List of alternative dicts that are qualified
    """
    alts = st.session_state.get("alts", [])
    disqualified = get_disqualified_alternatives()
    
    return [alt for alt in alts if alt["id"] not in disqualified]


def calculate_robustness_index(
    scores_df: pd.DataFrame,
    criteria: List[Dict[str, Any]],
    alt_names: List[str],
    n_simulations: int = 500,
    weight_perturbation: float = 0.20,
    score_perturbation: float = 1.0,
    score_range: Tuple[float, float] = (0.0, 5.0),
) -> Dict[str, Any]:
    """
    Calculate robustness index via Monte Carlo sensitivity analysis.
    
    Tests whether the top-ranked alternative changes under:
    1. Weight perturbation (±20%)
    2. Score perturbation (±1)
    3. Combined (both at once)
    4. Dominant criterion removal (deterministic)
    
    Args:
        scores_df: DataFrame with alternatives as rows, criteria as columns
        criteria: List of criteria dicts with 'name' and 'weight'
        alt_names: List of alternative names to evaluate
        n_simulations: Number of Monte Carlo iterations
        weight_perturbation: Fractional perturbation for weights (0.20 = ±20%)
        score_perturbation: Absolute perturbation for scores (±1)
        score_range: Min/max bounds for scores after perturbation
        
    Returns:
        Dict with keys:
            robustness_pct: Overall robustness percentage (0-100)
            weight_stability: % of sims where top-1 holds under weight perturbation
            score_stability: % of sims where top-1 holds under score perturbation
            combined_stability: % of sims where top-1 holds under both
            dominant_criterion: Name of dominant criterion (>40% weight) or None
            dominant_removal_flips: Whether removing dominant criterion changes winner
            dominant_removal_new_winner: New winner after removal (if flipped)
            baseline_winner: Name of the baseline top-1 alternative
            label: Qualitative label ("robusto", "moderado", "fragil")
            emoji: Corresponding emoji
    """
    if scores_df is None or scores_df.empty or not criteria or not alt_names:
        return {
            "robustness_pct": 0, "weight_stability": 0, "score_stability": 0,
            "combined_stability": 0, "dominant_criterion": None,
            "dominant_removal_flips": False, "dominant_removal_new_winner": None,
            "baseline_winner": None, "label": "sin datos", "emoji": "⚪",
        }

    criteria_names = [c["name"] for c in criteria]
    base_weights = normalize_weights(criteria)

    # Ensure all criteria exist in scores_df
    for c in criteria_names:
        if c not in scores_df.columns:
            scores_df[c] = 0.0

    # Baseline winner
    base_totals = scores_df.loc[alt_names, criteria_names].apply(
        lambda row: sum(row[c] * base_weights.get(c, 0) for c in criteria_names), axis=1
    )
    baseline_winner = base_totals.idxmax()

    rng = np.random.default_rng(42)

    def _simulate(perturb_weights: bool, perturb_scores: bool) -> int:
        """Run n_simulations and return count where baseline_winner stays on top."""
        wins = 0
        for _ in range(n_simulations):
            # Perturb weights
            if perturb_weights:
                w = {c: base_weights[c] * (1 + rng.uniform(-weight_perturbation, weight_perturbation))
                     for c in criteria_names}
                w_total = sum(w.values()) or 1.0
                w = {c: v / w_total for c, v in w.items()}
            else:
                w = base_weights

            # Perturb scores
            if perturb_scores:
                perturbed = scores_df.loc[alt_names, criteria_names].copy()
                noise = rng.uniform(-score_perturbation, score_perturbation, perturbed.shape)
                perturbed = perturbed + noise
                perturbed = perturbed.clip(lower=score_range[0], upper=score_range[1])
            else:
                perturbed = scores_df.loc[alt_names, criteria_names]

            totals = perturbed.apply(
                lambda row: sum(row[c] * w.get(c, 0) for c in criteria_names), axis=1
            )
            if totals.idxmax() == baseline_winner:
                wins += 1
        return wins

    weight_wins = _simulate(perturb_weights=True, perturb_scores=False)
    score_wins = _simulate(perturb_weights=False, perturb_scores=True)
    combined_wins = _simulate(perturb_weights=True, perturb_scores=True)

    weight_stability = round(100 * weight_wins / n_simulations)
    score_stability = round(100 * score_wins / n_simulations)
    combined_stability = round(100 * combined_wins / n_simulations)

    # Dominant criterion removal (deterministic)
    dominant_criterion = None
    dominant_removal_flips = False
    dominant_removal_new_winner = None

    if base_weights:
        max_weight_name = max(base_weights, key=base_weights.get)
        max_weight_val = base_weights[max_weight_name]
        if max_weight_val > 0.40:
            dominant_criterion = max_weight_name
            reduced_criteria = [c for c in criteria_names if c != max_weight_name]
            if reduced_criteria:
                reduced_w = {c: base_weights[c] for c in reduced_criteria}
                rw_total = sum(reduced_w.values()) or 1.0
                reduced_w = {c: v / rw_total for c, v in reduced_w.items()}
                reduced_totals = scores_df.loc[alt_names, reduced_criteria].apply(
                    lambda row: sum(row[c] * reduced_w.get(c, 0) for c in reduced_criteria), axis=1
                )
                new_winner = reduced_totals.idxmax()
                if new_winner != baseline_winner:
                    dominant_removal_flips = True
                    dominant_removal_new_winner = new_winner

    # Overall robustness = weighted average (combined gets most weight)
    robustness_pct = round(0.25 * weight_stability + 0.25 * score_stability + 0.50 * combined_stability)

    # Penalize if dominant criterion removal flips the winner
    if dominant_removal_flips:
        robustness_pct = max(0, robustness_pct - 15)

    # Qualitative label
    if robustness_pct >= 85:
        label, emoji = "robusto", "🟢"
    elif robustness_pct >= 60:
        label, emoji = "moderado", "🟡"
    else:
        label, emoji = "frágil", "🔴"

    return {
        "robustness_pct": robustness_pct,
        "weight_stability": weight_stability,
        "score_stability": score_stability,
        "combined_stability": combined_stability,
        "dominant_criterion": dominant_criterion,
        "dominant_removal_flips": dominant_removal_flips,
        "dominant_removal_new_winner": dominant_removal_new_winner,
        "baseline_winner": baseline_winner,
        "label": label,
        "emoji": emoji,
    }


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
        return ["Dimensionado", "Alternativas", "Información", "Prioridades", "Evaluación", "Resultados"]
    else:
        return all_sections[:]

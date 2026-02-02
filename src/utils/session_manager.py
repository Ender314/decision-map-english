# -*- coding: utf-8 -*-
"""
Session state management utilities for Decider Pro.
Provides efficient session state initialization, cleanup, and optimization.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from config.constants import DEFAULT_MCDA_CRITERIA


class SessionStateManager:
    """
    Centralized session state management for Decider Pro.
    Provides lazy initialization, cleanup, and optimization utilities.
    """
    
    # Define default values as class constants for better performance
    DEFAULTS = {
        # Impact assessment
        "impacto_corto": "bajo",
        "impacto_medio": "medio", 
        "impacto_largo": "bajo",
        
        # Core data
        "decision": "",
        "estrategia_corporativa": "",
        "objetivo": "",
        "tiempo": "Menos de media hora",
        "tiempo_user_override": False,
        "alts": [],
        "priorities": [],
        
        # Information
        "past_decisions": [],
        "kpis": [],
        "timeline_items": [],
        "stakeholders": [],
        "quantitative_notes": "",
        "qualitative_notes": "",
        
        # MCDA
        "mcda_criteria": DEFAULT_MCDA_CRITERIA.copy(),
        "mcda_scores": {},
        "mcda_scores_df": None,
        
        # Scenarios
        "scenarios": {},
        
        # Risk Analysis
        "risks": {},  # {risk_id: risk_data}
        
        # Retrospective
        "retro": {
            "decision_date": None,
            "review_date": None,
            "chosen_alternative_id": None,
            "outcomes": [],  # list of outcome dicts
            "tripwires": [],  # list of tripwire dicts
            "lessons_learned": "",
            "decision_quality_score": 3,
            "outcome_quality_score": 3
        },
        
        # Internal flags
        "_weights_changed": False,
        "weights_user_override": False,
    }
    
    @staticmethod
    def initialize_defaults() -> None:
        """
        Initialize session state with default values.
        Only sets values that don't already exist.
        """
        for key, value in SessionStateManager.DEFAULTS.items():
            if key not in st.session_state:
                # Create a copy for mutable objects to avoid reference issues
                if isinstance(value, (list, dict)):
                    st.session_state[key] = value.copy()
                else:
                    st.session_state[key] = value
    
    @staticmethod
    def lazy_init(key: str, default_value: Any = None) -> Any:
        """
        Lazy initialization of session state variables.
        
        Args:
            key: Session state key
            default_value: Default value if key doesn't exist
            
        Returns:
            Value from session state
        """
        if key not in st.session_state:
            if default_value is not None:
                st.session_state[key] = default_value
            elif key in SessionStateManager.DEFAULTS:
                value = SessionStateManager.DEFAULTS[key]
                if isinstance(value, (list, dict)):
                    st.session_state[key] = value.copy()
                else:
                    st.session_state[key] = value
            else:
                st.session_state[key] = None
        
        return st.session_state[key]
    
    @staticmethod
    def get_or_default(key: str, default: Any = None) -> Any:
        """
        Get session state value or return default.
        
        Args:
            key: Session state key
            default: Default value if key doesn't exist
            
        Returns:
            Value from session state or default
        """
        return st.session_state.get(key, default)
    
    @staticmethod
    def update_if_changed(key: str, new_value: Any) -> bool:
        """
        Update session state only if value has changed.
        
        Args:
            key: Session state key
            new_value: New value to set
            
        Returns:
            True if value was updated, False if unchanged
        """
        current_value = st.session_state.get(key)
        if current_value != new_value:
            st.session_state[key] = new_value
            return True
        return False
    
    @staticmethod
    def cleanup_empty_lists() -> None:
        """
        Clean up empty lists and None values from session state.
        Helps reduce memory usage.
        """
        keys_to_clean = []
        for key, value in st.session_state.items():
            if isinstance(value, list) and len(value) == 0:
                # Keep essential empty lists, clean others
                if key not in ["alts", "priorities", "kpis", "timeline_items", "stakeholders", "past_decisions"]:
                    keys_to_clean.append(key)
            elif value is None and key.startswith("_temp"):
                keys_to_clean.append(key)
        
        for key in keys_to_clean:
            del st.session_state[key]
    
    @staticmethod
    def reset_section(section: str) -> None:
        """
        Reset specific section data to defaults.
        
        Args:
            section: Section name to reset
        """
        section_keys = {
            "dimensionado": ["impacto_corto", "impacto_medio", "impacto_largo"],
            "alternativas": ["alts"],
            "prioridades": ["priorities"],
            "informacion": ["past_decisions", "kpis", "timeline_items", "stakeholders", 
                           "quantitative_notes", "qualitative_notes"],
            "mcda": ["mcda_criteria", "mcda_scores", "mcda_scores_df"],
            "scenarios": ["scenarios"],
            "risks": ["risks"],
            "retro": ["retro"]
        }
        
        if section in section_keys:
            for key in section_keys[section]:
                if key in SessionStateManager.DEFAULTS:
                    value = SessionStateManager.DEFAULTS[key]
                    if isinstance(value, (list, dict)):
                        st.session_state[key] = value.copy()
                    else:
                        st.session_state[key] = value
    
    @staticmethod
    def get_memory_usage() -> Dict[str, int]:
        """
        Get approximate memory usage of session state.
        
        Returns:
            Dictionary with memory usage statistics
        """
        import sys
        
        total_size = 0
        item_sizes = {}
        
        for key, value in st.session_state.items():
            size = sys.getsizeof(value)
            item_sizes[key] = size
            total_size += size
        
        return {
            "total_bytes": total_size,
            "total_kb": round(total_size / 1024, 2),
            "item_count": len(st.session_state),
            "largest_items": sorted(item_sizes.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    @staticmethod
    def validate_data_integrity() -> List[str]:
        """
        Validate session state data integrity.
        
        Returns:
            List of validation errors/warnings
        """
        errors = []
        
        # Check alternatives
        alts = st.session_state.get("alts", [])
        if alts:
            alt_ids = [alt.get("id") for alt in alts if isinstance(alt, dict)]
            if len(alt_ids) != len(set(alt_ids)):
                errors.append("Duplicate alternative IDs found")
        
        # Check MCDA criteria
        criteria = st.session_state.get("mcda_criteria", [])
        if criteria:
            total_weight = sum(c.get("weight", 0) for c in criteria if isinstance(c, dict))
            if abs(total_weight - 1.0) > 0.01:  # Allow small floating point errors
                errors.append(f"MCDA criteria weights don't sum to 1.0 (current: {total_weight})")
        
        # Check scenarios consistency
        scenarios = st.session_state.get("scenarios", {})
        if scenarios and alts:
            alt_ids = {alt.get("id") for alt in alts if isinstance(alt, dict)}
            scenario_ids = set(scenarios.keys())
            orphaned_scenarios = scenario_ids - alt_ids
            if orphaned_scenarios:
                errors.append(f"Orphaned scenarios found: {orphaned_scenarios}")
        
        return errors


# Convenience functions for common operations
def init_session_state() -> None:
    """Initialize session state with defaults."""
    SessionStateManager.initialize_defaults()


def lazy_get(key: str, default: Any = None) -> Any:
    """Lazy get session state value."""
    return SessionStateManager.lazy_init(key, default)


def safe_update(key: str, value: Any) -> bool:
    """Safely update session state only if changed."""
    return SessionStateManager.update_if_changed(key, value)


def cleanup_session() -> None:
    """Clean up session state."""
    SessionStateManager.cleanup_empty_lists()


def validate_session() -> List[str]:
    """Validate session state integrity."""
    return SessionStateManager.validate_data_integrity()

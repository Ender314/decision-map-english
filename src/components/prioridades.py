# -*- coding: utf-8 -*-
"""
Prioridades (Priorities) tab - Simplified version.
Clean component with reordering functionality.
Includes No Negociables (hard constraints) section.
"""

import streamlit as st
import uuid
from utils.ui_helpers import help_tip, get_tooltip


def add_priority(text: str = ""):
    """Add a new priority to the session state."""
    st.session_state.priorities.append({
        "id": str(uuid.uuid4()), 
        "text": text
    })


def remove_priority(priority_id: str):
    """Remove a priority from the session state."""
    st.session_state.priorities = [p for p in st.session_state.priorities if p["id"] != priority_id]


def move_priority(priority_id: str, direction: str):
    """Move priority up or down in the list."""
    priorities = st.session_state.priorities
    
    for i, priority in enumerate(priorities):
        if priority["id"] == priority_id:
            if direction == "up" and i > 0:
                priorities[i], priorities[i-1] = priorities[i-1], priorities[i]
            elif direction == "down" and i < len(priorities) - 1:
                priorities[i], priorities[i+1] = priorities[i+1], priorities[i]
            break


def add_no_negociable(text: str = ""):
    """Add a new no negociable (hard constraint) to the session state."""
    if "no_negociables" not in st.session_state:
        st.session_state.no_negociables = []
    st.session_state.no_negociables.append({
        "id": str(uuid.uuid4()), 
        "text": text
    })


def remove_no_negociable(constraint_id: str):
    """Remove a no negociable from the session state."""
    st.session_state.no_negociables = [
        c for c in st.session_state.get("no_negociables", []) 
        if c["id"] != constraint_id
    ]
    # Also clean up any scores for this constraint
    scores = st.session_state.get("no_negociables_scores", {})
    for alt_id in scores:
        if constraint_id in scores[alt_id]:
            del scores[alt_id][constraint_id]


def render_prioridades_tab():
    """Render the Prioridades (Priorities) tab."""
    
    # Display objetivo as read-only reference
    objetivo_text = st.session_state.get("objetivo", "").strip()
    if objetivo_text:
        # st.markdown("**Objetivo**")
        # st.markdown("🎯")
        st.markdown(f"🎯 *{objetivo_text}*")
        st.markdown("---")
    
    st.markdown(f"### ⭐ Priorities {help_tip(get_tooltip('prioridades'))}", unsafe_allow_html=True)
    
    # Show existing priorities with reordering
    if st.session_state.priorities:
        for i, priority in enumerate(st.session_state.priorities, start=1):
            col1, col2, col3, col4 = st.columns([0.5, 5, 0.5, 0.5])
            
            # Up button
            with col1:
                if i > 1 and st.button("⬆️", key=f"up_{priority['id']}", help="Move up"):
                    move_priority(priority["id"], "up")
                    st.rerun()
            
            # Text input
            with col2:
                new_text = st.text_input(
                    f"Priority {i}",
                    value=priority["text"],
                    key=f"priority_text_{priority['id']}",
                    placeholder="Our top priority is...",
                    label_visibility="collapsed",
                )
                # Update the priority if text changed
                if new_text != priority["text"]:
                    priority["text"] = new_text
            
            # Down button
            with col3:
                if i < len(st.session_state.priorities) and st.button("⬇️", key=f"down_{priority['id']}", help="Move down"):
                    move_priority(priority["id"], "down")
                    st.rerun()
            
            # Delete button
            with col4:
                if st.button("🗑️", key=f"del_priority_{priority['id']}", help="Delete priority"):
                    remove_priority(priority["id"])
                    st.rerun()
    else:
        st.info("💡 **Tip**: Define the priorities you will use as criteria to evaluate alternatives")
    
    # Add new priority button
    if st.button("➕ Add Priority", width="stretch"):
        add_priority()
        st.rerun()
    
    # Show guidance based on current state
    valid_priorities = [p for p in st.session_state.priorities if p["text"].strip()]
    
    # if len(valid_priorities) == 1:
    #     st.info("💡 **Siguiente paso**: Añade al menos una prioridad más para poder hacer una evaluación balanceada")
    
    # Warning for too many priorities
    if len(valid_priorities) > 4:
        st.warning("⚠️ **Warning: too many priorities can make prioritization meaningless**")
    
    # ===========================================
    # NO NEGOCIABLES SECTION
    # ===========================================
    
    st.markdown("---")
    st.markdown("### 🚫 Non-negotiables")
    st.caption("Mandatory requirements an alternative must satisfy to be considered.")
    
    # Initialize no_negociables if needed
    if "no_negociables" not in st.session_state:
        st.session_state.no_negociables = []
    
    # Show existing no negociables
    if st.session_state.no_negociables:
        for i, constraint in enumerate(st.session_state.no_negociables, start=1):
            col1, col2, col3 = st.columns([0.5, 5, 0.5])
            
            # Number indicator
            with col1:
                st.markdown(f"**{i}.**")
            
            # Text input
            with col2:
                new_text = st.text_input(
                    f"No negociable {i}",
                    value=constraint["text"],
                    key=f"no_neg_text_{constraint['id']}",
                    placeholder="E.g. Must have regulatory approval",
                    label_visibility="collapsed",
                )
                # Update if text changed
                if new_text != constraint["text"]:
                    constraint["text"] = new_text
            
            # Delete button
            with col3:
                if st.button("🗑️", key=f"del_no_neg_{constraint['id']}", help="Delete constraint"):
                    remove_no_negociable(constraint["id"])
                    st.rerun()
    else:
        st.info("💡 **Tip**: Non-negotiables are binary requirements (yes/no). An alternative that fails **any** non-negotiable will be disqualified from analysis.")
    
    # Add new no negociable button
    if st.button("➕ Add Non-negotiable", width="stretch"):
        add_no_negociable()
        st.rerun()

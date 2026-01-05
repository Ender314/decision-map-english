# -*- coding: utf-8 -*-
"""
Prioridades (Priorities) tab - Simplified version.
Clean component with reordering functionality.
"""

import streamlit as st
import uuid


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


def render_prioridades_tab():
    """Render the Prioridades (Priorities) tab."""
    
    # Display objetivo as read-only reference
    objetivo_text = st.session_state.get("objetivo", "").strip()
    if objetivo_text:
        # st.markdown("**Objetivo**")
        # st.markdown("🎯")
        st.markdown(f"🎯 *{objetivo_text}*")
        st.markdown("---")
    
    st.subheader("⭐ Prioridades")
    
    # Show existing priorities with reordering
    if st.session_state.priorities:
        for i, priority in enumerate(st.session_state.priorities, start=1):
            col1, col2, col3, col4 = st.columns([0.5, 5, 0.5, 0.5])
            
            # Up button
            with col1:
                if i > 1 and st.button("⬆️", key=f"up_{priority['id']}", help="Mover arriba"):
                    move_priority(priority["id"], "up")
                    st.rerun()
            
            # Text input
            with col2:
                new_text = st.text_input(
                    f"Prioridad {i}",
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
                if i < len(st.session_state.priorities) and st.button("⬇️", key=f"down_{priority['id']}", help="Mover abajo"):
                    move_priority(priority["id"], "down")
                    st.rerun()
            
            # Delete button
            with col4:
                if st.button("🗑️", key=f"del_priority_{priority['id']}", help="Eliminar prioridad"):
                    remove_priority(priority["id"])
                    st.rerun()
    else:
        st.info("💡 **Tip**: Define las prioridades que usarás como criterios para evaluar las alternativas")
    
    # Add new priority button
    if st.button("➕ Añadir Prioridad", use_container_width=True):
        add_priority()
        st.rerun()
    
    # Show guidance based on current state
    valid_priorities = [p for p in st.session_state.priorities if p["text"].strip()]
    
    # if len(valid_priorities) == 1:
    #     st.info("💡 **Siguiente paso**: Añade al menos una prioridad más para poder hacer una evaluación balanceada")
    
    # Warning for too many priorities
    if len(valid_priorities) > 4:
        st.warning("⚠️ **Cuidado, demasiadas prioridades es no tenerlas**")

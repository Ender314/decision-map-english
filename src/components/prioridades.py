# -*- coding: utf-8 -*-
"""
Prioridades (Priorities) tab component for Lambda Pro.
Handles creation, editing, and ordering of decision priorities/criteria.
"""

import streamlit as st
import uuid


def add_priority(default_text: str = "") -> None:
    """Add a new priority to the session state."""
    st.session_state.priorities.append({"id": str(uuid.uuid4()), "text": default_text})


def remove_priority(priority_id: str) -> None:
    """Remove a priority from the session state."""
    st.session_state.priorities = [p for p in st.session_state.priorities if p["id"] != priority_id]


def move_priority_up(priority_id: str) -> None:
    """Move a priority up in the list."""
    priorities = st.session_state.priorities
    for i, priority in enumerate(priorities):
        if priority["id"] == priority_id and i > 0:
            priorities[i], priorities[i-1] = priorities[i-1], priorities[i]
            break


def move_priority_down(priority_id: str) -> None:
    """Move a priority down in the list."""
    priorities = st.session_state.priorities
    for i, priority in enumerate(priorities):
        if priority["id"] == priority_id and i < len(priorities) - 1:
            priorities[i], priorities[i+1] = priorities[i+1], priorities[i]
            break


def render_prioridades_tab():
    """Render the Prioridades (Priorities) tab."""
    
    # Display objetivo as read-only reference
    objetivo_text = st.session_state.get("objetivo", "").strip()
    if objetivo_text:
        st.markdown("**Objetivo**")
        st.markdown(f"*{objetivo_text}*")
        st.markdown("---")
    
    st.subheader("Prioridades")
    
    # Display existing priorities with sorting controls
    if st.session_state.get("priorities", []):
        updated_priorities = []
        for i, priority in enumerate(st.session_state.priorities, start=1):
            c1, c2, c3, c4 = st.columns([0.5, 5, 0.5, 0.5])
            with c1:
                if i > 1 and st.button("⬆️", key=f"up_{priority['id']}", help="Mover arriba", use_container_width=True):
                    move_priority_up(priority["id"])
                    st.rerun()
            with c2:
                new_text = st.text_input(
                    label=f"Prioridad {i}",
                    value=priority["text"],
                    key=f"priority_text_{priority['id']}",
                    placeholder="Our top priority is...",
                    label_visibility="collapsed",
                )
            with c3:
                if i < len(st.session_state.priorities) and st.button("⬇️", key=f"down_{priority['id']}", help="Mover abajo", use_container_width=True):
                    move_priority_down(priority["id"])
                    st.rerun()
            with c4:
                if st.button("🗑️", key=f"del_priority_{priority['id']}", help="Eliminar esta prioridad", use_container_width=True):
                    remove_priority(priority["id"])
                    st.rerun()
            updated_priorities.append({"id": priority["id"], "text": new_text})

        st.session_state.priorities = updated_priorities

    # Add new priority button
    cols_add = st.columns([1, 3])
    with cols_add[0]:
        if st.button("➕ Añadir", key="add_priority_btn", use_container_width=True):
            add_priority()
            st.rerun()

    st.markdown('')

    # Warning if more than 3 priorities
    if len(st.session_state.get("priorities", [])) > 3:
        st.info("💡 Demasiadas prioridades es no tenerlas")

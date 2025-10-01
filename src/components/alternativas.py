# -*- coding: utf-8 -*-
"""
Alternativas (Alternatives) tab component for Lambda Pro.
Handles creation, editing, and management of decision alternatives.
"""

import streamlit as st
import uuid


def add_alternative(default_text: str = "") -> None:
    """Add a new alternative to the session state."""
    st.session_state.alts.append({"id": str(uuid.uuid4()), "text": default_text})


def remove_alternative(alt_id: str) -> None:
    """Remove an alternative from the session state."""
    st.session_state.alts = [a for a in st.session_state.alts if a["id"] != alt_id]


def render_alternativas_tab():
    """Render the Alternativas (Alternatives) tab."""
    
    st.subheader("Alternativas posibles")

    if not st.session_state.get("alts", []):
        st.info("No hay alternativas todavía. Pulsa **Añadir** para crear la primera.")
    else:
        updated_alts = []
        for i, alt in enumerate(st.session_state.alts, start=1):
            c1, c2 = st.columns([6, 1])
            with c1:
                new_text = st.text_input(
                    label=f"Alternativa {i}",
                    value=alt["text"],
                    key=f"alt_text_{alt['id']}",
                    placeholder="Describe la alternativa",
                    label_visibility="collapsed",
                )
            with c2:
                if st.button("🗑️", key=f"del_{alt['id']}", help="Eliminar esta alternativa", 
                           use_container_width=True):
                    remove_alternative(alt["id"])
                    st.rerun()
            
            # Collect updated text (don't mutate original item inline)
            updated_alts.append({"id": alt["id"], "text": new_text})

        # Single write after loop
        st.session_state.alts = updated_alts

    # Add new alternative button
    cols_add = st.columns([1, 3])
    with cols_add[0]:
        if st.button("➕ Añadir", key="add_alternative_btn", use_container_width=True):
            add_alternative()
            st.rerun()

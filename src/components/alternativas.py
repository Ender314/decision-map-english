# -*- coding: utf-8 -*-
"""
Alternativas (Alternatives) tab - Simplified version.
Clean component without over-engineering.
"""

import streamlit as st
import uuid


def add_alternative(text: str = ""):
    """Add a new alternative to the session state."""
    st.session_state.alts.append({
        "id": str(uuid.uuid4()), 
        "text": text
    })


def remove_alternative(alt_id: str):
    """Remove an alternative from the session state."""
    st.session_state.alts = [a for a in st.session_state.alts if a["id"] != alt_id]


def render_alternativas_tab():
    """Render the Alternativas (Alternatives) tab - exact original functionality."""
    st.subheader("🧭 Alternativas posibles")

    if not st.session_state.alts:
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
                if st.button("🗑️", key=f"del_{alt['id']}", help="Eliminar esta alternativa", use_container_width=True):
                    remove_alternative(alt["id"])
                    st.rerun()
            # collect (don't mutate the original item inline)
            updated_alts.append({"id": alt["id"], "text": new_text})

        # single write after loop
        st.session_state.alts = updated_alts

    cols_add = st.columns([1, 3])
    with cols_add[0]:
        if st.button("➕ Añadir", key="add_alternative_btn", use_container_width=True):
            add_alternative()
            st.rerun()
    
    # Reference section - Past decisions (minimal and less eye-catching)
    past_decisions = st.session_state.get("past_decisions", [])
    if past_decisions:
        st.markdown("#####")
        st.markdown("---")
        # st.markdown("#####")
        # st.markdown(" 📖 Decisiones Pasadas")
        
        for decision in past_decisions:
            if decision.get("decision", "").strip():
                with st.expander(f"📝 {decision['decision'][:60]}{'...' if len(decision.get('decision', '')) > 60 else ''}", expanded=False):
                    if decision.get("results", "").strip():
                        st.markdown(f"**Resultados:** {decision['results']}")
                    if decision.get("lessons", "").strip():
                        st.markdown(f"**Lecciones:** {decision['lessons']}")
                    if not decision.get("results", "").strip() and not decision.get("lessons", "").strip():
                        st.markdown("*Sin resultados o lecciones registradas*")

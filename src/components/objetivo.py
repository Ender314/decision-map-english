# -*- coding: utf-8 -*-
"""
Objetivo component for Decider Pro application.
Enhanced to provide strategic context from macro to micro level.
"""

import streamlit as st


def render_objetivo_tab():
    """
    Render the simplified Objetivo tab with bottom-up approach.
    From tactical alternatives to strategic context.
    """
    
    # Tactical Alternatives (First - Micro Level)
    st.markdown("### 🧭 Alternativas")
    
    # Show alternatives if they exist
    alternatives = st.session_state.get("alts", [])
    
    if alternatives:
        # Display alternatives in a clean format
        for i, alt in enumerate(alternatives, 1):
            alt_text = alt.get("text", "").strip()
            if alt_text:
                # Use different emoji for each alternative
                emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][i-1] if i <= 10 else f"{i}️⃣"
                st.markdown(f"- {emoji} {alt_text}")
            
    else:
        st.info("📝 Las alternativas se definirán en la pestaña **Alternativas**")
        st.markdown("*Aquí aparecerán listadas una vez que las hayas creado*")
    
    # st.markdown("---")
    st.markdown("#####")
    
    # Decision Objective (Second - Operational Level)
    st.markdown("### 🎯 Objetivo")
    
    st.text_area(
        "Objetivo",
        key="objetivo",
        placeholder="¿Qué habría de cumplirse para que estuviéramos seguros de que se tomó la decisión correcta?",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Strategic Context (Third - Macro Level)
    st.markdown("### 🏢 Estrategia")
    
    st.text_area(
        "Estrategia Corporativa",
        key="estrategia_corporativa",
        placeholder="¿Cómo ayuda este objetivo con la estrategia de la empresa?",
        label_visibility="collapsed"
    )

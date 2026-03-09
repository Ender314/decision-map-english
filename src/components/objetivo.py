# -*- coding: utf-8 -*-
"""
Objective component for Decision Map application.
Enhanced to provide strategic context from macro to micro level.
"""

import streamlit as st


def render_objetivo_tab():
    """
    Render the simplified Objective tab with bottom-up approach.
    From tactical alternatives to strategic context.
    """
    
    # Tactical Alternatives (First - Micro Level)
    st.markdown("### 🧭 Alternatives")
    
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
        st.info("📝 Alternatives are defined in the **Alternatives** tab")
        st.markdown("*They will appear here once you create them*")
    
    # st.markdown("---")
    st.markdown("#####")
    
    # Decision Objective (Second - Operational Level)
    st.markdown("### 🎯 Objective")
    
    st.text_area(
        "Objective",
        key="objetivo",
        placeholder="What would need to happen for us to be confident that the right decision was made?",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    # Strategic Context (Third - Macro Level)
    st.markdown("### 🏢 Strategy")
    
    st.text_area(
        "Corporate strategy",
        key="estrategia_corporativa",
        placeholder="How does this objective support the company strategy?",
        label_visibility="collapsed"
    )

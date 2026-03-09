# -*- coding: utf-8 -*-
"""
Offer Landing Page for Decision Map - Decision Mastery System
Marketing-focused landing page with conversion optimization.
"""

import streamlit as st
from config.constants import APP_NAME, APP_ICON, APP_VERSION

def render_offer_page():
    """Render the Decision Mastery System offer landing page."""
    
    # Custom CSS for marketing page styling
    st.markdown("""
    <style>
    .hero-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        font-weight: 300;
        margin-bottom: 2rem;
        opacity: 0.9;
    }
    
    .dream-outcome {
        font-size: 1.8rem;
        font-weight: 600;
        background: rgba(255,255,255,0.1);
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #FFD700;
    }
    
    .offer-stack {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 2rem;
        margin: 2rem 0;
        border: 2px solid #e9ecef;
    }
    
    .component-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        margin: 0.5rem 0;
        background: white;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .component-name {
        font-weight: 700;
        color: #2c3e50;
        font-size: 1.1rem;
    }
    
    .component-desc {
        color: #6c757d;
        font-size: 0.9rem;
        margin-top: 0.3rem;
    }
    
    .component-value {
        font-weight: 700;
        color: #28a745;
        font-size: 1.2rem;
    }
    
    .pricing-section {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin: 2rem 0;
    }
    
    .original-price {
        text-decoration: line-through;
        font-size: 2rem;
        opacity: 0.7;
        margin-right: 1rem;
    }
    
    .offer-price {
        font-size: 3rem;
        font-weight: 800;
        color: #FFD700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .guarantee-box {
        background: #fff3cd;
        border: 2px solid #ffeaa7;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 2rem 0;
        text-align: center;
    }
    
    .scarcity-alert {
        background: #f8d7da;
        border: 2px solid #f5c6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        text-align: center;
        font-weight: 600;
        color: #721c24;
    }
    
    .cta-button {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        padding: 1rem 3rem;
        border: none;
        border-radius: 50px;
        font-size: 1.3rem;
        font-weight: 700;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(238, 90, 36, 0.4);
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .cta-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(238, 90, 36, 0.6);
    }
    
    .testimonial-box {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-top: 4px solid #667eea;
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Navigation bar
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        if st.button("← Home", key="nav_to_landing", help="Go back to the main page"):
            st.session_state["current_page"] = "landing"
            st.query_params.clear()  # Clear URL parameters
            st.rerun()
    with col4:
        if st.button("🚀 Try free", key="nav_to_app", help="Try the app"):
            st.session_state["current_page"] = "app"
            st.query_params["page"] = "app"
            st.rerun()
    
    st.markdown("---")
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">🧭 Decision Mastery System</div>
        <div class="hero-subtitle">For ambitious professionals and business owners</div>
        <div class="dream-outcome">
            💎 "Make every important business or career decision with clarity and confidence — in minutes, not months."
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Positioning Line
    st.markdown("""
    <div style="text-align: center; font-size: 1.5rem; font-weight: 600; color: #2c3e50; margin: 2rem 0;">
        🎯 Turn overanalysis into clarity — and clarity into progress.
    </div>
    """, unsafe_allow_html=True)
    
    # Problem/Solution Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 😰 The Problem You Face Every Day
        
        - **Analysis Paralysis**: Weeks spent on decisions that should take hours
        - **Bias Blindness**: Obvious reasoning flaws you don't notice
        - **Inconsistent Process**: A different approach for every decision
        - **Regret and Doubt**: Second-guessing choices after making them
        - **Missed Opportunities**: While you deliberate, others act
        """)
    
    with col2:
        st.markdown("""
        ### ⚡ Your New Decision-Making Superpower
        
        - **Structured Framework**: The same proven process every time
        - **Bias Detection**: Built-in checks for cognitive traps
        - **Visual Clarity**: See your options mapped and weighted
        - **Confidence Boost**: Data-backed decisions you can defend
        - **Speed**: Cut decision time by 70% without sacrificing quality
        """)
    
    # Offer Stack
    st.markdown("""
    <div class="offer-stack">
        <h2 style="text-align: center; color: #2c3e50; margin-bottom: 2rem;">🚀 Complete Decision Mastery System</h2>
    """, unsafe_allow_html=True)
    
    # Component 1
    st.markdown(f"""
    <div class="component-item">
        <div>
            <div class="component-name">⚡ {APP_NAME} App (Pro Edition)</div>
            <div class="component-desc">Decision engine with bias checks, weighting tools, and visual reports</div>
        </div>
        <div class="component-value">€300</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Component 2
    st.markdown("""
    <div class="component-item">
        <div>
            <div class="component-name">📋 Decision Template Library</div>
            <div class="component-desc">15+ prebuilt templates (e.g., "Hire or Outsource", "Accept Job Offer", "Launch or Wait")</div>
        </div>
        <div class="component-value">€150</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Component 3
    st.markdown("""
    <div class="component-item">
        <div>
            <div class="component-name">🔍 Bias Audit Checklist</div>
            <div class="component-desc">Cognitive-bias checklist inspired by McKinsey-style reviews</div>
        </div>
        <div class="component-value">€50</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Component 4
    st.markdown("""
    <div class="component-item">
        <div>
            <div class="component-name">🤖 AI Decision Review</div>
            <div class="component-desc">Upload your reasoning → AI identifies blind spots and suggests improvements</div>
        </div>
        <div class="component-value">€250</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Component 5
    st.markdown("""
    <div class="component-item">
        <div>
            <div class="component-name">🎯 30-Day Clarity Challenge</div>
            <div class="component-desc">Guided daily micro-decisions to train faster, more rational thinking</div>
        </div>
        <div class="component-value">€100</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Component 6
    st.markdown("""
    <div class="component-item">
        <div>
            <div class="component-name">🔄 Lifetime Updates + Priority Access</div>
            <div class="component-desc">Continuous new templates and decision-science updates</div>
        </div>
        <div class="component-value">€100</div>
    </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Pricing Section
    st.markdown("""
    <div class="pricing-section">
        <h2>💰 Investment</h2>
        <div style="margin: 1rem 0;">
            <span class="original-price">€950+</span>
            <span style="font-size: 1.2rem;">Total Perceived Value</span>
        </div>
        <div style="margin: 2rem 0;">
            <div style="font-size: 1.5rem; margin-bottom: 1rem;">Your Investment Today:</div>
            <div class="offer-price">€99</div>
            <div style="font-size: 1.2rem; margin-top: 1rem;">One-time payment</div>
            <div style="font-size: 1rem; opacity: 0.8; margin-top: 0.5rem;">or €12/month</div>
        </div>
        <div style="font-size: 1.3rem; font-weight: 600; margin-top: 2rem;">
            💥 Save €851+ (89% OFF)
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Scarcity Alert
    st.markdown("""
    <div class="scarcity-alert">
        🔥 Launch price for the first 250 users — only 47 spots left!
    </div>
    """, unsafe_allow_html=True)
    
    # Guarantee
    st.markdown("""
    <div class="guarantee-box">
        <h3>🛡️ 30-Day "Better Decisions" Guarantee</h3>
        <p style="font-size: 1.1rem; margin: 1rem 0;">
            If you don't feel <strong>2× more clarity</strong> in any decision within 30 days,
            get a <strong>full refund</strong> — no questions asked.
        </p>
        <p style="font-style: italic; color: #6c757d;">
            We're so confident this system will transform your decision-making that we take all the risk.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Social Proof / Testimonials
    st.markdown("### 🗣️ What Early Users Say")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="testimonial-box">
            <p><em>"I used to spend weeks agonizing over business decisions. Now I get clarity in hours. This system paid for itself with my first major decision."</em></p>
            <strong>— Sara M., Marketing Director</strong>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="testimonial-box">
            <p><em>"The bias checklist alone is worth the price. I caught myself making a €50k mistake due to confirmation bias."</em></p>
            <strong>— David L., Small Business Owner</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # Feature Highlights
    st.markdown("### ⭐ Why This System Works")
    
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <h4>Science-Based</h4>
            <p>Built on Nobel-winning behavioral economics and McKinsey-style decision frameworks</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <h4>Ultra Fast</h4>
            <p>Get clarity in minutes, not months. Perfect for busy professionals who need to act fast</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <h4>Proven Process</h4>
            <p>The same systematic approach used by Fortune 500 companies, now available to individuals</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Final CTA Section
    st.markdown("""
    <div style="text-align: center; margin: 3rem 0;">
        <h2>Ready to Master Your Decisions?</h2>
        <p style="font-size: 1.2rem; color: #6c757d; margin: 1rem 0;">
            Join 203 ambitious professionals who have already transformed their decision-making
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA Buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 GET INSTANT ACCESS - €99", key="main_cta", help="One-time payment, lifetime access"):
            st.session_state["current_page"] = "app"
            st.query_params["page"] = "app"
            st.rerun()
        
        st.markdown("<div style='text-align: center; margin: 1rem 0;'>o</div>", unsafe_allow_html=True)
        
        if st.button("💳 Start at €12/month", key="monthly_cta", help="Monthly subscription"):
            st.session_state["current_page"] = "app"
            st.query_params["page"] = "app"
            st.rerun()
    
    # Trust Signals
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0; color: #6c757d;">
        <p>🔒 Secure payment • 💯 30-day guarantee • ⚡ Instant access</p>
        <p style="font-size: 0.9rem;">Used by professionals at Google, Microsoft, McKinsey, and 200+ companies</p>
    </div>
    """, unsafe_allow_html=True)
    
    # FAQ Section
    with st.expander("❓ Frequently Asked Questions"):
        st.markdown("""
        **Q: How is this different from making a simple pros and cons list?**
        A: Our system includes bias detection, weighted criteria, scenario planning, and visual analysis that reveals blind spots a simple list cannot.
        
        **Q: Do I need technical skills?**
        A: None. If you can use a web browser, you can master this system in minutes.
        
        **Q: What if I'm not satisfied?**
        A: Full refund within 30 days, no questions asked. We're confident you'll see results quickly.
        
        **Q: Does this also work for personal decisions?**
        A: Absolutely! Career changes, major purchases, relationship decisions — the framework works for any important choice.
        
        **Q: How long does it take to see results?**
        A: Most users report clearer thinking from their first decision. The 30-day challenge builds long-term mastery.
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #6c757d; font-size: 0.9rem;">
        <p>© 2024 {APP_NAME} • Decision Mastery System</p>
        <p>Transform your decision-making, transform your life.</p>
    </div>
    """, unsafe_allow_html=True)

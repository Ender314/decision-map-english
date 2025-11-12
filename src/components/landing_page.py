# -*- coding: utf-8 -*-
"""
Landing Page Component for Lambda Pro
Integrated landing page with navigation to main app functionality.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


def render_landing_page():
    """Render the integrated landing page component."""
    
    # Custom CSS for enhanced styling
    st.markdown("""
    <style>
        .main-header {
            font-size: 3.5rem;
            font-weight: 700;
            text-align: center;
            background: linear-gradient(90deg, #FF6B35, #F7931E, #FFD23F);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
        }
        
        .subtitle {
            font-size: 1.3rem;
            text-align: center;
            color: #666;
            margin-bottom: 2rem;
        }
        
        .feature-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white;
            margin: 1rem 0;
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .feature-card h3 {
            color: white;
            margin-bottom: 1rem;
        }
        
        .benefit-item {
            background: var(--secondary-background-color, #f8f9fa);
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #FF6B35;
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        
        /* Dark theme support for benefit items */
        @media (prefers-color-scheme: dark) {
            .benefit-item {
                background: #2d2d2d;
                color: #ffffff;
            }
        }
        
        /* Streamlit dark theme override */
        .stApp[data-theme="dark"] .benefit-item {
            background: #2d2d2d !important;
            color: #ffffff !important;
        }
        
        .stats-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white;
            text-align: center;
        }
        
        .workflow-step {
            background: var(--background-color, #ffffff);
            border: 1px solid var(--border-color, #e0e0e0);
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
            margin: 1rem 0;
            transition: all 0.3s ease;
        }
        
        /* Dark theme support for workflow cards */
        @media (prefers-color-scheme: dark) {
            .workflow-step {
                background: #2d2d2d;
                border: 1px solid #404040;
                color: #ffffff;
            }
        }
        
        /* Streamlit dark theme override */
        .stApp[data-theme="dark"] .workflow-step {
            background: #2d2d2d !important;
            border: 1px solid #404040 !important;
            color: #ffffff !important;
        }
        
        .nav-button {
            background: linear-gradient(45deg, #FF6B35, #F7931E);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 25px;
            border: none;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
    </style>
    """, unsafe_allow_html=True)

    # Navigation bar
    col1, col2, col3 = st.columns([1, 2, 1])
    with col3:
        if st.button("🚀 Start Analysis", key="nav_to_app", help="Go to Lambda Pro application"):
            st.session_state["current_page"] = "app"
            st.query_params["page"] = "app"  # Update URL
            st.rerun()

    # Hero Section
    st.markdown('<h1 class="main-header">⚡ Lambda Pro</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Transform Complex Corporate Decisions into Data-Driven Success</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div style="text-align: center; font-size: 1.1rem; line-height: 1.6; margin: 2rem 0;">
            <strong>Stop making critical business decisions based on gut feeling.</strong><br>
            Lambda Pro provides a structured, analytical framework that transforms high-stakes 
            corporate decisions into confident, data-backed choices.
        </div>
        """, unsafe_allow_html=True)

    # Key Statistics
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="stats-container">
            <h2 style="margin: 0; color: white;">8</h2>
            <p style="margin: 0;">Analysis Modules</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="stats-container">
            <h2 style="margin: 0; color: white;">43%</h2>
            <p style="margin: 0;">Code Reduction</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="stats-container">
            <h2 style="margin: 0; color: white;">1000+</h2>
            <p style="margin: 0;">Scenario Simulations</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="stats-container">
            <h2 style="margin: 0; color: white;">5</h2>
            <p style="margin: 0;">Visualization Styles</p>
        </div>
        """, unsafe_allow_html=True)

    # Problem Statement
    st.markdown("---")
    st.markdown("## 🎯 The Challenge")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        ### Corporate Decision-Making is Complex
        
        **Traditional approaches fall short:**
        - ❌ Decisions based on incomplete information
        - ❌ Lack of structured analysis framework  
        - ❌ No quantitative risk assessment
        - ❌ Poor stakeholder alignment
        - ❌ Difficulty comparing alternatives objectively
        """)

    with col2:
        # Create a sample problem visualization
        fig = go.Figure()
        
        categories = ['Information<br>Gathering', 'Risk<br>Assessment', 'Alternative<br>Analysis', 
                      'Stakeholder<br>Alignment', 'Quantitative<br>Modeling']
        traditional = [3, 2, 4, 3, 2]
        lambda_pro = [9, 9, 8, 8, 9]
        
        fig.add_trace(go.Scatterpolar(
            r=traditional,
            theta=categories,
            fill='toself',
            name='Traditional Approach',
            line_color='#ff7f7f'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=lambda_pro,
            theta=categories,
            fill='toself',
            name='Lambda Pro',
            line_color='#FF6B35'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )),
            showlegend=True,
            title="Decision-Making Capability Comparison",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # Solution Overview
    st.markdown("---")
    st.markdown("## 🚀 The Lambda Pro Solution")

    # Feature showcase with demo visualizations
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Impact Assessment</h3>
            <p>Analyze decision impact across short, medium, and long-term horizons with dynamic relevance calculations and automated time allocation recommendations.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Demo impact chart
        fig = go.Figure()
        
        x_vals = ['Short Term', 'Medium Term', 'Long Term']
        y_vals = [5, 10, 8]
        colors = ['#FFD23F', '#FF6B35', '#F7931E']
        
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode='lines+markers',
            line=dict(color='#FF6B35', width=4),
            marker=dict(size=12, color=colors),
            fill='tonexty'
        ))
        
        fig.update_layout(
            title="Sample Impact Analysis",
            xaxis_title="Time Horizon",
            yaxis_title="Impact Level",
            height=300,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 MCDA Evaluation</h3>
            <p>Multi-Criteria Decision Analysis with weighted scoring, radar chart visualizations, and automated ranking for objective alternative comparison.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Demo MCDA radar chart
        fig = go.Figure()
        
        categories = ['Strategic<br>Impact', 'Cost<br>Efficiency', 'Risk<br>Level', 'Timeline', 'Resources']
        
        fig.add_trace(go.Scatterpolar(
            r=[8, 6, 7, 9, 5],
            theta=categories,
            fill='toself',
            name='Option A',
            line_color='#FF6B35'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=[6, 9, 8, 6, 8],
            theta=categories,
            fill='toself',
            name='Option B',
            line_color='#667eea'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )),
            showlegend=True,
            title="MCDA Comparison Example",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # Second row of features
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📈 Scenario Planning</h3>
            <p>Probability-based modeling with Monte Carlo simulations, violin plots, and expected value calculations for comprehensive risk assessment.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Demo scenario visualization
        np.random.seed(42)
        data1 = np.random.normal(7, 1.5, 1000)
        data2 = np.random.normal(5, 2, 1000)
        
        fig = go.Figure()
        
        fig.add_trace(go.Violin(
            y=data1,
            name='Option A',
            box_visible=True,
            meanline_visible=True,
            fillcolor='rgba(255, 107, 53, 0.6)',
            line_color='#FF6B35'
        ))
        
        fig.add_trace(go.Violin(
            y=data2,
            name='Option B',
            box_visible=True,
            meanline_visible=True,
            fillcolor='rgba(102, 126, 234, 0.6)',
            line_color='#667eea'
        ))
        
        fig.update_layout(
            title="Scenario Distribution Analysis",
            yaxis_title="Expected Outcome",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📋 Executive Dashboard</h3>
            <p>Comprehensive results summary with integrated visualizations, export capabilities, and executive-ready decision documentation.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Demo dashboard metrics
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = 78,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Decision Confidence Score"},
            delta = {'reference': 50},
            gauge = {'axis': {'range': [None, 100]},
                    'bar': {'color': "#FF6B35"},
                    'steps' : [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"}],
                    'threshold' : {'line': {'color': "red", 'width': 4},
                                  'thickness': 0.75, 'value': 90}}))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Workflow Section
    st.markdown("---")
    st.markdown("## 🔄 How It Works")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="workflow-step">
            <h3>1️⃣</h3>
            <h4>Assess Impact</h4>
            <p>Evaluate decision impact across time horizons</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="workflow-step">
            <h3>2️⃣</h3>
            <h4>Gather Information</h4>
            <p>Collect KPIs, stakeholders, and timeline data</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="workflow-step">
            <h3>3️⃣</h3>
            <h4>Analyze Alternatives</h4>
            <p>Use MCDA and scenario planning</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="workflow-step">
            <h3>4️⃣</h3>
            <h4>Make Decision</h4>
            <p>Review executive dashboard and export results</p>
        </div>
        """, unsafe_allow_html=True)

    # Benefits Section
    st.markdown("---")
    st.markdown("## 💼 Business Benefits")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        <div class="benefit-item">
            <h4>🎯 Structured Decision Process</h4>
            <p>Transform chaotic decision-making into a systematic, repeatable process that ensures nothing is overlooked.</p>
        </div>
        
        <div class="benefit-item">
            <h4>📊 Data-Driven Confidence</h4>
            <p>Replace gut feelings with quantitative analysis, probability modeling, and statistical validation.</p>
        </div>
        
        <div class="benefit-item">
            <h4>⚡ Time Efficiency</h4>
            <p>Adaptive interface shows only relevant sections based on decision complexity and available time.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="benefit-item">
            <h4>🤝 Stakeholder Alignment</h4>
            <p>Visual dashboards and comprehensive documentation facilitate clear communication and buy-in.</p>
        </div>
        
        <div class="benefit-item">
            <h4>🔍 Risk Mitigation</h4>
            <p>Scenario planning with Monte Carlo simulations identifies potential risks and their probability distributions.</p>
        </div>
        
        <div class="benefit-item">
            <h4>📈 Improved Outcomes</h4>
            <p>Systematic analysis leads to better decisions, reduced regret, and measurable business improvements.</p>
        </div>
        """, unsafe_allow_html=True)

    # Use Cases
    st.markdown("---")
    st.markdown("## 🏢 Perfect For")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### Strategic Planning
        - Market entry decisions
        - Product portfolio choices
        - Investment prioritization
        - Resource allocation
        """)

    with col2:
        st.markdown("""
        ### Operational Changes
        - Technology implementations
        - Process improvements
        - Organizational restructuring
        - Vendor selections
        """)

    with col3:
        st.markdown("""
        ### Risk Assessment
        - Compliance decisions
        - Crisis response planning
        - Budget allocations
        - Partnership evaluations
        """)

    # Call to Action
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; color: white;">
            <h2 style="color: white; margin-bottom: 1rem;">Ready to Transform Your Decision-Making?</h2>
            <p style="font-size: 1.1rem; margin-bottom: 2rem;">Join executives who've moved beyond guesswork to data-driven confidence.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)  # Add extra spacing

        # Launch button - centered
        col_left, col_center, col_right = st.columns([1, 1, 1])
        with col_center:
            if st.button("🚀 Launch Lambda Pro", key="launch_app_main", help="Start your decision analysis", type="primary", use_container_width=True):
                st.session_state["current_page"] = "app"
                st.query_params["page"] = "app"  # Update URL
                st.rerun()
        
        st.markdown("""
        <div style="text-align: center; margin-top: 1rem;">
            <p><em>No installation required • Web-based • Instant results</em></p>
        </div>
        """, unsafe_allow_html=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p><strong>Lambda Pro v1.5</strong> • Built with Streamlit • Optimized for Executive Decision-Making</p>
    </div>
    """, unsafe_allow_html=True)

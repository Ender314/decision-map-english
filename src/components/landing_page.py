# -*- coding: utf-8 -*-
"""
Landing Page Component for Decider Pro
Integrated landing page with navigation to main app functionality.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from config.constants import APP_NAME, APP_ICON, APP_VERSION


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
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col3:
        if st.button("💎 Ver Oferta", key="nav_to_offer", help="Ver oferta del Sistema de Maestría en Decisiones"):
            st.session_state["current_page"] = "offer"
            st.query_params["page"] = "offer"  # Update URL
            st.rerun()
    with col4:
        if st.button("🚀 Probar Gratis", key="nav_to_app", help=f"Probar la aplicación {APP_NAME}"):
            st.session_state["current_page"] = "app"
            st.query_params["page"] = "app"  # Update URL
            st.rerun()

    # Hero Section
    st.markdown(f'<h1 class="main-header">{APP_ICON} {APP_NAME}</h1>', unsafe_allow_html=True)
    # st.markdown('<p class="subtitle">Transforma Decisiones Corporativas Complejas en Éxito Basado en Datos</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Convierte la paralisis por análisis en claridad <br> Convierte la claridad en progreso</p>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; font-size: 1.1rem; line-height: 1.6; margin: 2rem 0;">
            <strong>Deja de tomar decisiones críticas de negocio basándote solo en la intuición.</strong><br>
            {APP_NAME} proporciona un marco analítico estructurado que transforma decisiones 
            corporativas de alto riesgo en elecciones confiables respaldadas por datos.
        </div>
        """, unsafe_allow_html=True)

    # Key Statistics
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="stats-container">
            <h2 style="margin: 0; color: white;">⏱️</h2>
            <p style="margin: 0;">De días de deliberación<br>a horas de claridad</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="stats-container">
            <h2 style="margin: 0; color: white;">🎯</h2>
            <p style="margin: 0;">Decisiones más claras<br>en menos tiempo</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="stats-container">
            <h2 style="margin: 0; color: white;">5+</h2>
            <p style="margin: 0;">Visualizaciones<br>para entender tu decisión</p>
        </div>
        """, unsafe_allow_html=True)

    # Problem Statement
    st.markdown("---")
    st.markdown("## 🎯 El Desafío")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        ### La Toma de Decisiones Corporativas es Compleja
        
        **Los enfoques tradicionales se quedan cortos:**
        - ❌ Decisiones basadas en información incompleta
        - ❌ Falta de marco de análisis estructurado  
        - ❌ Sin evaluación cuantitativa de riesgos
        - ❌ Pobre alineación de stakeholders
        - ❌ Dificultad para comparar alternativas objetivamente
        """)

    with col2:
        # Create a sample problem visualization
        fig = go.Figure()
        
        categories = ['Recopilación de<br>Información', 'Evaluación de<br>Riesgos', 'Análisis de<br>Alternativas', 
                      'Alineación de<br>Stakeholders', 'Modelado<br>Cuantitativo']
        traditional = [3, 2, 4, 3, 2]
        lambda_pro = [9, 9, 8, 8, 9]
        
        fig.add_trace(go.Scatterpolar(
            r=traditional,
            theta=categories,
            fill='toself',
            name='Enfoque Tradicional',
            line_color='#e74c3c',
            fillcolor='rgba(231, 76, 60, 0.3)'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=lambda_pro,
            theta=categories,
            fill='toself',
            name='Decider Pro',
            line_color='#2ecc71',
            fillcolor='rgba(46, 204, 113, 0.3)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )),
            showlegend=True,
            title="Comparación de Capacidades de Toma de Decisiones",
            height=400
        )
        
        st.plotly_chart(fig, width="stretch")

    # Solution Overview
    st.markdown("---")
    st.markdown(f"## 🚀 La Solución {APP_NAME}")

    # Feature showcase with demo visualizations
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Evaluación de Impacto</h3>
            <p>Analiza el impacto de decisiones a través de horizontes de corto, mediano y largo plazo con cálculos dinámicos de relevancia y recomendaciones automatizadas de asignación de tiempo.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Demo impact chart
        fig = go.Figure()
        
        x_vals = ['Corto Plazo', 'Mediano Plazo', 'Largo Plazo']
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
            title="Ejemplo de Análisis de Impacto",
            xaxis_title="Horizonte Temporal",
            yaxis_title="Nivel de Impacto",
            height=300,
            showlegend=False
        )
        
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 Evaluación MCDA</h3>
            <p>Análisis de Decisión Multi-Criterio con puntuación ponderada, visualizaciones de gráficos radar y ranking automatizado para comparación objetiva de alternativas.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Demo MCDA radar chart
        fig = go.Figure()
        
        categories = ['Impacto<br>Estratégico', 'Eficiencia de<br>Costos', 'Nivel de<br>Riesgo', 'Cronograma', 'Recursos']
        
        fig.add_trace(go.Scatterpolar(
            r=[8, 6, 7, 9, 5],
            theta=categories,
            fill='toself',
            name='Opción A',
            line_color='#FF6B35'
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=[6, 9, 8, 6, 8],
            theta=categories,
            fill='toself',
            name='Opción B',
            line_color='#667eea'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 10]
                )),
            showlegend=True,
            title="Ejemplo de Comparación MCDA",
            height=300
        )
        
        st.plotly_chart(fig, width="stretch")

    # Second row of features
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>📈 Planificación de Escenarios</h3>
            <p>Modelado basado en probabilidades con simulaciones Monte Carlo, gráficos de violín y cálculos de valor esperado para evaluación integral de riesgos.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Demo scenario visualization
        np.random.seed(42)
        data1 = np.random.normal(7, 1.5, 1000)
        data2 = np.random.normal(5, 2, 1000)
        
        fig = go.Figure()
        
        fig.add_trace(go.Violin(
            y=data1,
            name='Opción A',
            box_visible=True,
            meanline_visible=True,
            fillcolor='rgba(255, 107, 53, 0.6)',
            line_color='#FF6B35'
        ))
        
        fig.add_trace(go.Violin(
            y=data2,
            name='Opción B',
            box_visible=True,
            meanline_visible=True,
            fillcolor='rgba(102, 126, 234, 0.6)',
            line_color='#667eea'
        ))
        
        fig.update_layout(
            title="Análisis de Distribución de Escenarios",
            yaxis_title="Resultado Esperado",
            height=300
        )
        
        st.plotly_chart(fig, width="stretch")

    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>📋 Panel Ejecutivo</h3>
            <p>Resumen integral de resultados con visualizaciones integradas, capacidades de exportación y documentación de decisiones lista para ejecutivos.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Demo dashboard metrics
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = 78,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Puntuación de Confianza en la Decisión"},
            delta = {'reference': 50},
            gauge = {'axis': {'range': [None, 100]},
                    'bar': {'color': "#FF6B35"},
                    'steps' : [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"}],
                    'threshold' : {'line': {'color': "red", 'width': 4},
                                  'thickness': 0.75, 'value': 90}}))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, width="stretch")

    # Workflow Section
    st.markdown("---")
    with st.expander("📋 Cómo Funciona", expanded=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("""
            <div class="workflow-step">
                <h3>1️⃣</h3>
                <h4>Evaluar Impacto</h4>
                <p>Evaluar el impacto de la decisión a través de horizontes temporales</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
            <div class="workflow-step">
                <h3>2️⃣</h3>
                <h4>Recopilar Información</h4>
                <p>Recopilar KPIs, stakeholders y datos de cronograma</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown("""
            <div class="workflow-step">
                <h3>3️⃣</h3>
                <h4>Analizar Alternativas</h4>
                <p>Usar MCDA y planificación de escenarios</p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown("""
            <div class="workflow-step">
                <h3>4️⃣</h3>
                <h4>Tomar Decisión</h4>
                <p>Revisar panel ejecutivo y exportar resultados</p>
            </div>
            """, unsafe_allow_html=True)

    # Benefits Section
    st.markdown("---")
    st.markdown("## 💼 Beneficios de Negocio")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("""
        <div class="benefit-item">
            <h4>🎯 Proceso de Decisión Estructurado</h4>
            <p>Transforma la toma de decisiones caótica en un proceso sistemático y repetible que asegura que nada se pase por alto.</p>
        </div>
        
        <div class="benefit-item">
            <h4>📊 Confianza Basada en Datos</h4>
            <p>Reemplaza las corazonadas con análisis cuantitativo, modelado de probabilidades y validación estadística.</p>
        </div>
        
        <div class="benefit-item">
            <h4>⚡ Eficiencia de Tiempo</h4>
            <p>La interfaz adaptativa muestra solo las secciones relevantes basadas en la complejidad de la decisión y el tiempo disponible.</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="benefit-item">
            <h4>🤝 Alineación de Stakeholders</h4>
            <p>Los paneles visuales y la documentación integral facilitan la comunicación clara y la aceptación.</p>
        </div>
        
        <div class="benefit-item">
            <h4>🔍 Mitigación de Riesgos</h4>
            <p>La planificación de escenarios con simulaciones Monte Carlo identifica riesgos potenciales y sus distribuciones de probabilidad.</p>
        </div>
        
        <div class="benefit-item">
            <h4>📈 Mejores Resultados</h4>
            <p>El análisis sistemático conduce a mejores decisiones, menor arrepentimiento y mejoras medibles del negocio.</p>
        </div>
        """, unsafe_allow_html=True)


    # Call to Action
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 3rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 20px; color: white;">
            <h2 style="color: white; margin-bottom: 1rem;">¿Listo para Transformar tu Toma de Decisiones?</h2>
            <p style="font-size: 1.1rem; margin-bottom: 2rem;">Unéte a ejecutivos que han superado las conjeturas hacia la confianza basada en datos.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)  # Add extra spacing

        # Action buttons - centered
        col_left, col_center, col_right = st.columns([1, 2, 1])
        with col_center:
            # Primary CTA - Offer Page
            if st.button("🧭 Obtener Sistema de Maestría en Decisiones - €99", key="view_offer", help="Ver nuestra solución completa de toma de decisiones", type="primary", width="stretch"):
                st.session_state["current_page"] = "offer"
                st.query_params["page"] = "offer"  # Update URL
                st.rerun()
            
            st.markdown("<div style='text-align: center; margin: 0.5rem 0; color: #666;'>o</div>", unsafe_allow_html=True)
            
            # Secondary CTA - Free Trial
            if st.button("🚀 Probar Demo", key="launch_app_main", help="Iniciar tu análisis de decisiones", width="stretch"):
                st.session_state["current_page"] = "app"
                st.query_params["page"] = "app"  # Update URL
                st.rerun()
        
        st.markdown("""
        <div style="text-align: center; margin-top: 1rem;">
            <p><em>No requiere instalación • Basado en web • Resultados instantáneos</em></p>
        </div>
        """, unsafe_allow_html=True)

    # Use Cases
    st.markdown("---")
    st.markdown("## 🏢 Perfecto Para")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        ### Planificación Estratégica
        - Decisiones de entrada al mercado
        - Elección de portafolio de productos
        - Priorización de inversiones
        - Asignación de recursos
        """)

    with col2:
        st.markdown("""
        ### Cambios Operacionales
        - Implementaciones tecnológicas
        - Mejoras de procesos
        - Reestructuración organizacional
        - Selección de proveedores
        """)

    with col3:
        st.markdown("""
        ### Evaluación de Riesgos
        - Decisiones de cumplimiento
        - Planificación de respuesta a crisis
        - Asignaciones presupuestarias
        - Evaluaciones de asociaciones
        """)

    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; padding: 2rem;">
        <p><strong>{APP_ICON} {APP_NAME} v{APP_VERSION}</strong> • Tu asistente para decisiones estratégicas</p>
    </div>
    """, unsafe_allow_html=True)

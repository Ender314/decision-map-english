# -*- coding: utf-8 -*-
"""
Offer Landing Page for Decider Pro - Sistema de Maestría en Decisiones
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
        if st.button("← Inicio", key="nav_to_landing", help="Volver a la página principal"):
            st.session_state["current_page"] = "landing"
            st.query_params.clear()  # Clear URL parameters
            st.rerun()
    with col4:
        if st.button("🚀 Demo Gratis", key="nav_to_app", help="Probar la aplicación"):
            st.session_state["current_page"] = "app"
            st.query_params["page"] = "app"
            st.rerun()
    
    st.markdown("---")
    
    # Hero Section
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">🧭 Sistema de Maestría en Decisiones</div>
        <div class="hero-subtitle">Para profesionales ambiciosos y dueños de negocio</div>
        <div class="dream-outcome">
            💎 "Toma cada decisión importante de negocio o carrera con claridad y confianza — en minutos, no en meses."
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Positioning Line
    st.markdown("""
    <div style="text-align: center; font-size: 1.5rem; font-weight: 600; color: #2c3e50; margin: 2rem 0;">
        🎯 Convierte el sobreanálisis en claridad — y la claridad en progreso.
    </div>
    """, unsafe_allow_html=True)
    
    # Problem/Solution Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 😰 El Problema que Enfrentas a Diario
        
        - **Parálisis por Análisis**: Semanas en decisiones que deberían tomar horas
        - **Ceguera de Sesgos**: Fallos obvios en tu razonamiento que no ves
        - **Proceso Inconsistente**: Un enfoque diferente para cada decisión
        - **Arrepentimiento y Duda**: Cuestionando tus elecciones después de tomarlas
        - **Oportunidades Perdidas**: Mientras deliberas, otros actúan
        """)
    
    with col2:
        st.markdown("""
        ### ⚡ Tu Nuevo Superpoder para Decidir
        
        - **Marco Estructurado**: El mismo proceso probado cada vez
        - **Detección de Sesgos**: Verificaciones integradas para trampas cognitivas
        - **Claridad Visual**: Ve tus opciones mapeadas y ponderadas
        - **Impulso de Confianza**: Decisiones respaldadas por datos que puedes defender
        - **Velocidad**: Reduce el tiempo de decisión un 70% sin sacrificar calidad
        """)
    
    # Offer Stack
    st.markdown("""
    <div class="offer-stack">
        <h2 style="text-align: center; color: #2c3e50; margin-bottom: 2rem;">🚀 Sistema Completo de Maestría en Decisiones</h2>
    """, unsafe_allow_html=True)
    
    # Component 1
    st.markdown("""
    <div class="component-item">
        <div>
            <div class="component-name">⚡ Decider Pro App (Edición Pro)</div>
            <div class="component-desc">Motor de toma de decisiones con verificación de sesgos, herramientas de ponderación e informes visuales</div>
        </div>
        <div class="component-value">€300</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Component 2
    st.markdown("""
    <div class="component-item">
        <div>
            <div class="component-name">📋 Biblioteca de Plantillas de Decisión</div>
            <div class="component-desc">15+ plantillas prediseñadas (ej. "Contratar o Subcontratar", "Aceptar Oferta de Trabajo", "Lanzar o Esperar")</div>
        </div>
        <div class="component-value">€150</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Component 3
    st.markdown("""
    <div class="component-item">
        <div>
            <div class="component-name">🔍 Checklist de Auditoría de Sesgos</div>
            <div class="component-desc">Lista de verificación de sesgos cognitivos usada en revisiones estilo McKinsey</div>
        </div>
        <div class="component-value">€50</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Component 4
    st.markdown("""
    <div class="component-item">
        <div>
            <div class="component-name">🤖 Revisión de Decisiones con IA</div>
            <div class="component-desc">Sube tu razonamiento → La IA identifica puntos ciegos y sugiere mejoras</div>
        </div>
        <div class="component-value">€250</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Component 5
    st.markdown("""
    <div class="component-item">
        <div>
            <div class="component-name">🎯 Reto de Claridad de 30 Días</div>
            <div class="component-desc">Micro-decisiones diarias guiadas para entrenar un pensamiento más rápido y racional</div>
        </div>
        <div class="component-value">€100</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Component 6
    st.markdown("""
    <div class="component-item">
        <div>
            <div class="component-name">🔄 Actualizaciones de por Vida + Acceso Prioritario</div>
            <div class="component-desc">Nuevas plantillas continuas y actualizaciones de ciencia de decisiones</div>
        </div>
        <div class="component-value">€100</div>
    </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Pricing Section
    st.markdown("""
    <div class="pricing-section">
        <h2>💰 Inversión</h2>
        <div style="margin: 1rem 0;">
            <span class="original-price">€950+</span>
            <span style="font-size: 1.2rem;">Valor Total Percibido</span>
        </div>
        <div style="margin: 2rem 0;">
            <div style="font-size: 1.5rem; margin-bottom: 1rem;">Tu Inversión Hoy:</div>
            <div class="offer-price">€99</div>
            <div style="font-size: 1.2rem; margin-top: 1rem;">Pago único</div>
            <div style="font-size: 1rem; opacity: 0.8; margin-top: 0.5rem;">o €12/mes</div>
        </div>
        <div style="font-size: 1.3rem; font-weight: 600; margin-top: 2rem;">
            💥 Ahorra €851+ (89% DESCUENTO)
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Scarcity Alert
    st.markdown("""
    <div class="scarcity-alert">
        🔥 Precio de lanzamiento para los primeros 250 usuarios — ¡47 plazas disponibles!
    </div>
    """, unsafe_allow_html=True)
    
    # Guarantee
    st.markdown("""
    <div class="guarantee-box">
        <h3>🛡️ Garantía de 30 Días "Mejor Decisión"</h3>
        <p style="font-size: 1.1rem; margin: 1rem 0;">
            Si no sientes <strong>2× más claridad</strong> en cualquier decisión en 30 días, 
            obtén un <strong>reembolso completo</strong> — sin preguntas.
        </p>
        <p style="font-style: italic; color: #6c757d;">
            Estamos tan seguros de que este sistema transformará tu toma de decisiones que asumimos todo el riesgo.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Social Proof / Testimonials
    st.markdown("### 🗣️ Lo que Dicen los Primeros Usuarios")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="testimonial-box">
            <p><em>"Solía pasar semanas agonizando sobre decisiones de negocio. Ahora tengo claridad en horas. Este sistema se pagó solo con mi primera decisión importante."</em></p>
            <strong>— Sara M., Directora de Marketing</strong>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="testimonial-box">
            <p><em>"Solo el checklist de sesgos vale el precio. Me pillé a mí mismo cometiendo un error de €50k por sesgo de confirmación."</em></p>
            <strong>— David L., Dueño de Pequeña Empresa</strong>
        </div>
        """, unsafe_allow_html=True)
    
    # Feature Highlights
    st.markdown("### ⭐ Por Qué Funciona Este Sistema")
    
    st.markdown("""
    <div class="feature-grid">
        <div class="feature-card">
            <div class="feature-icon">🧠</div>
            <h4>Basado en Ciencia</h4>
            <p>Basado en economía conductual ganadora del Premio Nobel y marcos de decisión estilo McKinsey</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">⚡</div>
            <h4>Ultra Rápido</h4>
            <p>Obtén claridad en minutos, no en meses. Perfecto para profesionales ocupados que necesitan actuar rápido</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <h4>Proceso Probado</h4>
            <p>El mismo enfoque sistemático usado por empresas Fortune 500, ahora disponible para individuos</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Final CTA Section
    st.markdown("""
    <div style="text-align: center; margin: 3rem 0;">
        <h2>¿Listo para Dominar tus Decisiones?</h2>
        <p style="font-size: 1.2rem; color: #6c757d; margin: 1rem 0;">
            Únete a 203 profesionales ambiciosos que ya han transformado su toma de decisiones
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # CTA Buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🚀 OBTENER ACCESO INMEDIATO - €99", key="main_cta", help="Pago único, acceso de por vida"):
            st.session_state["current_page"] = "app"
            st.query_params["page"] = "app"
            st.rerun()
        
        st.markdown("<div style='text-align: center; margin: 1rem 0;'>o</div>", unsafe_allow_html=True)
        
        if st.button("💳 Empezar por €12/mes", key="monthly_cta", help="Suscripción mensual"):
            st.session_state["current_page"] = "app"
            st.query_params["page"] = "app"
            st.rerun()
    
    # Trust Signals
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0; color: #6c757d;">
        <p>🔒 Pago seguro • 💯 Garantía 30 días • ⚡ Acceso instantáneo</p>
        <p style="font-size: 0.9rem;">Usado por profesionales en Google, Microsoft, McKinsey y más de 200 empresas</p>
    </div>
    """, unsafe_allow_html=True)
    
    # FAQ Section
    with st.expander("❓ Preguntas Frecuentes"):
        st.markdown("""
        **P: ¿En qué se diferencia esto de hacer una simple lista de pros y contras?**
        R: Nuestro sistema incluye detección de sesgos, criterios ponderados, planificación de escenarios y análisis visual que revela puntos ciegos que una lista simple no puede detectar.
        
        **P: ¿Necesito habilidades técnicas?**
        R: Ninguna. Si puedes usar un navegador web, puedes dominar este sistema en minutos.
        
        **P: ¿Qué pasa si no estoy satisfecho?**
        R: Reembolso completo en 30 días, sin preguntas. Estamos seguros de que verás resultados inmediatamente.
        
        **P: ¿Esto sirve también para decisiones personales?**
        R: ¡Absolutamente! Cambios de carrera, compras importantes, decisiones de relaciones - el marco funciona para cualquier elección importante.
        
        **P: ¿Cuánto tiempo tarda en verse resultados?**
        R: La mayoría de usuarios reportan pensar más claro desde su primera decisión. El reto de 30 días construye maestría a largo plazo.
        """)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #6c757d; font-size: 0.9rem;">
        <p>© 2024 {APP_NAME} • Sistema de Maestría en Decisiones</p>
        <p>Transforma tu toma de decisiones, transforma tu vida.</p>
    </div>
    """, unsafe_allow_html=True)

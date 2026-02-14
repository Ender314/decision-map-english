# -*- coding: utf-8 -*-
"""
Decision Templates for Decider Pro
Pre-populated templates to help users get started quickly and understand the app.
"""

import streamlit as st
import uuid
from typing import Dict, List, Any


# Template definitions with humor
DECISION_TEMPLATES = {
    "hire_vs_outsource": {
        "id": "hire_vs_outsource",
        "name": "¿Contratamos o subcontratamos?",
        "tagline": "Porque 'mi cuñado sabe de esto' no es una alternativa válida",
        "icon": "👥",
        "category": "Recursos Humanos",
        "tiempo": "Un par de horas",
        "decision": "Decidir si contratar un empleado a tiempo completo para cubrir una función clave o subcontratar el servicio a una agencia o freelancer",
        "objetivo": "Cubrir la necesidad operativa optimizando coste, calidad y flexibilidad a largo plazo",
        "impacto": {"corto": "medio", "medio": "alto", "largo": "alto"},
        "alternativas": [
            "Contratar empleado a tiempo completo",
            "Subcontratar a agencia especializada",
            "Contratar freelancer a largo plazo",
            "No hacer nada (mantener status quo)"
        ],
        "prioridades": [
            "Coste total (salario + beneficios vs factura)",
            "Calidad y consistencia del trabajo",
            "Flexibilidad para escalar",
            "Control y supervisión directa",
            "Velocidad de implementación"
        ],
        "mcda_scores": {
            "Contratar empleado a tiempo completo": {"Coste total (salario + beneficios vs factura)": 2.0, "Calidad y consistencia del trabajo": 4.0, "Flexibilidad para escalar": 2.0, "Control y supervisión directa": 5.0, "Velocidad de implementación": 2.0},
            "Subcontratar a agencia especializada": {"Coste total (salario + beneficios vs factura)": 3.0, "Calidad y consistencia del trabajo": 4.0, "Flexibilidad para escalar": 4.5, "Control y supervisión directa": 2.5, "Velocidad de implementación": 4.0},
            "Contratar freelancer a largo plazo": {"Coste total (salario + beneficios vs factura)": 4.0, "Calidad y consistencia del trabajo": 3.5, "Flexibilidad para escalar": 4.0, "Control y supervisión directa": 3.0, "Velocidad de implementación": 3.5},
            "No hacer nada (mantener status quo)": {"Coste total (salario + beneficios vs factura)": 5.0, "Calidad y consistencia del trabajo": 2.0, "Flexibilidad para escalar": 1.0, "Control y supervisión directa": 5.0, "Velocidad de implementación": 5.0}
        },
        "scenarios": {
            "Contratar empleado a tiempo completo": {"worst_score": 3, "best_score": 8, "p_best_pct": 60, "worst_desc": "No encaja en la cultura, hay que despedir en 6 meses", "best_desc": "Se convierte en pieza clave del equipo"},
            "Subcontratar a agencia especializada": {"worst_score": 4, "best_score": 7, "p_best_pct": 70, "worst_desc": "Resultados mediocres, dependencia excesiva", "best_desc": "Profesionalismo y escalabilidad sin complicaciones"},
            "Contratar freelancer a largo plazo": {"worst_score": 2, "best_score": 8, "p_best_pct": 50, "worst_desc": "Desaparece o sube precios drásticamente", "best_desc": "Relación estable, económica y de confianza"},
            "No hacer nada (mantener status quo)": {"worst_score": 1, "best_score": 4, "p_best_pct": 30, "worst_desc": "El problema empeora y afecta al negocio", "best_desc": "Se resuelve solo (poco probable)"}
        }
    },
    
    "launch_timing": {
        "id": "launch_timing",
        "name": "Lanzar ahora vs esperar",
        "tagline": "El perfeccionismo es el enemigo del progreso... y del sueño",
        "icon": "🚀",
        "category": "Producto",
        "tiempo": "Una mañana",
        "decision": "Decidir si lanzar el producto/feature ahora con funcionalidad básica o esperar a tener una versión más completa",
        "objetivo": "Maximizar el impacto del lanzamiento equilibrando velocidad al mercado con calidad percibida",
        "impacto": {"corto": "alto", "medio": "alto", "largo": "medio"},
        "alternativas": [
            "Lanzar ahora (MVP)",
            "Esperar 1 mes más",
            "Esperar 3 meses (versión completa)",
            "Lanzamiento gradual (beta cerrada)"
        ],
        "prioridades": [
            "Velocidad al mercado",
            "Calidad percibida por usuarios",
            "Feedback temprano para iterar",
            "Riesgo reputacional",
            "Coste de oportunidad"
        ],
        "mcda_scores": {
            "Lanzar ahora (MVP)": {"Velocidad al mercado": 5.0, "Calidad percibida por usuarios": 2.5, "Feedback temprano para iterar": 5.0, "Riesgo reputacional": 2.0, "Coste de oportunidad": 5.0},
            "Esperar 1 mes más": {"Velocidad al mercado": 3.5, "Calidad percibida por usuarios": 3.5, "Feedback temprano para iterar": 3.5, "Riesgo reputacional": 3.5, "Coste de oportunidad": 3.0},
            "Esperar 3 meses (versión completa)": {"Velocidad al mercado": 1.5, "Calidad percibida por usuarios": 4.5, "Feedback temprano para iterar": 2.0, "Riesgo reputacional": 4.5, "Coste de oportunidad": 1.5},
            "Lanzamiento gradual (beta cerrada)": {"Velocidad al mercado": 4.0, "Calidad percibida por usuarios": 3.0, "Feedback temprano para iterar": 4.5, "Riesgo reputacional": 4.0, "Coste de oportunidad": 4.0}
        },
        "scenarios": {
            "Lanzar ahora (MVP)": {"worst_score": 2, "best_score": 9, "p_best_pct": 45, "worst_desc": "Usuarios decepcionados, malas reseñas iniciales", "best_desc": "Capturamos mercado, iteramos rápido con feedback real"},
            "Esperar 1 mes más": {"worst_score": 4, "best_score": 7, "p_best_pct": 60, "worst_desc": "Competidor nos adelanta, mes perdido", "best_desc": "Lanzamiento más sólido, buena recepción"},
            "Esperar 3 meses (versión completa)": {"worst_score": 3, "best_score": 6, "p_best_pct": 50, "worst_desc": "Mercado cambió, producto ya no relevante", "best_desc": "Producto pulido pero llegamos tarde"},
            "Lanzamiento gradual (beta cerrada)": {"worst_score": 4, "best_score": 8, "p_best_pct": 65, "worst_desc": "Beta se alarga, usuarios beta se aburren", "best_desc": "Feedback valioso, lanzamiento público exitoso"}
        }
    },
    
    "job_offer": {
        "id": "job_offer",
        "name": "Aceptar oferta de trabajo",
        "tagline": "Tu madre opina que deberías aceptar. Veamos qué dicen los datos",
        "icon": "💼",
        "category": "Carrera Profesional",
        "tiempo": "Un par de horas",
        "decision": "Decidir si aceptar la nueva oferta de trabajo o mantener mi posición actual",
        "objetivo": "Tomar la decisión que maximice mi satisfacción profesional y personal a largo plazo",
        "impacto": {"corto": "alto", "medio": "crítico", "largo": "crítico"},
        "alternativas": [
            "Aceptar la nueva oferta",
            "Rechazar y quedarme donde estoy",
            "Negociar mejores condiciones",
            "Usar la oferta para negociar en mi trabajo actual"
        ],
        "prioridades": [
            "Compensación total",
            "Oportunidades de crecimiento",
            "Balance vida-trabajo",
            "Cultura y ambiente laboral",
            "Estabilidad y seguridad"
        ],
        "mcda_scores": {
            "Aceptar la nueva oferta": {"Compensación total": 4.5, "Oportunidades de crecimiento": 4.0, "Balance vida-trabajo": 3.0, "Cultura y ambiente laboral": 3.0, "Estabilidad y seguridad": 2.5},
            "Rechazar y quedarme donde estoy": {"Compensación total": 3.0, "Oportunidades de crecimiento": 2.5, "Balance vida-trabajo": 4.0, "Cultura y ambiente laboral": 4.0, "Estabilidad y seguridad": 4.5},
            "Negociar mejores condiciones": {"Compensación total": 4.0, "Oportunidades de crecimiento": 4.0, "Balance vida-trabajo": 3.5, "Cultura y ambiente laboral": 3.0, "Estabilidad y seguridad": 3.0},
            "Usar la oferta para negociar en mi trabajo actual": {"Compensación total": 3.5, "Oportunidades de crecimiento": 3.0, "Balance vida-trabajo": 4.0, "Cultura y ambiente laboral": 3.5, "Estabilidad y seguridad": 3.5}
        },
        "scenarios": {
            "Aceptar la nueva oferta": {"worst_score": 2, "best_score": 9, "p_best_pct": 55, "worst_desc": "No encajo, ambiente tóxico, me arrepiento", "best_desc": "Salto de carrera, crecimiento acelerado"},
            "Rechazar y quedarme donde estoy": {"worst_score": 3, "best_score": 6, "p_best_pct": 60, "worst_desc": "Me estanco, oportunidad perdida para siempre", "best_desc": "Estabilidad, mejora gradual"},
            "Negociar mejores condiciones": {"worst_score": 3, "best_score": 9, "p_best_pct": 40, "worst_desc": "Retiran la oferta, quedo sin nada", "best_desc": "Mejor paquete, mejor posición"},
            "Usar la oferta para negociar en mi trabajo actual": {"worst_score": 2, "best_score": 7, "p_best_pct": 35, "worst_desc": "Jefe se molesta, relación dañada", "best_desc": "Contraoferta competitiva, me quedo mejor"}
        }
    },
    
    "market_expansion": {
        "id": "market_expansion",
        "name": "Expandir a nuevo mercado",
        "tagline": "Conquistar el mundo, un mercado a la vez",
        "icon": "🌍",
        "category": "Estrategia",
        "tiempo": "Un par de días",
        "decision": "Decidir si expandir operaciones a un nuevo mercado geográfico o vertical",
        "objetivo": "Crecer el negocio de forma sostenible minimizando riesgos de expansión",
        "impacto": {"corto": "medio", "medio": "alto", "largo": "crítico"},
        "alternativas": [
            "Expansión agresiva inmediata",
            "Entrada gradual con piloto",
            "Partnership con empresa local",
            "Posponer y consolidar mercado actual"
        ],
        "prioridades": [
            "Potencial de ingresos",
            "Inversión requerida",
            "Riesgo operacional",
            "Tiempo hasta rentabilidad",
            "Sinergias con negocio actual"
        ],
        "mcda_scores": {
            "Expansión agresiva inmediata": {"Potencial de ingresos": 5.0, "Inversión requerida": 1.5, "Riesgo operacional": 1.5, "Tiempo hasta rentabilidad": 2.0, "Sinergias con negocio actual": 3.0},
            "Entrada gradual con piloto": {"Potencial de ingresos": 3.5, "Inversión requerida": 3.5, "Riesgo operacional": 4.0, "Tiempo hasta rentabilidad": 3.0, "Sinergias con negocio actual": 3.5},
            "Partnership con empresa local": {"Potencial de ingresos": 3.0, "Inversión requerida": 4.0, "Riesgo operacional": 3.5, "Tiempo hasta rentabilidad": 4.0, "Sinergias con negocio actual": 2.5},
            "Posponer y consolidar mercado actual": {"Potencial de ingresos": 2.0, "Inversión requerida": 5.0, "Riesgo operacional": 5.0, "Tiempo hasta rentabilidad": 5.0, "Sinergias con negocio actual": 4.5}
        },
        "scenarios": {
            "Expansión agresiva inmediata": {"worst_score": 1, "best_score": 10, "p_best_pct": 30, "worst_desc": "Fracaso costoso, afecta negocio principal", "best_desc": "Dominamos nuevo mercado rápidamente"},
            "Entrada gradual con piloto": {"worst_score": 3, "best_score": 8, "p_best_pct": 55, "worst_desc": "Piloto inconcluso, recursos desperdiciados", "best_desc": "Aprendemos y escalamos con confianza"},
            "Partnership con empresa local": {"worst_score": 3, "best_score": 7, "p_best_pct": 50, "worst_desc": "Partner no cumple, conflictos", "best_desc": "Acceso rápido con bajo riesgo"},
            "Posponer y consolidar mercado actual": {"worst_score": 4, "best_score": 6, "p_best_pct": 70, "worst_desc": "Competidor nos adelanta, oportunidad perdida", "best_desc": "Base sólida para expansión futura"}
        }
    },
    
    "tech_investment": {
        "id": "tech_investment",
        "name": "Invertir en tecnología",
        "tagline": "No, ChatGPT no puede tomar esta decisión por ti... todavía",
        "icon": "💻",
        "category": "Tecnología",
        "tiempo": "Una mañana",
        "decision": "Decidir si invertir en una nueva tecnología o sistema para el negocio",
        "objetivo": "Mejorar eficiencia operativa y competitividad con una inversión tecnológica inteligente",
        "impacto": {"corto": "bajo", "medio": "alto", "largo": "alto"},
        "alternativas": [
            "Implementar solución enterprise completa",
            "Adoptar herramienta SaaS existente",
            "Desarrollar solución interna",
            "Mantener procesos actuales"
        ],
        "prioridades": [
            "Coste total de propiedad",
            "Tiempo de implementación",
            "Escalabilidad futura",
            "Facilidad de adopción",
            "Soporte y mantenimiento"
        ],
        "mcda_scores": {
            "Implementar solución enterprise completa": {"Coste total de propiedad": 1.5, "Tiempo de implementación": 2.0, "Escalabilidad futura": 5.0, "Facilidad de adopción": 2.5, "Soporte y mantenimiento": 4.5},
            "Adoptar herramienta SaaS existente": {"Coste total de propiedad": 3.5, "Tiempo de implementación": 4.5, "Escalabilidad futura": 3.5, "Facilidad de adopción": 4.0, "Soporte y mantenimiento": 4.0},
            "Desarrollar solución interna": {"Coste total de propiedad": 2.5, "Tiempo de implementación": 1.5, "Escalabilidad futura": 4.0, "Facilidad de adopción": 3.0, "Soporte y mantenimiento": 2.0},
            "Mantener procesos actuales": {"Coste total de propiedad": 5.0, "Tiempo de implementación": 5.0, "Escalabilidad futura": 1.5, "Facilidad de adopción": 5.0, "Soporte y mantenimiento": 3.0}
        },
        "scenarios": {
            "Implementar solución enterprise completa": {"worst_score": 2, "best_score": 9, "p_best_pct": 45, "worst_desc": "Implementación fallida, costes disparados", "best_desc": "Transformación digital exitosa"},
            "Adoptar herramienta SaaS existente": {"worst_score": 4, "best_score": 7, "p_best_pct": 65, "worst_desc": "No se adapta bien, dependencia del proveedor", "best_desc": "Rápido valor, equipo productivo"},
            "Desarrollar solución interna": {"worst_score": 1, "best_score": 8, "p_best_pct": 35, "worst_desc": "Proyecto interminable, nunca se termina", "best_desc": "Solución perfecta a medida"},
            "Mantener procesos actuales": {"worst_score": 2, "best_score": 5, "p_best_pct": 50, "worst_desc": "Quedamos obsoletos, perdemos competitividad", "best_desc": "Ahorramos dinero, funciona por ahora"}
        }
    },
    
    "vendor_change": {
        "id": "vendor_change",
        "name": "Cambiar de proveedor",
        "tagline": "Porque 'siempre lo hemos hecho así' no es estrategia",
        "icon": "🔄",
        "category": "Operaciones",
        "tiempo": "Un par de horas",
        "decision": "Decidir si cambiar a un nuevo proveedor o mantener la relación actual",
        "objetivo": "Optimizar la cadena de suministro equilibrando coste, calidad y riesgo de transición",
        "impacto": {"corto": "medio", "medio": "medio", "largo": "medio"},
        "alternativas": [
            "Cambiar completamente al nuevo proveedor",
            "Mantener proveedor actual",
            "Diversificar con ambos proveedores",
            "Renegociar con proveedor actual"
        ],
        "prioridades": [
            "Precio y condiciones",
            "Calidad del producto/servicio",
            "Fiabilidad de entregas",
            "Coste de transición",
            "Relación a largo plazo"
        ],
        "mcda_scores": {
            "Cambiar completamente al nuevo proveedor": {"Precio y condiciones": 4.5, "Calidad del producto/servicio": 3.5, "Fiabilidad de entregas": 3.0, "Coste de transición": 2.0, "Relación a largo plazo": 2.5},
            "Mantener proveedor actual": {"Precio y condiciones": 2.5, "Calidad del producto/servicio": 4.0, "Fiabilidad de entregas": 4.5, "Coste de transición": 5.0, "Relación a largo plazo": 4.0},
            "Diversificar con ambos proveedores": {"Precio y condiciones": 3.5, "Calidad del producto/servicio": 3.5, "Fiabilidad de entregas": 4.0, "Coste de transición": 3.0, "Relación a largo plazo": 3.5},
            "Renegociar con proveedor actual": {"Precio y condiciones": 3.5, "Calidad del producto/servicio": 4.0, "Fiabilidad de entregas": 4.5, "Coste de transición": 4.5, "Relación a largo plazo": 4.0}
        },
        "scenarios": {
            "Cambiar completamente al nuevo proveedor": {"worst_score": 2, "best_score": 8, "p_best_pct": 45, "worst_desc": "Problemas de calidad, entregas fallidas", "best_desc": "Ahorro significativo, mejor servicio"},
            "Mantener proveedor actual": {"worst_score": 3, "best_score": 5, "p_best_pct": 60, "worst_desc": "Precios suben, nos quedamos atrapados", "best_desc": "Estabilidad, relación de confianza"},
            "Diversificar con ambos proveedores": {"worst_score": 3, "best_score": 7, "p_best_pct": 55, "worst_desc": "Complejidad operativa, costes ocultos", "best_desc": "Mejor negociación, menos riesgo"},
            "Renegociar con proveedor actual": {"worst_score": 3, "best_score": 7, "p_best_pct": 50, "worst_desc": "No ceden, relación deteriorada", "best_desc": "Mejores condiciones sin cambiar"}
        }
    }
}


def get_template_list() -> List[Dict[str, str]]:
    """Get list of templates for display."""
    return [
        {
            "id": t["id"],
            "name": t["name"],
            "tagline": t["tagline"],
            "icon": t["icon"],
            "category": t["category"]
        }
        for t in DECISION_TEMPLATES.values()
    ]


def load_template(template_id: str) -> bool:
    """
    Load a template into session state.
    Returns True if successful, False otherwise.
    """
    if template_id not in DECISION_TEMPLATES:
        return False
    
    template = DECISION_TEMPLATES[template_id]
    
    # Clear existing data (preserve system keys)
    keys_to_preserve = [
        k for k in st.session_state.keys()
        if k.startswith('_') or k in ['current_page', 'show_sidebar', 'show_template_selector']
    ]
    current_state = {k: st.session_state[k] for k in keys_to_preserve}
    st.session_state.clear()
    st.session_state.update(current_state)
    
    # Load basic data
    st.session_state["decision"] = template["decision"]
    st.session_state["objetivo"] = template["objetivo"]
    st.session_state["tiempo"] = template["tiempo"]
    st.session_state["tiempo_user_override"] = False
    
    # Load impact
    st.session_state["impacto_corto"] = template["impacto"]["corto"]
    st.session_state["impacto_medio"] = template["impacto"]["medio"]
    st.session_state["impacto_largo"] = template["impacto"]["largo"]
    
    # Load alternatives with IDs
    alts = []
    for alt_text in template["alternativas"]:
        alts.append({"id": str(uuid.uuid4()), "text": alt_text})
    st.session_state["alts"] = alts
    
    # Load priorities with IDs
    priorities = []
    for prio_text in template["prioridades"]:
        priorities.append({"id": str(uuid.uuid4()), "text": prio_text})
    st.session_state["priorities"] = priorities
    
    # Load MCDA criteria (from priorities with position-based weights)
    mcda_criteria = []
    for i, prio in enumerate(template["prioridades"]):
        weight = 1.0 / (i + 1)  # Position-based: 1st=1, 2nd=0.5, etc.
        mcda_criteria.append({"name": prio, "weight": weight})
    st.session_state["mcda_criteria"] = mcda_criteria
    st.session_state["weights_user_override"] = False
    
    # Load MCDA scores
    mcda_scores = {}
    for alt_name, scores in template["mcda_scores"].items():
        mcda_scores[alt_name] = scores
    st.session_state["mcda_scores"] = mcda_scores
    
    # Load scenarios
    scenarios = {}
    for alt in alts:
        alt_name = alt["text"]
        if alt_name in template["scenarios"]:
            scenario_data = template["scenarios"][alt_name]
            scenarios[alt["id"]] = {
                "name": alt_name,
                "worst_desc": scenario_data["worst_desc"],
                "worst_score": float(scenario_data["worst_score"]),
                "best_desc": scenario_data["best_desc"],
                "best_score": float(scenario_data["best_score"]),
                "p_best": scenario_data["p_best_pct"] / 100.0,
                "p_best_pct": scenario_data["p_best_pct"]
            }
    st.session_state["scenarios"] = scenarios
    
    # Initialize empty collections for other data
    st.session_state["kpis"] = []
    st.session_state["timeline_items"] = []
    st.session_state["stakeholders"] = []
    st.session_state["past_decisions"] = []
    st.session_state["quantitative_notes"] = ""
    st.session_state["qualitative_notes"] = ""
    st.session_state["estrategia_corporativa"] = ""
    st.session_state["risks"] = {}
    st.session_state["retro"] = {}
    
    return True


def render_template_selector():
    """Render the template selection modal/UI."""
    st.markdown("### 📋 Plantillas de Decisión")
    st.markdown("*Selecciona una plantilla para empezar con datos de ejemplo y entender cómo funciona la app.*")
    st.markdown("")
    
    templates = get_template_list()
    
    # Display all templates in a 2-column grid
    cols = st.columns(2)
    for i, template in enumerate(templates):
        with cols[i % 2]:
            st.markdown(f"""
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 1rem; margin-bottom: 0.5rem; background: var(--secondary-background-color, #f8f9fa);">
                <div style="font-size: 1.5rem; margin-bottom: 0.3rem;">{template['icon']} <span style="font-size: 0.7rem; color: #888;">{template['category']}</span></div>
                <div style="font-weight: 600;">{template['name']}</div>
                <div style="font-size: 0.85rem; color: #666; font-style: italic;">{template['tagline']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"Usar plantilla", key=f"load_template_{template['id']}", width="stretch"):
                if load_template(template['id']):
                    st.session_state["_template_loaded"] = True
                    st.session_state["_loaded_template_name"] = template['name']
                    st.session_state["show_template_selector"] = False  # Hide menu after selection
                    st.rerun()


def render_template_button_in_sidebar():
    """Render a button to access templates from the sidebar."""
    if st.button("📋 Cargar Plantilla", width="stretch", help="Cargar una plantilla de decisión de ejemplo"):
        st.session_state["show_template_selector"] = True
        st.rerun()

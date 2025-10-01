# -*- coding: utf-8 -*-
"""
Resultados (Results) tab component for Lambda Pro.
Handles executive summary dashboard with comprehensive analysis.
"""

import streamlit as st
import pandas as pd
from datetime import date

from config.constants import IMPACT_MAP, PLAZO_ORDER, YMAX
from utils.calculations import (
    mcda_totals_and_ranking, scenario_expected_value, 
    calculate_relevance_percentage
)
from utils.visualizations import (
    create_impact_chart, create_results_ranking_chart, 
    create_scenario_summary_chart
)


def render_decision_overview(relevance_pct: float):
    """Render the decision overview section."""
    st.markdown("## 🎯 Visión General de la Decisión")
    
    # Key metrics row
    alt_names = [a["text"].strip() for a in st.session_state.get("alts", []) if a["text"].strip()]
    prioridad_names = [p["text"].strip() for p in st.session_state.get("priorities", []) if p["text"].strip()]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Relevancia Estimada",
            value=f"{int(relevance_pct)}%",
            help="Basado en el análisis de impacto temporal"
        )
    
    with col2:
        st.metric(
            label="Alternativas",
            value=len(alt_names),
            help="Opciones identificadas para la decisión"
        )
    
    with col3:
        st.metric(
            label="Criterios",
            value=len(prioridad_names),
            help="Prioridades definidas para la evaluación"
        )
    
    with col4:
        tiempo_asignado = st.session_state.get("tiempo", "No definido")
        st.metric(
            label="Tiempo Asignado",
            value=tiempo_asignado,
            help="Tiempo dedicado al análisis de esta decisión"
        )
    
    # Decision description
    decision_text = st.session_state.get("decision", "").strip()
    if decision_text:
        st.markdown("### Descripción de la Decisión")
        st.markdown(f"*{decision_text}*")
    
    objetivo_text = st.session_state.get("objetivo", "").strip()
    if objetivo_text:
        st.markdown("### Objetivo")
        st.markdown(f"*{objetivo_text}*")


def render_impact_analysis(relevance_pct: float):
    """Render the impact analysis section."""
    st.markdown("## 📈 Análisis de Impacto")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Recreate the impact visualization
        impacto_corto = st.session_state.get("impacto_corto", "bajo")
        impacto_medio = st.session_state.get("impacto_medio", "medio")
        impacto_largo = st.session_state.get("impacto_largo", "bajo")
        
        df = pd.DataFrame([
            {"Plazo": "corto", "Impacto": impacto_corto, "Impacto_num": IMPACT_MAP[impacto_corto]},
            {"Plazo": "medio", "Impacto": impacto_medio, "Impacto_num": IMPACT_MAP[impacto_medio]},
            {"Plazo": "largo", "Impacto": impacto_largo, "Impacto_num": IMPACT_MAP[impacto_largo]},
        ])
        
        try:
            fig = create_impact_chart(df, relevance_pct)
            fig.update_layout(title="Curva de Impacto Temporal")
            fig.update_yaxes(
                tickmode="array", 
                tickvals=[0, 5, 10, 15],
                ticktext=["Bajo", "Medio", "Alto", "Crítico"]
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error al generar el gráfico de impacto: {str(e)}")
            st.info("💡 Intenta recargar la página o verificar los datos de impacto")
    
    with col2:
        st.markdown("### Impacto por Plazo")
        impact_data = [
            {"Plazo": "Corto", "Nivel": impacto_corto.title()},
            {"Plazo": "Medio", "Nivel": impacto_medio.title()},
            {"Plazo": "Largo", "Nivel": impacto_largo.title()}
        ]
        
        for item in impact_data:
            color = {"Bajo": "🟢", "Medio": "🟡", "Alto": "🟠", "Crítico": "🔴"}.get(item["Nivel"], "⚪")
            st.markdown(f"**{item['Plazo']}:** {color} {item['Nivel']}")
        
        # Recommendation based on relevancia
        st.markdown("### Recomendación")
        if relevance_pct <= 20:
            st.success("✅ Decisión de baja prioridad")
        elif relevance_pct <= 45:
            st.info("ℹ️ Decisión de prioridad media")
        elif relevance_pct <= 80:
            st.warning("⚠️ Decisión de alta prioridad")
        else:
            st.error("🚨 Decisión crítica")


def render_mcda_ranking():
    """Render the MCDA ranking section."""
    st.markdown("## 🏆 Ranking de Alternativas (MCDA)")
    
    # Get MCDA data
    crit = st.session_state.get("mcda_criteria", [])
    scores_df = st.session_state.get("mcda_scores_df", pd.DataFrame())
    
    if scores_df.empty or len(crit) == 0:
        st.info("💡 Complete la evaluación MCDA para ver el ranking de alternativas")
        return []
    
    totals, ranking_list = mcda_totals_and_ranking(scores_df.copy(), crit)
    
    if not ranking_list:
        st.info("💡 No hay datos de ranking disponibles")
        return []
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Ranking table
        st.markdown("### Ranking Final")
        ranking_df = pd.DataFrame(ranking_list)
        ranking_df['Posición'] = range(1, len(ranking_df) + 1)
        ranking_df['Puntuación'] = ranking_df['score'].round(2)
        ranking_df = ranking_df[['Posición', 'alternativa', 'Puntuación']]
        ranking_df.columns = ['#', 'Alternativa', 'Puntuación']
        
        # Style the dataframe
        st.dataframe(
            ranking_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "#": st.column_config.NumberColumn("Posición", width="small"),
                "Alternativa": st.column_config.TextColumn("Alternativa", width="large"),
                "Puntuación": st.column_config.NumberColumn("Puntuación", format="%.2f", width="medium")
            }
        )
    
    with col2:
        # Horizontal bar chart of rankings
        st.markdown("### Comparación Visual")
        try:
            fig = create_results_ranking_chart(ranking_list)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error al generar el gráfico de ranking: {str(e)}")
            st.info("💡 Verifica que los datos de evaluación MCDA estén completos")
    
    # Criteria weights
    st.markdown("### Pesos de los Criterios")
    weights_data = []
    for criterion in crit:
        weights_data.append({
            "Criterio": criterion.get("name", ""),
            "Peso": f"{criterion.get('weight', 0):.1%}"
        })
    
    if weights_data:
        weights_df = pd.DataFrame(weights_data)
        st.dataframe(weights_df, hide_index=True, use_container_width=True)
    
    return ranking_list


def render_scenario_planning():
    """Render the scenario planning section."""
    scenarios_state = st.session_state.get("scenarios", {})
    if not scenarios_state:
        return
    
    st.markdown("## 🎲 Planificación de Escenarios")
    
    # Create scenario summary
    scenario_data = []
    for alt_id, scenario in scenarios_state.items():
        ev = scenario_expected_value(
            scenario.get("p_best", 0.5),
            scenario.get("worst_score", 0),
            scenario.get("best_score", 0)
        )
        scenario_data.append({
            "Alternativa": scenario.get("name", ""),
            "Mejor Caso": scenario.get("best_score", 0),
            "Peor Caso": scenario.get("worst_score", 0),
            "Prob. Mejor": f"{scenario.get('p_best_pct', 50)}%",
            "Valor Esperado": round(ev, 2)
        })
    
    if not scenario_data:
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Resumen de Escenarios")
        scenario_df = pd.DataFrame(scenario_data)
        st.dataframe(scenario_df, hide_index=True, use_container_width=True)
    
    with col2:
        st.markdown("### Valores Esperados")
        try:
            fig = create_scenario_summary_chart(scenario_data)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error al generar el gráfico de escenarios: {str(e)}")
            st.info("💡 Verifica que los datos de escenarios estén completos")


def render_information_summary():
    """Render the information summary section."""
    kpis = st.session_state.get("kpis", [])
    timeline_items = st.session_state.get("timeline_items", [])
    stakeholders = st.session_state.get("stakeholders", [])
    
    # Define valid data
    valid_kpis = [k for k in kpis if k.get("name", "").strip()]
    valid_stakeholders = [s for s in stakeholders if s.get("name", "").strip()]
    
    if not (kpis or timeline_items or stakeholders):
        return
    
    st.markdown("## 📋 Información Recopilada")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # KPIs Summary
        if kpis:
            st.markdown("### 📊 KPIs Relevantes")
            if valid_kpis:
                for kpi in valid_kpis[:5]:  # Show max 5 KPIs
                    value_str = str(kpi.get("value", "N/A"))
                    unit_str = f" {kpi.get('unit', '')}" if kpi.get("unit", "").strip() else ""
                    st.markdown(f"**{kpi.get('name', '')}:** {value_str}{unit_str}")
        
        # Timeline Summary
        if timeline_items:
            st.markdown("### 📅 Eventos Clave")
            valid_timeline = [t for t in timeline_items if t.get("event", "").strip() and t.get("date")]
            if valid_timeline:
                # Sort by date
                valid_timeline.sort(key=lambda x: x.get("date", date.today()))
                for item in valid_timeline[:3]:  # Show max 3 events
                    event_date = item.get("date")
                    date_str = event_date.strftime("%d/%m/%Y") if event_date else "N/A"
                    st.markdown(f"**{date_str}:** {item.get('event', '')}")
    
    with col2:
        # Stakeholders Summary
        if stakeholders:
            st.markdown("### 👥 Stakeholders")
            if valid_stakeholders:
                for stakeholder in valid_stakeholders[:5]:  # Show max 5 stakeholders
                    name = stakeholder.get("name", "")
                    opinion = stakeholder.get("opinion", "")
                    if opinion:
                        st.markdown(f"**{name}:** {opinion}")
                    else:
                        st.markdown(f"**{name}**")
        
        # Notes Summary
        quant_notes = st.session_state.get("quantitative_notes", "").strip()
        qual_notes = st.session_state.get("qualitative_notes", "").strip()
        
        if quant_notes or qual_notes:
            st.markdown("### 📝 Notas Adicionales")
            if quant_notes:
                st.markdown("**Cuantitativas:**")
                st.markdown(f"*{quant_notes[:200]}{'...' if len(quant_notes) > 200 else ''}*")
            if qual_notes:
                st.markdown("**Cualitativas:**")
                st.markdown(f"*{qual_notes[:200]}{'...' if len(qual_notes) > 200 else ''}*")


def render_recommendations(relevance_pct: float, ranking_list: list):
    """Render the recommendations section."""
    st.markdown("## 💡 Recomendaciones")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Próximos Pasos")
        
        # Generate recommendations based on data
        recommendations = []
        
        if relevance_pct > 80:
            recommendations.append("🚨 **Prioridad máxima**: Esta decisión requiere atención inmediata")
        elif relevance_pct > 45:
            recommendations.append("⚠️ **Alta prioridad**: Asignar recursos significativos a esta decisión")
        else:
            recommendations.append("✅ **Prioridad moderada**: Proceder con el análisis estándar")
        
        if ranking_list and len(ranking_list) > 1:
            best_alt = ranking_list[0]['alternativa']
            best_score = ranking_list[0]['score']
            second_score = ranking_list[1]['score'] if len(ranking_list) > 1 else 0
            
            if best_score - second_score > 0.5:
                recommendations.append(f"🏆 **Alternativa recomendada**: '{best_alt}' tiene una ventaja clara")
            else:
                recommendations.append("🤔 **Análisis adicional**: Las alternativas están muy reñidas")
        
        scenarios_state = st.session_state.get("scenarios", {})
        if not scenarios_state:
            recommendations.append("🎲 **Considerar escenarios**: Añadir análisis de riesgos e incertidumbre")
        
        valid_kpis = [k for k in st.session_state.get("kpis", []) if k.get("name", "").strip()]
        if len(valid_kpis) < 3:
            recommendations.append("📊 **Más datos**: Recopilar KPIs adicionales para mejor análisis")
        
        for rec in recommendations:
            st.markdown(f"- {rec}")
    
    with col2:
        st.markdown("### Resumen de Calidad")
        
        # Quality assessment
        quality_score = 0
        max_score = 7
        
        quality_items = []
        
        decision_text = st.session_state.get("decision", "").strip()
        objetivo_text = st.session_state.get("objetivo", "").strip()
        alt_names = [a["text"].strip() for a in st.session_state.get("alts", []) if a["text"].strip()]
        prioridad_names = [p["text"].strip() for p in st.session_state.get("priorities", []) if p["text"].strip()]
        scores_df = st.session_state.get("mcda_scores_df", pd.DataFrame())
        scenarios_state = st.session_state.get("scenarios", {})
        valid_kpis = [k for k in st.session_state.get("kpis", []) if k.get("name", "").strip()]
        valid_stakeholders = [s for s in st.session_state.get("stakeholders", []) if s.get("name", "").strip()]
        
        if decision_text:
            quality_score += 1
            quality_items.append("✅ Decisión definida")
        else:
            quality_items.append("❌ Falta descripción de la decisión")
        
        if objetivo_text:
            quality_score += 1
            quality_items.append("✅ Objetivo establecido")
        else:
            quality_items.append("❌ Falta definición del objetivo")
        
        if len(alt_names) >= 2:
            quality_score += 1
            quality_items.append("✅ Múltiples alternativas")
        else:
            quality_items.append("❌ Pocas alternativas identificadas")
        
        if len(prioridad_names) >= 2:
            quality_score += 1
            quality_items.append("✅ Criterios múltiples")
        else:
            quality_items.append("❌ Pocos criterios de evaluación")
        
        if not scores_df.empty:
            quality_score += 1
            quality_items.append("✅ Evaluación MCDA completa")
        else:
            quality_items.append("❌ Falta evaluación MCDA")
        
        if scenarios_state:
            quality_score += 1
            quality_items.append("✅ Análisis de escenarios")
        else:
            quality_items.append("❌ Falta análisis de escenarios")
        
        if len(valid_kpis) > 0 or len(valid_stakeholders) > 0:
            quality_score += 1
            quality_items.append("✅ Información contextual")
        else:
            quality_items.append("❌ Falta información contextual")
        
        # Quality percentage
        quality_pct = (quality_score / max_score) * 100
        
        st.metric(
            label="Completitud del Análisis",
            value=f"{quality_pct:.0f}%",
            help="Porcentaje de elementos completados en el análisis"
        )
        
        for item in quality_items:
            st.markdown(f"- {item}")


def render_resultados_tab():
    """Render the Resultados (Results) tab."""
    
    # Check if we have data to show results
    alt_names = [a["text"].strip() for a in st.session_state.get("alts", []) if a["text"].strip()]
    prioridad_names = [p["text"].strip() for p in st.session_state.get("priorities", []) if p["text"].strip()]
    
    if not alt_names or not prioridad_names:
        # Show message when no data available
        st.info("💡 **Resumen ejecutivo disponible** una vez que hayas definido **Alternativas** y **Prioridades**")
        st.markdown("Completa las pestañas anteriores para generar un resumen completo de tu análisis de decisión.")
        return
    
    # EXECUTIVE SUMMARY DASHBOARD
    st.markdown("# 📊 Resumen Ejecutivo")
    st.markdown("---")
    
    # Calculate relevance percentage
    relevance_pct = calculate_relevance_percentage(
        st.session_state.get("impacto_corto", "bajo"),
        st.session_state.get("impacto_medio", "medio"),
        st.session_state.get("impacto_largo", "bajo"),
        IMPACT_MAP
    )
    
    # Render all sections
    render_decision_overview(relevance_pct)
    st.markdown("---")
    
    render_impact_analysis(relevance_pct)
    st.markdown("---")
    
    ranking_list = render_mcda_ranking()
    st.markdown("---")
    
    render_scenario_planning()
    
    render_information_summary()
    st.markdown("---")
    
    render_recommendations(relevance_pct, ranking_list)
    st.markdown("---")
    
    # Final export reminder
    st.success("✅ **Análisis completado** - Los datos están disponibles para exportar desde la barra lateral.")

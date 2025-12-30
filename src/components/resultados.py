# -*- coding: utf-8 -*-
"""
Resultados (Results) tab - Simplified version.
Clean executive summary without over-engineering.
"""

import streamlit as st
import pandas as pd
from datetime import date
from config.constants import IMPACT_MAP
from utils.calculations import calculate_relevance_percentage, mcda_totals_and_ranking, scenario_expected_value
from utils.visualizations import create_impact_chart


def render_resultados_tab():
    """Render the Resultados (Results) tab."""
    
    # Check if we have data to show results
    alt_names = [a["text"].strip() for a in st.session_state.alts if a["text"].strip()]
    prioridad_names = [p["text"].strip() for p in st.session_state.priorities if p["text"].strip()]
    
    if not alt_names or not prioridad_names:
        st.info("💡 **Resumen ejecutivo disponible** una vez que hayas definido **Alternativas** y **Prioridades**")
        st.markdown("Completa las pestañas anteriores para generar un resumen completo de tu análisis de decisión.")
        return
    
    # EXECUTIVE SUMMARY DASHBOARD
    # st.markdown("# 📊 Resumen Ejecutivo")
    # st.markdown("---")
    
    # Calculate relevance percentage
    relevance_pct = calculate_relevance_percentage(
        st.session_state.get("impacto_corto", "bajo"),
        st.session_state.get("impacto_medio", "medio"),
        st.session_state.get("impacto_largo", "bajo"),
        IMPACT_MAP
    )
    
    # Decision Overview
    st.markdown("## 🎈 Visión General de la Decisión")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Relevancia Estimada", f"{int(relevance_pct)}%")
    with col2:
        st.metric("Alternativas", len(alt_names))
    with col3:
        st.metric("Criterios", len(prioridad_names))
    with col4:
        tiempo_asignado = st.session_state.get("tiempo", "No definido")
        st.metric("Tiempo Asignado", tiempo_asignado)
    
    # Decision description
    decision_text = st.session_state.get("decision", "").strip()
    if decision_text:
        st.markdown("### Descripción de la Decisión")
        st.markdown(f"*{decision_text}*")
    
    objetivo_text = st.session_state.get("objetivo", "").strip()
    if objetivo_text:
        st.markdown("### Objetivo")
        st.markdown(f"*{objetivo_text}*")
    
    st.markdown("---")
    
    # Impact Analysis
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
            st.info("💡 Error al generar el gráfico de impacto")
    
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
    
    st.markdown("---")
    
    # MCDA Ranking
    st.markdown("## 🏆 Ranking de Alternativas (MCDA)")
    
    crit = st.session_state.get("mcda_criteria", [])
    scores_df = st.session_state.get("mcda_scores_df", pd.DataFrame())
    
    if not scores_df.empty and len(crit) > 0:
        totals, ranking_list = mcda_totals_and_ranking(scores_df.copy(), crit)
        
        if ranking_list:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("### Ranking Final")
                ranking_df = pd.DataFrame(ranking_list)
                ranking_df['Posición'] = range(1, len(ranking_df) + 1)
                ranking_df['Puntuación'] = ranking_df['score'].round(2)
                ranking_df = ranking_df[['Posición', 'alternativa', 'Puntuación']]
                ranking_df.columns = ['#', 'Alternativa', 'Puntuación']
                
                st.dataframe(ranking_df, hide_index=True, use_container_width=True)
            
            with col2:
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
    else:
        st.info("💡 Complete la evaluación MCDA para ver el ranking de alternativas")
    
    st.markdown("---")
    
    # Scenario Planning Summary
    scenarios_state = st.session_state.get("scenarios", {})
    if scenarios_state:
        st.markdown("## 🎲 Escenarios")
        
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
        
        if scenario_data:
            scenario_df = pd.DataFrame(scenario_data)
            st.dataframe(scenario_df, hide_index=True, use_container_width=True)
    
    # Information Summary
    kpis = st.session_state.get("kpis", [])
    stakeholders = st.session_state.get("stakeholders", [])
    
    valid_kpis = [k for k in kpis if k.get("name", "").strip()]
    valid_stakeholders = [s for s in stakeholders if s.get("name", "").strip()]
    
    if valid_kpis or valid_stakeholders:
        st.markdown("---")
        st.markdown("## 📋 Información Recopilada")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if valid_kpis:
                st.markdown("### 📊 KPIs Relevantes")
                for kpi in valid_kpis[:5]:  # Show max 5 KPIs
                    value_str = str(kpi.get("value", "N/A"))
                    unit_str = f" {kpi.get('unit', '')}" if kpi.get("unit", "").strip() else ""
                    st.markdown(f"**{kpi.get('name', '')}:** {value_str}{unit_str}")
        
        with col2:
            if valid_stakeholders:
                st.markdown("### 👥 Stakeholders")
                for stakeholder in valid_stakeholders[:5]:  # Show max 5 stakeholders
                    name = stakeholder.get("name", "")
                    opinion = stakeholder.get("opinion", "")
                    if opinion:
                        st.markdown(f"**{name}:** {opinion}")
                    else:
                        st.markdown(f"**{name}**")
    
    st.markdown("---")
    
    # Recommendations
    st.markdown("## 💡 Recomendaciones")
    
    recommendations = []
    
    if relevance_pct > 80:
        recommendations.append("🚨 **Prioridad máxima**: Esta decisión requiere atención inmediata")
    elif relevance_pct > 45:
        recommendations.append("⚠️ **Alta prioridad**: Asignar recursos significativos a esta decisión")
    else:
        recommendations.append("✅ **Prioridad moderada**: Proceder con el análisis estándar")
    
    if not scores_df.empty and ranking_list and len(ranking_list) > 1:
        best_alt = ranking_list[0]['alternativa']
        best_score = ranking_list[0]['score']
        second_score = ranking_list[1]['score'] if len(ranking_list) > 1 else 0
        
        if best_score - second_score > 0.5:
            recommendations.append(f"🏆 **Alternativa recomendada**: '{best_alt}' tiene una ventaja clara")
        else:
            recommendations.append("🤔 **Análisis adicional**: Las alternativas están muy reñidas")
    
    if not scenarios_state:
        recommendations.append("🎲 **Considerar escenarios**: Añadir análisis de riesgos e incertidumbre")
    
    if len(valid_kpis) < 3:
        recommendations.append("📊 **Más datos**: Recopilar KPIs adicionales para mejor análisis")
    
    for rec in recommendations:
        st.markdown(f"- {rec}")
    
    st.markdown("---")
    st.success("✅ **Análisis completado** - Los datos están disponibles para exportar desde la barra lateral.")

# -*- coding: utf-8 -*-
"""
Información (Information) tab - Simplified version.
Clean component for KPIs, timeline, and stakeholders.
"""

import streamlit as st
import uuid
from datetime import date
import pandas as pd
from utils.visualizations import create_timeline_chart, create_kpi_bar_chart


def add_kpi(name: str = "", value: str = "", unit: str = ""):
    """Add a new KPI to the session state."""
    st.session_state.kpis.append({
        "id": str(uuid.uuid4()), 
        "name": name, 
        "value": value, 
        "unit": unit
    })


def remove_kpi(kpi_id: str):
    """Remove a KPI from the session state."""
    st.session_state.kpis = [k for k in st.session_state.kpis if k["id"] != kpi_id]


def add_timeline_item(event: str = "", date_val: date = None):
    """Add a new timeline item to the session state."""
    st.session_state.timeline_items.append({
        "id": str(uuid.uuid4()), 
        "event": event, 
        "date": date_val
    })


def remove_timeline_item(item_id: str):
    """Remove a timeline item from the session state."""
    st.session_state.timeline_items = [t for t in st.session_state.timeline_items if t["id"] != item_id]


def add_stakeholder(name: str = "", opinion: str = ""):
    """Add a new stakeholder to the session state."""
    st.session_state.stakeholders.append({
        "id": str(uuid.uuid4()), 
        "name": name, 
        "opinion": opinion
    })


def remove_stakeholder(stakeholder_id: str):
    """Remove a stakeholder from the session state."""
    st.session_state.stakeholders = [s for s in st.session_state.stakeholders if s["id"] != stakeholder_id]


def add_past_decision(decision: str = "", results: str = "", lessons: str = ""):
    """Add a new past decision to the session state."""
    st.session_state.past_decisions.append({
        "id": str(uuid.uuid4()),
        "decision": decision,
        "results": results,
        "lessons": lessons
    })


def remove_past_decision(decision_id: str):
    """Remove a past decision from the session state."""
    st.session_state.past_decisions = [d for d in st.session_state.past_decisions if d["id"] != decision_id]


def render_informacion_tab():
    """Render the Información (Information) tab."""
    
    # PAST DECISIONS Section (First - at the top)
    st.subheader("📚 Decisiones Similares Pasadas")
    
    if st.session_state.past_decisions:
        for decision in st.session_state.past_decisions:
            with st.container():
                c1, c2 = st.columns([10, 1])
                with c1:
                    # Decision description
                    new_decision = st.text_area(
                        "Decisión",
                        value=decision["decision"],
                        key=f"past_decision_{decision['id']}",
                        placeholder="Describe la decisión similar que se tomó en el pasado...",
                        height=60,
                        label_visibility="collapsed"
                    )
                    decision["decision"] = new_decision
                    
                    # Results and lessons in two columns
                    col1, col2 = st.columns(2)
                    with col1:
                        new_results = st.text_area(
                            "Resultados",
                            value=decision["results"],
                            key=f"past_results_{decision['id']}",
                            placeholder="¿Qué resultados se obtuvieron?",
                            height=80,
                            label_visibility="collapsed"
                        )
                        decision["results"] = new_results
                    
                    with col2:
                        new_lessons = st.text_area(
                            "Lecciones Aprendidas",
                            value=decision["lessons"],
                            key=f"past_lessons_{decision['id']}",
                            placeholder="¿Qué lecciones se aprendieron?",
                            height=80,
                            label_visibility="collapsed"
                        )
                        decision["lessons"] = new_lessons
                
                with c2:
                    st.markdown("##")  # Add some spacing
                    if st.button("🗑️", key=f"del_past_decision_{decision['id']}", help="Eliminar decisión"):
                        remove_past_decision(decision["id"])
                        st.rerun()
                
                st.markdown("---")
    
    if st.button("➕ Añadir Decisión Pasada", key="add_past_decision_btn", use_container_width=True):
        add_past_decision()
        st.rerun()
    
    st.markdown("##")
    
    # QUANTITATIVE DATA Section
    st.subheader("📊 Datos Cuantitativos")
    
    # KPIs Section
    st.markdown("**KPIs Relevantes**")
    
    if st.session_state.kpis:
        for kpi in st.session_state.kpis:
            c1, c2, c3, c4 = st.columns([3, 2, 2, 0.5])
            with c1:
                new_name = st.text_input(
                    "KPI",
                    value=kpi["name"],
                    key=f"kpi_name_{kpi['id']}",
                    placeholder="Nombre del KPI",
                    label_visibility="collapsed"
                )
                kpi["name"] = new_name
            with c2:
                new_value = st.text_input(
                    "Valor",
                    value=kpi["value"],
                    key=f"kpi_value_{kpi['id']}",
                    placeholder="Valor",
                    label_visibility="collapsed"
                )
                kpi["value"] = new_value
            with c3:
                new_unit = st.text_input(
                    "Unidad",
                    value=kpi["unit"],
                    key=f"kpi_unit_{kpi['id']}",
                    placeholder="Unidad",
                    label_visibility="collapsed"
                )
                kpi["unit"] = new_unit
            with c4:
                if st.button("🗑️", key=f"del_kpi_{kpi['id']}", help="Eliminar KPI"):
                    remove_kpi(kpi["id"])
                    st.rerun()
    
    if st.button("➕ Añadir KPI", key="add_kpi_btn", use_container_width=True):
        add_kpi()
        st.rerun()
    
    st.markdown("---")
    
    # Timeline Section
    st.markdown("**Timeline Clave**")
    
    if st.session_state.timeline_items:
        for item in st.session_state.timeline_items:
            c1, c2, c3 = st.columns([4, 3, 0.5])
            with c1:
                new_event = st.text_input(
                    "Evento",
                    value=item["event"],
                    key=f"timeline_event_{item['id']}",
                    placeholder="Descripción del evento",
                    label_visibility="collapsed"
                )
                item["event"] = new_event
            with c2:
                new_date = st.date_input(
                    "Fecha",
                    value=item["date"],
                    key=f"timeline_date_{item['id']}",
                    label_visibility="collapsed"
                )
                item["date"] = new_date
            with c3:
                if st.button("🗑️", key=f"del_timeline_{item['id']}", help="Eliminar evento"):
                    remove_timeline_item(item["id"])
                    st.rerun()
    
    if st.button("➕ Añadir Evento", key="add_timeline_btn", use_container_width=True):
        add_timeline_item()
        st.rerun()
    
    # Timeline Visualization
    timeline_items = [item for item in st.session_state.timeline_items 
                     if item.get("event", "").strip() and item.get("date") is not None]
    
    if timeline_items:
        try:
            fig = create_timeline_chart(timeline_items)
            if fig.data:
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.info("💡 Error al generar la visualización del timeline")
    
    # KPI Visualizations
    valid_kpis = [k for k in st.session_state.kpis if k.get("name", "").strip()]
    
    if valid_kpis:
        # KPI Cards Layout
        if len(valid_kpis) <= 3:
            cols = st.columns(len(valid_kpis))
            for i, kpi in enumerate(valid_kpis):
                with cols[i]:
                    value_str = str(kpi.get("value", "")) if kpi.get("value") else "N/A"
                    unit_str = f" {kpi.get('unit', '')}" if kpi.get("unit", "").strip() else ""
                    st.metric(
                        label=kpi.get("name", ""),
                        value=f"{value_str}{unit_str}"
                    )
        else:
            # For more than 3 KPIs, create rows of 3
            rows = (len(valid_kpis) + 2) // 3
            for row in range(rows):
                start_idx = row * 3
                end_idx = min(start_idx + 3, len(valid_kpis))
                row_kpis = valid_kpis[start_idx:end_idx]
                cols = st.columns(len(row_kpis))
                
                for i, kpi in enumerate(row_kpis):
                    with cols[i]:
                        value_str = str(kpi.get("value", "")) if kpi.get("value") else "N/A"
                        unit_str = f" {kpi.get('unit', '')}" if kpi.get("unit", "").strip() else ""
                        st.metric(
                            label=kpi.get("name", ""),
                            value=f"{value_str}{unit_str}"
                        )
        
        # Create bar chart for numeric KPIs
        numeric_kpis = []
        for kpi in valid_kpis:
            try:
                value_str = str(kpi.get("value", ""))
                if value_str and value_str.replace(".", "").replace("-", "").replace(",", "").isdigit():
                    numeric_value = float(value_str.replace(",", ""))
                    numeric_kpis.append({
                        "name": kpi.get("name", ""),
                        "value": numeric_value,
                        "unit": kpi.get("unit", "")
                    })
            except (ValueError, TypeError):
                continue
        
        if len(numeric_kpis) > 1:
            st.markdown("**Comparación de KPIs Numéricos**")
            try:
                fig = create_kpi_bar_chart(numeric_kpis)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.info("💡 Error al generar gráfico de KPIs")
    
    st.markdown("---")
    
    # Free-form quantitative notes
    st.text_area(
        "Notas Adicionales (Cuantitativas)",
        key="quantitative_notes",
        placeholder="Otros datos numéricos, métricas o información cuantitativa relevante...",
        height=100,
        label_visibility="collapsed"
    )
    
    st.markdown("##")
    
    # QUALITATIVE DATA Section
    st.subheader("👥 Datos Cualitativos")
    
    # Stakeholders Section
    st.markdown("**Stakeholders y Opiniones**")
    
    if st.session_state.stakeholders:
        for stakeholder in st.session_state.stakeholders:
            c1, c2, c3 = st.columns([3, 4, 0.5])
            with c1:
                new_name = st.text_input(
                    "Stakeholder",
                    value=stakeholder["name"],
                    key=f"stakeholder_name_{stakeholder['id']}",
                    placeholder="Nombre/Rol",
                    label_visibility="collapsed"
                )
                stakeholder["name"] = new_name
            with c2:
                new_opinion = st.text_input(
                    "Opinión",
                    value=stakeholder["opinion"],
                    key=f"stakeholder_opinion_{stakeholder['id']}",
                    placeholder="Su opinión/posición",
                    label_visibility="collapsed"
                )
                stakeholder["opinion"] = new_opinion
            with c3:
                if st.button("🗑️", key=f"del_stakeholder_{stakeholder['id']}", help="Eliminar stakeholder"):
                    remove_stakeholder(stakeholder["id"])
                    st.rerun()
    
    if st.button("➕ Añadir Stakeholder", key="add_stakeholder_btn", use_container_width=True):
        add_stakeholder()
        st.rerun()
    
    st.markdown("---")
    
    # Free-form qualitative notes
    st.text_area(
        "Notas Adicionales (Cualitativas)",
        key="qualitative_notes",
        placeholder="Contexto, observaciones, feedback, análisis cualitativo u otra información relevante...",
        height=200,
        label_visibility="collapsed"
    )

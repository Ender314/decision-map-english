# -*- coding: utf-8 -*-
"""
Sidebar component - Simplified version.
Clean export/import functionality without over-engineering.
"""

import streamlit as st
import json
from datetime import datetime
from config.constants import APP_NAME, APP_ICON
from utils.data_manager import create_export_data, validate_json_structure, parse_date_string


def render_sidebar():
    """Render the complete sidebar."""
    with st.sidebar:
        # Navigation section (only show if we're in the app)
        if st.session_state.get("current_page") == "app":
            st.markdown("### 🏠 Navigation")
            if st.button("← Home", use_container_width=True, key="sidebar_nav_landing"):
                st.session_state["current_page"] = "landing"
                st.rerun()
            st.markdown("---")
        
        # Export section
        st.markdown("### 📤 Exportar Datos")
        st.markdown("Guarda tu análisis actual en formato JSON para poder restaurarlo más tarde.")
        
        # Check if we have data to export
        alt_names = [a["text"].strip() for a in st.session_state.get("alts", []) if a["text"].strip()]
        prioridad_names = [p["text"].strip() for p in st.session_state.get("priorities", []) if p["text"].strip()]
        
        if alt_names and prioridad_names:
            if st.button("📥 Exportar JSON", use_container_width=True):
                try:
                    export_data = create_export_data()
                    if export_data:
                        json_str = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
                        
                        st.download_button(
                            "⬇️ Descargar archivo JSON",
                            data=json_str,
                            file_name=f"lambda_pro_decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True
                        )
                        st.success("✅ Archivo JSON generado exitosamente")
                    else:
                        st.error("❌ Error al generar los datos de exportación")
                except Exception as e:
                    st.error(f"❌ Error durante la exportación: {str(e)}")
        else:
            st.info("💡 **Exportación disponible** una vez que hayas definido **Alternativas** y **Prioridades**")
        
        st.markdown("---")
        
        # Import section
        st.markdown("### 📥 Importar Datos")
        st.markdown("Restaura una sesión previa desde un archivo JSON exportado.")
        
        uploaded_file = st.file_uploader(
            "Selecciona archivo JSON",
            type=['json'],
            help="Solo archivos JSON exportados desde Lambda Pro",
            accept_multiple_files=False
        )
        
        if uploaded_file is not None:
            try:
                # Read and parse JSON
                json_data = json.loads(uploaded_file.read().decode('utf-8'))
                
                # Validate data structure
                is_valid, error_msg = validate_json_structure(json_data)
                
                if not is_valid:
                    st.error(f"❌ Archivo JSON inválido: {error_msg}")
                else:
                    if st.button("🔄 Importar Datos", use_container_width=True):
                        try:
                            # Store import data temporarily and trigger rerun
                            st.session_state["_import_data"] = json_data
                            st.session_state["_pending_import"] = True
                            st.success("✅ Datos importados exitosamente")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error durante la importación: {str(e)}")
                            
            except json.JSONDecodeError:
                st.error("❌ El archivo no contiene JSON válido")
            except Exception as e:
                st.error(f"❌ Error al leer el archivo: {str(e)}")
        
        st.markdown("---")
        
        # App information
        st.markdown("### ℹ️ Información")
        st.markdown(f"**{APP_NAME}** v1.5 (Simplified)")
        st.markdown("✅ Arquitectura modular simplificada")
        st.markdown("✅ Todas las funcionalidades principales")
        st.markdown("⚡ Optimizado para rendimiento")
        
        # Simple progress indicator
        components = [
            ("Dimensionado", bool(st.session_state.get("impacto_corto"))),
            ("Alternativas", len([a for a in st.session_state.get("alts", []) if a["text"].strip()]) >= 2),
            ("Objetivo", bool(st.session_state.get("objetivo", "").strip())),
            ("Prioridades", len([p for p in st.session_state.get("priorities", []) if p["text"].strip()]) >= 2),
            ("Información", len([k for k in st.session_state.get("kpis", []) if k.get("name", "").strip()]) > 0),
            ("Evaluación", st.session_state.get("mcda_scores_df") is not None),
            ("Escenarios", bool(st.session_state.get("scenarios", {}))),
        ]
        
        completed = sum(1 for _, status in components if status)
        total = len(components)
        
        st.progress(completed / total, text=f"Progreso: {completed}/{total}")
        
        with st.expander("Estado de Componentes"):
            for name, status in components:
                icon = "✅" if status else "⏳"
                st.markdown(f"{icon} {name}")

# -*- coding: utf-8 -*-
"""
Sidebar component for Lambda Pro.
Handles export/import functionality and app information.
"""

import streamlit as st
import json
from datetime import datetime

from config.constants import APP_NAME
from utils.data_manager import (
    create_export_data, import_json_data, validate_json_structure, 
    make_json_ready, create_filename_slug
)


def render_export_section():
    """Render the export section of the sidebar."""
    st.markdown("### 📤 Exportar Datos")
    st.markdown("Guarda tu sesión actual en un archivo JSON.")
    
    # Check if we have data to export
    alt_names = [a["text"].strip() for a in st.session_state.get("alts", []) if a["text"].strip()]
    prioridad_names = [p["text"].strip() for p in st.session_state.get("priorities", []) if p["text"].strip()]
    
    if alt_names and prioridad_names:
        # Create export data
        export_data = create_export_data()
        
        if export_data:
            # Create filename
            decision_text = st.session_state.get("decision", "")
            filename = f"{create_filename_slug(decision_text)}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            
            st.download_button(
                "⬇️ Descargar JSON",
                data=json.dumps(make_json_ready(export_data), ensure_ascii=False, indent=2),
                file_name=filename,
                mime="application/json",
                use_container_width=True,
            )
            
            with st.expander("Ver datos (JSON)"):
                st.json(export_data)
        else:
            st.info("💡 No hay datos suficientes para exportar")
    else:
        st.info("💡 **Exportación disponible** una vez que hayas definido **Alternativas** y **Prioridades**")


def render_import_section():
    """Render the import section of the sidebar."""
    st.markdown("### 📥 Importar Datos")
    st.markdown("Restaura una sesión previa desde un archivo JSON exportado.")
    
    # File uploader
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
            
            # Validate structure
            is_valid, message = validate_json_structure(json_data)
            
            if not is_valid:
                st.error(f"❌ **Error**: {message}")
                st.info("💡 Usa un archivo JSON exportado desde Lambda Pro")
            else:
                # Show preview information
                st.success("✅ **Archivo válido**")
                
                meta = json_data.get("meta", {})
                st.metric("Fecha", meta.get("exported_at", "N/A")[:10])
                st.metric("Alternativas", len(json_data.get("alternativas", [])))
                st.metric("Prioridades", len(json_data.get("prioridades", [])))
                
                # Warning and confirmation
                st.warning("⚠️ Importar eliminará los datos actuales")
                
                # Confirmation button
                if st.button("🔄 Confirmar Importación", type="primary", use_container_width=True):
                    try:
                        # Show loading animation
                        with st.spinner("⏳ Importando datos..."):
                            import time
                            time.sleep(0.5)  # Brief pause for visual feedback
                            import_json_data(json_data)
                        
                        # Success feedback
                        st.success("✅ **¡Datos importados correctamente!**")
                        st.balloons()  # Visual celebration
                        
                        # Add session state flag to redirect to first tab
                        st.session_state["redirect_to_first_tab"] = True
                        
                        st.info("🔄 Redirigiendo al primer paso...")
                        time.sleep(1)  # Brief pause before redirect
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ **Error durante la importación**: {str(e)}")
                        st.info("💡 Verifica que el archivo JSON sea válido")
                        
        except json.JSONDecodeError as e:
            st.error(f"❌ **Error de formato JSON**: {str(e)}")
            st.info("💡 El archivo no contiene JSON válido")
        except Exception as e:
            st.error(f"❌ **Error inesperado**: {str(e)}")


def render_sidebar():
    """Render the complete sidebar."""
    with st.sidebar:
        render_export_section()
        st.markdown("---")
        render_import_section()
        st.markdown("---")
        
        # App information
        st.markdown("### ℹ️ Información")
        st.markdown(f"**{APP_NAME}** v0.2.0")
        st.markdown("✅ Arquitectura modular completa")
        st.markdown("✅ Todas las funcionalidades restauradas")
        st.markdown("🎯 Listo para Phase 2")
        
        # Progress indicator
        completed_components = [
            "Dimensionado", "Alternativas", "Objetivo", "Prioridades", 
            "Información", "Evaluación", "Escenarios", "Resultados"
        ]
        
        st.progress(1.0, text="Progreso: 100% ✅")
        
        # Component status
        with st.expander("Estado de Componentes"):
            for component in completed_components:
                st.markdown(f"✅ {component}")
            
            st.markdown("---")
            st.markdown("**Próximas mejoras (Phase 2):**")
            st.markdown("🔄 Componentes CRUD genéricos")
            st.markdown("⚡ Optimizaciones de rendimiento")
            st.markdown("🎨 Mejoras de UX")

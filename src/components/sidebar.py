# -*- coding: utf-8 -*-
"""
Sidebar component - Simplified version.
Clean export/import functionality without over-engineering.
"""

import streamlit as st
import json
from datetime import datetime
from config.constants import APP_NAME, APP_ICON, APP_VERSION, APP_FILENAME_PREFIX
from utils.data_manager import create_export_data, validate_json_structure, parse_date_string, create_excel_export, import_excel_data
from components.templates import render_template_button_in_sidebar


def _export_filename(ext: str) -> str:
    """Build an export filename with date and truncated decision description."""
    import re
    date_str = datetime.now().strftime('%Y%m%d')
    base = f"{APP_FILENAME_PREFIX}_decision_{date_str}"
    
    decision = st.session_state.get("decision", "").strip()
    if decision:
        # Remove characters that are invalid in filenames
        safe = re.sub(r'[<>:"/\\|?*]', '', decision)
        # Truncate to ~60 chars on a word boundary
        max_len = 60
        if len(safe) > max_len:
            safe = safe[:max_len].rsplit(' ', 1)[0] + '…'
        base = f"{base} - {safe}"
    
    return f"{base}.{ext}"


def render_sidebar():
    """Render the complete sidebar."""
    with st.sidebar:
        # Export section
        st.markdown("### 📤 Exportar Datos")
        st.markdown("Guarda tu análisis actual en formato JSON o Excel.")
        
        # Check if we have data to export
        alt_names = [a["text"].strip() for a in st.session_state.get("alts", []) if a["text"].strip()]
        prioridad_names = [p["text"].strip() for p in st.session_state.get("priorities", []) if p["text"].strip()]
        
        if alt_names and prioridad_names:
            col1, col2 = st.columns(2)
            
            # JSON Export
            with col1:
                if st.button("📥 JSON", use_container_width=True, help="Exportar como JSON"):
                    try:
                        export_data = create_export_data()
                        if export_data:
                            json_str = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
                            
                            st.download_button(
                                "⬇️ Descargar JSON",
                                data=json_str,
                                file_name=_export_filename('json'),
                                mime="application/json",
                                use_container_width=True
                            )
                            st.success("✅ JSON generado")
                        else:
                            st.error("❌ Error al generar JSON")
                    except Exception as e:
                        st.error(f"❌ Error JSON: {str(e)}")
            
            # Excel Export
            with col2:
                if st.button("📈 Excel", use_container_width=True, help="Exportar como Excel"):
                    try:
                        excel_data = create_excel_export()
                        if excel_data:
                            st.download_button(
                                "⬇️ Descargar Excel",
                                data=excel_data,
                                file_name=_export_filename('xlsx'),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True
                            )
                            st.success("✅ Excel generado")
                        else:
                            st.error("❌ Error al generar Excel")
                    except Exception as e:
                        st.error(f"❌ Error Excel: {str(e)}")
        else:
            st.info("💡 **Exportación disponible** una vez que hayas definido **Alternativas** y **Prioridades**")
        
        st.markdown("---")
        
        # Import section
        st.markdown("### 📥 Importar Datos")
        st.markdown("Restaura una sesión previa desde JSON o Excel.")
        
        # File uploader for both formats
        uploaded_file = st.file_uploader(
            "Selecciona archivo",
            type=['json', 'xlsx', 'xls'],
            help=f"Archivos JSON o Excel exportados desde {APP_NAME}",
            accept_multiple_files=False
        )
        
        if uploaded_file is not None:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'json':
                # JSON Import
                try:
                    # Read and parse JSON
                    json_data = json.loads(uploaded_file.read().decode('utf-8'))
                    
                    # Validate data structure
                    is_valid, error_msg = validate_json_structure(json_data)
                    
                    if not is_valid:
                        st.error(f"❌ JSON inválido: {error_msg}")
                    else:
                        if st.button("🔄 Importar JSON", use_container_width=True):
                            try:
                                # Store import data temporarily and trigger rerun
                                st.session_state["_import_data"] = json_data
                                st.session_state["_pending_import"] = True
                                st.success("✅ JSON importado")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Error importando JSON: {str(e)}")
                                
                except json.JSONDecodeError:
                    st.error("❌ El archivo no contiene JSON válido")
                except Exception as e:
                    st.error(f"❌ Error leyendo JSON: {str(e)}")
            
            elif file_extension in ['xlsx', 'xls']:
                # Excel Import
                if st.button("🔄 Importar Excel", use_container_width=True):
                    try:
                        success, message = import_excel_data(uploaded_file)
                        if success:
                            st.success(f"✅ {message}")
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                    except Exception as e:
                        st.error(f"❌ Error importando Excel: {str(e)}")
            
            else:
                st.error("❌ Formato de archivo no soportado")
        
        st.markdown("---")
        
        # Templates section
        st.markdown("### 📋 Plantillas")
        render_template_button_in_sidebar()
        
        st.markdown("---")
        
        # App information
        st.markdown("### ℹ️ Información")
        st.markdown(f"**{APP_ICON} {APP_NAME}** v{APP_VERSION}")
        st.markdown("Tu asistente para decisiones estratégicas")
        
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

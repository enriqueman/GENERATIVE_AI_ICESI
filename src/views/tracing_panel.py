"""
Panel de trazabilidad para el administrador
Muestra todos los logs y actividades del sistema RAG
"""

import streamlit as st
from utils.tracing import tracer, get_statistics, get_trace_logs
from datetime import datetime
import pandas as pd

def display_tracing_panel():
    """Mostrar el panel de trazabilidad"""
    st.header("[DATA] Panel de Trazabilidad")
    st.markdown("Monitoreo en tiempo real de las operaciones del sistema RAG")
    
    # Obtener estadísticas
    stats = get_statistics()
    
    if not stats or stats.get("total_logs", 0) == 0:
        st.info("[NOTE] No hay logs registrados aún. El sistema comenzará a registrar actividad cuando se realicen consultas.")
        return
    
    # Mostrar estadísticas generales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Logs", stats.get("total_logs", 0))
    
    with col2:
        st.metric("Tasa de Éxito", f"{stats.get('success_rate', 0)}%")
    
    with col3:
        st.metric("Errores", stats.get("error_count", 0))
    
    with col4:
        operations = stats.get("operations", {})
        total_ops = sum(operations.values())
        st.metric("Operaciones", total_ops)
    
    # Métricas de traces
    unique_traces = stats.get("unique_traces", 0)
    if unique_traces > 0:
        st.info(f"[RELOAD] {unique_traces} interacciones únicas trazadas")
    
    st.divider()
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        filter_operation = st.selectbox(
            "Filtrar por Operación",
            options=["Todas"] + list(stats.get("operations", {}).keys())
        )
    
    with col2:
        filter_level = st.selectbox(
            "Filtrar por Nivel",
            options=["Todos", "INFO", "SUCCESS", "ERROR"]
        )
    
    # Obtener logs
    all_logs = tracer.get_recent_logs(limit=500)
    
    # Aplicar filtros
    filtered_logs = all_logs
    
    if filter_operation != "Todas":
        filtered_logs = [log for log in filtered_logs if log.get("operation") == filter_operation]
    
    if filter_level != "Todos":
        filtered_logs = [log for log in filtered_logs if log.get("level") == filter_level]
    
    # Mostrar conteo
    st.markdown(f"**Mostrando {len(filtered_logs)} de {stats.get('total_logs', 0)} logs**")
    
    st.divider()
    
    # Mostrar logs en tabla
    if filtered_logs:
        # Preparar datos para tabla
        table_data = []
        for log in filtered_logs:
            timestamp = log.get("timestamp", "")
            # Formatear timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = timestamp
            
            table_data.append({
                "[TIME] Hora": formatted_time,
                "[CONFIG] Operación": log.get("operation", "Unknown"),
                "[NOTE] Mensaje": log.get("message", ""),
                "[DATA] Nivel": log.get("level", "INFO"),
            })
        
        df = pd.DataFrame(table_data)
        
        # Mostrar tabla con color según nivel
        def color_level(val):
            if val == "ERROR":
                return "background-color: #ffe0e0"
            elif val == "SUCCESS":
                return "background-color: #e0ffe0"
            elif val == "INFO":
                return "background-color: #e0f0ff"
            return ""
        
        styled_df = df.style.apply(lambda x: x.map(color_level), subset=["[DATA] Nivel"])
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
    else:
        st.info("No hay logs que coincidan con los filtros seleccionados")
    
    st.divider()
    
    # Mostrar últimos logs en detalle
    st.subheader("[LIST] Detalles de los Últimos 10 Logs")
    
    for log in filtered_logs[:10]:
        with st.expander(f"[{log.get('level')}] {log.get('operation')}: {log.get('message', '')[:80]}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Timestamp:**")
                st.code(log.get("timestamp", ""))
                
                st.markdown("**Nivel:**")
                st.code(log.get("level", ""))
            
            with col2:
                st.markdown("**Operación:**")
                st.code(log.get("operation", ""))
                
                st.markdown("**Mensaje Completo:**")
                st.code(log.get("message", ""))
            
            # Mostrar metadata
            metadata = log.get("metadata", {})
            if metadata:
                st.markdown("**Metadata:**")
                st.json(metadata)
    
    st.divider()
    
    # Botón para limpiar logs
    if st.button("🗑️ Limpiar todos los logs", type="secondary"):
        tracer.clear_logs()
        st.success("[OK] Logs limpiados")
        st.rerun()
    
    # Mostrar distribución por operación
    st.subheader("📈 Distribución de Operaciones")
    operations = stats.get("operations", {})
    
    if operations:
        operation_df = pd.DataFrame([
            {"Operación": k, "Cantidad": v}
            for k, v in operations.items()
        ])
        
        st.bar_chart(operation_df.set_index("Operación"))
    
    st.divider()
    
    # Estadísticas por nivel
    st.subheader("🔢 Estadísticas por Nivel")
    
    level_counts = {}
    for log in all_logs:
        level = log.get("level", "UNKNOWN")
        level_counts[level] = level_counts.get(level, 0) + 1
    
    if level_counts:
        level_df = pd.DataFrame([
            {"Nivel": k, "Cantidad": v}
            for k, v in level_counts.items()
        ])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.bar_chart(level_df.set_index("Nivel"))
        
        with col2:
            st.dataframe(level_df, hide_index=True, use_container_width=True)
    
    # Mostrar Traces Agrupados
    st.divider()
    st.subheader("[RELOAD] Traces de Interacciones (Agrupados)")
    
    # Extraer todos los trace_ids únicos
    all_logs_with_trace = [log for log in all_logs if log.get("trace_id")]
    unique_trace_ids = list(set([log.get("trace_id") for log in all_logs_with_trace]))
    
    if unique_trace_ids:
        # Seleccionar un trace para ver
        selected_trace = st.selectbox(
            "Selecciona un trace para ver detalles",
            options=unique_trace_ids
        )
        
        if selected_trace:
            trace_logs = get_trace_logs(selected_trace)
            
            st.markdown(f"**📌 Trace ID:** `{selected_trace}`")
            st.markdown(f"**[DATA] Total de operaciones:** {len(trace_logs)}")
            
            # Mostrar timeline del trace
            st.markdown("**⏱️ Timeline de operaciones:**")
            
            for i, log in enumerate(trace_logs, 1):
                level = log.get("level", "INFO")
                operation = log.get("operation", "UNKNOWN")
                message = log.get("message", "")
                metadata = log.get("metadata", {})
                
                # Color según nivel
                if level == "ERROR":
                    st.error(f"**{i}. {operation}** [ERROR] - {message}")
                elif level == "SUCCESS":
                    st.success(f"**{i}. {operation}** [OK] - {message}")
                else:
                    st.info(f"**{i}. {operation}** [INFO] - {message}")
                
                # Mostrar metadata si existe
                if metadata:
                    with st.expander("[DATA] Ver metadata"):
                        st.json(metadata)
                
                st.markdown("---")
    else:
        st.info("No hay traces disponibles para mostrar")


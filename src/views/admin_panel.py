import streamlit as st
import os
from controllers.auth import verify_session, logout_session
from models.db import create_source, list_sources, delete_source, connect_db, init_database
from utils.vector_functions import (
    load_document,
    create_collection,
    load_collection,
    add_documents_to_collection,
)
from utils.theme_utils import apply_theme_with_header

def check_admin_auth():
    """Check if user is authenticated as admin"""
    if "session_token" not in st.session_state:
        return False
    
    user_info = verify_session(st.session_state.session_token)
    if user_info:
        st.session_state.user_info = user_info
        return True
    else:
        del st.session_state.session_token
        return False

def admin_panel():
    """Main admin panel for managing RAG knowledge base"""
    
    # Inicializar la base de datos
    init_database()
    
    # Aplicar tema con header
    apply_theme_with_header()
    
    if not check_admin_auth():
        st.error("No autorizado. Por favor, inicia sesión.")
        if st.button("Ir a Login"):
            st.switch_page("views/admin_login.py")
        return
    
    st.markdown("### [CONFIG] Panel de Administración")
    st.write(f"Bienvenido, **{st.session_state.user_info['username']}**")
    
    # Logout button
    col1, col2 = st.columns([0.9, 0.1])
    with col2:
        if st.button("🚪 Salir"):
            logout_session(st.session_state.session_token)
            del st.session_state.session_token
            del st.session_state.user_info
            st.rerun()
    
    # Tabs for different management sections
    tab1, tab2, tab3, tab4 = st.tabs(["[BOOKS] Documentos", "[DATA] Estadísticas", "[SETTINGS] Configuración", "[DEBUG] Trazabilidad"])
    
    with tab1:
        manage_documents()
    
    with tab4:
        from views.tracing_panel import display_tracing_panel
        display_tracing_panel()
    
    with tab2:
        show_statistics()
    
    with tab3:
        show_settings()

def manage_documents():
    """Document management interface"""
    
    st.subheader("Gestión de Base de Conocimiento")
    
    # Get system chat (chat_id = 1 reserved for system documents)
    collection_name = "ecomarket_kb"
    
    # Upload new document
    st.markdown("### 📤 Subir Nuevo Documento")
    
    with st.form("upload_form"):
        uploaded_file = st.file_uploader(
            "Selecciona un documento",
            type=["txt", "pdf", "docx", "csv", "html", "md"],
            help="Formatos soportados: TXT, PDF, DOCX, CSV, HTML, MD"
        )
        
        doc_description = st.text_area(
            "Descripción del documento",
            placeholder="Ej: Política de devoluciones actualizada 2024"
        )
        
        submit_button = st.form_submit_button("Subir Documento", type="primary")
        
        if submit_button and uploaded_file:
            with st.spinner("Procesando documento..."):
                try:
                    # Save temp file
                    temp_dir = "temp_files"
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                    
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Load document
                    document = load_document(temp_file_path)
                    
                    # Detect file type for SQLite registration
                    _, file_ext = os.path.splitext(uploaded_file.name)
                    source_type = "excel" if file_ext in [".xlsx", ".xls"] else "document"
                    
                    # Create or update collection
                    if not os.path.exists(f"./static/persist/{collection_name}"):
                        vectordb = create_collection(collection_name, document)
                    else:
                        vectordb = load_collection(collection_name)
                        vectordb = add_documents_to_collection(vectordb, document)
                    
                    # Save to database with proper type
                    create_source(
                        uploaded_file.name, 
                        doc_description, 
                        1,  # System chat
                        source_type=source_type
                    )
                    
                    # Remove temp file
                    os.remove(temp_file_path)
                    
                    st.success(f"[OK] Documento '{uploaded_file.name}' subido exitosamente!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"[ERROR] Error al procesar el documento: {str(e)}")
    
    # List existing documents
    st.markdown("### [LIST] Documentos en el Sistema")
    
    # Get both regular documents and sample documents
    regular_documents = list_sources(1, source_type="document")
    sample_documents = list_sources(1, source_type="sample_document")
    
    total_docs = len(regular_documents) + len(sample_documents)
    
    if total_docs > 0:
        st.write(f"Total de documentos: **{total_docs}**")
        
        # Show sample documents first
        if sample_documents:
            st.markdown("#### [ECOMARKET] Documentos de Muestra (Pre-cargados)")
            for doc in sample_documents:
                doc_id = doc[0]
                doc_name = doc[1]
                doc_description = doc[2]
                
                with st.expander(f"[DOC] {doc_name} (Muestra)", expanded=False):
                    st.write(f"**Descripción:** {doc_description if doc_description else 'Sin descripción'}")
                    st.info("[INFO] Este es un documento de muestra pre-cargado en el sistema")
                    
                    col1, col2 = st.columns([0.8, 0.2])
                    with col2:
                        if st.button("🗑️ Eliminar", key=f"delete_sample_{doc_id}"):
                            delete_source(doc_id)
                            st.success(f"Documento de muestra eliminado: {doc_name}")
                            st.rerun()
        
        # Show regular documents
        if regular_documents:
            st.markdown("#### [BOOKS] Documentos Subidos por Administrador")
            for doc in regular_documents:
                doc_id = doc[0]
                doc_name = doc[1]
                doc_description = doc[2]
                
                with st.expander(f"[DOC] {doc_name}"):
                    st.write(f"**Descripción:** {doc_description if doc_description else 'Sin descripción'}")
                    
                    col1, col2 = st.columns([0.8, 0.2])
                    with col2:
                        if st.button("🗑️ Eliminar", key=f"delete_{doc_id}"):
                            delete_source(doc_id)
                            st.success(f"Documento eliminado: {doc_name}")
                            st.rerun()
    else:
        st.info("No hay documentos en el sistema. Los documentos de muestra se cargarán automáticamente al iniciar la aplicación.")

def show_statistics():
    """Show system statistics"""
    st.subheader("[DATA] Estadísticas del Sistema")
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # Count documents (both regular and sample)
    cursor.execute("SELECT COUNT(*) FROM sources WHERE chat_id = 1 AND (type = 'document' OR type = 'sample_document')")
    doc_count = cursor.fetchone()[0]
    
    # Count sample documents separately
    cursor.execute("SELECT COUNT(*) FROM sources WHERE chat_id = 1 AND type = 'sample_document'")
    sample_doc_count = cursor.fetchone()[0]
    
    # Count customer queries (from public chat, chat_id = 2)
    cursor.execute("SELECT COUNT(*) FROM messages WHERE chat_id = 2 AND sender = 'user'")
    query_count = cursor.fetchone()[0]
    
    # Count AI responses
    cursor.execute("SELECT COUNT(*) FROM messages WHERE chat_id = 2 AND sender = 'ai'")
    response_count = cursor.fetchone()[0]
    
    conn.close()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("[BOOKS] Total Documentos", doc_count)
    
    with col2:
        st.metric("[ECOMARKET] Documentos Muestra", sample_doc_count)
    
    with col3:
        st.metric("❓ Consultas Recibidas", query_count)
    
    with col4:
        st.metric("[CHAT] Respuestas Generadas", response_count)
    
    st.markdown("---")
    
    # Recent queries
    st.markdown("### [DEBUG] Consultas Recientes")
    
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT content, timestamp 
        FROM messages 
        WHERE chat_id = 2 AND sender = 'user' 
        ORDER BY timestamp DESC 
        LIMIT 10
    """)
    recent_queries = cursor.fetchall()
    conn.close()
    
    if recent_queries:
        for query, timestamp in recent_queries:
            st.text(f"[{timestamp}] {query[:100]}...")
    else:
        st.info("No hay consultas registradas aún.")

def show_settings():
    """Show system settings"""
    st.subheader("[SETTINGS] Configuración del Sistema")
    
    st.markdown("### [TARGET] Parámetros del RAG")
    
    # Score threshold setting
    score_threshold = st.slider(
        "Umbral de similitud",
        min_value=0.0,
        max_value=1.0,
        value=0.6,
        step=0.05,
        help="Valor mínimo de similitud para considerar un documento relevante"
    )
    
    st.info(f"Umbral actual: {score_threshold}")
    
    # Chunk size setting
    chunk_size = st.number_input(
        "Tamaño de fragmentos",
        min_value=100,
        max_value=2000,
        value=1000,
        step=100,
        help="Tamaño de los fragmentos de texto para procesamiento"
    )
    
    st.markdown("### [RELOAD] Mantenimiento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Limpiar sesiones expiradas"):
            from controllers.auth import cleanup_expired_sessions
            cleanup_expired_sessions()
            st.success("Sesiones expiradas eliminadas")
    
    with col2:
        if st.button("[DATA] Exportar estadísticas"):
            st.info("Función de exportación en desarrollo")

if __name__ == "__main__":
    admin_panel()
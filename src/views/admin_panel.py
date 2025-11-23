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
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "[BOOKS] Documentos", 
        "[🎓] Programas Posgrado", 
        "[DATA] Estadísticas", 
        "[SETTINGS] Configuración", 
        "[DEBUG] Trazabilidad"
    ])
    
    with tab1:
        manage_documents()
    
    with tab2:
        manage_posgrado_programs()
    
    with tab5:
        from views.tracing_panel import display_tracing_panel
        display_tracing_panel()
    
    with tab3:
        show_statistics()
    
    with tab4:
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

def manage_posgrado_programs():
    """Gestión de programas de posgrado"""
    
    st.subheader("🎓 Gestión de Programas de Posgrado")
    
    # Opciones: Ver programas, Añadir manualmente, Cargar archivo
    option = st.radio(
        "Selecciona una opción:",
        ["📋 Ver Programas", "➕ Añadir Manualmente", "📤 Cargar Archivo"],
        horizontal=True
    )
    
    if option == "📋 Ver Programas":
        list_posgrado_programs()
    elif option == "➕ Añadir Manualmente":
        add_program_manually()
    elif option == "📤 Cargar Archivo":
        upload_program_file()

def list_posgrado_programs():
    """Listar todos los programas de posgrado"""
    from models.db import list_posgrado_programs
    
    st.markdown("### 📋 Programas Cargados en el Sistema")
    
    programs = list_posgrado_programs(active_only=False)
    
    if programs:
        st.write(f"**Total de programas:** {len(programs)}")
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            program_type_filter = st.selectbox(
                "Filtrar por tipo:",
                ["Todos", "maestria", "especializacion", "mba", "doctorado"]
            )
        with col2:
            active_filter = st.selectbox(
                "Estado:",
                ["Todos", "Activos", "Inactivos"]
            )
        
        # Aplicar filtros
        filtered_programs = programs
        if program_type_filter != "Todos":
            filtered_programs = [p for p in filtered_programs if p.get("program_type", "").lower() == program_type_filter.lower()]
        if active_filter == "Activos":
            filtered_programs = [p for p in filtered_programs if p.get("active", 0) == 1]
        elif active_filter == "Inactivos":
            filtered_programs = [p for p in filtered_programs if p.get("active", 0) == 0]
        
        st.write(f"**Programas mostrados:** {len(filtered_programs)}")
        st.markdown("---")
        
        # Mostrar programas
        for program in filtered_programs:
            program_id = program.get("id")
            program_name = program.get("program_name", "Sin nombre")
            program_type = program.get("program_type", "N/A")
            description = program.get("description", "Sin descripción")
            source_file = program.get("source_file", "Manual")
            active = program.get("active", 0) == 1
            loaded_to_rag = program.get("loaded_to_rag", 0) == 1
            areas = program.get("areas_tematicas", "")
            modalidad = program.get("modalidad", "N/A")
            duracion = program.get("duracion", "N/A")
            
            # Estado visual
            status_color = "🟢" if active else "🔴"
            rag_status = "✅" if loaded_to_rag else "❌"
            
            with st.expander(f"{status_color} **{program_name}** ({program_type.upper()})", expanded=False):
                col1, col2 = st.columns([0.7, 0.3])
                
                with col1:
                    st.write(f"**Descripción:** {description[:200]}{'...' if len(description) > 200 else ''}")
                    if areas:
                        st.write(f"**Áreas temáticas:** {areas}")
                    st.write(f"**Modalidad:** {modalidad} | **Duración:** {duracion}")
                    st.write(f"**Fuente:** {source_file}")
                    st.write(f"**Cargado en RAG:** {rag_status}")
                
                with col2:
                    if st.button("✏️ Editar", key=f"edit_{program_id}"):
                        st.session_state[f"editing_program_{program_id}"] = True
                        st.rerun()
                    
                    if st.button("🗑️ Eliminar", key=f"delete_{program_id}"):
                        from models.db import delete_posgrado_program
                        try:
                            delete_posgrado_program(program_id)
                            st.success(f"Programa '{program_name}' eliminado")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error eliminando programa: {e}")
                    
                    # Toggle activo/inactivo
                    toggle_text = "Desactivar" if active else "Activar"
                    if st.button(toggle_text, key=f"toggle_{program_id}"):
                        from models.db import update_posgrado_program
                        try:
                            update_posgrado_program(program_id, active=not active)
                            st.success(f"Programa {'activado' if not active else 'desactivado'}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error actualizando programa: {e}")
    else:
        st.info("No hay programas cargados en el sistema. Puedes añadirlos manualmente o cargar un archivo.")

def add_program_manually():
    """Formulario para añadir programa manualmente"""
    from models.db import create_posgrado_program
    from agents.program_loader_agent import ProgramLoaderAgent
    
    st.markdown("### ➕ Añadir Programa de Posgrado Manualmente")
    
    with st.form("add_program_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            program_name = st.text_input("Nombre del Programa *", placeholder="Ej: Maestría en Ciencia de Datos")
            program_type = st.selectbox(
                "Tipo de Programa *",
                ["maestria", "especializacion", "mba", "doctorado"]
            )
            modalidad = st.selectbox(
                "Modalidad",
                ["presencial", "virtual", "hibrida", "flexible"]
            )
            duracion = st.text_input("Duración", placeholder="Ej: 2 años, 4 semestres")
        
        with col2:
            areas_tematicas = st.text_area(
                "Áreas Temáticas (separadas por comas)",
                placeholder="Ej: Ciencia de Datos, Machine Learning, Big Data"
            )
            requisitos = st.text_area(
                "Requisitos",
                placeholder="Ej: Título profesional, experiencia mínima 2 años"
            )
            inversion = st.text_input("Inversión", placeholder="Ej: $15.000.000")
        
        description = st.text_area(
            "Descripción del Programa *",
            placeholder="Descripción detallada del programa, objetivos, perfil del egresado, etc.",
            height=150
        )
        
        source_type = st.selectbox(
            "Tipo de Fuente",
            ["manual", "document"]
        )
        
        active = st.checkbox("Programa Activo", value=True)
        
        submitted = st.form_submit_button("💾 Guardar Programa", type="primary")
        
        if submitted:
            if not program_name or not description:
                st.error("Por favor completa los campos obligatorios (*)")
            else:
                with st.spinner("Guardando programa..."):
                    try:
                        # Convertir áreas temáticas a lista
                        areas_list = [a.strip() for a in areas_tematicas.split(",") if a.strip()] if areas_tematicas else []
                        
                        program_id = create_posgrado_program(
                            program_name=program_name,
                            program_type=program_type,
                            description=description,
                            areas_tematicas=areas_list,
                            requisitos=requisitos if requisitos else None,
                            modalidad=modalidad if modalidad else None,
                            duracion=duracion if duracion else None,
                            inversion=inversion if inversion else None,
                            source_file="manual_entry",
                            source_type=source_type,
                            active=active
                        )
                        
                        # Cargar al RAG
                        try:
                            # Crear documento temporal para cargar al RAG
                            from langchain_core.documents import Document
                            
                            program_doc = Document(
                                page_content=description,
                                metadata={
                                    "program_name": program_name,
                                    "program_type": program_type,
                                    "source_type": "posgrado_program",
                                    "program_tag": "programa_posgrado",
                                    "source": "manual_entry",
                                    "areas_tematicas": ", ".join(areas_list) if areas_list else "",
                                    "modalidad": modalidad,
                                    "duracion": duracion
                                }
                            )
                            
                            # Cargar al RAG
                            from utils.vector_functions import load_collection, add_documents_to_collection, create_collection
                            collection_name = "posgrado_programs"
                            
                            try:
                                vectordb = load_collection(collection_name)
                                vectordb = add_documents_to_collection(vectordb, [program_doc])
                            except:
                                vectordb = create_collection(collection_name, [program_doc])
                            
                            # Actualizar flag en BD
                            from models.db import update_posgrado_program
                            update_posgrado_program(program_id, loaded_to_rag=True)
                            
                            st.success(f"✅ Programa '{program_name}' guardado y cargado al RAG exitosamente!")
                        except Exception as rag_error:
                            st.warning(f"⚠️ Programa guardado en BD pero error al cargar al RAG: {rag_error}")
                            st.success(f"✅ Programa '{program_name}' guardado en base de datos")
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ Error guardando programa: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())

def upload_program_file():
    """Cargar archivo de programa y procesarlo con ProgramLoaderAgent"""
    from agents.program_loader_agent import ProgramLoaderAgent
    import os
    
    st.markdown("### 📤 Cargar Archivo de Programa de Posgrado")
    st.info("💡 El sistema procesará automáticamente el archivo y extraerá la información del programa usando IA.")
    
    uploaded_file = st.file_uploader(
        "Selecciona un archivo de programa",
        type=["pdf", "txt", "docx"],
        help="Formatos soportados: PDF, TXT, DOCX"
    )
    
    if uploaded_file:
        st.write(f"**Archivo seleccionado:** {uploaded_file.name}")
        st.write(f"**Tamaño:** {uploaded_file.size / 1024:.2f} KB")
        
        if st.button("🚀 Procesar y Cargar Programa", type="primary"):
            with st.spinner("Procesando archivo con IA..."):
                try:
                    # Guardar archivo temporal
                    temp_dir = "static/temp_files"
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                    
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Procesar con ProgramLoaderAgent
                    loader = ProgramLoaderAgent()
                    
                    # Obtener ruta completa
                    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    full_path = os.path.join(base_dir, temp_file_path)
                    
                    # Crear documentos del programa
                    program_docs = loader.create_program_documents(full_path)
                    
                    if program_docs:
                        st.success(f"✅ Programa procesado exitosamente!")
                        st.write(f"**Documentos creados:** {len(program_docs)}")
                        
                        # Mostrar información extraída
                        if program_docs:
                            doc = program_docs[0]
                            metadata = doc.metadata
                            
                            st.markdown("#### 📋 Información Extraída:")
                            st.json({
                                "Nombre": metadata.get("program_name", "N/A"),
                                "Tipo": metadata.get("program_type", "N/A"),
                                "Fuente": metadata.get("source", "N/A"),
                                "Áreas": metadata.get("areas_tematicas", "N/A")
                            })
                        
                        # Limpiar archivo temporal
                        try:
                            os.remove(temp_file_path)
                        except:
                            pass
                        
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ No se pudo procesar el archivo. Verifica que contenga información de un programa de posgrado.")
                        try:
                            os.remove(temp_file_path)
                        except:
                            pass
                        
                except Exception as e:
                    st.error(f"❌ Error procesando archivo: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())
                    
                    # Limpiar archivo temporal
                    try:
                        if 'temp_file_path' in locals():
                            os.remove(temp_file_path)
                    except:
                        pass

if __name__ == "__main__":
    admin_panel()
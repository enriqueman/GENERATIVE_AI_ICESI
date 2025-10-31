import streamlit as st
import time
import os
import sys

# Agregar src al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.db import create_message, get_messages, verify_chat_session
from agents.intelligent_agent import get_intelligent_agent
from utils.theme_utils import apply_theme_with_header
from tools.otp_auth import check_authentication_status

def stream_response(response):
    """Stream response word by word"""
    for word in response.split():
        yield word + " "
        time.sleep(0.05)

def public_chat():
    """Public chat interface for customers"""
    
    # Subtítulo (el header principal se maneja en theme_utils)
    st.markdown("<p class='subtitle'>Tu compañero para productos sostenibles</p>", unsafe_allow_html=True)
    
    # Initialize session state for authentication
    if 'chat_authenticated' not in st.session_state:
        st.session_state.chat_authenticated = False
        st.session_state.chat_session_token = None
        st.session_state.chat_user_email = None
        st.session_state.chat_user_name = None
        st.session_state.auth_welcome_shown = False
    
    # Check authentication status
    if st.session_state.chat_session_token:
        # Verify existing session
        session_data = verify_chat_session(st.session_state.chat_session_token)
        if session_data and session_data.get("authenticated"):
            st.session_state.chat_authenticated = True
            st.session_state.chat_user_email = session_data.get("email")
            st.session_state.chat_user_name = session_data.get("name")
        else:
            # Session expired or invalid
            st.session_state.chat_authenticated = False
            st.session_state.chat_session_token = None
    
    # Chat history (using chat_id = 2 for public chat)
    CHAT_ID = 2
    messages = get_messages(CHAT_ID)
    
    # Show welcome and authentication request if not authenticated
    if not st.session_state.chat_authenticated:
        # Show welcome message on first visit
        if not messages and not st.session_state.auth_welcome_shown:
            with st.container():
                st.markdown("""
                    <div class='welcome-box'>
                        <h3>👋 ¡Bienvenido a EcoMarket!</h3>
                        <p>Estoy aquí para ayudarte con:</p>
                        <ul>
                            <li>📦 Estado de pedidos y envíos</li>
                            <li>🔄 Políticas de devolución y cambio</li>
                            <li>🌱 Información sobre productos sostenibles</li>
                            <li>💳 Métodos de pago y facturación</li>
                            <li>❓ Preguntas frecuentes</li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)
                st.session_state.auth_welcome_shown = True
        
        # Show authentication prompt from agent if no messages
        if not messages:
            # Initial greeting asking for authentication
            initial_greeting = """¡Hola! Un gusto saludarte 👋

Para continuar y poder ayudarte mejor, necesitamos que te autentiques. 

Por favor, proporciona:
1. Tu correo electrónico
2. Tu nombre

Una vez que me proporciones esta información, te enviaré un código de verificación a tu correo para completar el proceso de autenticación."""
            
            with st.chat_message("assistant", avatar="🌿"):
                st.markdown(initial_greeting)
        else:
            # Display existing chat history
            for sender, content in messages:
                if sender == "user":
                    with st.chat_message("user"):
                        st.markdown(content)
                elif sender == "ai":
                    with st.chat_message("assistant", avatar="🌿"):
                        st.markdown(content)
        
        # Chat input for unauthenticated users
        prompt = st.chat_input("Escribe tu correo y nombre para autenticarte...")
        
        if prompt:
            # Save user message
            create_message(CHAT_ID, "user", prompt)
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            try:
                # Use intelligent agent to process authentication request
                agent = get_intelligent_agent()
                
                # Process query (agent will handle OTP_SEND or OTP_VERIFY based on query content)
                response = agent.process_query(prompt, enable_logging=False)
                
            except Exception as e:
                response = """
                😔 Lo siento, tuve un problema al procesar tu consulta.
                
                Por favor, intenta nuevamente o contacta a nuestro equipo:
                - 📧 soporte@ecomarket.com
                - 📞 +57 324 456 4450
                """
            
            # Save AI response
            create_message(CHAT_ID, "ai", response)
            
            # Display AI response with streaming
            with st.chat_message("assistant", avatar="🌿"):
                st.write_stream(stream_response(response))
            
            # Check if response indicates successful authentication
            if "✅" in response and ("autenticación exitosa" in response.lower() or "ya puedes usar" in response.lower()):
                # Get email from session memory (not from prompt, as prompt might only have OTP code)
                from tools.chat_memory import retrieve_chat_memory
                session_id = "default_session"
                email_memory = retrieve_chat_memory(session_id, "email")
                
                # Try to get email from memory first, then from prompt as fallback
                email = None
                if email_memory.get("found") and email_memory.get("memory_value"):
                    email = email_memory.get("memory_value")
                else:
                    # Fallback: try to extract from prompt
                    import re
                    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', prompt)
                    if email_match:
                        email = email_match.group(0)
                
                if email:
                    # Get user and session info - wait a moment for DB to be updated
                    import time
                    time.sleep(0.1)  # Small delay to ensure DB is updated
                    
                    from models.db import get_chat_user_by_email
                    user = get_chat_user_by_email(email)
                    
                    # Mark as authenticated if not already (in case of timing issue)
                    if user and not user.get("authenticated"):
                        from models.db import mark_chat_user_authenticated
                        mark_chat_user_authenticated(email)
                        user = get_chat_user_by_email(email)  # Refresh user data
                    
                    if user:
                        # Get the most recent session for this user
                        from models.db import connect_db
                        conn = connect_db()
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT session_token FROM chat_sessions 
                            WHERE user_id = ? 
                            ORDER BY created_at DESC LIMIT 1
                        """, (user["id"],))
                        session_result = cursor.fetchone()
                        conn.close()
                        
                        if session_result:
                            st.session_state.chat_session_token = session_result[0]
                            st.session_state.chat_authenticated = True
                            st.session_state.chat_user_email = email
                            st.session_state.chat_user_name = user.get("name") or "Usuario"
                            # Force immediate rerun to update authentication state
                            st.rerun()
    
    else:
        # User is authenticated - show full chat functionality
        # Display chat history
        if messages:
            for sender, content in messages:
                if sender == "user":
                    with st.chat_message("user"):
                        st.markdown(content)
                elif sender == "ai":
                    with st.chat_message("assistant", avatar="🌿"):
                        st.markdown(content)
        
        # Chat input for authenticated users
        prompt = st.chat_input("Escribe tu pregunta aquí...")
        
        if prompt:
            # Save user message
            create_message(CHAT_ID, "user", prompt)
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            try:
                # Usar el agente inteligente (Intelligent Agent es el punto de entrada)
                # Pasar is_authenticated=True porque el usuario ya está autenticado
                agent = get_intelligent_agent()
                response = agent.process_query(prompt, enable_logging=False, is_authenticated=True)
            except Exception as e:
                response = """
                😔 Lo siento, tuve un problema al procesar tu consulta.
                
                Por favor, intenta nuevamente o contacta a nuestro equipo:
                - 📧 soporte@ecomarket.com
                - 📞 +57 324 456 4450
                """
            
            # Save AI response
            create_message(CHAT_ID, "ai", response)
            
            # Display AI response with streaming
            with st.chat_message("assistant", avatar="🌿"):
                st.write_stream(stream_response(response))
    
    # Sidebar with info
    with st.sidebar:
        st.markdown("### 📞 Contacto Directo")
        st.markdown("""
            Si necesitas asistencia personalizada:
            
            **Email:** ceman217@gmail.com
            
            **Teléfono:** +57 300 733 5302
            
            **WhatsApp:** +57 300 733 5302
            
            **Horario de atención:**
            Lunes a Viernes: 9:00 AM - 6:00 PM
            Sábados: 10:00 AM - 2:00 PM
        """)
        
        st.markdown("---")
        
        st.markdown("### 🌿 Sobre EcoMarket")
        st.markdown("""
            Somos tu tienda de productos sostenibles, 
            comprometidos con el medio ambiente y 
            la calidad de vida.
        """)
        
        st.markdown("---")
        


if __name__ == "__main__":
    public_chat()
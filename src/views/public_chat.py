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
    """Public chat interface for prospective graduate students"""

    # Subtítulo (el header principal se maneja en theme_utils)
    st.markdown("<p class='subtitle'>Sistema de Recomendación de Posgrados</p>", unsafe_allow_html=True)
    
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
                        <h3>[GRADUATE] ¡Bienvenido al Sistema de Recomendación de Posgrados ICESI!</h3>
                        <p>Estoy aquí para ayudarte a encontrar el posgrado ideal para tu perfil profesional.</p>
                        <p>Te haré algunas preguntas sobre:</p>
                        <ul>
                            <li>[USER] Tu formación académica y experiencia</li>
                            <li>[TARGET] Tus intereses y objetivos profesionales</li>
                            <li>[SKILLS] Tus habilidades y competencias</li>
                            <li>[CALENDAR] Tu disponibilidad de tiempo</li>
                        </ul>
                        <p>Al finalizar, te recomendaré los programas más adecuados para ti.</p>
                    </div>
                """, unsafe_allow_html=True)
                st.session_state.auth_welcome_shown = True
        
        # Show authentication prompt from agent if no messages
        if not messages:
            # Initial greeting asking for authentication
            initial_greeting = """[GRADUATE] ¡Bienvenido/a al Sistema de Recomendación de Posgrados de la Universidad ICESI!

Soy tu asistente de admisiones y voy a ayudarte a encontrar el programa de posgrado que mejor se ajuste a tu perfil profesional.

Para comenzar con la entrevista de recomendación, necesito que te registres.

Por favor, proporciona:
1. Tu correo electrónico
2. Tu nombre completo

Te enviaré un código de verificación a tu correo para confirmar tu identidad y comenzar con la entrevista."""

            with st.chat_message("assistant", avatar="🎓"):
                st.markdown(initial_greeting)
        else:
            # Display existing chat history
            for sender, content in messages:
                if sender == "user":
                    with st.chat_message("user"):
                        st.markdown(content)
                elif sender == "ai":
                    with st.chat_message("assistant", avatar="🎓"):
                        st.markdown(content)

        # Chat input for unauthenticated users
        prompt = st.chat_input("Escribe tu correo y nombre para registrarte...")
        
        if prompt:
            # Save user message
            create_message(CHAT_ID, "user", prompt)
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            try:
                # Use intelligent agent to process authentication request
                agent = get_intelligent_agent()

                # Usar session_id basado en el CHAT_ID para mantener consistencia
                session_id = f"chat_{CHAT_ID}"

                # Process query (agent will handle OTP_SEND or OTP_VERIFY based on query content)
                response = agent.process_query(prompt, enable_logging=False, session_id=session_id)

            except Exception as e:
                response = """
                [ERROR] Lo siento, tuve un problema al procesar tu registro.

                Por favor, intenta nuevamente o contacta a nuestro equipo de admisiones:
                - [EMAIL] admisiones.posgrados@icesi.edu.co
                - [PHONE] +57 (2) 555-2000
                - [WHATSAPP] +57 318 765 4321
                """
            
            # Save AI response
            create_message(CHAT_ID, "ai", response)
            
            # Display AI response with streaming
            with st.chat_message("assistant", avatar="🎓"):
                st.write_stream(stream_response(response))
            
            # Check if response indicates successful authentication
            print(f"[DEBUG] Checking authentication in response: {response[:100]}")
            if "[OK]" in response and "autenticación exitosa" in response.lower():
                print(f"[DEBUG] Authentication detected! Retrieving email from session_id: {session_id}")
                # Get email from session memory (not from prompt, as prompt might only have OTP code)
                from tools.chat_memory import retrieve_chat_memory
                # Usar el mismo session_id que usamos arriba
                email_memory = retrieve_chat_memory(session_id, "email")
                print(f"[DEBUG] Email memory found: {email_memory}")
                
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
                    print(f"[DEBUG] Email found: {email}, proceeding with authentication setup")
                    # Get user and session info - wait a moment for DB to be updated
                    import time
                    time.sleep(0.1)  # Small delay to ensure DB is updated

                    from models.db import get_chat_user_by_email
                    user = get_chat_user_by_email(email)
                    print(f"[DEBUG] User from DB: {user}")
                    
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
                            print(f"[DEBUG] Setting session state for authenticated user")
                            st.session_state.chat_session_token = session_result[0]
                            st.session_state.chat_authenticated = True
                            st.session_state.chat_user_email = email
                            st.session_state.chat_user_name = user.get("name") or "Usuario"
                            print(f"[DEBUG] Session state updated. Forcing rerun...")
                            # Force immediate rerun to update authentication state
                            st.rerun()
                        else:
                            print(f"[DEBUG] No session token found for user")
    
    else:
        # User is authenticated - show full chat functionality
        # Display chat history
        if messages:
            for sender, content in messages:
                if sender == "user":
                    with st.chat_message("user"):
                        st.markdown(content)
                elif sender == "ai":
                    with st.chat_message("assistant", avatar="🎓"):
                        st.markdown(content)
        
        # Chat input for authenticated users
        prompt = st.chat_input("Escribe tu respuesta aquí...")
        
        if prompt:
            # Verificar nuevamente el estado de autenticación antes de procesar
            # Esto previene problemas de sincronización con el estado de Streamlit
            is_user_authenticated = False
            if st.session_state.chat_session_token:
                session_data = verify_chat_session(st.session_state.chat_session_token)
                if session_data and session_data.get("authenticated"):
                    is_user_authenticated = True
                    # Actualizar estado por si acaso
                    st.session_state.chat_authenticated = True
                    st.session_state.chat_user_email = session_data.get("email")
                    st.session_state.chat_user_name = session_data.get("name")
                else:
                    # Session expired or invalid - redirect to unauthenticated flow
                    st.session_state.chat_authenticated = False
                    st.session_state.chat_session_token = None
                    st.rerun()
                    return
            
            if not is_user_authenticated:
                # Si por alguna razón no está autenticado, redirigir
                st.rerun()
                return
            
            # Save user message
            create_message(CHAT_ID, "user", prompt)
            
            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)
            
            try:
                # Usar el agente inteligente (Intelligent Agent es el punto de entrada)
                # Pasar is_authenticated=True porque el usuario ya está autenticado
                # También pasar información de sesión (email, nombre) para uso automático
                agent = get_intelligent_agent()

                # Usar session_id basado en el CHAT_ID para mantener consistencia
                session_id = f"chat_{CHAT_ID}"

                session_info = {
                    "email": st.session_state.chat_user_email,
                    "name": st.session_state.chat_user_name
                } if st.session_state.chat_user_email else None
                response = agent.process_query(prompt, enable_logging=False, session_id=session_id, is_authenticated=True, session_info=session_info)
            except Exception as e:
                response = """
                [ERROR] Lo siento, tuve un problema al procesar tu respuesta.

                Por favor, intenta nuevamente o contacta a nuestro equipo de admisiones:
                - [EMAIL] admisiones.posgrados@icesi.edu.co
                - [PHONE] +57 (2) 555-2000
                - [WHATSAPP] +57 318 765 4321
                """
            
            # Save AI response
            create_message(CHAT_ID, "ai", response)
            
            # Display AI response with streaming
            with st.chat_message("assistant", avatar="🎓"):
                st.write_stream(stream_response(response))
    
    # Sidebar with info
    with st.sidebar:
        st.markdown("### [PHONE] Contacto Admisiones")
        st.markdown("""
            Si necesitas asistencia personalizada:

            **Email:** admisiones.posgrados@icesi.edu.co

            **Teléfono:** +57 (2) 555-2000

            **WhatsApp:** +57 318 765 4321

            **Horario de atención:**
            Lunes a Viernes: 8:00 AM - 6:00 PM
            Sábados: 9:00 AM - 1:00 PM
        """)

        st.markdown("---")

        st.markdown("### [GRADUATE] Sobre Nuestros Posgrados")
        st.markdown("""
            La Universidad ICESI ofrece programas de posgrado
            de alta calidad, diseñados para profesionales que
            buscan impulsar su carrera y transformar su futuro.

            **Programas disponibles:**
            - Maestría en Ciencia de Datos
            - Maestría en Ingeniería de Software
            - MBA - Administración
            - Maestría en Marketing Digital

            [WEB] www.icesi.edu.co/posgrados
        """)

        st.markdown("---")
        


if __name__ == "__main__":
    public_chat()
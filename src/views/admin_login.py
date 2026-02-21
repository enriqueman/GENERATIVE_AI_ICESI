import streamlit as st
import time
from controllers.auth import verify_admin, create_session
from utils.theme_utils import apply_theme_with_header
from models.db import init_database

def admin_login():
    """Admin login page"""
    
    # Inicializar la base de datos
    init_database()
    
    # Aplicar tema con header
    apply_theme_with_header()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h2 class='login-header'>🔐 Admin Login</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: var(--text-color); margin-bottom: 30px;'>Acceso administrativo</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Ingresa tu usuario")
            password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña")
            
            submit = st.form_submit_button("Iniciar Sesión", type="primary", use_container_width=True)
            
            if submit:
                if username and password:
                    user_info = verify_admin(username, password)
                    
                    if user_info:
                        # Create session
                        session_token = create_session(user_info["id"])
                        st.session_state.session_token = session_token
                        st.session_state.user_info = user_info
                        
                        st.success("[OK] Login exitoso!")
                        st.balloons()
                        time.sleep(1)
                        st.switch_page("views/admin_panel.py")
                    else:
                        st.error("[ERROR] Usuario o contraseña incorrectos")
                else:
                    st.warning("[WARNING] Por favor ingresa usuario y contraseña")
        
        st.markdown("---")
        
        # Google Login button
        if st.button("[GOOGLE] Continuar con Google", use_container_width=True, type="secondary"):
            st.switch_page("views/google_login.py")
        
        st.markdown("---")
        
        if st.button("← Volver al Chat Público", use_container_width=True):
            st.switch_page("app.py")

if __name__ == "__main__":
    admin_login()
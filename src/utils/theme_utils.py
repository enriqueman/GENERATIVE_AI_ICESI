"""
Utilidades para el sistema de temas global
"""

import streamlit as st
from config.theme_config import get_available_themes, generate_css, get_theme

def init_theme():
    """Inicializa el tema en session_state si no existe"""
    if "selected_theme" not in st.session_state:
        st.session_state.selected_theme = "default"

def render_theme_selector():
    """Renderiza el selector de temas en el header"""
    # Asegurar que el tema esté inicializado
    init_theme()
    
    # Crear el selector de temas
    themes = get_available_themes()
    theme_options = {get_theme(theme)["name"]: theme for theme in themes}
    
    # Crear un header personalizado con el selector de temas integrado
    st.markdown("""
        <div class="custom-header">
            <h1>[GRADUATE] Universidad ICESI - Sistema de Recomendación de Posgrados</h1>
            <div class="theme-controls">
                <span>[THEME] Tema:</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Posicionar el selector de temas en la misma línea que el header
    col1, col2, col3 = st.columns([0.7, 0.1, 0.2])
    
    with col3:
        selected_theme_name = st.selectbox(
            "Seleccionar tema",
            options=list(theme_options.keys()),
            index=list(theme_options.keys()).index(get_theme(st.session_state.selected_theme)["name"]),
            key="theme_selector",
            help="Cambia el esquema de colores de la aplicación",
            label_visibility="collapsed"
        )
        
        # Actualizar tema si cambió
        if theme_options[selected_theme_name] != st.session_state.selected_theme:
            st.session_state.selected_theme = theme_options[selected_theme_name]
            st.rerun()

def apply_global_theme():
    """Aplica el tema seleccionado globalmente"""
    # Asegurar que el tema esté inicializado
    init_theme()
    
    # Renderizar el selector de temas
    render_theme_selector()
    
    # Aplicar CSS del tema
    css = generate_css(st.session_state.selected_theme)
    st.markdown(css, unsafe_allow_html=True)

def apply_theme_css_only():
    """Aplica solo el CSS del tema sin el selector (para páginas secundarias)"""
    # Asegurar que el tema esté inicializado
    init_theme()
    
    # Aplicar CSS del tema
    css = generate_css(st.session_state.selected_theme)
    st.markdown(css, unsafe_allow_html=True)

def render_header_with_theme_selector():
    """Renderiza el header con selector de temas integrado para todas las páginas"""
    # Asegurar que el tema esté inicializado
    init_theme()
    
    # Crear el selector de temas
    themes = get_available_themes()
    theme_options = {get_theme(theme)["name"]: theme for theme in themes}
    
    # Crear un header personalizado con el selector de temas integrado
    st.markdown("""
        <div class="custom-header">
            <h1>[GRADUATE] Universidad ICESI - Sistema de Recomendación de Posgrados</h1>
            <div class="theme-controls">
                <span>[THEME] Tema:</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Posicionar el selector de temas justo debajo del header, alineado a la derecha
    col1, col2, col3 = st.columns([0.75, 0.05, 0.2])
    
    with col3:
        selected_theme_name = st.selectbox(
            "Seleccionar tema",
            options=list(theme_options.keys()),
            index=list(theme_options.keys()).index(get_theme(st.session_state.selected_theme)["name"]),
            key="theme_selector",
            help="Cambia el esquema de colores de la aplicación",
            label_visibility="collapsed"
        )
        
        # Actualizar tema si cambió
        if theme_options[selected_theme_name] != st.session_state.selected_theme:
            st.session_state.selected_theme = theme_options[selected_theme_name]
            st.rerun()

def apply_theme_with_header():
    """Aplica el tema con header para todas las páginas"""
    # Asegurar que el tema esté inicializado
    init_theme()
    
    # Renderizar el header con selector de temas
    render_header_with_theme_selector()
    
    # Aplicar CSS del tema
    css = generate_css(st.session_state.selected_theme)
    st.markdown(css, unsafe_allow_html=True)

def get_current_theme():
    """Retorna el tema actualmente seleccionado"""
    init_theme()
    return st.session_state.selected_theme

def get_current_theme_config():
    """Retorna la configuración del tema actual"""
    init_theme()
    return get_theme(st.session_state.selected_theme)

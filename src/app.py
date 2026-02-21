import streamlit as st
import sys
import os

# Agregar el directorio src al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from views.public_chat import public_chat
from utils.theme_utils import apply_global_theme
from models.db import init_database
from utils.vector_functions import initialize_sample_collection

# Page configuration
st.set_page_config(
    page_title="Universidad ICESI - Sistema de Recomendación de Posgrados",
    page_icon="[GRADUATE]",
    layout="wide",
    initial_sidebar_state="expanded"
)

if __name__ == "__main__":
    # La inicialización se hace en init_app.py antes de ejecutar la aplicación
    # Solo inicializar la base de datos si es necesario
    init_database()
    
    # Aplicar tema global
    apply_global_theme()
    
    # Ejecutar la aplicación principal
    public_chat()
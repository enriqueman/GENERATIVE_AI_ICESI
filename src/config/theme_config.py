"""
Configuración de temas para la aplicación EcoMarket
"""

# Definición de temas disponibles
THEMES = {
    "default": {
        "name": "[ECOMARKET] EcoMarket (Verde)",
        "primary_color": "#2E7D32",
        "secondary_color": "#4CAF50", 
        "accent_color": "#E8F5E9",
        "text_color": "#333333",
        "background_color": "#FFFFFF",
        "sidebar_color": "#F5F5F5"
    },
    "ocean": {
        "name": "🌊 Océano (Azul)",
        "primary_color": "#1976D2",
        "secondary_color": "#42A5F5",
        "accent_color": "#E3F2FD",
        "text_color": "#333333",
        "background_color": "#FFFFFF",
        "sidebar_color": "#F5F5F5"
    },
    "sunset": {
        "name": "🌅 Atardecer (Naranja)",
        "primary_color": "#F57C00",
        "secondary_color": "#FFB74D",
        "accent_color": "#FFF3E0",
        "text_color": "#333333",
        "background_color": "#FFFFFF",
        "sidebar_color": "#F5F5F5"
    },
    "lavender": {
        "name": "💜 Lavanda (Púrpura)",
        "primary_color": "#7B1FA2",
        "secondary_color": "#BA68C8",
        "accent_color": "#F3E5F5",
        "text_color": "#333333",
        "background_color": "#FFFFFF",
        "sidebar_color": "#F5F5F5"
    },
    "forest": {
        "name": "🌲 Bosque (Verde Oscuro)",
        "primary_color": "#1B5E20",
        "secondary_color": "#388E3C",
        "accent_color": "#E8F5E9",
        "text_color": "#333333",
        "background_color": "#FFFFFF",
        "sidebar_color": "#F5F5F5"
    },
    "cherry": {
        "name": "🍒 Cereza (Rojo)",
        "primary_color": "#C62828",
        "secondary_color": "#EF5350",
        "accent_color": "#FFEBEE",
        "text_color": "#333333",
        "background_color": "#FFFFFF",
        "sidebar_color": "#F5F5F5"
    }
}

def get_theme(theme_name="default"):
    """Obtiene la configuración de un tema específico"""
    return THEMES.get(theme_name, THEMES["default"])

def get_available_themes():
    """Retorna la lista de temas disponibles"""
    return list(THEMES.keys())

def generate_css(theme_name="default"):
    """Genera CSS personalizado basado en el tema seleccionado"""
    theme = get_theme(theme_name)
    
    css = f"""
    <style>
    /* Variables CSS para el tema {theme['name']} */
    :root {{
        --primary-color: {theme['primary_color']};
        --secondary-color: {theme['secondary_color']};
        --accent-color: {theme['accent_color']};
        --text-color: {theme['text_color']};
        --background-color: {theme['background_color']};
        --sidebar-color: {theme['sidebar_color']};
    }}
    
    /* Estilos globales */
    .main-header {{
        text-align: center;
        color: var(--primary-color);
        padding: 20px;
        background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: bold;
    }}
    
    .subtitle {{
        text-align: center;
        color: var(--text-color);
        font-size: 18px;
        margin-bottom: 30px;
        opacity: 0.8;
    }}
    
    .welcome-box {{
        background-color: var(--accent-color);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border-left: 4px solid var(--primary-color);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    
    .welcome-box h3 {{
        color: var(--primary-color);
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 15px;
        text-align: center;
    }}
    
    .welcome-box p {{
        color: var(--text-color);
        font-size: 16px;
        line-height: 1.6;
        margin-bottom: 15px;
    }}
    
    .welcome-box ul {{
        color: var(--text-color);
        font-size: 15px;
        line-height: 1.8;
        margin-bottom: 20px;
        padding-left: 20px;
    }}
    
    .welcome-box li {{
        margin-bottom: 8px;
        color: var(--text-color);
    }}
    
    .welcome-box strong {{
        color: var(--primary-color);
        font-size: 16px;
        font-weight: bold;
    }}
    
    .login-header {{
        text-align: center;
        color: var(--primary-color);
        margin-bottom: 30px;
    }}
    
    .login-container {{
        max-width: 400px;
        margin: 50px auto;
        padding: 30px;
        background-color: var(--sidebar-color);
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border: 1px solid var(--accent-color);
    }}
    
    /* Botones personalizados */
    .stButton > button {{
        background-color: var(--primary-color);
        color: white;
        border: none;
        border-radius: 6px;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background-color: var(--secondary-color);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    
    /* Sidebar personalizada */
    .css-1d391kg {{
        background-color: var(--sidebar-color);
    }}
    
    /* Chat messages */
    .stChatMessage {{
        border-radius: 10px;
    }}
    
    /* Input personalizado */
    .stTextInput > div > div > input {{
        border: 2px solid var(--accent-color);
        border-radius: 6px;
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px var(--accent-color);
    }}
    
    /* Selectbox personalizado */
    .stSelectbox > div > div {{
        background-color: var(--background-color);
        border: 2px solid var(--accent-color);
        border-radius: 6px;
    }}
    
    /* Selectbox del tema - estilos específicos */
    .stSelectbox[data-testid="stSelectbox"] > div > div {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border: 2px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 6px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
        min-height: 36px !important;
        margin-top: -5px !important;
    }}
    
    .stSelectbox[data-testid="stSelectbox"] > div > div:hover {{
        background-color: white !important;
        border-color: rgba(255, 255, 255, 0.6) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
    }}
    
    /* Texto del selectbox del tema */
    .stSelectbox[data-testid="stSelectbox"] > div > div > div {{
        color: var(--text-color) !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }}
    
    /* Posicionamiento del selector para que se vea integrado */
    .stSelectbox[data-testid="stSelectbox"] {{
        margin-top: -8px !important;
    }}
    
    /* Opciones del dropdown del tema */
    .stSelectbox[data-testid="stSelectbox"] .stSelectbox-option {{
        background-color: white;
        color: var(--text-color);
        border-bottom: 1px solid var(--accent-color);
    }}
    
    .stSelectbox[data-testid="stSelectbox"] .stSelectbox-option:hover {{
        background-color: var(--accent-color);
        color: var(--primary-color);
    }}
    
    /* Icono del selectbox del tema */
    .stSelectbox[data-testid="stSelectbox"] > div > div > div > div {{
        color: var(--primary-color) !important;
    }}
    
    /* Tabs personalizados */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: var(--accent-color);
        border-radius: 6px;
        color: var(--text-color);
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: var(--primary-color);
        color: white;
    }}
    
    /* Theme selector */
    .theme-selector {{
        position: fixed;
        top: 10px;
        right: 10px;
        z-index: 999;
        background: white;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border: 1px solid var(--accent-color);
    }}
    
    .theme-selector select {{
        border: 1px solid var(--primary-color);
        border-radius: 4px;
        padding: 5px 10px;
        background: white;
        color: var(--text-color);
    }}
    
    /* Custom header */
    .custom-header {{
        background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
        padding: 15px 20px;
        margin: -1rem -1rem 1rem -1rem;
        border-radius: 0 0 15px 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: relative;
    }}
    
    .custom-header h1 {{
        color: white;
        font-weight: bold;
        font-size: 20px;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }}
    
    .theme-controls {{
        display: flex;
        align-items: center;
        gap: 10px;
        color: white;
    }}
    
    .theme-controls span {{
        font-size: 14px;
        font-weight: 500;
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }}
    
    .theme-select {{
        background-color: rgba(255, 255, 255, 0.9);
        border: 2px solid rgba(255, 255, 255, 0.3);
        border-radius: 6px;
        color: var(--text-color);
        font-size: 14px;
        font-weight: 500;
        padding: 6px 12px;
        min-width: 150px;
        cursor: pointer;
        transition: all 0.3s ease;
    }}
    
    .theme-select:hover {{
        background-color: white;
        border-color: rgba(255, 255, 255, 0.6);
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }}
    
    .theme-select:focus {{
        outline: none;
        background-color: white;
        border-color: white;
        box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.3);
    }}
    
    .theme-select option {{
        background-color: white;
        color: var(--text-color);
        padding: 8px;
    }}
    </style>
    """
    
    return css

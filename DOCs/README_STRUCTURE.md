# Estructura del Proyecto EcoMarket

## 📁 Organización de Carpetas

```
GENERATIVE_AI_ICESI/
├── app.py                          # Punto de entrada principal de la aplicación
├── setup.py                        # Script de configuración inicial
├── requirements.txt                # Dependencias del proyecto
├── README.md                       # Documentación principal
├── README_STRUCTURE.md            # Este archivo - documentación de estructura
│
├── controllers/                    # Controladores de la aplicación
│   ├── __init__.py
│   └── auth.py                    # Autenticación y sesiones de usuario
│
├── models/                        # Modelos de datos y base de datos
│   ├── __init__.py
│   └── db.py                      # Operaciones de base de datos SQLite
│
├── views/                         # Vistas y páginas de la aplicación
│   ├── __init__.py
│   ├── public_chat.py             # Chat público para clientes
│   ├── admin_login.py             # Página de login de administradores
│   └── admin_panel.py             # Panel de administración
│
├── pages/                         # Enlaces simbólicos para compatibilidad con Streamlit
│   ├── admin_login.py -> ../views/admin_login.py
│   └── admin_panel.py -> ../views/admin_panel.py
│
├── utils/                         # Utilidades y funciones auxiliares
│   ├── __init__.py
│   ├── vector_functions.py        # Funciones de RAG y vectorización
│   └── theme_utils.py             # Utilidades del sistema de temas
│
├── config/                        # Configuraciones de la aplicación
│   ├── __init__.py
│   └── theme_config.py            # Configuración de temas y estilos
│
└── static/                        # Archivos estáticos
    ├── persist/                   # Base de datos vectorial ChromaDB
    ├── sample_documents/          # Documentos de ejemplo
    └── temp_files/                # Archivos temporales
```

## 🎯 Descripción de Componentes

### Controllers (`controllers/`)
- **auth.py**: Maneja la autenticación de usuarios administradores, creación de sesiones y verificación de permisos.

### Models (`models/`)
- **db.py**: Contiene todas las operaciones de base de datos SQLite, incluyendo CRUD para chats, mensajes, fuentes y usuarios.

### Views (`views/`)
- **public_chat.py**: Interfaz principal del chat público para clientes.
- **admin_login.py**: Página de inicio de sesión para administradores.
- **admin_panel.py**: Panel de control para gestión de documentos y configuración.

### Utils (`utils/`)
- **vector_functions.py**: Funciones para procesamiento de documentos, creación de embeddings y búsqueda semántica.
- **theme_utils.py**: Utilidades para el sistema de temas global de la aplicación.

### Config (`config/`)
- **theme_config.py**: Definición de temas, colores y estilos CSS personalizados.

### Static (`static/`)
- **persist/**: Almacenamiento de la base de datos vectorial ChromaDB.
- **sample_documents/**: Documentos de ejemplo para la base de conocimiento.
- **temp_files/**: Archivos temporales durante el procesamiento.

## 🔧 Beneficios de esta Estructura

1. **Separación de responsabilidades**: Cada carpeta tiene un propósito específico.
2. **Mantenibilidad**: Fácil localización y modificación de componentes.
3. **Escalabilidad**: Estructura preparada para crecimiento del proyecto.
4. **Claridad**: Código organizado y fácil de entender.
5. **Reutilización**: Componentes bien definidos y reutilizables.

## 🚀 Cómo Ejecutar

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
streamlit run app.py
```

## 📝 Notas Importantes

- Todas las importaciones han sido actualizadas para reflejar la nueva estructura.
- Los archivos estáticos se han movido a la carpeta `static/`.
- La base de datos SQLite se mantiene en la raíz del proyecto para compatibilidad.
- **Compatibilidad con Streamlit**: Se crearon enlaces simbólicos en `pages/` que apuntan a los archivos en `views/` para mantener la compatibilidad con el sistema de navegación automática de Streamlit.

## 🔗 Enlaces Simbólicos

Streamlit busca automáticamente páginas en la carpeta `pages/`. Para mantener nuestra estructura organizada y la compatibilidad con Streamlit, se crearon enlaces simbólicos:

- `pages/admin_login.py` → `views/admin_login.py`
- `pages/admin_panel.py` → `views/admin_panel.py`

Esto permite que:
- ✅ Streamlit encuentre las páginas automáticamente
- ✅ El código se mantenga organizado en `views/`
- ✅ Los cambios en `views/` se reflejen automáticamente en `pages/`

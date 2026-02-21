# Templates - Sistema RAG EcoMarket

Este directorio contiene todas las plantillas de prompts utilizadas por el sistema RAG de EcoMarket.

## 📁 Estructura

```
templates/
├── __init__.py          # Inicialización del módulo
├── agent_prompts.py     # Plantillas de prompts del agente
└── README.md           # Esta documentación
```

## 🎯 Plantillas Disponibles

### 1. `get_rag_prompt_template()`
**Propósito**: Prompt principal para consultas RAG sobre documentos.

**Uso**: Se utiliza cuando el agente necesita responder preguntas basándose en el contexto recuperado de los documentos.

**Contexto proporcionado**:
- Información sobre EcoMarket
- Capacidades del sistema
- Contexto del usuario
- Reglas de respuesta

**Placeholders**:
- `{question}`: Pregunta del usuario
- `{context}`: Contexto recuperado de los documentos

### 2. `get_product_query_prompt_template()`
**Propósito**: Prompt para consultas específicas de productos.

**Uso**: Se utiliza cuando se busca información sobre productos en el inventario.

**Placeholders**:
- `{question}`: Pregunta del usuario sobre productos
- `{products_info}`: Información de productos recuperada

### 3. `get_ticket_response_prompt_template()`
**Propósito**: Prompt para formatear respuestas sobre tickets.

**Uso**: Se utiliza al responder sobre tickets creados o consultados.

**Placeholders**:
- `{ticket_info}`: Información del ticket

### 4. `get_system_context_prompt()`
**Propósito**: Contexto general del sistema EcoMarket.

**Uso**: Proporciona información de fondo sobre la empresa y sus servicios.

**Contexto incluye**:
- Información de EcoMarket
- Departamentos
- Productos disponibles
- Contacto de soporte

### 5. `get_help_message()`
**Propósito**: Mensaje de ayuda para usuarios.

**Uso**: Se muestra cuando el usuario necesita ayuda inicial.

### 6. `get_error_message(error_type)`
**Propósito**: Mensajes de error predefinidos.

**Tipos de error disponibles**:
- `"general"`: Error general
- `"not_found"`: No se encontró información
- `"database"`: Problema de conexión a base de datos
- `"validation"`: Información faltante o inválida

## 📝 Uso

### Importar una plantilla:

```python
from templates.agent_prompts import get_rag_prompt_template

template = get_rag_prompt_template()
# Usar el template con el LLM
```

### Usar una plantilla específica:

```python
from templates.agent_prompts import get_template

# Obtener el template RAG
rag_template = get_template("rag_prompt")

# Obtener el template de productos
product_template = get_template("product_query")
```

### Modificar una plantilla:

1. Abre `agent_prompts.py`
2. Localiza la función de la plantilla que deseas modificar
3. Edita el string de retorno
4. Guarda el archivo

## 🔧 Personalización

Para personalizar las plantillas:

1. **Crea una nueva función** en `agent_prompts.py`:

```python
def get_mi_prompt_template():
    return """
    Tu template personalizado aquí
    Placeholder: {variable}
    """
```

2. **Regístrala en el diccionario TEMPLATES**:

```python
TEMPLATES = {
    "rag_prompt": get_rag_prompt_template(),
    "mi_prompt": get_mi_prompt_template(),
    # ...
}
```

3. **Úsala en el código**:

```python
from templates.agent_prompts import get_template

mi_template = get_template("mi_prompt")
```

## 📊 Flujo de Uso

```
Usuario hace consulta
         ↓
Sistema detecta tipo de consulta
         ↓
Selecciona template apropiado
         ↓
Llena template con contexto
         ↓
Envía a LLM
         ↓
Usuario recibe respuesta
```

## ⚙️ Importación Actual

El sistema actual importa automáticamente el template RAG en `src/utils/vector_functions.py`:

```python
try:
    from templates.agent_prompts import get_rag_prompt_template
    message = get_rag_prompt_template()
except ImportError:
    # Fallback si no se puede importar
    message = """..."""
```

## 🎨 Ejemplo de Plantilla

```python
def get_rag_prompt_template():
    return """
    Eres el asistente virtual de EcoMarket...
    
    Pregunta del usuario: {question}
    Contexto relevante: {context}
    Tu respuesta: ...
    """
```

## 📝 Notas Importantes

1. **Placeholders**: Todas las plantillas usan placeholders con formato `{nombre_variable}`
2. **Idiomas**: Las respuestas deben generarse en el idioma del usuario
3. **Contexto**: Los templates incluyen contexto sobre EcoMarket y sus capacidades
4. **Actualización**: Modificar templates no requiere reiniciar el servidor (en desarrollo)

## 🚀 Mejoras Futuras

- [ ] Template para consultas de inventario
- [ ] Template para análisis de sentimientos
- [ ] Template para resúmenes de documentos
- [ ] Template para generación de reportes
- [ ] Integración con sistema de traducción


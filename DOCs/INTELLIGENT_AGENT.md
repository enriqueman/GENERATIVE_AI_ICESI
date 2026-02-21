# Agente Inteligente con Sistema de Reasoning

## 🎯 Visión General

El sistema EcoMarket ahora incluye un **Agente Inteligente** que usa **LLM para analizar consultas** y **decidir qué herramientas usar**, en lugar de depender únicamente de heurísticas rígidas basadas en keywords.

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    CONSULTA DEL USUARIO                      │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              AGENTE INTELIGENTE (Reasoning)                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  1. Analiza la consulta con LLM                        │  │
│  │  2. Determina intención del usuario                   │  │
│  │  3. Decide qué herramientas usar                      │  │
│  │  4. Identifica si necesita información adicional       │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         ↓
         ┌───────────────┴───────────────┐
         ↓                                ↓
┌────────────────┐              ┌────────────────┐
│ EJECUTA        │              │ NO HAY INFO     │
│ HERRAMIENTAS   │              │ SUFICIENTE      │
└────────┬───────┘              └────────────────┘
         ↓
         ↓
┌─────────────────────────────────────────────────────────────┐
│              GENERA RESPUESTA FINAL                         │
│  - Usa resultados de herramientas                           │
│  - Sintetiza información                                    │
│  - Presenta respuesta al usuario                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Componentes del Sistema

### 1. **Intelligent Agent** (`src/agents/intelligent_agent.py`)

El agente principal que:
- Analiza consultas usando LLM
- Decide qué herramientas usar
- Ejecuta herramientas
- Genera respuestas finales

**Métodos principales:**

```python
# Analizar una consulta
analysis = agent.analyze_query("¿Tienen botellas de acero?")
# Retorna: {"intent": "...", "tools_needed": ["PRODUCT_SEARCH"], ...}

# Ejecutar herramientas
results = agent.execute_tools(analysis, original_query)

# Generar respuesta final
response = agent.generate_response(analysis, results, original_query)

# Procesar consulta completa (todo en uno)
response = agent.process_query("¿Tienen botellas de acero?")
```

### 2. **Sistema de Reasoning** (`src/templates/agent_reasoning.py`)

Contiene los prompts para:
- **Reasoning**: Analizar consultas y decidir herramientas
- **Respuestas**: Generar respuestas finales
- **Contexto**: Información del sistema

**Ejemplo de reasoning prompt:**

```python
"""
Eres el agente inteligente de EcoMarket.

HERRAMIENTAS DISPONIBLES:
1. RAG_SEARCH - Buscar en documentos
2. PRODUCT_SEARCH - Buscar productos
3. TICKET_CREATE - Crear tickets
4. TICKET_QUERY - Consultar tickets

Analiza la consulta del usuario y decide qué herramientas usar.

RESPONDE CON JSON:
{
    "intent": "descripción de la intención",
    "tools_needed": ["TOOL_NAME"],
    "reasoning": "por qué usar esta herramienta"
}
"""
```

## 🛠️ Herramientas Disponibles

### 1. **RAG_SEARCH**
**Uso**: Buscar información en documentos  
**Cuándo usar**: Preguntas sobre políticas, procesos, información general  
**Ejemplo**: "¿Cuál es la política de devoluciones?"

### 2. **PRODUCT_SEARCH**
**Uso**: Buscar productos en inventario  
**Cuándo usar**: Preguntas sobre productos, disponibilidad, precios  
**Ejemplo**: "¿Tienen botellas de acero?"

### 3. **TICKET_CREATE**
**Uso**: Crear tickets  
**Cuándo usar**: Solicitudes de devolución, compra, queja, etc.  
**Ejemplo**: "Quiero devolver un producto defectuoso"

### 4. **TICKET_QUERY**
**Uso**: Consultar tickets existentes  
**Cuándo usar**: Ver estado de tickets  
**Ejemplo**: "Consultar mi ticket TKT-12345"

## 🔄 Flujo de Procesamiento

### Paso 1: Análisis (Reasoning)

```python
# El agente analiza la consulta
analysis = agent.analyze_query("¿Tienen botellas de acero?")

# Resultado:
{
    "intent": "Buscar producto específico en inventario",
    "tools_needed": ["PRODUCT_SEARCH"],
    "reasoning": "El usuario pregunta por un producto específico",
    "requires_additional_info": false
}
```

### Paso 2: Ejecución

```python
# Ejecuta las herramientas necesarias
results = agent.execute_tools(analysis, query)

# Resultado:
{
    "tools_used": ["PRODUCT_SEARCH"],
    "data": {
        "product_search": {
            "existe": true,
            "producto_nombre": "Botella de Acero",
            "precio": "$25.00",
            ...
        }
    }
}
```

### Paso 3: Respuesta Final

```python
# Genera la respuesta final sintetizando todo
response = agent.generate_response(analysis, results, query)

# Respuesta:
"✅ Sí, tenemos Botella de Acero disponible. 
- Categoría: Hogar
- Stock: 50 unidades  
- Precio: $25.00
..."
```

## 📊 Ventajas del Sistema Inteligente

### ✅ **Flexibilidad**
- No depende de keywords rígidas
- Entiende intenciones del usuario
- Maneja variaciones de lenguaje

### ✅ **Inteligencia**
- LLM analiza la consulta
- Decide qué herramientas usar
- Identifica información faltante

### ✅ **Extensibilidad**
- Fácil agregar nuevas herramientas
- Prompts configurables
- Sistema modular

### ✅ **Robustez**
- Fallback a heurísticas si LLM falla
- Manejo de errores
- Tracing completo

## 🚀 Uso del Sistema

### Uso Básico

```python
from agents.intelligent_agent import get_intelligent_agent

# Obtener instancia del agente
agent = get_intelligent_agent()

# Procesar consulta
response = agent.process_query("¿Tienen botellas de acero?")
print(response)
```

### Uso Avanzado

```python
# 1. Analizar consulta
analysis = agent.analyze_query("Quiero devolver un producto")

# 2. Verificar si necesita información
if analysis.get("requires_additional_info"):
    print(f"Necesita: {analysis.get('missing_info')}")

# 3. Ejecutar herramientas
results = agent.execute_tools(analysis, "Quiero devolver un producto")

# 4. Generar respuesta
response = agent.generate_response(analysis, results, "Quiero devolver...")
```

## 🔄 Comparación: Antes vs Ahora

### Antes (Sistema Rígido)

```python
# Dependía de keywords
if "producto" in query.lower():
    return handle_product_query()
elif "ticket" in query.lower():
    return handle_ticket_query()
else:
    return handle_rag_query()
```

**Problemas:**
- ❌ Rígido con keywords
- ❌ No entiende intenciones
- ❌ Difícil mantener

### Ahora (Sistema Inteligente)

```python
# LLM analiza y decide
analysis = llm.analyze(query)
tools = analysis["tools_needed"]
execute(tools)
```

**Ventajas:**
- ✅ Flexible con lenguaje natural
- ✅ Entiende intenciones
- ✅ Fácil de extender

## 🎨 Ejemplos de Uso

### Ejemplo 1: Búsqueda de Producto

```
Usuario: "¿Tienen botellas de acero?"

Agente:
1. Analiza: "intent: buscar producto en inventario"
2. Herramienta: PRODUCT_SEARCH
3. Ejecuta: Busca en inventario
4. Responde: "Sí, tenemos Botella de Acero disponible. Precio: $25, Stock: 50 unidades"
```

### Ejemplo 2: Creación de Ticket

```
Usuario: "Quiero devolver un producto"

Agente:
1. Analiza: "intent: crear ticket de devolución"
2. Detecta: falta información (email, factura, producto)
3. Pide: "Para procesar tu devolución, necesito:
   - Tu email
   - Número de factura
   - Producto a devolver"
```

### Ejemplo 3: Consulta de Información

```
Usuario: "¿Cuál es la política de devoluciones?"

Agente:
1. Analiza: "intent: consultar política en documentos"
2. Herramienta: RAG_SEARCH
3. Ejecuta: Busca en documentos
4. Responde: [Información sobre política de devoluciones]
```

## 📝 Configuración

### Variables de Entorno

```env
OPENAI_API_KEY=tu_api_key          # Requerido para LLM
LANGSMITH_TRACING=false            # Opcional
LANGCHAIN_TRACING_V2=false         # Opcional
```

### Parámetros del LLM

```python
# En intelligent_agent.py
self.llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1  # Baja temperatura para reasoning preciso
)
```

## 🔍 Debugging y Tracing

El sistema incluye logging completo:

```python
# Ver análisis de reasoning
tracer.log(operation="REASONING_ANALYSIS", ...)

# Ver ejecución de herramientas
tracer.log(operation="TOOL_EXECUTION", ...)

# Ver generación de respuesta
tracer.log(operation="RESPONSE_GENERATION", ...)
```

## 🎯 Próximos Pasos

1. **Más herramientas**: Agregar nuevas capacidades
2. **Memoria**: Recordar contexto de conversación
3. **Streaming**: Respuestas en tiempo real
4. **Multimodal**: Procesar imágenes y documentos

## 📚 Archivos Relacionados

- `src/agents/intelligent_agent.py` - Agente principal
- `src/templates/agent_reasoning.py` - Prompts de reasoning
- `src/agents/rag_agent.py` - Agente RAG (base)
- `src/utils/vector_functions.py` - Funciones RAG

## 🤝 Contribución

Para agregar nuevas herramientas:

1. Agregar en `agent_reasoning.py`:
```python
HERRAMIENTAS DISPONIBLES:
...
N. TU_HERRAMIENTA - Descripción
```

2. Implementar en `intelligent_agent.py`:
```python
def _execute_tu_herramienta(self, query):
    # Tu implementación
    pass
```

3. Mapear en `execute_tools()`:
```python
elif tool == "TU_HERRAMIENTA":
    results["data"]["tu_herramienta"] = self._execute_tu_herramienta(query)
```


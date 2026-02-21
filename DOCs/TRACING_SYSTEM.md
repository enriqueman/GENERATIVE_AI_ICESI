# Sistema de Trazabilidad - EcoMarket

## 📊 Visión General

El sistema de trazabilidad de EcoMarket registra todas las operaciones importantes para monitorización, debugging y análisis de rendimiento.

## 🔍 Componentes del Sistema de Tracing

### 1. **TracingLogger** (`src/utils/tracing.py`)
Sistema centralizado de logging que registra:
- Todas las operaciones del sistema
- Metadata relevante
- Tiempos de procesamiento
- Errores y excepciones

### 2. **Integración LangSmith** (Opcional)
- Trazabilidad avanzada si está configurado
- Variables de entorno: `LANGSMITH_TRACING`, `LANGSMITH_API_KEY`

## 📝 Puntos de Trazabilidad Actuales

### ✅ **Agent Tracing**

#### Intelligent Agent
```python
tracer.log("ORCHESTRATOR_ANALYSIS", ...)      # Analiza consulta
tracer.log("TOOLS_EXECUTED", ...)             # Ejecuta herramientas
tracer.log("INTELLIGENT_QUERY_COMPLETE", ...) # Resumen final
tracer.log("INTELLIGENT_AGENT_ERROR", ...)    # Errores
```

#### Orchestrator Agent
```python
tracer.log("REASONING_ANALYSIS", ...)        # Análisis reasoning
tracer.log("REASONING_ERROR", ...)           # Errores de reasoning
tracer.log("TOOL_EXECUTION_ERROR", ...)      # Errores de herramientas
```

#### Response Agent
```python
tracer.log("RESPONSE_GENERATION_ERROR", ...)  # Errores de generación
```

#### RAG Agent
```python
tracer.log("AGENT_INITIALIZATION", ...)      # Inicialización
tracer.log("AGENT_PROCESSING", ...)          # Procesamiento
tracer.log("RAG_ERROR", ...)                 # Errores RAG
tracer.log("PRODUCT_QUERY", ...)             # Consultas productos
tracer.log("TICKET_QUERY_ERROR", ...)        # Errores tickets
```

### ✅ **Tools Tracing**

#### Ticket Manager
```python
tracer.log("CREATE_RETURN_TICKET", ...)
tracer.log("CREATE_PURCHASE_TICKET", ...)
tracer.log("GENERATE_TRACKING_GUIDE", ...)
tracer.log("QUERY_TRACKING_ERROR", ...)
tracer.log("GET_INVOICE_ERROR", ...)
tracer.log("CREATE_COMPLAINT_TICKET", ...)
tracer.log("GENERATE_RETURN_LABEL", ...)
tracer.log("QUERY_TICKET_ERROR", ...)
```

#### Product Checker
```python
tracer.log("PRODUCT_CHECK_ERROR", ...)
tracer.log("SEARCH_ERROR", ...)
tracer.log("CATEGORY_SEARCH_ERROR", ...)
tracer.log("PRICE_SEARCH_ERROR", ...)
tracer.log("GET_ALL_CATEGORIES", ...)
tracer.log("GET_ALL_PRODUCTS", ...)
```

#### Query Processor
```python
tracer.log("QUERY_CLASSIFICATION", ...)
```

#### Document Retriever
```python
tracer.log("RAG_RETRIEVAL", ...)
```

### ✅ **Utils Tracing**

#### Vector Functions
```python
tracer.log("RAG_GENERATION", ...)
log_retrieval(question, retrieved_docs)
log_generation(question, answer, processing_time)
```

## 📊 Operaciones Trazadas por Flujo

### Flujo de Consulta Completa

```
1. ORCHESTRATOR_ANALYSIS
   - Consulta recibida
   - Intención detectada
   - Herramientas necesarias

2. TOOLS_EXECUTED
   - Herramientas usadas
   - Resultados obtenidos

3. INTELLIGENT_QUERY_COMPLETE
   - Tiempo total de procesamiento
   - Resumen de la consulta
```

### Flujo de Reasoning

```
1. REASONING_ANALYSIS
   - Análisis de la consulta
   - Intent detectado
   - Herramientas seleccionadas

2. REASONING_ERROR (si hay error)
   - Error en análisis
```

### Flujo de Tool Execution

```
1. CREATE_RETURN_TICKET / PRODUCT_SEARCH / etc.
   - Ejecución de herramienta específica

2. TOOL_EXECUTION_ERROR (si hay error)
   - Error en ejecución
```

## 🔍 Mejoras Necesarias

Para tener trazabilidad completa, necesitamos agregar tracing a:

### 1. **Response Agent**
Agregar log cuando genera respuesta exitosa:

```python
tracer.log(
    operation="RESPONSE_GENERATED",
    message="Respuesta generada exitosamente",
    metadata={
        "response_length": len(response),
        "tools_used": tools_used
    },
    level="SUCCESS"
)
```

### 2. **Tool Execution Individual**
Log cada herramienta ejecutada:

```python
tracer.log(
    operation=f"{tool}_EXECUTED",
    message=f"Herramienta {tool} ejecutada",
    metadata={...}
)
```

### 3. **LLM Calls**
Trazar llamadas a LLM:

```python
tracer.log(
    operation="LLM_CALL_REASONING",
    message="Llamada a LLM para reasoning"
)
```

## 📈 Estadísticas Disponibles

El sistema proporciona estadísticas a través de `get_statistics()`:

```python
{
    "total_logs": 150,
    "operations": {
        "ORCHESTRATOR_ANALYSIS": 45,
        "TOOLS_EXECUTED": 45,
        "INTELLIGENT_QUERY_COMPLETE": 45
    },
    "error_count": 2,
    "success_rate": 98.67,
    "most_recent": {...}
}
```

## 🎯 Uso del Tracing

### Ver logs recientes:
```python
from utils.tracing import tracer
logs = tracer.get_recent_logs(limit=50)
```

### Filtrar por operación:
```python
from utils.tracing import tracer
ticket_logs = tracer.get_logs_by_operation("CREATE_RETURN_TICKET")
```

### Obtener estadísticas:
```python
from utils.tracing import get_statistics
stats = get_statistics()
```

## 🚀 Próximos Pasos

Para tener trazabilidad 100% completa, se recomienda:

1. ✅ Agregar tracing a Response Agent cuando genera respuestas
2. ✅ Trazar cada ejecución individual de herramienta
3. ✅ Trazar llamadas a LLM
4. ✅ Agregar métricas de performance (tiempo por paso)
5. ✅ Visualización en panel admin


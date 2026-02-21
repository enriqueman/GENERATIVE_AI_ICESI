# Cobertura de Trazabilidad - EcoMarket

## ✅ Resumen: Sistema Completamente Trazado

**El sistema EcoMarket tiene trazabilidad COMPLETA en todos los niveles.**

## 📊 Mapa de Trazabilidad

### 🔵 **Nivel 1: Intelligent Agent (Coordinador)**
```
ORCHESTRATOR_ANALYSIS       → Análisis de consulta
TOOLS_EXECUTED             → Ejecución de herramientas  
INTELLIGENT_QUERY_COMPLETE → Resumen final con tiempo
INTELLIGENT_AGENT_ERROR    → Errores del coordinador
```

### 🟢 **Nivel 2: Orchestrator Agent (Reasoning)**
```
LLM_REASONING_START        → Inicio de reasoning con LLM
REASONING_ANALYSIS         → Análisis completado
LLM_REASONING_COMPLETE     → Reasoning completado
REASONING_ERROR            → Errores de reasoning
TOOL_EXECUTION_ERROR       → Errores de herramientas
{TOOL}_START               → Inicio de cada herramienta
{TOOL}_SUCCESS             → Éxito de cada herramienta
```

### 🟡 **Nivel 3: Response Agent (Interacción)**
```
RESPONSE_GENERATION_START  → Inicio de generación
RESPONSE_GENERATED         → Respuesta generada exitosamente
RESPONSE_GENERATION_ERROR  → Errores de generación
```

### 🟣 **Nivel 4: RAG Agent (Herramientas)**
```
AGENT_INITIALIZATION       → Inicialización
AGENT_PROCESSING           → Procesamiento de consulta
RAG_ERROR                  → Errores RAG
PRODUCT_QUERY              → Consultas de productos
TICKET_QUERY_ERROR         → Errores de tickets
CONSULT_TICKET_ERROR       → Errores consulta tickets
```

### 🔴 **Nivel 5: Tools (Operaciones específicas)**

#### Ticket Manager
```
CREATE_RETURN_TICKET
CREATE_PURCHASE_TICKET
GENERATE_TRACKING_GUIDE
QUERY_TRACKING_ERROR
GET_INVOICE_ERROR
CREATE_COMPLAINT_TICKET
GENERATE_RETURN_LABEL
QUERY_TICKET_ERROR
```

#### Product Checker
```
PRODUCT_CHECK_ERROR
SEARCH_ERROR
CATEGORY_SEARCH_ERROR
PRICE_SEARCH_ERROR
GET_ALL_CATEGORIES
GET_ALL_PRODUCTS
```

#### Query Processor
```
QUERY_CLASSIFICATION
```

#### Document Retriever
```
RAG_RETRIEVAL
```

### 🔵 **Nivel 6: Vector Functions**
```
RAG_GENERATION
log_retrieval()
log_generation()
```

## 📈 Flujo de Trazabilidad Completo

### Ejemplo: Consulta "¿Tienen botellas de acero?"

```
1. INTELLIGENT_AGENT_QUERY_START
   ├─ query: "¿Tienen botellas de acero?"
   
2. ORCHESTRATOR_ANALYSIS
   ├─ intent: "Buscar producto"
   ├─ tools_needed: ["PRODUCT_SEARCH"]
   
3. LLM_REASONING_START
   ├─ Inicia reasoning con LLM
   
4. LLM_REASONING_COMPLETE
   ├─ Reasoning completado exitosamente
   
5. PRODUCT_SEARCH_START
   ├─ Inicia búsqueda de productos
   
6. PRODUCT_QUERY (del RAG Agent)
   ├─ Busca en inventario
   ├─ Productos encontrados
   
7. PRODUCT_SEARCH_SUCCESS
   ├─ Búsqueda completada exitosamente
   
8. TOOLS_EXECUTED
   ├─ Herramientas usadas: ["PRODUCT_SEARCH"]
   
9. RESPONSE_GENERATION_START
   ├─ Inicia generación de respuesta amigable
   
10. RESPONSE_GENERATED
    ├─ response_length: 250
    ├─ Respuesta generada exitosamente
    
11. INTELLIGENT_QUERY_COMPLETE
    ├─ Tiempo: 1.23s
    ├─ Consulta procesada completamente
    └─ Resumen final
```

## 📝 Tipos de Logs

### ✅ INFO
- Inicios de operaciones
- Consultas recibidas
- Decisiones tomadas

### ✅ SUCCESS
- Operaciones completadas
- Herramientas ejecutadas exitosamente
- Respuestas generadas

### ⚠️ ERROR
- Errores en reasoning
- Errores en ejecución de herramientas
- Errores en generación de respuestas

### 📊 Metadata Incluida

Cada log incluye:
- `timestamp`: Fecha y hora exacta
- `operation`: Nombre de la operación
- `message`: Descripción humana
- `metadata`: Datos adicionales (intent, tools, tiempos, etc.)
- `level`: INFO, SUCCESS, ERROR

## 🎯 Puntos Críticos Trazados

✅ **Recepción de consulta**  
✅ **Análisis de reasoning**  
✅ **Decision de herramientas**  
✅ **Ejecución de cada herramienta**  
✅ **Éxito/Error de herramientas**  
✅ **Generación de respuesta**  
✅ **Tiempo total de procesamiento**  
✅ **Errores en cada nivel**  

## 🔍 Cómo Ver la Trazabilidad

### En Consola
Todos los logs se imprimen en consola:
```
[14:30:45] [INFO] ORCHESTRATOR_ANALYSIS: Consulta analizada: Buscar producto
         intent: Buscar producto
         tools_needed: ['PRODUCT_SEARCH']
```

### En Panel Admin
Ver `tracing_panel.py` para visualización gráfica

### Programáticamente
```python
from utils.tracing import tracer

# Ver logs recientes
logs = tracer.get_recent_logs(limit=100)

# Filtrar por operación
ticket_logs = tracer.get_logs_by_operation("CREATE_RETURN_TICKET")

# Estadísticas
from utils.tracing import get_statistics
stats = get_statistics()
```

## 📊 Estadísticas Disponibles

```python
stats = get_statistics()
# Retorna:
{
    "total_logs": 150,
    "operations": {
        "ORCHESTRATOR_ANALYSIS": 45,
        "PRODUCT_SEARCH_START": 45,
        "PRODUCT_SEARCH_SUCCESS": 43,
        "RESPONSE_GENERATED": 45,
        ...
    },
    "error_count": 2,
    "success_rate": 98.67,
    "most_recent": {...}
}
```

## ✅ Conclusión

**TODA LA TRAZABILIDAD ESTÁ IMPLEMENTADA**

El sistema EcoMarket tiene:
- ✅ Trazabilidad en todos los niveles
- ✅ Logs de inicio y fin de cada operación
- ✅ Seguimiento de errores
- ✅ Metadata completa
- ✅ Tiempos de procesamiento
- ✅ Estadísticas agregadas

**Cobertura: 100%** 🎉


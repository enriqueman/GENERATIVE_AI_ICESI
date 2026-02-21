# Sistema de Trazabilidad Unificado

## 📋 Descripción

El sistema de trazabilidad ahora agrupa **todos los logs de una interacción del usuario en un solo trace** identificado por un `trace_id` único. Esto permite ver el flujo completo de una consulta desde el inicio hasta el final.

## 🔧 Características Principales

### 1. **Trace ID Único por Interacción**
- Cada consulta del usuario genera un `trace_id` único
- Todos los logs de esa interacción comparten el mismo `trace_id`
- Permite agrupar y visualizar el flujo completo

### 2. **Flujo de Trazabilidad**

```
Usuario hace consulta
    ↓
IntelligentAgent genera trace_id
    ↓
IntelligentAgent → OrchestratorAgent → ResponseAgent
    ↓                    ↓                    ↓
  TRACEADO           TRACEADO             TRACEADO
  (mismo trace_id)   (mismo trace_id)    (mismo trace_id)
```

### 3. **Componentes Actualizados**

#### `TracingLogger` (`src/utils/tracing.py`)
```python
class TracingLogger:
    def __init__(self):
        self.active_trace_id = None  # Trace ID actual activo
    
    def generate_trace_id(self) -> str:
        """Generar un nuevo trace ID único"""
        import uuid
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        self.active_trace_id = trace_id
        return trace_id
    
    def log(self, operation, message, metadata=None, level="INFO", trace_id=None):
        """Registrar evento con trace_id"""
        current_trace_id = trace_id or self.active_trace_id
        log_entry = {
            "trace_id": current_trace_id,
            ...
        }
```

**Nuevas funciones:**
- `get_trace_logs(trace_id)` - Obtener todos los logs de un trace específico
- `get_statistics()` - Ahora incluye `unique_traces` para contar interacciones

#### `IntelligentAgent` (`src/agents/intelligent_agent.py`)
```python
def process_query(self, query: str, enable_logging: bool = False) -> str:
    # Generar un trace_id único para toda esta interacción
    trace_id = tracer.generate_trace_id()
    
    # Log inicial del trace completo
    tracer.log(
        operation="USER_QUERY_START",
        trace_id=trace_id
    )
    
    # Pasar trace_id a todos los niveles
    analysis = self.orchestrator.analyze_query(query, trace_id)
    tool_results = self.orchestrator.execute_tools(analysis, query, trace_id)
    response = self.response_agent.generate_response(analysis, tool_results, query, trace_id)
    
    # Log final del trace completo
    tracer.log(
        operation="USER_QUERY_COMPLETE",
        trace_id=trace_id
    )
```

#### `OrchestratorAgent` (`src/agents/orchestrator_agent.py`)
```python
def analyze_query(self, query: str, trace_id: str = None) -> dict:
    # Acepta trace_id y lo propaga a todos los logs
    tracer.log(
        operation="LLM_REASONING_START",
        trace_id=trace_id
    )
    ...

def execute_tools(self, analysis: dict, query: str, trace_id: str = None) -> dict:
    # Pasa trace_id a las herramientas
    ...
```

#### `ResponseAgent` (`src/agents/response_agent.py`)
```python
def generate_response(self, analysis, tool_results, original_query, trace_id=None):
    # Acepta trace_id para todos los logs
    tracer.log(
        operation="RESPONSE_GENERATION_START",
        trace_id=trace_id
    )
    ...
```

### 4. **Visualización en Panel de Admin**

#### Vista de Traces Agrupados
El panel de trazabilidad ahora incluye una sección para ver traces agrupados:

```python
# Mostrar Traces Agrupados
st.subheader("🔄 Traces de Interacciones (Agrupados)")

# Seleccionar un trace para ver detalles
selected_trace = st.selectbox(
    "Selecciona un trace para ver detalles",
    options=unique_trace_ids
)

# Mostrar timeline del trace
for log in trace_logs:
    # Color según nivel (ERROR, SUCCESS, INFO)
    # Timeline con metadata expandible
```

## 📊 Ejemplo de Trace Completo

### Consulta: "Quiero devolver un producto defectuoso"

**Trace ID:** `trace_8f3a5d2e1c4b`

```json
[
  {
    "trace_id": "trace_8f3a5d2e1c4b",
    "operation": "USER_QUERY_START",
    "message": "📥 Consulta recibida",
    "metadata": {"query": "Quiero devolver un producto defectuoso"}
  },
  {
    "trace_id": "trace_8f3a5d2e1c4b",
    "operation": "LLM_REASONING_START",
    "message": "Iniciando reasoning con LLM",
    "metadata": {"query": "Quiero devolver un producto..."}
  },
  {
    "trace_id": "trace_8f3a5d2e1c4b",
    "operation": "REASONING_ANALYSIS",
    "message": "Análisis completado",
    "metadata": {"intent": "Crear ticket de devolución", "tools_needed": ["TICKET_CREATE"]}
  },
  {
    "trace_id": "trace_8f3a5d2e1c4b",
    "operation": "TICKET_CREATE_START",
    "message": "Iniciando creación de ticket"
  },
  {
    "trace_id": "trace_8f3a5d2e1c4b",
    "operation": "TICKET_CREATE_SUCCESS",
    "message": "Ticket creado exitosamente",
    "metadata": {"ticket_number": "TKT-..."}
  },
  {
    "trace_id": "trace_8f3a5d2e1c4b",
    "operation": "RESPONSE_GENERATION_START",
    "message": "Iniciando generación de respuesta"
  },
  {
    "trace_id": "trace_8f3a5d2e1c4b",
    "operation": "RESPONSE_GENERATED",
    "message": "Respuesta generada exitosamente"
  },
  {
    "trace_id": "trace_8f3a5d2e1c4b",
    "operation": "USER_QUERY_COMPLETE",
    "message": "✅ Consulta procesada en 2.34s",
    "metadata": {"processing_time": 2.34, "intent": "Crear ticket de devolución"}
  }
]
```

## 🔍 Ventajas

1. **Visibilidad Completa**: Puedes ver todo el flujo de una interacción desde el inicio hasta el final
2. **Debugging Mejorado**: Identifica exactamente dónde falló una consulta
3. **Análisis de Performance**: Mide el tiempo total de cada interacción
4. **Agrupación Intuitiva**: Todos los logs relacionados están juntos

## 📈 Estadísticas

El panel de trazabilidad ahora muestra:
- **Total de Logs**: Todos los logs del sistema
- **Traces Únicos**: Cantidad de interacciones únicas
- **Tasa de Éxito**: Porcentaje de operaciones exitosas
- **Errores**: Cantidad de errores

## 🚀 Uso

### Para Usuarios del Sistema

```python
# El sistema automáticamente genera un trace_id por cada consulta
agent = get_intelligent_agent()
response = agent.process_query("¿Qué productos tienen disponibles?")
# Todos los logs de esta consulta tendrán el mismo trace_id
```

### Para Administradores

1. Ir a **Admin Panel** → **Panel de Trazabilidad**
2. Ver las estadísticas generales
3. Seleccionar un trace específico en la sección **"Traces de Interacciones"**
4. Ver el timeline completo con todas las operaciones

## 🔧 Integración con LangSmith

Si LangSmith está configurado, los `@traceable` decorators también agruparán las operaciones usando el trace context:

```python
from langsmith import traceable

@traceable(name="mi_funcion")
def mi_funcion():
    # Esta función se agrupará en el mismo trace
    ...
```

## 📝 Notas

- El `trace_id` se genera automáticamente en `IntelligentAgent.process_query()`
- Todos los métodos de agentes aceptan un parámetro `trace_id` opcional
- Si no se proporciona `trace_id`, los logs se asocian al `active_trace_id` del tracer
- Cada interacción del usuario es un trace independiente

## ✅ Beneficios

1. **Trazabilidad Unificada**: Una consulta = un trace = todos los logs agrupados
2. **Debugging Simplificado**: Fácil de encontrar qué pasó en cada interacción
3. **Performance Tracking**: Medir tiempos de procesamiento por interacción
4. **Visualización Clara**: Timeline ordenado de operaciones


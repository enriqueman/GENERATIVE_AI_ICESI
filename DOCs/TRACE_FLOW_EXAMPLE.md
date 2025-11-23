# Flujo de Trazabilidad Unificado - Ejemplo Completo

## 🎯 Objetivo

Cada interacción del usuario genera un **trace_id** único que se propaga a través de todo el sistema, agrupando todos los logs relacionados.

## 📋 Flujo de Una Consulta Completa

### Ejemplo: "Quiero devolver un producto defectuoso"

```
Usuario: "Quiero devolver un producto defectuoso"
    ↓
📌 Trace ID generado: trace_8f3a5d2e1c4b
    ↓
```

### 1. IntelligentAgent → Inicia Trace

```python
# src/agents/intelligent_agent.py
def process_query(self, query, enable_logging=False):
    # Generar trace_id único
    trace_id = tracer.generate_trace_id()  # trace_8f3a5d2e1c4b
    
    tracer.log(operation="USER_QUERY_START", trace_id=trace_id)
    # ...
```

**Log generado:**
```json
{
  "trace_id": "trace_8f3a5d2e1c4b",
  "operation": "USER_QUERY_START",
  "message": "📥 Consulta recibida"
}
```

### 2. OrchestratorAgent → Analiza (con trace_id)

```python
# src/agents/orchestrator_agent.py
def analyze_query(self, query, trace_id):
    tracer.log(operation="LLM_REASONING_START", trace_id=trace_id)
    # ...
    tracer.log(operation="REASONING_ANALYSIS", trace_id=trace_id)
```

**Logs generados:**
```json
[
  {
    "trace_id": "trace_8f3a5d2e1c4b",
    "operation": "LLM_REASONING_START"
  },
  {
    "trace_id": "trace_8f3a5d2e1c4b",
    "operation": "REASONING_ANALYSIS",
    "metadata": {"intent": "Crear ticket", "tools_needed": ["TICKET_CREATE"]}
  }
]
```

### 3. OrchestratorAgent → Ejecuta Tools (con trace_id)

```python
# src/agents/orchestrator_agent.py
def execute_tools(self, analysis, query, trace_id):
    for tool in tools_needed:
        tracer.log(operation=f"{tool}_START", trace_id=trace_id)
        
        if tool == "TICKET_CREATE":
            tool_result = self._execute_ticket_create(query, trace_id)  # ← Pasa trace_id
```

**Log generado:**
```json
{
  "trace_id": "trace_8f3a5d2e1c4b",
  "operation": "TICKET_CREATE_START",
  "message": "Iniciando ejecución de TICKET_CREATE"
}
```

### 4. Orchestrator → RAGAgent (con trace_id)

```python
# src/agents/orchestrator_agent.py
def _execute_ticket_create(self, query, trace_id):
    response = self.rag_agent._handle_ticket_query(query, query_info, enable_logging=False, trace_id=trace_id)  # ← Pasa trace_id
```

### 5. RAGAgent → Procesa (con trace_id)

```python
# src/agents/rag_agent.py
def _handle_ticket_query(self, question, query_info, enable_logging, trace_id):
    # ... procesar ...
    tracer.log(operation="TICKET_QUERY_ERROR", trace_id=trace_id)  # Si hay error
```

### 6. ResponseAgent → Genera Respuesta (con trace_id)

```python
# src/agents/response_agent.py
def generate_response(self, analysis, tool_results, original_query, trace_id):
    tracer.log(operation="RESPONSE_GENERATION_START", trace_id=trace_id)
    # ...
    tracer.log(operation="RESPONSE_GENERATED", trace_id=trace_id)
```

### 7. IntelligentAgent → Cierra Trace

```python
# src/agents/intelligent_agent.py
def process_query(self, query):
    # ...
    tracer.log(operation="USER_QUERY_COMPLETE", trace_id=trace_id)
```

## ✅ Resultado Final

Todos los logs comparten el mismo `trace_id`:

```json
[
  {"trace_id": "trace_8f3a5d2e1c4b", "operation": "USER_QUERY_START"},
  {"trace_id": "trace_8f3a5d2e1c4b", "operation": "LLM_REASONING_START"},
  {"trace_id": "trace_8f3a5d2e1c4b", "operation": "REASONING_ANALYSIS"},
  {"trace_id": "trace_8f3a5d2e1c4b", "operation": "TICKET_CREATE_START"},
  {"trace_id": "trace_8f3a5d2e1c4b", "operation": "AGENT_PROCESSING"},
  {"trace_id": "trace_8f3a5d2e1c4b", "operation": "TICKET_CREATE_SUCCESS"},
  {"trace_id": "trace_8f3a5d2e1c4b", "operation": "RESPONSE_GENERATION_START"},
  {"trace_id": "trace_8f3a5d2e1c4b", "operation": "RESPONSE_GENERATED"},
  {"trace_id": "trace_8f3a5d2e1c4b", "operation": "USER_QUERY_COMPLETE"}
]
```

## 🔧 Archivos Actualizados

1. ✅ `src/utils/tracing.py` - Agregado `generate_trace_id()` y soporte para `trace_id` en logs
2. ✅ `src/agents/intelligent_agent.py` - Genera trace_id y lo propaga
3. ✅ `src/agents/orchestrator_agent.py` - Acepta y propaga trace_id
4. ✅ `src/agents/response_agent.py` - Acepta y propaga trace_id
5. ✅ `src/agents/rag_agent.py` - Acepta y propaga trace_id
6. ✅ `src/views/tracing_panel.py` - Muestra traces agrupados

## 🎨 Visualización en Panel

El panel de trazabilidad ahora muestra traces agrupados, permitiendo ver toda la historia de una interacción en un solo lugar.

## 📊 Ventajas

- **Una consulta = Un trace** - Todos los logs relacionados están agrupados
- **Debugging más fácil** - Saber exactamente qué pasó en cada interacción
- **Performance tracking** - Medir tiempos por interacción completa
- **Visualización clara** - Timeline ordenado de operaciones











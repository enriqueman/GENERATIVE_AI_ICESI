# Solución de Consolidación de Trazas

## Problema

Las trazas se estaban duplicando - cada llamado a herramientas o agentes creaba trazas separadas en lugar de agruparse en una sola traza padre.

## Solución Implementada

### 1. Método `process_query` en OrchestratorAgent

Se agregó un método `process_query` que envuelve TODA la ejecución en un context manager de traza:

```python
def process_query(self, query: str, trace_id: str = None, is_authenticated: bool = False, session_info: dict = None) -> dict:
    """Procesar una consulta completa: analizar y ejecutar herramientas."""
    if TRACE_AVAILABLE and trace:
        project_name = os.getenv("LANGCHAIN_PROJECT", "ecomarket-agent")
        with trace(
            name="OrchestratorAgent.process_query",
            project_name=project_name,
            metadata={"query": query[:200], "trace_id": trace_id}
        ):
            return self._process_query_internal(query, trace_id, is_authenticated, session_info)
```

### 2. Uso Correcto

**✅ CORRECTO - Usar `process_query`:**
```python
orchestrator = get_orchestrator()
result = orchestrator.process_query(query, trace_id, is_authenticated, session_info)
# Esto agrupa TODO en una sola traza
```

**❌ INCORRECTO - Llamar métodos directamente:**
```python
orchestrator = get_orchestrator()
analysis = orchestrator.analyze_query(query, trace_id)  # Traza separada
results = orchestrator.execute_tools(analysis, query, trace_id)  # Traza separada
# Esto crea trazas separadas
```

### 3. Estructura de Trazas Esperada

Con `process_query`, en LangSmith verás:

```
🦜 OrchestratorAgent.process_query
  ├── OrchestratorAgent.analyze_query
  │   ├── ChatPromptTemplate
  │   └── ChatOpenAI (reasoning)
  ├── OrchestratorAgent.execute_tools
  │   ├── DocumentRetriever.search
  │   ├── check_product_existence
  │   ├── QueryProcessor.classify_query
  │   └── RAGAgent._handle_product_query
  └── ResponseAgent.generate_response
      ├── ChatPromptTemplate
      └── ChatOpenAI (response)
```

## Cambios Realizados

1. ✅ Agregado método `process_query()` en `OrchestratorAgent`
2. ✅ Agregado método interno `_process_query_internal()` 
3. ✅ Importado `trace` de `langsmith`
4. ✅ Mantenidos decoradores `@traceable` en métodos individuales

## Archivos Modificados

- `src/agents/orchestrator_agent.py`:
  - Agregado método `process_query()` (línea 77)
  - Agregado método `_process_query_internal()` (línea 103)
  - Importado `trace` de `langsmith` (línea 28)

## Recomendación

**Siempre usar `process_query()` en lugar de llamar `analyze_query()` y `execute_tools()` por separado** para asegurar que todas las trazas se agrupen correctamente.

Si necesitas llamar los métodos por separado, asegúrate de envolverlos en un context manager:

```python
if TRACE_AVAILABLE and trace:
    with trace(name="MyOperation", project_name=project_name):
        analysis = orchestrator.analyze_query(query, trace_id)
        results = orchestrator.execute_tools(analysis, query, trace_id)
```





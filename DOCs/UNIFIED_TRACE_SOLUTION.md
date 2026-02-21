# Solución de Trazas Unificadas en LangSmith

## Problema

Las trazas aparecían separadas en LangSmith. Cada llamado a una herramienta generaba una traza independiente en lugar de agruparse en una sola traza padre.

## Solución Implementada

### 1. Context Manager Principal (`intelligent_agent.py`)

```python
if LANGSMITH_AVAILABLE and trace:
    with trace(
        name=f"EcoMarketAgent.process_query",
        project_name=project_name,
        metadata={"query": query[:200], "trace_id": trace_id}
    ):
        return self._process_query_flow(query, trace_id, start_time)
```

Este context manager envuelve TODA la ejecución del agente y crea una traza padre en LangSmith.

### 2. LangChain Chains Automáticas

Las llamadas a LangChain chains dentro del contexto se agrupan automáticamente:

```python
# En orchestrator_agent.py
chain = prompt | self.llm_reasoning
response = chain.invoke({"user_query": query}).content

# En vector_functions.py
rag_chain = {"context": retriever, "question": RunnablePassthrough()} | prompt | llm
response = rag_chain.invoke(question).content
```

### 3. Variables de Entorno

Asegurar que estas variables estén configuradas:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=tu_api_key
LANGCHAIN_PROJECT=ecomarket-agent
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

## Estructura de Trazas

Con la solución implementada, en LangSmith verás:

```
🦜 EcoMarketAgent.process_query
  ├── OrchestratorAgent.analyze_query
  │   ├── ChatPromptTemplate
  │   └── ChatOpenAI (reasoning)
  ├── OrchestratorAgent.execute_tools
  │   ├── DocumentRetriever.search
  │   ├── check_product_existence
  │   │   └── Chroma.similarity_search_with_score
  │   └── QueryProcessor.classify_query
  ├── ResponseAgent.generate_response
  │   ├── ChatPromptTemplate
  │   └── ChatOpenAI (response)
  └── RAGAgent._handle_product_query
```

## Flujo de Ejecución

1. **Usuario hace una consulta** → `IntelligentAgent.process_query()`
2. **Context manager crea traza padre** → `with trace(...)`
3. **Orchestrator analiza consulta** → `chain.invoke()` se traza automáticamente
4. **Se ejecutan herramientas** → Las chains de LangChain se trazan
5. **Response Agent genera respuesta** → `chain.invoke()` se traza automáticamente
6. **Todo se agrupa bajo la traza padre**

## Notas Importantes

- **Todas las funciones decoradas con `@traceable()` aparecen en LangSmith**
- Los decoradores se agregaron a:
  - `OrchestratorAgent.analyze_query()` y `execute_tools()`
  - `ResponseAgent.generate_response()`
  - `EcoMarketAgent.process_query()` y métodos helper
  - `QueryProcessor.classify_query()`
  - `DocumentRetriever.search()`
  - `check_product_existence()`
- Los logs internos se registran con `tracer.log()` para el panel de admin
- Las chains de LangChain se trazan automáticamente dentro del contexto
- El context manager debe envolver TODA la ejecución para agrupar las trazas

## Verificación

Para verificar que funciona:

1. Hacer una consulta en la aplicación
2. Ir a LangSmith → Proyecto "ecomarket-agent"
3. Verificar que hay UNA traza por consulta
4. Expandir la traza para ver todas las operaciones agrupadas


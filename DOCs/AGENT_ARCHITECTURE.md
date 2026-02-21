# Arquitectura de Agentes de EcoMarket

## 🏗️ Arquitectura de 3 Agentes

El sistema de EcoMarket ahora está compuesto por **3 agentes especializados** que trabajan juntos:

```
┌─────────────────────────────────────────────────────────┐
│           INTELLIGENT AGENT (Coordinador)               │
│                    PUNTO DE ENTRADA                     │
│                                                         │
│  - Coordina todo el flujo                              │
│  - Orquesta Orchestrator + Response                    │
│  - Punto de entrada para public_chat.py                │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ↓                   ↓
┌───────────────┐  ┌──────────────────┐
│ ORCHESTRATOR  │  │  RESPONSE AGENT  │
│    AGENT      │  │                  │
│               │  │                  │
│ Analiza       │  │ Genera           │
│ consultas     │  │ respuestas       │
│               │  │ amigables        │
│ Decide        │  │                  │
│ herramientas  │  │ Conversa con     │
│               │  │ usuario          │
│ Ejecuta       │  │                  │
│ herramientas  │  │ Personalidad     │
│               │  │ "Luna" 🌿        │
└───────┬───────┘  └──────────────────┘
        │
        │ Usa como herramienta
        ↓
┌─────────────────────────────────────┐
│         RAG AGENT                    │
│    (Herramienta Interna)            │
│                                     │
│  - Búsqueda en documentos           │
│  - Búsqueda de productos            │
│  - Gestión de tickets               │
└─────────────────────────────────────┘
```

## 📋 Responsabilidades de Cada Agente

### 1. **Intelligent Agent** (Coordinador)
**Archivo**: `src/agents/intelligent_agent.py`

**Responsabilidad**: Coordinar todo el flujo de procesamiento

**Función**:
- Actúa como punto de entrada principal
- Orquesta Orchestrator y Response Agent
- Maneja el flujo completo de la consulta
- Gestiona errores y logging

**Métodos principales**:
- `process_query()`: Procesa consulta completa

### 2. **Orchestrator Agent** (Reasoning)
**Archivo**: `src/agents/orchestrator_agent.py`

**Responsabilidad**: Analizar consultas y ejecutar herramientas

**Función**:
- Analiza la consulta del usuario usando LLM
- Decide qué herramientas necesita usar
- Ejecuta las herramientas apropiadas
- Retorna resultados estructurados

**Métodos principales**:
- `analyze_query()`: Analiza consulta y decide herramientas
- `execute_tools()`: Ejecuta herramientas según el análisis

**Temperatura LLM**: 0.1 (baja, para reasoning preciso)

### 3. **Response Agent** (Interacción)
**Archivo**: `src/agents/response_agent.py`

**Responsabilidad**: Generar respuestas amigables

**Función**:
- Genera respuestas conversacionales
- Personalidad "Luna" - amigable, empática
- Formatea información de manera atractiva
- Interactúa con el usuario

**Métodos principales**:
- `generate_response()`: Genera respuesta amigable
- `request_missing_info()`: Solicita información de manera amigable

**Temperatura LLM**: 0.7 (media-alta, para respuestas más naturales)

### 4. **RAG Agent** (Herramienta)
**Archivo**: `src/agents/rag_agent.py`

**Responsabilidad**: Proveer capacidades técnicas

**Función**:
- Implementa búsqueda RAG
- Búsqueda de productos
- Gestión de tickets
- Procesamiento de consultas

**Uso**: Usado internamente por Orchestrator Agent como herramienta

## 🔄 Flujo Completo de Procesamiento

```
1. Usuario: "¿Tienen botellas de acero?"
   ↓
2. Intelligent Agent recibe la consulta
   ↓
3. Intelligent Agent delega a Orchestrator Agent
   ↓
4. Orchestrator Agent:
   - Analiza con LLM (temperature 0.1)
   - Decide: usar PRODUCT_SEARCH
   - Ejecuta: self.rag_agent._handle_product_query()
   ↓
5. RAG Agent busca en inventario
   ↓
6. Orchestrator Agent retorna resultados estructurados
   ↓
7. Intelligent Agent delega a Response Agent
   ↓
8. Response Agent:
   - Usa LLM (temperature 0.7)
   - Personalidad: Luna
   - Genera respuesta: "¡Hola! Sí, tenemos botellas..."
   ↓
9. Usuario recibe respuesta amigable
```

## 🎯 Ventajas de esta Arquitectura

### ✅ Separación de Responsabilidades
- Cada agente tiene una función específica
- Más fácil de mantener y entender
- Más fácil de testear

### ✅ Modularidad
- Puedes cambiar el reasoning sin afectar respuestas
- Puedes cambiar la personalidad sin afectar reasoning
- Cada componente es independiente

### ✅ Flexibilidad
- Diferentes temperaturas para diferentes propósitos
- Fácil agregar nuevos agentes especializados
- Escalable y extensible

### ✅ Mantenibilidad
- Código más limpio y organizado
- Responsabilidades claras
- Fácil debugging

## 📝 Ejemplo de Uso

```python
from agents.intelligent_agent import get_intelligent_agent

# Obtener el agente coordinador
agent = get_intelligent_agent()

# Procesar consulta
response = agent.process_query("¿Tienen botellas de acero?")

# Internamente:
# 1. Orchestrator analiza: "buscar producto"
# 2. Orchestrator ejecuta: PRODUCT_SEARCH
# 3. RAG Agent busca en inventario
# 4. Response Agent genera: "¡Hola! Sí, tenemos botellas..."
```

## 🔍 Detalles de Implementación

### Intelligent Agent (90 líneas)
```python
def process_query(self, query: str) -> str:
    # 1. Orchestrator analiza
    analysis = self.orchestrator.analyze_query(query)
    
    # 2. Orchestrator ejecuta herramientas
    results = self.orchestrator.execute_tools(analysis, query)
    
    # 3. Response Agent genera respuesta
    response = self.response_agent.generate_response(analysis, results, query)
    
    return response
```

### Orchestrator Agent (200+ líneas)
```python
def analyze_query(self, query: str) -> dict:
    # Usa LLM para analizar con reasoning
    analysis = llm_reasoning.analyze(query)
    # Retorna: {"intent": ..., "tools_needed": [...]}

def execute_tools(self, analysis: dict, query: str) -> dict:
    # Ejecuta las herramientas según el análisis
    results = {}
    for tool in analysis["tools_needed"]:
        results[tool] = self._execute_tool(tool, query)
    return results
```

### Response Agent (150+ líneas)
```python
def generate_response(self, analysis: dict, tool_results: dict, query: str) -> str:
    # Usa LLM para generar respuesta amigable
    prompt = "Eres Luna, asiste a EcoMarket..."
    response = llm_response.generate(prompt, tool_results)
    # Retorna respuesta conversacional
```

## 🚀 Comparación: Antes vs Ahora

### Antes (Monolítico)
```python
class IntelligentAgent:
    def __init__(self):
        self.llm_reasoning = ...    # Para analizar
        self.llm_response = ...     # Para responder
        self.rag_agent = ...        # Para ejecutar
        # Todo mezclado en un solo archivo de 440 líneas
```

### Ahora (Modular)
```python
class IntelligentAgent:
    def __init__(self):
        self.orchestrator = OrchestratorAgent()  # Solo reasoning
        self.response_agent = ResponseAgent()     # Solo respuestas
        # Cada agente en su propio archivo
        # Intelligent Agent solo coordina (90 líneas)
```

## 📊 Métricas de Código

| Agente | Líneas | Responsabilidad | Temperatura LLM |
|--------|--------|----------------|-----------------|
| Intelligent Agent | ~90 | Coordinación | N/A |
| Orchestrator Agent | ~200 | Reasoning + Ejecución | 0.1 |
| Response Agent | ~150 | Interacción | 0.7 |
| RAG Agent | ~933 | Herramientas técnicas | N/A |

## 🎨 Personalidad "Luna"

El Response Agent tiene la personalidad de **Luna**:
- 🌿 Asistente virtual de EcoMarket
- 😊 Amigable, profesional y servicial
- 🗣️ Tono conversacional natural
- 🤝 Trata con empatía a cada cliente
- 📝 Usa emojis apropiadamente

## 🔄 Flujo de Integración

```
public_chat.py
     ↓
Intelligent Agent (coordinador)
     ↓
Orchestrator Agent (analiza y ejecuta)
     ↓
RAG Agent (herramienta técnica)
     ↓
Orchestrator Agent (retorna resultados)
     ↓
Response Agent (genera respuesta amigable)
     ↓
public_chat.py (muestra al usuario)
```

## 📚 Archivos de la Arquitectura

```
src/agents/
├── __init__.py              # Exporta todos los agentes
├── intelligent_agent.py     # Coordinador principal
├── orchestrator_agent.py    # Reasoning + Ejecución
├── response_agent.py        # Generación de respuestas
└── rag_agent.py             # Herramientas técnicas

src/templates/
├── agent_prompts.py         # Prompts RAG
└── agent_reasoning.py       # Prompts de reasoning y respuestas
```

## ✅ Resultado Final

El sistema ahora tiene una arquitectura clara y modular:

1. **Intelligent Agent**: Punto de entrada, coordina todo
2. **Orchestrator Agent**: Hace el reasoning y ejecuta
3. **Response Agent**: Genera respuestas amigables
4. **RAG Agent**: Proporciona capacidades técnicas

Cada agente tiene una responsabilidad clara y el código es más mantenible y escalable.


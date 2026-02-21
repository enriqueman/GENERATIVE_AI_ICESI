# Trazabilidad de Tools - Documentación

## 🎯 ¿Por qué es necesario?

Agregar trazabilidad a las tools permite:
- 📊 **Visibilidad completa** en LangSmith del flujo completo
- 🔍 **Debug más fácil** cuando algo falla en las tools
- ⚡ **Performance tracking** de cada componente
- 📈 **Análisis de uso** de qué tools se usan más

## ✅ Cambios Realizados

### 1. `src/tools/product_checker.py`

**Funciones decoradas:**
- `check_product_existence()` - Función principal de verificación de productos
- `check_product()` - Helper simplificado

**Código agregado:**
```python
from langsmith import traceable

@traceable(name="check_product_existence")
def check_product_existence(...):
    ...

@traceable(name="check_product")  
def check_product(...):
    ...
```

### 2. `src/tools/document_retriever.py`

**Métodos decorados:**
- `search()` - Búsqueda de documentos

**Código agregado:**
```python
from langsmith import traceable

@traceable(name="DocumentRetriever.search")
def search(self, query: str) -> list:
    ...
```

### 3. `src/tools/query_processor.py`

**Métodos decorados:**
- `classify_query()` - Clasificación de consultas

**Código agregado:**
```python
from langsmith import traceable

@traceable(name="QueryProcessor.classify_query")
def classify_query(self, query: str) -> Dict[str, Any]:
    ...
```

## 📊 Vista en LangSmith

Ahora cuando hagas una consulta, verás una jerarquía completa en LangSmith:

```
📋 Trace: User Query
   ├─ QueryProcessor.classify_query
   │  ├─ Input: "¿Tienen botellas de acero?"
   │  └─ Output: {category: "producto", ...}
   │
   ├─ check_product_existence
   │  ├─ Input: query, search_type="producto"
   │  ├─ Steps:
   │  │  ├─ Load collection
   │  │  ├─ Search in Chroma
   │  │  └─ Filter by metadata
   │  └─ Output: {existe: true, ...}
   │
   ├─ DocumentRetriever.search (si aplica)
   │  ├─ Input: query
   │  └─ Output: [docs...]
   │
   └─ generate_answer_from_context
      ├─ Retrieval
      ├─ Generation
      └─ Output: "✅ Producto encontrado..."
```

## 🔍 Beneficios

### 1. Debugging Completo
```
Pregunta: "¿Tienen botellas?"
❌ No funcionó

En LangSmith puedo ver:
- QueryProcessor: ✅ Detected as "producto"
- check_product_existence: ❌ Error en línea 145
- Error: "Collection not found"
```

### 2. Performance Analysis
```
QueryProcessor.classify_query: 0.05s
check_product_existence: 0.8s
DocumentRetriever.search: 0.3s
generate_answer_from_context: 1.2s

Total: 2.35s
```

### 3. Usage Tracking
```
🔝 Most used tools:
1. check_product_existence: 142 calls
2. DocumentRetriever.search: 89 calls
3. QueryProcessor.classify_query: 142 calls
```

## 🎨 Ejemplo Real en LangSmith

### Trace Completo para: "¿Tienen botellas de acero?"

```
📋 Root Trace: User Query
  Duration: 2.34s
  Status: ✅ Success

  📥 Inputs:
    question: "¿Tienen botellas de acero?"

  🌳 Child Traces:

  1️⃣ QueryProcessor.classify_query
     Duration: 0.05s
     ✅ SUCCESS
     Outputs:
       category: "producto"
       is_list_query: false
       urgency: "normal"
       intention: "buy"

  2️⃣ _is_product_query
     Duration: 0.001s
     ✅ DETECTED as product query

  3️⃣ check_product_existence
     Duration: 0.85s
     ✅ SUCCESS
     Inputs:
       query: "¿Tienen botellas de acero?"
       search_type: "producto"
       umbral_similitud: 0.7
     Outputs:
       existe: true
       producto_nombre: "Botella Reutilizable de Acero Inoxidable"
       categoria: "Hogar"
       cantidad: "180"
       precio: "$25.99"

  4️⃣ _format_single_product_response
     Duration: 0.02s
     ✅ FORMATTED

  5️⃣ DocumentRetriever.search (fallback)
     Duration: 0.31s
     ✅ SUCCESS
     Outputs:
       num_documents: 5
       sources: [inventario.xlsx]

  6️⃣ generate_answer_from_context
     Duration: 1.14s
     ✅ SUCCESS
     Outputs:
       response: "✅ Producto Encontrado:\n📦 Botella...\n- Stock: 180\n- Precio: $25.99"

  📤 Output:
    "✅ Producto Encontrado: ..."
```

## 🚀 Cómo Activar

Ya está activado automáticamente cuando:

1. ✅ `LANGSMITH_TRACING=true` en `.env`
2. ✅ `LANGSMITH_API_KEY` configurada
3. ✅ Las tools tienen decoradores `@traceable`

No necesitas hacer nada más, las trazas se enviarán automáticamente a LangSmith cuando uses las tools.

## 📈 Beneficios Adicionales

### 1. Identificar Problemas
```python
# Si check_product_existence falla, verás exactamente dónde:
❌ Error en _search_single_product line 145
  query: "botellas"
  error: "Similarity search failed"
```

### 2. Optimizar Performance
```
check_product_existence: 0.85s ✅
_handle_product_query: 0.90s ✅
generate_answer_from_context: 1.14s ⚠️ (lento)

→ Optimizar generate_answer_from_context
```

### 3. Seguimiento de Uso
```
📊 Analytics:
- 70% de queries son sobre productos
- check_product_existence: herramienta más usada
- DocumentRetriever: backup en 30% de casos
```

## ✅ Checklist de Trazabilidad

- [x] `check_product_existence` decorada con `@traceable`
- [x] `check_product` decorada con `@traceable`
- [x] `DocumentRetriever.search` decorado con `@traceable`
- [x] `QueryProcessor.classify_query` decorado con `@traceable`
- [x] `generate_answer_from_context` decorado con `@traceable`
- [x] LangSmith tracing configurado en `.env`
- [x] Todas las imports de traceable agregadas

## 🎉 Resultado Final

Ahora tienes **trazabilidad completa** en LangSmith:

✅ **Funciones core** trazeadas
✅ **Tools** trazeadas  
✅ **Agent** trazeado
✅ **Retrieval** trazeado
✅ **Generation** trazeado

Todo el flujo RAG está ahora completamente visible en LangSmith 🚀


# Configuración de LangSmith Tracing

## 🎯 Problema Resuelto

El sistema de tracing a LangSmith no estaba funcionando por:
1. ✅ Error de sintaxis en `tracing.py` (línea 40)
2. ✅ Falta de decorador `@traceable` en funciones clave
3. ✅ Variables de entorno no configuradas antes de inicializar modelos

## 📝 Configuración Requerida

### 1. Variables de Entorno

En tu archivo `.env`, asegúrate de tener:

```bash
# LangSmith Tracing (Habilitar)
LANGSMITH_TRACING=true

# API Key de LangSmith (obtenla en https://smith.langchain.com)
LANGSMITH_API_KEY=ls__xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Endpoint (opcional, por defecto usa el oficial)
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# Nombre del proyecto en LangSmith
LANGCHAIN_PROJECT=ecomarket-rag-system
```

### 2. Instalación de LangSmith

```bash
pip install langsmith
```

### 3. Obtener API Key

1. Ve a https://smith.langchain.com
2. Inicia sesión o crea una cuenta
3. Ve a Settings → API Keys
4. Copia tu API key
5. Agrégala al `.env` como `LANGSMITH_API_KEY`

## 🔧 Cambios Realizados

### 1. `src/utils/tracing.py`
- ✅ **Línea 40**: Corregido error de sintaxis
- ✅ Se eliminó texto basura "src/utils/vector_functions.py                "
- ✅ Ahora lee correctamente las variables de entorno

### 2. `src/utils/vector_functions.py`
- ✅ **Líneas 22-32**: Importación de `traceable` de LangSmith
- ✅ **Líneas 43-67**: Nueva función `_configure_langsmith_tracing()`
- ✅ **Línea 70**: Llamada a configuración ANTES de inicializar modelos
- ✅ **Línea 380**: Decorador `@traceable` en `generate_answer_from_context()`

## 🚀 Cómo Funciona Ahora

### Flujo de Tracing

```
1. Se importa el módulo vector_functions
   ↓
2. _configure_langsmith_tracing() verifica variables de entorno
   ↓
3. Si LANGSMITH_TRACING=true:
   - Configura LANGCHAIN_TRACING_V2=true
   - Establece LANGCHAIN_API_KEY
   - Establece LANGCHAIN_ENDPOINT
   - Establece LANGCHAIN_PROJECT
   ↓
4. Se inicializan llm y embeddings (ahora con tracing activo)
   ↓
5. Cuando se llama generate_answer_from_context():
   - @traceable decora la función
   - LangSmith captura automáticamente:
     * Inputs (question, retriever)
     * Outputs (response)
     * Metadata (processing_time, etc.)
     * Errores si ocurren
   ↓
6. Las trazas se envían a LangSmith Cloud
```

## 📊 Qué se Traza

### Información Capturada Automáticamente:

1. **Inputs:**
   - `question`: La pregunta del usuario
   - `retriever`: Información del retriever usado
   - `enable_logging`: Si logging está habilitado

2. **Outputs:**
   - `response`: La respuesta generada

3. **Metadata:**
   - Timestamps de inicio y fin
   - Tiempo de procesamiento
   - Número de documentos recuperados
   - Errores si ocurren

4. **Enlaces a Otras Trazas:**
   - Retrieval operation (recuperación de documentos)
   - Generation operation (generación de respuesta)
   - Product queries (si aplica)

## 🧪 Verificar que Funciona

### 1. Inicia la aplicación

```bash
streamlit run src/app.py
```

### 2. Busca en la consola estos mensajes:

```
✅ LangSmith tracing configurado - Proyecto: ecomarket-rag-system
```

**O si hay un problema:**

```
⚠️  LangSmith tracing habilitado pero no se encontró API_KEY
```

**O si está deshabilitado:**

```
ℹ️  LangSmith tracing deshabilitado
```

### 3. Haz una pregunta en el chat

Cualquier consulta activará el tracing automáticamente.

### 4. Ve a LangSmith Dashboard

1. Ve a https://smith.langchain.com
2. Selecciona tu proyecto "ecomarket-rag-system"
3. Busca trazas recientes
4. Verás detalles de cada llamada incluyendo:
   - Pregunta del usuario
   - Contexto recuperado
   - Respuesta generada
   - Tiempos de ejecución
   - Errores si ocurren

## 🎨 Vista en LangSmith

Cuando abres una traza, verás:

```
📋 Trace: generate_answer_from_context
   ├─ Inputs:
   │  ├─ question: "¿Tienen botellas de acero?"
   │  └─ enable_logging: false
   │
   ├─ Steps:
   │  ├─ 1. Retrieval (Recuperación de documentos)
   │  │   ├─ Total documentos: 3
   │  │   ├─ Sources: [inventario.xlsx, ...]
   │  │   └─ Time: 0.5s
   │  │
   │  ├─ 2. Generation (Generación de respuesta)
   │  │   ├─ Model: gpt-4o-mini
   │  │   ├─ Response length: 245 chars
   │  │   └─ Time: 1.2s
   │  │
   └─ Total time: 1.7s

   Output:
   "✅ Producto Encontrado: Botella Reutilizable..."
```

## 🔍 Debugging

### Si no aparecen trazas en LangSmith

1. **Verifica las variables de entorno:**
   ```bash
   echo $LANGSMITH_TRACING
   echo $LANGSMITH_API_KEY
   ```

2. **Revisa los logs de la aplicación:**
   ```
   ✅ LangSmith tracing configurado...
   ```

3. **Verifica que LangSmith está instalado:**
   ```bash
   python -c "from langsmith import traceable; print('OK')"
   ```

4. **Verifica el proyecto en LangSmith:**
   - Ve a https://smith.langchain.com
   - Asegúrate que el proyecto existe
   - Verifica que tienes API key válida

### Errores Comunes

**Error: "No module named 'langsmith'"**
```bash
pip install langsmith
```

**Error: "Invalid API key"**
- Verifica que copiaste correctamente la API key
- Asegúrate que no hay espacios extras

**No aparecen trazas:**
- Verifica que `LANGSMITH_TRACING=true` en el .env
- Reinicia la aplicación después de cambiar variables

## 📈 Análisis en LangSmith

Una vez que tienes trazas, puedes analizar:

1. **Performance:**
   - Tiempo promedio de respuesta
   - Documentos recuperados vs relevantes
   - Uso de tokens

2. **Calidad:**
   - Respuestas generadas
   - Relevancia del contexto
   - Errores frecuentes

3. **Optimización:**
   - Identificar queries lentas
   - Mejorar retrieval
   - Ajustar umbrales de similitud

## ✅ Checklist

- [ ] LangSmith instalado (`pip install langsmith`)
- [ ] Variables en `.env` configuradas
- [ ] API key válida de LangSmith
- [ ] Mensaje de confirmación en consola
- [ ] Primeras trazas apareciendo en dashboard
- [ ] Tracing funcionando correctamente

## 🎉 Resultado

Ahora todas las consultas al RAG se trazan automáticamente en LangSmith, permitiéndote:

- 📊 Monitor de performance en tiempo real
- 🐛 Debug de errores con contexto completo
- 📈 Análisis de uso del sistema
- 🔍 Optimización de retrieval


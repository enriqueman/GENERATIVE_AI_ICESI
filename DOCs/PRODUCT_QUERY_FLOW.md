# Flujo de Consultas de Productos - EcoMarket

## 🎯 Visión General

El sistema ahora detecta automáticamente consultas sobre productos y usa la herramienta `product_checker` para búsquedas precisas en el inventario con filtros avanzados.

## 📊 Flujo de Decisión

```
Usuario hace una pregunta
         ↓
    Clasificar consulta
         ↓
    ¿Es sobre productos?
    ├─ Sí → ¿Es lista?
    │       ├─ Sí → Verificar si es lista de PRODUCTOS → Usar product_checker(search_type="lista")
    │       └─ No → Usar product_checker(search_type="producto" o "categoria")
    │
    └─ No → ¿Es lista general?
            ├─ Sí → Usar RAG estándar con documentos
            └─ No → Usar RAG estándar
```

## 🔍 Detección de Consultas de Productos

### `_is_product_query()` - Detecta consultas individuales de productos

**Keywords de activación:**
- "¿tienen", "¿tienes", "¿hay", "¿existe", "¿disponible"
- "producto", "productos", "catalogo", "catálogo", "inventario"
- "en stock", "disponibilidad", "busco", "necesito", "quiero"
- "categoría", "categoria", "precio"

**Ejemplos:**
- ✅ "¿Tienen botellas de acero?"
- ✅ "¿Qué productos hay en stock?"
- ✅ "Necesito un cepillo de bambú"
- ❌ "¿Cuál es la política de devoluciones?"

### `_is_product_list_query()` - Detecta listas de productos

**Keywords específicas:**
- "producto", "productos", "catalogo", "catálogo", "inventario"
- "en stock", "disponibilidad"
- "categoría", "categoria", "precio", "stock", "disponible"

**Ejemplos:**
- ✅ "¿Qué productos tienen en la categoría Hogar?"
- ✅ "Muéstrame todos los productos disponibles"
- ✅ "Lista de productos con precio menor a $30"
- ❌ "¿Cuáles son las políticas de envío?" (no es sobre productos)

## 🛠️ Tipos de Búsqueda

### 1. Búsqueda Individual (`search_type="producto"`)

**Activación:**
- Consulta sobre un solo producto
- Pregunta directa sobre disponibilidad

**Ejemplo:**
```python
"¿Tienen botellas de acero inoxidable?"
```

**Respuesta:**
```
✅ Producto Encontrado:

📦 Botella Reutilizable de Acero Inoxidable
- Categoría: Hogar
- Cantidad en Stock: 180 unidades
- Precio: $25.99

¿Te gustaría más información sobre este producto?
```

### 2. Búsqueda de Lista (`search_type="lista"`)

**Activación:**
- Palabras: "lista", "cuáles", "qué productos", "muestra", "todos los"
- Múltiples productos separados por comas o "y"
- Query de tipo lista

**Ejemplo 1:**
```python
"¿Tienen botella, bolsa y cepillo?"
```

**Respuesta:**
```
📋 Resultados de Búsqueda:

Encontrados 2 de 3 productos buscados:

1. ✅ botella
   → Botella Reutilizable de Acero Inoxidable
   - Categoría: Hogar
   - Stock: 180
   - Precio: $25.99

2. ✅ bolsa
   → Bolsa de Tela Ecológica Reutilizable
   - Categoría: Hogar
   - Stock: 500
   - Precio: $3.5

3. ❌ cepillo (No encontrado)
```

**Ejemplo 2:**
```python
"¿Cuáles son sus productos disponibles?"
```

**Resultado:** Busca todos los productos y retorna lista completa

### 3. Búsqueda por Categoría (`search_type="categoria"`)

**Activación:**
- Palabras "categoría", "categoria" en la pregunta
- Filtro explícito de categoría

**Ejemplo:**
```python
"¿Qué productos tienen en la categoría Hogar?"
```

**Respuesta:**
```
📦 Productos en categoría: Hogar

Encontrados 2 productos:

1. Botella Reutilizable de Acero Inoxidable
   - Stock: 180 unidades
   - Precio: $25.99

2. Bolsa de Tela Ecológica Reutilizable
   - Stock: 500 unidades
   - Precio: $3.5
```

### 4. Búsqueda con Filtros Combinados

**Filtros disponibles:**
- `categoria_filtro`: Filtrar por categoría específica
- `precio_min`: Precio mínimo
- `precio_max`: Precio máximo

**Ejemplo:**
```python
"¿Tienen botellas de la categoría Hogar menores a $30?"
```

**Extracción automática:**
- categoria_filtro = "Hogar"
- precio_max = 30.0

## 🔄 Procesamiento Detallado

### 1. Clasificación de la Consulta

```python
query_info = {
    'category': 'producto',  # o 'precio', 'contacto', etc.
    'is_list_query': True,   # o False
    'intention': 'buy',      # o 'info', 'track', etc.
    'urgency': 'normal'      # o 'urgent', 'high'
}
```

### 2. Extracción de Parámetros

**Categoría:**
```python
# Busca: "categoría Hogar", "categoria Hogar", "de Hogar"
categoria_match = re.search(r'(?:categoría|categoria|de)\s+(\w+)', question)
```

**Precio:**
```python
# Busca números y determina si es min o max
"menos de $30" → precio_max = 30.0
"más de $10" → precio_min = 10.0
```

**Lista:**
```python
# Detecta múltiples productos
"botella, bolsa, cepillo" → search_type = "lista"
"botella y bolsa" → search_type = "lista"
```

### 3. Ejecución de Búsqueda

```python
result = check_product_existence(
    query=question,
    search_type=search_type,          # "producto", "lista", "categoria", "precio"
    categoria_filtro=categoria_filtro,
    precio_min=precio_min,
    precio_max=precio_max,
    umbral_similitud=0.7
)
```

### 4. Formateo de Respuesta

**Single Product:**
```python
_format_single_product_response(result)
```

**List:**
```python
_format_list_product_response(result)
```

**Category:**
```python
_format_category_response(result)
```

## 📝 Ejemplos Completos

### Ejemplo 1: Producto Individual
**Usuario:** "¿Tienen botellas de acero inoxidable?"

**Procesamiento:**
1. ✅ Detected as product query
2. search_type = "producto"
3. check_product_existence(query="botellas de acero inoxidable", ...)
4. Found: Botella Reutilizable de Acero Inoxidable
5. Return formatted response

### Ejemplo 2: Múltiples Productos
**Usuario:** "¿Tienen botella, bolsa y cepillo?"

**Procesamiento:**
1. ✅ Detected as product query
2. ✅ Has multiple products (", " and " y ")
3. search_type = "lista"
4. check_product_existence(search_type="lista", ...)
5. Search each: "botella", "bolsa", "cepillo"
6. Return list with results for each

### Ejemplo 3: Por Categoría
**Usuario:** "¿Qué productos tienen en la categoría Hogar?"

**Procesamiento:**
1. ✅ Detected as product query
2. ✅ "categoría" keyword found
3. categoria_filtro = "Hogar"
4. search_type = "categoria"
5. check_product_existence(search_type="categoria", categoria_filtro="Hogar")
6. Return all products in category

### Ejemplo 4: Filtro por Precio
**Usuario:** "¿Qué productos tienen menores a $30?"

**Procesamiento:**
1. ✅ Detected as product query
2. ✅ "menores a" + number found
3. precio_max = 30.0
4. Extract products matching price filter
5. Return filtered list

### Ejemplo 5: Consulta General (No de Productos)
**Usuario:** "¿Cuál es la política de devoluciones?"

**Procesamiento:**
1. ❌ Not detected as product query
2. Use standard RAG flow
3. Retrieve relevant documents
4. Generate answer from context

## 🎨 Formato de Respuestas

### Producto Encontrado
```markdown
✅ Producto Encontrado:

📦 [Nombre Producto]
- Categoría: [Categoría]
- Cantidad en Stock: [Cantidad] unidades
- Precio: $[Precio]

¿Te gustaría más información sobre este producto?

[Si hay matches alternativos]
📋 Productos alternativos similares:
- [Producto] (Categoría: X, Precio: $Y)
```

### Producto No Encontrado
```markdown
❌ Producto no encontrado

No encontramos el producto que buscas en nuestro inventario.

¿Podrías intentar con:
- Otro nombre o descripción
- Buscar por categoría
- O contactarnos directamente
```

### Lista de Productos
```markdown
📋 Resultados de Búsqueda:

Encontrados X de Y productos buscados:

1. ✅ [nombre]
   → [nombre completo encontrado]
   - Categoría: X
   - Stock: Y
   - Precio: $Z

[Si no encontrado]
2. ❌ [nombre] (No encontrado)
```

### Categoría
```markdown
📦 Productos en categoría: [Categoría]

Encontrados X productos:

1. [Nombre Producto]
   - Stock: Y unidades
   - Precio: $Z
```

## 🚀 Ventajas del Nuevo Sistema

1. **Detección Automática**: No requiere especificar tipo de búsqueda
2. **Extracción Inteligente**: Parsea automáticamente filtros de categoría y precio
3. **Múltiples Formatos**: Soporta consultas naturales del usuario
4. **Fallback Inteligente**: Si falla, usa RAG estándar
5. **Respuestas Formateadas**: Markdown bonito con emojis
6. **Traza Completa**: Logging de todas las operaciones

## 🧪 Testing

Puedes probar con las siguientes consultas:

1. "¿Tienen botellas de acero?"
2. "¿Qué productos hay en la categoría Hogar?"
3. "¿Tienen botella, bolsa y cepillo?"
4. "¿Qué productos tienen menos de $30?"
5. "Muéstrame todos los productos disponibles"
6. "¿Tienen botellas de Hogar menores a $30?"


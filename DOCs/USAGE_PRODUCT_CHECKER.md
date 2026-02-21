# Product Checker Tool - Guía de Uso

## Descripción
La herramienta `check_product_existence` permite verificar la existencia de productos en el inventario usando búsqueda semántica en Chroma con filtros avanzados por metadata.

## Instalación
El módulo ya está integrado en `src/tools/product_checker.py` y exportado en `src/tools/__init__.py`.

## Funciones Disponibles

### 1. `check_product_existence()` - Función principal

Busca productos con múltiples opciones de filtrado.

**Parámetros:**
- `query` (str): Nombre, lista, categoría o rango de precio
- `search_type` (str): Tipo de búsqueda - "producto", "lista", "categoria", "precio", "nombre_exacto"
- `categoria_filtro` (str, opcional): Filtrar por categoría específica
- `precio_min` (float, opcional): Precio mínimo
- `precio_max` (float, opcional): Precio máximo  
- `umbral_similitud` (float, default 0.7): Score mínimo de similitud
- `collection_name` (str, default "sample_documents"): Colección de Chroma

**Retorna:** Dict con resultados estructurados

### 2. `check_product()` - Helper simplificado

Verificación rápida de un producto individual.

**Parámetros:**
- `product_name` (str): Nombre del producto
- `umbral` (float, default 0.7): Umbral de similitud

**Retorna:** Dict con resultado de verificación

## Tipos de Búsqueda

### 1. Búsqueda Individual (`search_type="producto"` o `"nombre_exacto"`)

Busca un producto específico usando similitud semántica.

```python
from src.tools import check_product_existence

# Búsqueda flexible
result = check_product_existence(
    query="botella de acero",
    search_type="producto",
    umbral_similitud=0.7
)

# Retorna:
# {
#     "existe": True,
#     "producto_nombre": "Botella Reutilizable de Acero Inoxidable",
#     "categoria": "Hogar",
#     "cantidad": "180",
#     "precio": "25.99",
#     "similitud": 0.85,
#     "mensaje": "Producto encontrado con similitud 0.85",
#     "detalles": {...}
# }
```

### 2. Búsqueda de Lista (`search_type="lista"`)

Busca múltiples productos desde una lista separada por comas.

```python
result = check_product_existence(
    query="botella, bolsa, cepillo",
    search_type="lista",
    umbral_similitud=0.7
)

# Retorna:
# {
#     "resultados": [
#         {
#             "producto_ingresado": "botella",
#             "existe": True,
#             "similitud": 0.85,
#             "detalles_match": {
#                 "producto_nombre": "Botella Reutilizable de Acero Inoxidable",
#                 "categoria": "Hogar",
#                 "cantidad": "180",
#                 "precio": "25.99"
#             }
#         },
#         ...
#     ],
#     "total_encontrados": 2,
#     "total_buscados": 3
# }
```

### 3. Búsqueda por Categoría (`search_type="categoria"`)

Busca todos los productos de una categoría específica.

```python
result = check_product_existence(
    query="Hogar",
    search_type="categoria",
    categoria_filtro="Hogar"
)

# Retorna:
# {
#     "categoria": "Hogar",
#     "productos": [
#         {
#             "nombre": "Botella Reutilizable de Acero Inoxidable",
#             "cantidad": "180",
#             "precio": "25.99",
#             "categoria": "Hogar"
#         },
#         ...
#     ],
#     "total": 2
# }
```

### 4. Búsqueda por Rango de Precio (`search_type="precio"`)

Busca productos dentro de un rango de precios.

```python
result = check_product_existence(
    query="productos menos de $30",
    search_type="precio",
    precio_max=30.0
)

# Retorna:
# {
#     "rango_precio": {"min": None, "max": 30.0},
#     "productos": [
#         {
#             "nombre": "Bolsa de Tela Ecológica Reutilizable",
#             "categoria": "Hogar",
#             "cantidad": "500",
#             "precio": 3.5
#         },
#         ...
#     ],
#     "total": 1
# }
```

## Ejemplos Avanzados

### Búsqueda con Filtros Combinados

```python
# Buscar botellas de categoría "Hogar" con precio menor a $30
result = check_product_existence(
    query="botella",
    search_type="producto",
    categoria_filtro="Hogar",
    precio_max=30.0,
    umbral_similitud=0.7
)
```

### Verificación de Múltiples Productos con Filtro

```python
# Verificar lista de productos en una categoría específica
result = check_product_existence(
    query="botella, bolsa, cepillo",
    search_type="lista",
    categoria_filtro="Hogar",
    umbral_similitud=0.6
)
```

## Integración con el Agente

```python
from src.tools import check_product_existence

# En tu agente RAG
def process_product_query(user_query: str):
    # Detectar tipo de consulta
    if "lista" in user_query.lower():
        search_type = "lista"
    elif "categoría" in user_query.lower() or "categoría" in user_query:
        search_type = "categoria"
    elif "precio" in user_query.lower():
        search_type = "precio"
    else:
        search_type = "producto"
    
    # Ejecutar búsqueda
    result = check_product_existence(
        query=user_query,
        search_type=search_type,
        umbral_similitud=0.7
    )
    
    return result
```

## Estructura de Respuestas

### Búsqueda Individual
```python
{
    "existe": bool,
    "producto_nombre": str,
    "categoria": str,
    "cantidad": str,
    "precio": str,
    "similitud": float,
    "mensaje": str,
    "detalles": {...},
    "matches_alternativos": [...]  # Solo si hay múltiples matches >0.9
}
```

### Búsqueda de Lista
```python
{
    "resultados": [
        {
            "producto_ingresado": str,
            "existe": bool,
            "similitud": float,
            "detalles_match": {...} or None,
            "mensaje": str  # Solo si no existe
        }
    ],
    "total_encontrados": int,
    "total_buscados": int
}
```

### Búsqueda por Categoría
```python
{
    "categoria": str,
    "productos": [
        {
            "nombre": str,
            "cantidad": str,
            "precio": str,
            "categoria": str
        }
    ],
    "total": int
}
```

### Búsqueda por Precio
```python
{
    "rango_precio": {"min": float, "max": float},
    "productos": [
        {
            "nombre": str,
            "categoria": str,
            "cantidad": str,
            "precio": float
        }
    ],
    "total": int
}
```

## Manejo de Errores

```python
# Query vacío
{
    "error": "Query vacío",
    "existe": False,
    "mensaje": "El query de búsqueda no puede estar vacío"
}

# Colección no encontrada
{
    "existe": False,
    "mensaje": "Colección no encontrada o vacía"
}

# Tipo de búsqueda inválido
{
    "error": "Tipo de búsqueda no válido: xyz",
    "existe": False
}
```

## Notas Importantes

1. **Umbral de Similitud**: Por defecto es 0.7. Ajusta según tus necesidades:
   - 0.9+ = Muy estricto (coincidencias casi exactas)
   - 0.7 = Balanceado (recomendado)
   - 0.5 = Relajado (acepta coincidencias débiles)

2. **Metadata Filtros**: Los filtros de categoría y precio se aplican después de la búsqueda semántica debido a limitaciones actuales de Chroma/LangChain.

3. **Múltiples Matches**: Si encuentra múltiples productos con similitud >0.9, retorna todos en `matches_alternativos`.

4. **Formato de Precio**: El sistema acepta precios con "$" y comas (ej: "$25,99" o "25.99").

5. **Deduplicación**: Los resultados por categoría y precio eliminan duplicados automáticamente.


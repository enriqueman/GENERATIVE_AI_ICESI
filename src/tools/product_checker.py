"""
Herramienta para verificar existencia de productos en el inventario
Usa búsqueda semántica en Chroma con filtros por metadata
"""

import os
import sys
import re
from typing import Dict, Any, List, Optional, Tuple

# Agregar src al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.vector_functions import load_collection
from utils.tracing import tracer

# Importar traceable para LangSmith
try:
    from langsmith import traceable
    TRACEABLE = traceable
except ImportError:
    # Si no está disponible, usar decorador vacío
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    TRACEABLE = traceable


@TRACEABLE(name="check_product_existence")
def check_product_existence(
    query: str,
    search_type: str = "producto",
    categoria_filtro: Optional[str] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    umbral_similitud: float = 0.7,
    collection_name: str = "sample_documents"
) -> Dict[str, Any]:
    """
    Verificar existencia de productos usando búsqueda semántica en Chroma
    
    ⚠️ ADVERTENCIA - SISTEMA DE TRAZAS:
    Esta función tiene el decorador @TRACEABLE que crea una traza en LangSmith.
    - Se agrupa automáticamente bajo la traza padre si se llama desde OrchestratorAgent.process_query()
    - NO crear context managers adicionales aquí - el de OrchestratorAgent es suficiente
    - NO remover el decorador @TRACEABLE - es necesario para que aparezca en LangSmith
    
    Args:
        query: Nombre del producto, lista, categoría o rango de precio
        search_type: Tipo de búsqueda - "producto", "lista", "categoria", "precio", "nombre_exacto"
        categoria_filtro: Filtrar por categoría específica (opcional)
        precio_min: Precio mínimo (opcional)
        precio_max: Precio máximo (opcional)
        umbral_similitud: Score mínimo de similitud (default: 0.7)
        collection_name: Nombre de la colección en Chroma
        
    Returns:
        dict: Resultados estructurados según el tipo de búsqueda
    """
    
    if not query or query.strip() == "":
        return {
            "error": "Query vacío",
            "existe": False,
            "mensaje": "El query de búsqueda no puede estar vacío"
        }
    
    try:
        # Cargar colección de Chroma
        vectordb = load_collection(collection_name)
        
        # Validar que la colección existe
        if vectordb is None:
            return {
                "existe": False,
                "mensaje": "Colección no encontrada o vacía"
            }
        
        # Procesar según el tipo de búsqueda
        if search_type == "producto" or search_type == "nombre_exacto":
            return _search_single_product(
                query, vectordb, umbral_similitud, categoria_filtro, 
                precio_min, precio_max, exact=search_type == "nombre_exacto"
            )
        elif search_type == "lista":
            return _search_product_list(
                query, vectordb, umbral_similitud, categoria_filtro, 
                precio_min, precio_max
            )
        elif search_type == "categoria":
            return _search_by_category(
                query, vectordb, categoria_filtro
            )
        elif search_type == "precio":
            return _search_by_price(
                query, vectordb, precio_min, precio_max
            )
        elif search_type == "todas_categorias":
            return _get_all_categories(
                vectordb
            )
        elif search_type == "todos_productos":
            return _get_all_products(
                vectordb
            )
        else:
            return {
                "error": f"Tipo de búsqueda no válido: {search_type}",
                "existe": False
            }
            
    except Exception as e:
        tracer.log(
            operation="PRODUCT_CHECK_ERROR",
            message=f"Error verificando producto: {str(e)}",
            metadata={"query": query, "search_type": search_type},
            level="ERROR"
        )
        return {
            "error": str(e),
            "existe": False
        }


def _search_single_product(
    query: str,
    vectordb,
    umbral_similitud: float,
    categoria_filtro: Optional[str],
    precio_min: Optional[float],
    precio_max: Optional[float],
    exact: bool = False
) -> Dict[str, Any]:
    """Buscar un producto individual"""
    
    try:
        # Construir filtros de metadata
        where_filters = _build_metadata_filters(categoria_filtro, precio_min, precio_max)
        
        # Buscar en Chroma (similarity search)
        # Nota: Chroma/LangChain no soporta where directamente en similarity_search
        # Necesitamos filtrar post-procesamiento
        results = vectordb.similarity_search_with_score(
            query=query,
            k=10  # Buscar múltiples matches
        )
        
        # Filtrar por umbral de similitud y metadata
        # Chroma devuelve distancia (menor = más similar), convertimos a similitud
        # Distancia máxima típica es ~1-2, normalizamos
        filtered_results = []
        
        for doc, distance in results:
            # IMPORTANTE: Solo incluir productos de archivos Excel/inventario
            source_type = doc.metadata.get("source_type", "")
            file_type = doc.metadata.get("file_type", "")
            source = doc.metadata.get("source", "")
            
            # Solo procesar si es un archivo de inventario (Excel)
            is_inventory = (
                source_type == "inventory" or
                file_type == "excel" or
                ("inventario" in source.lower() if source else False) or
                (".xlsx" in source.lower() if source else False)
            )
            
            if not is_inventory:
                continue
            
            # Convertir distancia a similitud (normalizado)
            # Distancias típicas: 0 (exacto) a ~1.5 (poco similar)
            similarity = max(0, 1 - (distance / 2.0))  # Normalizar a 0-1
            
            if similarity >= umbral_similitud:
                # Aplicar filtros de metadata
                if _matches_metadata_filters(
                    doc.metadata, 
                    categoria_filtro, 
                    precio_min, 
                    precio_max
                ):
                    filtered_results.append((doc, similarity))
        
        # Ordenar por similitud descendente
        filtered_results.sort(key=lambda x: x[1], reverse=True)
        
        # Si es búsqueda exacta, tomar solo el mejor match
        if exact:
            filtered_results = filtered_results[:1]
        else:
            # Si hay múltiples matches con alta similitud (>0.9), retornar todos
            high_similarity_results = [r for r in filtered_results if r[1] > 0.9]
            if high_similarity_results:
                filtered_results = high_similarity_results
        
        if filtered_results:
            best_match = filtered_results[0]
            doc = best_match[0]
            similarity = best_match[1]
            
            # Extraer detalles de metadata
            # Si metadata está vacío, parsear del content
            producto_nombre = doc.metadata.get("producto_nombre")
            categoria = doc.metadata.get("categoria")
            cantidad = doc.metadata.get("cantidad")
            precio = doc.metadata.get("precio")
            
            # Si metadata está vacío, parsear del content
            if producto_nombre in ["N/A", None, ""] and doc.page_content:
                parsed = _parse_product_from_content(doc.page_content)
                producto_nombre = parsed.get("producto_nombre", "N/A")
                categoria = parsed.get("categoria", "N/A")
                cantidad = parsed.get("cantidad", "N/A")
                precio = parsed.get("precio", "N/A")
            
            details = {
                "producto_nombre": producto_nombre,
                "categoria": categoria,
                "cantidad": cantidad,
                "precio": precio,
                "similitud": round(similarity, 3),
                "content": doc.page_content
            }
            
            result = {
                "existe": True,
                "producto_nombre": producto_nombre,
                "categoria": categoria,
                "cantidad": cantidad,
                "precio": precio,
                "similitud": round(similarity, 3),
                "mensaje": f"Producto encontrado con similitud {similarity:.2f}",
                "detalles": details
            }
            
            # Si hay múltiples matches, incluir todos
            if len(filtered_results) > 1:
                result["matches_alternativos"] = []
                for alt_doc, alt_sim in filtered_results[1:]:
                    alt_producto = alt_doc.metadata.get("producto_nombre")
                    alt_categoria = alt_doc.metadata.get("categoria")
                    alt_cantidad = alt_doc.metadata.get("cantidad")
                    alt_precio = alt_doc.metadata.get("precio")
                    
                    # Si metadata está vacío, parsear del content
                    if alt_producto in ["N/A", None, ""] and alt_doc.page_content:
                        parsed = _parse_product_from_content(alt_doc.page_content)
                        alt_producto = parsed.get("producto_nombre", "N/A")
                        alt_categoria = parsed.get("categoria", "N/A")
                        alt_cantidad = parsed.get("cantidad", "N/A")
                        alt_precio = parsed.get("precio", "N/A")
                    
                    result["matches_alternativos"].append({
                        "producto_nombre": alt_producto,
                        "categoria": alt_categoria,
                        "cantidad": alt_cantidad,
                        "precio": alt_precio,
                        "similitud": round(alt_sim, 3)
                    })
            
            return result
        else:
            return {
                "existe": False,
                "producto_nombre": query,
                "mensaje": f"No se encontró producto con similitud >= {umbral_similitud}"
            }
            
    except Exception as e:
        tracer.log(
            operation="SEARCH_ERROR",
            message=f"Error en búsqueda individual: {str(e)}",
            level="ERROR"
        )
        return {
            "existe": False,
            "error": str(e)
        }


def _search_product_list(
    query: str,
    vectordb,
    umbral_similitud: float,
    categoria_filtro: Optional[str],
    precio_min: Optional[float],
    precio_max: Optional[float]
) -> Dict[str, Any]:
    """Buscar múltiples productos desde una lista separada por comas"""
    
    # Parsear lista de productos
    product_list = [p.strip() for p in query.split(",") if p.strip()]
    
    if not product_list:
        return {
            "error": "Lista de productos vacía",
            "resultados": [],
            "total_encontrados": 0,
            "total_buscados": 0
        }
    
    resultados = []
    total_encontrados = 0
    
    for producto in product_list:
        # Buscar cada producto individualmente
        result = _search_single_product(
            producto, vectordb, umbral_similitud, 
            categoria_filtro, precio_min, precio_max, exact=False
        )
        
        resultado_item = {
            "producto_ingresado": producto,
            "existe": result.get("existe", False),
            "similitud": result.get("similitud", 0.0)
        }
        
        if result.get("existe"):
            resultado_item["detalles_match"] = {
                "producto_nombre": result.get("producto_nombre", "N/A"),
                "categoria": result.get("categoria", "N/A"),
                "cantidad": result.get("cantidad", "N/A"),
                "precio": result.get("precio", "N/A")
            }
            total_encontrados += 1
        else:
            resultado_item["detalles_match"] = None
            resultado_item["mensaje"] = result.get("mensaje", "Producto no encontrado")
        
        resultados.append(resultado_item)
    
    return {
        "resultados": resultados,
        "total_encontrados": total_encontrados,
        "total_buscados": len(product_list)
    }


def _search_by_category(
    query: str,
    vectordb,
    categoria_filtro: Optional[str]
) -> Dict[str, Any]:
    """Buscar todos los productos de una categoría"""
    
    category = categoria_filtro if categoria_filtro else query
    
    try:
        # Usar query semántica para encontrar productos de la categoría
        # Nota: Esta es una aproximación, idealmente deberíamos usar metadata where filters
        results = vectordb.similarity_search_with_score(
            query=f"categoría {category} productos disponibles stock",
            k=999  # Buscar muchos resultados
        )
        
        productos = []
        
        for doc, distance in results:
            # IMPORTANTE: Solo incluir productos de archivos Excel/inventario
            source_type = doc.metadata.get("source_type", "")
            file_type = doc.metadata.get("file_type", "")
            source = doc.metadata.get("source", "")
            
            # Solo procesar si es un archivo de inventario (Excel)
            is_inventory = (
                source_type == "inventory" or
                file_type == "excel" or
                ("inventario" in source.lower() if source else False) or
                (".xlsx" in source.lower() if source else False)
            )
            
            if not is_inventory:
                continue
            
            doc_category = doc.metadata.get("categoria", "").lower()
            query_category = category.lower()
            
            # Si metadata está vacío, parsear del content
            if not doc_category or doc_category == "n/a":
                parsed = _parse_product_from_content(doc.page_content)
                doc_category = parsed.get("categoria", "").lower()
            
            # Solo incluir si la categoría coincide (filtro manual)
            if query_category in doc_category or doc_category in query_category:
                producto_nombre = doc.metadata.get("producto_nombre", "N/A")
                cantidad = doc.metadata.get("cantidad", "N/A")
                precio = doc.metadata.get("precio", "N/A")
                cat = doc.metadata.get("categoria", "N/A")
                
                # Si metadata está vacío, parsear del content
                if producto_nombre in ["N/A", None, ""] and doc.page_content:
                    parsed = _parse_product_from_content(doc.page_content)
                    producto_nombre = parsed.get("producto_nombre", "N/A")
                    cantidad = parsed.get("cantidad", "N/A")
                    precio = parsed.get("precio", "N/A")
                    cat = parsed.get("categoria", "N/A")
                
                producto = {
                    "nombre": producto_nombre,
                    "cantidad": cantidad,
                    "precio": precio,
                    "categoria": cat
                }
                productos.append(producto)
        
        # Eliminar duplicados basados en nombre
        seen = set()
        productos_unicos = []
        for p in productos:
            if p["nombre"] not in seen:
                seen.add(p["nombre"])
                productos_unicos.append(p)
        
        return {
            "categoria": category,
            "productos": productos_unicos,
            "total": len(productos_unicos)
        }
        
    except Exception as e:
        tracer.log(
            operation="CATEGORY_SEARCH_ERROR",
            message=f"Error buscando por categoría: {str(e)}",
            level="ERROR"
        )
        return {
            "categoria": category,
            "productos": [],
            "total": 0,
            "error": str(e)
        }


def _search_by_price(
    query: str,
    vectordb,
    precio_min: Optional[float],
    precio_max: Optional[float]
) -> Dict[str, Any]:
    """Buscar productos por rango de precio"""
    
    # Parsear precio si viene como string en query
    if not precio_min and not precio_max and query:
        # Intentar extraer números del query
        numbers = re.findall(r'\d+\.?\d*', query)
        if len(numbers) >= 2:
            precio_min = float(numbers[0])
            precio_max = float(numbers[1])
        elif len(numbers) == 1:
            # Precio máximo
            precio_max = float(numbers[0])
    
    if not precio_min and not precio_max:
        return {
            "error": "Debe especificar precio_min y/o precio_max",
            "rango_precio": {"min": None, "max": None},
            "productos": [],
            "total": 0
        }
    
    try:
        # Buscar todos los productos (requiere paginación o todas las entradas)
        # Nota: Chroma no soporta directamente where con comparaciones numéricas
        # para precio, así que hacemos búsqueda amplia y filtramos post-procesamiento
        
        # Usar query genérica para traer muchos productos
        results = vectordb.similarity_search_with_score(
            query="productos inventario stock disponible",
            k=999
        )
        
        productos = []
        
        for doc, distance in results:
            # IMPORTANTE: Solo incluir productos de archivos Excel/inventario
            source_type = doc.metadata.get("source_type", "")
            file_type = doc.metadata.get("file_type", "")
            source = doc.metadata.get("source", "")
            
            # Solo procesar si es un archivo de inventario (Excel)
            is_inventory = (
                source_type == "inventory" or
                file_type == "excel" or
                ("inventario" in source.lower() if source else False) or
                (".xlsx" in source.lower() if source else False)
            )
            
            if not is_inventory:
                continue
            
            precio_str = doc.metadata.get("precio", "0")
            producto_nombre = doc.metadata.get("producto_nombre", "N/A")
            categoria = doc.metadata.get("categoria", "N/A")
            cantidad = doc.metadata.get("cantidad", "N/A")
            
            # Si metadata está vacío, parsear del content
            if producto_nombre in ["N/A", None, ""] and doc.page_content:
                parsed = _parse_product_from_content(doc.page_content)
                producto_nombre = parsed.get("producto_nombre", "N/A")
                categoria = parsed.get("categoria", "N/A")
                cantidad = parsed.get("cantidad", "N/A")
                precio_str = parsed.get("precio", "0")
            
            # Limpiar y convertir precio
            try:
                # Remover símbolos y espacios
                precio_limpio = precio_str.replace("$", "").replace(",", "").strip()
                precio_num = float(precio_limpio)
                
                # Verificar si está en el rango
                in_range = True
                if precio_min and precio_num < precio_min:
                    in_range = False
                if precio_max and precio_num > precio_max:
                    in_range = False
                
                if in_range:
                    producto = {
                        "nombre": producto_nombre,
                        "categoria": categoria,
                        "cantidad": cantidad,
                        "precio": precio_num
                    }
                    productos.append(producto)
            except (ValueError, AttributeError):
                # Precio no válido, saltar
                continue
        
        # Eliminar duplicados
        seen = set()
        productos_unicos = []
        for p in productos:
            if p["nombre"] not in seen:
                seen.add(p["nombre"])
                productos_unicos.append(p)
        
        # Ordenar por precio
        productos_unicos.sort(key=lambda x: x["precio"])
        
        return {
            "rango_precio": {"min": precio_min, "max": precio_max},
            "productos": productos_unicos,
            "total": len(productos_unicos)
        }
        
    except Exception as e:
        tracer.log(
            operation="PRICE_SEARCH_ERROR",
            message=f"Error buscando por precio: {str(e)}",
            level="ERROR"
        )
        return {
            "error": str(e),
            "rango_precio": {"min": precio_min, "max": precio_max},
            "productos": [],
            "total": 0
        }


def _build_metadata_filters(
    categoria: Optional[str],
    precio_min: Optional[float],
    precio_max: Optional[float]
) -> dict:
    """Construir filtros de metadata (placeholder para futuras versiones)"""
    # Nota: Chroma/LangChain actualmente no soporta where con comparaciones complejas
    # Retornamos un dict para futuro uso
    filters = {}
    
    if categoria:
        filters["categoria"] = categoria
    if precio_min:
        filters["precio_min"] = precio_min
    if precio_max:
        filters["precio_max"] = precio_max
    
    return filters


def _matches_metadata_filters(
    metadata: dict,
    categoria_filtro: Optional[str],
    precio_min: Optional[float],
    precio_max: Optional[float]
) -> bool:
    """Verificar si los metadata cumplen con los filtros"""
    
    # Filtro por categoría
    if categoria_filtro:
        doc_category = metadata.get("categoria", "").lower()
        filter_category = categoria_filtro.lower()
        if filter_category not in doc_category and doc_category not in filter_category:
            return False
    
    # Filtro por precio
    if precio_min is not None or precio_max is not None:
        precio_str = metadata.get("precio", "0")
        try:
            precio_limpio = precio_str.replace("$", "").replace(",", "").strip()
            precio_num = float(precio_limpio)
            
            if precio_min is not None and precio_num < precio_min:
                return False
            if precio_max is not None and precio_num > precio_max:
                return False
        except (ValueError, AttributeError):
            # Precio no válido, excluir
            return False
    
    return True


def _parse_product_from_content(content: str) -> Dict[str, str]:
    """
    Parsear información de producto desde el contenido del documento.
    Usado cuando los metadata están vacíos (archivos Excel antiguos).
    
    Ejemplo de content:
    "Fila 4: Nombre del Producto: Cargador Solar Portátil, Categoría: Electrónica, Cantidad en Stock: 75, Precio Unitario ($): 49.99, Fecha de Ingreso: 2025-09-15"
    """
    result = {
        "producto_nombre": "N/A",
        "categoria": "N/A",
        "cantidad": "N/A",
        "precio": "N/A"
    }
    
    if not content:
        return result
    
    try:
        # Formato 1: "Nombre del Producto: X, Categoría: Y, Cantidad: Z, Precio: W"
        # Buscar cada campo individualmente
        patterns = {
            "producto_nombre": [
                r'Nombre del Producto:\s*([^,]+)',
                r'Producto:\s*([^,|]+)',
                r'nombre:\s*([^,|]+)'
            ],
            "categoria": [
                r'Categoría:\s*([^,]+)',
                r'Categoria:\s*([^,|]+)',
                r'categoría:\s*([^,|]+)'
            ],
            "cantidad": [
                r'Cantidad en Stock:\s*([^,]+)',
                r'Cantidad:\s*([^,|]+)',
                r'cantidad:\s*([^,|]+)'
            ],
            "precio": [
                r'Precio Unitario.*?:\s*([^,]+)',
                r'Precio:\s*([^,|]+)',
                r'precio:\s*([^,|]+)'
            ]
        }
        
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                    # Limpiar espacios extra y caracteres especiales
                    value = value.rstrip(',')
                    if value and value != "":
                        result[key] = value
                        break
        
        # Si no encontramos con patrones, intentar formato libre
        if all(v == "N/A" for v in result.values()):
            # Extraer números que puedan ser precio o cantidad
            numbers = re.findall(r'(\d+(?:\.\d+)?)', content)
            
            # Intentar identificar estructura básica por separadores
            parts = content.split(',')
            for part in parts:
                part = part.strip()
                if ':' in part:
                    key, value = part.split(':', 1)
                    key = key.strip().lower()
                    value = value.strip()
                    
                    if 'nombre' in key or 'producto' in key:
                        result["producto_nombre"] = value
                    elif 'categor' in key:
                        result["categoria"] = value
                    elif 'cantidad' in key or 'stock' in key:
                        result["cantidad"] = value
                    elif 'precio' in key:
                        result["precio"] = value
        
    except Exception as e:
        # Si falla el parseo, retornar N/A
        pass
    
    return result


def _get_all_categories(vectordb) -> Dict[str, Any]:
    """Obtener todas las categorías disponibles en el inventario"""
    
    try:
        # Buscar todos los productos (con una query genérica)
        results = vectordb.similarity_search_with_score(
            query="productos disponibles inventario stock categoría",
            k=999  # Obtener todos los productos posibles
        )
        
        # Extraer categorías únicas con conteo
        categorias_dict = {}
        
        for doc, distance in results:
            # IMPORTANTE: Solo incluir productos de archivos Excel/inventario
            source_type = doc.metadata.get("source_type", "")
            file_type = doc.metadata.get("file_type", "")
            source = doc.metadata.get("source", "")
            
            # Solo procesar si es un archivo de inventario (Excel)
            is_inventory = (
                source_type == "inventory" or
                file_type == "excel" or
                ("inventario" in source.lower() if source else False) or
                (".xlsx" in source.lower() if source else False)
            )
            
            if not is_inventory:
                continue
            
            categoria = doc.metadata.get("categoria", "")
            
            if categoria and categoria != "N/A" and categoria != "":
                # Validar que es una categoría válida (nombres cortos, no texto largo)
                if len(categoria) < 100 and categoria not in ["Sin categoría", "N/A"]:
                    if categoria not in categorias_dict:
                        categorias_dict[categoria] = {
                            "categoria": categoria,
                            "cantidad_productos": 0
                        }
                    categorias_dict[categoria]["cantidad_productos"] += 1
        
        # Convertir a lista y ordenar por cantidad de productos
        categorias_list = list(categorias_dict.values())
        categorias_list.sort(key=lambda x: x["cantidad_productos"], reverse=True)
        
        tracer.log(
            operation="GET_ALL_CATEGORIES",
            message=f"Encontradas {len(categorias_list)} categorías",
            metadata={"total_categorias": len(categorias_list)},
            level="INFO"
        )
        
        return {
            "categorias": categorias_list,
            "total": len(categorias_list)
        }
        
    except Exception as e:
        tracer.log(
            operation="GET_ALL_CATEGORIES_ERROR",
            message=f"Error obteniendo categorías: {str(e)}",
            level="ERROR"
        )
        return {
            "categorias": [],
            "total": 0,
            "error": str(e)
        }


def _get_all_products(vectordb) -> Dict[str, Any]:
    """Obtener todos los productos disponibles en el inventario"""
    
    try:
        # Buscar todos los productos (con una query genérica que capture todo)
        results = vectordb.similarity_search_with_score(
            query="productos disponibles en inventario stock catalogo catálogo",
            k=999  # Obtener todos los productos posibles
        )
        
        # Extraer todos los productos con sus detalles
        productos = []
        
        for doc, distance in results:
            # IMPORTANTE: Solo incluir productos de archivos Excel/inventario
            # Excluir documentos de texto como preguntas_frecuentes, políticas, etc.
            source_type = doc.metadata.get("source_type", "")
            file_type = doc.metadata.get("file_type", "")
            source = doc.metadata.get("source", "")
            
            # Solo procesar si es un archivo de inventario (Excel) o tiene metadata de producto
            is_inventory = (
                source_type == "inventory" or
                file_type == "excel" or
                ("inventario" in source.lower() if source else False) or
                ".xlsx" in source.lower() if source else False
            )
            
            if not is_inventory:
                continue
            
            # Extraer información de metadata
            producto_nombre = doc.metadata.get("producto_nombre")
            categoria = doc.metadata.get("categoria")
            cantidad = doc.metadata.get("cantidad")
            precio = doc.metadata.get("precio")
            
            # Si metadata está vacío, parsear del content
            if producto_nombre in ["N/A", None, ""] and doc.page_content:
                parsed = _parse_product_from_content(doc.page_content)
                producto_nombre = parsed.get("producto_nombre", "N/A")
                categoria = parsed.get("categoria", "N/A")
                cantidad = parsed.get("cantidad", "N/A")
                precio = parsed.get("precio", "N/A")
            
            # Solo agregar productos válidos (no N/A)
            # Y asegurarse de que no sean líneas de texto largo (productos reales son nombres cortos)
            if producto_nombre not in ["N/A", None, ""]:
                # Validar que es un nombre de producto válido (no texto largo de documentos)
                is_valid_product_name = (
                    len(producto_nombre) < 200 and  # Nombres de productos no son muy largos
                    not producto_nombre.startswith('-') and  # No bullet points
                    '\n' not in producto_nombre  # No múltiples líneas
                )
                
                if is_valid_product_name:
                    producto = {
                        "nombre": producto_nombre,
                        "categoria": categoria if categoria != "N/A" else "Sin categoría",
                        "cantidad": cantidad if cantidad != "N/A" else "N/A",
                        "precio": precio if precio != "N/A" else "N/A"
                    }
                    productos.append(producto)
        
        # Eliminar duplicados basados en nombre
        seen = set()
        productos_unicos = []
        for p in productos:
            if p["nombre"] not in seen:
                seen.add(p["nombre"])
                productos_unicos.append(p)
        
        # Ordenar por nombre alfabéticamente
        productos_unicos.sort(key=lambda x: x["nombre"])
        
        tracer.log(
            operation="GET_ALL_PRODUCTS",
            message=f"Encontrados {len(productos_unicos)} productos en inventario",
            metadata={"total_productos": len(productos_unicos)},
            level="INFO"
        )
        
        return {
            "productos": productos_unicos,
            "total": len(productos_unicos)
        }
        
    except Exception as e:
        tracer.log(
            operation="GET_ALL_PRODUCTS_ERROR",
            message=f"Error obteniendo todos los productos: {str(e)}",
            level="ERROR"
        )
        return {
            "productos": [],
            "total": 0,
            "error": str(e)
        }


# Helper function para usar directamente desde el agente
def check_product(product_name: str, umbral: float = 0.7) -> Dict[str, Any]:
    """
    Helper simplificado para verificar un producto
    
    Args:
        product_name: Nombre del producto a verificar
        umbral: Umbral de similitud (default: 0.7)
        
    Returns:
        dict: Resultado de la verificación
    """
    return check_product_existence(
        query=product_name,
        search_type="producto",
        umbral_similitud=umbral
    )


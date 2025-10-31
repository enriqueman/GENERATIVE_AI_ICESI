"""
Agente RAG para el sistema de EcoMarket
Maneja la lógica de recuperación y generación de respuestas
"""

import os
import sys
import time
import re

# Agregar src al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.vector_functions import (
    load_retriever,
    get_combined_retriever,
    generate_answer_from_context
)
from utils.tracing import tracer, log_retrieval, log_generation
from tools.document_retriever import DocumentRetriever
from tools.query_processor import QueryProcessor
from tools.product_checker import check_product_existence
from tools.ticket_manager import (
    crear_ticket_devolucion, crear_ticket_compra, generar_guia_de_seguimiento,
    consulta_seguimiento, obtener_factura, crear_ticket_queja_reclamo,
    generar_etiqueta_devolucion, consultar_ticket, extraer_info_cliente
)

# Importar traceable para unificar trazas
try:
    from langsmith import traceable
    from contextlib import nullcontext
    TRACEABLE_AVAILABLE = True
except ImportError:
    # Si no está disponible, crear decorador vacío
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    from contextlib import nullcontext
    TRACEABLE_AVAILABLE = False


class EcoMarketAgent:
    """
    Agente RAG para responder consultas de clientes usando documentos internos
    """
    
    def __init__(self):
        """Inicializar el agente RAG"""
        self.retriever = None
        self.initialized = False
        
        # Inicializar herramientas
        self.document_retriever = DocumentRetriever()
        self.query_processor = QueryProcessor()
        
        self._initialize()
    
    def _initialize(self):
        """Inicializar el retriever"""
        try:
            # Verificar si existe la base de datos ChromaDB
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            chroma_path = os.path.join(base_dir, "static/persist/chroma.sqlite3")
            
            if os.path.exists(chroma_path):
                self.retriever = get_combined_retriever()
                self.initialized = True
                tracer.log(
                    operation="AGENT_INITIALIZATION",
                    message="Agente RAG inicializado exitosamente",
                    metadata={"initialized": True},
                    level="SUCCESS"
                )
            else:
                self.initialized = False
                tracer.log(
                    operation="AGENT_INITIALIZATION",
                    message="Base de datos vectorial no encontrada",
                    metadata={"chroma_path": chroma_path},
                    level="WARNING"
                )
        except Exception as e:
            self.initialized = False
            tracer.log(
                operation="AGENT_INITIALIZATION",
                message=f"Error inicializando agente: {str(e)}",
                metadata={"error": str(e)},
                level="ERROR"
            )
    
    def is_ready(self):
        """Verificar si el agente está listo para responder"""
        return self.initialized and self.retriever is not None
    
    @traceable(name="EcoMarketAgent.process_query")
    def process_query(self, question: str, enable_logging: bool = False, trace_id: str = None) -> str:
        """
        Procesar una consulta del usuario usando herramientas
        
        Args:
            question (str): Pregunta del usuario
            enable_logging (bool): Habilitar logging detallado
            trace_id (str): ID del trace para agrupar logs
            
        Returns:
            str: Respuesta del agente
        """
        if not self.is_ready():
            return self._get_fallback_response()
        
        try:
            # Paso 1: Clasificar la consulta
            query_info = self.query_processor.classify_query(question)
            
            tracer.log(
                operation="AGENT_PROCESSING",
                message=f"Procesando consulta tipo: {query_info['category']}",
                metadata=query_info,
                level="INFO",
                trace_id=trace_id
            )
            
            # Paso 2: Detectar si es consulta de ticket/servicio
            if self._is_ticket_query(question, query_info):
                response = self._handle_ticket_query(question, query_info, enable_logging, trace_id)
                return response
            
            # Paso 3: Detectar si es consulta de producto
            if self._is_product_query(question, query_info):
                response = self._handle_product_query(question, query_info, enable_logging, trace_id)
                return response
            
            # Paso 4: Si es una consulta de lista, detectar si es sobre productos
            if query_info['is_list_query']:
                # Verificar si es lista de productos o lista general
                if self._is_product_list_query(question, query_info):
                    # Usar herramienta de verificación de productos
                    response = self._handle_product_query(question, query_info, enable_logging, trace_id)
                else:
                    # Usar estrategia de lista general (RAG estándar)
                    response = self._handle_list_query(question, query_info, enable_logging, trace_id)
            else:
                # Paso 4: Usar estrategia estándar con herramientas
                response = self._handle_standard_query(question, query_info, enable_logging, trace_id)
            
            return response
            
        except Exception as e:
            tracer.log(
                operation="RAG_ERROR",
                message=f"Error procesando consulta: {str(e)}",
                metadata={"question": question[:100], "error": str(e)},
                level="ERROR",
                trace_id=trace_id
            )
            
            return self._get_error_response(str(e))
    
    @traceable(name="RAGAgent._handle_list_query")
    def _handle_list_query(self, question: str, query_info: dict, enable_logging: bool, trace_id: str = None) -> str:
        """Manejar consultas que solicitan listas de productos"""
        # Generar múltiples variaciones de la consulta
        queries = self.query_processor.generate_search_queries(question)
        
        # Recuperar documentos para cada variación
        all_documents = []
        for query_variant in queries:
            docs = self.document_retriever.search(query_variant)
            all_documents.extend(docs)
        
        # Generar respuesta con el contexto ampliado
        response = generate_answer_from_context(
            self.retriever,
            question,
            enable_logging=enable_logging
        )
        
        return response
    
    @traceable(name="RAGAgent._handle_standard_query")
    def _handle_standard_query(self, question: str, query_info: dict, enable_logging: bool, trace_id: str = None) -> str:
        """Manejar consultas estándar"""
        # Buscar documentos relevantes
        search_results = self.document_retriever.search(question)
        
        # Generar respuesta usando RAG estándar
        response = generate_answer_from_context(
            self.retriever,
            question,
            enable_logging=enable_logging
        )
        
        return response
    
    def _is_product_query(self, question: str, query_info: dict) -> bool:
        """Detectar si la consulta es sobre productos específicos"""
        question_lower = question.lower()
        
        # Palabras clave que indican consultas de producto
        product_keywords = [
            "¿tienen", "¿tienes", "¿hay", "¿existe", "¿disponible",
            "producto", "productos", "catalogo", "catálogo", "inventario",
            "en stock", "disponibilidad", "busco", "necesito", "quiero",
            "por categoria", "por categoría", "menos de", "menor a",
            "mayor a", "más de", "precio"
        ]
        
        # Si es categoría producto o contiene keywords
        is_product = query_info.get('category') == 'producto'
        has_keywords = any(keyword in question_lower for keyword in product_keywords)
        
        return is_product or has_keywords
    
    def _is_product_list_query(self, question: str, query_info: dict) -> bool:
        """Detectar si una consulta de lista es sobre productos específicos"""
        question_lower = question.lower()
        
        # Palabras clave específicas de productos
        product_keywords = [
            "producto", "productos", "catalogo", "catálogo", "inventario",
            "en stock", "disponibilidad", "busco", "necesito", "quiero",
            "categoría", "categoria", "precio", "stock", "disponible"
        ]
        
        # Verificar si es categoría producto
        is_product_category = query_info.get('category') == 'producto'
        
        # Verificar keywords de productos
        has_product_keywords = any(keyword in question_lower for keyword in product_keywords)
        
        return is_product_category or has_product_keywords
    
    @traceable(name="RAGAgent._handle_product_query")
    def _handle_product_query(self, question: str, query_info: dict, enable_logging: bool, trace_id: str = None) -> str:
        """Manejar consultas de productos usando la herramienta de verificación"""
        try:
            question_lower = question.lower()
            
            # Determinar tipo de búsqueda
            search_type = "producto"
            categoria_filtro = None
            precio_min = None
            precio_max = None
            
            # Extraer categoría del filtro si existe
            # Primero verificar si pregunta por categorías disponibles (pregunta sobre categorías, no filtro)
            is_asking_about_categories = (
                "qué categor" in question_lower or 
                "que categor" in question_lower or
                "cuales categor" in question_lower or
                "cuáles categor" in question_lower or
                "que tipos" in question_lower or
                "qué tipos" in question_lower
            )
            
            if "categoría" in question_lower or "categoria" in question_lower and not is_asking_about_categories:
                # Buscar palabra después de "categoría" o "de"
                categoria_match = re.search(r'(?:categoría|categoria|de)\s+(\w+)', question_lower)
                if categoria_match:
                    categoria_filtro = categoria_match.group(1).title()
                    search_type = "categoria"
            
            # Si pregunta sobre categorías disponibles, usar búsqueda especial
            if is_asking_about_categories:
                search_type = "todas_categorias"
            
            # Extraer rango de precio
            precio_matches = re.findall(r'(\d+(?:\.\d+)?)', question)
            if precio_matches:
                if "menos de" in question_lower or "menor a" in question_lower:
                    precio_max = float(precio_matches[0])
                elif "más de" in question_lower or "mayor a" in question_lower:
                    precio_min = float(precio_matches[0])
            
            # Detectar si es búsqueda de lista (productos separados por comas, "y", o preguntas de lista)
            is_list_query = (
                "lista" in question_lower or 
                "cuáles" in question_lower or
                "qué productos" in question_lower or
                "muestra" in question_lower or
                query_info.get('is_list_query')
            )
            
            # Detectar si es solicitud de TODOS los productos disponibles
            is_all_products_query = (
                "todos los productos" in question_lower or
                "todos tus productos" in question_lower or
                "todos productos" in question_lower or
                "catálogo completo" in question_lower or
                ("lista" in question_lower and "disponibles" in question_lower) or
                ("lista" in question_lower and "tienes" in question_lower) or
                ("qué productos" in question_lower and "tienes" in question_lower)
            )
            
            # También detectar si hay múltiples productos separados por comas o "y"
            has_multiple_products = (
                question.count(',') > 0 or 
                (question.count(' y ') > 0 or question.count(' y ') > 0)
            )
            
            # Si es solicitud de todos los productos
            if is_all_products_query:
                search_type = "todos_productos"
            # Si es lista de productos específicos
            elif is_list_query and has_multiple_products:
                search_type = "lista"
            elif is_list_query:
                # Si es pregunta de lista sin productos específicos, también retornar todos
                search_type = "todos_productos"
            
            # Ejecutar búsqueda de producto
            result = check_product_existence(
                query=question,
                search_type=search_type,
                categoria_filtro=categoria_filtro,
                precio_min=precio_min,
                precio_max=precio_max,
                umbral_similitud=0.7
            )
            
            # Formatear respuesta según el tipo de resultado
            if search_type == "producto":
                response = self._format_single_product_response(result)
            elif search_type == "lista":
                response = self._format_list_product_response(result)
            elif search_type == "categoria":
                response = self._format_category_response(result)
            elif search_type == "todas_categorias":
                response = self._format_all_categories_response(result)
            elif search_type == "todos_productos":
                response = self._format_all_products_response(result)
            else:
                # Respuesta estándar con RAG
                response = generate_answer_from_context(
                    self.retriever,
                    question,
                    enable_logging=enable_logging
                )
            
            tracer.log(
                operation="PRODUCT_QUERY",
                message=f"Consulta de producto procesada: {search_type}",
                metadata={"search_type": search_type, "result": result},
                level="INFO"
            )
            
            return response
            
        except Exception as e:
            tracer.log(
                operation="PRODUCT_QUERY_ERROR",
                message=f"Error en consulta de producto: {str(e)}",
                level="ERROR"
            )
            # Fallback a RAG estándar
            return generate_answer_from_context(
                self.retriever,
                question,
                enable_logging=enable_logging
            )
    
    def _format_single_product_response(self, result: dict) -> str:
        """Formatear respuesta para un producto individual"""
        if result.get('existe'):
            nombre = result.get('producto_nombre', 'Producto')
            categoria = result.get('categoria', 'N/A')
            cantidad = result.get('cantidad', 'N/A')
            precio = result.get('precio', 'N/A')
            
            response = f"""
✅ **Producto Encontrado:**

📦 **{nombre}**
- Categoría: {categoria}
- Cantidad en Stock: {cantidad} unidades
- Precio: ${precio}

¿Te gustaría más información sobre este producto?
"""
            
            # Agregar matches alternativos si existen
            if result.get('matches_alternativos'):
                response += "\n\n📋 **Productos alternativos similares:**\n"
                for alt in result['matches_alternativos'][:3]:  # Máximo 3 alternativas
                    response += f"- {alt['producto_nombre']} (Categoría: {alt['categoria']}, Precio: ${alt['precio']})\n"
            
            return response
        else:
            return f"""
❌ **Producto no encontrado**

No encontramos el producto que buscas en nuestro inventario.

¿Podrías intentar con:
- Otro nombre o descripción
- Buscar por categoría
- O contactarnos directamente:
  📧 soporte@ecomarket.com
  📞 +57 324 456 4450
"""
    
    def _format_list_product_response(self, result: dict) -> str:
        """Formatear respuesta para lista de productos"""
        resultados = result.get('resultados', [])
        total_encontrados = result.get('total_encontrados', 0)
        total_buscados = result.get('total_buscados', 0)
        
        if total_encontrados == 0:
            return """
❌ **No se encontraron productos**

No se encontraron productos en nuestro inventario.

¿Podrías intentar con otros términos de búsqueda?
"""
        
        response = f"""
📋 **Resultados de Búsqueda:**

Encontrados {total_encontrados} de {total_buscados} productos buscados:

"""
        for idx, producto in enumerate(resultados, 1):
            if producto.get('existe'):
                det = producto.get('detalles_match', {})
                response += f"{idx}. ✅ **{producto.get('producto_ingresado')}**\n"
                response += f"   → {det.get('producto_nombre', 'Producto encontrado')}\n"
                response += f"   - Categoría: {det.get('categoria', 'N/A')}\n"
                response += f"   - Stock: {det.get('cantidad', 'N/A')}\n"
                response += f"   - Precio: ${det.get('precio', 'N/A')}\n\n"
            else:
                response += f"{idx}. ❌ **{producto.get('producto_ingresado')}** (No encontrado)\n\n"
        
        return response
    
    def _format_category_response(self, result: dict) -> str:
        """Formatear respuesta para búsqueda por categoría"""
        productos = result.get('productos', [])
        total = result.get('total', 0)
        categoria = result.get('categoria', 'Productos')
        
        if total == 0:
            return f"""
❌ **No se encontraron productos**

No hay productos en la categoría '{categoria}' actualmente disponibles.
"""
        
        response = f"""
📦 **Productos en categoría: {categoria}**

Encontrados {total} productos:

"""
        for idx, producto in enumerate(productos, 1):
            response += f"{idx}. **{producto.get('nombre', 'Producto')}**\n"
            response += f"   - Stock: {producto.get('cantidad', 'N/A')} unidades\n"
            response += f"   - Precio: ${producto.get('precio', 'N/A')}\n\n"
        
        return response
    
    def _format_all_categories_response(self, result: dict) -> str:
        """Formatear respuesta para listar todas las categorías disponibles"""
        categorias = result.get('categorias', [])
        total = result.get('total', 0)
        
        if total == 0:
            return """
❌ **No se encontraron categorías**

No hay categorías disponibles en nuestro inventario actual.
"""
        
        response = """
📦 **Categorías Disponibles:**

Tienes {total} categorías de productos:

""".format(total=total)
        
        for idx, cat in enumerate(categorias, 1):
            cat_name = cat.get('categoria', 'Sin categoría')
            cat_count = cat.get('cantidad_productos', 0)
            response += f"{idx}. **{cat_name}** ({cat_count} productos)\n"
        
        response += "\n💡 *Pregúntame por productos de una categoría específica para ver más detalles*"
        
        return response
    
    def _format_all_products_response(self, result: dict) -> str:
        """Formatear respuesta para listar todos los productos disponibles"""
        productos = result.get('productos', [])
        total = result.get('total', 0)
        
        if total == 0:
            return """
❌ **No se encontraron productos**

No hay productos disponibles en nuestro inventario actual.
"""
        
        response = f"""
📦 **Catálogo Completo - {total} Productos Disponibles**

"""
        
        # Agrupar por categoría para mejor visualización
        por_categoria = {}
        for producto in productos:
            categoria = producto.get('categoria', 'Sin categoría')
            if categoria not in por_categoria:
                por_categoria[categoria] = []
            por_categoria[categoria].append(producto)
        
        # Formatear por categorías
        for idx, (categoria, prods) in enumerate(por_categoria.items(), 1):
            response += f"\n### {categoria} ({len(prods)} productos)\n\n"
            
            for prod in prods:
                nombre = prod.get('nombre', 'Producto')
                cantidad = prod.get('cantidad', 'N/A')
                precio = prod.get('precio', 'N/A')
                
                # Mostrar como lista numerada
                response += f"**{nombre}**\n"
                response += f"- Stock: {cantidad} unidades\n"
                response += f"- Precio: ${precio}\n\n"
        
        response += "\n💡 *¿Te interesa algún producto en particular? Pregúntame por más detalles*"
        
        return response
    
    def _is_ticket_query(self, question: str, query_info: dict) -> bool:
        """Detectar si la consulta requiere crear o consultar un ticket"""
        import re
        
        question_lower = question.lower()
        
        # DETECCIÓN PRIORITARIA: Patrón de número de ticket (TKT-XXXXX-XXXX)
        ticket_number_pattern = r'TKT[-]\d+[-][A-Z0-9]+'
        if re.search(ticket_number_pattern, question, re.IGNORECASE):
            return True
        
        # DETECCIÓN: Palabras clave de consulta de ticket existente
        consult_ticket_keywords = [
            "consultar", "ver", "mostrar", "buscar", "encontrar",
            "estado del", "información del", "datos del",
            "mi ticket", "mis tickets", "historial",
            "qué estado", "está mi ticket"
        ]
        has_consult_keywords = any(keyword in question_lower for keyword in consult_ticket_keywords)
        
        # Si menciona "ticket" con palabras de consulta, es consulta de ticket
        if "ticket" in question_lower and has_consult_keywords:
            return True
        
        # DETECCIÓN: Palabras clave de creación de ticket
        create_ticket_keywords = [
            "devolver", "devolución", "retornar", "devolver producto",
            "reclamo", "queja", "felicitación", "felicitacion",
            "solicitar devolución", "hacer devolución", "procesar devolución",
            "guía de seguimiento", "seguimiento de pedido", "rastrear pedido",
            "consultar factura", "obtener factura", "solicitar factura",
            "hacer pedido", "comprar productos", "realizar compra"
        ]
        has_create_keywords = any(keyword in question_lower for keyword in create_ticket_keywords)
        
        # DETECCIÓN: Verbos de acción que indican creación
        action_verbs = ["devolver", "solicitar", "hacer", "comprar", "pedir", "obtener"]
        has_action_verb = any(verb in question_lower for verb in action_verbs)
        has_ticket_context = (
            "producto defectuoso" in question_lower or
            "producto roto" in question_lower or
            "necesito devolver" in question_lower or
            "quiero devolver" in question_lower
        )
        
        if has_create_keywords or (has_action_verb and has_ticket_context):
            return True
        
        # Detectar categorías específicas (menos prioridad)
        is_ticket_category = query_info.get('category') in ['devolución', 'envío', 'contacto']
        
        return is_ticket_category
    
    @traceable(name="RAGAgent._handle_ticket_query")
    def _handle_ticket_query(self, question: str, query_info: dict, enable_logging: bool, trace_id: str = None) -> str:
        """Manejar consultas que requieren crear o consultar tickets"""
        import re
        
        question_lower = question.lower()
        
        try:
            # DETECCIÓN INTELIGENTE DE INTENCIÓN
            # Prioridad 1: ¿Tiene número de ticket en el texto?
            ticket_number_pattern = r'TKT[-]\d+[-][A-Z0-9]+'
            ticket_match = re.search(ticket_number_pattern, question, re.IGNORECASE)
            
            if ticket_match:
                # Hay número de ticket → es consulta, no creación
                return self._handle_consulta_ticket(question, query_info)
            
            # Prioridad 2: ¿Palabras clave explícitas de consulta?
            consult_keywords = [
                "consultar", "ver", "mostrar", "buscar", "encontrar",
                "estado del", "información del", "datos del",
                "mi ticket", "mis tickets", "historial de",
                "qué estado", "está mi ticket"
            ]
            is_consultation = any(keyword in question_lower for keyword in consult_keywords) and "ticket" in question_lower
            
            if is_consultation:
                return self._handle_consulta_ticket(question, query_info)
            
            # Prioridad 3: Palabras clave de creación de ticket
            creation_keywords = [
                "devolver", "devolución", "retornar",
                "necesito devolver", "quiero devolver", "solicitar devolución",
                "reclamo", "queja", "felicitación"
            ]
            is_creation = any(keyword in question_lower for keyword in creation_keywords)
            
            if not is_creation:
                # No es claro si es creación o consulta, intentar ambos
                # Pero primero verificar si menciona "ticket" sin verbo de acción
                if "ticket" in question_lower:
                    # Asumir que es consulta si no hay verbo de acción claro
                    return self._handle_consulta_ticket(question, query_info)
            
            # Si llegamos aquí, es creación de ticket
            # Extraer información del cliente (de la consulta y de memoria si existe)
            cliente_info = self._get_cliente_info(question, trace_id)
            
            # Detectar tipo de ticket
            if any(word in question_lower for word in ["devolver", "devolución", "retornar"]):
                return self._handle_devolucion_ticket(question, cliente_info, query_info)
            
            elif any(word in question_lower for word in ["seguimiento", "rastrear", "donde está"]):
                return self._handle_seguimiento_query(question, cliente_info, query_info)
            
            elif any(word in question_lower for word in ["factura", "recibo"]):
                return self._handle_factura_query(question, cliente_info, query_info)
            
            elif any(word in question_lower for word in ["comprar", "pedir", "ordenar", "quiero"]):
                return self._handle_compra_ticket(question, cliente_info, query_info)
            
            elif any(word in question_lower for word in ["reclamo", "queja", "felicitación"]):
                return self._handle_queja_ticket(question, cliente_info, query_info)
            
            else:
                # Respuesta genérica
                return self._get_ticket_help_response()
                
        except Exception as e:
            tracer.log(
                operation="TICKET_QUERY_ERROR",
                message=f"Error manejando consulta de ticket: {str(e)}",
                level="ERROR",
                trace_id=trace_id
            )
            return self._get_error_response(str(e))
    
    def _handle_devolucion_ticket(self, question: str, cliente_info: dict, query_info: dict) -> str:
        """Manejar solicitudes de devolución"""
        try:
            # Extraer información del producto y factura
            import re
            
            # Buscar número de factura
            factura_match = re.search(r'factura\s*[:#]?\s*(\w+)', question, re.IGNORECASE)
            factura_numero = factura_match.group(1) if factura_match else None
            
            # Buscar producto
            producto_match = re.search(r'producto\s*(?:es)?\s*[:]?\s*([\w\s]+)', question, re.IGNORECASE)
            producto_id = producto_match.group(1).strip() if producto_match else "No especificado"
            
            # Motivo básico
            motivo = "Solicitud de devolución"
            if "defectuoso" in question or "roto" in question or "dañado" in question:
                motivo = "Producto defectuoso o dañado"
            elif "talla" in question or "tamaño" in question:
                motivo = "Problema de talla o tamaño"
            elif "no me gustó" in question or "no me gusta" in question:
                motivo = "No quedó conforme con el producto"
            
            # Intentar crear ticket
            result = crear_ticket_devolucion(
                cliente_email=cliente_info.get('email') or "cliente@ejemplo.com",
                cliente_nombre=cliente_info.get('nombre') or "Cliente",
                producto_id=producto_id,
                factura_numero=factura_numero,
                motivo_devolucion=motivo,
                cliente_telefono=cliente_info.get('telefono'),
                notas=f"Consulta: {question}"
            )
            
            if result.get('exito'):
                return result.get('mensaje', 'Ticket creado exitosamente')
            else:
                return f"Hubo un problema: {result.get('mensaje')}"
                
        except Exception as e:
            return "Lo siento, necesito más información. Por favor, proporcione: su email, número de factura y producto a devolver."
    
    def _handle_seguimiento_query(self, question: str, cliente_info: dict, query_info: dict) -> str:
        """Manejar consultas de seguimiento y creación de guías de seguimiento"""
        try:
            import re
            
            question_lower = question.lower()
            
            # Detectar si el usuario quiere CREAR una guía de seguimiento o SOLO CONSULTAR
            create_keywords = ["crear", "generar", "solicitar", "necesito", "quiero", "hacer", "nueva"]
            is_creating = any(keyword in question_lower for keyword in create_keywords) and (
                "guía" in question_lower or "seguimiento" in question_lower
            )
            
            if is_creating:
                # Crear nueva guía de seguimiento
                # Validar que se tenga email del cliente
                if not cliente_info.get('email'):
                    return """
📦 **Crear Guía de Seguimiento**

Para crear una guía de seguimiento, necesito:
- Tu correo electrónico
- Número de pedido (opcional)
- Empresa de envío (opcional)

Por favor, proporciona esta información para procesar tu solicitud.
"""
                
                # Extraer información del pedido
                pedido_match = re.search(r'(?:pedido|orden|compra|ticket)\s*[:#]?\s*([A-Z0-9\-]+)', question, re.IGNORECASE)
                numero_pedido = pedido_match.group(1) if pedido_match else None
                
                # Extraer empresa de envío si se menciona
                empresa_match = re.search(r'(?:empresa|transportadora|envío|envio|courier)\s*(?:es|:)?\s*([\w\s]+)', question, re.IGNORECASE)
                empresa_envio = empresa_match.group(1).strip() if empresa_match else "Por definir"
                
                # Crear ticket de seguimiento
                result = generar_guia_de_seguimiento(
                    cliente_email=cliente_info.get('email'),
                    numero_pedido=numero_pedido or "Sin número de pedido",
                    empresa_envio=empresa_envio
                )
                
                if result.get('exito'):
                    return result.get('mensaje', 'Guía de seguimiento creada exitosamente')
                else:
                    return f"Hubo un problema al crear la guía: {result.get('mensaje', 'Error desconocido')}"
            else:
                # Solo consultar seguimiento existente
                seguimiento_match = re.search(r'(?:seguimiento|guía|número|ticket)\s*[:#]?\s*([A-Z0-9\-]+)', question, re.IGNORECASE)
                numero_seguimiento = seguimiento_match.group(1) if seguimiento_match else None
                
                # También buscar número de ticket
                ticket_match = re.search(r'TKT[-]\d+[-][A-Z0-9]+', question, re.IGNORECASE)
                ticket_number = ticket_match.group(0) if ticket_match else None
                
                if numero_seguimiento:
                    result = consulta_seguimiento(numero_seguimiento=numero_seguimiento)
                    return result.get('mensaje', 'No se encontró información de seguimiento')
                elif ticket_number:
                    result = consulta_seguimiento(ticket_number=ticket_number)
                    return result.get('mensaje', 'No se encontró información de seguimiento')
                else:
                    return "Para consultar el seguimiento, necesito el número de guía o número de ticket. Por favor, proporciónelo."
                
        except Exception as e:
            tracer.log(
                operation="SEGUIMIENTO_QUERY_ERROR",
                message=f"Error manejando consulta de seguimiento: {str(e)}",
                level="ERROR"
            )
            return "Lo siento, no pude procesar tu solicitud de seguimiento."
    
    def _handle_factura_query(self, question: str, cliente_info: dict, query_info: dict) -> str:
        """Manejar solicitudes de factura"""
        try:
            import re
            
            factura_match = re.search(r'factura\s*[:#]?\s*(\w+)', question, re.IGNORECASE)
            factura_numero = factura_match.group(1) if factura_match else None
            
            result = obtener_factura(
                factura_numero=factura_numero,
                cliente_email=cliente_info.get('email')
            )
            
            return result.get('mensaje', 'No se encontró información')
            
        except Exception as e:
            return "Lo siento, necesito más información. Por favor, proporcione su email y número de factura."
    
    def _handle_compra_ticket(self, question: str, cliente_info: dict, query_info: dict) -> str:
        """Manejar solicitudes de compra y crear ticket de compra"""
        try:
            import re
            
            # Extraer información de la compra
            # Buscar productos mencionados
            productos_match = re.search(r'(?:productos?|comprar|quiero|necesito)\s*(?:son|es)?\s*[:]?\s*([^.]+)', question, re.IGNORECASE)
            productos_text = productos_match.group(1).strip() if productos_match else "Productos varios"
            
            # Si hay comas o "y", son múltiples productos
            if ',' in productos_text or ' y ' in productos_text:
                productos = productos_text
            else:
                # Buscar más patrones de productos
                productos_list = re.findall(r'(\w+(?:\s+\w+)*)', productos_text)
                productos = ', '.join(productos_list[:5]) if productos_list else productos_text  # Máximo 5 productos
            
            # Extraer total de la compra
            total_match = re.search(r'(?:total|precio|costo|suma)\s*(?:es|de|:)?\s*\$?\s*(\d+(?:\.\d+)?)', question, re.IGNORECASE)
            total = float(total_match.group(1)) if total_match else None
            
            # Si no hay total, intentar sumar números mencionados
            if total is None:
                numeros = re.findall(r'\$?\s*(\d+(?:\.\d+)?)', question)
                if numeros:
                    # Asumir que el número más grande es el total
                    try:
                        total = max([float(n) for n in numeros])
                    except:
                        total = None
            
            # Validar información mínima requerida
            if not cliente_info.get('email'):
                return """
🛒 **Solicitud de Compra**

Para crear un ticket de compra, necesito:
- Tu correo electrónico
- Los productos que deseas comprar
- El total de la compra (opcional)

Por favor, proporciona esta información para procesar tu solicitud.
"""
            
            # Crear ticket de compra
            result = crear_ticket_compra(
                cliente_email=cliente_info.get('email'),
                cliente_nombre=cliente_info.get('nombre') or "Cliente",
                productos=productos[:200],  # Limitar longitud
                total=total or 0.0,
                cliente_telefono=cliente_info.get('telefono'),
                notas=f"Solicitud de compra: {question[:200]}"
            )
            
            if result.get('exito'):
                return result.get('mensaje', 'Ticket de compra creado exitosamente')
            else:
                return f"Hubo un problema al crear el ticket: {result.get('mensaje', 'Error desconocido')}"
                
        except Exception as e:
            tracer.log(
                operation="COMPRA_TICKET_ERROR",
                message=f"Error creando ticket de compra: {str(e)}",
                level="ERROR"
            )
            return """
🛒 **Proceso de Compra**

Lo siento, necesito más información para crear tu ticket de compra:

**Información requerida:**
- Tu correo electrónico
- Nombre de los productos que deseas comprar
- Total de la compra (opcional)

**Ejemplo:**
"Quiero comprar botellas de acero y bolsas reutilizables, mi correo es cliente@ejemplo.com, total $50000"

Si necesitas información sobre productos disponibles, pregúntame por ellos.
"""
    
    def _handle_queja_ticket(self, question: str, cliente_info: dict, query_info: dict) -> str:
        """Manejar quejas, reclamos o felicitaciones"""
        try:
            question_lower = question.lower()
            
            if "queja" in question_lower or "reclamo" in question_lower:
                tipo = "reclamo"
            elif "felicitación" in question_lower or "felicitacion" in question_lower or "me gustó" in question_lower:
                tipo = "felicitacion"
            else:
                tipo = "queja"
            
            result = crear_ticket_queja_reclamo(
                cliente_email=cliente_info.get('email') or "cliente@ejemplo.com",
                cliente_nombre=cliente_info.get('nombre') or "Cliente",
                tipo_queja=tipo,
                descripcion=question,
                cliente_telefono=cliente_info.get('telefono')
            )
            
            return result.get('mensaje', 'Ticket creado exitosamente')
            
        except Exception as e:
            return "Lo siento, necesito más información. Por favor, proporcione su email y detalles del caso."
    
    @traceable(name="RAGAgent._handle_consulta_ticket")
    def _handle_consulta_ticket(self, question: str, query_info: dict, trace_id: str = None) -> str:
        """Manejar consultas de tickets existentes"""
        try:
            import re
            
            question_lower = question.lower()
            cliente_info = self._get_cliente_info(question, trace_id)
            
            # Buscar número de ticket en la consulta
            ticket_match = re.search(r'ticket\s*(?:número|numero|#)?\s*[:]?\s*([A-Z0-9\-]+)', question, re.IGNORECASE)
            ticket_number = ticket_match.group(1) if ticket_match else None
            
            # Extraer email del cliente
            cliente_email = cliente_info.get('email')
            
            # Consultar tickets
            if ticket_number:
                # Consultar ticket específico
                result = consultar_ticket(ticket_number=ticket_number)
            elif cliente_email:
                # Consultar tickets del cliente por email
                result = consultar_ticket(cliente_email=cliente_email)
            else:
                return """
🔍 **Consulta de Ticket**

Para consultar tus tickets, necesito:
- Tu número de ticket, O
- Tu email registrado

Ejemplos:
- "Consultar mi ticket TKT-1234567890-ABCD1234"
- "Mis tickets con email cliente@ejemplo.com"
"""
            
            if not result.get('exito'):
                return f"""
❌ **No se encontraron tickets**

{result.get('mensaje', 'No se encontraron tickets')}

Por favor, verifica:
- El número de ticket
- Tu email registrado
"""
            
            # Formatear respuesta
            tickets = result.get('tickets', [])
            total = result.get('total', 0)
            
            if total == 0:
                return "No se encontraron tickets."
            
            # Construir respuesta formateada
            response = f"""
📋 **Consulta de Tickets**

Se encontraron {total} ticket(s):

"""
            
            for idx, ticket in enumerate(tickets, 1):
                response += f"""
**Ticket #{idx}**
- **Número**: {ticket.get('numero', 'N/A')}
- **Tipo**: {ticket.get('tipo', 'N/A')}
- **Estado**: {ticket.get('estado', 'N/A')}
- **Prioridad**: {ticket.get('prioridad', 'N/A')}
- **Título**: {ticket.get('titulo', 'N/A')}
- **Fecha**: {ticket.get('fecha_creacion', 'N/A')}
"""
                
                # Agregar información adicional según el tipo
                if ticket.get('producto_id') != 'N/A':
                    response += f"- **Producto**: {ticket.get('producto_id')}\n"
                
                if ticket.get('factura_numero') != 'N/A':
                    response += f"- **Factura**: {ticket.get('factura_numero')}\n"
                
                if ticket.get('numero_seguimiento') != 'N/A':
                    response += f"- **Número Seguimiento**: {ticket.get('numero_seguimiento')}\n"
                
                response += "\n"
            
            return response
            
        except Exception as e:
            tracer.log(
                operation="CONSULT_TICKET_ERROR",
                message=f"Error consultando ticket: {str(e)}",
                level="ERROR",
                trace_id=trace_id
            )
            return "Lo siento, hubo un error al consultar los tickets."
    
    def _get_cliente_info(self, question: str, trace_id: str = None) -> dict:
        """
        Obtener información del cliente combinando extracción de texto y memoria de chat
        
        Args:
            question: Consulta del usuario
            trace_id: ID del trace (opcional)
            
        Returns:
            dict: Información del cliente (email, nombre, telefono)
        """
        # Primero extraer del texto
        cliente_info = extraer_info_cliente(question)
        
        # Intentar recuperar de memoria de chat si está disponible
        try:
            from tools.chat_memory import retrieve_chat_memory
            # Usar un session_id por defecto basado en trace_id o generar uno
            session_id = f"session_{trace_id[:8]}" if trace_id else "default_session"
            
            # Intentar recuperar información almacenada previamente
            memory_result = retrieve_chat_memory(session_id, memory_key=None, trace_id=trace_id)
            
            if memory_result.get("found") and memory_result.get("data"):
                memory_data = memory_result.get("data", {})
                
                # Completar campos faltantes con información de memoria
                if not cliente_info.get('email') and memory_data.get('email'):
                    cliente_info['email'] = memory_data.get('email')
                if not cliente_info.get('nombre') and memory_data.get('nombre'):
                    cliente_info['nombre'] = memory_data.get('nombre')
                if not cliente_info.get('telefono') and memory_data.get('telefono'):
                    cliente_info['telefono'] = memory_data.get('telefono')
        except Exception as e:
            # Si falla la recuperación de memoria, usar solo la extracción de texto
            pass
        
        return cliente_info
    
    def _get_ticket_help_response(self) -> str:
        """Respuesta de ayuda para tickets"""
        return """
📋 **Atención al Cliente**

Puedo ayudarte con:
- ✅ Devoluciones de productos
- ✅ Consulta de seguimiento de pedidos
- ✅ Obtención de facturas
- ✅ Quejas, reclamos y felicitaciones
- ✅ Gestión de compras
- ✅ Consultar estado de tus tickets

¿En qué puedo asistirte hoy?
"""
    
    def _get_fallback_response(self) -> str:
        """Obtener respuesta de respaldo cuando el agente no está disponible"""
        return """
        🙏 Disculpa, actualmente estamos configurando nuestro sistema de respuestas automáticas.
        
        Por favor, contacta directamente con nuestro equipo de soporte:
        - 📧 Email: soporte@ecomarket.com
        - 📞 Teléfono: +57 324 456 4450
        - ⏰ Horario: Lunes a Viernes 9:00 AM - 6:00 PM
        """
    
    def _get_error_response(self, error_msg: str) -> str:
        """Obtener respuesta de error"""
        return """
        😔 Lo siento, tuve un problema al procesar tu consulta.
        
        Por favor, intenta nuevamente o contacta a nuestro equipo:
        - 📧 soporte@ecomarket.com
        - 📞 +57 324 456 4450
        """
    
    def get_system_status(self) -> dict:
        """Obtener estado del sistema del agente"""
        status = {
            "initialized": self.initialized,
            "ready": self.is_ready(),
            "retriever_available": self.retriever is not None
        }
        
        # Agregar información adicional si está disponible
        if self.is_ready():
            status["status"] = "operational"
            status["message"] = "Agente listo para responder consultas"
        else:
            status["status"] = "not_initialized"
            status["message"] = "Agente no puede responder - base de datos no disponible"
        
        return status

# Instancia global del agente (singleton)
_agent_instance = None

def get_agent() -> EcoMarketAgent:
    """Obtener instancia global del agente (singleton pattern)"""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = EcoMarketAgent()
    return _agent_instance


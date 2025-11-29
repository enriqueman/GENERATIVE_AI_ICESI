"""
Agente Orquestador - Analiza consultas y decide qué hacer
Responsabilidad: Reasoning y toma de decisiones
"""

import os
import sys
import json
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.tracing import tracer
from templates.agent_reasoning import get_agent_reasoning_prompt, get_reasoning_prompt
from agents.rag_agent import PosgradoAgent
from tools.chat_memory import store_chat_memory, retrieve_chat_memory, extract_user_info, get_context_for_query
from tools.otp_auth import send_otp_to_user, verify_otp_code, check_authentication_status

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

try:
    from langsmith import traceable, trace
    TRACEABLE_AVAILABLE = True
    TRACE_AVAILABLE = True
except ImportError:
    TRACEABLE_AVAILABLE = False
    TRACE_AVAILABLE = False
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    trace = None


class OrchestratorAgent:
    """
    Agente Orquestador que analiza consultas y decide qué herramientas usar.
    Su función es hacer reasoning y orquestar las herramientas.
    
    ⚠️ ADVERTENCIA CRÍTICA - SISTEMA DE TRAZAS UNIFICADAS:
    Este agente implementa un sistema de trazas unificadas para LangSmith.
    
    PUNTO DE ENTRADA PRINCIPAL:
    - SIEMPRE usar process_query() como punto de entrada - NO llamar analyze_query() o execute_tools() directamente
    - process_query() crea un context manager que agrupa TODAS las trazas en una sola
    
    ESTRUCTURA DE TRAZAS:
    - process_query() → context manager padre (with trace())
    - analyze_query() → tiene @traceable, se agrupa bajo el padre
    - execute_tools() → llama a _execute_tools_internal() que tiene @traceable, se agrupa bajo el padre
    - Todas las herramientas y agentes llamados también se agrupan automáticamente
    
    REGLAS CRÍTICAS:
    1. NO crear context managers adicionales (with trace()) dentro de los métodos
    2. NO remover los decoradores @traceable - son necesarios para que aparezcan en LangSmith
    3. NO llamar analyze_query() o execute_tools() directamente desde fuera - usar process_query()
    4. Si necesitas agregar nuevas funciones con trazas, usar @traceable pero NO crear context managers
    """
    
    def __init__(self):
        """Inicializar el agente orquestador"""
        self.llm_reasoning = None
        self.rag_agent = PosgradoAgent()
        self._initialize()
    
    def _initialize(self):
        """Inicializar el LLM para reasoning"""
        if not LLM_AVAILABLE:
            print("[WARNING]  LLM no disponible para reasoning")
            return
        
        try:
            from utils.vector_functions import env
            
            # LLM específico para reasoning - temperatura muy baja para precisión
            self.llm_reasoning = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=env("OPENAI_API_KEY"),
                temperature=0.1  # Muy baja temperatura para reasoning preciso
            )
            print("[OK] Orchestrator Agent inicializado")
        except Exception as e:
            print(f"[WARNING]  Error inicializando LLM para reasoning: {e}")
            self.llm_reasoning = None
    
    def is_ready(self):
        """Verificar si el agente está listo"""
        return self.rag_agent.is_ready()
    
    def process_query(self, query: str, trace_id: str = None, is_authenticated: bool = False, session_info: dict = None) -> dict:
        """
        Procesar una consulta completa: analizar y ejecutar herramientas.
        Este método envuelve todo en una traza unificada.
        
        ⚠️ ADVERTENCIA CRÍTICA - SISTEMA DE TRAZAS:
        Este método es el PUNTO DE ENTRADA PRINCIPAL para el sistema de trazas unificadas.
        - NO crear context managers `with trace()` adicionales dentro de este método o sus llamados
        - NO llamar directamente a `analyze_query()` o `execute_tools()` desde fuera de este método
        - Este context manager agrupa TODAS las trazas de agentes y herramientas en LangSmith
        - Si necesitas procesar una consulta, SIEMPRE usa este método, no los métodos internos
        
        Args:
            query: Consulta del usuario
            trace_id: ID del trace para agrupar logs
            is_authenticated: Si el usuario está autenticado
            session_info: Información de sesión
            
        Returns:
            dict: Resultados completos con análisis y ejecución de herramientas
        """
        # ⚠️ ADVERTENCIA: Este context manager es CRÍTICO para agrupar todas las trazas
        # NO crear context managers adicionales dentro de los métodos llamados
        # NO modificar esta estructura sin entender completamente el sistema de trazas
        if TRACE_AVAILABLE and trace:
            project_name = os.getenv("LANGCHAIN_PROJECT", "ecomarket-agent")
            with trace(
                name="OrchestratorAgent.process_query",
                project_name=project_name,
                metadata={"query": query[:200], "trace_id": trace_id}
            ):
                return self._process_query_internal(query, trace_id, is_authenticated, session_info)
        else:
            return self._process_query_internal(query, trace_id, is_authenticated, session_info)
    
    def _process_query_internal(self, query: str, trace_id: str = None, is_authenticated: bool = False, session_info: dict = None) -> dict:
        """
        Procesar consulta internamente (sin context manager).
        
        ⚠️ ADVERTENCIA: Este método se ejecuta DENTRO del context manager de process_query().
        NO agregar context managers aquí - todas las trazas se agrupan automáticamente.
        """
        # Analizar consulta (tiene @traceable - se agrupa bajo la traza padre de process_query)
        analysis = self.analyze_query(query, trace_id, is_authenticated, session_info)
        
        # Ejecutar herramientas (llama a _execute_tools_internal que tiene @traceable)
        tool_results = self.execute_tools(analysis, query, trace_id, session_info)
        
        return {
            "analysis": analysis,
            "tool_results": tool_results
        }
    
    @traceable(name="OrchestratorAgent.analyze_query")
    def analyze_query(self, query: str, trace_id: str = None, is_authenticated: bool = False, session_info: dict = None) -> dict:
        """
        Analizar la consulta del usuario usando reasoning.
        
        ⚠️ ADVERTENCIA - SISTEMA DE TRAZAS:
        Este método tiene el decorador @traceable que crea una traza en LangSmith.
        - Se agrupa automáticamente bajo la traza padre si se llama desde process_query()
        - Si se llama directamente (sin process_query()), creará una traza separada
        - Para mantener trazas unificadas, SIEMPRE usar process_query() como punto de entrada
        - NO remover el decorador @traceable - es necesario para que aparezca en LangSmith
        
        Args:
            query: Consulta del usuario
            trace_id: ID del trace para agrupar logs
            is_authenticated: Si el usuario está autenticado
            
        Returns:
            dict: Análisis con herramientas a usar y datos extraídos
        """
        # CRÍTICO: Si el usuario ya está autenticado, NO debe activar herramientas OTP
        # Saltar completamente la detección de email/OTP y procesar como consulta normal
        if is_authenticated:
            # Usuario autenticado - procesar como consulta normal, NO como autenticación
            # Continuar con el flujo normal de reasoning (LLM o heurística)
            pass
        else:
            # Solo verificar autenticación si el usuario NO está autenticado
            # Primero verificar heurísticamente si es autenticación (prioridad alta)
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, query)
            otp_pattern = r'\b\d{6}\b'
            otp_codes = re.findall(otp_pattern, query)
            
            # Si hay email y código OTP, es verificación - usar heurística directa
            if emails and otp_codes:
                return {
                    "intent": "Verificar código OTP",
                    "tools_needed": ["OTP_VERIFY"],
                    "reasoning": "Usuario proporciona correo y código OTP, necesito verificar",
                    "requires_additional_info": False
                }
            
            # Si hay solo email (sin código), es solicitud de autenticación - usar heurística directa
            if emails and not otp_codes:
                return {
                    "intent": "Autenticarse en el sistema",
                    "tools_needed": ["OTP_SEND"],
                    "reasoning": "Usuario proporciona correo electrónico para autenticación, debo enviar código OTP",
                    "requires_additional_info": False
                }
        
        if not self.llm_reasoning:
            # Si no hay LLM, usar heurística simple
            return self._simple_analysis(query, is_authenticated)
        
        try:
            # Obtener prompt de reasoning (incluir info de autenticación)
            reasoning_prompt_template = get_agent_reasoning_prompt()
            # Agregar contexto de autenticación al prompt
            if is_authenticated:
                auth_context = "\n\n[WARNING] CONTEXTO CRÍTICO DE AUTENTICACIÓN:\nEl usuario YA ESTÁ AUTENTICADO en el sistema. NO debes activar herramientas OTP_SEND o OTP_VERIFY bajo ninguna circunstancia. Procesa la consulta como una solicitud normal del usuario autenticado (puede usar RAG_SEARCH, PRODUCT_SEARCH, TICKET_CREATE, TICKET_QUERY, etc.)."
                # Si hay session_info con email, indicar que el email está disponible automáticamente
                if session_info and session_info.get("email"):
                        auth_context += f"\n\n[OK] INFORMACIÓN DE SESIÓN DISPONIBLE:\nEl usuario autenticado tiene email disponible automáticamente: {session_info.get('email')}. Si la consulta requiere crear un ticket (TICKET_CREATE), NO marques 'requires_additional_info' por falta de email, nombre, número de factura, número de pedido o número de ticket (todos se generan automáticamente). El sistema puede extraer cantidad, productos y dirección de la consulta. SOLO marca 'requires_additional_info: true' si falta información REALMENTE crítica que no se puede inferir ni generar automáticamente. Si el usuario menciona productos, cantidad o dirección en su consulta, esa información está disponible."
                reasoning_prompt_template = reasoning_prompt_template + auth_context
            else:
                auth_context = "\n\n[WARNING] CONTEXTO CRÍTICO DE AUTENTICACIÓN:\nEl usuario NO está autenticado. Si proporciona email/código OTP en la consulta, debes activar herramientas de autenticación (OTP_SEND o OTP_VERIFY)."
                reasoning_prompt_template = reasoning_prompt_template + auth_context
            prompt = ChatPromptTemplate.from_messages([
                ("system", get_reasoning_prompt("system_context")),
                ("human", reasoning_prompt_template)
            ])
            
            # Log inicio de reasoning
            tracer.log(
                operation="LLM_REASONING_START",
                message="Iniciando reasoning con LLM",
                metadata={"query": query[:100]},
                level="INFO",
                trace_id=trace_id
            )
            
            # Generar análisis usando LLM de reasoning
            chain = prompt | self.llm_reasoning
            response = chain.invoke({"user_query": query}).content
            
            # Log reasoning completado
            tracer.log(
                operation="LLM_REASONING_COMPLETE",
                message="Reasoning completado",
                metadata={"response_length": len(response)},
                level="SUCCESS",
                trace_id=trace_id
            )
            
            # Parsear JSON
            try:
                analysis = json.loads(response)
                tracer.log(
                    operation="REASONING_ANALYSIS",
                    message="Análisis de consulta completado por Orchestrator",
                    metadata=analysis,
                    level="INFO",
                    trace_id=trace_id
                )
                return analysis
            except json.JSONDecodeError:
                print("[WARNING]  No se pudo parsear JSON, usando heurística")
                return self._simple_analysis(query, is_authenticated)
                
        except Exception as e:
            tracer.log(
                operation="REASONING_ERROR",
                message=f"Error en reasoning: {str(e)}",
                level="ERROR",
                trace_id=trace_id
            )
            return self._simple_analysis(query, is_authenticated)
    
    def _simple_analysis(self, query: str, is_authenticated: bool = False) -> dict:
        """Análisis heurístico simple cuando no hay LLM"""
        import re
        query_lower = query.lower()
        
        # CRÍTICO: Si el usuario está autenticado, NO detectar email/OTP para autenticación
        # Solo procesar como consulta normal
        if not is_authenticated:
            # Detectar emails y códigos OTP primero (prioridad alta) solo si NO está autenticado
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, query)
            otp_pattern = r'\b\d{6}\b'
            otp_codes = re.findall(otp_pattern, query)
            
            # Si hay email y código OTP, es verificación
            if emails and otp_codes:
                return {
                    "intent": "Verificar código OTP",
                    "tools_needed": ["OTP_VERIFY"],
                    "reasoning": "Usuario proporciona correo y código OTP, necesito verificar",
                    "requires_additional_info": False
                }
            
            # Si hay solo email (sin código), es solicitud de autenticación
            if emails and not otp_codes:
                return {
                    "intent": "Autenticarse en el sistema",
                    "tools_needed": ["OTP_SEND"],
                    "reasoning": "Usuario proporciona correo electrónico para autenticación, debo enviar código OTP",
                    "requires_additional_info": False
                }
        
        # Detección heurística para otras consultas
        # Verificar si hay contexto previo en la query (pasado por retrieve_memory)
        has_context = "Contexto de la sesión" in query or "mentioned_products" in query or "last_intent" in query
        
        # Detectar solicitudes de cantidad/unidades que probablemente se refieren a un producto previo
        quantity_patterns = [
            r'\d+\s*(?:unidades?|packs?|piezas?|cantidad)',
            r'(?:dame|quiero|necesito|por favor)\s+\d+\s*(?:unidades?|packs?|piezas?)',
            r'(?:unidades?|packs?|piezas?)\s+(?:de|del)',
        ]
        is_quantity_request = any(re.search(pattern, query_lower) for pattern in quantity_patterns)
        
        if is_quantity_request and has_context:
            # Si hay solicitud de cantidad Y hay contexto previo, probablemente es continuar con un producto/ticket previo
            if "ticket" in query_lower or "tiket" in query_lower:
                return {
                    "intent": "Completar creación de ticket",
                    "tools_needed": ["TICKET_CREATE"],
                    "reasoning": "Usuario proporciona cantidad para completar ticket mencionado previamente",
                    "requires_additional_info": False
                }
            else:
                # Probablemente se refiere a un producto mencionado anteriormente
                return {
                    "intent": "Continuar con producto mencionado previamente",
                    "tools_needed": ["PRODUCT_SEARCH", "TICKET_CREATE"],
                    "reasoning": "Usuario proporciona cantidad, probablemente para producto del contexto previo",
                    "requires_additional_info": False
                }
        
        if "ticket" in query_lower or "tiket" in query_lower:
            if "consultar" in query_lower or "ver" in query_lower or "TKT-" in query:
                return {
                    "intent": "Consultar ticket existente",
                    "tools_needed": ["TICKET_QUERY"],
                    "reasoning": "Menciona consultar ticket",
                    "requires_additional_info": False
                }
            else:
                return {
                    "intent": "Crear ticket",
                    "tools_needed": ["TICKET_CREATE"],
                    "reasoning": "Menciona ticket sin consulta",
                    "requires_additional_info": True,
                    "missing_info": ["tipo de ticket"]
                }
        
        elif "producto" in query_lower or "inventario" in query_lower:
            return {
                "intent": "Buscar productos",
                "tools_needed": ["PRODUCT_SEARCH"],
                "reasoning": "Pregunta sobre productos",
                "requires_additional_info": False
            }
        
        else:
            return {
                "intent": "Consultar información general",
                "tools_needed": ["RAG_SEARCH"],
                "reasoning": "Consulta general, usar RAG",
                "requires_additional_info": False
            }
    
    def execute_tools(self, analysis: dict, query: str, trace_id: str = None, session_info: dict = None) -> dict:
        """
        Ejecutar las herramientas necesarias según el análisis.
        
        ⚠️ ADVERTENCIA - SISTEMA DE TRAZAS:
        Este método es un wrapper que llama a _execute_tools_internal().
        - NO agregar lógica de context managers aquí
        - NO agregar decoradores @traceable aquí (está en _execute_tools_internal)
        - El context manager de process_query() agrupa todas las trazas automáticamente
        - Para mantener trazas unificadas, SIEMPRE usar process_query() como punto de entrada
        
        Args:
            analysis: Resultado del análisis de reasoning
            query: Consulta original del usuario
            trace_id: ID del trace para agrupar logs
            session_info: Información de sesión (email, name) si el usuario está autenticado
            
        Returns:
            dict: Resultados de las herramientas
        """
        # ⚠️ ADVERTENCIA: Llamar directamente a _execute_tools_internal que tiene @traceable
        # NO crear context managers adicionales aquí - el de process_query() es suficiente
        return self._execute_tools_internal(analysis, query, trace_id, session_info)
    
    @traceable(name="OrchestratorAgent.execute_tools")
    def _execute_tools_internal(self, analysis: dict, query: str, trace_id: str = None, session_info: dict = None) -> dict:
        """
        Ejecutar las herramientas necesarias según el análisis.
        
        ⚠️ ADVERTENCIA - SISTEMA DE TRAZAS:
        Este método tiene el decorador @traceable que crea una traza en LangSmith.
        - Se agrupa automáticamente bajo la traza padre si se llama desde process_query()
        - NO remover el decorador @traceable - es necesario para que aparezca en LangSmith
        - NO crear context managers adicionales aquí - el de process_query() es suficiente
        - Las herramientas llamadas dentro (check_product_existence, QueryProcessor, etc.) 
          también se agrupan automáticamente si tienen @traceable
        
        Args:
            analysis: Resultado del análisis de reasoning
            query: Consulta original del usuario
            trace_id: ID del trace para agrupar logs
            session_info: Información de sesión (email, name) si el usuario está autenticado
            
        Returns:
            dict: Resultados de las herramientas
        """
        tools_used = analysis.get("tools_needed", [])
        results = {
            "tools_used": tools_used,
            "data": {}
        }
        
        for tool in tools_used:
            try:
                # Log inicio de ejecución de herramienta
                tracer.log(
                    operation=f"{tool}_START",
                    message=f"Iniciando ejecución de {tool}",
                    metadata={"query": query[:100]},
                    level="INFO",
                    trace_id=trace_id
                )
                
                if tool == "RAG_SEARCH":
                    tool_result = self._execute_rag_search(query, trace_id)
                    results["data"]["rag_search"] = tool_result
                
                elif tool == "PRODUCT_SEARCH":
                    tool_result = self._execute_product_search(query, trace_id)
                    results["data"]["product_search"] = tool_result
                
                elif tool == "TICKET_CREATE":
                    tool_result = self._execute_ticket_create(query, trace_id, session_info=session_info)
                    results["data"]["ticket_create"] = tool_result
                
                elif tool == "TICKET_QUERY":
                    tool_result = self._execute_ticket_query(query, trace_id, session_info=session_info)
                    results["data"]["ticket_query"] = tool_result
                
                elif tool == "OTP_SEND":
                    tool_result = self._execute_otp_send(query, trace_id)
                    results["data"]["otp_send"] = tool_result
                
                elif tool == "OTP_VERIFY":
                    tool_result = self._execute_otp_verify(query, trace_id)
                    results["data"]["otp_verify"] = tool_result
                
                else:
                    tool_result = {"error": "Herramienta no implementada"}
                    results["data"][tool] = tool_result
                
                # Log éxito de herramienta
                tracer.log(
                    operation=f"{tool}_SUCCESS",
                    message=f"Herramienta {tool} ejecutada exitosamente",
                    metadata={"method": tool_result.get("method", "N/A")},
                    level="SUCCESS",
                    trace_id=trace_id
                )
                    
            except Exception as e:
                tracer.log(
                    operation="TOOL_EXECUTION_ERROR",
                    message=f"Error ejecutando {tool}: {str(e)}",
                    level="ERROR",
                    trace_id=trace_id
                )
                results["data"][tool] = {"error": str(e)}
        
        return results
    
    def _execute_rag_search(self, query: str, trace_id: str = None) -> dict:
        """Ejecutar búsqueda RAG usando el RAG Agent"""
        response = self.rag_agent.process_query(query, enable_logging=False, trace_id=trace_id)
        return {
            "result": response,
            "method": "RAG search in documents"
        }
    
    def _execute_product_search(self, query: str, trace_id: str = None) -> dict:
        """Ejecutar búsqueda de productos usando el RAG Agent"""
        import re
        # Si la query es ambigua (solo cantidad) pero hay contexto, usar producto del contexto
        query_to_use = query
        from tools.chat_memory import retrieve_chat_memory
        session_id = "default_session"
        
        # Si parece ser una solicitud de cantidad sin producto específico, buscar en contexto
        quantity_only = bool(re.search(r'\d+\s*(?:unidades?|packs?|piezas?)', query.lower())) and not any(word in query.lower() for word in ['producto', 'cuaderno', 'bolsa', 'vela', 'pajilla', 'cubierto'])
        
        if quantity_only:
            memory_result = retrieve_chat_memory(session_id, "mentioned_products", trace_id=trace_id)
            if memory_result.get("found") and memory_result.get("memory_value"):
                product_name = memory_result.get("memory_value").split(",")[0].strip()  # Tomar el primer producto
                query_to_use = f"{product_name} {query}"  # Combinar producto del contexto con la query
        
        query_info = self.rag_agent.query_processor.classify_query(query_to_use)
        response = self.rag_agent._handle_product_query(query_to_use, query_info, enable_logging=False, trace_id=trace_id)
        return {
            "result": response,
            "method": "Product search in inventory"
        }
    
    def _execute_ticket_create(self, query: str, trace_id: str = None, session_info: dict = None) -> dict:
        """Ejecutar creación de ticket usando el RAG Agent"""
        import re
        # Enriquecer query con contexto si es necesario
        query_to_use = query
        from tools.chat_memory import retrieve_chat_memory
        session_id = "default_session"
        
        # Si parece ser una solicitud de cantidad para completar ticket, buscar producto en contexto
        quantity_only = bool(re.search(r'\d+\s*(?:unidades?|packs?|piezas?)', query.lower())) and not any(word in query.lower() for word in ['producto', 'cuaderno', 'bolsa', 'vela', 'pajilla', 'cubierto'])
        
        if quantity_only:
            memory_result = retrieve_chat_memory(session_id, "mentioned_products", trace_id=trace_id)
            if memory_result.get("found") and memory_result.get("memory_value"):
                product_name = memory_result.get("memory_value").split(",")[0].strip()
                query_to_use = f"{query}. Producto: {product_name}"
        
        query_info = self.rag_agent.query_processor.classify_query(query_to_use)
        # Pasar session_info al RAG agent para uso automático de email
        response = self.rag_agent._handle_ticket_query(query_to_use, query_info, enable_logging=False, trace_id=trace_id, session_info=session_info)
        return {
            "result": response,
            "method": "Ticket creation"
        }
    
    def _execute_ticket_query(self, query: str, trace_id: str = None, session_info: dict = None) -> dict:
        """Ejecutar consulta de ticket usando el RAG Agent"""
        query_info = self.rag_agent.query_processor.classify_query(query)
        response = self.rag_agent._handle_consulta_ticket(query, query_info, trace_id=trace_id, session_info=session_info)
        return {
            "result": response,
            "method": "Ticket query"
        }
    
    def _execute_otp_send(self, query: str, trace_id: str = None) -> dict:
        """Ejecutar envío de OTP"""
        import re
        
        # Extract email and name from query
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, query)
        email = emails[0] if emails else None
        
        # Try to extract name (improved heuristic)
        name = None
        # Look for patterns like "mi nombre es X", "me llamo X", "soy X", "nombre: X"
        name_patterns = [
            r'(?:mi nombre es|me llamo|soy|nombre:)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
            r'nombre[:\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                break
        
        # If name not found with patterns, check if there's a capitalized word after the email
        if not name and email:
            # Find the position of the email
            email_pos = query.find(email)
            if email_pos != -1:
                # Get text after the email, but only the first line (before any newlines or context)
                text_after_email = query[email_pos + len(email):].strip()
                # Split by newlines and take only the first part
                first_line = text_after_email.split('\n')[0].strip()
                # Remove any "Contexto" or similar words
                first_line = re.sub(r'(?i)contexto.*', '', first_line).strip()
                # Look for capitalized words (potential names) - max 2 words
                name_match = re.search(r'^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)', first_line)
                if name_match:
                    extracted_name = name_match.group(1).strip()
                    # Validate it's not too long (max 40 chars) and doesn't contain common non-name words
                    if len(extracted_name) <= 40 and not any(word in extracted_name.lower() for word in ['contexto', 'sesion', 'email']):
                        name = extracted_name
        
        if not email:
            return {
                "result": {
                    "success": False,
                    "message": "No se encontró un correo electrónico válido en tu mensaje. Por favor, proporciona tu correo electrónico."
                },
                "method": "OTP send"
            }
        
        result = send_otp_to_user(email, name, trace_id)
        return {
            "result": result,
            "method": "OTP send"
        }
    
    def _execute_otp_verify(self, query: str, trace_id: str = None) -> dict:
        """Ejecutar verificación de OTP"""
        import re
        from tools.chat_memory import retrieve_chat_memory
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, query)
        email = emails[0] if emails else None
        
        # If email not found in query, try to get it from memory
        if not email:
            # Try to get email from session memory
            session_id = "default_session"  # Could be passed as parameter
            email_memory_result = retrieve_chat_memory(session_id, "email", trace_id=trace_id)
            if email_memory_result.get("found") and email_memory_result.get("memory_value"):
                email = email_memory_result.get("memory_value")
        
        # Extract OTP code (6 digits)
        otp_pattern = r'\b(\d{6})\b'
        otp_matches = re.findall(otp_pattern, query)
        otp_code = otp_matches[-1] if otp_matches else None  # Get last 6-digit code found
        
        if not email or not otp_code:
            return {
                "result": {
                    "success": False,
                    "message": "Por favor proporciona tu correo electrónico y el código OTP de 6 dígitos que recibiste."
                },
                "method": "OTP verify"
            }
        
        result = verify_otp_code(email, otp_code, trace_id)
        return {
            "result": result,
            "method": "OTP verify"
        }
    
    @traceable(name="OrchestratorAgent.store_user_info")
    def store_user_info(self, session_id: str, query: str, trace_id: str = None, is_authenticated: bool = False) -> dict:
        """
        Extraer y almacenar información del usuario de la consulta
        
        ⚠️ ADVERTENCIA - SISTEMA DE TRAZAS:
        Este método tiene @traceable y se agrupa bajo la traza padre automáticamente.
        NO remover el decorador - es necesario para que aparezca en LangSmith.
        
        Args:
            session_id: ID de la sesión
            query: Consulta del usuario
            trace_id: ID del trace
            is_authenticated: Si el usuario está autenticado (para no extraer email)
            
        Returns:
            dict: Información extraída
        """
        try:
            from tools.chat_memory import extract_user_info as extract_info_helper
            
            # Llamar a la función helper con is_authenticated para evitar extraer emails
            info = extract_info_helper(query, session_id, trace_id=trace_id, is_authenticated=is_authenticated)
            
            tracer.log(
                operation="USER_INFO_EXTRACTED",
                message=f"Información extraída: {len(info.get('extracted', {}))} campo(s)",
                metadata=info,
                level="INFO",
                trace_id=trace_id
            )
            
            return info
            
        except Exception as e:
            tracer.log(
                operation="EXTRACT_INFO_ERROR",
                message=f"Error extrayendo info: {str(e)}",
                level="ERROR",
                trace_id=trace_id
            )
            return {"session_id": session_id, "extracted": {}, "count": 0}
    
    @traceable(name="OrchestratorAgent.retrieve_memory")
    def retrieve_memory(self, session_id: str, trace_id: str = None, is_authenticated: bool = False) -> str:
        """
        Recuperar memorias de la sesión para enriquecer el contexto
        
        ⚠️ ADVERTENCIA - SISTEMA DE TRAZAS:
        Este método tiene @traceable y se agrupa bajo la traza padre automáticamente.
        NO remover el decorador - es necesario para que aparezca en LangSmith.
        
        Args:
            session_id: ID de la sesión
            trace_id: ID del trace
            is_authenticated: Si el usuario está autenticado (para filtrar emails)
            
        Returns:
            str: Contexto formateado
        """
        try:
            memories = retrieve_chat_memory(session_id, memory_key=None, trace_id=trace_id)
            
            if memories.get("found"):
                memories_dict = memories.get("memories", {})
                
                # Si el usuario está autenticado, filtrar la clave "email" de las memorias
                if is_authenticated:
                    # Crear una copia sin la clave "email"
                    filtered_memories = {k: v for k, v in memories_dict.items() if k != "email"}
                    
                    # Si no quedan memorias útiles después de filtrar, retornar vacío
                    if not filtered_memories:
                        return ""
                    
                    # Formatear contexto sin email
                    context_parts = []
                    for key, value in filtered_memories.items():
                        context_parts.append(f"{key}: {value}")
                    
                    context = "\n".join(context_parts)
                    context = f"\n\nContexto de la sesión:\n{context}"
                else:
                    # Usar la función normal si no está autenticado
                    context = get_context_for_query(session_id, trace_id=trace_id)
                
                tracer.log(
                    operation="MEMORY_RETRIEVED",
                    message=f"Memorias recuperadas para sesión",
                    metadata={"session_id": session_id, "count": memories.get("count", 0), "filtered": is_authenticated},
                    level="INFO",
                    trace_id=trace_id
                )
                
                return context
            else:
                return ""
                
        except Exception as e:
            tracer.log(
                operation="MEMORY_RETRIEVE_ERROR",
                message=f"Error recuperando memoria: {str(e)}",
                level="ERROR",
                trace_id=trace_id
            )
            return ""


# Singleton global
_orchestrator_instance = None

def get_orchestrator():
    """
    Obtener instancia global del orquestador
    
    ⚠️ ADVERTENCIA - SISTEMA DE TRAZAS:
    Para mantener trazas unificadas en LangSmith, SIEMPRE usar:
        orchestrator.process_query(query, trace_id, is_authenticated, session_info)
    
    NO usar directamente:
        orchestrator.analyze_query() o orchestrator.execute_tools()
    
    Esto asegura que todas las trazas se agrupen bajo una sola traza padre.
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorAgent()
    return _orchestrator_instance


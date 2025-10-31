"""
Agente Inteligente de EcoMarket - Coordinador Principal
Combina Orchestrator Agent (reasoning) y Response Agent (respuestas)
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.tracing import tracer
from agents.orchestrator_agent import get_orchestrator
from agents.response_agent import get_response_agent

# Importar LangSmith para agrupar trazas
try:
    from langsmith import trace
    from langchain_core.tracers import LangChainTracer
    from langchain_core.globals import set_verbose
    import os
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    trace = None
    LangChainTracer = None
    os = None


class IntelligentAgent:
    """
    Agente inteligente principal que coordina:
    - Orchestrator Agent: Analiza y decide qué herramientas usar
    - Response Agent: Genera respuestas amigables
    
    Este agente actúa como coordinador de alto nivel.
    """
    
    def __init__(self):
        """Inicializar el agente inteligente"""
        # Usar los agentes especializados
        self.orchestrator = get_orchestrator()
        self.response_agent = get_response_agent()
        self.active_sessions = {}  # Track active user sessions
        print("✅ Intelligent Agent (Coordinador) inicializado")
    
    def is_ready(self):
        """Verificar si el agente está listo"""
        return self.orchestrator.is_ready()
    
    def process_query(self, query: str, enable_logging: bool = False, session_id: str = None, is_authenticated: bool = False, session_info: dict = None) -> str:
        """
        Procesar una consulta del usuario de manera inteligente.
        
        Flujo:
        1. Generar trace_id único para toda la interacción
        2. Gestionar memoria de sesión
        3. Orchestrator analiza y decide qué hacer
        4. Orchestrator ejecuta herramientas
        5. Response Agent genera respuesta amigable
        
        Args:
            query: Consulta del usuario
            enable_logging: Habilitar logging detallado
            session_id: ID de sesión del usuario (opcional)
            is_authenticated: Si el usuario está autenticado (opcional)
            session_info: Información de sesión del usuario (email, name) si está autenticado
            
        Returns:
            str: Respuesta amigable del agente
        """
        start_time = time.time()
        
        # Generar o usar session_id
        if not session_id:
            # Por ahora usamos un session_id simple basado en el usuario
            # En producción esto vendría de la sesión del usuario
            session_id = "default_session"
        
        # Generar un trace_id único para toda esta interacción
        trace_id = tracer.generate_trace_id()
        
        try:
            # Log inicial del trace completo
            tracer.log(
                operation="USER_QUERY_START",
                message=f"📥 Consulta recibida",
                metadata={"query": query[:200]},
                level="INFO",
                trace_id=trace_id
            )
            
            # Crear contexto de LangSmith para agrupar todas las trazas
            # Este context manager envuelve TODA la ejecución
            if LANGSMITH_AVAILABLE and trace:
                # Configurar variables de entorno para que las trazas se agrupen
                # IMPORTANTE: Configurar ANTES del context manager
                project_name = os.getenv("LANGCHAIN_PROJECT", "ecomarket-agent")
                os.environ["LANGCHAIN_PROJECT"] = project_name
                
                # Crear traza padre para agrupar todo
                with trace(
                    name=f"EcoMarketAgent.process_query",
                    project_name=project_name,
                    metadata={
                        "query": query[:200],
                        "trace_id": trace_id,
                        "session_id": session_id
                    }
                ):
                    # Ahora ejecutar todo el flujo dentro del contexto
                    return self._process_query_flow(query, trace_id, start_time, session_id, is_authenticated, session_info)
            else:
                return self._process_query_flow(query, trace_id, start_time, session_id, is_authenticated, session_info)
            
        except Exception as e:
            tracer.log(
                operation="USER_QUERY_ERROR",
                message=f"❌ Error procesando consulta: {str(e)}",
                level="ERROR",
                trace_id=trace_id
            )
            
            # Respuesta de error amigable
            return self.response_agent.get_error_response(str(e))
    
    def _process_query_flow(self, query: str, trace_id: str, start_time: float, session_id: str = None, is_authenticated: bool = False, session_info: dict = None) -> str:
        """Procesar el flujo completo de la consulta (con o sin LangSmith)"""
        
        # PASO 0: Gestionar memoria de sesión
        # Pasar is_authenticated para que NO extraiga email si el usuario ya está autenticado
        self.orchestrator.store_user_info(session_id, query, trace_id, is_authenticated)
        
        # Si hay session_info con email, guardarlo en memoria para uso automático
        if session_info and session_info.get("email"):
            from tools.chat_memory import store_chat_memory
            store_chat_memory(session_id, "user_email", session_info.get("email"), ttl_minutes=60, trace_id=trace_id)
            if session_info.get("name"):
                store_chat_memory(session_id, "user_name", session_info.get("name"), ttl_minutes=60, trace_id=trace_id)
        
        # Recuperar memoria existente para enriquecer el contexto
        # Pasar is_authenticated para que retrieve_memory filtre emails automáticamente
        memory_context = self.orchestrator.retrieve_memory(session_id, trace_id, is_authenticated)
        
        # CRÍTICO: Si el usuario está autenticado, limpiar emails de la query antes de analizarla
        # Esto previene que menciones casuales del email activen autenticación
        query_to_analyze = query
        if is_authenticated:
            import re
            # Remover emails de la query para análisis (pero mantener la query original para contexto)
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            query_to_analyze = re.sub(email_pattern, '', query).strip()
            # Limpiar espacios múltiples y líneas vacías
            query_to_analyze = re.sub(r'\s+', ' ', query_to_analyze)
            query_to_analyze = query_to_analyze.strip()
            # Si después de limpiar queda vacío, usar la query original pero sin email
            if not query_to_analyze:
                query_to_analyze = query
        
        # Enriquecer query con contexto de memoria si existe
        enriched_query = query_to_analyze
        if memory_context:
            enriched_query = f"{query_to_analyze}\n\n{memory_context}"
        
        # PASO 1: Orchestrator analiza la consulta (enriquecida con memoria, sin emails si está autenticado)
        # Pasar is_authenticated y session_info para que use email disponible automáticamente
        analysis = self.orchestrator.analyze_query(enriched_query, trace_id, is_authenticated, session_info=session_info)
        
        tracer.log(
            operation="ORCHESTRATOR_ANALYSIS",
            message=f"Consulta analizada: {analysis.get('intent')}",
            metadata=analysis,
            level="INFO",
            trace_id=trace_id
        )
        
        # CRÍTICO: Si el usuario está autenticado y quiere crear un ticket, verificar si tenemos email disponible
        # Si tenemos email de session_info, NO pedir información adicional
        if analysis.get("requires_additional_info", False) and is_authenticated and session_info:
            # Verificar si la intención es crear un ticket
            intent = analysis.get("intent", "").lower()
            tools_needed = analysis.get("tools_needed", [])
            is_ticket_creation = "TICKET_CREATE" in tools_needed or any(word in intent for word in ["crear ticket", "ticket de compra", "ticket de devolución", "orden de compra"])
            
            if is_ticket_creation and session_info.get("email"):
                # Tenemos email disponible, no necesitamos pedir información adicional
                # Actualizar el análisis para no requerir email
                missing = analysis.get("missing_info", [])
                if "email" in missing:
                    missing.remove("email")
                if not missing or (len(missing) == 1 and missing[0] in ["número de factura", "numero de factura"]):
                    # Solo falta número de factura o detalles, que podemos generar/extraer automáticamente
                    analysis["requires_additional_info"] = False
                    analysis["missing_info"] = []
        
        # Verificar si necesita información adicional
        if analysis.get("requires_additional_info", False):
            missing = analysis.get("missing_info", [])
            intent = analysis.get("intent", "su solicitud")
            response = self.response_agent.request_missing_info(missing, intent)
            
            tracer.log(
                operation="MISSING_INFO_REQUESTED",
                message=f"Solicitada información adicional: {missing}",
                metadata={"missing_info": missing, "intent": intent},
                level="INFO",
                trace_id=trace_id
            )
            
            return response
        
        # PASO 2: Orchestrator ejecuta herramientas (pasar session_info para uso automático)
        tool_results = self.orchestrator.execute_tools(analysis, enriched_query, trace_id, session_info=session_info)
        
        tracer.log(
            operation="TOOLS_EXECUTED",
            message=f"Herramientas usadas: {tool_results.get('tools_used')}",
            metadata=tool_results,
            level="INFO",
            trace_id=trace_id
        )
        
        # PASO 3: Response Agent genera respuesta amigable
        response = self.response_agent.generate_response(analysis, tool_results, query, trace_id)
        
        # PASO 4: Extraer y guardar contexto relevante de la conversación
        self._store_conversation_context(query, analysis, tool_results, response, session_id, trace_id)
        
        # Log tiempo de procesamiento total
        processing_time = time.time() - start_time
        tracer.log(
            operation="USER_QUERY_COMPLETE",
            message=f"✅ Consulta procesada en {processing_time:.2f}s",
            metadata={
                "query": query[:100],
                "intent": analysis.get("intent"),
                "tools": analysis.get("tools_needed", []),
                "processing_time": processing_time,
                "response_length": len(response)
            },
            level="SUCCESS",
            trace_id=trace_id
        )
        
        return response
    
    def _store_conversation_context(self, query: str, analysis: dict, tool_results: dict, response: str, session_id: str, trace_id: str = None):
        """
        Extraer y almacenar contexto relevante de la conversación en memoria
        
        Args:
            query: Consulta del usuario
            analysis: Análisis del orchestrator
            tool_results: Resultados de las herramientas
            response: Respuesta generada
            session_id: ID de sesión
            trace_id: ID del trace
        """
        try:
            from tools.chat_memory import store_chat_memory
            import re
            import json
            
            # 1. Guardar la intención del usuario
            intent = analysis.get("intent", "")
            if intent:
                store_chat_memory(session_id, "last_intent", intent, ttl_minutes=5, trace_id=trace_id)
            
            # 2. Extraer productos mencionados en tool_results y response
            products_mentioned = []
            
            # Buscar productos en tool_results
            for tool_name, tool_data in tool_results.get("data", {}).items():
                if isinstance(tool_data, dict):
                    result = tool_data.get("result", "")
                    if isinstance(result, str):
                        # Buscar nombres de productos (patrones comunes)
                        # Ejemplo: "Cuaderno Reciclado", "Producto: X", etc.
                        product_patterns = [
                            r'📦\s*\*\*([^*\(]+)',  # Emoji 📦 seguido de producto (antes de paréntesis)
                            r'\*\*([^*\(]+?)\*\*',  # Texto en negrita (captura antes de paréntesis)
                            r'Producto[:\s]+([A-ZÁÉÍÓÚÑ][^\n\(]+)',  # "Producto: X"
                            r'Nombre del Producto[:\s]+([^\n,\(]+)',  # "Nombre del Producto: X"
                            r'📦\s+([A-ZÁÉÍÓÚÑ][^\n\(]+)',  # Emoji sin negrita
                        ]
                        
                        for pattern in product_patterns:
                            matches = re.findall(pattern, result, re.IGNORECASE)
                            # Limpiar cada match (remover paréntesis y espacios)
                            cleaned = [m.split('(')[0].strip() for m in matches if m.strip()]
                            products_mentioned.extend(cleaned)
            
            # Buscar productos en la respuesta final
            product_patterns = [
                r'📦\s*\*\*([^*\(]+)',  # Emoji 📦 seguido de producto en negrita
                r'\*\*([^*\(]+?)\*\*',  # Texto en negrita
                r'📦\s+([A-ZÁÉÍÓÚÑ][^\n\(]+)',  # Emoji sin negrita
            ]
            for pattern in product_patterns:
                matches = re.findall(pattern, response, re.IGNORECASE)
                # Limpiar cada match
                cleaned = [m.split('(')[0].strip() for m in matches if m.strip()]
                products_mentioned.extend(cleaned)
            
            # Limpiar y deduplicar productos
            products_mentioned = [p.strip() for p in products_mentioned if p.strip() and len(p) > 2]
            products_mentioned = list(dict.fromkeys(products_mentioned))  # Remover duplicados
            
            if products_mentioned:
                # Guardar productos mencionados (últimos 3 para no sobrecargar)
                products_str = ", ".join(products_mentioned[:3])
                store_chat_memory(session_id, "mentioned_products", products_str, ttl_minutes=5, trace_id=trace_id)
            
            # 3. Extraer información de tickets mencionados
            ticket_pattern = r'TKT-?\d+|ticket[:\s]+([A-Z0-9-]+)'
            ticket_matches = re.findall(ticket_pattern, response + query, re.IGNORECASE)
            if ticket_matches:
                tickets = ", ".join(ticket_matches)
                store_chat_memory(session_id, "mentioned_tickets", tickets, ttl_minutes=5, trace_id=trace_id)
            
            # 4. Guardar contexto resumido de la última consulta
            context_summary = f"Última intención: {intent}"
            if products_mentioned:
                context_summary += f". Productos mencionados: {products_str}"
            
            if context_summary:
                store_chat_memory(session_id, "conversation_context", context_summary, ttl_minutes=5, trace_id=trace_id)
                
                tracer.log(
                    operation="CONTEXT_STORED",
                    message="Contexto de conversación almacenado",
                    metadata={
                        "intent": intent,
                        "products_count": len(products_mentioned),
                        "session_id": session_id
                    },
                    level="INFO",
                    trace_id=trace_id
                )
                
        except Exception as e:
            tracer.log(
                operation="CONTEXT_STORE_ERROR",
                message=f"Error almacenando contexto: {str(e)}",
                level="ERROR",
                trace_id=trace_id
            )


# Singleton global
_intelligent_agent_instance = None

def get_intelligent_agent():
    """Obtener instancia global del agente inteligente"""
    global _intelligent_agent_instance
    if _intelligent_agent_instance is None:
        _intelligent_agent_instance = IntelligentAgent()
    return _intelligent_agent_instance

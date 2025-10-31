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
    
    def process_query(self, query: str, enable_logging: bool = False, session_id: str = None, is_authenticated: bool = False) -> str:
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
                    return self._process_query_flow(query, trace_id, start_time, session_id, is_authenticated)
            else:
                return self._process_query_flow(query, trace_id, start_time, session_id, is_authenticated)
            
        except Exception as e:
            tracer.log(
                operation="USER_QUERY_ERROR",
                message=f"❌ Error procesando consulta: {str(e)}",
                level="ERROR",
                trace_id=trace_id
            )
            
            # Respuesta de error amigable
            return self.response_agent.get_error_response(str(e))
    
    def _process_query_flow(self, query: str, trace_id: str, start_time: float, session_id: str = None, is_authenticated: bool = False) -> str:
        """Procesar el flujo completo de la consulta (con o sin LangSmith)"""
        
        # PASO 0: Gestionar memoria de sesión
        # Extraer y almacenar información del usuario si la proporciona
        self.orchestrator.store_user_info(session_id, query, trace_id)
        
        # Recuperar memoria existente para enriquecer el contexto
        # Pasar is_authenticated para que retrieve_memory filtre emails automáticamente
        memory_context = self.orchestrator.retrieve_memory(session_id, trace_id, is_authenticated)
        
        # Enriquecer query con contexto de memoria si existe
        enriched_query = query
        if memory_context:
            enriched_query = f"{query}\n\n{memory_context}"
        
        # PASO 1: Orchestrator analiza la consulta (enriquecida con memoria)
        # Pasar is_authenticated para que no active OTP si ya está autenticado
        analysis = self.orchestrator.analyze_query(enriched_query, trace_id, is_authenticated)
        
        tracer.log(
            operation="ORCHESTRATOR_ANALYSIS",
            message=f"Consulta analizada: {analysis.get('intent')}",
            metadata=analysis,
            level="INFO",
            trace_id=trace_id
        )
        
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
        
        # PASO 2: Orchestrator ejecuta herramientas
        tool_results = self.orchestrator.execute_tools(analysis, enriched_query, trace_id)
        
        tracer.log(
            operation="TOOLS_EXECUTED",
            message=f"Herramientas usadas: {tool_results.get('tools_used')}",
            metadata=tool_results,
            level="INFO",
            trace_id=trace_id
        )
        
        # PASO 3: Response Agent genera respuesta amigable
        response = self.response_agent.generate_response(analysis, tool_results, query, trace_id)
        
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


# Singleton global
_intelligent_agent_instance = None

def get_intelligent_agent():
    """Obtener instancia global del agente inteligente"""
    global _intelligent_agent_instance
    if _intelligent_agent_instance is None:
        _intelligent_agent_instance = IntelligentAgent()
    return _intelligent_agent_instance

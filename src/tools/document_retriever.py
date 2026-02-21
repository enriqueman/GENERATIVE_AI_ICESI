"""
Herramienta para recuperar documentos relevantes de la base de datos vectorial
"""

import os
import sys

# Agregar src al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.vector_functions import get_combined_retriever
from utils.tracing import tracer, log_retrieval

# Importar traceable para LangSmith
try:
    from langsmith import traceable
except ImportError:
    # Si no está disponible, usar decorador vacío
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class DocumentRetriever:
    """
    Herramienta para recuperar documentos relevantes según una consulta
    """
    
    def __init__(self, max_documents: int = 10):
        """
        Inicializar el recuperador de documentos
        
        Args:
            max_documents (int): Número máximo de documentos a recuperar
        """
        self.max_documents = max_documents
        self.retriever = None
        self._initialize()
    
    def _initialize(self):
        """Inicializar el retriever de forma lazy"""
        if self.retriever is None:
            try:
                self.retriever = get_combined_retriever()
                tracer.log(
                    operation="TOOL_INITIALIZATION",
                    message="DocumentRetriever inicializado",
                    level="SUCCESS"
                )
            except Exception as e:
                tracer.log(
                    operation="TOOL_INITIALIZATION",
                    message=f"Error inicializando DocumentRetriever: {str(e)}",
                    level="ERROR"
                )
    
    @traceable(name="DocumentRetriever.search")
    def search(self, query: str) -> list:
        """
        Buscar documentos relevantes para una consulta
        
        ⚠️ ADVERTENCIA - SISTEMA DE TRAZAS:
        Este método tiene el decorador @traceable que crea una traza en LangSmith.
        - Se agrupa automáticamente bajo la traza padre si se llama desde OrchestratorAgent.process_query()
        - NO crear context managers adicionales aquí - el de OrchestratorAgent es suficiente
        - NO remover el decorador @traceable - es necesario para que aparezca en LangSmith
        
        Args:
            query (str): Consulta del usuario
            
        Returns:
            list: Lista de documentos relevantes con metadata
        """
        if not self.retriever:
            return []
        
        try:
            # Obtener documentos relevantes
            # En versiones recientes de LangChain, usar invoke() en lugar de get_relevant_documents()
            try:
                docs = self.retriever.invoke(query)
            except AttributeError:
                # Fallback para versiones antiguas
                docs = self.retriever.get_relevant_documents(query)
            
            # Limitar número de documentos
            docs = docs[:self.max_documents]
            
            # Log para trazabilidad
            log_retrieval(query, docs)
            
            # Formatear resultados
            results = []
            for i, doc in enumerate(docs):
                results.append({
                    "rank": i + 1,
                    "source": doc.metadata.get("source", "Unknown"),
                    "file_type": doc.metadata.get("file_type", "Unknown"),
                    "content": doc.page_content,
                    "content_preview": doc.page_content[:200] + "...",
                    "relevance_score": getattr(doc, 'score', None)
                })
            
            tracer.log(
                operation="TOOL_USE",
                message=f"DocumentRetriever: {len(results)} documentos encontrados",
                metadata={"query": query[:100], "num_results": len(results)},
                level="INFO"
            )
            
            return results
            
        except Exception as e:
            tracer.log(
                operation="TOOL_ERROR",
                message=f"Error en DocumentRetriever: {str(e)}",
                metadata={"query": query[:100], "error": str(e)},
                level="ERROR"
            )
            return []
    
    def is_available(self) -> bool:
        """Verificar si el retriever está disponible"""
        return self.retriever is not None


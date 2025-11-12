"""
Sistema de trazabilidad para el agente RAG
Registra todas las operaciones para visualización en el panel admin
"""

import os
import json
import datetime
from typing import Dict, List, Any, Optional
from functools import wraps

# Intentar importar LangSmith si está disponible
try:
    from langsmith import Client, traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    # Crear funciones dummy
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# Almacenamiento local para logs
LOGS_STORAGE = []
MAX_LOGS = 1000  # Mantener solo los últimos 1000 logs

class TracingLogger:
    """Logger centralizado para la trazabilidad del sistema"""
    
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        self.client = None
        self.active_trace_id = None  # Trace ID actual activo
        
        # Configurar LangSmith si está disponible
        if LANGSMITH_AVAILABLE:
            try:
                # Configurar variables de entorno para LangSmith
                # Verificar múltiples variables de entorno posibles
                langsmith_tracing = os.getenv("LANGSMITH_TRACING", "false")
                langchain_tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2", "false")
                
                print(f"[DEBUG] LANGSMITH_TRACING={langsmith_tracing}")
                print(f"[DEBUG] LANGCHAIN_TRACING_V2={langchain_tracing_v2}")
                
                tracing_enabled = (
                    langsmith_tracing.lower() == "true" or
                    langchain_tracing_v2.lower() == "true"
                )
                
                if tracing_enabled:
                    print(f"[OK] Tracing habilitado")
                    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
                    api_url = os.getenv("LANGSMITH_ENDPOINT") or os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
                    
                    print(f"[DEBUG] API Key presente: {bool(api_key)}")
                    
                    if api_key:
                        # Configurar variables de entorno para LangChain
                        os.environ["LANGCHAIN_TRACING_V2"] = "true"
                        os.environ["LANGCHAIN_ENDPOINT"] = api_url
                        os.environ["LANGCHAIN_API_KEY"] = api_key
                        os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "ecomarket-rag-system")
                        
                        self.client = Client(api_key=api_key, api_url=api_url)
                        print("[OK] LangSmith tracing habilitado")
                else:
                    print("[INFO] LangSmith tracing deshabilitado (LANGSMITH_TRACING=false)")
            except Exception as e:
                print(f"[WARNING] No se pudo configurar LangSmith: {e}")
    
    def generate_trace_id(self) -> str:
        """Generar un nuevo trace ID único"""
        import uuid
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        self.active_trace_id = trace_id
        return trace_id
    
    def log(
        self,
        operation: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        level: str = "INFO",
        trace_id: Optional[str] = None
    ):
        """Registrar un evento en el log con trace_id"""
        # Usar trace_id proporcionado o el activo
        current_trace_id = trace_id or self.active_trace_id
        
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "trace_id": current_trace_id,
            "operation": operation,
            "message": message,
            "metadata": metadata or {},
            "level": level
        }
        
        # Agregar al almacenamiento local
        self.logs.insert(0, log_entry)  # Insertar al inicio para mostrar los más recientes primero
        
        # Mantener solo los últimos MAX_LOGS
        if len(self.logs) > MAX_LOGS:
            self.logs = self.logs[:MAX_LOGS]
        
        # Formatear para consola
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {operation}: {message}")
        
        if metadata:
            for key, value in metadata.items():
                print(f"         {key}: {value}")
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener logs recientes"""
        return self.logs[:limit]
    
    def get_logs_by_operation(self, operation: str) -> List[Dict[str, Any]]:
        """Obtener logs filtrados por operación"""
        return [log for log in self.logs if log.get("operation") == operation]
    
    def clear_logs(self):
        """Limpiar todos los logs"""
        self.logs = []

# Instancia global del logger
tracer = TracingLogger()

def trace_operation(operation_name: str):
    """Decorador para trazar operaciones"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Log inicio de operación
            tracer.log(
                operation=operation_name,
                message=f"Iniciando {func.__name__}",
                metadata={
                    "function": func.__name__,
                    "args": str(args)[:200],  # Limitar tamaño
                    "kwargs_keys": list(kwargs.keys())
                },
                level="INFO"
            )
            
            try:
                # Ejecutar función
                result = func(*args, **kwargs)
                
                # Log éxito
                tracer.log(
                    operation=operation_name,
                    message=f"Completado {func.__name__} exitosamente",
                    metadata={
                        "function": func.__name__,
                        "result_type": type(result).__name__
                    },
                    level="SUCCESS"
                )
                
                return result
                
            except Exception as e:
                # Log error
                tracer.log(
                    operation=operation_name,
                    message=f"Error en {func.__name__}: {str(e)}",
                    metadata={
                        "function": func.__name__,
                        "error": str(e),
                        "error_type": type(e).__name__
                    },
                    level="ERROR"
                )
                raise
        
        return wrapper
    return decorator

def log_retrieval(question: str, retrieved_docs: List[Any], source: str = "chroma"):
    """Log específico para operaciones de recuperación RAG"""
    tracer.log(
        operation="RAG_RETRIEVAL",
        message=f"Recuperación de documentos para: '{question[:50]}...'",
        metadata={
            "question_length": len(question),
            "num_documents": len(retrieved_docs),
            "source": source,
            "documents": [
                {
                    "source": doc.metadata.get("source", "unknown"),
                    "content_preview": doc.page_content[:100] + "..."
                }
                for doc in retrieved_docs[:5]  # Solo primeros 5
            ]
        },
        level="INFO"
    )

def log_generation(question: str, answer: str, processing_time: float = None):
    """Log específico para generación de respuestas"""
    metadata = {
        "question_length": len(question),
        "answer_length": len(answer),
        "processing_time": processing_time
    }
    
    tracer.log(
        operation="RAG_GENERATION",
        message=f"Respuesta generada",
        metadata=metadata,
        level="SUCCESS"
    )

def log_document_upload(filename: str, file_type: str, success: bool):
    """Log para carga de documentos"""
    tracer.log(
        operation="DOCUMENT_UPLOAD",
        message=f"Documento {'cargado' if success else 'falló'}: {filename}",
        metadata={
            "filename": filename,
            "file_type": file_type,
            "success": success
        },
        level="SUCCESS" if success else "ERROR"
    )

def log_collection_update(collection_name: str, num_documents: int):
    """Log para actualizaciones de colección"""
    tracer.log(
        operation="COLLECTION_UPDATE",
        message=f"Colección actualizada: {collection_name}",
        metadata={
            "collection_name": collection_name,
            "num_documents": num_documents
        },
        level="INFO"
    )

# Funciones auxiliares para obtener estadísticas
def get_statistics() -> Dict[str, Any]:
    """Obtener estadísticas generales de uso"""
    all_logs = tracer.get_recent_logs()
    
    if not all_logs:
        return {}
    
    # Contar por operación
    operations = {}
    error_count = 0
    unique_traces = set()
    
    for log in all_logs:
        op = log.get("operation", "unknown")
        operations[op] = operations.get(op, 0) + 1
        
        if log.get("level") == "ERROR":
            error_count += 1
        
        # Rastrear trace_id únicos
        trace_id = log.get("trace_id")
        if trace_id:
            unique_traces.add(trace_id)
    
    return {
        "total_logs": len(all_logs),
        "unique_traces": len(unique_traces),
        "operations": operations,
        "error_count": error_count,
        "success_rate": round((len(all_logs) - error_count) / len(all_logs) * 100, 2) if all_logs else 0,
        "most_recent": all_logs[0] if all_logs else None
    }


def get_trace_logs(trace_id: str) -> List[Dict[str, Any]]:
    """
    Obtener todos los logs de un trace específico.
    
    Args:
        trace_id: ID del trace
        
    Returns:
        List[Dict]: Logs del trace
    """
    all_logs = tracer.get_recent_logs()
    return [log for log in all_logs if log.get("trace_id") == trace_id]


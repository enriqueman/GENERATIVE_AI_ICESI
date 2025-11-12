"""
Herramienta para gestionar memoria en el chat
Permite almacenar y recuperar información temporal con TTL de 5 minutos
"""

import os
import sys
import re
from typing import Dict, Any, Optional, List

# Agregar src al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.db import store_memory as db_store_memory, get_memory as db_get_memory, delete_memory as db_delete_memory
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


@TRACEABLE(name="store_chat_memory")
def store_chat_memory(
    session_id: str,
    memory_key: str,
    memory_value: str,
    ttl_minutes: int = 5,
    trace_id: str = None
) -> Dict[str, Any]:
    """
    Almacenar información en memoria del chat con TTL
    
    Args:
        session_id: Identificador de la sesión
        memory_key: Clave de la memoria (ej: "nombre", "email", "preferencia")
        memory_value: Valor a almacenar
        ttl_minutes: Tiempo de vida en minutos (default: 5)
        
    Returns:
        dict: Resultado de la operación
    """
    
    if not session_id or not memory_key:
        return {
            "success": False,
            "error": "session_id y memory_key son requeridos"
        }
    
    if not memory_value:
        return {
            "success": False,
            "error": "memory_value no puede estar vacío"
        }
    
    try:
        success = db_store_memory(session_id, memory_key, memory_value, ttl_minutes)
        
        if success:
            tracer.log(
                operation="MEMORY_STORED",
                message=f"Memoria almacenada: {memory_key}",
                metadata={
                    "session_id": session_id,
                    "memory_key": memory_key,
                    "ttl_minutes": ttl_minutes
                },
                level="INFO",
                trace_id=trace_id
            )
            
            return {
                "success": True,
                "message": f"Memoria '{memory_key}' almacenada exitosamente",
                "session_id": session_id,
                "memory_key": memory_key,
                "ttl_minutes": ttl_minutes,
                "value_preview": memory_value[:50] + "..." if len(memory_value) > 50 else memory_value
            }
        else:
            return {
                "success": False,
                "error": "No se pudo almacenar la memoria"
            }
            
    except Exception as e:
        tracer.log(
            operation="MEMORY_STORE_ERROR",
            message=f"Error almacenando memoria: {str(e)}",
            metadata={"session_id": session_id, "memory_key": memory_key},
            level="ERROR",
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }


@TRACEABLE(name="retrieve_chat_memory")
def retrieve_chat_memory(
    session_id: str,
    memory_key: Optional[str] = None,
    trace_id: str = None
) -> Dict[str, Any]:
    """
    Recuperar información de memoria del chat
    
    Args:
        session_id: Identificador de la sesión
        memory_key: Clave específica a recuperar (opcional, si no se proporciona retorna todas)
        
    Returns:
        dict: Memoria(s) recuperada(s)
    """
    
    if not session_id:
        return {
            "success": False,
            "error": "session_id es requerido"
        }
    
    try:
        memories = db_get_memory(session_id, memory_key)
        
        if memory_key:
            # Si se pidió una clave específica
            if memories:
                tracer.log(
                    operation="MEMORY_RETRIEVED",
                    message=f"Memoria recuperada: {memory_key}",
                    metadata={"session_id": session_id, "memory_key": memory_key},
                    level="INFO",
                    trace_id=trace_id
                )
                
                return {
                    "success": True,
                    "found": True,
                    "memory_key": memory_key,
                    "memory_value": memories,
                    "preview": str(memories)[:100] if memories else None
                }
            else:
                return {
                    "success": True,
                    "found": False,
                    "memory_key": memory_key,
                    "message": f"No se encontró memoria para '{memory_key}'"
                }
        else:
            # Si se pidieron todas las memorias
            if memories:
                tracer.log(
                    operation="MEMORY_RETRIEVED_ALL",
                    message=f"Memorias recuperadas: {len(memories)} item(s)",
                    metadata={"session_id": session_id, "count": len(memories)},
                    level="INFO",
                    trace_id=trace_id
                )
                
                return {
                    "success": True,
                    "found": True,
                    "memories": memories,
                    "count": len(memories)
                }
            else:
                return {
                    "success": True,
                    "found": False,
                    "message": "No se encontraron memorias en esta sesión"
                }
            
    except Exception as e:
        tracer.log(
            operation="MEMORY_RETRIEVE_ERROR",
            message=f"Error recuperando memoria: {str(e)}",
            metadata={"session_id": session_id, "memory_key": memory_key},
            level="ERROR",
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }


@TRACEABLE(name="clear_chat_memory")
def clear_chat_memory(
    session_id: str,
    memory_key: Optional[str] = None,
    trace_id: str = None
) -> Dict[str, Any]:
    """
    Eliminar memoria(s) del chat
    
    Args:
        session_id: Identificador de la sesión
        memory_key: Clave específica a eliminar (opcional, si no se proporciona elimina todas)
        
    Returns:
        dict: Resultado de la operación
    """
    
    if not session_id:
        return {
            "success": False,
            "error": "session_id es requerido"
        }
    
    try:
        success = db_delete_memory(session_id, memory_key)
        
        if success:
            tracer.log(
                operation="MEMORY_DELETED",
                message=f"Memoria eliminada",
                metadata={"session_id": session_id, "memory_key": memory_key},
                level="INFO",
                trace_id=trace_id
            )
            
            return {
                "success": True,
                "message": f"Memoria{'s' if not memory_key else ''} eliminada{'s' if not memory_key else ''} exitosamente",
                "session_id": session_id,
                "memory_key": memory_key
            }
        else:
            return {
                "success": False,
                "error": "No se encontró memoria para eliminar"
            }
            
    except Exception as e:
        tracer.log(
            operation="MEMORY_DELETE_ERROR",
            message=f"Error eliminando memoria: {str(e)}",
            metadata={"session_id": session_id, "memory_key": memory_key},
            level="ERROR",
            trace_id=trace_id
        )
        return {
            "success": False,
            "error": str(e)
        }


# Funciones helper para uso común
def extract_user_info(query: str, session_id: str = None, trace_id: str = None, is_authenticated: bool = False) -> Dict[str, Any]:
    """
    Extraer información del usuario de la consulta y almacenarla
    
    Args:
        query: Consulta del usuario
        session_id: ID de sesión (opcional)
        trace_id: ID del trace para agrupar logs
        is_authenticated: Si el usuario está autenticado (para no extraer email)
        
    Returns:
        dict: Información extraída y almacenada
    """
    
    if not session_id:
        # Generar un session_id por defecto si no se proporciona
        import uuid
        session_id = f"session_{uuid.uuid4().hex[:8]}"
    
    extracted = {}
    
    # Patrones para extraer información
    patterns = {
        "nombre": [
            r"(?:me llamo|mi nombre es|soy) ([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
            r"nombre ([A-Z][a-z]+(?: [A-Z][a-z]+)*)",
        ],
        "email": [
            r"(\S+@\S+\.\S+)",
        ],
        "telefono": [
            r"(\+?[0-9]{1,3}[-.\s]?)?([0-9]{3,4})[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})",
        ],
    }
    
    # Extraer información
    # CRÍTICO: Si el usuario está autenticado, NO extraer email (evitar activar autenticación)
    for key, pattern_list in patterns.items():
        # Si está autenticado y es email, saltar
        if is_authenticated and key == "email":
            continue
            
        for pattern in pattern_list:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                value = match.group(1) if match.lastindex >= 1 else match.group(0)
                extracted[key] = value
                # Almacenar en memoria con trace_id
                store_chat_memory(session_id, key, value, trace_id=trace_id)
                break
    
    return {
        "session_id": session_id,
        "extracted": extracted,
        "count": len(extracted)
    }


def get_context_for_query(session_id: str, trace_id: str = None) -> str:
    """
    Obtener contexto de memoria para enriquecer la consulta
    
    Args:
        session_id: Identificador de la sesión
        trace_id: ID del trace para agrupar logs
        
    Returns:
        str: Contexto formateado para el LLM
    """
    
    try:
        memories = retrieve_chat_memory(session_id, trace_id=trace_id)
        
        if not memories.get("found"):
            return ""
        
        memories_dict = memories.get("memories", {})
        
        if not memories_dict:
            return ""
        
        # Formatear contexto
        context_parts = []
        for key, value in memories_dict.items():
            context_parts.append(f"{key}: {value}")
        
        context = "\n".join(context_parts)
        
        return f"\n\nContexto de la sesión:\n{context}"
        
    except Exception as e:
        tracer.log(
            operation="CONTEXT_ERROR",
            message=f"Error obteniendo contexto: {str(e)}",
            level="ERROR",
            trace_id=trace_id
        )
        return ""


# ============================================================================
# FUNCIONES PARA INTERVIEWER AGENT
# ============================================================================

def store_interview_data(session_id: str, key: str, value: Any, ttl_minutes: int = 30) -> bool:
    """
    Almacenar datos de la entrevista (TTL extendido a 30 minutos)
    
    Args:
        session_id: ID de la sesión
        key: Clave del dato (ej: "profile", "current_question", "completed")
        value: Valor a almacenar (puede ser dict, list, str, int, bool)
        ttl_minutes: Tiempo de vida en minutos (default: 30)
        
    Returns:
        bool: True si se almacenó exitosamente
    """
    import json
    
    try:
        # Convertir el valor a string JSON si no es string
        if not isinstance(value, str):
            value_str = json.dumps(value, ensure_ascii=False)
        else:
            value_str = value
        
        # Usar la función existente de memoria
        interview_key = f"interview_{key}"
        success = db_store_memory(session_id, interview_key, value_str, ttl_minutes)
        
        return success
        
    except Exception as e:
        print(f"[ERROR] Error storing interview data: {e}")
        return False


def get_interview_data(session_id: str, key: str) -> Any:
    """
    Obtener datos de la entrevista
    
    Args:
        session_id: ID de la sesión
        key: Clave del dato
        
    Returns:
        Valor almacenado (deserializado) o None si no existe
    """
    import json
    
    try:
        interview_key = f"interview_{key}"
        value_str = db_get_memory(session_id, interview_key)
        
        if not value_str:
            return None
        
        # Intentar parsear como JSON
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            # Si no es JSON, retornar el string directamente
            return value_str
            
    except Exception as e:
        print(f"[ERROR] Error getting interview data: {e}")
        return None


def clear_interview_data(session_id: str) -> bool:
    """
    Limpiar todos los datos de la entrevista
    
    Args:
        session_id: ID de la sesión
        
    Returns:
        bool: True si se limpió exitosamente
    """
    try:
        # Limpiar las claves principales de la entrevista
        keys_to_clear = [
            "interview_profile",
            "interview_current_question",
            "interview_completed"
        ]
        
        for key in keys_to_clear:
            db_delete_memory(session_id, key)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error clearing interview data: {e}")
        return False


def check_interview_complete(session_id: str) -> bool:
    """
    Verificar si la entrevista está completa
    
    Args:
        session_id: ID de la sesión
        
    Returns:
        bool: True si está completa
    """
    completed = get_interview_data(session_id, "completed")
    return completed if completed is not None else False

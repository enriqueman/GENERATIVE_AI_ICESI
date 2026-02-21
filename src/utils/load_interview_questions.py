"""
Script para cargar preguntas de entrevista desde JSON al RAG y base de datos
"""

import json
import os
import pathlib
from langchain_core.documents import Document
from utils.vector_functions import (
    load_collection,
    create_collection,
    add_documents_to_collection,
    get_base_dir
)
from models.db import (
    create_interview_question,
    get_interview_question,
    connect_db
)


def load_questions_from_json(json_path: str = None) -> list:
    """
    Cargar preguntas desde el archivo JSON
    
    Args:
        json_path: Ruta al archivo JSON. Si es None, usa el path por defecto.
    
    Returns:
        Lista de diccionarios con las preguntas
    """
    if json_path is None:
        base_dir = get_base_dir()
        json_path = os.path.join(base_dir, "static/sample_documents/banco_preguntas_posgrados.json")
    
    if not os.path.exists(json_path):
        print(f"[ERROR] Archivo JSON no encontrado: {json_path}")
        return []
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        print(f"[OK] Cargadas {len(questions)} preguntas desde {json_path}")
        return questions
    except Exception as e:
        print(f"[ERROR] Error cargando JSON: {e}")
        return []


def save_questions_to_database(questions: list) -> int:
    """
    Guardar preguntas en la base de datos
    
    Args:
        questions: Lista de diccionarios con las preguntas
    
    Returns:
        Número de preguntas guardadas
    """
    saved_count = 0
    
    for q in questions:
        try:
            question_id = q.get("id", f"question_{saved_count}")
            question_text = q.get("question", "")
            field = q.get("field", "")
            field_secondary = q.get("field_secondary")
            validation = q.get("validation", "text")
            required = q.get("required", True)
            
            # Extraer categoría del field (ej: "academico.titulo_pregrado" -> "academico")
            category = field.split(".")[0] if "." in field else None
            
            # Crear metadata JSON
            metadata_dict = {
                "id": question_id,
                "field": field,
                "validation": validation,
                "required": required
            }
            if field_secondary:
                metadata_dict["field_secondary"] = field_secondary
            
            metadata_json = json.dumps(metadata_dict, ensure_ascii=False)
            
            result = create_interview_question(
                question_id=question_id,
                question=question_text,
                field=field,
                field_secondary=field_secondary,
                validation=validation,
                required=required,
                category=category,
                metadata=metadata_json
            )
            
            if result:
                saved_count += 1
        except Exception as e:
            print(f"[WARNING] Error guardando pregunta {q.get('id', 'unknown')}: {e}")
    
    print(f"[OK] {saved_count} preguntas guardadas en la base de datos")
    return saved_count


def save_questions_to_rag(questions: list, collection_name: str = "interview_questions") -> bool:
    """
    Guardar preguntas en el RAG (vector database)
    
    Args:
        questions: Lista de diccionarios con las preguntas
        collection_name: Nombre de la colección en ChromaDB
    
    Returns:
        True si fue exitoso, False en caso contrario
    """
    try:
        base_dir = get_base_dir()
        persist_directory = os.path.join(base_dir, "static/persist")
        os.makedirs(persist_directory, exist_ok=True)
        
        # Crear documentos para el RAG
        documents = []
        for q in questions:
            question_id = q.get("id", "")
            question_text = q.get("question", "")
            field = q.get("field", "")
            field_secondary = q.get("field_secondary")
            validation = q.get("validation", "text")
            required = q.get("required", True)
            category = field.split(".")[0] if "." in field else "general"
            
            # Crear contenido del documento
            content_parts = [
                f"Pregunta: {question_text}",
                f"Campo: {field}",
            ]
            
            if field_secondary:
                content_parts.append(f"Campo secundario: {field_secondary}")
            
            content_parts.extend([
                f"Validación: {validation}",
                f"Requerida: {'Sí' if required else 'No'}",
                f"Categoría: {category}"
            ])
            
            content = "\n".join(content_parts)
            
            # Crear metadata
            metadata = {
                "source": "banco_preguntas_posgrados.json",
                "file_type": "interview_question",
                "source_type": "interview",
                "question_id": question_id,
                "field": field,
                "category": category,
                "validation": validation,
                "required": str(required)
            }
            
            if field_secondary:
                metadata["field_secondary"] = field_secondary
            
            doc = Document(page_content=content, metadata=metadata)
            documents.append(doc)
        
        print(f"[DATA] Creando {len(documents)} documentos para RAG...")
        
        # Verificar si la colección existe
        collection_path = os.path.join(persist_directory, "chroma.sqlite3")
        collection_exists = os.path.exists(collection_path)
        
        if collection_exists:
            try:
                # Intentar cargar la colección existente
                vectordb = load_collection(collection_name)
                print(f"[OK] Colección '{collection_name}' cargada, agregando documentos...")
                vectordb = add_documents_to_collection(vectordb, documents)
                print(f"[OK] Documentos agregados a la colección existente")
            except Exception as e:
                print(f"[WARNING] No se pudo cargar colección existente: {e}")
                print(f"[NOTE] Creando nueva colección...")
                vectordb = create_collection(collection_name, documents)
                if vectordb:
                    print(f"[OK] Nueva colección '{collection_name}' creada")
        else:
            # Crear nueva colección
            vectordb = create_collection(collection_name, documents)
            if vectordb:
                print(f"[OK] Colección '{collection_name}' creada con {len(documents)} documentos")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error guardando preguntas en RAG: {e}")
        import traceback
        traceback.print_exc()
        return False


def initialize_interview_questions(json_path: str = None, load_to_db: bool = True, load_to_rag: bool = True) -> dict:
    """
    Inicializar preguntas de entrevista desde JSON
    
    Args:
        json_path: Ruta al archivo JSON (opcional)
        load_to_db: Si True, carga a la base de datos
        load_to_rag: Si True, carga al RAG
    
    Returns:
        Diccionario con el resultado de la operación
    """
    print("[RELOAD] Inicializando preguntas de entrevista...")
    
    # Cargar preguntas desde JSON
    questions = load_questions_from_json(json_path)
    
    if not questions:
        return {
            "success": False,
            "message": "No se encontraron preguntas para cargar",
            "db_count": 0,
            "rag_success": False
        }
    
    result = {
        "success": True,
        "total_questions": len(questions),
        "db_count": 0,
        "rag_success": False
    }
    
    # Guardar en base de datos
    if load_to_db:
        result["db_count"] = save_questions_to_database(questions)
    
    # Guardar en RAG
    if load_to_rag:
        result["rag_success"] = save_questions_to_rag(questions)
    
    print(f"[OK] Inicialización completada: {result['db_count']} preguntas en DB, RAG: {'OK' if result['rag_success'] else 'ERROR'}")
    
    return result


if __name__ == "__main__":
    # Ejecutar inicialización
    result = initialize_interview_questions()
    print(f"\n[RESULT] {result}")







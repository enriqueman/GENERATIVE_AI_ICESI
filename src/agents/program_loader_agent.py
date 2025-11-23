"""
PROGRAM LOADER AGENT
Agente para analizar documentos de programas de posgrado y cargarlos al RAG
con etiquetas apropiadas para recuperación.
"""

import os
import sys
import json
from typing import Dict, List, Any
from langchain_core.documents import Document

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.vector_functions import (
    load_document,
    load_collection,
    create_collection,
    add_documents_to_collection,
    get_base_dir,
    load_retriever
)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import environ
import pathlib

# Configurar environment
env = environ.Env()
env_path = pathlib.Path(__file__).resolve().parent.parent.parent / '.env'
environ.Env.read_env(str(env_path))


class ProgramLoaderAgent:
    """
    Agente que analiza documentos de programas de posgrado y los carga al RAG
    con metadata estructurada para recuperación.
    """
    
    def __init__(self):
        """Inicializar el agente"""
        self.llm = None
        self._initialize()
    
    def _initialize(self):
        """Inicializar el LLM"""
        try:
            api_key = env("OPENAI_API_KEY")
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.2,
                api_key=api_key
            )
            print("[OK] Program Loader Agent initialized")
        except Exception as e:
            print(f"[WARNING] Could not initialize LLM for Program Loader: {e}")
            self.llm = None
    
    def extract_program_info(self, document_content: str, filename: str) -> Dict[str, Any]:
        """
        Extraer información estructurada de un documento de programa usando LLM.
        
        Args:
            document_content: Contenido del documento
            filename: Nombre del archivo
        
        Returns:
            Diccionario con información extraída del programa
        """
        if not self.llm:
            # Fallback: extracción básica
            return {
                "program_name": filename.replace(".pdf", "").replace(".txt", "").replace("_", " ").title(),
                "type": "maestria",
                "description": document_content[:500],
                "tags": []
            }
        
        try:
            # Truncar contenido antes de pasarlo al template
            truncated_content = document_content[:4000] if len(document_content) > 4000 else document_content
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Eres un experto en extraer información estructurada de documentos de programas académicos.

Extrae la siguiente información del documento:
- Nombre completo del programa
- Tipo (maestría, especialización, MBA, doctorado, etc.)
- Descripción breve
- Áreas temáticas principales
- Requisitos principales
- Modalidad (presencial, virtual, híbrida)
- Duración aproximada
- Inversión aproximada (si está disponible)

Responde SOLO con un JSON válido sin texto adicional."""),
                ("user", "Documento:\n{document_content}")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({"document_content": truncated_content})
            
            # Parsear JSON
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            program_info = json.loads(content.strip())
            
            # Asegurar campos mínimos
            if "program_name" not in program_info:
                program_info["program_name"] = filename.replace(".pdf", "").replace(".txt", "").replace("_", " ").title()
            
            return program_info
            
        except Exception as e:
            print(f"[WARNING] Error extracting program info: {e}")
            return {
                "program_name": filename.replace(".pdf", "").replace(".txt", "").replace("_", " ").title(),
                "type": "maestria",
                "description": document_content[:500],
                "tags": []
            }
    
    def create_program_documents(self, file_path: str) -> List[Document]:
        """
        Crear documentos estructurados para RAG a partir de un archivo de programa.
        
        Args:
            file_path: Ruta al archivo del programa
        
        Returns:
            Lista de documentos para RAG
        """
        try:
            # Cargar documento
            raw_docs = load_document(file_path)
            
            if not raw_docs:
                return []
            
            # Combinar contenido de todos los chunks
            full_content = "\n\n".join([doc.page_content for doc in raw_docs])
            
            # Extraer información estructurada
            filename = os.path.basename(file_path)
            program_info = self.extract_program_info(full_content, filename)
            
            # Crear documento principal con metadata rica
            program_name = program_info.get("program_name", filename)
            program_type = program_info.get("type", "maestria")
            description = program_info.get("description", full_content[:500])
            areas = program_info.get("areas_tematicas", [])
            if isinstance(areas, str):
                areas = [a.strip() for a in areas.split(",") if a.strip()]
            
            # Guardar en base de datos
            try:
                from models.db import create_posgrado_program, get_posgrado_program, update_posgrado_program
                
                # Obtener ruta relativa del archivo para mejor trazabilidad
                base_dir = get_base_dir()
                sample_dir = os.path.join(base_dir, "static/sample_documents")
                if file_path.startswith(sample_dir):
                    relative_path = os.path.relpath(file_path, sample_dir)
                else:
                    relative_path = os.path.basename(file_path)
                
                # Convertir áreas a string si es lista
                areas_str = None
                if areas:
                    if isinstance(areas, list):
                        areas_str = ", ".join([str(a).strip() for a in areas if a])
                    else:
                        areas_str = str(areas)
                
                # Convertir otros campos a strings
                requisitos_str = str(program_info.get("requisitos", "")) if program_info.get("requisitos") else None
                modalidad_str = str(program_info.get("modalidad", "")) if program_info.get("modalidad") else None
                duracion_str = str(program_info.get("duracion", "")) if program_info.get("duracion") else None
                inversion_str = str(program_info.get("inversion", "")) if program_info.get("inversion") else None
                
                # Verificar si ya existe (por nombre o por archivo fuente)
                existing = get_posgrado_program(program_name=program_name, active_only=False)
                
                # Si no existe por nombre, buscar por archivo fuente
                if not existing:
                    all_programs = get_posgrado_program(active_only=False)
                    for prog in all_programs:
                        if prog.get("source_file") and relative_path in prog.get("source_file", ""):
                            existing = [prog]
                            break
                
                if existing:
                    # Actualizar programa existente
                    program_id = existing[0]['id']
                    update_posgrado_program(
                        program_id,
                        program_name=program_name,
                        program_type=program_type,
                        description=description,
                        areas_tematicas=areas_str,
                        requisitos=requisitos_str,
                        modalidad=modalidad_str,
                        duracion=duracion_str,
                        inversion=inversion_str,
                        metadata=program_info,
                        active=True
                    )
                    print(f"[DB] Programa actualizado en BD: {program_name} (ID: {program_id})")
                else:
                    # Crear nuevo programa
                    program_id = create_posgrado_program(
                        program_name=program_name,
                        program_type=program_type,
                        description=description,
                        areas_tematicas=areas_str,
                        requisitos=requisitos_str,
                        modalidad=modalidad_str,
                        duracion=duracion_str,
                        inversion=inversion_str,
                        source_file=relative_path,  # Guardar ruta relativa
                        source_type="document",
                        metadata=program_info
                    )
                    print(f"[DB] Programa guardado en BD: {program_name} (ID: {program_id}, Archivo: {relative_path})")
            except Exception as e:
                print(f"[WARNING] Error guardando programa en BD: {e}")
                import traceback
                traceback.print_exc()
            
            # Crear contenido estructurado para RAG
            content_parts = [
                f"Programa: {program_name}",
                f"Tipo: {program_type}",
                f"Descripción: {description}",
            ]
            
            if areas:
                content_parts.append(f"Áreas temáticas: {', '.join(areas)}")
            
            if program_info.get("requisitos"):
                content_parts.append(f"Requisitos: {program_info['requisitos']}")
            
            if program_info.get("modalidad"):
                content_parts.append(f"Modalidad: {program_info['modalidad']}")
            
            if program_info.get("duracion"):
                content_parts.append(f"Duración: {program_info['duracion']}")
            
            if program_info.get("inversion"):
                content_parts.append(f"Inversión: {program_info['inversion']}")
            
            # Agregar contenido completo al final
            content_parts.append(f"\n\nContenido completo:\n{full_content}")
            
            content = "\n".join(content_parts)
            
            # Obtener ruta relativa del archivo para metadata
            base_dir = get_base_dir()
            sample_dir = os.path.join(base_dir, "static/sample_documents")
            if file_path.startswith(sample_dir):
                relative_path = os.path.relpath(file_path, sample_dir)
            else:
                relative_path = os.path.basename(file_path)
            
            # Crear metadata
            metadata = {
                "source": relative_path,  # Ruta relativa para mejor trazabilidad
                "source_absolute": file_path,  # Ruta absoluta completa
                "file_type": "program_document",
                "source_type": "posgrado_program",
                "program_name": program_name,
                "program_type": program_type,
                "program_tag": "programa_posgrado",  # Etiqueta para recuperación
            }
            
            if areas:
                if isinstance(areas, list):
                    metadata["areas_tematicas"] = ", ".join([str(a) for a in areas])
                else:
                    metadata["areas_tematicas"] = str(areas)
            
            if program_info.get("modalidad"):
                metadata["modalidad"] = str(program_info["modalidad"])
            
            # Crear documento
            doc = Document(page_content=content, metadata=metadata)
            
            return [doc]
            
        except Exception as e:
            print(f"[ERROR] Error creating program documents: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def load_programs_to_rag(self, collection_name: str = "posgrado_programs") -> bool:
        """
        Cargar todos los documentos de programas al RAG.
        
        Args:
            collection_name: Nombre de la colección en ChromaDB
        
        Returns:
            True si fue exitoso
        """
        try:
            base_dir = get_base_dir()
            sample_dir = os.path.join(base_dir, "static/sample_documents")
            
            if not os.path.exists(sample_dir):
                print(f"[ERROR] Directory {sample_dir} not found")
                return False
            
            # Buscar archivos de programas (PDFs principalmente)
            import glob
            program_files = []
            
            # Buscar PDFs que parezcan ser programas
            pdf_files = glob.glob(os.path.join(sample_dir, "*.pdf"))
            for pdf_file in pdf_files:
                filename = os.path.basename(pdf_file).lower()
                # Filtrar solo archivos que parezcan programas (no preguntas)
                if "maestria" in filename or "mba" in filename or "especializacion" in filename or "doctorado" in filename:
                    program_files.append(pdf_file)
            
            # También buscar TXT de programas
            txt_files = glob.glob(os.path.join(sample_dir, "maestria_*.txt"))
            program_files.extend(txt_files)
            
            if not program_files:
                print("[WARNING] No program files found")
                return False
            
            print(f"[DATA] Found {len(program_files)} program files")
            
            # Crear documentos para cada programa
            all_documents = []
            for file_path in program_files:
                print(f"[LOADING] Processing: {os.path.basename(file_path)}")
                docs = self.create_program_documents(file_path)
                all_documents.extend(docs)
                print(f"[OK] Created {len(docs)} document(s) for {os.path.basename(file_path)}")
            
            if not all_documents:
                print("[WARNING] No documents created")
                return False
            
            print(f"[DATA] Created {len(all_documents)} total documents for RAG")
            
            # Cargar al RAG
            persist_directory = os.path.join(base_dir, "static/persist")
            os.makedirs(persist_directory, exist_ok=True)
            
            # Verificar si la colección existe
            collection_path = os.path.join(persist_directory, "chroma.sqlite3")
            collection_exists = os.path.exists(collection_path)
            
            if collection_exists:
                try:
                    vectordb = load_collection(collection_name)
                    print(f"[OK] Collection '{collection_name}' loaded, adding documents...")
                    vectordb = add_documents_to_collection(vectordb, all_documents)
                    print(f"[OK] Documents added to existing collection")
                    
                    # Marcar programas como cargados en RAG
                    try:
                        from models.db import update_posgrado_program, get_posgrado_program
                        for doc in all_documents:
                            program_name = doc.metadata.get("program_name", "")
                            if program_name:
                                existing = get_posgrado_program(program_name=program_name, active_only=False)
                                if existing:
                                    update_posgrado_program(existing[0]['id'], loaded_to_rag=True)
                    except Exception as e:
                        print(f"[WARNING] Error marcando programas como cargados en RAG: {e}")
                        
                except Exception as e:
                    print(f"[WARNING] Could not load existing collection: {e}")
                    print(f"[NOTE] Creating new collection...")
                    vectordb = create_collection(collection_name, all_documents)
                    if vectordb:
                        print(f"[OK] New collection '{collection_name}' created")
            else:
                vectordb = create_collection(collection_name, all_documents)
                if vectordb:
                    print(f"[OK] Collection '{collection_name}' created with {len(all_documents)} documents")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Error loading programs to RAG: {e}")
            import traceback
            traceback.print_exc()
            return False


# Singleton instance
_program_loader_instance = None

def get_program_loader() -> ProgramLoaderAgent:
    """Obtener instancia singleton del program loader agent"""
    global _program_loader_instance
    if _program_loader_instance is None:
        _program_loader_instance = ProgramLoaderAgent()
    return _program_loader_instance


if __name__ == "__main__":
    loader = get_program_loader()
    result = loader.load_programs_to_rag()
    print(f"\n[RESULT] Programs loaded: {result}")


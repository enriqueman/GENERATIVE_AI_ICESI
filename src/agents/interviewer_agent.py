"""
INTERVIEWER AGENT
Agente entrevistador para recopilar información del candidato a posgrado.

Responsabilidades:
1. Hacer preguntas secuenciales al candidato
2. Validar y extraer información de las respuestas
3. Construir un perfil progresivo del estudiante
4. Determinar cuándo el perfil está completo
"""

import os
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import pathlib
import environ

# Importar traceable para instrumentar funciones
try:
    from langsmith import traceable
    TRACEABLE_AVAILABLE = True
except ImportError:
    TRACEABLE_AVAILABLE = False
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

# Configurar environment
env = environ.Env()
env_path = pathlib.Path(__file__).resolve().parent.parent.parent / '.env'
environ.Env.read_env(str(env_path))

# Importar utilidades
try:
    from utils.tracing import tracer
    from tools.chat_memory import (
        store_interview_data,
        get_interview_data,
        clear_interview_data,
        check_interview_complete
    )
except ImportError:
    # Fallback si no están disponibles
    tracer = None
    def store_interview_data(*args, **kwargs): pass
    def get_interview_data(*args, **kwargs): return {}
    def clear_interview_data(*args, **kwargs): pass
    def check_interview_complete(*args, **kwargs): return False


# Estructura del perfil del estudiante (actualizada según JSON)
STUDENT_PROFILE_STRUCTURE = {
    "academico": {
        "titulo_pregrado": None,
        "universidad": None,
        "ano_graduacion": None,
        "posgrados_previos": None,
        "fortalezas": None
    },
    "laboral": {
        "sector": None,
        "cargo": None,
        "responsabilidades": None,
        "anos_experiencia": None,
        "intencion_cambio": None
    },
    "objetivos": {
        "meta_principal": None,
        "motivacion": None,
        "futuro_laboral": None,
        "enfoque_preferido": None,
        "enfasis": None
    },
    "logistica": {
        "modalidad_preferida": None,
        "ubicacion": None,
        "cambio_residencia": None,
        "tiempo_estudio": None,
        "horario_preferido": None
    },
    "economia": {
        "presupuesto": None,
        "opciones_financiacion": None,
        "convenios": None
    },
    "intereses": {
        "areas": None,
        "temas_clave": None,
        "temas_exclusion": None
    },
    "informacion_personal": {
        "nombre": None,
        "email": None,
        "telefono": None,
        "ciudad": None
    }
}


class InterviewerAgent:
    """
    Agente entrevistador que recopila información del candidato
    mediante una conversación estructurada dinámica.
    """

    def __init__(self):
        """Inicializar el agente entrevistador"""
        self.llm = None
        self.retriever = None
        self.questions_cache = []
        self._initialize()

    def _initialize(self):
        """Inicializar el modelo de lenguaje y retriever"""
        try:
            api_key = env("OPENAI_API_KEY")
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,  # Baja temperatura para ser más preciso en la extracción
                api_key=api_key
            )
            print("[OK] Interviewer Agent initialized with GPT-4o-mini")
            
            # Inicializar retriever para preguntas
            try:
                from utils.vector_functions import load_retriever, get_combined_retriever
                # Intentar cargar retriever de preguntas, si no existe usar el combinado
                try:
                    self.retriever = load_retriever("interview_questions", score_threshold=0.3)
                except:
                    self.retriever = get_combined_retriever(score_threshold=0.3)
                print("[OK] Retriever initialized for interview questions")
            except Exception as e:
                print(f"[WARNING] Could not initialize retriever: {e}")
                self.retriever = None
                
        except Exception as e:
            print(f"[WARNING] Could not initialize LLM for Interviewer: {e}")
            self.llm = None

    def _get_questions_from_db(self) -> List[Dict]:
        """Obtener preguntas desde la base de datos"""
        try:
            from models.db import get_interview_question
            questions = get_interview_question(active_only=True)
            if not questions:
                return []
            
            # Normalizar formato: asegurar que question_id sea string y agregar 'id' si falta
            normalized_questions = []
            for q in questions:
                q_normalized = dict(q)  # Copia
                # Asegurar que question_id sea string
                if "question_id" in q_normalized:
                    q_normalized["id"] = str(q_normalized["question_id"])
                elif "id" in q_normalized:
                    q_normalized["id"] = str(q_normalized["id"])
                    q_normalized["question_id"] = q_normalized["id"]
                normalized_questions.append(q_normalized)
            
            return normalized_questions
        except Exception as e:
            print(f"[WARNING] Error obteniendo preguntas de DB: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _get_questions_from_rag(self, query: str = "preguntas de entrevista para posgrados", k: int = 20) -> List[Dict]:
        """Obtener preguntas relevantes desde RAG"""
        if not self.retriever:
            return []
        
        try:
            # Usar invoke() si está disponible, sino get_relevant_documents()
            if hasattr(self.retriever, 'invoke'):
                docs = self.retriever.invoke(query)
            elif hasattr(self.retriever, 'get_relevant_documents'):
                docs = self.retriever.get_relevant_documents(query)
            else:
                # Intentar como función callable
                docs = self.retriever(query)
            
            # Asegurar que docs es una lista
            if not isinstance(docs, list):
                docs = list(docs) if docs else []
            
            questions = []
            
            for doc in docs[:k]:
                metadata = doc.metadata
                if metadata.get("file_type") == "interview_question":
                    question_id = metadata.get("question_id", "")
                    field = metadata.get("field", "")
                    category = metadata.get("category", "")
                    validation = metadata.get("validation", "text")
                    required = metadata.get("required", "True") == "True"
                    
                    # Extraer pregunta del contenido
                    content = doc.page_content
                    question_match = re.search(r'Pregunta:\s*(.+?)(?:\n|$)', content)
                    question_text = question_match.group(1).strip() if question_match else content.split("\n")[0]
                    
                    # Extraer field_secondary si existe
                    field_secondary = None
                    if "Campo secundario:" in content:
                        sec_match = re.search(r'Campo secundario:\s*(.+?)(?:\n|$)', content)
                        if sec_match:
                            field_secondary = sec_match.group(1).strip()
                    
                    questions.append({
                        "id": question_id,
                        "question": question_text,
                        "field": field,
                        "field_secondary": field_secondary,
                        "validation": validation,
                        "required": required,
                        "category": category,
                        "source": "rag"
                    })
            
            return questions
        except Exception as e:
            print(f"[WARNING] Error obteniendo preguntas de RAG: {e}")
            return []

    def _select_next_question(self, profile: Dict, answered_questions: List[str], session_id: str) -> Optional[Dict]:
        """
        Seleccionar la siguiente pregunta dinámicamente usando LLM basado en el perfil actual
        
        Args:
            profile: Perfil actual del estudiante
            answered_questions: Lista de IDs de preguntas ya respondidas
            session_id: ID de la sesión
        
        Returns:
            Diccionario con la pregunta seleccionada o None si está completo
        """
        # Obtener todas las preguntas disponibles
        db_questions = self._get_questions_from_db()
        rag_questions = self._get_questions_from_rag()
        
        # Combinar y deduplicar por question_id
        all_questions = {}
        for q in db_questions:
            all_questions[q.get("question_id", "")] = q
        for q in rag_questions:
            qid = q.get("id", "")
            if qid not in all_questions:
                all_questions[qid] = q
        
        # Filtrar preguntas ya respondidas (normalizar a strings para comparación)
        answered_questions_str = [str(qid) for qid in answered_questions]
        available_questions = [
            q for qid, q in all_questions.items() 
            if str(qid) not in answered_questions_str
        ]
        
        if not available_questions:
            return None
        
        # Si no hay LLM, usar lógica simple: priorizar requeridas no respondidas
        if not self.llm:
            # Priorizar preguntas requeridas
            required_questions = [q for q in available_questions if q.get("required", True)]
            if required_questions:
                # Seleccionar por categoría: primero información personal, luego académico, etc.
                priority_order = ["informacion_personal", "academico", "laboral", "objetivos", "intereses", "logistica", "economia"]
                for category in priority_order:
                    for q in required_questions:
                        field = q.get("field", "")
                        if field.startswith(category):
                            return q
                return required_questions[0]
            return available_questions[0]
        
        # Usar LLM para seleccionar la mejor pregunta
        try:
            # Construir contexto del perfil
            profile_summary = self._profile_to_summary(profile)
            
            # Construir lista de preguntas disponibles
            questions_text = "\n".join([
                f"- ID: {q.get('id', '')}, Campo: {q.get('field', '')}, Pregunta: {q.get('question', '')[:100]}"
                for q in available_questions[:15]  # Limitar a 15 para no sobrecargar
            ])
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Eres un asistente experto en entrevistas para admisiones de posgrados.
Tu tarea es seleccionar la mejor pregunta siguiente para hacer al candidato, basándote en:
1. El perfil actual del candidato
2. Las preguntas ya respondidas
3. La importancia de cada pregunta para construir un perfil completo

IMPORTANTE: 
- Prioriza terminar la entrevista lo antes posible cuando tengas información suficiente
- Un perfil está completo si tiene: título académico, sector laboral, objetivos principales, e intereses
- Si el perfil tiene estos 4 elementos críticos, responde "COMPLETO" inmediatamente
- Si faltan 1-2 elementos críticos, selecciona preguntas que los cubran
- Evita hacer preguntas redundantes o de bajo valor

Responde SOLO con el ID de la pregunta que consideras más apropiada en este momento.
Si el perfil está completo (tiene información suficiente para generar recomendaciones), responde "COMPLETO"."""),
                ("user", """Perfil actual del candidato:
{profile_summary}

Preguntas ya respondidas: {answered_ids}

Preguntas disponibles:
{questions_text}

INSTRUCCIONES:
- Selecciona preguntas que sean naturales y conversacionales
- Prefiere preguntas abiertas que inviten a respuestas detalladas
- Si el candidato ya ha dado información sobre un tema, no repitas preguntas similares
- Haz que la conversación fluya de manera amena

¿Cuál es la mejor pregunta siguiente? Responde solo con el ID. Si el perfil está completo, responde "COMPLETO".""")
            ])
            
            chain = prompt | self.llm
            # Asegurar que answered_questions son strings
            answered_ids_str = ", ".join([str(qid) for qid in answered_questions])
            response = chain.invoke({
                "profile_summary": profile_summary,
                "answered_ids": answered_ids_str,
                "questions_text": questions_text
            })
            
            selected_id = response.content.strip()
            
            if selected_id.upper() == "COMPLETO":
                return None
            
            # Buscar la pregunta seleccionada
            for q in available_questions:
                if q.get("id", "") == selected_id or q.get("question_id", "") == selected_id:
                    return q
            
            # Si no se encuentra, usar lógica de fallback
            required_questions = [q for q in available_questions if q.get("required", True)]
            return required_questions[0] if required_questions else available_questions[0]
            
        except Exception as e:
            print(f"[WARNING] Error seleccionando pregunta con LLM: {e}")
            # Fallback a lógica simple
            required_questions = [q for q in available_questions if q.get("required", True)]
            return required_questions[0] if required_questions else available_questions[0]

    def _profile_to_summary(self, profile: Dict) -> str:
        """Convertir perfil a texto resumido para el LLM"""
        parts = []
        
        for category, data in profile.items():
            if isinstance(data, dict):
                filled_fields = {k: v for k, v in data.items() if v is not None and v != []}
                if filled_fields:
                    parts.append(f"{category}: {', '.join([f'{k}={v}' for k, v in filled_fields.items()])}")
        
        return "\n".join(parts) if parts else "Perfil vacío"

    @traceable(name="InterviewerAgent.start_interview")
    def start_interview(self, session_id: str = "default_session") -> str:
        """
        Iniciar una nueva entrevista.

        Args:
            session_id: ID de la sesión del usuario

        Returns:
            Primera pregunta de la entrevista
        """
        # Limpiar datos previos
        clear_interview_data(session_id)

        # Inicializar perfil vacío
        profile = STUDENT_PROFILE_STRUCTURE.copy()
        store_interview_data(session_id, "profile", profile)
        store_interview_data(session_id, "answered_questions", [])
        store_interview_data(session_id, "completed", False)

        # Registrar en tracing
        if tracer:
            tracer.log(
                operation="INTERVIEW_START",
                message="Nueva entrevista iniciada",
                metadata={"session_id": session_id},
                level="INFO"
            )

        # Obtener primera pregunta (saludo/información personal)
        first_question = self._select_next_question(profile, [], session_id)
        
        if first_question:
            # Guardar pregunta actual para la próxima iteración
            store_interview_data(session_id, "current_question_data", first_question)
            
            # Si no hay pregunta de saludo, usar una genérica
            question_text = first_question.get("question", "")
            if not question_text:
                question_text = "¡Hola! Soy el asistente de admisiones de la Universidad ICESI. Estoy aquí para ayudarte a encontrar el posgrado perfecto para ti. Para comenzar, ¿cuál es tu nombre completo?"
            return question_text
        else:
            return "¡Hola! Soy el asistente de admisiones de la Universidad ICESI. Estoy aquí para ayudarte a encontrar el posgrado perfecto para ti. Para comenzar, ¿cuál es tu nombre completo?"

    @traceable(name="InterviewerAgent.process_answer")
    def process_answer(self, answer: str, session_id: str = "default_session", current_question_id: str = None) -> Dict[str, Any]:
        """
        Procesar la respuesta del usuario y avanzar en la entrevista.

        Args:
            answer: Respuesta del usuario
            session_id: ID de la sesión
            current_question_id: ID de la pregunta actual (opcional)

        Returns:
            {
                "next_question": str,
                "profile_complete": bool,
                "extracted_data": dict,
                "validation_error": str (opcional)
            }
        """
        try:
            # Obtener estado actual de la entrevista
            profile = get_interview_data(session_id, "profile") or STUDENT_PROFILE_STRUCTURE.copy()
            answered_questions = get_interview_data(session_id, "answered_questions") or []
            current_question_data = get_interview_data(session_id, "current_question_data") or {}

            # Si no hay current_question_id, intentar obtenerlo de current_question_data
            if not current_question_id:
                current_question_id = current_question_data.get("id") or current_question_data.get("question_id")

            # Obtener todas las preguntas para uso posterior
            db_questions = self._get_questions_from_db()
            rag_questions = self._get_questions_from_rag()
            all_questions = {}
            for q in db_questions:
                all_questions[q.get("question_id", "")] = q
            for q in rag_questions:
                all_questions[q.get("id", "")] = q
            
            # Si aún no hay, buscar la pregunta actual desde las disponibles
            if not current_question_id:
                # Obtener todas las preguntas y seleccionar la primera no respondida
                available = self._select_next_question(profile, answered_questions, session_id)
                if available:
                    current_question_id = available.get("id") or available.get("question_id")
                    current_question_data = available

            # Si no hay pregunta actual, usar la primera disponible
            if not current_question_data:
                current_question_data = self._select_next_question(profile, answered_questions, session_id)
                if current_question_data:
                    current_question_id = current_question_data.get("id") or current_question_data.get("question_id")

            if not current_question_data:
                # No hay más preguntas, entrevista completa
                store_interview_data(session_id, "completed", True)
                return {
                    "next_question": None,
                    "profile_complete": True,
                    "extracted_data": profile,
                    "message": "¡Perfecto! He recopilado toda la información necesaria. Ahora voy a analizar tu perfil para recomendarte los posgrados más adecuados."
                }

            # Extraer información de la respuesta
            extracted_data = self._extract_info_from_answer(answer, current_question_data, profile)
            
            # Debug: Log extracted data
            if tracer:
                tracer.log(
                    operation="DATA_EXTRACTION",
                    message="Datos extraídos de la respuesta",
                    metadata={
                        "answer": answer[:100],
                        "extracted_data": extracted_data,
                        "field": current_question_data.get("field", ""),
                        "question_id": current_question_id
                    },
                    level="INFO"
                )

            # Validar respuesta
            validation_result = self._validate_answer(answer, current_question_data)

            if not validation_result["valid"]:
                return {
                    "next_question": current_question_data.get("question", ""),
                    "profile_complete": False,
                    "validation_error": validation_result["error"],
                    "extracted_data": None
                }

            # Actualizar perfil con los datos extraídos
            profile = self._update_profile(profile, extracted_data, current_question_data)
            
            # Si la respuesta era larga y se extrajeron campos adicionales, actualizarlos también
            additional_fields = extracted_data.get("additional_fields", [])
            if additional_fields:
                # Obtener todas las preguntas para buscar campos adicionales
                db_questions = self._get_questions_from_db()
                rag_questions = self._get_questions_from_rag()
                all_questions = {}
                for q in db_questions:
                    all_questions[q.get("question_id", "")] = q
                for q in rag_questions:
                    all_questions[q.get("id", "")] = q
                
                for field_data in additional_fields:
                    field = field_data.get("field")
                    value = field_data.get("extracted_value")
                    if field and value:
                        # Crear un question_config temporal para el campo adicional
                        temp_question = {
                            "field": field,
                            "validation": "text"
                        }
                        temp_extracted = {
                            "extracted_value": value,
                            "confidence": field_data.get("confidence", "medium")
                        }
                        profile = self._update_profile(profile, temp_extracted, temp_question)
                        
                        # Marcar como respondida si existe la pregunta
                        for qid, q in all_questions.items():
                            if q.get("field") == field:
                                if str(qid) not in [str(aq) for aq in answered_questions]:
                                    answered_questions.append(str(qid))
                                    break

            # Guardar perfil actualizado
            store_interview_data(session_id, "profile", profile)

            # Marcar pregunta como respondida (asegurar que sea string)
            if current_question_id:
                current_question_id = str(current_question_id)
                # Convertir answered_questions a strings para comparación
                answered_questions_str = [str(qid) for qid in answered_questions]
                if current_question_id not in answered_questions_str:
                    answered_questions.append(current_question_id)
                    store_interview_data(session_id, "answered_questions", answered_questions)

            # Verificar si el perfil está completo (pasar número de preguntas respondidas)
            if self._is_profile_complete(profile, len(answered_questions)):
                store_interview_data(session_id, "completed", True)

                # Registrar en tracing
                if tracer:
                    tracer.log(
                        operation="INTERVIEW_COMPLETE",
                        message="Entrevista completada",
                        metadata={"session_id": session_id, "profile_keys": list(profile.keys())},
                        level="SUCCESS"
                    )

                return {
                    "next_question": None,
                    "profile_complete": True,
                    "extracted_data": profile,
                    "message": "¡Excelente! He recopilado toda la información necesaria. Ahora voy a analizar tu perfil para recomendarte los posgrados más adecuados para ti."
                }

            # Seleccionar siguiente pregunta dinámicamente
            next_q = self._select_next_question(profile, answered_questions, session_id)

            if not next_q:
                # No hay más preguntas relevantes
                store_interview_data(session_id, "completed", True)
                return {
                    "next_question": None,
                    "profile_complete": True,
                    "extracted_data": profile,
                    "message": "¡Excelente! He recopilado suficiente información. Ahora voy a analizar tu perfil para recomendarte los posgrados más adecuados para ti."
                }

            # Guardar pregunta actual para la próxima iteración
            store_interview_data(session_id, "current_question_data", next_q)

            # Personalizar pregunta con el nombre si está disponible
            original_question = next_q.get("question", "")
            if "{nombre}" in original_question and profile.get("informacion_personal", {}).get("nombre"):
                nombre = profile["informacion_personal"]["nombre"].split()[0]  # Primer nombre
                original_question = original_question.format(nombre=nombre)
            
            # Hacer la pregunta más amena usando IA
            next_question = self._make_question_amenable(original_question, profile)

            return {
                "next_question": next_question,
                "profile_complete": False,
                "extracted_data": extracted_data,
                "current_progress": str(len(answered_questions))  # Solo el número
            }

        except Exception as e:
            print(f"[ERROR] Error processing answer: {e}")
            import traceback
            traceback.print_exc()

            return {
                "next_question": "Lo siento, hubo un error procesando tu respuesta. ¿Podrías repetir lo que dijiste?",
                "profile_complete": False,
                "error": str(e)
            }

    def _is_profile_complete(self, profile: Dict, answered_questions_count: int = 0) -> bool:
        """
        Verificar si el perfil está completo basándose en campos requeridos.
        Optimizado para terminar la entrevista lo antes posible con información suficiente.
        NO requiere un mínimo fijo de preguntas - si hay información suficiente, está completo.
        
        Args:
            profile: Perfil del estudiante
            answered_questions_count: Número de preguntas respondidas
        
        Returns:
            True si el perfil tiene información suficiente para generar recomendaciones
        """
        # Verificar información básica crítica (mínimo necesario para recomendaciones)
        academico = profile.get("academico", {})
        laboral = profile.get("laboral", {})
        objetivos = profile.get("objetivos", {})
        intereses = profile.get("intereses", {})
        
        # Campos críticos mínimos:
        has_academic = academico.get("titulo_pregrado") is not None
        has_laboral = laboral.get("sector") is not None or laboral.get("cargo") is not None
        has_objetivos = objetivos.get("meta_principal") is not None
        has_intereses = intereses.get("areas") is not None or intereses.get("temas_clave") is not None
        
        # Contar campos críticos completos
        critical_fields = sum([has_academic, has_laboral, has_objetivos, has_intereses])
        
        # Si tiene todos los 4 campos críticos, está completo (sin importar número de preguntas)
        if critical_fields >= 4:
            return True
        
        # Si tiene 3 de los 4 campos críticos Y al menos 3 preguntas respondidas, está completo
        if critical_fields >= 3 and answered_questions_count >= 3:
            return True
        
        # Si tiene información muy rica en 2 campos críticos (con detalles), puede estar completo
        # Ejemplo: tiene formación + experiencia detallada + objetivos claros
        rich_academic = has_academic and (academico.get("fortalezas") or academico.get("institucion"))
        rich_laboral = has_laboral and (laboral.get("anos_experiencia") or laboral.get("responsabilidades"))
        rich_objetivos = has_objetivos and (objetivos.get("razones") or objetivos.get("expectativas"))
        
        if (rich_academic and rich_laboral and rich_objetivos) and answered_questions_count >= 3:
            return True
        
        # Verificación adicional: si tiene información en múltiples categorías
        categories_with_data = 0
        if academico.get("titulo_pregrado"):
            categories_with_data += 1
        if laboral.get("sector") or laboral.get("cargo"):
            categories_with_data += 1
        if objetivos.get("meta_principal"):
            categories_with_data += 1
        if intereses.get("areas") or intereses.get("temas_clave"):
            categories_with_data += 1
        if profile.get("logistica", {}).get("modalidad_preferida"):
            categories_with_data += 1
        
        # Si tiene información en al menos 3 categorías y mínimo 5 preguntas, está completo
        if categories_with_data >= 3 and answered_questions_count >= 5:
            return True
        
        return False

    def _extract_info_from_answer(self, answer: str, question_config: Dict, current_profile: Dict) -> Dict[str, Any]:
        """
        Extraer información estructurada de la respuesta usando LLM.
        Si la respuesta es larga, analiza el contexto completo para extraer múltiples campos.

        Args:
            answer: Respuesta del usuario
            question_config: Configuración de la pregunta actual
            current_profile: Perfil actual del estudiante

        Returns:
            Diccionario con la información extraída
        """
        if not self.llm:
            # Fallback: extracción simple sin LLM
            field = question_config.get("field", "")
            validation = question_config.get("validation", "text")
            
            if validation == "number":
                import re
                numbers = re.findall(r'\d+', answer)
                value = numbers[0] if numbers else answer
            elif validation == "list":
                items = [item.strip() for item in answer.replace(",", " ").split() if item.strip()]
                value = items if items else [answer]
            else:
                value = answer.strip()
            
            return {
                "extracted_value": value,
                "confidence": "low"
            }

        try:
            # Detectar si la respuesta es larga (más de 50 palabras o contiene múltiples oraciones)
            is_long_answer = len(answer.split()) > 50 or answer.count('.') > 2
            
            # Construir resumen del perfil actual ANTES de usarlo
            profile_summary = self._profile_to_summary(current_profile)
            
            # Si es una respuesta larga, hacer análisis completo del contexto
            if is_long_answer:
                return self._extract_multiple_fields_from_long_answer(answer, question_config, current_profile)
            
            # Extracción normal para respuestas cortas (pero con contexto completo)
            extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", """Eres un asistente experto en extraer información estructurada de respuestas de candidatos a posgrados.

Tu tarea es extraer información relevante de la respuesta del usuario, considerando TODO el contexto de la conversación y el perfil construido hasta ahora.

Campo solicitado: {field}
Tipo de validación: {validation}

CONTEXTO DEL PERFIL ACTUAL:
{profile_summary}

INSTRUCCIONES:
- Analiza la respuesta considerando el contexto completo del perfil
- Si la respuesta menciona información relacionada con otros campos del perfil, anótalo en secondary_value
- Si el campo es una lista, extrae múltiples items
- Si es texto, resume la información clave pero mantén los detalles importantes
- Si es contacto, extrae email y teléfono
- Si es numérico, extrae solo números
- Usa el contexto del perfil para interpretar mejor la respuesta (ej: si ya mencionó su formación, usa ese contexto)

IMPORTANTE: 
- Construye el perfil de forma incremental con cada respuesta
- Si detectas información adicional relevante, inclúyela en secondary_value
- Sé preciso pero también captura información relacionada

Formato de respuesta:
{{
    "extracted_value": "valor principal extraído",
    "secondary_value": "información adicional o contexto relevante",
    "confidence": "high/medium/low"
}}"""),
                ("user", "Respuesta del usuario: {answer}\n\nPregunta actual: {current_question}")
            ])

            chain = extraction_prompt | self.llm
            response = chain.invoke({
                "field": question_config.get("field", ""),
                "validation": question_config.get("validation", "text"),
                "answer": answer,
                "profile_summary": profile_summary,
                "current_question": question_config.get("question", "")
            })

            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            extracted = json.loads(content.strip())
            return extracted

        except Exception as e:
            print(f"[WARNING] LLM extraction failed: {e}")
            return {"extracted_value": answer, "confidence": "low"}

    def _extract_multiple_fields_from_long_answer(self, answer: str, current_question: Dict, current_profile: Dict) -> Dict[str, Any]:
        """
        Analizar respuestas largas y extraer múltiples campos del perfil en paralelo.
        
        Args:
            answer: Respuesta larga del usuario
            current_question: Pregunta actual
            current_profile: Perfil actual
            
        Returns:
            Diccionario con información extraída (puede incluir múltiples campos)
        """
        if not self.llm:
            # Fallback simple
            return {
                "extracted_value": answer[:200],
                "confidence": "low"
            }
        
        try:
            # Obtener todas las preguntas disponibles para saber qué campos buscar
            db_questions = self._get_questions_from_db()
            rag_questions = self._get_questions_from_rag()
            all_questions = {}
            for q in db_questions:
                all_questions[q.get("question_id", "")] = q
            for q in rag_questions:
                all_questions[q.get("id", "")] = q
            
            # Construir lista de campos relevantes que podrían estar en la respuesta
            profile_summary = self._profile_to_summary(current_profile)
            
            # Identificar campos faltantes o incompletos
            missing_fields = []
            field_descriptions = []
            
            for qid, q in all_questions.items():
                field = q.get("field", "")
                if field:
                    parts = field.split(".")
                    if len(parts) == 2:
                        category, subfield = parts
                        current_value = current_profile.get(category, {}).get(subfield)
                        if not current_value or (isinstance(current_value, str) and len(current_value.strip()) < 3):
                            missing_fields.append(field)
                            field_descriptions.append(f"{field}: {q.get('question', '')[:80]}")
            
            # Limitar a los 10 campos más relevantes
            relevant_fields = missing_fields[:10]
            fields_text = "\n".join(field_descriptions[:10])
            
            extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", """Eres un asistente experto en analizar respuestas extensas de candidatos a posgrados y extraer información estructurada.

Tu tarea es analizar la respuesta del usuario y extraer TODA la información relevante que pueda responder múltiples preguntas del perfil.

IMPORTANTE:
- Analiza la respuesta completa, no solo el campo solicitado
- Extrae información para múltiples campos si está disponible
- Si la respuesta menciona información sobre formación, experiencia, objetivos, intereses, etc., extráela
- Usa el contexto del perfil actual para entender mejor la información
- Si no encuentras información para un campo, déjalo como null

Campos que podrías encontrar en la respuesta:
{fields_list}

Perfil actual del candidato:
{profile_summary}

Formato de respuesta JSON:
{{
    "primary_field": {{
        "field": "campo.principal",
        "extracted_value": "valor extraído",
        "confidence": "high/medium/low"
    }},
    "additional_fields": [
        {{
            "field": "campo.adicional",
            "extracted_value": "valor",
            "confidence": "high/medium/low"
        }}
    ],
    "summary": "Resumen breve de lo que se extrajo"
}}"""),
                ("user", """Pregunta actual: {current_question}

Respuesta del usuario: {answer}

Analiza esta respuesta y extrae toda la información relevante que puedas identificar.""")
            ])
            
            chain = extraction_prompt | self.llm
            response = chain.invoke({
                "current_question": current_question.get("question", ""),
                "answer": answer,
                "fields_list": fields_text,
                "profile_summary": profile_summary
            })
            
            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            
            # Retornar en formato compatible con el sistema actual
            primary = result.get("primary_field", {})
            if primary.get("field") == current_question.get("field"):
                extracted = {
                    "extracted_value": primary.get("extracted_value", answer[:200]),
                    "secondary_value": result.get("summary", ""),
                    "confidence": primary.get("confidence", "medium"),
                    "additional_fields": result.get("additional_fields", [])
                }
            else:
                # Si el campo principal no coincide, usar el primero disponible
                extracted = {
                    "extracted_value": primary.get("extracted_value", answer[:200]) if primary else answer[:200],
                    "secondary_value": result.get("summary", ""),
                    "confidence": "medium",
                    "additional_fields": result.get("additional_fields", [])
                }
            
            return extracted
            
        except Exception as e:
            print(f"[WARNING] Error extracting multiple fields: {e}")
            import traceback
            traceback.print_exc()
            return {
                "extracted_value": answer[:200],
                "confidence": "low"
            }

    def _validate_answer(self, answer: str, question_config: Dict) -> Dict[str, Any]:
        """
        Validar que la respuesta sea adecuada para la pregunta.

        Args:
            answer: Respuesta del usuario
            question_config: Configuración de la pregunta

        Returns:
            {"valid": bool, "error": str (opcional)}
        """
        # Respuesta muy corta
        if len(answer.strip()) < 3:
            return {
                "valid": False,
                "error": "Por favor, proporciona una respuesta más detallada."
            }

        validation_type = question_config.get("validation", "text")

        # Validación de contacto (email)
        if validation_type == "contact":
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            if not re.search(email_pattern, answer):
                return {
                    "valid": False,
                    "error": "Por favor, proporciona un email válido."
                }

        # Validación de lista (al menos 2 palabras significativas)
        if validation_type == "list":
            words = [w for w in answer.split() if len(w) > 3]
            if len(words) < 2:
                return {
                    "valid": False,
                    "error": "Por favor, menciona al menos 2 áreas o temas de interés."
                }

        return {"valid": True}

    def _update_profile(self, profile: Dict, extracted_data: Dict, question_config: Dict) -> Dict:
        """
        Actualizar el perfil del estudiante con los datos extraídos.

        Args:
            profile: Perfil actual
            extracted_data: Datos extraídos de la respuesta
            question_config: Configuración de la pregunta

        Returns:
            Perfil actualizado
        """
        field = question_config.get("field")
        if not field:
            return profile

        # Dividir el campo en categoría y subcampo
        parts = field.split(".")
        if len(parts) != 2:
            return profile

        category, subfield = parts

        # Asegurar que la categoría existe
        if category not in profile:
            profile[category] = {}

        # Actualizar valor principal
        value = extracted_data.get("extracted_value")
        if value:
            if question_config.get("validation") == "list":
                # Convertir a lista si es necesario
                if isinstance(value, str):
                    value = [item.strip() for item in value.split(",") if item.strip()]
            profile[category][subfield] = value

        # Actualizar valor secundario si existe
        field_secondary = question_config.get("field_secondary")
        if field_secondary and extracted_data.get("secondary_value"):
            parts_sec = field_secondary.split(".")
            if len(parts_sec) == 2:
                category_sec, subfield_sec = parts_sec
                if category_sec not in profile:
                    profile[category_sec] = {}
                profile[category_sec][subfield_sec] = extracted_data["secondary_value"]

        return profile

    def get_current_profile(self, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Obtener el perfil actual del estudiante.

        Args:
            session_id: ID de la sesión

        Returns:
            Perfil del estudiante
        """
        return get_interview_data(session_id, "profile") or {}

    def is_interview_complete(self, session_id: str = "default_session") -> bool:
        """
        Verificar si la entrevista está completa.

        Args:
            session_id: ID de la sesión

        Returns:
            True si está completa, False en caso contrario
        """
        return get_interview_data(session_id, "completed") or False
    
    def _make_question_amenable(self, original_question: str, profile: Dict) -> str:
        """
        Hacer la pregunta más amena y conversacional usando IA, sin demasiado texto.
        
        Args:
            original_question: Pregunta original
            profile: Perfil actual del estudiante
            
        Returns:
            Pregunta más amena y conversacional
        """
        if not self.llm:
            return original_question
        
        try:
            nombre = profile.get("informacion_personal", {}).get("nombre", "")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Eres un asistente amigable que hace preguntas de manera conversacional y amena.

Tu tarea es reformular una pregunta para que sea más amigable, natural y conversacional, pero SIN agregar demasiado texto.

REGLAS:
- Mantén la pregunta corta y directa (máximo 2 oraciones)
- Hazla más amigable y conversacional
- Usa un tono cálido pero profesional
- NO agregues explicaciones largas
- NO cambies el significado de la pregunta
- Si hay un nombre, úsalo de manera natural

Ejemplos:
- "¿Cuál es tu título de pregrado?" → "¿Qué estudiaste en tu pregrado?"
- "¿En qué sector trabajas?" → "¿En qué área te desempeñas profesionalmente?"
- "¿Cuáles son tus objetivos?" → "¿Qué te gustaría lograr con un posgrado?"

Responde SOLO con la pregunta reformulada, sin texto adicional."""),
                ("user", """Pregunta original: {original_question}
Nombre del candidato: {nombre}

Reformula esta pregunta de manera más amena y conversacional, manteniéndola corta.""")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({
                "original_question": original_question,
                "nombre": nombre if nombre else "el candidato"
            })
            
            improved_question = response.content.strip()
            
            # Limpiar si tiene comillas o markdown
            if improved_question.startswith('"') and improved_question.endswith('"'):
                improved_question = improved_question[1:-1]
            if improved_question.startswith("'") and improved_question.endswith("'"):
                improved_question = improved_question[1:-1]
            
            return improved_question
            
        except Exception as e:
            print(f"[WARNING] Error making question amenable: {e}")
            return original_question


# Singleton instance
_interviewer_instance = None

def get_interviewer() -> InterviewerAgent:
    """Obtener instancia singleton del interviewer agent"""
    global _interviewer_instance
    if _interviewer_instance is None:
        _interviewer_instance = InterviewerAgent()
    return _interviewer_instance


# Para testing
if __name__ == "__main__":
    interviewer = get_interviewer()

    # Iniciar entrevista
    first_question = interviewer.start_interview("test_session")
    print(f"Pregunta 1: {first_question}")

    # Simular respuestas
    answers = [
        "Mi nombre es Juan Pérez",
        "Estudié Ingeniería de Sistemas en la Universidad del Valle",
        "Tengo 5 años de experiencia en desarrollo de software",
        "Me interesan la inteligencia artificial y el análisis de datos",
        "Quiero especializarme en machine learning para liderar proyectos de IA",
        "Tengo habilidades en Python, machine learning, y gestión de proyectos",
        "Prefiero estudiar tiempo parcial en horario nocturno",
        "Mi email es juan.perez@example.com y mi teléfono es 3001234567"
    ]

    for i, answer in enumerate(answers):
        print(f"\nRespuesta {i+1}: {answer}")
        result = interviewer.process_answer(answer, "test_session")

        if result.get("next_question"):
            print(f"Siguiente pregunta: {result['next_question']}")

        if result.get("profile_complete"):
            print("\n[SUCCESS] Entrevista completada!")
            print(f"Perfil final: {json.dumps(result['extracted_data'], indent=2, ensure_ascii=False)}")
            break

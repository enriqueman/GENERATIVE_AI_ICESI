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


# Estructura del perfil del estudiante
STUDENT_PROFILE_STRUCTURE = {
    "formacion_academica": {
        "pregrado": None,  # Carrera de pregrado
        "universidad": None,  # Universidad de origen
        "ano_graduacion": None  # Año de graduación
    },
    "experiencia_laboral": {
        "anos_experiencia": None,  # Años de experiencia
        "area_trabajo": None,  # Área de trabajo actual
        "cargo_actual": None  # Cargo o rol actual
    },
    "intereses": {
        "areas_interes": [],  # Lista de áreas de interés
        "objetivos_carrera": None,  # Objetivos profesionales
        "motivacion": None  # Motivación para el posgrado
    },
    "habilidades": {
        "habilidades_tecnicas": [],  # Lista de habilidades técnicas
        "habilidades_blandas": [],  # Lista de habilidades blandas
        "idiomas": []  # Idiomas que maneja
    },
    "disponibilidad": {
        "modalidad": None,  # "tiempo_completo", "tiempo_parcial", "virtual"
        "horario_preferido": None,  # "diurno", "nocturno", "fines_de_semana"
        "inicio_deseado": None  # Cuándo desea iniciar
    },
    "informacion_personal": {
        "nombre": None,
        "email": None,
        "telefono": None,
        "ciudad": None
    }
}


# Secuencia de preguntas de la entrevista
INTERVIEW_QUESTIONS = [
    {
        "id": "saludo",
        "question": "¡Hola! Soy el asistente de admisiones de la Universidad ICESI. Estoy aquí para ayudarte a encontrar el posgrado perfecto para ti. Para comenzar, ¿cuál es tu nombre completo?",
        "field": "informacion_personal.nombre",
        "validation": "text",
        "required": True
    },
    {
        "id": "formacion",
        "question": "Excelente, {nombre}. Cuéntame sobre tu formación académica. ¿Qué carrera de pregrado estudiaste y en qué universidad?",
        "field": "formacion_academica.pregrado",
        "field_secondary": "formacion_academica.universidad",
        "validation": "text",
        "required": True
    },
    {
        "id": "experiencia",
        "question": "Perfecto. Ahora háblame de tu experiencia profesional. ¿Cuántos años de experiencia laboral tienes y en qué área trabajas actualmente?",
        "field": "experiencia_laboral.anos_experiencia",
        "field_secondary": "experiencia_laboral.area_trabajo",
        "validation": "text",
        "required": True
    },
    {
        "id": "intereses",
        "question": "Me gustaría conocer tus intereses. ¿Qué áreas o temas te apasionan profesionalmente? ¿Hay algún campo específico en el que te gustaría especializarte?",
        "field": "intereses.areas_interes",
        "validation": "list",
        "required": True
    },
    {
        "id": "objetivos",
        "question": "¿Cuáles son tus objetivos profesionales a mediano y largo plazo? ¿Qué esperas lograr con un posgrado?",
        "field": "intereses.objetivos_carrera",
        "field_secondary": "intereses.motivacion",
        "validation": "text",
        "required": True
    },
    {
        "id": "habilidades",
        "question": "¿Qué habilidades técnicas o especializadas posees? Por ejemplo: programación, análisis de datos, gestión de proyectos, marketing digital, etc.",
        "field": "habilidades.habilidades_tecnicas",
        "validation": "list",
        "required": False
    },
    {
        "id": "disponibilidad",
        "question": "Finalmente, cuéntame sobre tu disponibilidad. ¿Prefieres estudiar tiempo completo, tiempo parcial, o de forma virtual? ¿Qué horario te acomoda mejor?",
        "field": "disponibilidad.modalidad",
        "field_secondary": "disponibilidad.horario_preferido",
        "validation": "text",
        "required": True
    },
    {
        "id": "contacto",
        "question": "Para poder enviarte información personalizada, necesito tus datos de contacto. ¿Cuál es tu email y número de teléfono?",
        "field": "informacion_personal.email",
        "field_secondary": "informacion_personal.telefono",
        "validation": "contact",
        "required": True
    }
]


class InterviewerAgent:
    """
    Agente entrevistador que recopila información del candidato
    mediante una conversación estructurada.
    """

    def __init__(self):
        """Inicializar el agente entrevistador"""
        self.llm = None
        self.current_question_index = 0
        self._initialize()

    def _initialize(self):
        """Inicializar el modelo de lenguaje"""
        try:
            api_key = env("OPENAI_API_KEY")
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,  # Baja temperatura para ser más preciso en la extracción
                api_key=api_key
            )
            print("[OK] Interviewer Agent initialized with GPT-4o-mini")
        except Exception as e:
            print(f"[WARNING] Could not initialize LLM for Interviewer: {e}")
            self.llm = None

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
        store_interview_data(session_id, "current_question", 0)
        store_interview_data(session_id, "completed", False)

        # Registrar en tracing
        if tracer:
            tracer.log(
                operation="INTERVIEW_START",
                message="Nueva entrevista iniciada",
                metadata={"session_id": session_id},
                level="INFO"
            )

        # Retornar primera pregunta
        return INTERVIEW_QUESTIONS[0]["question"]

    def process_answer(self, answer: str, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Procesar la respuesta del usuario y avanzar en la entrevista.

        Args:
            answer: Respuesta del usuario
            session_id: ID de la sesión

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
            current_index = get_interview_data(session_id, "current_question") or 0
            profile = get_interview_data(session_id, "profile") or STUDENT_PROFILE_STRUCTURE.copy()

            if current_index >= len(INTERVIEW_QUESTIONS):
                return {
                    "next_question": None,
                    "profile_complete": True,
                    "extracted_data": profile,
                    "message": "¡Perfecto! He recopilado toda la información necesaria. Ahora voy a analizar tu perfil para recomendarte los posgrados más adecuados."
                }

            current_q = INTERVIEW_QUESTIONS[current_index]

            # Extraer información de la respuesta
            extracted_data = self._extract_info_from_answer(answer, current_q, profile)

            # Validar respuesta
            validation_result = self._validate_answer(answer, current_q)

            if not validation_result["valid"]:
                return {
                    "next_question": current_q["question"],
                    "profile_complete": False,
                    "validation_error": validation_result["error"],
                    "extracted_data": None
                }

            # Actualizar perfil con los datos extraídos
            profile = self._update_profile(profile, extracted_data, current_q)

            # Guardar perfil actualizado
            store_interview_data(session_id, "profile", profile)

            # Avanzar a la siguiente pregunta
            next_index = current_index + 1
            store_interview_data(session_id, "current_question", next_index)

            # Verificar si la entrevista está completa
            if next_index >= len(INTERVIEW_QUESTIONS):
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

            # Obtener siguiente pregunta
            next_q = INTERVIEW_QUESTIONS[next_index]

            # Personalizar pregunta con el nombre si está disponible
            next_question = next_q["question"]
            if "{nombre}" in next_question and profile.get("informacion_personal", {}).get("nombre"):
                nombre = profile["informacion_personal"]["nombre"].split()[0]  # Primer nombre
                next_question = next_question.format(nombre=nombre)

            return {
                "next_question": next_question,
                "profile_complete": False,
                "extracted_data": extracted_data,
                "current_progress": f"{next_index}/{len(INTERVIEW_QUESTIONS)} preguntas completadas"
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

    def _extract_info_from_answer(self, answer: str, question_config: Dict, current_profile: Dict) -> Dict[str, Any]:
        """
        Extraer información estructurada de la respuesta usando LLM.

        Args:
            answer: Respuesta del usuario
            question_config: Configuración de la pregunta actual
            current_profile: Perfil actual del estudiante

        Returns:
            Diccionario con la información extraída
        """
        if not self.llm:
            # Fallback: extracción simple sin LLM
            return {"raw_answer": answer}

        try:
            # Crear prompt para extracción
            extraction_prompt = ChatPromptTemplate.from_messages([
                ("system", """Eres un asistente experto en extraer información estructurada de respuestas de candidatos a posgrados.

Extrae la información relevante de la respuesta del usuario según el campo solicitado.
Devuelve SOLO un JSON válido sin texto adicional.

Campo solicitado: {field}
Tipo de validación: {validation}

Reglas de extracción:
- Si el campo es una lista, extrae múltiples items
- Si es texto, resume la información clave
- Si es contacto, extrae email y teléfono
- Si es numérico, extrae solo números

Formato de respuesta:
{{
    "extracted_value": "valor principal extraído",
    "secondary_value": "valor secundario si aplica",
    "confidence": "high/medium/low"
}}"""),
                ("user", "Respuesta del usuario: {answer}")
            ])

            # Invocar LLM
            chain = extraction_prompt | self.llm
            response = chain.invoke({
                "field": question_config.get("field", ""),
                "validation": question_config.get("validation", "text"),
                "answer": answer
            })

            # Parsear respuesta JSON
            content = response.content
            # Limpiar markdown si existe
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            extracted = json.loads(content.strip())
            return extracted

        except Exception as e:
            print(f"[WARNING] LLM extraction failed: {e}")
            # Fallback a extracción simple
            return {"extracted_value": answer, "confidence": "low"}

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

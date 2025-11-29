"""
RECOMMENDER AGENT
Agente recomendador que genera recomendaciones personalizadas de posgrados
en lenguaje natural basándose en el análisis del PROFILER Agent.

Responsabilidades:
1. Recibir resultados del análisis del PROFILER
2. Generar recomendaciones personalizadas en lenguaje natural
3. Explicar por qué cada programa es adecuado
4. Proporcionar próximos pasos y llamados a la acción
5. Incluir información relevante de cada programa (inversión, duración, etc.)
"""

import os
import json
from typing import Dict, List, Any, Optional
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
    from utils.vector_functions import load_retriever, generate_answer_from_context
except ImportError as e:
    print(f"[WARNING] Import error in recommender_agent: {e}")
    tracer = None
    def load_retriever(*args, **kwargs): return None
    def generate_answer_from_context(*args, **kwargs): return "Error: RAG not available"


class RecommenderAgent:
    """
    Agente recomendador que genera recomendaciones personalizadas
    """

    def __init__(self):
        """Inicializar el agente recomendador"""
        self.llm = None
        self.retriever = None
        self._initialize()

    def _initialize(self):
        """Inicializar el modelo de lenguaje y el retriever"""
        try:
            api_key = env("OPENAI_API_KEY")
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,  # Temperatura media para respuestas naturales pero precisas
                api_key=api_key,
                max_tokens=1500
            )
            print("[OK] Recommender Agent initialized with GPT-4o-mini")

            # Inicializar retriever
            self.retriever = load_retriever("sample_documents", score_threshold=0.3)
            print("[OK] Vector retriever initialized for recommendations")

        except Exception as e:
            print(f"[WARNING] Could not initialize Recommender Agent: {e}")
            self.llm = None
            self.retriever = None

    @traceable(name="RecommenderAgent.generate_recommendation")
    def generate_recommendation(
        self,
        profiler_results: Dict[str, Any],
        student_profile: Dict[str, Any]
    ) -> str:
        """
        Generar recomendación personalizada en lenguaje natural.

        Args:
            profiler_results: Resultados del análisis del PROFILER Agent
            student_profile: Perfil completo del estudiante

        Returns:
            Recomendación personalizada como string
        """
        try:
            top_matches = profiler_results.get("top_matches", [])
            profile_summary = profiler_results.get("profile_summary", "")

            if not top_matches:
                return self._generate_no_matches_response(student_profile)

            # Si hay LLM disponible, generar recomendación con IA
            if self.llm:
                recommendation = self._generate_llm_recommendation(
                    top_matches,
                    profile_summary,
                    student_profile
                )
            else:
                # Fallback: generar recomendación sin LLM
                recommendation = self._generate_fallback_recommendation(
                    top_matches,
                    profile_summary
                )

            # Enriquecer con información adicional del RAG
            enriched_recommendation = self._enrich_with_rag_info(recommendation, top_matches)

            # Registrar en tracing
            if tracer:
                tracer.log(
                    operation="RECOMMENDATION_GENERATED",
                    message="Recomendación generada para estudiante",
                    metadata={"programs": [m["program_name"] for m in top_matches[:3]]},
                    level="SUCCESS"
                )

            return enriched_recommendation

        except Exception as e:
            print(f"[ERROR] Error generating recommendation: {e}")
            import traceback
            traceback.print_exc()

            return self._generate_error_response()

    def _generate_llm_recommendation(
        self,
        top_matches: List[Dict],
        profile_summary: str,
        student_profile: Dict
    ) -> str:
        """Generar recomendación usando LLM"""
        try:
            # Preparar información de los programas
            programs_info = []
            for i, match in enumerate(top_matches[:3], 1):
                program_info = f"""
Programa {i}: {match['program_name']}
- Score de afinidad: {match['score']}/100
- Razones principales:
{chr(10).join([f"  • {reason}" for reason in match['reasons']])}
"""
                programs_info.append(program_info)

            programs_text = "\n".join(programs_info)

            # Crear prompt para el LLM
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Eres un asesor educativo experto de la Universidad ICESI especializado en orientación vocacional para posgrados.

Tu tarea es generar una recomendación PERSONALIZADA, CÁLIDA y PROFESIONAL para un candidato a posgrado.

ESTRUCTURA DE TU RESPUESTA:
1. Saludo personalizado mencionando el nombre del candidato (SIEMPRE usa el nombre, nunca "None")
2. Resumen breve de su perfil (2-3 oraciones)
3. Presentación de los 3 programas recomendados:
   - Para cada programa:
     * Nombre del programa
     * Por qué es ideal para el candidato (2-3 razones específicas)
     * Qué lo hace destacar
4. Programa TOP recomendado con explicación detallada
5. Próximos pasos concretos y claros
6. Llamado a la acción con información de contacto

TONO:
- Profesional pero cercano
- Entusiasta y motivador
- Específico y personalizado (usa el nombre del candidato)
- Evita ser genérico

IMPORTANTE:
- SIEMPRE usa el nombre del candidato en el saludo, NUNCA uses "None" o "Estudiante" si hay nombre disponible
- NO inventes información sobre los programas
- NO menciones precios específicos (eso viene después)
- Sé específico sobre por qué cada programa es adecuado
- Máximo 400 palabras"""),
                ("user", """Candidato: {profile_summary}
Nombre: {nombre}

Programas analizados:
{programs_info}

Genera una recomendación personalizada y motivadora. SIEMPRE usa el nombre del candidato en el saludo.""")
            ])

            # Extraer nombre del perfil
            nombre = (
                student_profile.get("informacion_personal", {}).get("nombre") or
                "Estudiante"
            )
            if not nombre or nombre == "None" or str(nombre).strip() == "":
                nombre = "Estudiante"
            
            # Generar recomendación
            chain = prompt | self.llm
            response = chain.invoke({
                "profile_summary": profile_summary,
                "nombre": nombre,
                "programs_info": programs_text
            })

            return response.content

        except Exception as e:
            print(f"[ERROR] LLM recommendation generation failed: {e}")
            return self._generate_fallback_recommendation(top_matches, profile_summary)

    def _generate_fallback_recommendation(
        self,
        top_matches: List[Dict],
        profile_summary: str
    ) -> str:
        """Generar recomendación sin LLM (fallback)"""

        recommendation = f"""Hola,

{profile_summary}

Basado en tu perfil, he identificado los programas de posgrado más adecuados para ti:

"""

        for i, match in enumerate(top_matches[:3], 1):
            recommendation += f"""
{i}. **{match['program_name']}** (Afinidad: {match['score']}/100)

Razones por las que es ideal para ti:
"""
            for reason in match['reasons']:
                recommendation += f"   • {reason}\n"

            recommendation += "\n"

        # Agregar programa top recomendado
        top_program = top_matches[0]
        recommendation += f"""
📌 **MI RECOMENDACIÓN PRINCIPAL: {top_program['program_name']}**

Este programa destaca por su alto nivel de afinidad con tu perfil ({top_program['score']}/100).
{top_program['reasons'][0] if top_program['reasons'] else 'Es la mejor opción para tus objetivos profesionales.'}

"""

        # Próximos pasos
        recommendation += """
**PRÓXIMOS PASOS:**

1. Revisa la información detallada de cada programa
2. Consulta los requisitos de admisión específicos
3. Agenda una cita con nuestro equipo de admisiones
4. Prepara tu documentación para el proceso de admisión

**CONTACTO:**
📧 admisiones.posgrados@icesi.edu.co
📱 WhatsApp: +57 318 765 4321
🌐 www.icesi.edu.co/posgrados

¡Estamos aquí para ayudarte en tu proceso de admisión!
"""

        return recommendation

    def _enrich_with_rag_info(self, recommendation: str, top_matches: List[Dict]) -> str:
        """Enriquecer la recomendación con información adicional del RAG"""
        try:
            if not self.retriever:
                return recommendation

            # Obtener información detallada del programa top
            top_program = top_matches[0]
            query = f"Información sobre {top_program['program_name']}: inversión, duración, requisitos, contacto"

            # Consultar RAG - usar método disponible
            if hasattr(self.retriever, 'invoke'):
                docs = self.retriever.invoke(query)
            elif hasattr(self.retriever, 'get_relevant_documents'):
                docs = self.retriever.get_relevant_documents(query)
            else:
                docs = self.retriever(query) if callable(self.retriever) else []
            
            if not isinstance(docs, list):
                docs = list(docs) if docs else []

            if docs:
                # Extraer información relevante
                rag_info = docs[0].page_content

                # Agregar información adicional al final
                additional_info = f"""

---

**INFORMACIÓN ADICIONAL DEL PROGRAMA TOP:**

{rag_info[:800]}...

Para información completa, consulta nuestra página web o contáctanos directamente.
"""
                recommendation += additional_info

            return recommendation

        except Exception as e:
            print(f"[WARNING] Could not enrich with RAG info: {e}")
            return recommendation

    def _generate_no_matches_response(self, student_profile: Dict) -> str:
        """Generar respuesta cuando no hay matches"""
        nombre = student_profile.get("informacion_personal", {}).get("nombre", "")

        return f"""Hola {nombre},

Gracias por completar la entrevista. He analizado tu perfil cuidadosamente.

Aunque tu perfil es muy interesante, me gustaría tener una conversación más detallada contigo para recomendarte el programa más adecuado.

**Te invito a:**
1. Agendar una cita con nuestro equipo de admisiones
2. Realizar un assessment vocacional más profundo
3. Explorar opciones de nivelación si es necesario

**CONTACTO DIRECTO:**
📧 admisiones.posgrados@icesi.edu.co
📱 WhatsApp: +57 318 765 4321

Nuestro equipo estará encantado de ayudarte a encontrar el programa perfecto para ti.

¡Te esperamos!
"""

    def _generate_error_response(self) -> str:
        """Generar respuesta de error"""
        return """Lo siento, hubo un error al generar tu recomendación personalizada.

Por favor, contacta directamente a nuestro equipo de admisiones:

📧 admisiones.posgrados@icesi.edu.co
📱 WhatsApp: +57 318 765 4321
🌐 www.icesi.edu.co/posgrados

Estaremos encantados de ayudarte personalmente en tu proceso de selección de posgrado.
"""

    def get_program_details(self, program_name: str) -> str:
        """
        Obtener detalles específicos de un programa usando RAG.

        Args:
            program_name: Nombre del programa

        Returns:
            Información detallada del programa
        """
        try:
            if not self.retriever:
                return f"No hay información disponible sobre {program_name} en este momento."

            # Consultar RAG con pregunta específica
            query = f"Dame información completa sobre {program_name}: requisitos, inversión, duración, plan de estudios, contacto"
            response = generate_answer_from_context(self.retriever, query, enable_logging=False)

            return response

        except Exception as e:
            print(f"[ERROR] Could not get program details: {e}")
            return f"Error al obtener información de {program_name}. Por favor, contacta admisiones directamente."

    def answer_specific_question(self, question: str, context: Dict = None) -> str:
        """
        Responder preguntas específicas sobre posgrados.

        Args:
            question: Pregunta del usuario
            context: Contexto adicional (opcional)

        Returns:
            Respuesta a la pregunta
        """
        try:
            if not self.retriever:
                return "Lo siento, no puedo responder preguntas en este momento. Por favor, contacta admisiones."

            # Usar RAG para responder
            response = generate_answer_from_context(self.retriever, question, enable_logging=False)

            return response

        except Exception as e:
            print(f"[ERROR] Could not answer question: {e}")
            return "Lo siento, no pude procesar tu pregunta. ¿Podrías reformularla?"


# Singleton instance
_recommender_instance = None

def get_recommender() -> RecommenderAgent:
    """Obtener instancia singleton del recommender agent"""
    global _recommender_instance
    if _recommender_instance is None:
        _recommender_instance = RecommenderAgent()
    return _recommender_instance


# Para testing
if __name__ == "__main__":
    recommender = get_recommender()

    # Resultados de prueba del profiler
    test_profiler_results = {
        "top_matches": [
            {
                "program_name": "Maestría en Ciencia de Datos",
                "score": 92.5,
                "reasons": [
                    "Tu formación en Ingeniería de Sistemas es ideal",
                    "Tu experiencia en machine learning es muy relevante",
                    "Tus habilidades en Python y TensorFlow son perfectas"
                ]
            },
            {
                "program_name": "Maestría en Ingeniería de Software",
                "score": 85.3,
                "reasons": [
                    "Tu experiencia en desarrollo de software es excelente",
                    "Tu formación técnica es adecuada",
                    "Tienes las habilidades técnicas requeridas"
                ]
            },
            {
                "program_name": "MBA - Administración",
                "score": 65.0,
                "reasons": [
                    "Tu experiencia puede ser valiosa",
                    "El programa acepta profesionales de cualquier área"
                ]
            }
        ],
        "profile_summary": "Juan Pérez es un profesional con formación en ingeniería de sistemas y 5 años de experiencia. Sus principales intereses incluyen inteligencia artificial, análisis de datos, machine learning."
    }

    test_profile = {
        "informacion_personal": {
            "nombre": "Juan Pérez"
        }
    }

    print("\n[TEST] Generating recommendation...")
    recommendation = recommender.generate_recommendation(test_profiler_results, test_profile)
    print("\n" + "="*80)
    print(recommendation)
    print("="*80)

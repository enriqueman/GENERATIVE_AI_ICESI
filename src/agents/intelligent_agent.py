"""
Agente Inteligente Principal - Universidad ICESI
Sistema de Recomendación de Posgrados

Este agente coordina el flujo completo:
1. INTERVIEWER Agent: Recopila información del candidato
2. PROFILER Agent: Analiza el perfil y calcula matches
3. RECOMMENDER Agent: Genera recomendaciones personalizadas
"""

import os
import sys
import time
from typing import Dict, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.tracing import tracer
from agents.interviewer_agent import get_interviewer
from agents.profiler_agent import get_profiler
from agents.recommender_agent import get_recommender
from tools.chat_memory import get_interview_data, check_interview_complete

# Importar LangSmith para trazas
try:
    from langsmith import trace, traceable
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    trace = None
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class IntelligentAgent:
    """
    Agente inteligente principal que coordina el sistema de recomendación de posgrados

    Flujo:
    1. Detecta si hay una entrevista en curso
    2. Si no hay entrevista → inicia INTERVIEWER Agent
    3. INTERVIEWER recopila información paso a paso
    4. Cuando entrevista completa → PROFILER Agent analiza
    5. PROFILER genera ranking → RECOMMENDER Agent genera recomendación
    6. Usuario puede hacer preguntas adicionales sobre programas
    """

    def __init__(self):
        """Inicializar el agente inteligente"""
        self.interviewer = get_interviewer()
        self.profiler = get_profiler()
        self.recommender = get_recommender()
        self.active_sessions = {}
        print("[OK] Intelligent Agent - Sistema de Recomendación inicializado")

    def is_ready(self):
        """Verificar si el agente está listo"""
        return self.interviewer is not None

    @traceable(name="IntelligentAgent.process_query")
    def process_query(
        self,
        query: str,
        enable_logging: bool = False,
        session_id: str = None,
        is_authenticated: bool = False,
        session_info: dict = None
    ) -> str:
        """
        Procesar una consulta del usuario.

        Flujo inteligente:
        - Si no hay entrevista activa → Inicia entrevista
        - Si hay entrevista en curso → Procesa respuesta
        - Si entrevista completa → Genera recomendación
        - Si ya generó recomendación → Responde preguntas sobre programas

        Args:
            query: Consulta/respuesta del usuario
            enable_logging: Habilitar logging detallado
            session_id: ID de sesión del usuario
            is_authenticated: Si el usuario está autenticado
            session_info: Información de sesión (email, nombre)

        Returns:
            str: Respuesta del agente
        """
        start_time = time.time()

        # Generar o usar session_id
        if not session_id:
            session_id = "default_session"

        # Generar trace_id para esta interacción
        trace_id = tracer.generate_trace_id()

        try:
            tracer.log(
                operation="USER_QUERY_START",
                message=f"[CHAT] Consulta recibida",
                metadata={"query": query[:200], "session_id": session_id},
                level="INFO",
                trace_id=trace_id
            )

            # PASO 0: Si no está autenticado, manejar autenticación OTP primero
            if not is_authenticated:
                response = self._handle_authentication(query, session_id, trace_id)

                # Log de finalización de autenticación
                processing_time = time.time() - start_time
                tracer.log(
                    operation="AUTH_HANDLED",
                    message=f"[AUTH] Proceso de autenticación manejado",
                    metadata={"session_id": session_id, "processing_time": processing_time},
                    level="INFO",
                    trace_id=trace_id
                )

                return response

            # PASO 1: Detectar estado de la sesión (solo si está autenticado)
            session_state = self._get_session_state(session_id)

            # PASO 2: Enrutar según el estado
            if session_state == "NEW":
                # Nueva sesión → Iniciar entrevista
                response = self._start_interview(session_id, query)

            elif session_state == "INTERVIEWING":
                # Entrevista en curso → Procesar respuesta
                response = self._continue_interview(session_id, query)

            elif session_state == "ANALYZING":
                # Entrevista completa → Analizar y recomendar
                response = self._analyze_and_recommend(session_id)

            elif session_state == "RECOMMENDING":
                # Ya hay recomendación → Iniciar flujo post-recomendación
                response = self._handle_post_recommendation_flow(session_id, query)
            
            elif session_state == "ASKING_EMAIL":
                # Preguntando si quiere recibir por email
                response = self._handle_email_request(session_id, query)
            
            elif session_state == "ASKING_CONTACT":
                # Preguntando si quiere ser contactado
                response = self._handle_contact_request(session_id, query)
            
            elif session_state == "SURVEY":
                # Encuesta de satisfacción
                response = self._handle_satisfaction_survey(session_id, query)

            else:
                response = "Lo siento, hubo un error. ¿Quieres empezar de nuevo?"

            # Log de finalización
            processing_time = time.time() - start_time
            tracer.log(
                operation="USER_QUERY_COMPLETE",
                message=f"[SUCCESS] Respuesta generada en {processing_time:.2f}s",
                metadata={
                    "session_id": session_id,
                    "state": session_state,
                    "processing_time": processing_time
                },
                level="INFO",
                trace_id=trace_id
            )

            return response

        except Exception as e:
            print(f"[ERROR] Error processing query: {e}")
            import traceback
            traceback.print_exc()

            tracer.log(
                operation="USER_QUERY_ERROR",
                message=f"[ERROR] {str(e)}",
                metadata={"session_id": session_id},
                level="ERROR",
                trace_id=trace_id
            )

            return self._generate_error_response()

    def _get_session_state(self, session_id: str) -> str:
        """
        Determinar el estado actual de la sesión.

        Estados posibles:
        - NEW: Nueva sesión, no hay entrevista
        - INTERVIEWING: Entrevista en curso
        - ANALYZING: Entrevista completa, analizando perfil
        - RECOMMENDING: Ya se generó recomendación, puede hacer preguntas
        - ASKING_EMAIL: Preguntando si quiere recibir por email
        - ASKING_CONTACT: Preguntando si quiere ser contactado
        - SURVEY: Encuesta de satisfacción

        Returns:
            str: Estado de la sesión
        """
        # Verificar estados del flujo post-recomendación
        post_recommendation_state = get_interview_data(session_id, "post_recommendation_state")
        if post_recommendation_state:
            return post_recommendation_state
        
        # Verificar si hay entrevista completa
        interview_complete = check_interview_complete(session_id)

        if interview_complete:
            # Verificar si ya se generó recomendación
            recommendation = get_interview_data(session_id, "recommendation")
            if recommendation:
                return "RECOMMENDING"
            else:
                return "ANALYZING"

        # Verificar si hay entrevista en curso
        current_question = get_interview_data(session_id, "current_question")

        if current_question is not None and current_question > 0:
            return "INTERVIEWING"

        # Verificar si hay algún dato de entrevista
        profile = get_interview_data(session_id, "profile")
        if profile:
            return "INTERVIEWING"

        # Nueva sesión
        return "NEW"

    def _start_interview(self, session_id: str, first_message: str) -> str:
        """
        Iniciar una nueva entrevista.

        Args:
            session_id: ID de la sesión
            first_message: Primer mensaje del usuario

        Returns:
            Primera pregunta de la entrevista
        """
        try:
            # Intentar obtener nombre y email de la memoria del chat
            from tools.chat_memory import retrieve_chat_memory
            name_memory = retrieve_chat_memory(session_id, "name")
            email_memory = retrieve_chat_memory(session_id, "email")
            
            # Si hay nombre en memoria, guardarlo en el perfil
            if name_memory and name_memory.get("found"):
                nombre = name_memory.get("memory_value", "")
                if nombre:
                    from tools.chat_memory import get_interview_data, store_interview_data
                    profile = get_interview_data(session_id, "profile") or {}
                    if "informacion_personal" not in profile:
                        profile["informacion_personal"] = {}
                    profile["informacion_personal"]["nombre"] = nombre
                    if email_memory and email_memory.get("found"):
                        profile["informacion_personal"]["email"] = email_memory.get("memory_value", "")
                    store_interview_data(session_id, "profile", profile)
            
            # Si el usuario dice algo como "hola", "quiero información", etc.
            # iniciamos directamente con la primera pregunta

            first_question = self.interviewer.start_interview(session_id)

            tracer.log(
                operation="INTERVIEW_STARTED",
                message="[INTERVIEW] Nueva entrevista iniciada",
                metadata={"session_id": session_id},
                level="INFO"
            )

            # Mensaje de bienvenida + primera pregunta
            welcome_message = """Hola, soy el asistente de postgrados de la ICESI, te haré una serie de preguntas (máximo 20, en algunos casos) para poder construir un perfil y darte las mejores opciones de postgrado. Si no quieres responder más preguntas, solo escribe: "No me hagas mas preguntas"

"""

            return welcome_message + first_question

        except Exception as e:
            print(f"[ERROR] Error starting interview: {e}")
            import traceback
            traceback.print_exc()
            return f"[ERROR] Hubo un error al iniciar la entrevista: {str(e)}\n\nPor favor, contacta al administrador del sistema."

    def _continue_interview(self, session_id: str, answer: str) -> str:
        """
        Continuar con la entrevista procesando la respuesta del usuario.

        Args:
            session_id: ID de la sesión
            answer: Respuesta del usuario

        Returns:
            Siguiente pregunta o confirmación de finalización
        """
        try:
            # PASO 0: Detectar si el usuario quiere detener las preguntas
            if self._wants_to_stop_interview(answer):
                # El usuario quiere detener, analizar perfil actual y recomendar
                from tools.chat_memory import store_interview_data
                store_interview_data(session_id, "interview_complete", True)
                store_interview_data(session_id, "completed", True)
                
                tracer.log(
                    operation="INTERVIEW_STOPPED_BY_USER",
                    message="[INTERVIEW] Usuario solicitó detener preguntas",
                    metadata={"session_id": session_id},
                    level="INFO"
                )
                
                # Analizar y generar recomendación inmediatamente
                recommendation = self._analyze_and_recommend(session_id)
                return f"Entendido. He detenido las preguntas. Voy a analizar el perfil que he recopilado hasta ahora para recomendarte los mejores programas.\n\n{recommendation}"
            
            # PASO 1: Detectar si el usuario está haciendo una pregunta en lugar de responder
            if self._is_question_instead_of_answer(answer):
                # El usuario está haciendo una pregunta, usar RAG para responder
                rag_response = self._answer_question_with_rag(answer, session_id)
                
                # Después de responder, volver a mostrar la pregunta actual de la entrevista
                current_question_data = get_interview_data(session_id, "current_question_data")
                if current_question_data:
                    current_question = current_question_data.get("question", "")
                    return f"{rag_response}\n\n---\n\n{current_question}"
                else:
                    # Si no hay pregunta actual, iniciar nueva pregunta
                    profile = self.interviewer.get_current_profile(session_id)
                    answered_questions = get_interview_data(session_id, "answered_questions") or []
                    next_q = self.interviewer._select_next_question(profile, answered_questions, session_id)
                    if next_q:
                        from tools.chat_memory import store_interview_data
                        store_interview_data(session_id, "current_question_data", next_q)
                        return f"{rag_response}\n\n---\n\n{next_q.get('question', '')}"
                    else:
                        return rag_response
            
            # Procesar la respuesta con el INTERVIEWER Agent
            result = self.interviewer.process_answer(answer, session_id)

            # Verificar si hay error de validación
            if result.get("validation_error"):
                return f"{result['validation_error']}\n\n{result.get('next_question', '')}"

            # Verificar si la entrevista está completa
            if result.get("profile_complete"):
                # Guardar flag de completado
                from tools.chat_memory import store_interview_data
                store_interview_data(session_id, "interview_complete", True)

                tracer.log(
                    operation="INTERVIEW_COMPLETE",
                    message="[INTERVIEW] Entrevista completada",
                    metadata={"session_id": session_id},
                    level="INFO"
                )

                # Mensaje de transición + análisis automático
                transition_message = result.get("message", "¡Perfecto! He recopilado toda la información.")

                # Analizar y generar recomendación inmediatamente
                recommendation = self._analyze_and_recommend(session_id)

                return f"{transition_message}\n\n{recommendation}"

            # Entrevista continúa → retornar siguiente pregunta
            next_question = result.get("next_question", "")
            progress = result.get("current_progress", "")

            response = f"{next_question}"
            if progress:
                response = f"[Progreso: {progress}]\n\n{response}"

            return response

        except Exception as e:
            print(f"[ERROR] Error continuing interview: {e}")
            import traceback
            traceback.print_exc()
            return "Lo siento, hubo un error procesando tu respuesta. ¿Podrías repetir?"

    def _wants_to_stop_interview(self, text: str) -> bool:
        """
        Detectar si el usuario quiere detener las preguntas de la entrevista.
        
        Args:
            text: Texto del usuario
        
        Returns:
            True si quiere detener, False en caso contrario
        """
        import re
        text_lower = text.lower().strip()
        
        # Patrones que indican que quiere detener
        stop_patterns = [
            r'no me hagas mas preguntas',
            r'no me hagas más preguntas',
            r'no más preguntas',
            r'no mas preguntas',
            r'ya no preguntes',
            r'deja de preguntar',
            r'para de preguntar',
            r'no quiero responder más',
            r'no quiero responder mas',
            r'ya tengo suficiente',
            r'ya es suficiente',
            r'recomiéndame ya',
            r'recomiendame ya',
            r'dame la recomendación',
            r'dame la recomendacion',
        ]
        
        for pattern in stop_patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False

    def _is_question_instead_of_answer(self, text: str) -> bool:
        """
        Detectar si el usuario está haciendo una pregunta en lugar de responder.
        
        Args:
            text: Texto del usuario
        
        Returns:
            True si parece ser una pregunta, False si es una respuesta
        """
        import re
        text_lower = text.lower().strip()
        
        # Patrones que indican que es una pregunta
        question_patterns = [
            r'^¿',  # Empieza con ¿
            r'\?$',  # Termina con ?
            r'^(qué|que|cuál|cual|cuáles|cuales|cuando|cuándo|donde|dónde|como|cómo|por qué|porque|quien|quién)',
            r'^(dime|cuéntame|explícame|información sobre|quiero saber|me gustaría saber|puedes decirme)',
            r'^(cuánto|cuanto|cuántos|cuantos|cuántas|cuantas)',
            r'^(hay|existe|tienen|tienes)',
        ]
        
        # Verificar si coincide con algún patrón de pregunta
        for pattern in question_patterns:
            if re.search(pattern, text_lower):
                return True
        
        # Si tiene signos de interrogación
        if '?' in text or '¿' in text:
            return True
        
        # Si es muy corto y parece pregunta
        if len(text.split()) <= 5 and any(word in text_lower for word in ['qué', 'que', 'cuál', 'cual', 'cómo', 'como']):
            return True
        
        return False

    def _answer_question_with_rag(self, question: str, session_id: str) -> str:
        """
        Responder una pregunta del usuario usando RAG.
        
        Args:
            question: Pregunta del usuario
            session_id: ID de la sesión
        
        Returns:
            Respuesta generada con RAG
        """
        try:
            # Usar el recommender agent que tiene RAG integrado
            response = self.recommender.answer_specific_question(question)
            
            tracer.log(
                operation="RAG_QUESTION_ANSWERED",
                message="[RAG] Pregunta respondida durante entrevista",
                metadata={"session_id": session_id, "question": question[:100]},
                level="INFO"
            )
            
            return response
            
        except Exception as e:
            print(f"[ERROR] Error answering question with RAG: {e}")
            return "Lo siento, no pude responder tu pregunta en este momento. ¿Podrías continuar con la entrevista?"

    def _analyze_and_recommend(self, session_id: str) -> str:
        """
        Analizar el perfil del estudiante y generar recomendación.

        Este método coordina PROFILER Agent + RECOMMENDER Agent usando ORCHESTRATOR

        Args:
            session_id: ID de la sesión

        Returns:
            Recomendación personalizada
        """
        try:
            # Obtener perfil completo de la entrevista
            profile = self.interviewer.get_current_profile(session_id)

            if not profile:
                return "Lo siento, no pude recuperar tu perfil. ¿Quieres empezar de nuevo?"

            tracer.log(
                operation="PROFILE_ANALYSIS_START",
                message="[PROFILER] Iniciando análisis de perfil",
                metadata={"session_id": session_id},
                level="INFO"
            )

            # PASO 1: PROFILER Agent analiza el perfil
            profiler_results = self.profiler.analyze_profile(profile, session_id)

            if profiler_results.get("error"):
                return f"Hubo un error al analizar tu perfil: {profiler_results['error']}"

            tracer.log(
                operation="PROFILE_ANALYSIS_COMPLETE",
                message="[PROFILER] Análisis completado",
                metadata={
                    "session_id": session_id,
                    "top_programs": [m["program_name"] for m in profiler_results.get("top_matches", [])]
                },
                level="INFO"
            )

            # PASO 2: RECOMMENDER Agent genera la recomendación
            tracer.log(
                operation="RECOMMENDATION_GENERATION_START",
                message="[RECOMMENDER] Generando recomendación",
                metadata={"session_id": session_id},
                level="INFO"
            )

            recommendation = self.recommender.generate_recommendation(
                profiler_results,
                profile
            )

            # Guardar recomendación en memoria
            from tools.chat_memory import store_interview_data
            store_interview_data(session_id, "recommendation", recommendation)
            store_interview_data(session_id, "profiler_results", profiler_results)

            tracer.log(
                operation="RECOMMENDATION_GENERATION_COMPLETE",
                message="[RECOMMENDER] Recomendación generada",
                metadata={"session_id": session_id},
                level="INFO"
            )

            # Iniciar flujo post-recomendación: preguntar si quiere recibir por email
            store_interview_data(session_id, "post_recommendation_state", "ASKING_EMAIL")
            
            return recommendation + "\n\n---\n\n📧 ¿Te gustaría recibir esta recomendación por correo electrónico? Responde 'sí' o 'no'."

        except Exception as e:
            print(f"[ERROR] Error analyzing and recommending: {e}")
            import traceback
            traceback.print_exc()

            return """Lo siento, hubo un error al generar tu recomendación personalizada.

Por favor, contacta directamente a nuestro equipo de admisiones:

📧 admisiones.posgrados@icesi.edu.co
📱 WhatsApp: +57 318 765 4321

Estaremos encantados de ayudarte personalmente."""

    def _answer_followup_question(self, session_id: str, question: str) -> str:
        """
        Responder preguntas adicionales después de la recomendación.

        Args:
            session_id: ID de la sesión
            question: Pregunta del usuario

        Returns:
            Respuesta a la pregunta
        """
        try:
            # Obtener contexto de la recomendación
            profiler_results = get_interview_data(session_id, "profiler_results")

            # Usar RECOMMENDER Agent para responder preguntas específicas
            response = self.recommender.answer_specific_question(
                question,
                context=profiler_results
            )

            tracer.log(
                operation="FOLLOWUP_QUESTION_ANSWERED",
                message="[RECOMMENDER] Pregunta adicional respondida",
                metadata={"session_id": session_id, "question": question[:100]},
                level="INFO"
            )

            return response

        except Exception as e:
            print(f"[ERROR] Error answering followup question: {e}")
            return """Puedo ayudarte con información específica sobre los programas recomendados.

Si necesitas información detallada, no dudes en contactar admisiones:
📧 admisiones.posgrados@icesi.edu.co
📱 WhatsApp: +57 318 765 4321"""

    def _handle_post_recommendation_flow(self, session_id: str, query: str) -> str:
        """Iniciar flujo post-recomendación: preguntar si quiere recibir por email"""
        # Si el usuario hace una pregunta, responderla primero
        if any(word in query.lower() for word in ["qué", "cuál", "cómo", "cuándo", "dónde", "información", "detalle", "pregunta"]):
            return self._answer_followup_question(session_id, query)
        
        # Si no, iniciar el flujo de email
        store_interview_data(session_id, "post_recommendation_state", "ASKING_EMAIL")
        return "📧 ¿Te gustaría recibir esta recomendación por correo electrónico? Responde 'sí' o 'no'."

    def _handle_email_request(self, session_id: str, query: str) -> str:
        """Manejar solicitud de envío por email"""
        from tools.chat_memory import retrieve_chat_memory
        from tools.email_service import get_email_service
        from models.db import create_contact_lead, update_contact_lead
        
        query_lower = query.lower().strip()
        wants_email = any(word in query_lower for word in ["sí", "si", "yes", "s", "quiero", "deseo", "envía", "envia"])
        
        if wants_email:
            # Obtener email y nombre
            email_memory = retrieve_chat_memory(session_id, "email")
            name_memory = retrieve_chat_memory(session_id, "name")
            
            email = email_memory.get("memory_value") if email_memory.get("found") else None
            name = name_memory.get("memory_value") if name_memory.get("found") else "Estudiante"
            
            if not email:
                # Intentar obtener del perfil
                profile = get_interview_data(session_id, "profile")
                if profile:
                    email = profile.get("informacion_personal", {}).get("email")
                    name = profile.get("informacion_personal", {}).get("nombre") or name
            
            if email:
                # Obtener recomendación y programas
                recommendation = get_interview_data(session_id, "recommendation")
                profiler_results = get_interview_data(session_id, "profiler_results")
                programs = profiler_results.get("top_matches", []) if profiler_results else []
                
                # Enviar email
                email_service = get_email_service()
                email_sent = email_service.send_recommendation_email(
                    email=email,
                    name=name or "Estudiante",
                    recommendation=recommendation or "",
                    programs=programs
                )
                
                if email_sent:
                    # Guardar en contact_leads
                    try:
                        create_contact_lead(
                            email=email,
                            name=name,
                            profile_data=profile,
                            recommendation_data=profiler_results,
                            email_sent=True
                        )
                    except:
                        pass
                    
                    # Continuar con pregunta de contacto
                    store_interview_data(session_id, "post_recommendation_state", "ASKING_CONTACT")
                    return f"✅ ¡Perfecto! He enviado tu recomendación a {email}.\n\n📞 ¿Te gustaría que un especialista de admisiones te contacte para ayudarte con más información? Responde 'sí' o 'no'."
                else:
                    return "❌ Hubo un error al enviar el correo. Por favor, verifica tu dirección de correo o contacta directamente a admisiones: 📧 admisiones.posgrados@icesi.edu.co"
            else:
                return "❌ No pude encontrar tu correo electrónico. Por favor, compártelo nuevamente."
        else:
            # No quiere email, preguntar directamente por contacto
            store_interview_data(session_id, "post_recommendation_state", "ASKING_CONTACT")
            return "Entendido. 📞 ¿Te gustaría que un especialista de admisiones te contacte para ayudarte con más información? Responde 'sí' o 'no'."

    def _handle_contact_request(self, session_id: str, query: str) -> str:
        """Manejar solicitud de contacto por especialista"""
        from tools.chat_memory import retrieve_chat_memory
        from models.db import create_contact_lead, update_contact_lead
        
        query_lower = query.lower().strip()
        wants_contact = any(word in query_lower for word in ["sí", "si", "yes", "s", "quiero", "deseo", "contacta", "contacto"])
        
        # Obtener información del usuario
        email_memory = retrieve_chat_memory(session_id, "email")
        name_memory = retrieve_chat_memory(session_id, "name")
        
        email = email_memory.get("memory_value") if email_memory.get("found") else None
        name = name_memory.get("memory_value") if name_memory.get("found") else None
        
        profile = get_interview_data(session_id, "profile")
        if profile:
            email = email or profile.get("informacion_personal", {}).get("email")
            name = name or profile.get("informacion_personal", {}).get("nombre")
        
        profiler_results = get_interview_data(session_id, "profiler_results")
        
        if wants_contact:
            # Guardar en contact_leads
            if email:
                try:
                    # Verificar si ya existe
                    from models.db import list_contact_leads
                    existing_leads = list_contact_leads()
                    existing = next((l for l in existing_leads if l.get("email") == email), None)
                    
                    if existing:
                        update_contact_lead(existing["id"], wants_contact=True, contacted=False)
                    else:
                        create_contact_lead(
                            email=email,
                            name=name,
                            profile_data=profile,
                            recommendation_data=profiler_results,
                            wants_contact=True,
                            email_sent=False
                        )
                except Exception as e:
                    print(f"[ERROR] Error saving contact lead: {e}")
            
            # Iniciar encuesta
            store_interview_data(session_id, "post_recommendation_state", "SURVEY")
            store_interview_data(session_id, "survey_question", 1)
            
            return "✅ Perfecto. Tu información ha sido guardada y un especialista te contactará pronto.\n\n📋 Ahora me gustaría conocer tu opinión sobre el sistema. Por favor, responde las siguientes preguntas:\n\n**1. ¿Qué tan satisfecho estás con las recomendaciones recibidas?**\n(Responde con un número del 1 al 5, donde 1 es muy insatisfecho y 5 es muy satisfecho)"
        else:
            # No quiere contacto, ir directamente a encuesta
            store_interview_data(session_id, "post_recommendation_state", "SURVEY")
            store_interview_data(session_id, "survey_question", 1)
            
            return "Entendido. 📋 Me gustaría conocer tu opinión sobre el sistema. Por favor, responde las siguientes preguntas:\n\n**1. ¿Qué tan satisfecho estás con las recomendaciones recibidas?**\n(Responde con un número del 1 al 5, donde 1 es muy insatisfecho y 5 es muy satisfecho)"

    def _handle_satisfaction_survey(self, session_id: str, query: str) -> str:
        """Manejar encuesta de satisfacción"""
        from models.db import create_satisfaction_survey
        
        current_question = get_interview_data(session_id, "survey_question") or 1
        
        # Guardar respuesta de la pregunta actual
        if current_question == 1:
            # Pregunta 1: Satisfacción general
            try:
                satisfaction = int(query.strip()[0])  # Tomar primer dígito
                if 1 <= satisfaction <= 5:
                    store_interview_data(session_id, "survey_answer_1", satisfaction)
                    store_interview_data(session_id, "survey_question", 2)
                    return "**2. ¿Qué tan fácil fue usar el sistema?**\n(Responde con un número del 1 al 5, donde 1 es muy difícil y 5 es muy fácil)"
                else:
                    return "Por favor, responde con un número del 1 al 5."
            except:
                return "Por favor, responde con un número del 1 al 5."
        
        elif current_question == 2:
            # Pregunta 2: Facilidad de uso
            try:
                ease = int(query.strip()[0])
                if 1 <= ease <= 5:
                    store_interview_data(session_id, "survey_answer_2", ease)
                    store_interview_data(session_id, "survey_question", 3)
                    return "**3. ¿Recomendarías este sistema a otros estudiantes?**\n(Responde con un número del 1 al 5, donde 1 es definitivamente no y 5 es definitivamente sí)"
                else:
                    return "Por favor, responde con un número del 1 al 5."
            except:
                return "Por favor, responde con un número del 1 al 5."
        
        elif current_question == 3:
            # Pregunta 3: Recomendación
            try:
                recommendation = int(query.strip()[0])
                if 1 <= recommendation <= 5:
                    # Guardar todas las respuestas
                    answer_1 = get_interview_data(session_id, "survey_answer_1")
                    answer_2 = get_interview_data(session_id, "survey_answer_2")
                    
                    create_satisfaction_survey(
                        session_id=session_id,
                        question_1="¿Qué tan satisfecho estás con las recomendaciones recibidas?",
                        answer_1=str(answer_1) if answer_1 else None,
                        question_2="¿Qué tan fácil fue usar el sistema?",
                        answer_2=str(answer_2) if answer_2 else None,
                        question_3="¿Recomendarías este sistema a otros estudiantes?",
                        answer_3=str(recommendation),
                        overall_satisfaction=answer_1 if answer_1 else None
                    )
                    
                    # Limpiar estado
                    store_interview_data(session_id, "post_recommendation_state", None)
                    store_interview_data(session_id, "survey_question", None)
                    
                    return "✅ ¡Gracias por tu feedback! Tu opinión es muy valiosa para nosotros.\n\nSi tienes más preguntas sobre los programas recomendados, no dudes en contactarnos:\n📧 admisiones.posgrados@icesi.edu.co\n📱 WhatsApp: +57 318 765 4321\n\n¡Éxito en tu proceso de admisión! 🎓"
                else:
                    return "Por favor, responde con un número del 1 al 5."
            except:
                return "Por favor, responde con un número del 1 al 5."
        
        return "Gracias por completar la encuesta."

    def _handle_authentication(self, query: str, session_id: str = "default_session", trace_id: str = None) -> str:
        """
        Manejar el proceso de autenticación OTP.

        Detecta si el usuario está:
        1. Enviando email + nombre (OTP_SEND)
        2. Enviando código de verificación (OTP_VERIFY)

        Args:
            query: Mensaje del usuario
            session_id: ID de sesión del usuario
            trace_id: ID de trace para logging

        Returns:
            Respuesta del sistema de autenticación
        """
        import re
        from tools.otp_auth import send_otp_to_user, verify_otp_code
        from tools.chat_memory import store_chat_memory

        # Detectar si hay un código de 6 dígitos (OTP_VERIFY)
        otp_pattern = r'\b\d{6}\b'
        otp_match = re.search(otp_pattern, query)

        if otp_match:
            # Usuario está enviando código OTP
            otp_code = otp_match.group(0)

            # Recuperar email de memoria temporal
            from tools.chat_memory import retrieve_chat_memory
            email_memory = retrieve_chat_memory(session_id, "email")

            if not email_memory.get("found"):
                return """No he encontrado tu correo electrónico en mi memoria.

Por favor, vuelve a proporcionarme tu correo electrónico y nombre para enviarte un nuevo código."""

            email = email_memory.get("memory_value")

            # Verificar OTP
            verification_result = verify_otp_code(email, otp_code, trace_id)

            return verification_result.get("message", "Error en la verificación.")

        # Detectar si hay un email (OTP_SEND)
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_match = re.search(email_pattern, query)

        if email_match:
            email = email_match.group(0)

            # Extraer nombre (todo lo que no sea el email)
            name_candidate = query.replace(email, "").strip()
            # Limpiar palabras comunes
            name_candidate = re.sub(r'\b(mi|nombre|es|soy|me|llamo|correo|email)\b', '', name_candidate, flags=re.IGNORECASE).strip()

            # Si no hay nombre, usar "usuario"
            name = name_candidate if name_candidate else None

            # Guardar email en memoria temporal
            store_chat_memory(session_id, "email", email, ttl_minutes=10)
            if name:
                store_chat_memory(session_id, "name", name, ttl_minutes=10)

            # Enviar OTP
            otp_result = send_otp_to_user(email, name, trace_id)

            return otp_result.get("message", "Error al enviar el código.")

        # No se detectó ni email ni código
        return """Para comenzar, necesito tu correo electrónico y nombre.

Por favor proporcióname:
1. Tu correo electrónico
2. Tu nombre completo

Ejemplo: "Mi correo es juan.perez@ejemplo.com y mi nombre es Juan Pérez"
"""

    def _generate_error_response(self) -> str:
        """Generar respuesta de error genérica"""
        return """Lo siento, hubo un error procesando tu solicitud.

Por favor, intenta de nuevo o contacta directamente a:

📧 admisiones.posgrados@icesi.edu.co
📱 WhatsApp: +57 318 765 4321
🌐 www.icesi.edu.co/posgrados

¡Estamos aquí para ayudarte!"""

    def reset_session(self, session_id: str) -> bool:
        """
        Reiniciar una sesión (útil para empezar de nuevo).

        Args:
            session_id: ID de la sesión a reiniciar

        Returns:
            bool: True si se reinició exitosamente
        """
        try:
            from tools.chat_memory import clear_interview_data
            clear_interview_data(session_id)

            tracer.log(
                operation="SESSION_RESET",
                message="[SYSTEM] Sesión reiniciada",
                metadata={"session_id": session_id},
                level="INFO"
            )

            return True

        except Exception as e:
            print(f"[ERROR] Error resetting session: {e}")
            return False


# Singleton instance
_intelligent_agent_instance = None

def get_intelligent_agent() -> IntelligentAgent:
    """Obtener instancia singleton del agente inteligente"""
    global _intelligent_agent_instance
    if _intelligent_agent_instance is None:
        _intelligent_agent_instance = IntelligentAgent()
    return _intelligent_agent_instance


# Para testing
if __name__ == "__main__":
    agent = get_intelligent_agent()

    print("[TEST] Sistema de Recomendación de Posgrados")
    print("=" * 60)

    # Simular conversación
    session_id = "test_session_001"

    # Primera interacción
    response1 = agent.process_query("Hola, quiero información sobre posgrados", session_id=session_id)
    print(f"\n[AGENT]: {response1}")

    # Simular respuestas
    test_answers = [
        "Mi nombre es Juan Pérez",
        "Estudié Ingeniería de Sistemas en la Universidad del Valle",
        "Tengo 5 años de experiencia en desarrollo de software y machine learning",
        "Me interesan la inteligencia artificial, análisis de datos y machine learning",
        "Quiero especializarme en IA para liderar proyectos de innovación tecnológica",
        "Tengo habilidades en Python, TensorFlow, machine learning y análisis de datos",
        "Prefiero estudiar tiempo parcial en horario nocturno",
        "Mi email es juan.perez@example.com y mi teléfono es 3001234567"
    ]

    for i, answer in enumerate(test_answers, 2):
        print(f"\n[USER]: {answer}")
        response = agent.process_query(answer, session_id=session_id)
        print(f"\n[AGENT]: {response}")

    # Pregunta adicional
    print(f"\n[USER]: ¿Cuánto cuesta la Maestría en Ciencia de Datos?")
    response = agent.process_query(
        "¿Cuánto cuesta la Maestría en Ciencia de Datos?",
        session_id=session_id
    )
    print(f"\n[AGENT]: {response}")

    print("\n" + "=" * 60)
    print("[TEST] Finalizado")

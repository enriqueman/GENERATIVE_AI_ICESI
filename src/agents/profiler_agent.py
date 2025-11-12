"""
PROFILER AGENT
Agente perfilador que analiza el perfil del estudiante y determina
qué posgrados son más adecuados según sus características.

Responsabilidades:
1. Analizar el perfil completo del estudiante
2. Consultar la base de datos vectorial para obtener información de posgrados
3. Calcular scores de afinidad entre el perfil y cada posgrado
4. Rankear posgrados según relevancia
5. Generar explicaciones de por qué cada programa es adecuado
"""

import os
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
    from utils.vector_functions import load_retriever, get_combined_retriever
    from tools.chat_memory import get_interview_data
except ImportError as e:
    print(f"[WARNING] Import error in profiler_agent: {e}")
    tracer = None
    def load_retriever(*args, **kwargs): return None
    def get_combined_retriever(*args, **kwargs): return None
    def get_interview_data(*args, **kwargs): return {}


# Criterios de matching por programa
PROGRAM_CRITERIA = {
    "maestria_ciencia_datos": {
        "keywords": [
            "datos", "data", "estadística", "machine learning", "inteligencia artificial",
            "python", "programación", "análisis", "big data", "ia", "ml"
        ],
        "required_background": ["ingeniería", "sistemas", "matemáticas", "estadística", "computación"],
        "weight_factors": {
            "formacion_tecnica": 0.35,
            "experiencia_datos": 0.25,
            "habilidades_programacion": 0.20,
            "interes_ia_ml": 0.20
        }
    },
    "mba_administracion": {
        "keywords": [
            "administración", "gerencia", "gestión", "liderazgo", "negocios",
            "estrategia", "finanzas", "marketing", "emprendimiento", "management"
        ],
        "required_background": [],  # Acepta cualquier formación
        "weight_factors": {
            "experiencia_gerencial": 0.30,
            "liderazgo": 0.25,
            "vision_estrategica": 0.25,
            "anos_experiencia": 0.20
        }
    },
    "maestria_ingenieria_software": {
        "keywords": [
            "software", "programación", "desarrollo", "arquitectura", "devops",
            "sistemas", "aplicaciones", "backend", "frontend", "cloud", "microservicios"
        ],
        "required_background": ["ingeniería", "sistemas", "software", "computación"],
        "weight_factors": {
            "experiencia_desarrollo": 0.35,
            "conocimiento_tecnologias": 0.30,
            "arquitectura_software": 0.20,
            "interes_tecnologia": 0.15
        }
    },
    "maestria_marketing_digital": {
        "keywords": [
            "marketing", "digital", "redes sociales", "publicidad", "contenido",
            "seo", "sem", "analytics", "e-commerce", "comunicación", "ventas"
        ],
        "required_background": [],  # Acepta cualquier formación
        "weight_factors": {
            "experiencia_marketing": 0.30,
            "habilidades_digitales": 0.25,
            "creatividad": 0.20,
            "interes_comunicacion": 0.25
        }
    }
}


class ProfilerAgent:
    """
    Agente perfilador que analiza estudiantes y recomienda posgrados
    """

    def __init__(self):
        """Inicializar el agente perfilador"""
        self.llm = None
        self.retriever = None
        self._initialize()

    def _initialize(self):
        """Inicializar el modelo de lenguaje y el retriever"""
        try:
            api_key = env("OPENAI_API_KEY")
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.2,  # Baja temperatura para análisis preciso
                api_key=api_key
            )
            print("[OK] Profiler Agent initialized with GPT-4o-mini")

            # Inicializar retriever
            self.retriever = get_combined_retriever(score_threshold=0.3)
            print("[OK] Vector retriever initialized")

        except Exception as e:
            print(f"[WARNING] Could not initialize Profiler Agent: {e}")
            self.llm = None
            self.retriever = None

    def analyze_profile(self, student_profile: Dict[str, Any], session_id: str = "default_session") -> Dict[str, Any]:
        """
        Analizar el perfil del estudiante y calcular matches con posgrados.

        Args:
            student_profile: Perfil completo del estudiante
            session_id: ID de la sesión

        Returns:
            {
                "top_matches": [
                    {
                        "program_name": str,
                        "score": float (0-100),
                        "reasons": [str],
                        "details": dict
                    }
                ],
                "profile_summary": str,
                "analysis": dict
            }
        """
        try:
            if not student_profile:
                return {
                    "error": "No profile data available",
                    "top_matches": []
                }

            # Paso 1: Extraer características clave del perfil
            profile_features = self._extract_profile_features(student_profile)

            # Paso 2: Calcular scores para cada programa
            program_scores = self._calculate_program_scores(profile_features, student_profile)

            # Paso 3: Rankear programas
            ranked_programs = sorted(program_scores, key=lambda x: x["score"], reverse=True)

            # Paso 4: Obtener detalles de los top 3 programas usando RAG
            top_matches = self._enrich_top_matches(ranked_programs[:3], profile_features)

            # Paso 5: Generar resumen del perfil
            profile_summary = self._generate_profile_summary(student_profile, profile_features)

            # Registrar en tracing
            if tracer:
                tracer.log(
                    operation="PROFILE_ANALYSIS",
                    message=f"Perfil analizado para {student_profile.get('informacion_personal', {}).get('nombre', 'Desconocido')}",
                    metadata={"top_matches": [m["program_name"] for m in top_matches], "session_id": session_id},
                    level="SUCCESS"
                )

            return {
                "top_matches": top_matches,
                "profile_summary": profile_summary,
                "analysis": {
                    "profile_features": profile_features,
                    "total_programs_analyzed": len(program_scores)
                }
            }

        except Exception as e:
            print(f"[ERROR] Error analyzing profile: {e}")
            import traceback
            traceback.print_exc()

            return {
                "error": str(e),
                "top_matches": []
            }

    def _extract_profile_features(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extraer características clave del perfil del estudiante.

        Args:
            profile: Perfil del estudiante

        Returns:
            Diccionario con características extraídas
        """
        features = {
            "formacion": profile.get("formacion_academica", {}).get("pregrado", "").lower(),
            "universidad": profile.get("formacion_academica", {}).get("universidad", "").lower(),
            "anos_experiencia": self._extract_years_experience(profile.get("experiencia_laboral", {})),
            "area_trabajo": profile.get("experiencia_laboral", {}).get("area_trabajo", "").lower(),
            "intereses": [i.lower() for i in profile.get("intereses", {}).get("areas_interes", [])],
            "objetivos": profile.get("intereses", {}).get("objetivos_carrera", "").lower(),
            "habilidades_tecnicas": [h.lower() for h in profile.get("habilidades", {}).get("habilidades_tecnicas", [])],
            "modalidad_preferida": profile.get("disponibilidad", {}).get("modalidad", "").lower(),
            "all_text": self._profile_to_text(profile)
        }

        return features

    def _extract_years_experience(self, experiencia: Dict) -> int:
        """Extraer años de experiencia del perfil"""
        exp_text = str(experiencia.get("anos_experiencia", "0")).lower()

        # Buscar números en el texto
        import re
        numbers = re.findall(r'\d+', exp_text)

        if numbers:
            return int(numbers[0])
        return 0

    def _profile_to_text(self, profile: Dict[str, Any]) -> str:
        """Convertir perfil a texto para análisis"""
        text_parts = []

        # Formación
        formacion = profile.get("formacion_academica", {})
        if formacion.get("pregrado"):
            text_parts.append(f"Estudió {formacion.get('pregrado')}")

        # Experiencia
        experiencia = profile.get("experiencia_laboral", {})
        if experiencia.get("area_trabajo"):
            text_parts.append(f"Trabaja en {experiencia.get('area_trabajo')}")

        # Intereses
        intereses = profile.get("intereses", {})
        if intereses.get("areas_interes"):
            text_parts.append(f"Interesado en {', '.join(intereses.get('areas_interes', []))}")

        # Objetivos
        if intereses.get("objetivos_carrera"):
            text_parts.append(f"Objetivos: {intereses.get('objetivos_carrera')}")

        # Habilidades
        habilidades = profile.get("habilidades", {})
        if habilidades.get("habilidades_tecnicas"):
            text_parts.append(f"Habilidades: {', '.join(habilidades.get('habilidades_tecnicas', []))}")

        return ". ".join(text_parts)

    def _calculate_program_scores(self, features: Dict[str, Any], full_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calcular scores de afinidad para cada programa.

        Args:
            features: Características extraídas del perfil
            full_profile: Perfil completo

        Returns:
            Lista de programas con sus scores
        """
        program_scores = []

        for program_id, criteria in PROGRAM_CRITERIA.items():
            score = 0.0
            reasons = []

            # 1. Match de keywords (30% del score)
            keyword_score, keyword_reasons = self._calculate_keyword_match(features, criteria)
            score += keyword_score * 0.30
            reasons.extend(keyword_reasons)

            # 2. Match de formación académica (25% del score)
            background_score, background_reasons = self._calculate_background_match(features, criteria)
            score += background_score * 0.25
            reasons.extend(background_reasons)

            # 3. Match de experiencia (25% del score)
            experience_score, experience_reasons = self._calculate_experience_match(features, criteria)
            score += experience_score * 0.25
            reasons.extend(experience_reasons)

            # 4. Match de disponibilidad (10% del score)
            availability_score = self._calculate_availability_match(features, program_id)
            score += availability_score * 0.10

            # 5. Bonus por LLM analysis (10% del score)
            if self.llm:
                llm_score, llm_reasons = self._llm_match_analysis(features, program_id)
                score += llm_score * 0.10
                reasons.extend(llm_reasons)

            # Normalizar score a 0-100
            final_score = min(100, max(0, score * 100))

            program_scores.append({
                "program_id": program_id,
                "program_name": self._get_program_display_name(program_id),
                "score": round(final_score, 2),
                "reasons": reasons[:5],  # Top 5 razones
                "details": {
                    "keyword_match": round(keyword_score * 30, 2),
                    "background_match": round(background_score * 25, 2),
                    "experience_match": round(experience_score * 25, 2),
                    "availability_match": round(availability_score * 10, 2)
                }
            })

        return program_scores

    def _calculate_keyword_match(self, features: Dict, criteria: Dict) -> Tuple[float, List[str]]:
        """Calcular match basado en keywords"""
        keywords = criteria["keywords"]
        all_text = features["all_text"].lower()
        intereses = " ".join(features["intereses"]).lower()
        habilidades = " ".join(features["habilidades_tecnicas"]).lower()

        combined_text = f"{all_text} {intereses} {habilidades}"

        matches = []
        for keyword in keywords:
            if keyword in combined_text:
                matches.append(keyword)

        if matches:
            score = min(1.0, len(matches) / (len(keywords) * 0.3))  # 30% de keywords = score perfecto
            reasons = [f"Tu perfil menciona: {', '.join(matches[:3])}"]
            return score, reasons

        return 0.0, []

    def _calculate_background_match(self, features: Dict, criteria: Dict) -> Tuple[float, List[str]]:
        """Calcular match basado en formación académica"""
        required_background = criteria["required_background"]

        if not required_background:  # Si no hay requisitos específicos
            return 1.0, ["Este programa acepta profesionales de cualquier área"]

        formacion = features["formacion"].lower()
        reasons = []

        for required in required_background:
            if required in formacion:
                reasons.append(f"Tu formación en {required} es ideal para este programa")
                return 1.0, reasons

        # Si no hay match directo, retornar score bajo
        return 0.3, ["Tu formación puede requerir nivelación para este programa"]

    def _calculate_experience_match(self, features: Dict, criteria: Dict) -> Tuple[float, List[str]]:
        """Calcular match basado en experiencia laboral"""
        anos = features["anos_experiencia"]
        area = features["area_trabajo"]
        reasons = []

        # Score basado en años de experiencia
        if anos >= 3:
            exp_score = 1.0
            reasons.append(f"Tienes {anos} años de experiencia, lo cual es excelente")
        elif anos >= 1:
            exp_score = 0.7
            reasons.append(f"Tu experiencia de {anos} años es adecuada")
        else:
            exp_score = 0.4
            reasons.append("El programa prefiere candidatos con más experiencia")

        # Bonus si el área de trabajo es relevante
        program_keywords = criteria["keywords"]
        if any(keyword in area for keyword in program_keywords):
            exp_score = min(1.0, exp_score + 0.2)
            reasons.append(f"Tu experiencia en {area} es muy relevante")

        return exp_score, reasons

    def _calculate_availability_match(self, features: Dict, program_id: str) -> float:
        """Calcular match basado en disponibilidad"""
        modalidad = features["modalidad_preferida"]

        # Todos los programas son flexibles, así que siempre hay match parcial
        if "tiempo parcial" in modalidad or "virtual" in modalidad or "nocturno" in modalidad:
            return 1.0  # Ideal para profesionales que trabajan

        return 0.8  # Aún así es compatible

    def _llm_match_analysis(self, features: Dict, program_id: str) -> Tuple[float, List[str]]:
        """Usar LLM para análisis adicional de match"""
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """Eres un experto en orientación vocacional para posgrados.
Analiza si el perfil del estudiante es adecuado para el programa especificado.
Responde SOLO con un JSON en este formato:
{{
    "match_score": 0.0-1.0,
    "key_reason": "Una razón clave en máximo 15 palabras"
}}"""),
                ("user", """Perfil del estudiante: {profile}

Programa: {program}

¿Es un buen match?""")
            ])

            chain = prompt | self.llm
            response = chain.invoke({
                "profile": features["all_text"],
                "program": self._get_program_display_name(program_id)
            })

            content = response.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            return result["match_score"], [result["key_reason"]]

        except Exception as e:
            print(f"[WARNING] LLM match analysis failed: {e}")
            return 0.5, []

    def _enrich_top_matches(self, top_programs: List[Dict], features: Dict) -> List[Dict]:
        """Enriquecer los top matches con información detallada del RAG"""
        enriched = []

        for program in top_programs:
            try:
                # Consultar RAG para obtener detalles del programa
                if self.retriever:
                    query = f"Información sobre {program['program_name']} requisitos inversión"
                    docs = self.retriever.get_relevant_documents(query)

                    if docs:
                        program["rag_info"] = docs[0].page_content[:500]  # Primeros 500 caracteres

                enriched.append(program)

            except Exception as e:
                print(f"[WARNING] Could not enrich program {program['program_name']}: {e}")
                enriched.append(program)

        return enriched

    def _generate_profile_summary(self, profile: Dict, features: Dict) -> str:
        """Generar un resumen del perfil del estudiante"""
        nombre = profile.get("informacion_personal", {}).get("nombre", "Estudiante")
        formacion = features["formacion"]
        anos = features["anos_experiencia"]
        intereses = ", ".join(features["intereses"][:3]) if features["intereses"] else "diversos campos"

        summary = f"{nombre} es un profesional con formación en {formacion} y {anos} años de experiencia. "
        summary += f"Sus principales intereses incluyen {intereses}."

        return summary

    def _get_program_display_name(self, program_id: str) -> str:
        """Obtener nombre legible del programa"""
        names = {
            "maestria_ciencia_datos": "Maestría en Ciencia de Datos",
            "mba_administracion": "MBA - Administración",
            "maestria_ingenieria_software": "Maestría en Ingeniería de Software",
            "maestria_marketing_digital": "Maestría en Marketing Digital y Analítica"
        }
        return names.get(program_id, program_id)


# Singleton instance
_profiler_instance = None

def get_profiler() -> ProfilerAgent:
    """Obtener instancia singleton del profiler agent"""
    global _profiler_instance
    if _profiler_instance is None:
        _profiler_instance = ProfilerAgent()
    return _profiler_instance


# Para testing
if __name__ == "__main__":
    profiler = get_profiler()

    # Perfil de prueba
    test_profile = {
        "formacion_academica": {
            "pregrado": "Ingeniería de Sistemas",
            "universidad": "Universidad del Valle"
        },
        "experiencia_laboral": {
            "anos_experiencia": "5 años",
            "area_trabajo": "desarrollo de software y machine learning"
        },
        "intereses": {
            "areas_interes": ["inteligencia artificial", "análisis de datos", "machine learning"],
            "objetivos_carrera": "Especializarme en IA para liderar proyectos innovadores"
        },
        "habilidades": {
            "habilidades_tecnicas": ["Python", "TensorFlow", "SQL", "Docker"]
        },
        "disponibilidad": {
            "modalidad": "tiempo parcial"
        },
        "informacion_personal": {
            "nombre": "Juan Pérez"
        }
    }

    print("\n[TEST] Analyzing profile...")
    result = profiler.analyze_profile(test_profile)

    print(f"\n[RESULT] Profile Summary: {result['profile_summary']}")
    print(f"\n[RESULT] Top Matches:")
    for i, match in enumerate(result['top_matches'], 1):
        print(f"\n{i}. {match['program_name']} - Score: {match['score']}/100")
        print(f"   Reasons:")
        for reason in match['reasons']:
            print(f"   - {reason}")

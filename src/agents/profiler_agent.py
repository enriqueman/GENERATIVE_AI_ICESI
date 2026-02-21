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
    from utils.vector_functions import load_retriever, get_combined_retriever
    from tools.chat_memory import get_interview_data
except ImportError as e:
    print(f"[WARNING] Import error in profiler_agent: {e}")
    tracer = None
    def load_retriever(*args, **kwargs): return None
    def get_combined_retriever(*args, **kwargs): return None
    def get_interview_data(*args, **kwargs): return {}


# Criterios de matching por programa (ahora se obtienen dinámicamente del RAG)
# Este diccionario se usa como fallback si no hay RAG disponible
PROGRAM_CRITERIA = {}


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

            # Inicializar retriever - intentar cargar programas primero, luego combinado
            try:
                self.retriever = load_retriever("posgrado_programs", score_threshold=0.3)
                print("[OK] Program retriever initialized")
            except:
                try:
                    self.retriever = get_combined_retriever(score_threshold=0.3)
                    print("[OK] Combined retriever initialized")
                except:
                    self.retriever = None
                    print("[WARNING] Could not initialize retriever")

        except Exception as e:
            print(f"[WARNING] Could not initialize Profiler Agent: {e}")
            self.llm = None
            self.retriever = None

    @traceable(name="ProfilerAgent.analyze_profile")
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
            
            # Debug: Log del perfil extraído
            if tracer:
                tracer.log(
                    operation="PROFILE_FEATURES_EXTRACTED",
                    message="Características del perfil extraídas",
                    metadata={
                        "formacion": profile_features.get("formacion", ""),
                        "area_trabajo": profile_features.get("area_trabajo", ""),
                        "intereses": profile_features.get("intereses", []),
                        "objetivos": profile_features.get("objetivos", ""),
                        "anos_experiencia": profile_features.get("anos_experiencia", 0)
                    },
                    level="INFO"
                )

            # Paso 2: Obtener TODOS los programas disponibles desde RAG basados en el perfil
            all_programs = self._get_all_programs_from_rag(profile_features)
            
            if tracer:
                tracer.log(
                    operation="PROGRAMS_RETRIEVED_FROM_RAG",
                    message=f"Programas recuperados desde RAG: {len(all_programs)}",
                    metadata={"program_count": len(all_programs)},
                    level="INFO"
                )
            
            # Paso 3: Calcular scores para cada programa basado en el perfil
            if all_programs:
                program_scores = self._calculate_program_scores_rag(all_programs, profile_features, student_profile)
            else:
                # Fallback a método antiguo si no hay programas en RAG
                print("[WARNING] No se encontraron programas en RAG, usando método fallback")
                program_scores = self._calculate_program_scores(profile_features, student_profile)

            # Paso 4: Rankear programas
            ranked_programs = sorted(program_scores, key=lambda x: x["score"], reverse=True)
            
            # Filtrar programas con afinidad >= 51 (umbral mínimo)
            MIN_AFFINITY_THRESHOLD = 51.0
            filtered_programs = [p for p in ranked_programs if p["score"] >= MIN_AFFINITY_THRESHOLD]
            
            if tracer:
                tracer.log(
                    operation="PROGRAMS_RANKED",
                    message=f"Programas rankeados: {len(ranked_programs)}, filtrados (>=51): {len(filtered_programs)}",
                    metadata={
                        "total_programs": len(ranked_programs),
                        "filtered_programs": len(filtered_programs),
                        "min_affinity_threshold": MIN_AFFINITY_THRESHOLD,
                        "top_3_scores": [p["score"] for p in filtered_programs[:3]] if filtered_programs else [],
                        "top_3_names": [p["program_name"] for p in filtered_programs[:3]] if filtered_programs else []
                    },
                    level="INFO"
                )

            # Paso 5: Obtener detalles de los top programas (máximo 3, solo si tienen afinidad >= 45)
            top_matches = self._enrich_top_matches(filtered_programs[:3], profile_features) if filtered_programs else []

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
        # Nueva estructura: academico, laboral, objetivos, intereses, logistica, economia
        academico = profile.get("academico", {})
        laboral = profile.get("laboral", {})
        intereses = profile.get("intereses", {})
        objetivos = profile.get("objetivos", {})
        logistica = profile.get("logistica", {})
        
        # Compatibilidad con estructura antigua
        formacion_academica = profile.get("formacion_academica", {})
        experiencia_laboral = profile.get("experiencia_laboral", {})
        disponibilidad = profile.get("disponibilidad", {})
        habilidades = profile.get("habilidades", {})
        
        features = {
            "formacion": (academico.get("titulo_pregrado") or formacion_academica.get("pregrado") or "").lower(),
            "universidad": (academico.get("universidad") or formacion_academica.get("universidad") or "").lower(),
            "anos_experiencia": self._extract_years_experience(laboral or experiencia_laboral),
            "area_trabajo": (laboral.get("sector") or experiencia_laboral.get("area_trabajo") or "").lower(),
            "intereses": self._extract_interests(intereses),
            "objetivos": (objetivos.get("meta_principal") or intereses.get("objetivos_carrera") or "").lower(),
            "habilidades_tecnicas": self._extract_skills(habilidades, academico),
            "modalidad_preferida": (logistica.get("modalidad_preferida") or disponibilidad.get("modalidad") or "").lower(),
            "all_text": self._profile_to_text(profile)
        }

        return features

    def _extract_interests(self, intereses: Dict) -> List[str]:
        """Extraer intereses del perfil"""
        areas = intereses.get("areas", [])
        if isinstance(areas, str):
            areas = [a.strip() for a in areas.split(",") if a.strip()]
        elif not isinstance(areas, list):
            areas = []
        
        # Compatibilidad con estructura antigua
        if not areas:
            old_areas = intereses.get("areas_interes", [])
            if isinstance(old_areas, str):
                areas = [a.strip() for a in old_areas.split(",") if a.strip()]
            elif isinstance(old_areas, list):
                areas = old_areas
        
        return [i.lower() for i in areas if i]

    def _extract_skills(self, habilidades: Dict, academico: Dict) -> List[str]:
        """Extraer habilidades técnicas"""
        skills = habilidades.get("habilidades_tecnicas", [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        elif not isinstance(skills, list):
            skills = []
        
        # Agregar fortalezas académicas
        fortalezas = academico.get("fortalezas")
        if fortalezas:
            if isinstance(fortalezas, str):
                fortalezas_list = [f.strip() for f in fortalezas.split(",") if f.strip()]
                skills.extend(fortalezas_list)
        
        return [s.lower() for s in skills if s]

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

        # Formación (nueva estructura: academico)
        academico = profile.get("academico", {})
        formacion_academica = profile.get("formacion_academica", {})  # Compatibilidad
        
        titulo = academico.get("titulo_pregrado") or formacion_academica.get("pregrado")
        if titulo:
            text_parts.append(f"Estudió {titulo}")
        
        universidad = academico.get("universidad") or formacion_academica.get("universidad")
        if universidad:
            text_parts.append(f"en {universidad}")

        # Experiencia (nueva estructura: laboral)
        laboral = profile.get("laboral", {})
        experiencia_laboral = profile.get("experiencia_laboral", {})  # Compatibilidad
        
        sector = laboral.get("sector") or experiencia_laboral.get("area_trabajo")
        if sector:
            text_parts.append(f"Trabaja en {sector}")
        
        cargo = laboral.get("cargo")
        if cargo:
            text_parts.append(f"como {cargo}")

        # Intereses
        intereses = profile.get("intereses", {})
        areas = intereses.get("areas", [])
        if isinstance(areas, str):
            areas = [a.strip() for a in areas.split(",") if a.strip()]
        elif isinstance(areas, list):
            areas = [a for a in areas if a]
        
        # Compatibilidad con estructura antigua
        if not areas:
            old_areas = intereses.get("areas_interes", [])
            if isinstance(old_areas, list):
                areas = old_areas
        
        if areas:
            text_parts.append(f"Interesado en {', '.join(areas)}")

        # Objetivos
        objetivos = profile.get("objetivos", {})
        meta = objetivos.get("meta_principal") or intereses.get("objetivos_carrera")
        if meta:
            text_parts.append(f"Objetivos: {meta}")

        # Habilidades
        habilidades = profile.get("habilidades", {})
        skills = habilidades.get("habilidades_tecnicas", [])
        if isinstance(skills, str):
            skills = [s.strip() for s in skills.split(",") if s.strip()]
        elif isinstance(skills, list):
            skills = [s for s in skills if s]
        
        if skills:
            text_parts.append(f"Habilidades: {', '.join(skills)}")

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
                    # Usar método disponible del retriever
                    if hasattr(self.retriever, 'invoke'):
                        docs = self.retriever.invoke(query)
                    elif hasattr(self.retriever, 'get_relevant_documents'):
                        docs = self.retriever.get_relevant_documents(query)
                    else:
                        docs = self.retriever(query) if callable(self.retriever) else []
                    
                    if not isinstance(docs, list):
                        docs = list(docs) if docs else []

                    if docs:
                        program["rag_info"] = docs[0].page_content[:500]  # Primeros 500 caracteres

                enriched.append(program)

            except Exception as e:
                print(f"[WARNING] Could not enrich program {program['program_name']}: {e}")
                enriched.append(program)

        return enriched

    def _generate_profile_summary(self, profile: Dict, features: Dict) -> str:
        """Generar un resumen del perfil del estudiante"""
        # Obtener nombre - verificar múltiples fuentes y evitar "None"
        nombre = (
            profile.get("informacion_personal", {}).get("nombre") or
            "Estudiante"
        )
        
        # Si nombre es None o vacío, usar "Estudiante"
        if not nombre or nombre == "None" or str(nombre).strip() == "":
            nombre = "Estudiante"
        
        formacion = features["formacion"] or "formación profesional"
        anos = features["anos_experiencia"]
        intereses = ", ".join(features["intereses"][:3]) if features["intereses"] else "diversos campos"
        
        # Obtener objetivos
        objetivos = profile.get("objetivos", {})
        meta = objetivos.get("meta_principal", "")
        if not meta:
            meta = profile.get("intereses", {}).get("objetivos_carrera", "")

        summary = f"{nombre} es un profesional con formación en {formacion}"
        if anos > 0:
            summary += f" y {anos} años de experiencia"
        summary += ". "
        
        if intereses and intereses != "diversos campos":
            summary += f"Sus principales intereses incluyen {intereses}. "
        
        if meta:
            summary += f"Su objetivo principal es {meta}."

        return summary

    @traceable(name="ProfilerAgent._get_all_programs_from_rag")
    def _get_all_programs_from_rag(self, features: Dict) -> List[Dict]:
        """
        Obtener TODOS los programas disponibles desde RAG basados en el perfil del estudiante.
        
        Args:
            features: Características del perfil
        
        Returns:
            Lista de programas con su información
        """
        if not self.retriever:
            return []
        
        try:
            # Construir query basada en el perfil completo
            query_parts = []
            
            # Agregar información académica
            if features.get("formacion"):
                query_parts.append(f"formación {features['formacion']}")
            if features.get("universidad"):
                query_parts.append(f"universidad {features['universidad']}")
            
            # Agregar información laboral
            if features.get("area_trabajo"):
                query_parts.append(f"sector {features['area_trabajo']}")
            if features.get("anos_experiencia", 0) > 0:
                query_parts.append(f"experiencia {features['anos_experiencia']} años")
            
            # Agregar intereses
            if features.get("intereses"):
                query_parts.extend(features["intereses"][:5])  # Más intereses
            
            # Agregar objetivos
            if features.get("objetivos"):
                query_parts.append(features["objetivos"])
            
            # Agregar habilidades técnicas
            if features.get("habilidades_tecnicas"):
                query_parts.extend(features["habilidades_tecnicas"][:3])
            
            # Construir query completa
            if query_parts:
                query = "programas de posgrado " + " ".join(query_parts[:10])  # Más términos
            else:
                query = "programas de posgrado maestría especialización MBA"
            
            print(f"[DEBUG] Query para RAG: {query[:200]}")
            
            # Obtener documentos - usar invoke() o método disponible
            if hasattr(self.retriever, 'invoke'):
                docs = self.retriever.invoke(query)
            elif hasattr(self.retriever, 'get_relevant_documents'):
                docs = self.retriever.get_relevant_documents(query)
            else:
                docs = self.retriever(query) if callable(self.retriever) else []
            
            if not isinstance(docs, list):
                docs = list(docs) if docs else []
            
            print(f"[DEBUG] Documentos recuperados de RAG: {len(docs)}")
            
            # Extraer programas únicos de la colección posgrado_programs
            programs = {}
            for doc in docs:
                metadata = doc.metadata
                # Buscar programas con etiqueta específica
                if (metadata.get("source_type") == "posgrado_program" or 
                    metadata.get("program_tag") == "programa_posgrado" or
                    "programa" in metadata.get("source", "").lower()):
                    
                    program_name = metadata.get("program_name", "")
                    if not program_name:
                        # Intentar extraer del source
                        source = metadata.get("source", "")
                        if source:
                            import os
                            filename = os.path.basename(source)
                            program_name = filename.replace(".pdf", "").replace(".txt", "").replace("_", " ").title()
                    
                    if program_name and program_name not in programs:
                        # Extraer áreas temáticas
                        areas = []
                        if metadata.get("areas_tematicas"):
                            if isinstance(metadata["areas_tematicas"], str):
                                areas = [a.strip() for a in metadata["areas_tematicas"].split(",") if a.strip()]
                            elif isinstance(metadata["areas_tematicas"], list):
                                areas = metadata["areas_tematicas"]
                        
                        programs[program_name] = {
                            "program_name": program_name,
                            "program_type": metadata.get("program_type", "maestria"),
                            "content": doc.page_content,
                            "metadata": metadata,
                            "areas_tematicas": areas
                        }
            
            print(f"[DEBUG] Programas únicos encontrados: {len(programs)}")
            
            # Si no se encontraron programas específicos, buscar en sample_documents también
            if not programs:
                # Intentar buscar en sample_documents
                try:
                    from utils.vector_functions import load_retriever
                    sample_retriever = load_retriever("sample_documents", score_threshold=0.3)
                    if hasattr(sample_retriever, 'invoke'):
                        sample_docs = sample_retriever.invoke(query)
                    elif hasattr(sample_retriever, 'get_relevant_documents'):
                        sample_docs = sample_retriever.get_relevant_documents(query)
                    else:
                        sample_docs = sample_retriever(query) if callable(sample_retriever) else []
                    
                    if not isinstance(sample_docs, list):
                        sample_docs = list(sample_docs) if sample_docs else []
                    
                    # Extraer programas de sample_documents
                    for doc in sample_docs[:20]:  # Limitar a 20
                        source = doc.metadata.get("source", "")
                        if "maestria" in source.lower() or "mba" in source.lower():
                            # Extraer nombre del archivo
                            import os
                            filename = os.path.basename(source)
                            program_name = filename.replace(".pdf", "").replace(".txt", "").replace("_", " ").title()
                            
                            if program_name and program_name not in programs:
                                programs[program_name] = {
                                    "program_name": program_name,
                                    "program_type": "maestria" if "maestria" in filename.lower() else "mba",
                                    "content": doc.page_content,
                                    "metadata": doc.metadata,
                                    "areas_tematicas": []
                                }
                except Exception as e:
                    print(f"[WARNING] Error buscando en sample_documents: {e}")
            
            return list(programs.values())
            
        except Exception as e:
            print(f"[WARNING] Error obteniendo programas de RAG: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _calculate_program_scores_rag(self, programs: List[Dict], features: Dict, full_profile: Dict) -> List[Dict]:
        """
        Calcular scores de afinidad para programas obtenidos desde RAG.
        
        Args:
            programs: Lista de programas desde RAG
            features: Características del perfil
            full_profile: Perfil completo
        
        Returns:
            Lista de programas con sus scores
        """
        program_scores = []
        
        for program in programs:
            program_name = program.get("program_name", "Programa desconocido")
            program_content = program.get("content", "").lower()
            program_areas = program.get("areas_tematicas", [])
            
            score = 0.0
            reasons = []
            
            # 1. Match de keywords en el contenido (40%)
            profile_text = features.get("all_text", "").lower()
            intereses_text = " ".join(features.get("intereses", [])).lower()
            objetivos_text = features.get("objetivos", "").lower()
            formacion_text = features.get("formacion", "").lower()
            area_trabajo_text = features.get("area_trabajo", "").lower()
            habilidades_text = " ".join(features.get("habilidades_tecnicas", [])).lower()
            
            combined_profile = f"{profile_text} {intereses_text} {objetivos_text} {formacion_text} {area_trabajo_text} {habilidades_text}"
            
            # Buscar coincidencias de palabras clave del perfil en el contenido del programa
            # Filtrar palabras muy comunes
            common_words = {"programa", "maestria", "especializacion", "universidad", "estudiante", "perfil", "años", "año", "curso", "cursos"}
            profile_words = set([w for w in combined_profile.split() if len(w) > 3 and w not in common_words])
            program_words = set([w for w in program_content.split() if len(w) > 3 and w not in common_words])
            
            matches = profile_words.intersection(program_words)
            # Ajustar cálculo: más matches = mejor score, pero con límite razonable
            keyword_score = min(1.0, len(matches) / max(1, min(len(profile_words) * 0.15, 20)))
            score += keyword_score * 0.40
            if matches:
                match_list = list(matches)[:3]
                reasons.append(f"Tu perfil coincide con temas del programa: {', '.join(match_list)}")
            
            # 2. Match de áreas temáticas (30%)
            area_score = 0.0
            if program_areas:
                intereses = features["intereses"]
                if intereses:
                    # Buscar matches entre áreas del programa e intereses del perfil
                    area_matches = []
                    for area in program_areas:
                        area_lower = area.lower()
                        for interes in intereses:
                            interes_lower = interes.lower()
                            # Match si el área contiene el interés o viceversa
                            if interes_lower in area_lower or area_lower in interes_lower:
                                area_matches.append(area)
                                break
                    
                    area_score = min(1.0, len(area_matches) / max(1, len(program_areas)))
                    score += area_score * 0.30
                    if area_matches:
                        reasons.append(f"El programa cubre tus áreas de interés: {', '.join(area_matches[:2])}")
                else:
                    score += 0.15  # Score parcial si no hay intereses definidos
            else:
                score += 0.10  # Score mínimo si no hay áreas definidas
            
            # 3. Match de formación/experiencia (20%)
            formacion = features.get("formacion", "")
            area_trabajo = features.get("area_trabajo", "")
            anos_exp = features.get("anos_experiencia", 0)
            
            formacion_match = False
            if formacion:
                # Buscar palabras clave de la formación en el contenido
                formacion_keywords = formacion.split()
                for keyword in formacion_keywords:
                    if len(keyword) > 4 and keyword in program_content:
                        formacion_match = True
                        break
            
            if formacion_match:
                score += 0.20
                reasons.append(f"Tu formación en {formacion} es relevante para este programa")
            elif area_trabajo:
                # Buscar área de trabajo en el contenido
                area_keywords = area_trabajo.split()
                for keyword in area_keywords:
                    if len(keyword) > 4 and keyword in program_content:
                        score += 0.15
                        reasons.append(f"Tu experiencia en {area_trabajo} es relevante")
                        break
                else:
                    score += 0.05  # Score mínimo
            else:
                score += 0.05  # Score mínimo
            
            # Bonus por años de experiencia si es relevante
            if anos_exp >= 3:
                score += 0.05
            
            # 4. Match de modalidad (10%)
            modalidad = features.get("modalidad_preferida", "")
            if modalidad and modalidad in program_content:
                score += 0.10
                reasons.append(f"El programa ofrece modalidad {modalidad}")
            else:
                score += 0.05
            
            # Normalizar score a 0-100
            final_score = min(100, max(0, score * 100))
            
            program_scores.append({
                "program_id": program_name.lower().replace(" ", "_"),
                "program_name": program_name,
                "score": round(final_score, 2),
                "reasons": reasons[:5] if reasons else ["Programa disponible en ICESI"],
                "details": {
                    "keyword_match": round(keyword_score * 40, 2),
                    "area_match": round(area_score * 30, 2) if program_areas else 0,
                    "content_preview": program_content[:200]
                }
            })
        
        return program_scores

    def _get_program_display_name(self, program_id: str) -> str:
        """Obtener nombre legible del programa"""
        # Si ya es un nombre legible, retornarlo
        if " " in program_id or program_id[0].isupper():
            return program_id
        
        # Mapeo de fallback
        names = {
            "maestria_ciencia_datos": "Maestría en Ciencia de Datos",
            "mba_administracion": "MBA - Administración",
            "maestria_ingenieria_software": "Maestría en Ingeniería de Software",
            "maestria_marketing_digital": "Maestría en Marketing Digital y Analítica"
        }
        return names.get(program_id, program_id.replace("_", " ").title())


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

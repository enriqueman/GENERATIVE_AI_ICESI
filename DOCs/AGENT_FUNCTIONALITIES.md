# 🤖 Funcionalidades de los Agentes del Sistema
## Sistema de Recomendación de Posgrados - Universidad ICESI

Este documento describe las funcionalidades de cada agente del sistema desde la perspectiva del usuario y del sistema, sin entrar en detalles de implementación técnica.

---

## 📋 Tabla de Contenidos

1. [Visión General del Sistema de Agentes](#visión-general-del-sistema-de-agentes)
2. [Intelligent Agent (Agente Coordinador)](#intelligent-agent-agente-coordinador)
3. [Interviewer Agent (Agente Entrevistador)](#interviewer-agent-agente-entrevistador)
4. [Profiler Agent (Agente Perfilador)](#profiler-agent-agente-perfilador)
5. [Recommender Agent (Agente Recomendador)](#recommender-agent-agente-recomendador)
6. [RAG Agent (Agente de Búsqueda Semántica)](#rag-agent-agente-de-búsqueda-semántica)
7. [Flujo Completo de Funcionalidades](#flujo-completo-de-funcionalidades)
8. [Casos de Uso por Agente](#casos-de-uso-por-agente)

---

## Visión General del Sistema de Agentes

El sistema de recomendación de posgrados utiliza una arquitectura basada en agentes especializados que trabajan de manera coordinada. Cada agente tiene responsabilidades específicas y se comunica con otros agentes para proporcionar una experiencia completa al usuario.

### Principios de Diseño

- **Especialización**: Cada agente se enfoca en una tarea específica
- **Coordinación**: Los agentes trabajan juntos de manera coordinada
- **Modularidad**: Cada agente puede funcionar de manera independiente
- **Escalabilidad**: Fácil agregar nuevos agentes o funcionalidades

---

## Intelligent Agent (Agente Coordinador)

### 🎯 Propósito Principal

El Intelligent Agent es el **punto de entrada principal** del sistema. Actúa como coordinador maestro que gestiona todo el flujo de interacción con el usuario, desde la autenticación hasta la generación de recomendaciones finales.

### 🔑 Funcionalidades Principales

#### 1. Gestión de Autenticación
- **Detección de estado de autenticación**: Identifica si el usuario está autenticado o no
- **Procesamiento de autenticación OTP**: 
  - Detecta cuando el usuario proporciona email y nombre
  - Coordina el envío de códigos OTP
  - Verifica códigos de autenticación
  - Crea sesiones autenticadas
- **Manejo de sesiones**: Gestiona tokens de sesión y estados de autenticación

#### 2. Gestión de Estados de Sesión
El agente mantiene y gestiona diferentes estados de la sesión del usuario:

- **NEW (Nueva Sesión)**: 
  - Detecta cuando un usuario autenticado inicia una nueva conversación
  - Inicia el proceso de entrevista

- **INTERVIEWING (Entrevista en Curso)**:
  - Detecta cuando hay una entrevista activa
  - Enruta las respuestas del usuario al Interviewer Agent
  - Gestiona el progreso de la entrevista

- **ANALYZING (Analizando Perfil)**:
  - Detecta cuando la entrevista está completa
  - Inicia el proceso de análisis del perfil
  - Coordina Profiler y Recommender Agents

- **RECOMMENDING (Recomendación Generada)**:
  - Detecta cuando ya se generó una recomendación
  - Permite al usuario hacer preguntas adicionales
  - Enruta consultas sobre programas al Recommender Agent

#### 3. Enrutamiento Inteligente
- **Análisis de consultas**: Determina qué tipo de consulta es (autenticación, respuesta a entrevista, pregunta sobre programas)
- **Delegación a agentes especializados**: Enruta cada consulta al agente apropiado según el contexto
- **Manejo de transiciones**: Gestiona las transiciones entre diferentes estados del flujo

#### 4. Detección de Intenciones del Usuario
- **Detectar solicitud de detener entrevista**: Identifica cuando el usuario quiere finalizar la entrevista antes de tiempo
- **Detectar preguntas durante entrevista**: Identifica cuando el usuario hace una pregunta en lugar de responder
- **Manejo de respuestas y preguntas**: Distingue entre respuestas a preguntas de la entrevista y preguntas del usuario

#### 5. Coordinación del Flujo Completo
- **Orquestación de agentes**: Coordina la secuencia de trabajo entre Interviewer, Profiler y Recommender Agents
- **Gestión de errores**: Maneja errores y proporciona respuestas de respaldo
- **Logging y trazabilidad**: Registra todas las operaciones para debugging y análisis

#### 6. Respuestas de Respaldo
- **Manejo de errores**: Proporciona mensajes de error amigables cuando algo falla
- **Información de contacto**: Proporciona información de contacto cuando el sistema no puede ayudar
- **Reinicio de sesión**: Permite al usuario reiniciar el proceso si es necesario

### 🔄 Flujo de Trabajo

1. **Recepción de consulta** → Analiza el estado de autenticación
2. **Si no autenticado** → Gestiona proceso de autenticación OTP
3. **Si autenticado** → Determina estado de sesión
4. **Según estado** → Enruta a agente apropiado:
   - NEW → Interviewer Agent
   - INTERVIEWING → Interviewer Agent
   - ANALYZING → Profiler + Recommender Agents
   - RECOMMENDING → Recommender Agent
5. **Retorna respuesta** → Devuelve respuesta al usuario

---

## Interviewer Agent (Agente Entrevistador)

### 🎯 Propósito Principal

El Interviewer Agent es responsable de **recopilar información del estudiante** mediante una entrevista estructurada y dinámica. Su objetivo es construir un perfil completo del estudiante que será utilizado para generar recomendaciones personalizadas.

### 🔑 Funcionalidades Principales

#### 1. Inicio de Entrevista
- **Bienvenida personalizada**: Proporciona un mensaje de bienvenida al usuario
- **Explicación del proceso**: Informa al usuario sobre el proceso de entrevista
- **Primera pregunta**: Inicia la entrevista con la primera pregunta relevante
- **Gestión de sesión**: Inicializa y mantiene el estado de la entrevista

#### 2. Selección Dinámica de Preguntas
- **Base de datos de preguntas**: Accede a un conjunto de preguntas predefinidas almacenadas en la base de datos
- **Búsqueda semántica**: Utiliza RAG para encontrar preguntas relevantes basadas en el contexto
- **Selección inteligente**: Selecciona la siguiente pregunta más relevante basándose en:
  - Información ya recopilada
  - Preguntas ya respondidas
  - Relevancia para construir el perfil completo
- **Evita repeticiones**: No hace preguntas que ya fueron respondidas

#### 3. Procesamiento de Respuestas
- **Extracción de información**: Extrae información relevante de las respuestas del usuario
- **Validación de respuestas**: Valida que las respuestas sean apropiadas y completas
- **Almacenamiento estructurado**: Almacena la información en un formato estructurado (perfil del estudiante)
- **Manejo de respuestas incompletas**: Solicita aclaraciones cuando las respuestas no son claras

#### 4. Construcción del Perfil del Estudiante
El agente construye un perfil estructurado que incluye:

- **Información Personal**:
  - Nombre completo
  - Email
  - Teléfono
  - Ubicación

- **Formación Académica**:
  - Título universitario
  - Universidad de origen
  - Año de graduación
  - Área de estudio

- **Experiencia Profesional**:
  - Años de experiencia
  - Área de trabajo actual
  - Cargo actual
  - Industria

- **Intereses y Objetivos**:
  - Áreas de interés profesional
  - Objetivos de carrera
  - Razones para estudiar posgrado
  - Expectativas del programa

- **Preferencias**:
  - Modalidad de estudio (presencial, virtual, híbrido)
  - Disponibilidad de tiempo
  - Restricciones geográficas
  - Presupuesto

#### 5. Gestión del Progreso de la Entrevista
- **Seguimiento de progreso**: Mantiene registro de cuántas preguntas se han hecho y respondido
- **Indicadores de progreso**: Informa al usuario sobre el progreso de la entrevista
- **Detección de completitud**: Determina cuando se ha recopilado suficiente información
- **Límite de preguntas**: Respeta un límite máximo de preguntas (típicamente 20)

#### 6. Manejo de Preguntas del Usuario
- **Detección de preguntas**: Identifica cuando el usuario hace una pregunta en lugar de responder
- **Integración con RAG**: Utiliza RAG Agent para responder preguntas del usuario sobre programas
- **Continuación de entrevista**: Después de responder, continúa con la entrevista

#### 7. Finalización de Entrevista
- **Detección de finalización**: Identifica cuando la entrevista está completa
- **Validación de perfil**: Verifica que el perfil tenga información suficiente
- **Transición a análisis**: Señala que el perfil está listo para ser analizado
- **Mensaje de transición**: Informa al usuario que se procederá al análisis

### 🔄 Flujo de Trabajo

1. **Inicio** → Recibe solicitud de iniciar entrevista
2. **Selección de pregunta** → Selecciona primera pregunta relevante
3. **Presentación** → Muestra pregunta al usuario
4. **Espera respuesta** → Recibe respuesta del usuario
5. **Procesamiento** → Extrae y valida información
6. **Almacenamiento** → Guarda información en perfil
7. **Evaluación** → Determina si necesita más información
8. **Loop** → Repite pasos 2-7 hasta completar
9. **Finalización** → Marca entrevista como completa

---

## Profiler Agent (Agente Perfilador)

### 🎯 Propósito Principal

El Profiler Agent es responsable de **analizar el perfil del estudiante** y **calcular la compatibilidad** con los diferentes programas de posgrado disponibles. Genera un ranking de programas ordenados por relevancia para el estudiante.

### 🔑 Funcionalidades Principales

#### 1. Análisis del Perfil del Estudiante
- **Extracción de características clave**: Identifica las características más importantes del perfil:
  - Formación académica
  - Área de trabajo
  - Intereses profesionales
  - Objetivos de carrera
  - Años de experiencia
  - Preferencias de modalidad

- **Resumen del perfil**: Genera un resumen estructurado del perfil del estudiante
- **Identificación de fortalezas**: Identifica las fortalezas y competencias del estudiante
- **Detección de necesidades**: Identifica las necesidades de formación del estudiante

#### 2. Recuperación de Programas Disponibles
- **Búsqueda en base de conocimiento**: Utiliza RAG para recuperar información de todos los programas disponibles
- **Filtrado por relevancia**: Filtra programas basándose en características del perfil
- **Recuperación contextual**: Obtiene información detallada de cada programa relevante

#### 3. Cálculo de Compatibilidad (Scoring)
Para cada programa, el agente calcula un score de compatibilidad (0-100) basándose en:

- **Alineación académica**: 
  - Qué tan bien se alinea la formación previa con los requisitos del programa
  - Relevancia del área de estudio

- **Alineación profesional**:
  - Qué tan bien se alinea la experiencia profesional con el enfoque del programa
  - Relevancia del área de trabajo

- **Alineación de intereses**:
  - Qué tan bien se alinean los intereses del estudiante con el contenido del programa
  - Relevancia de los objetivos profesionales

- **Preferencias**:
  - Compatibilidad con modalidad preferida
  - Disponibilidad de tiempo
  - Restricciones geográficas

- **Experiencia**:
  - Años de experiencia relevante
  - Nivel de experiencia apropiado para el programa

#### 4. Generación de Rankings
- **Ordenamiento por score**: Ordena programas de mayor a menor compatibilidad
- **Selección de top matches**: Identifica los programas más relevantes (típicamente top 3-5)
- **Justificación de scores**: Genera razones explicando por qué cada programa tiene ese score

#### 5. Análisis Comparativo
- **Comparación entre programas**: Compara programas similares
- **Identificación de diferencias**: Destaca diferencias clave entre programas
- **Recomendaciones contextuales**: Proporciona contexto sobre por qué ciertos programas son mejores opciones

#### 6. Generación de Metadatos
Para cada programa en el ranking, genera:

- **Score de compatibilidad**: Número de 0 a 100
- **Razones de compatibilidad**: Lista de razones específicas
- **Detalles del programa**: Información relevante del programa
- **Áreas de fortaleza**: Qué aspectos del perfil se alinean mejor
- **Áreas de consideración**: Qué aspectos podrían necesitar atención

### 🔄 Flujo de Trabajo

1. **Recepción de perfil** → Recibe perfil completo del estudiante
2. **Extracción de características** → Identifica características clave
3. **Recuperación de programas** → Obtiene información de programas disponibles
4. **Cálculo de scores** → Calcula compatibilidad para cada programa
5. **Generación de ranking** → Ordena programas por relevancia
6. **Selección de top matches** → Identifica programas más relevantes
7. **Generación de justificaciones** → Crea razones para cada score
8. **Retorno de resultados** → Devuelve ranking y análisis completo

---

## Recommender Agent (Agente Recomendador)

### 🎯 Propósito Principal

El Recommender Agent es responsable de **generar recomendaciones personalizadas en lenguaje natural** basándose en el análisis del Profiler Agent. Transforma los datos técnicos en recomendaciones comprensibles y accionables para el usuario.

### 🔑 Funcionalidades Principales

#### 1. Generación de Recomendaciones Personalizadas
- **Transformación de datos a lenguaje natural**: Convierte el análisis técnico en texto comprensible
- **Personalización**: Adapta el lenguaje y tono al perfil del estudiante
- **Estructuración clara**: Organiza la recomendación de manera lógica y fácil de leer

#### 2. Explicación de Recomendaciones
Para cada programa recomendado, el agente explica:

- **Por qué es adecuado**: Explica las razones específicas de compatibilidad
- **Alineación con perfil**: Muestra cómo el programa se alinea con:
  - Formación académica del estudiante
  - Experiencia profesional
  - Intereses y objetivos
  - Preferencias personales

- **Beneficios esperados**: Describe qué beneficios obtendría el estudiante
- **Oportunidades de crecimiento**: Identifica oportunidades de desarrollo profesional

#### 3. Enriquecimiento con Información de Programas
Utiliza RAG para enriquecer las recomendaciones con información detallada:

- **Información académica**:
  - Plan de estudios
  - Cursos principales
  - Enfoque del programa
  - Metodología

- **Información práctica**:
  - Duración del programa
  - Modalidad (presencial, virtual, híbrido)
  - Horarios
  - Inversión/costo

- **Información de admisión**:
  - Requisitos
  - Proceso de admisión
  - Fechas importantes
  - Documentos necesarios

- **Información adicional**:
  - Facultad
  - Certificaciones
  - Oportunidades de investigación
  - Redes profesionales

#### 4. Comparación de Programas
- **Comparación lado a lado**: Compara programas recomendados destacando:
  - Similitudes
  - Diferencias clave
  - Ventajas de cada uno

- **Recomendación contextual**: Sugiere cuál programa podría ser mejor según diferentes criterios

#### 5. Próximos Pasos y Llamados a la Acción
- **Pasos siguientes**: Proporciona pasos concretos que el estudiante puede tomar:
  - Cómo obtener más información
  - Cómo iniciar proceso de admisión
  - Contactos relevantes
  - Recursos adicionales

- **Llamados a la acción**: Incluye acciones específicas y motivadoras
- **Información de contacto**: Proporciona información de contacto de admisiones

#### 6. Respuesta a Preguntas Específicas
Después de generar la recomendación inicial, el agente puede:

- **Responder preguntas sobre programas**: Utiliza RAG para responder preguntas específicas sobre cualquier programa
- **Búsqueda contextualizada**: Busca información relevante considerando el contexto del perfil del estudiante
- **Respuestas personalizadas**: Adapta las respuestas al perfil y contexto del estudiante

#### 7. Formato y Presentación
- **Estructura clara**: Organiza la información de manera lógica:
  - Resumen ejecutivo
  - Programas recomendados (ordenados por relevancia)
  - Detalles de cada programa
  - Comparación
  - Próximos pasos

- **Lenguaje natural y amigable**: Usa un tono conversacional y accesible
- **Formato legible**: Estructura el texto para fácil lectura

### 🔄 Flujo de Trabajo

1. **Recepción de análisis** → Recibe resultados del Profiler Agent
2. **Enriquecimiento con RAG** → Obtiene información detallada de programas recomendados
3. **Generación de recomendación** → Crea texto de recomendación personalizada
4. **Estructuración** → Organiza la información de manera clara
5. **Inclusión de próximos pasos** → Agrega llamados a la acción
6. **Retorno** → Devuelve recomendación completa al usuario

---

## RAG Agent (Agente de Búsqueda Semántica)

### 🎯 Propósito Principal

El RAG Agent proporciona capacidades de **búsqueda semántica y recuperación de información** desde la base de conocimiento del sistema. Es utilizado por otros agentes para obtener información relevante sobre programas, preguntas de entrevista y documentación general.

### 🔑 Funcionalidades Principales

#### 1. Búsqueda Semántica en Documentos
- **Búsqueda por significado**: Busca información basándose en el significado semántico, no solo palabras clave
- **Recuperación de contexto relevante**: Encuentra documentos y fragmentos relevantes para una consulta
- **Ranking por relevancia**: Ordena resultados por relevancia semántica
- **Filtrado por umbral**: Filtra resultados por un umbral de relevancia mínimo

#### 2. Búsqueda de Información de Programas
- **Búsqueda de programas específicos**: Encuentra información sobre programas de posgrado específicos
- **Búsqueda por características**: Busca programas que cumplan ciertas características:
  - Área de estudio
  - Modalidad
  - Duración
  - Enfoque

- **Información completa**: Recupera información detallada sobre:
  - Descripción del programa
  - Plan de estudios
  - Requisitos
  - Costos
  - Facultad

#### 3. Búsqueda de Preguntas de Entrevista
- **Recuperación de preguntas relevantes**: Encuentra preguntas de entrevista relevantes basándose en el contexto
- **Filtrado por categoría**: Filtra preguntas por categoría o campo
- **Selección contextual**: Selecciona preguntas apropiadas según información ya recopilada

#### 4. Generación de Respuestas Contextualizadas
- **Síntesis de información**: Combina información de múltiples fuentes
- **Respuestas coherentes**: Genera respuestas coherentes y completas
- **Contexto relevante**: Incluye solo información relevante para la consulta
- **Citas y referencias**: Puede incluir referencias a fuentes cuando es apropiado

#### 5. Soporte para Múltiples Colecciones
El agente puede trabajar con diferentes colecciones de documentos:

- **Programas de posgrado**: Información sobre programas académicos
- **Preguntas de entrevista**: Banco de preguntas para la entrevista
- **Documentación general**: Documentos generales sobre la universidad y procesos
- **Documentos combinados**: Búsqueda en múltiples colecciones simultáneamente

#### 6. Integración con LLM
- **Generación de embeddings**: Utiliza modelos de embeddings para representar documentos y consultas
- **Generación de respuestas**: Utiliza LLM para generar respuestas basadas en contexto recuperado
- **Mejora de búsqueda**: Utiliza LLM para mejorar y refinar búsquedas

### 🔄 Flujo de Trabajo

1. **Recepción de consulta** → Recibe consulta o pregunta
2. **Generación de embedding** → Crea representación vectorial de la consulta
3. **Búsqueda semántica** → Busca documentos similares en la base vectorial
4. **Ranking y filtrado** → Ordena y filtra resultados por relevancia
5. **Recuperación de contexto** → Extrae fragmentos relevantes de documentos
6. **Síntesis** → Combina información recuperada
7. **Generación de respuesta** → Crea respuesta contextualizada (si aplica)
8. **Retorno** → Devuelve información o respuesta

---

## Flujo Completo de Funcionalidades

### 🔄 Flujo Principal del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO INICIA SESIÓN                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         INTELLIGENT AGENT: Gestión de Autenticación          │
│  - Detecta que usuario no está autenticado                   │
│  - Solicita email y nombre                                   │
│  - Genera y envía código OTP                                 │
│  - Verifica código y crea sesión autenticada                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│      INTELLIGENT AGENT: Detección de Estado (NEW)            │
│  - Detecta que es una nueva sesión                          │
│  - Enruta a Interviewer Agent                                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         INTERVIEWER AGENT: Inicio de Entrevista              │
│  - Proporciona bienvenida                                   │
│  - Explica el proceso                                       │
│  - Selecciona primera pregunta relevante                    │
│  - Muestra pregunta al usuario                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                    ┌───────┴───────┐
                    │               │
                    ▼               ▼
        ┌──────────────────┐  ┌──────────────────┐
        │ Usuario responde │  │ Usuario pregunta │
        └────────┬─────────┘  └────────┬─────────┘
                 │                     │
                 │                     ▼
                 │         ┌───────────────────────┐
                 │         │ RAG AGENT: Responde   │
                 │         │ pregunta del usuario  │
                 │         └───────────┬───────────┘
                 │                     │
                 └──────────┬──────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│    INTERVIEWER AGENT: Procesamiento de Respuesta             │
│  - Extrae información de la respuesta                      │
│  - Valida y almacena en perfil                             │
│  - Evalúa si necesita más información                      │
│  - Selecciona siguiente pregunta relevante                  │
│  - Muestra siguiente pregunta                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                    ┌───────┴───────┐
                    │               │
                    ▼               ▼
        ┌──────────────────┐  ┌──────────────────┐
        │ Más preguntas    │  │ Entrevista       │
        │ necesarias       │  │ completa         │
        └────────┬─────────┘  └────────┬─────────┘
                 │                     │
                 │                     ▼
                 │    ┌──────────────────────────────┐
                 │    │ INTELLIGENT AGENT: Estado    │
                 │    │ cambia a ANALYZING          │
                 │    └──────────────┬───────────────┘
                 │                   │
                 └───────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         PROFILER AGENT: Análisis del Perfil                 │
│  - Extrae características clave del perfil                 │
│  - Recupera información de programas disponibles           │
│  - Calcula scores de compatibilidad para cada programa     │
│  - Genera ranking de programas ordenados por relevancia    │
│  - Identifica top matches                                  │
│  - Genera justificaciones para cada score                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│      RECOMMENDER AGENT: Generación de Recomendación          │
│  - Recibe resultados del análisis                          │
│  - Utiliza RAG para enriquecer con información detallada   │
│  - Genera recomendación personalizada en lenguaje natural │
│  - Explica por qué cada programa es adecuado               │
│  - Compara programas recomendados                          │
│  - Proporciona próximos pasos y llamados a la acción       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         INTELLIGENT AGENT: Estado cambia a RECOMMENDING     │
│  - Marca sesión como con recomendación generada            │
│  - Permite preguntas adicionales                           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│    RECOMMENDER AGENT: Respuesta a Preguntas Adicionales     │
│  - Recibe pregunta del usuario sobre programas              │
│  - Utiliza RAG para buscar información específica           │
│  - Genera respuesta contextualizada y personalizada        │
│  - Considera el perfil del estudiante en la respuesta      │
└─────────────────────────────────────────────────────────────┘
```

---

## Casos de Uso por Agente

### Intelligent Agent

#### Caso de Uso 1: Nuevo Usuario
1. Usuario accede al sistema
2. Intelligent Agent detecta que no está autenticado
3. Solicita email y nombre
4. Genera y envía código OTP
5. Usuario ingresa código
6. Intelligent Agent verifica y crea sesión autenticada
7. Inicia proceso de entrevista

#### Caso de Uso 2: Usuario Durante Entrevista
1. Usuario está en medio de entrevista
2. Intelligent Agent detecta estado INTERVIEWING
3. Enruta respuesta a Interviewer Agent
4. Interviewer procesa y genera siguiente pregunta
5. Intelligent Agent retorna pregunta al usuario

#### Caso de Uso 3: Usuario Quiere Detener Entrevista
1. Usuario escribe "No me hagas más preguntas"
2. Intelligent Agent detecta intención
3. Marca entrevista como completa
4. Inicia proceso de análisis inmediatamente
5. Genera recomendación con información disponible

### Interviewer Agent

#### Caso de Uso 1: Primera Pregunta
1. Interviewer Agent recibe solicitud de iniciar entrevista
2. Accede a base de datos de preguntas
3. Selecciona pregunta más relevante para comenzar (típicamente nombre)
4. Presenta pregunta al usuario
5. Espera respuesta

#### Caso de Uso 2: Selección Inteligente de Preguntas
1. Usuario ha respondido varias preguntas
2. Interviewer Agent analiza información recopilada
3. Identifica qué información falta
4. Utiliza RAG para encontrar preguntas relevantes
5. Selecciona pregunta que mejor complementa el perfil
6. Evita preguntas ya respondidas

#### Caso de Uso 3: Validación de Respuesta
1. Usuario proporciona respuesta
2. Interviewer Agent valida formato y completitud
3. Si respuesta es incompleta, solicita aclaración
4. Si respuesta es válida, extrae información
5. Almacena en perfil estructurado

### Profiler Agent

#### Caso de Uso 1: Análisis de Perfil Completo
1. Profiler Agent recibe perfil completo del estudiante
2. Extrae características clave (formación, experiencia, intereses)
3. Utiliza RAG para recuperar información de todos los programas
4. Calcula score de compatibilidad para cada programa
5. Genera ranking ordenado
6. Identifica top 3-5 programas más relevantes
7. Genera justificaciones para cada score

#### Caso de Uso 2: Análisis de Perfil Parcial
1. Usuario detiene entrevista antes de completar
2. Profiler Agent recibe perfil parcial
3. Trabaja con información disponible
4. Calcula scores considerando información faltante
5. Genera recomendaciones con advertencias sobre información incompleta

### Recommender Agent

#### Caso de Uso 1: Generación de Recomendación Inicial
1. Recommender Agent recibe resultados del Profiler
2. Para cada programa en top matches:
   - Utiliza RAG para obtener información detallada
   - Genera explicación personalizada
   - Identifica beneficios específicos para el estudiante
3. Compara programas entre sí
4. Genera texto de recomendación estructurado
5. Incluye próximos pasos y llamados a la acción

#### Caso de Uso 2: Respuesta a Pregunta Específica
1. Usuario pregunta: "¿Cuánto cuesta la Maestría en Ciencia de Datos?"
2. Recommender Agent utiliza RAG para buscar información específica
3. Encuentra información de costo del programa
4. Genera respuesta contextualizada considerando el perfil del estudiante
5. Puede incluir información adicional relevante (becas, financiación, etc.)

### RAG Agent

#### Caso de Uso 1: Búsqueda de Información de Programa
1. Otro agente necesita información sobre un programa específico
2. RAG Agent recibe consulta: "Información sobre Maestría en Ciencia de Datos"
3. Genera embedding de la consulta
4. Busca en base vectorial de programas
5. Encuentra documentos relevantes
6. Recupera fragmentos con información relevante
7. Retorna información estructurada

#### Caso de Uso 2: Búsqueda de Preguntas de Entrevista
1. Interviewer Agent necesita siguiente pregunta
2. RAG Agent recibe contexto: información ya recopilada
3. Busca preguntas relevantes basándose en contexto
4. Filtra por categoría y relevancia
5. Retorna preguntas candidatas ordenadas por relevancia

---

## Resumen de Funcionalidades por Agente

| Agente | Funcionalidad Principal | Entrada | Salida |
|--------|------------------------|---------|--------|
| **Intelligent Agent** | Coordinación y enrutamiento | Consultas del usuario | Respuestas coordinadas |
| **Interviewer Agent** | Recopilación de información | Respuestas del usuario | Perfil estructurado del estudiante |
| **Profiler Agent** | Análisis y matching | Perfil del estudiante | Ranking de programas con scores |
| **Recommender Agent** | Generación de recomendaciones | Resultados del análisis | Recomendación personalizada en texto |
| **RAG Agent** | Búsqueda semántica | Consultas de búsqueda | Información relevante recuperada |

---

## Características Clave del Sistema

### ✅ Inteligencia Contextual
- Los agentes consideran el contexto completo de la conversación
- Las decisiones se basan en información acumulada
- Las respuestas se adaptan al perfil del usuario

### ✅ Personalización
- Cada recomendación es única para cada estudiante
- El sistema se adapta a las preferencias y necesidades individuales
- El lenguaje y tono se ajustan al usuario

### ✅ Modularidad
- Cada agente puede funcionar independientemente
- Fácil agregar nuevas funcionalidades
- Fácil modificar comportamiento de agentes individuales

### ✅ Escalabilidad
- El sistema puede manejar múltiples usuarios simultáneamente
- Cada sesión es independiente
- Fácil agregar nuevos agentes o capacidades

### ✅ Trazabilidad
- Todas las operaciones se registran
- Fácil debugging y análisis
- Transparencia en el proceso de recomendación

---

**Última actualización**: 2024  
**Versión**: 1.0  
**Mantenedor**: Equipo de Desarrollo ICESI


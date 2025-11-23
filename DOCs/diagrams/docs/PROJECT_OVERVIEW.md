# 📚 Documentación General del Proyecto
## Sistema de Recomendación de Posgrados - Universidad ICESI

---

## 📋 Tabla de Contenidos

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Diagramas de Arquitectura C4](#diagramas-de-arquitectura-c4)
4. [Componentes Principales](#componentes-principales)
5. [Flujos de Proceso](#flujos-de-proceso)
6. [Tecnologías Utilizadas](#tecnologías-utilizadas)
7. [Estructura del Proyecto](#estructura-del-proyecto)
8. [Instalación y Configuración](#instalación-y-configuración)
9. [Documentación Adicional](#documentación-adicional)

---

## Descripción del Proyecto

### 🎯 Propósito

El **Sistema de Recomendación de Posgrados de la Universidad ICESI** es una aplicación inteligente basada en IA que ayuda a estudiantes prospectivos a encontrar el programa de posgrado más adecuado para su perfil profesional. El sistema utiliza técnicas avanzadas de procesamiento de lenguaje natural (NLP), recuperación aumentada por generación (RAG) y agentes inteligentes para proporcionar recomendaciones personalizadas.

### 🎓 Objetivos

- **Recomendación Personalizada**: Analizar el perfil del estudiante y recomendar programas de posgrado que mejor se ajusten a sus objetivos profesionales
- **Experiencia Interactiva**: Proporcionar una entrevista guiada que recopila información relevante del estudiante
- **Información Contextualizada**: Utilizar RAG para responder preguntas específicas sobre programas usando documentación oficial
- **Autenticación Segura**: Implementar autenticación mediante códigos OTP para proteger la información del usuario

### 👥 Usuarios

- **Estudiantes Prospectivos**: Usuarios que buscan información sobre programas de posgrado
- **Administradores**: Personal administrativo que gestiona el sistema y la documentación

---

## Arquitectura del Sistema

### 🏗️ Visión General

El sistema está construido con una arquitectura modular basada en agentes inteligentes que trabajan de manera coordinada para proporcionar una experiencia completa al usuario.

```
┌─────────────────────────────────────────────────────────┐
│              Aplicación Web (Streamlit)                 │
│              Interfaz de Usuario                        │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│         Intelligent Agent (Coordinador)                 │
│  - Gestiona autenticación                             │
│  - Coordina flujo completo                            │
│  - Maneja estados de sesión                           │
└─────┬──────────────┬──────────────┬────────────────────┘
      │              │              │
      ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│Interviewer│  │ Profiler │  │Recommender│
│  Agent    │  │  Agent   │  │  Agent   │
└──────────┘  └──────────┘  └──────────┘
                     │
                     ▼
              ┌──────────┐
              │RAG Agent │
              └──────────┘
```

### 🔄 Flujo Principal

1. **Autenticación**: El usuario se autentica mediante código OTP enviado por email
2. **Entrevista**: El sistema realiza una entrevista guiada para recopilar información del estudiante
3. **Análisis**: El perfil del estudiante se analiza y se calculan matches con programas disponibles
4. **Recomendación**: Se genera una recomendación personalizada basada en el análisis
5. **Seguimiento**: El usuario puede hacer preguntas adicionales sobre los programas recomendados

---

## Diagramas de Arquitectura C4

El proyecto incluye diagramas de arquitectura siguiendo el modelo C4, que proporciona diferentes niveles de abstracción para entender el sistema. Todos los diagramas están disponibles en `DOCs/diagrams/` y se pueden generar usando las herramientas descritas en [C4_ARCHITECTURE_DIAGRAMS.md](./C4_ARCHITECTURE_DIAGRAMS.md).

### 📊 Nivel 1: Diagrama de Contexto

**Archivo**: `DOCs/diagrams/C4_Context.puml`  
**Imagen generada**: `DOCs/diagrams/generated/C4_Context.png`

#### Descripción

El diagrama de contexto muestra el sistema en su entorno completo, identificando:

- **Actores**:
  - **Estudiante Prospectivo**: Usuario principal que consulta información sobre posgrados
  - **Administrador**: Personal que gestiona el sistema y la configuración

- **Sistema Principal**:
  - **Sistema de Recomendación de Posgrados ICESI**: El sistema completo que proporciona recomendaciones personalizadas

- **Sistemas Externos**:
  - **OpenAI API**: Proporciona servicios de IA (embeddings y LLM GPT-4o-mini)
  - **Servidor SMTP**: Envía códigos OTP por correo electrónico
  - **Google OAuth**: Servicio de autenticación con Google (opcional)
  - **LangSmith**: Plataforma de observabilidad y trazabilidad para aplicaciones LLM (opcional)

#### Relaciones Clave

- El estudiante consulta información a través de HTTPS
- El sistema obtiene embeddings y genera respuestas usando OpenAI API
- El sistema envía códigos OTP mediante SMTP
- El sistema puede autenticar usuarios con Google OAuth
- El sistema envía trazas y métricas a LangSmith (opcional)

#### Uso

Este diagrama es ideal para:
- Presentaciones a stakeholders no técnicos
- Documentación de alto nivel
- Entender el contexto del sistema en su ecosistema

---

### 🏢 Nivel 2: Diagrama de Contenedores

**Archivo**: `DOCs/diagrams/C4_Container.puml`  
**Imagen generada**: `DOCs/diagrams/generated/C4_Container.png`

#### Descripción

El diagrama de contenedores descompone el sistema en sus componentes principales de infraestructura:

- **Aplicación Web (Streamlit)**:
  - Tecnología: Streamlit
  - Responsabilidad: Interfaz de usuario para chat y administración
  - Puerto: 8501

- **Backend Python**:
  - Tecnología: Python 3.13
  - Responsabilidad: Lógica de negocio, agentes inteligentes y herramientas
  - Contiene toda la lógica de procesamiento

- **Base de Datos SQLite**:
  - Tecnología: SQLite
  - Responsabilidad: Almacena metadatos, sesiones, usuarios y mensajes
  - Archivo: `doc_sage.sqlite`

- **Base de Datos Vectorial (ChromaDB)**:
  - Tecnología: ChromaDB
  - Responsabilidad: Almacena embeddings y documentos para RAG
  - Directorio: `static/persist/`

- **Sistema de Archivos**:
  - Tecnología: File System
  - Responsabilidad: Documentos fuente, archivos temporales y persistencia
  - Directorios: `static/sample_documents/`, `static/temp_files/`

#### Flujo de Datos

```
Usuario → Aplicación Web → Backend Python
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
                SQLite              ChromaDB
                    ↓                   ↓
              Metadatos            Vectores
```

#### Uso

Este diagrama es útil para:
- Arquitectos de software
- Desarrolladores senior
- Planificación de infraestructura
- Decisiones de despliegue

---

### 🧩 Nivel 3: Diagrama de Componentes

**Archivo**: `DOCs/diagrams/C4_Component.puml`  
**Imagen generada**: `DOCs/diagrams/generated/C4_Component.png`

#### Descripción

El diagrama de componentes muestra la estructura interna del Backend Python, identificando los agentes, herramientas y módulos de infraestructura.

#### Agentes

1. **Intelligent Agent** (`src/agents/intelligent_agent.py`)
   - Coordina el flujo completo del sistema
   - Gestiona estados de sesión (NEW, INTERVIEWING, ANALYZING, RECOMMENDING)
   - Maneja autenticación y enrutamiento

2. **Interviewer Agent** (`src/agents/interviewer_agent.py`)
   - Recopila información del estudiante mediante entrevista estructurada
   - Gestiona preguntas y respuestas
   - Almacena perfil del estudiante

3. **Profiler Agent** (`src/agents/profiler_agent.py`)
   - Analiza el perfil del estudiante
   - Calcula matches con programas disponibles
   - Genera rankings de programas

4. **Recommender Agent** (`src/agents/recommender_agent.py`)
   - Genera recomendaciones personalizadas
   - Utiliza RAG para obtener información de programas
   - Responde preguntas específicas sobre programas

5. **RAG Agent** (`src/agents/rag_agent.py`)
   - Realiza búsqueda semántica en documentos
   - Utiliza ChromaDB para recuperación vectorial
   - Integra con OpenAI para embeddings

#### Herramientas

- **OTP Auth** (`src/tools/otp_auth.py`): Autenticación mediante códigos OTP
- **Google Auth** (`src/tools/google_auth.py`): Autenticación con Google OAuth
- **Document Retriever** (`src/tools/document_retriever.py`): Recupera documentos relevantes
- **Query Processor** (`src/tools/query_processor.py`): Procesa y clasifica consultas
- **Chat Memory** (`src/tools/chat_memory.py`): Gestiona memoria de conversación

#### Infraestructura

- **DB Model** (`src/models/db.py`): Acceso a base de datos SQLite
- **Vector Functions** (`src/utils/vector_functions.py`): Operaciones con ChromaDB
- **Tracing** (`src/utils/tracing.py`): Sistema de trazabilidad

#### Uso

Este diagrama es esencial para:
- Desarrolladores del equipo
- Entender la estructura del código
- Planificar nuevas funcionalidades
- Refactorización

---

### 📈 Diagramas de Secuencia

#### Flujo Completo del Sistema

**Archivo**: `DOCs/diagrams/sequence_complete.mmd`  
**Imagen generada**: `DOCs/diagrams/generated/sequence_complete.png`

Este diagrama muestra el flujo completo desde la autenticación hasta la recomendación:

1. **Fase de Autenticación**:
   - Usuario proporciona email y nombre
   - Sistema genera y envía código OTP
   - Usuario verifica código
   - Sistema autentica y crea sesión

2. **Fase de Entrevista**:
   - Sistema inicia entrevista
   - Loop de preguntas y respuestas
   - Sistema almacena información del perfil

3. **Fase de Análisis y Recomendación**:
   - Sistema analiza perfil con Profiler Agent
   - Sistema calcula matches con programas
   - Recommender Agent genera recomendación usando RAG
   - Sistema presenta recomendación al usuario

#### Flujo de Autenticación OTP

**Archivo**: `DOCs/diagrams/sequence_auth.mmd`  
**Imagen generada**: `DOCs/diagrams/generated/sequence_auth.png`

Este diagrama detalla el proceso de autenticación:

1. **Envío de Código**:
   - Usuario proporciona email y nombre
   - Sistema genera código OTP de 6 dígitos
   - Sistema almacena código en base de datos
   - Sistema envía email con código

2. **Verificación**:
   - Usuario proporciona código
   - Sistema verifica código y expiración
   - Si válido: crea usuario y sesión
   - Si inválido: muestra error

---

## Componentes Principales

### 🤖 Agentes Inteligentes

El sistema utiliza una arquitectura basada en agentes donde cada agente tiene responsabilidades específicas:

#### Intelligent Agent (Coordinador)

- **Responsabilidad**: Coordinar todo el flujo del sistema
- **Funciones principales**:
  - Gestionar autenticación OTP
  - Determinar estado de sesión
  - Enrutar consultas a agentes apropiados
  - Manejar errores y logging

#### Interviewer Agent

- **Responsabilidad**: Recopilar información del estudiante
- **Funciones principales**:
  - Iniciar y gestionar entrevista
  - Seleccionar preguntas relevantes
  - Validar respuestas
  - Construir perfil del estudiante

#### Profiler Agent

- **Responsabilidad**: Analizar perfil y calcular matches
- **Funciones principales**:
  - Analizar perfil del estudiante
  - Calcular compatibilidad con programas
  - Generar rankings de programas
  - Identificar programas más relevantes

#### Recommender Agent

- **Responsabilidad**: Generar recomendaciones personalizadas
- **Funciones principales**:
  - Generar recomendación basada en análisis
  - Utilizar RAG para obtener información de programas
  - Responder preguntas específicas sobre programas
  - Formatear recomendación de manera amigable

#### RAG Agent

- **Responsabilidad**: Búsqueda semántica en documentos
- **Funciones principales**:
  - Realizar búsqueda vectorial en ChromaDB
  - Recuperar documentos relevantes
  - Generar contexto para LLM
  - Integrar información de múltiples fuentes

### 🛠️ Herramientas

- **OTP Auth**: Sistema de autenticación mediante códigos de un solo uso
- **Google Auth**: Integración con Google OAuth (opcional)
- **Document Retriever**: Recuperación de documentos desde ChromaDB
- **Query Processor**: Procesamiento y clasificación de consultas
- **Chat Memory**: Gestión de memoria de conversación y sesiones

### 💾 Almacenamiento

- **SQLite**: Metadatos, usuarios, sesiones, mensajes, códigos OTP
- **ChromaDB**: Embeddings de documentos, búsqueda vectorial
- **File System**: Documentos fuente (PDF, TXT, Excel), archivos temporales

---

## Flujos de Proceso

### 🔐 Flujo de Autenticación

```
1. Usuario → Proporciona email y nombre
2. Sistema → Genera código OTP (6 dígitos)
3. Sistema → Almacena código en BD (expira en 10 min)
4. Sistema → Envía email con código
5. Usuario → Proporciona código
6. Sistema → Verifica código y expiración
7. Sistema → Crea sesión autenticada
```

### 📝 Flujo de Entrevista

```
1. Sistema → Detecta sesión nueva
2. Sistema → Inicia entrevista con Interviewer Agent
3. Sistema → Muestra primera pregunta
4. Loop:
   a. Usuario → Responde pregunta
   b. Sistema → Valida y almacena respuesta
   c. Sistema → Selecciona siguiente pregunta
   d. Sistema → Muestra siguiente pregunta
5. Sistema → Detecta entrevista completa
6. Sistema → Transición a análisis
```

### 🎯 Flujo de Recomendación

```
1. Sistema → Obtiene perfil completo
2. Sistema → Profiler Agent analiza perfil
3. Sistema → Calcula matches con programas
4. Sistema → Recommender Agent genera recomendación
5. Recommender → RAG Agent busca información de programas
6. RAG Agent → Recupera documentos relevantes
7. Recommender → Genera recomendación personalizada
8. Sistema → Presenta recomendación al usuario
```

---

## Tecnologías Utilizadas

### Frontend
- **Streamlit**: Framework para aplicaciones web interactivas
- **Python 3.13**: Lenguaje de programación

### Backend
- **Python 3.13**: Lenguaje principal
- **LangChain**: Framework para aplicaciones LLM
- **OpenAI API**: Servicios de embeddings y LLM (GPT-4o-mini)

### Bases de Datos
- **SQLite**: Base de datos relacional para metadatos
- **ChromaDB**: Base de datos vectorial para embeddings

### Autenticación
- **OTP (One-Time Password)**: Códigos de verificación por email
- **Google OAuth**: Autenticación con Google (opcional)

### Observabilidad
- **LangSmith**: Plataforma de trazabilidad (opcional)
- **Sistema de Tracing**: Logging y trazabilidad interno

### Despliegue
- **Docker**: Contenedorización
- **Docker Compose**: Orquestación de contenedores
- **Nginx**: Proxy reverso (opcional, producción)

---

## Estructura del Proyecto

```
GENERATIVE_AI_ICESI/
├── 📁 src/                          # Código fuente principal
│   ├── app.py                      # Aplicación principal Streamlit
│   ├── init_app.py                 # Script de inicialización
│   ├── agents/                     # Agentes inteligentes
│   │   ├── intelligent_agent.py   # Coordinador principal
│   │   ├── interviewer_agent.py   # Recopila información
│   │   ├── profiler_agent.py       # Analiza perfil
│   │   ├── recommender_agent.py    # Genera recomendaciones
│   │   └── rag_agent.py            # Búsqueda semántica
│   ├── tools/                      # Herramientas del sistema
│   │   ├── otp_auth.py            # Autenticación OTP
│   │   ├── google_auth.py          # Autenticación Google
│   │   ├── document_retriever.py   # Recuperación de documentos
│   │   ├── query_processor.py     # Procesamiento de consultas
│   │   └── chat_memory.py          # Memoria de conversación
│   ├── models/                     # Modelos de datos
│   │   └── db.py                  # Acceso a SQLite
│   ├── utils/                      # Utilidades
│   │   ├── vector_functions.py    # Operaciones con ChromaDB
│   │   └── tracing.py             # Sistema de trazabilidad
│   ├── views/                      # Vistas de la aplicación
│   │   └── public_chat.py         # Vista principal de chat
│   └── templates/                  # Plantillas y prompts
│       ├── agent_prompts.py        # Prompts para agentes
│       └── agent_reasoning.py     # Prompts de reasoning
│
├── 📁 DOCs/                         # Documentación
│   ├── PROJECT_OVERVIEW.md         # Este documento
│   ├── C4_ARCHITECTURE_DIAGRAMS.md # Guía de diagramas C4
│   ├── AGENT_ARCHITECTURE.md       # Arquitectura de agentes
│   └── diagrams/                   # Archivos fuente de diagramas
│       ├── C4_Context.puml        # Diagrama de contexto
│       ├── C4_Container.puml      # Diagrama de contenedores
│       ├── C4_Component.puml       # Diagrama de componentes
│       ├── sequence_complete.mmd   # Flujo completo
│       ├── sequence_auth.mmd      # Flujo de autenticación
│       └── generated/             # Diagramas generados (PNG)
│
├── 📁 static/                       # Archivos estáticos
│   ├── sample_documents/          # Documentos fuente
│   ├── persist/                    # Base de datos ChromaDB
│   └── temp_files/                 # Archivos temporales
│
├── 📁 scripts/                      # Scripts de utilidad
│   └── generate_diagrams.sh       # Generar diagramas C4
│
├── docker-compose.yml              # Configuración Docker
├── Dockerfile                      # Imagen Docker
├── requirements.txt                # Dependencias Python
├── env.example                     # Ejemplo de variables de entorno
└── README.md                       # README principal
```

---

## Instalación y Configuración

### Prerrequisitos

- Python 3.13 o superior
- Docker y Docker Compose (opcional)
- API Key de OpenAI
- Servidor SMTP configurado (para OTP)

### Instalación Rápida

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd GENERATIVE_AI_ICESI

# 2. Configurar variables de entorno
cp env.example .env
# Editar .env con tus credenciales

# 3. Ejecutar con Docker
docker-compose up --build

# O ejecutar localmente
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd src && python init_app.py
streamlit run app.py
```

### Variables de Entorno Requeridas

```env
# OpenAI (Requerido)
OPENAI_API_KEY=tu_api_key_aqui

# Email SMTP (Requerido para OTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_app_password
SMTP_FROM=tu_email@gmail.com

# Google OAuth (Opcional)
GOOGLE_CLIENT_ID=tu_client_id
GOOGLE_CLIENT_SECRET=tu_client_secret

# LangSmith (Opcional)
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=tu_api_key
```

Para más detalles, consulta:
- [README.md](../README.md) - Instrucciones detalladas
- [DOCKER_ENV_SETUP.md](./DOCKER_ENV_SETUP.md) - Configuración Docker

---

## Documentación Adicional

### 📚 Documentos Disponibles

1. **[C4_ARCHITECTURE_DIAGRAMS.md](./C4_ARCHITECTURE_DIAGRAMS.md)**
   - Guía completa para generar diagramas C4
   - Ejemplos de código PlantUML y Mermaid
   - Instrucciones de uso de herramientas

2. **[AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md)**
   - Arquitectura detallada de agentes
   - Responsabilidades de cada agente
   - Flujos de comunicación

3. **[README.md](../README.md)**
   - Documentación principal del proyecto
   - Instrucciones de instalación
   - Guía de uso

4. **Documentación de Configuración**:
   - [DOCKER_ENV_SETUP.md](./DOCKER_ENV_SETUP.md) - Configuración Docker
   - [GOOGLE_AUTH_SETUP.md](./GOOGLE_AUTH_SETUP.md) - Configuración Google OAuth
   - [LANGSMITH_SETUP.md](./LANGSMITH_SETUP.md) - Configuración LangSmith

### 🔗 Enlaces Útiles

- **Generar Diagramas**: `./scripts/generate_diagrams.sh`
- **Ver Diagramas**: `DOCs/diagrams/generated/`
- **Archivos Fuente**: `DOCs/diagrams/*.puml` y `*.mmd`

---

## Resumen de Diagramas

| Diagrama | Nivel | Archivo Fuente | Descripción |
|----------|-------|----------------|-------------|
| **Contexto** | C4-1 | `C4_Context.puml` | Sistema en su entorno, usuarios y sistemas externos |
| **Contenedores** | C4-2 | `C4_Container.puml` | Componentes principales de infraestructura |
| **Componentes** | C4-3 | `C4_Component.puml` | Estructura interna del backend |
| **Secuencia Completa** | - | `sequence_complete.mmd` | Flujo completo desde autenticación hasta recomendación |
| **Secuencia Autenticación** | - | `sequence_auth.mmd` | Proceso detallado de autenticación OTP |

### Cómo Generar Diagramas

```bash
# Opción 1: Script automatizado
./scripts/generate_diagrams.sh

# Opción 2: Manual
cd DOCs/diagrams
plantuml *.puml -o generated
mmdc -i sequence_complete.mmd -o generated/sequence_complete.png
```

---

## Conclusión

Este documento proporciona una visión general completa del **Sistema de Recomendación de Posgrados de la Universidad ICESI**, incluyendo:

- ✅ Descripción del proyecto y objetivos
- ✅ Arquitectura del sistema
- ✅ Descripción detallada de todos los diagramas C4
- ✅ Componentes principales y sus responsabilidades
- ✅ Flujos de proceso principales
- ✅ Tecnologías utilizadas
- ✅ Estructura del proyecto
- ✅ Referencias a documentación adicional

Para más detalles sobre cualquier aspecto específico, consulta la documentación adicional en el directorio `DOCs/`.

---

**Última actualización**: 2024  
**Versión del documento**: 1.0  
**Autor**: Equipo de Desarrollo ICESI


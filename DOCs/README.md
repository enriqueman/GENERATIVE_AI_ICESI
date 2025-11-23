# 📚 Documentación del Proyecto
## Sistema de Recomendación de Posgrados - Universidad ICESI

Este directorio contiene toda la documentación técnica del proyecto. El **Sistema de Recomendación de Posgrados** es una aplicación inteligente basada en IA que utiliza técnicas avanzadas de procesamiento de lenguaje natural (NLP), recuperación aumentada por generación (RAG) y agentes inteligentes para proporcionar recomendaciones personalizadas de programas de posgrado a estudiantes prospectivos.

A continuación encontrarás un índice completo y detallado organizado por categorías, con descripciones extensas de cada documento para ayudarte a encontrar rápidamente la información que necesitas.

---

## 🚀 Inicio Rápido

### Documentación Principal

1. **[PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)** ⭐ **COMENZAR AQUÍ**
   - **Documentación general completa del proyecto** que sirve como punto de entrada principal
   - **Descripción detallada del propósito**: Sistema inteligente de recomendación de posgrados para la Universidad ICESI
   - **Arquitectura del sistema**: Visión general de la arquitectura modular basada en agentes inteligentes
   - **Descripción completa de diagramas C4**: Incluye explicaciones detalladas de todos los niveles (Contexto, Contenedores, Componentes) y diagramas de secuencia
   - **Componentes principales**: Descripción detallada de todos los agentes (Intelligent, Interviewer, Profiler, Recommender, RAG), herramientas y módulos de infraestructura
   - **Flujos de proceso**: Documentación completa de los flujos de autenticación, entrevista y recomendación
   - **Tecnologías utilizadas**: Stack tecnológico completo (Streamlit, Python, LangChain, OpenAI, ChromaDB, SQLite)
   - **Estructura del proyecto**: Organización completa de directorios y archivos
   - **Instalación y configuración**: Guías paso a paso para setup del proyecto
   - **Referencias a documentación adicional**: Enlaces a documentos específicos para profundizar

2. **[C4_ARCHITECTURE_DIAGRAMS.md](./C4_ARCHITECTURE_DIAGRAMS.md)**
   - **Guía completa para generar diagramas de arquitectura C4** siguiendo el modelo estándar de la industria
   - **Introducción al modelo C4**: Explicación de los 4 niveles de abstracción (Contexto, Contenedores, Componentes, Código)
   - **Ejemplos de código PlantUML**: Código completo y listo para usar para generar diagramas de contexto, contenedores y componentes
   - **Ejemplos de código Mermaid**: Diagramas de secuencia en formato Mermaid para flujos completos y autenticación
   - **Herramientas para generar diagramas**: Instrucciones detalladas de instalación y uso de PlantUML, Mermaid CLI, Structurizr y Draw.io
   - **Diagramas de secuencia**: Flujos completos documentados desde autenticación hasta recomendación
   - **Scripts de automatización**: Scripts bash y Python para generar y validar diagramas automáticamente
   - **Mejores prácticas**: Guías para mantener diagramas actualizados, nivel de detalle apropiado y nomenclatura consistente
   - **Referencias y recursos**: Enlaces a documentación oficial de herramientas y estándares

---

## 📐 Diagramas de Arquitectura

El proyecto incluye una suite completa de diagramas de arquitectura siguiendo el modelo C4, que proporciona diferentes niveles de abstracción para entender el sistema desde diferentes perspectivas. Estos diagramas son esenciales para comunicar la arquitectura a stakeholders técnicos y no técnicos.

### Archivos Fuente

Los archivos fuente de los diagramas están en `diagrams/` y están versionados en Git para facilitar el mantenimiento:

- **C4_Context.puml** - Diagrama de contexto (Nivel 1)
  - Muestra el sistema en su entorno completo
  - Identifica usuarios (Estudiantes, Administradores) y sistemas externos (OpenAI, SMTP, Google OAuth, LangSmith)
  - Ideal para presentaciones a stakeholders no técnicos
  - Formato: PlantUML con librería C4-PlantUML

- **C4_Container.puml** - Diagrama de contenedores (Nivel 2)
  - Descompone el sistema en contenedores principales de infraestructura
  - Incluye: Aplicación Web (Streamlit), Backend Python, SQLite, ChromaDB, Sistema de Archivos
  - Muestra relaciones y flujos de datos entre contenedores
  - Útil para arquitectos y desarrolladores senior

- **C4_Component.puml** - Diagrama de componentes (Nivel 3)
  - Muestra la estructura interna del Backend Python
  - Detalla todos los agentes (Intelligent, Interviewer, Profiler, Recommender, RAG)
  - Incluye herramientas (OTP Auth, Google Auth, Document Retriever, Query Processor, Chat Memory)
  - Muestra módulos de infraestructura (DB Model, Vector Functions, Tracing)
  - Esencial para desarrolladores del equipo

- **sequence_complete.mmd** - Flujo completo del sistema
  - Diagrama de secuencia que muestra el flujo completo desde autenticación hasta recomendación
  - Incluye todas las fases: Autenticación OTP, Entrevista, Análisis de Perfil, Generación de Recomendación
  - Muestra interacciones entre todos los componentes
  - Formato: Mermaid (renderizado automático en GitHub)

- **sequence_auth.mmd** - Flujo de autenticación OTP
  - Diagrama de secuencia detallado del proceso de autenticación
  - Incluye: Envío de código OTP, Verificación, Creación de sesión
  - Muestra casos de éxito y error
  - Formato: Mermaid

### Diagramas Generados

Los diagramas generados (PNG) están en `diagrams/generated/` y se actualizan cuando se regeneran los diagramas:

- `C4_Context.png` - Vista de contexto del sistema mostrando usuarios, sistema principal y sistemas externos con sus relaciones
- `C4_Container.png` - Contenedores principales (Streamlit, Backend, SQLite, ChromaDB, File System) y sus interacciones
- `C4_Component.png` - Componentes internos del backend mostrando agentes, herramientas y módulos de infraestructura
- `sequence_complete.png` - Flujo completo del sistema desde autenticación hasta recomendación con todas las interacciones
- `sequence_auth.png` - Flujo detallado de autenticación OTP con casos de éxito y error

### Generar Diagramas

El proyecto incluye un script automatizado para generar todos los diagramas:

```bash
# Opción 1: Script automatizado (recomendado)
# Desde la raíz del proyecto
./scripts/generate_diagrams.sh

# El script:
# - Verifica que PlantUML y Mermaid CLI estén instalados
# - Genera todos los diagramas PlantUML (.puml → .png)
# - Genera todos los diagramas Mermaid (.mmd → .png)
# - Guarda los resultados en diagrams/generated/

# Opción 2: Manual
cd DOCs/diagrams

# Generar diagramas PlantUML
plantuml *.puml -o generated

# Generar diagramas Mermaid
mmdc -i sequence_complete.mmd -o generated/sequence_complete.png
mmdc -i sequence_auth.mmd -o generated/sequence_auth.png
```

**Prerrequisitos para generar diagramas:**
- PlantUML: `brew install plantuml` (macOS) o `sudo apt-get install plantuml` (Linux)
- Mermaid CLI: `npm install -g @mermaid-js/mermaid-cli`

---

## 🏗️ Arquitectura y Diseño

Esta sección contiene documentación detallada sobre la arquitectura del sistema, el diseño de agentes inteligentes y los flujos de proceso. Es esencial para entender cómo funciona el sistema internamente.

### Documentos de Arquitectura

- **[AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md)**
  - **Arquitectura detallada de agentes**: Descripción completa de la arquitectura basada en agentes especializados
  - **Responsabilidades de cada agente**: 
    - Intelligent Agent (Coordinador): Punto de entrada, coordina todo el flujo
    - Orchestrator Agent: Analiza consultas y ejecuta herramientas (temperature 0.1 para reasoning preciso)
    - Response Agent: Genera respuestas amigables con personalidad "Luna" (temperature 0.7 para respuestas naturales)
    - RAG Agent: Herramienta interna para búsqueda en documentos, productos y gestión de tickets
  - **Flujos de comunicación entre agentes**: Cómo los agentes se comunican y coordinan
  - **Ventajas de la arquitectura**: Separación de responsabilidades, modularidad, flexibilidad, mantenibilidad
  - **Métricas de código**: Líneas de código por agente y responsabilidades
  - **Ejemplos de uso**: Código de ejemplo mostrando cómo usar los agentes

- **[AGENT_FUNCTIONALITIES.md](./AGENT_FUNCTIONALITIES.md)** ⭐ **NUEVO**
  - **Funcionalidades de los agentes desde perspectiva del sistema**: Descripción completa de qué hace cada agente sin entrar en código
  - **Funcionalidades detalladas por agente**:
    - **Intelligent Agent**: Gestión de autenticación, estados de sesión, enrutamiento inteligente, coordinación del flujo completo
    - **Interviewer Agent**: Inicio de entrevista, selección dinámica de preguntas, procesamiento de respuestas, construcción de perfil, gestión de progreso
    - **Profiler Agent**: Análisis del perfil, recuperación de programas, cálculo de compatibilidad, generación de rankings, análisis comparativo
    - **Recommender Agent**: Generación de recomendaciones personalizadas, explicación de recomendaciones, enriquecimiento con información, comparación de programas, próximos pasos
    - **RAG Agent**: Búsqueda semántica, búsqueda de información de programas, búsqueda de preguntas, generación de respuestas contextualizadas
  - **Flujo completo de funcionalidades**: Diagrama y descripción del flujo completo desde autenticación hasta recomendación
  - **Casos de uso por agente**: Ejemplos prácticos de cómo funciona cada agente en diferentes escenarios
  - **Resumen de funcionalidades**: Tabla resumen de entradas y salidas de cada agente
  - **Características clave**: Inteligencia contextual, personalización, modularidad, escalabilidad, trazabilidad

- **[INTELLIGENT_AGENT.md](./INTELLIGENT_AGENT.md)**
  - **Documentación del Intelligent Agent**: Documentación específica del agente coordinador principal
  - **Sistema de reasoning**: Cómo el agente usa LLM para analizar consultas y decidir qué herramientas usar
  - **Toma de decisiones**: Proceso de análisis de consultas, determinación de intención del usuario, selección de herramientas
  - **Arquitectura del sistema**: Diagramas y explicaciones del flujo de reasoning
  - **Prompts de reasoning**: Ejemplos de prompts utilizados para el análisis

### Flujos y Procesos

- **[PRODUCT_QUERY_FLOW.md](./PRODUCT_QUERY_FLOW.md)**
  - **Flujo de consultas de productos**: Cómo el sistema procesa consultas relacionadas con productos
  - **Procesamiento de queries**: Pipeline completo desde la recepción de la consulta hasta la respuesta
  - **Clasificación de consultas**: Cómo se identifican y categorizan diferentes tipos de consultas
  - **Integración con herramientas**: Cómo se utilizan las herramientas para responder consultas de productos

- **[TRACE_FLOW_EXAMPLE.md](./TRACE_FLOW_EXAMPLE.md)**
  - **Ejemplos de flujos de trazabilidad**: Ejemplos prácticos de cómo funciona el sistema de trazabilidad
  - **Casos de uso**: Diferentes escenarios donde se aplica la trazabilidad
  - **Flujos de trazas**: Cómo las trazas se generan, consolidan y almacenan
  - **Visualización**: Cómo interpretar las trazas generadas

---

## 🔧 Configuración y Setup

Esta sección contiene toda la documentación necesaria para configurar y desplegar el sistema, incluyendo configuración de Docker, autenticación y servicios externos.

### Configuración Inicial

- **[DOCKER_ENV_SETUP.md](./DOCKER_ENV_SETUP.md)**
  - **Configuración de variables de entorno para Docker**: Guía completa para configurar todas las variables de entorno necesarias en Docker
  - **Setup completo del entorno**: Pasos detallados desde la creación del archivo `.env` hasta la ejecución del contenedor
  - **Variables requeridas**: Lista completa de variables de entorno con descripciones (OpenAI, SMTP, Google OAuth, LangSmith)
  - **Verificación de configuración**: Comandos para verificar que las variables se están leyendo correctamente
  - **Reconstrucción de contenedores**: Instrucciones para aplicar cambios en variables de entorno
  - **Troubleshooting**: Soluciones a problemas comunes de configuración

- **[GOOGLE_AUTH_SETUP.md](./GOOGLE_AUTH_SETUP.md)**
  - **Configuración de autenticación con Google OAuth**: Guía completa para integrar autenticación con Google
  - **Pasos detallados de setup**: 
    - Creación de proyecto en Google Cloud Console
    - Configuración de OAuth 2.0 credentials
    - Configuración de redirect URIs
    - Obtención de Client ID y Client Secret
  - **Configuración en la aplicación**: Cómo configurar las variables de entorno y el código
  - **Pruebas de autenticación**: Cómo verificar que la autenticación funciona correctamente
  - **Consideraciones de seguridad**: Mejores prácticas de seguridad para OAuth

- **[INSTRUCCIONES_GOOGLE_AUTH.md](./INSTRUCCIONES_GOOGLE_AUTH.md)**
  - **Instrucciones paso a paso para Google Auth**: Tutorial detallado con capturas de pantalla y ejemplos
  - **Solución de problemas comunes**: 
    - Errores de redirect URI
    - Problemas de permisos
    - Errores de configuración de credenciales
    - Problemas de CORS
  - **FAQ**: Preguntas frecuentes y sus respuestas
  - **Enlaces útiles**: Referencias a documentación oficial de Google

- **[LANGSMITH_SETUP.md](./LANGSMITH_SETUP.md)**
  - **Configuración de LangSmith para trazabilidad**: Guía para integrar LangSmith (opcional) para observabilidad avanzada
  - **Integración opcional**: Cómo habilitar y configurar LangSmith sin afectar el funcionamiento básico
  - **Obtención de API key**: Pasos para crear cuenta y obtener credenciales
  - **Configuración de variables**: Variables de entorno necesarias para LangSmith
  - **Visualización de trazas**: Cómo acceder y usar el dashboard de LangSmith
  - **Beneficios**: Ventajas de usar LangSmith para debugging y monitoreo

### Solución de Problemas

- **[SOLUCION_ERROR_GOOGLE_AUTH.md](./SOLUCION_ERROR_GOOGLE_AUTH.md)**
  - **Soluciones a errores comunes de Google Auth**: Guía de troubleshooting específica
  - **Errores documentados**: 
    - "redirect_uri_mismatch"
    - "invalid_client"
    - "access_denied"
    - Problemas de configuración de OAuth consent screen
  - **Pasos de solución**: Soluciones paso a paso para cada error
  - **Verificación**: Cómo verificar que el problema está resuelto

---

## 🛠️ Componentes y Herramientas

Esta sección documenta los componentes específicos del sistema, sus funcionalidades, uso y casos de uso. Incluye documentación detallada del sistema de trazabilidad que es fundamental para debugging y monitoreo.

### Documentación de Componentes

- **[TICKET_SYSTEM.md](./TICKET_SYSTEM.md)**
  - **Sistema de gestión de tickets**: Documentación completa del sistema de tickets integrado
  - **Funcionalidades**: 
    - Creación de tickets para devoluciones, compras y consultas
    - Seguimiento de estado de tickets
    - Asignación y gestión de tickets
  - **Uso**: Cómo crear, consultar y gestionar tickets desde el sistema
  - **Integración con agentes**: Cómo los agentes utilizan el sistema de tickets
  - **API y métodos**: Documentación de métodos disponibles para interactuar con tickets

- **[USAGE_PRODUCT_CHECKER.md](./USAGE_PRODUCT_CHECKER.md)**
  - **Uso del Product Checker**: Guía completa de la herramienta de verificación de productos
  - **Funcionalidades**: 
    - Verificación de disponibilidad de productos
    - Consulta de precios y especificaciones
    - Búsqueda de productos por categoría
  - **Ejemplos y casos de uso**: Ejemplos prácticos de cómo usar el Product Checker
  - **Integración**: Cómo se integra con otros componentes del sistema
  - **Formato de respuestas**: Estructura de datos retornados

### Sistema de Trazabilidad

El sistema incluye un sistema completo de trazabilidad que permite monitorear y debuggear todas las operaciones del sistema. La documentación está organizada por versiones y mejoras.

- **[TRACING_SYSTEM.md](./TRACING_SYSTEM.md)**
  - **Sistema de trazabilidad básico**: Documentación de la versión inicial del sistema de trazabilidad
  - **Logging y monitoreo**: Cómo se registran las operaciones y eventos del sistema
  - **Estructura de trazas**: Formato y estructura de las trazas generadas
  - **Niveles de logging**: Diferentes niveles (INFO, WARNING, ERROR) y cuándo usarlos
  - **Almacenamiento**: Dónde y cómo se almacenan las trazas

- **[TRACING_SYSTEM_V2.md](./TRACING_SYSTEM_V2.md)**
  - **Versión mejorada del sistema de trazabilidad**: Documentación de mejoras y nuevas funcionalidades
  - **Nuevas funcionalidades**: 
    - Consolidación de trazas
    - Mejor estructuración de datos
    - Integración mejorada con LangSmith
  - **Mejoras de rendimiento**: Optimizaciones implementadas
  - **Migración**: Cómo migrar desde la versión anterior

- **[TRACING_COVERAGE.md](./TRACING_COVERAGE.md)**
  - **Cobertura de trazabilidad**: Documentación de qué componentes están instrumentados
  - **Componentes instrumentados**: Lista completa de agentes, herramientas y módulos con trazabilidad
  - **Cobertura por módulo**: Detalle de qué operaciones se trazan en cada módulo
  - **Gaps de cobertura**: Componentes que aún no tienen trazabilidad completa
  - **Plan de cobertura**: Roadmap para mejorar la cobertura

- **[TOOLS_TRACING.md](./TOOLS_TRACING.md)**
  - **Trazabilidad de herramientas**: Documentación específica de cómo se trazan las herramientas
  - **Instrumentación de componentes**: Cómo se instrumentan las herramientas para generar trazas
  - **Decoradores y utilidades**: Utilidades disponibles para agregar trazabilidad fácilmente
  - **Ejemplos de instrumentación**: Código de ejemplo mostrando cómo instrumentar nuevas herramientas
  - **Mejores prácticas**: Guías para instrumentar correctamente

- **[LANGSMITH_UNIFIED_TRACE.md](./LANGSMITH_UNIFIED_TRACE.md)**
  - **Trazabilidad unificada con LangSmith**: Documentación de la integración avanzada con LangSmith
  - **Integración avanzada**: Cómo se integran las trazas locales con LangSmith
  - **Sincronización**: Cómo se sincronizan las trazas entre sistemas
  - **Dashboard**: Cómo usar el dashboard de LangSmith para visualizar trazas
  - **Configuración avanzada**: Opciones de configuración avanzadas

- **[UNIFIED_TRACE_SOLUTION.md](./UNIFIED_TRACE_SOLUTION.md)**
  - **Solución de trazabilidad unificada**: Arquitectura y diseño de la solución unificada
  - **Arquitectura y diseño**: Diseño arquitectónico del sistema de trazabilidad
  - **Flujo de datos**: Cómo fluyen las trazas a través del sistema
  - **Componentes principales**: Componentes clave del sistema de trazabilidad
  - **Escalabilidad**: Consideraciones de escalabilidad y rendimiento

- **[TRACE_CONSOLIDATION_FIX.md](./TRACE_CONSOLIDATION_FIX.md)**
  - **Corrección de consolidación de trazas**: Documentación de correcciones específicas
  - **Mejoras implementadas**: Detalles de las mejoras realizadas en la consolidación
  - **Problemas resueltos**: Problemas específicos que se corrigieron
  - **Testing**: Cómo se verificaron las correcciones
  - **Impacto**: Impacto de las correcciones en el sistema

- **[TRACE_FIX_SUMMARY.md](./TRACE_FIX_SUMMARY.md)**
  - **Resumen de correcciones de trazabilidad**: Resumen ejecutivo de todas las correcciones
  - **Cambios realizados**: Lista completa de cambios y mejoras
  - **Changelog**: Historial de cambios en el sistema de trazabilidad
  - **Estado actual**: Estado actual del sistema después de las correcciones
  - **Próximos pasos**: Mejoras planificadas para el futuro

---

## 📖 Guías y Referencias

Esta sección contiene guías de referencia y documentación sobre la estructura y organización del proyecto.

### Estructura del Proyecto

- **[README_STRUCTURE.md](./README_STRUCTURE.md)**
  - **Estructura de directorios**: Documentación completa de la organización de directorios del proyecto
  - **Organización del código**: 
    - Explicación de cada directorio principal (`src/`, `static/`, `DOCs/`, etc.)
    - Propósito de cada subdirectorio
    - Convenciones de nombres de archivos
  - **Arquitectura de directorios**: Cómo la estructura refleja la arquitectura del sistema
  - **Mejores prácticas**: Guías para mantener la organización del código
  - **Navegación**: Cómo encontrar rápidamente archivos específicos

---

## 📊 Resumen de Documentación

### Por Categoría

| Categoría | Documentos | Descripción |
|-----------|------------|-------------|
| **General** | PROJECT_OVERVIEW.md | Visión general completa del proyecto, incluyendo propósito, arquitectura, componentes, flujos, tecnologías, estructura e instalación. Incluye descripción detallada de todos los diagramas C4. |
| **Arquitectura** | C4_ARCHITECTURE_DIAGRAMS.md, AGENT_ARCHITECTURE.md, INTELLIGENT_AGENT.md | Diseño y estructura del sistema. Incluye guía completa de diagramas C4, arquitectura de agentes, responsabilidades y flujos de comunicación. |
| **Configuración** | DOCKER_ENV_SETUP.md, GOOGLE_AUTH_SETUP.md, INSTRUCCIONES_GOOGLE_AUTH.md, LANGSMITH_SETUP.md, SOLUCION_ERROR_GOOGLE_AUTH.md | Setup y configuración completa del entorno, Docker, autenticación Google OAuth, LangSmith y solución de problemas comunes. |
| **Componentes** | TICKET_SYSTEM.md, USAGE_PRODUCT_CHECKER.md, PRODUCT_QUERY_FLOW.md | Funcionalidades específicas de componentes: sistema de tickets, verificación de productos, y flujos de procesamiento de consultas. |
| **Trazabilidad** | TRACING_SYSTEM.md, TRACING_SYSTEM_V2.md, TRACING_COVERAGE.md, TOOLS_TRACING.md, LANGSMITH_UNIFIED_TRACE.md, UNIFIED_TRACE_SOLUTION.md, TRACE_CONSOLIDATION_FIX.md, TRACE_FIX_SUMMARY.md, TRACE_FLOW_EXAMPLE.md | Sistema completo de logging y monitoreo. Incluye versiones del sistema, cobertura, instrumentación, integración con LangSmith, y documentación de correcciones y mejoras. |

### Por Prioridad de Lectura

**Ruta de aprendizaje recomendada para nuevos desarrolladores:**

1. **Primero**: [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) 
   - **Por qué**: Proporciona una visión general completa del proyecto
   - **Qué aprenderás**: Propósito del sistema, arquitectura general, componentes principales, flujos de proceso, tecnologías utilizadas
   - **Tiempo estimado**: 30-45 minutos

2. **Segundo**: [C4_ARCHITECTURE_DIAGRAMS.md](./C4_ARCHITECTURE_DIAGRAMS.md)
   - **Por qué**: Entender la arquitectura visual del sistema
   - **Qué aprenderás**: Modelo C4, cómo leer diagramas de arquitectura, herramientas para generar diagramas
   - **Tiempo estimado**: 20-30 minutos

3. **Tercero**: [AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md)
   - **Por qué**: Entender cómo funcionan los agentes inteligentes que son el corazón del sistema
   - **Qué aprenderás**: Responsabilidades de cada agente, flujos de comunicación, arquitectura de agentes
   - **Tiempo estimado**: 25-35 minutos

4. **Cuarto**: Documentos de configuración según necesidad
   - **DOCKER_ENV_SETUP.md**: Si vas a trabajar con Docker
   - **GOOGLE_AUTH_SETUP.md**: Si necesitas configurar autenticación
   - **LANGSMITH_SETUP.md**: Si quieres habilitar trazabilidad avanzada
   - **Tiempo estimado**: Variable según necesidad

---

## 🔍 Búsqueda Rápida

### ¿Qué necesitas?

Esta sección te ayuda a encontrar rápidamente la documentación que necesitas según tu objetivo o problema específico.

#### Entender el Sistema

- **Entender el proyecto completo** → [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)
  - Visión general, arquitectura, componentes, flujos, tecnologías
  - Incluye descripción detallada de todos los diagramas C4

- **Ver diagramas de arquitectura** → [diagrams/generated/](./diagrams/generated/)
  - Diagramas PNG listos para visualizar
  - Contexto, Contenedores, Componentes, Secuencias

- **Entender la arquitectura visual** → [C4_ARCHITECTURE_DIAGRAMS.md](./C4_ARCHITECTURE_DIAGRAMS.md)
  - Guía completa para generar y entender diagramas C4
  - Código fuente de todos los diagramas

- **Entender agentes** → [AGENT_ARCHITECTURE.md](./AGENT_ARCHITECTURE.md)
  - Arquitectura de agentes, responsabilidades, flujos de comunicación

#### Configuración y Setup

- **Configurar Docker** → [DOCKER_ENV_SETUP.md](./DOCKER_ENV_SETUP.md)
  - Variables de entorno, setup completo, verificación

- **Configurar Google Auth** → [GOOGLE_AUTH_SETUP.md](./GOOGLE_AUTH_SETUP.md)
  - Setup completo de OAuth, credenciales, configuración

- **Configurar LangSmith** → [LANGSMITH_SETUP.md](./LANGSMITH_SETUP.md)
  - Integración opcional para trazabilidad avanzada

#### Desarrollo y Componentes

- **Generar diagramas** → [C4_ARCHITECTURE_DIAGRAMS.md](./C4_ARCHITECTURE_DIAGRAMS.md)
  - Scripts automatizados y comandos manuales

- **Entender sistema de tickets** → [TICKET_SYSTEM.md](./TICKET_SYSTEM.md)
  - Funcionalidades, uso, integración

- **Usar Product Checker** → [USAGE_PRODUCT_CHECKER.md](./USAGE_PRODUCT_CHECKER.md)
  - Ejemplos, casos de uso, integración

- **Entender trazabilidad** → [TRACING_SYSTEM_V2.md](./TRACING_SYSTEM_V2.md)
  - Sistema de logging y monitoreo mejorado

#### Solución de Problemas

- **Errores de Google Auth** → [SOLUCION_ERROR_GOOGLE_AUTH.md](./SOLUCION_ERROR_GOOGLE_AUTH.md)
  - Soluciones a errores comunes de autenticación

- **Problemas de configuración** → [DOCKER_ENV_SETUP.md](./DOCKER_ENV_SETUP.md)
  - Troubleshooting de variables de entorno

- **Problemas de trazabilidad** → [TRACE_FIX_SUMMARY.md](./TRACE_FIX_SUMMARY.md)
  - Resumen de correcciones y soluciones

---

## 📝 Notas Importantes

### Mantenimiento de Diagramas

- **Archivos fuente**: Todos los diagramas se generan desde archivos fuente (`.puml` para PlantUML, `.mmd` para Mermaid)
- **Versionado**: Los archivos fuente están versionados en Git, los diagramas generados pueden estar en `.gitignore` si son muy grandes
- **Actualización**: Cuando cambie la arquitectura, actualiza los archivos fuente y regenera los diagramas
- **Ubicación**: Los diagramas generados están en `diagrams/generated/`

### Mantenimiento de Documentación

- **Actualización regular**: La documentación se actualiza regularmente para reflejar cambios en el sistema
- **Consistencia**: Se mantiene consistencia en formato y estructura entre documentos
- **Enlaces**: Todos los enlaces internos se verifican regularmente

### Contribuir

- **Estructura del proyecto**: Para contribuir, consulta [README_STRUCTURE.md](./README_STRUCTURE.md) para entender la organización
- **Convenciones**: Sigue las convenciones establecidas en los documentos existentes
- **Diagramas**: Al agregar nuevas funcionalidades, actualiza los diagramas correspondientes
- **Documentación**: Documenta nuevas funcionalidades siguiendo el formato de documentos existentes

### Recursos Adicionales

- **Código fuente**: El código fuente está en `src/` con estructura modular
- **Scripts**: Scripts de utilidad están en `scripts/` incluyendo generación de diagramas
- **Ejemplos**: Ejemplos de código y uso están en los documentos correspondientes
- **FAQ**: Preguntas frecuentes están documentadas en los documentos de configuración

---

## 📞 Contacto y Soporte

Para preguntas, sugerencias o problemas con la documentación:

- **Issues**: Abre un issue en el repositorio del proyecto
- **Pull Requests**: Las contribuciones son bienvenidas
- **Actualizaciones**: Revisa regularmente este README para nuevas actualizaciones

---

**Última actualización**: 2024  
**Mantenedor**: Equipo de Desarrollo ICESI  
**Versión de documentación**: 1.0


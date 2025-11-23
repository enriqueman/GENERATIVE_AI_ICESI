# 🎓 Sistema de Recomendación de Posgrados - Universidad ICESI

**Sistema Inteligente de Recomendación basado en IA**

Este proyecto implementa un sistema inteligente de recomendación de posgrados para la Universidad ICESI. El sistema utiliza técnicas avanzadas de procesamiento de lenguaje natural (NLP), recuperación aumentada por generación (RAG) y agentes inteligentes para proporcionar recomendaciones personalizadas a estudiantes prospectivos.

## 📚 Documentación General

Para una visión completa del proyecto, incluyendo arquitectura, diagramas C4 y componentes principales, consulta:

👉 **[PROJECT_OVERVIEW.md](./DOCs/PROJECT_OVERVIEW.md)** - Documentación general del proyecto

### Diagramas de Arquitectura

El proyecto incluye diagramas de arquitectura C4 completos:

- 📊 **[C4_ARCHITECTURE_DIAGRAMS.md](./DOCs/C4_ARCHITECTURE_DIAGRAMS.md)** - Guía completa para generar diagramas C4
- 📐 **[Diagramas Generados](./DOCs/diagrams/generated/)** - Diagramas en formato PNG

Para generar los diagramas:
```bash
./scripts/generate_diagrams.sh
```

---

## 🌿 EcoMarket RAG System (Legacy)

**Nota**: Este proyecto evolucionó desde un sistema RAG para EcoMarket hacia el Sistema de Recomendación de Posgrados ICESI. La siguiente información corresponde a la versión anterior del sistema.

## 👥 Integrantes

- Enrique Manzano

## 🎯 Objetivos del Proyecto

- Integrar un modelo de lenguaje con recuperación semántica para responder consultas reales de clientes
- Utilizar documentos internos (TXT, Excel, PDF) como base de conocimiento
- Evaluar la precisión, transparencia y ética del sistema en un entorno educativo
- Implementar una interfaz web moderna y fácil de usar

## 🏗️ Arquitectura del Sistema

```
Frontend (Streamlit) → Backend (Python) → ChromaDB (Vectores) + SQLite (Metadatos)
                                    ↓
                              OpenAI API (Embeddings + LLM)
```

## 🔧 Componentes del Sistema

| **Componente** | **Herramienta elegida** | **Justificación** |
|----------------|-------------------------|-------------------|
| **Embeddings** | OpenAI Embeddings (text-embedding-ada-002) | Alta calidad multilingüe, 1536 dimensiones |
| **Vector DB** | ChromaDB | Persistencia automática, integración con LangChain |
| **LLM** | GPT-4o-mini | Respuestas precisas, configuración optimizada |
| **Framework** | LangChain | Modular, flexible y orientado a sistemas RAG |
| **Frontend** | Streamlit | Interfaz web moderna y responsiva |
| **Backend** | Python + FastAPI | API REST robusta y escalable |
| **Base de Datos** | SQLite | Metadatos y gestión de documentos |
| **Despliegue** | Docker + Nginx | Contenedorización y proxy reverso |

## 📚 Documentos Utilizados

| **Tipo** | **Archivo** | **Contenido** |
|----------|-------------|---------------|
| TXT | `politica_devoluciones.txt` | Normativa de reembolsos y condiciones |
| Excel | `Inventario_Sostenible.xlsx` | Productos, stock y precios |
| TXT | `preguntas_frecuentes.txt` | Preguntas frecuentes de clientes |

## 🧠 Estrategia de Chunking Adaptativa

- **Datos estructurados** (Excel, CSV): `chunk_size=300`, `chunk_overlap=30`
- **Texto narrativo** (TXT, PDF): `chunk_size=500`, `chunk_overlap=50`

## 🚀 Instalación y Ejecución

### Prerrequisitos

- Docker y Docker Compose
- Git
- API Key de OpenAI

### 1. Clonar el Repositorio

```bash
git clone <repository-url>
cd GENERATIVE_AI_ICESI
```

### 2. Configurar Variables de Entorno

```bash
cp env.example .env
```

Editar el archivo `.env` y agregar tu API key de OpenAI:

```env
OPENAI_API_KEY=tu_api_key_aqui
DOCKER_CONTAINER=true
```

### 3. Ejecutar con Docker (Recomendado)

```bash
# Construir y ejecutar todos los servicios
docker-compose up --build

# O ejecutar en segundo plano
docker-compose up -d --build
```

La aplicación estará disponible en: `http://localhost:8501`

### 4. Ejecutar Localmente (Desarrollo)

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
export OPENAI_API_KEY=tu_api_key_aqui

# Inicializar la aplicación
cd src && python init_app.py

# Ejecutar la aplicación
cd src && streamlit run app.py

# O usar el script wrapper desde la raíz
python run_app.py
```

## 🎮 Uso del Sistema

### Acceso a la Aplicación

1. **Chat Público**: `http://localhost:8501`
   - Interfaz principal para consultas de clientes
   - Respuestas automáticas basadas en documentos

2. **Panel de Administración**: `http://localhost:8501/admin`
   - Usuario: `admin`
   - Contraseña: `admin123`
   - Gestión de documentos y configuración

### Ejemplos de Consultas

- "¿Cuál es la política de devoluciones de EcoMarket?"
- "¿Qué productos no aplican para devoluciones?"
- "¿Tienen disponibilidad del Cargador Solar Portátil?"
- "¿Cuál es el precio del Cargador Solar Portátil?"
- "¿Cuál es el teléfono para devoluciones?"
- "¿Cuál es el WhatsApp de soporte?"

## 🔧 Configuración Avanzada

### Personalizar el Sistema

1. **Agregar Documentos**: Coloca archivos en `static/sample_documents/`
2. **Modificar Prompts**: Edita `utils/vector_functions.py`
3. **Cambiar Temas**: Modifica `config/theme_config.py`
4. **Ajustar Chunking**: Configura `create_optimal_splitter()`

### Variables de Entorno Disponibles

```env
OPENAI_API_KEY=tu_api_key_openai
DOCKER_CONTAINER=true
DB_PATH=doc_sage.sqlite
PERSIST_DIRECTORY=./static/persist
```

## 🧪 Pruebas y Debugging

### Habilitar Logging Detallado

```python
# En views/public_chat.py
response = generate_answer_from_context(retriever, prompt, enable_logging=True)
```

### Verificar Estado del Sistema

```bash
# Verificar contenedores
docker-compose ps

# Ver logs
docker-compose logs -f

# Verificar base de datos
sqlite3 doc_sage.sqlite ".tables"
```

## 📊 Características Técnicas

### Optimizaciones Implementadas

- **Chunking Adaptativo**: Ajusta parámetros según tipo de contenido
- **Prompts Especializados**: Evita alucinaciones del LLM
- **Configuración de Base de Datos**: WAL mode para mejor concurrencia
- **Manejo de Errores**: Reintentos automáticos y logging detallado
- **Detección Inteligente**: Identifica consultas de contacto automáticamente

### Agente RAG

- **Arquitectura Modular**: El agente está separado en `src/agents/` para mejor organización
- **Singleton Pattern**: Una única instancia del agente se comparte en toda la aplicación
- **Manejo de Estado**: Gestiona automáticamente la inicialización y disponibilidad del sistema
- **Respuestas Inteligentes**: Maneja errores y respuestas de respaldo automáticamente
- **Sistema de Herramientas**: Herramientas modulares en `src/tools/` que el agente puede usar

#### Herramientas Disponibles

- **DocumentRetriever**: Recupera documentos relevantes de la base vectorial
- **QueryProcessor**: Clasifica y procesa consultas del usuario
  - Clasificación por categoría (producto, precio, contacto, etc.)
  - Detección de consultas de lista vs consultas específicas
  - Extracción de entidades relevantes
  - Generación de variaciones de consultas

### Sistema de Trazabilidad

- **Logging Automático**: Todas las operaciones RAG se registran automáticamente
- **Panel de Trazabilidad**: Visualiza logs en tiempo real en el panel de administración
- **Métricas y Estadísticas**: Tasa de éxito, operaciones por tipo, tiempos de procesamiento
- **Integración con LangSmith**: Opcional, para trazabilidad avanzada en la nube

#### Configurar LangSmith (Opcional)

```bash
# En tu archivo .env
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=tu_api_key_de_langsmith
LANGCHAIN_PROJECT=ecomarket-rag-system
```

### Configuración del LLM

```python
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.1,  # Respuestas más precisas
    max_tokens=500,   # Respuestas concisas
)
```

## 🛠️ Estructura del Proyecto

```
GENERATIVE_AI_ICESI/
├── 📁 src/                    # Código fuente principal
│   ├── app.py                # Aplicación principal Streamlit
│   ├── init_app.py           # Script de inicialización
│   ├── agents/               # Agentes RAG (lógica del agente)
│   ├── tools/                # 🆕 Herramientas del agente
│   ├── config/               # Configuración y temas
│   ├── controllers/          # Controladores (auth, etc.)
│   ├── models/               # Modelos de datos (SQLite)
│   ├── utils/                # Utilidades (RAG, temas, tracing)
│   ├── views/                # Vistas de la aplicación
│   └── pages/                # Páginas de Streamlit
│
├── 📁 static/                 # Archivos estáticos
│   ├── sample_documents/     # Documentos de muestra
│   └── persist/              # Base de datos vectorial
│
├── 📁 data/                   # Directorio de datos
├── 📁 fase1 y fase 2/        # Documentación del proyecto
├── docker-compose.yml        # Configuración Docker
├── Dockerfile                # Imagen Docker
├── nginx.conf               # Configuración Nginx
├── requirements.txt         # Dependencias Python
└── README.md                # Este archivo
```

## 🚨 Solución de Problemas

### Error: "database is locked"
```bash
# Reiniciar la aplicación
docker-compose restart
```

### Error: "OPENAI_API_KEY not found"
```bash
# Verificar variables de entorno
echo $OPENAI_API_KEY
# O en Docker
docker-compose exec app env | grep OPENAI
```

### Documentos no se cargan
```bash
# Verificar permisos de archivos
ls -la static/sample_documents/
# Reinicializar colección
docker-compose exec app python init_app.py
```

## 📈 Consideraciones Éticas

- Se prioriza la transparencia en las fuentes utilizadas
- El sistema no reemplaza la supervisión humana
- Se evita la generación de respuestas fuera del contexto documental
- Implementa prompts estrictos para evitar alucinaciones
- Logging detallado para auditoría y debugging

## 📞 Soporte

Para problemas técnicos o consultas sobre el sistema, contacta al equipo de desarrollo o revisa los logs de la aplicación.
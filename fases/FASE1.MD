# Fase 1: Diseño de la Arquitectura del Agente

## Introducción al Diseño Arquitectónico

Diseñamos la arquitectura del sistema multi-agente de EcoMarket mediante un proceso meticuloso de conceptualización y justificación que transforma la visión de un chatbot RAG simple en un sistema inteligente capaz de razonar, decidir y ejecutar acciones específicas. Esta fase representa el fundamento conceptual donde establecimos las bases arquitectónicas que guiarían toda la implementación subsecuente, definiendo no solo qué herramientas el sistema requeriría sino también por qué cada decisión arquitectónica contribuiría al objetivo general de crear un agente conversacional verdaderamente funcional.

La conceptualización que desarrollamos comenzó identificando las limitaciones fundamentales del sistema original: un chatbot que solo podía responder preguntas mediante recuperación de documentos pero carecía completamente de capacidades de acción o razonamiento contextual. A partir de este análisis de brechas, establecimos principios arquitectónicos claros donde separaríamos razonamiento de ejecución, donde cada herramienta tendría responsabilidades específicas y claramente definidas, y donde el sistema mantendría trazabilidad completa de todas las operaciones para debugging y optimización.

## Definición de las Herramientas del Sistema

### Conceptualización de Capacidades Requeridas

Antes de implementar código, realizamos análisis exhaustivo de los requisitos funcionales del sistema, identificando las capacidades fundamentales que el agente necesitaría para servir efectivamente como asistente de atención al cliente para EcoMarket. El análisis que llevamos a cabo identificó cinco categorías principales de funcionalidad que el sistema requeriría: recuperación de información documental, verificación de inventario de productos, gestión de casos de clientes mediante tickets, procesamiento inteligente de consultas de usuario, y mantenimiento de contexto conversacional.

Para cada una de estas capacidades que identificamos, diseñamos herramientas especializadas que encapsulan la lógica específica del dominio. Esta aproximación de diseño que adoptamos sigue principios de responsabilidad única donde cada herramienta resuelve un problema claramente definido, facilita testing y mantenimiento independiente de componentes, y permite extensión del sistema mediante agregar nuevas herramientas sin modificar código existente.

### DocumentRetriever: Capacidades de Recuperación RAG

Diseñamos la herramienta DocumentRetriever como componente fundamental que proporciona al sistema acceso al conocimiento corporativo almacenado en documentos internos. Esta herramienta que desarrollamos encapsula toda la lógica de búsqueda semántica en ChromaDB, manejo de embeddings generados por OpenAI, y recuperación de documentos relevantes basándose en similitud semántica en lugar de coincidencia literal de términos.

La interfaz que definimos para esta herramienta recibe simplemente una consulta en texto libre del usuario y retorna una lista estructurada de documentos relevantes, cada uno con metadata completa incluyendo fuente del documento, tipo de archivo, contenido completo, y score de relevancia semántica. El diseño de esta herramienta que establecimos abstrae completamente los detalles de implementación de ChromaDB y embeddings, permitiendo que el agente use capacidades RAG sin necesidad de entender los mecanismos internos de búsqueda vectorial.

La implementación que concebimos utiliza búsqueda semántica para encontrar documentos relevantes basándose en significado en lugar de keywords específicas, filtra resultados según tipo de contenido diferenciando entre documentos de inventario y documentación corporativa general, y limita resultados a configurable de documentos para balancear entre completitud de información y concisión de respuesta. Esta aproximación que diseñamos permite al sistema proporcionar información contextualmente relevante sin abrumar al usuario con exceso de información recuperada.

### ProductChecker: Verificación de Inventario

Desarrollamos la herramienta ProductChecker para proporcionar capacidades especializadas de búsqueda en el inventario de productos de EcoMarket, permitiendo al sistema verificar disponibilidad, precios, y categorías de productos específicos. La complejidad de esta herramienta que implementamos radica en su capacidad para manejar múltiples tipos de consultas: búsqueda de producto individual, listado de múltiples productos simultáneamente, búsqueda por categoría completa, búsqueda por rango de precio, y obtención de catálogos completos.

La interfaz que diseñamos para ProductChecker acepta parámetros flexibles que permiten refinar búsquedas con filtros adicionales como categoría específica, rangos de precio, y umbrales de similitud configurable. Esta flexibilidad que incorporamos permite al sistema adaptarse a diferentes tipos de consultas de usuario, desde "¿tienen botellas?" hasta "muéstrame productos de hogar entre $20 y $30". El retorno que estructuramos incluye no solo información de producto sino también matches alternativos cuando la búsqueda exacta no encuentra resultados, scores de similitud para transparencia, y detalles completos de cada producto encontrado.

La implementación que concebimos utiliza embeddings semánticos para encontrar productos similares incluso cuando el nombre exacto difiere del inventario, convierte scores de distancia a escalas de similitud normalizadas para interpretación consistente, y parsea automáticamente información de productos desde metadata de documentos Excel incluso cuando la estructura de datos no es perfecta. Esta robustez que diseñamos permite al sistema proporcionar resultados útiles incluso con datos incompletos o inconsistentes en el inventario.

### TicketManager: Gestión de Casos de Clientes

Diseñamos TicketManager como sistema integral para gestión de casos de clientes, proporcionando funcionalidad para crear, consultar y gestionar tickets de devolución, compra, seguimiento, facturas y quejas. La arquitectura que establecimos para esta herramienta genera identificadores únicos automáticamente, persiste información completa en SQLite con todos los metadatos relevantes, y proporciona trazabilidad completa de cada caso desde creación hasta resolución.

La complejidad de TicketManager que implementamos radica en su capacidad para manejar diferentes tipos de tickets con parámetros distintos según el contexto. Para tickets de devolución, la herramienta requiere producto específico, número de factura, y motivo de devolución. Para tickets de compra, necesita información de productos adquiridos y total de transacción. Para guías de seguimiento, integra información de transportistas y números de tracking. Esta variedad que diseñamos requiere que cada función de ticket maneje validación específica según sus requisitos.

La interfaz que definimos retorna información estructurada sobre el éxito o fallo de cada operación, incluyendo número de ticket generado, mensajes de confirmación para el usuario, e instrucciones claras sobre siguientes pasos. El sistema que establecimos incluye generación automática de etiquetas de devolución, consulta de estado de tickets existentes, y extracción de información de facturas históricas. Esta amplitud de funcionalidad que incorporamos posiciona TicketManager como herramienta central del sistema de atención al cliente de EcoMarket.

### QueryProcessor: Análisis de Intenciones

Desarrollamos QueryProcessor para proporcionar análisis automático de consultas de usuario, clasificando intenciones según categoría, urgencia, y objetivo específico del usuario. La herramienta que implementamos utiliza detección de keywords para categorizar consultas como relacionadas con productos, precios, información de contacto, devoluciones, envíos, o consultas generales. Esta clasificación que establecimos permite al sistema enrutar consultas a las herramientas apropiadas sin requerir razonamiento de LLM para cada decisión simple.

La capacidad que diseñamos para QueryProcessor incluye detección automática de si el usuario solicita una lista de elementos versus información específica sobre un elemento individual, análisis de urgencia basado en lenguaje utilizado, e identificación de intención subyacente como comprar, rastrear pedidos, solicitar soporte, o buscar información general. Esta sofisticación que incorporamos permite al sistema anticipar necesidades del usuario y preparar respuestas más útiles y contextualmente relevantes.

La implementación que concebimos también genera variaciones automáticas de consultas para mejorar recuperación de información, extrae entidades relevantes como productos y números de la consulta del usuario, y mantiene histórico de consultas para análisis de patrones. Esta funcionalidad adicional que desarrollamos extiende las capacidades del sistema más allá de simple clasificación, habilitando mejoras progresivas en comprensión de consultas basadas en aprendizaje de interacciones previas.

### ChatMemory: Gestión de Contexto Conversacional

Diseñamos ChatMemory como sistema de gestión de memoria temporal que permite al sistema mantener contexto de conversación sin persistencia permanente de datos sensibles. La arquitectura que establecimos utiliza patrón de almacenamiento con TTL de cinco minutos, donde información se elimina automáticamente después de período de inactividad, balanceando necesidad de contexto conversacional con protección de privacidad del usuario.

La herramienta que implementamos extrae automáticamente información personal de consultas de usuario utilizando expresiones regulares optimizadas que reconocen patrones comunes de email, teléfono y nombres. Esta extracción automática que desarrollamos almacena información en base de datos SQLite con asociación a session_id, permitiendo que consultas subsiguientes del mismo usuario se enriquezcan automáticamente con contexto previo sin requerir que el usuario repita información.

La funcionalidad que concebimos incluye recuperación selectiva de información específica o conjunto completo de datos de sesión, eliminación de memoria individual o completa de sesión, y construcción de contexto formateado para incluir en consultas enriquecidas enviadas a agentes. Este mecanismo que diseñamos permite al sistema mantener conversaciones coherentes y naturales donde usuario no necesita repetir información previamente proporcionada, mejorando significativamente la experiencia de usuario.

## Planificación del Flujo de Trabajo: Proceso de Devolución

### Diseño del Flujo de Decisión del Agente

Diseñamos el flujo de trabajo para el proceso de devolución como caso de uso representativo que demuestra las capacidades del sistema multi-agente y la coordinación entre herramientas. El flujo que concebimos ilustra cómo el sistema maneja consultas complejas que requieren razonamiento, ejecución de acciones, y gestión de información multi-paso donde el usuario proporciona datos progresivamente en lugar de una sola consulta completa.

![Diagrama de Flujo del Proceso de Devolución](../data/devolucion.svg)

El diagrama visual que presentamos muestra el flujo completo desde entrada del usuario hasta generación de respuesta final, ilustrando cada punto de decisión donde el agente evalúa qué acción tomar y qué herramientas invocar. Este flujo que diseñamos no es simplemente secuencial sino incluye bucles de retroalimentación donde el sistema detecta información faltante y solicita datos adicionales antes de proceder con acciones irrevocables.

### Análisis del Proceso Detallado

Trazamos el proceso de devolución como secuencia de diez pasos que cada consulta atraviesa sistemáticamente. El proceso que diseñamos comienza con entrada del usuario donde sistema recibe consulta libre en lenguaje natural, continúa con gestión de memoria de sesión donde información relevante se extrae y almacena temporalmente, progresa a través de análisis de intención realizado por OrchestratorAgent, ejecuta herramientas apropiadas según decisión del agente, y culmina con generación de respuesta amigable por ResponseAgent.

En cada paso del flujo que planificamos, el sistema toma decisiones específicas que afectan comportamiento subsiguiente. Cuando OrchestratorAgent detecta que falta información crítica para ejecutar acción requerida, el sistema que diseñamos genera solicitud estructurada de datos faltantes y espera respuesta del usuario antes de continuar. Esta capacidad de gestión multi-paso que incorporamos permite manejar conversaciones naturales donde usuarios no proporcionan toda la información necesaria inmediatamente.

El proceso que estructuramos incluye puntos de validación en múltiples niveles: extracción de información valida formato de datos antes de almacenar en memoria, análisis de intención valida que decisiones del agente son razonables, y ejecución de herramientas valida que parámetros son correctos antes de invocar. Esta arquitectura defensiva que establecimos previene ejecución de acciones basadas en información incorrecta o incompleta, protegiendo integridad del sistema y confianza del usuario.

### Herramientas Invocadas en el Proceso

Identificamos ocho herramientas específicas que el sistema invoca durante procesamiento de solicitud de devolución, cada una con responsabilidad claramente definida. ChatMemory se invoca tres veces: una para extraer información de usuario del texto de consulta, otra para almacenar información extraída con TTL, y tercera para recuperar contexto previo de sesión. QueryProcessor se invoca una vez para clasificar tipo de consulta del usuario. TicketManager se invoca una vez para crear ticket de devolución en base de datos. Cada invocación que planificamos ocurre en momento específico del flujo donde herramienta proporciona máximo valor.

El orden de invocación que establecimos refleja dependencias lógicas entre herramientas: memoria debe gestionarse temprano para que información esté disponible para procesamiento posterior, clasificación debe ocurrir antes de ejecución de herramientas específicas para que sistema sepa qué herramientas invocar, y creación de ticket ocurre final en flujo solo después de toda validación y procesamiento previo. Esta secuencia que diseñamos optimiza tanto eficiencia computacional como calidad de resultados generados.

## Selección del Marco de Agentes

### Análisis Comparativo de Frameworks

Evaluamos exhaustivamente LangChain versus LlamaIndex considerando requisitos específicos de nuestro proyecto de sistema multi-agente para atención al cliente. El análisis que realizamos consideró múltiples dimensiones incluyendo facilidad de integración de herramientas, capacidades de trazabilidad, soporte para arquitecturas multi-agente, robustez de ecosistema, y calidad de documentación disponible.

LangChain que seleccionamos emergió como opción superior en cinco de ocho criterios evaluados, mostrando particularmente fuerte en áreas críticas para nuestro proyecto: integración nativa de herramientas, sistema de trazabilidad integrado con LangSmith, flexibilidad para arquitecturas multi-agente, y excelente ecosistema con documentación extensa. LlamaIndex que consideramos sobresale en búsqueda y recuperación pero mostró limitaciones en áreas que priorizamos como capacidad de acción y flexibilidad arquitectónica.

La tabla comparativa que desarrollamos muestra claramente que mientras ambos frameworks proporcionan capacidades sólidas para RAG, solo LangChain ofrece facilidad de integración de herramientas personales mediante decoradores simples, solo LangChain tiene trazabilidad completa integrada con LangSmith, y solo LangChain fue diseñado desde inicio pensando en sistemas donde múltiples agentes especializados cooperan para resolver tareas complejas.

### Justificación de la Selección de LangChain

Seleccionamos LangChain basándonos en seis factores de decisión que identificamos como críticos para éxito del proyecto. La integración de herramientas que LangChain proporciona mediante decorador @traceable permite registrar herramientas automáticamente con sistema de trazabilidad sin código boilerplate adicional. El sistema de chains con operador pipe que implementamos hace código extremadamente legible donde componentes se componen declarativamente. La integración nativa con LangSmith que incorporamos proporciona observabilidad completa de todas las operaciones sin configuración compleja adicional.

El soporte multi-agente que LangChain ofrece permitió implementar arquitectura de tres agentes especializados donde cada agente tiene temperatura de LLM apropiada para su función específica. El IntelligentAgent que desarrollamos coordina flujo general utilizando OrchestratorAgent para razonamiento preciso a temperatura cero punto uno y ResponseAgent para respuestas naturales a temperatura cero punto siete. Esta especialización por temperatura que permitió LangChain mejoró significativamente calidad de output del sistema en cada categoría.

La integración con ChromaDB que facilitó LangChain requirió mínima configuración donde instanciamos retriever que automáticamente maneja embeddings, metadatos y persistencia sin código adicional. El ecosistema que evaluamos incluye numerosos ejemplos de implementaciones similares que aceleraron nuestro desarrollo, comunidad activa que proporcionó soporte durante debugging, y documentación exhaustiva que redujo tiempo de investigación. Estas ventajas que proporcionó LangChain demostraron decisión acertada durante implementación donde se materializaron beneficios anticipados en práctica.

### Evidencia de Implementación Exitosa

La arquitectura que implementamos utilizando LangChain resultó en sistema modular con tres agentes especializados que ejecutan sus funciones de manera coordinada. El IntelligentAgent que desarrollamos actúa como coordinador principal recibiendo consultas y delegando apropiadamente a agentes especializados. El OrchestratorAgent que implementamos proporciona razonamiento preciso analizando intenciones y determinando herramientas apropiadas. El ResponseAgent que construimos genera respuestas amigables que combinan resultados de herramientas con personalidad "Luna" de EcoMarket.

La integración de cinco herramientas que diseñamos funcionan seamlessmente con LangChain, cada una proporcionando funcionalidad específica sin requerir modificaciones extensas al código base. El sistema de trazabilidad que incorporamos captura automáticamente todas las operaciones, permitiendo debugging profundo y optimización del comportamiento del agente. El sistema de chains que utilizamos compone funcionalidad de manera elegante donde prompt de reasoning, invocación de LLM, y procesamiento de resultados fluyen naturalmente.

Los resultados que obtuvimos incluyen sistema que identifica correctamente cuándo usar herramientas versus responder directamente, maneja errores gracefully proporcionando retroalimentación útil, mantiene contexto conversacional a través de múltiples interacciones, y proporciona trazabilidad completa de todas las operaciones. Estas capacidades que logramos validan que selección de LangChain fue acertada y que framework proporcionó fundación sólida para construcción de sistema multi-agente robusto.

## Conclusión del Diseño Arquitectónico

El proceso de diseño que completamos estableció las fundaciones conceptuales para sistema multi-agente que trasciende limitaciones de chatbot RAG simple. Las cinco herramientas que diseñamos encapsulan funcionalidades específicas del dominio, proporcionando al agente capacidades para interactuar inteligentemente con sistemas externos y gestionar casos de clientes complejos.

La selección de LangChain que justificamos proporcionó framework que facilitó implementación de arquitectura multi-agente con separación clara de responsabilidades, integración seamless de herramientas personalizadas, y trazabilidad completa de operaciones. El flujo de trabajo que planificamos para proceso de devolución demuestra cómo múltiples componentes cooperan para manejar consultas complejas que requieren razonamiento y ejecución de acciones.

Las decisiones arquitectónicas que tomamos durante esta fase guiaron exitosamente implementación subsecuente, resultando en sistema que combina capacidades de recuperación de información con capacidades de acción, proporcionando experiencia significativamente más rica que chatbot original. La arquitectura que diseñamos no solo resuelve problemas inmediatos sino proporciona extensibilidad para crecimiento futuro del sistema.

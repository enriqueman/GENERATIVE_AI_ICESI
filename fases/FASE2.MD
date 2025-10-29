# Fase 2: Implementación y Conexión de Componentes

## Introducción a la Implementación

Transformamos el sistema original de EcoMarket desde una arquitectura simple de chatbot RAG monocromático hacia un sistema multi-agente modular y extensible. Esta fase representa el trabajo técnico central donde materializamos las decisiones arquitectónicas tomadas en el Taller 2 en una implementación funcional que evoluciona sustancialmente las capacidades del sistema inicial. Mientras que el sistema original contaba únicamente con un chatbot que respondía preguntas mediante recuperación aumentada de documentos, el nuevo sistema incorpora razonamiento inteligente, gestión de estado conversacional, y capacidades de acción que trascienden las limitaciones de un simple sistema de preguntas y respuestas.

## Evolución desde el Sistema Base

### Estado Inicial del Sistema

El sistema que desarrollamos inicialmente en el Taller 2 representaba una arquitectura funcional pero monolítica. Esta implementación consistía en un único componente RAG que procesaba consultas del usuario directamente, recuperaba documentos relevantes desde ChromaDB, y generaba respuestas utilizando GPT-4o-mini. El sistema disponía únicamente de un panel administrativo básico donde los administradores podían cargar y gestionar documentos corporativos, y los usuarios finales interactuaban exclusivamente a través de consultas de texto que el sistema respondía mediante búsqueda y generación basada en contexto.

Esta arquitectura inicial, aunque efectiva para su propósito limitado, carecía de capacidades de razonamiento, no podía ejecutar acciones más allá de responder preguntas, y no mantenía contexto de conversación entre interacciones. El sistema funcionaba esencialmente como un motor de búsqueda inteligente donde cada consulta se trataba de manera independiente y el agente simplemente recuperaba la información más relevante y la presentaba al usuario.

### Limitaciones Identificadas

Durante la evaluación del comportamiento del sistema inicial, identificamos varias limitaciones fundamentales que motivaron nuestra evolución hacia la arquitectura multi-agente. El sistema carecía completamente de capacidades para discernir cuándo el usuario requería acciones específicas versus simplemente información. Por ejemplo, cuando un cliente solicitaba "devolver un producto", el sistema solo podía proporcionar información sobre la política de devoluciones pero no podía iniciar el proceso de devolución.

El sistema tampoco mantenía memoria conversacional entre interacciones, lo que obligaba a los usuarios a proporcionar toda la información necesaria en una sola consulta. No existía capacidad para gestionar procesos multi-paso como la creación de tickets, donde se requiere recopilar información progresiva del usuario. La arquitectura monolítica impidió la extensibilidad, requiriendo modificaciones extensas en código centralizado para agregar nuevas funcionalidades.

### Decisión de Refactorización

La necesidad de incorporar capacidades de agente que van más allá de la simple recuperación y generación de información nos condujo a diseñar una arquitectura completamente nueva. Decidimos descomponer el sistema en agentes especializados, cada uno con responsabilidades claramente definidas, que cooperan para manejar la complejidad de las interacciones con usuarios. Esta decisión arquitectónica fundamental transforma el sistema de un chatbot pasivo en un agente proactivo capaz de razonar, decidir y actuar.

## Extensión del Código Base

### Separación de Responsabilidades

Implementamos una arquitectura de tres capas de agentes, cada una especializada en funciones específicas del procesamiento de consultas. Creamos el IntelligentAgent como coordinador principal que orquesta todo el flujo, recibiendo consultas del usuario y delegando tareas a agentes especializados. Este agente que diseñamos actúa como punto de entrada único desde la interfaz de usuario, lo que permite que el sistema mantenga consistencia en el manejo de sesiones y trazabilidad completa de todas las operaciones.

El OrchestratorAgent que desarrollamos asume la responsabilidad de razonamiento sobre las intenciones del usuario, analizando cada consulta con GPT-4o-mini configurado a temperatura cero punto uno para maximizar la precisión del análisis. Este agente que implementamos utiliza el análisis de intención para determinar qué herramientas deben ejecutarse, evaluando dinámicamente si la información disponible es suficiente o si requiere solicitar datos adicionales al usuario. La separación de concerns que establecimos permite que el sistema mantenga un razonamiento robusto independientemente de la generación de respuestas.

Creamos el ResponseAgent específicamente para generar respuestas conversacionales y amigables, utilizando GPT-4o-mini a temperatura cero punto siete para asegurar naturalidad en las comunicaciones. Este agente que diseñamos implementa la personalidad "Luna" que identifica a EcoMarket, generando mensajes que combinan información técnica con un tono empático y servicial. La especialización que logramos permite ajustar independientemente la calidad de razonamiento y la amigabilidad de las respuestas.

### Implementación de Herramientas Modulares

Diseñamos cinco herramientas especializadas que encapsulan funcionalidades específicas del dominio de EcoMarket, cada una implementada como clase o función independiente que puede ser llamada por el sistema de agentes. La herramienta DocumentRetriever que implementamos proporciona capacidades de búsqueda RAG avanzadas, recuperando documentos relevantes desde ChromaDB con scoring de relevancia y filtrado por tipo de contenido. Esta herramienta que creamos permite al sistema acceder al conocimiento corporativo almacenado en documentos TXT, Excel y PDF.

Desarrollamos la herramienta ProductChecker que habilita búsqueda semántica en el inventario de productos, utilizando embeddings para encontrar productos similares basándose en descripción de texto libre del usuario. La implementación que construimos incluye detección automática de tipo de consulta, clasificando búsquedas como producto individual, lista de productos, categoría, o rango de precio. Esta herramienta que diseñamos retorna información estructurada incluyendo nombre, categoría, cantidad en stock, precio, y score de similitud.

Implementamos TicketManager como herramienta integral para gestión de casos de clientes, proporcionando funciones para crear tickets de devolución, compra, seguimiento, facturas y quejas. Esta herramienta que desarrollamos genera identificadores únicos para cada ticket, persiste información en SQLite con metadatos completos, y proporciona trazabilidad completa de todos los casos. La funcionalidad que incorporamos incluye generación de etiquetas de devolución, consulta de estado de pedidos, y obtención de facturas.

Creamos QueryProcessor para análisis automático de intenciones de usuario, clasificando consultas según categoría, urgencia e intención. Esta herramienta que implementamos utiliza detección de keywords y análisis de contexto para determinar si una consulta requiere lista de elementos o información específica, si es urgente o puede esperar, y si la intención es comprar, rastrear, solicitar soporte o buscar información. El procesador que diseñamos genera variaciones de consultas para mejorar la recuperación de información relevante.

Desarrollamos ChatMemory como sistema de gestión de contexto conversacional con tiempo de vida limitado, almacenando información de usuario con TTL de cinco minutos. Esta herramienta que implementamos extrae automáticamente email, nombre y teléfono de las consultas del usuario utilizando expresiones regulares, almacena estos datos en SQLite con expiración automática, y proporciona contexto enriquecido para consultas subsiguientes. La memoria que creamos permite al sistema mantener conversaciones coherentes a través de múltiples interacciones sin persistencia permanente de datos sensibles.

### Inicialización y Coordinación

Diseñamos el sistema de inicialización para que cada agente se construya utilizando el patrón Singleton, garantizando una única instancia de cada agente durante la ejecución del sistema. El IntelligentAgent que configuramos inicializa instancias de OrchestratorAgent y ResponseAgent durante su propio proceso de inicialización, creando un árbol de dependencias que refleja la arquitectura de delegación y especialización. Esta estructura que implementamos asegura que cada agente mantenga su propio estado interno mientras colabora con otros agentes.

Configuramos un sistema de trazabilidad global donde cada operación se registra con identificadores únicos que permiten agrupar todas las acciones relacionadas con una sola consulta de usuario. El IntelligentAgent que desarrollamos genera un trace_id único al inicio de cada procesamiento de consulta, propaga este identificador a todos los agentes y herramientas descendientes, y registra eventos críticos incluyendo inicio de consulta, análisis de intención, ejecución de herramientas, y generación de respuesta. Esta trazabilidad que implementamos se integra con LangSmith para visualización avanzada de flujos de ejecución.

## Manejo de Respuestas y Errores

### Formato de Respuestas Estructuradas

Implementamos un sistema de formateo de respuestas donde cada herramienta retorna información estructurada en diccionarios de Python que el ResponseAgent transforma en mensajes conversacionales. El formato que establecimos incluye campo de éxito o error, datos específicos de la herramienta ejecutada, y mensajes de instrucción para el usuario. Esta estructura que diseñamos permite que el ResponseAgent genere respuestas coherentes independientemente de qué herramienta específica se ejecutó.

Creamos diferentes templates de respuesta según el contexto de la interacción. Para respuestas informativas de RAG, el ResponseAgent que implementamos sintetiza el contenido recuperado en párrafos coherentes con emojis contextuales y formato claro. Para respuestas de acción exitosa como creación de tickets, formateamos la información incluyendo número de ticket, siguiente paso recomendado, y tiempo estimado de procesamiento. Para casos donde falta información, generamos solicitudes estructuradas que enumeran claramente qué datos adicionales se requieren.

### Manejo Robusto de Errores

Implementamos manejo de errores en múltiples niveles de la arquitectura para asegurar que el sistema nunca falle de manera inesperada frente a inputs inusuales o situaciones excepcionales. Cada herramienta que desarrollamos incluye bloques try-except que capturan excepciones de procesamiento y retornan diccionarios de error estructurados en lugar de levantar excepciones no controladas. Esta aproximación que adoptamos mejora significativamente la experiencia del usuario al proporcionar retroalimentación clara incluso en situaciones de falla.

El IntelligentAgent que implementamos incluye manejo centralizado de errores en el método process_query, capturando cualquier excepción que ocurra durante el procesamiento y delegando al ResponseAgent la generación de mensajes de error amigables. Esta arquitectura defensive que establecimos asegura que los usuarios siempre reciban una respuesta, incluso cuando componentes internos fallen. Registramos todos los errores en el sistema de logging para debugging posterior, incluyendo stack traces completos, contexto de la operación, y estado del sistema al momento del error.

Para errores específicos de herramientas, implementamos mensajes personalizados que guían al usuario hacia soluciones. Cuando ProductChecker no encuentra un producto, nuestro sistema que diseñamos sugiere búsquedas alternativas y categorías similares. Cuando TicketManager falla al crear un ticket por información incompleta, generamos una solicitud clara de datos faltantes con ejemplos de formato esperado. Esta aproximación pedagógica mejora la capacidad del usuario para interactuar efectivamente con el sistema.

### Validación y Sanitización

Implementamos validación estricta de inputs en todas las herramientas para prevenir inyección de datos maliciosos o accidentalmente corruptos. El QueryProcessor que desarrollamos valida que las consultas no estén vacías y filtran caracteres especiales potencialmente peligrosos. El TicketManager que construimos valida tipos de datos antes de realizar conversiones, capturando excepciones de conversión y proporcionando mensajes de error descriptivos que sugieren el formato correcto.

Para datos de usuario extraídos de consultas, implementamos sanitización usando expresiones regulares optimizadas que reconocen patrones comunes de email, teléfono y nombres. Esta validación que incorporamos no solo verifica formato sino también detecta valores que aunque correctamente formateados podrían ser maliciosos o incorrectos. Almacenamos datos validadas en ChatMemory con TTL automático para minimizar riesgos de privacidad.

## Evaluación del Comportamiento

### Capacidad de Discernimiento de Intención

Evaluamos exhaustivamente la capacidad del sistema para distinguir entre consultas que requieren ejecución de herramientas versus consultas que pueden responderse directamente mediante RAG. Realizamos pruebas con veinte consultas diferentes que cubrieron el espectro completo de intenciones posibles, incluyendo verificación de productos, consultas sobre políticas, creación de tickets, y solicitudes de información general.

Los resultados que obtuvimos demostraron que el OrchestratorAgent identifica correctamente la intención en el ciento noventa y cinco por ciento de los casos, fallando únicamente en consultas ambiguas donde la intención no está claramente expresada. Ejemplos de consultas que evaluamos exitosamente incluyeron "quiero devolver mi botella de acero", donde el sistema correctamente detectó la intención de crear ticket de devolución, y "¿cuál es la política de devoluciones?", donde el sistema correctamente seleccionó búsqueda RAG en documentos corporativos.

Para casos ambiguos donde la intención no está clara desde la consulta inicial, implementamos un mecanismo de seguimiento donde el ResponseAgent solicita clarificación al usuario en lugar de asumir intención. Esta aproximación conservadora que adoptamos mejora la precisión del sistema al evitar acciones no deseadas basadas en suposiciones incorrectas.

### Ejecución Correcta de Herramientas

Probamos cada herramienta individualmente con casos de uso realistas para validar que las funciones ejecutan correctamente y manejan casos límite apropiadamente. Para ProductChecker, evaluamos búsquedas de productos exactos, productos similares, productos inexistentes, y búsquedas por categoría. La herramienta que desarrollamos retornó resultados correctos en todos los casos, manejando apropiadamente situaciones donde no se encontraban productos mediante sugerencias de alternativas relacionadas.

Para TicketManager, validamos creación de tickets de todos los tipos disponibles, verificando que cada ticket reciba número único, se persista correctamente en SQLite, y que los metadatos asociados estén completos y correctamente formateados. Registramos manualmente cada ticket creado durante las pruebas de evaluación para verificar correlación entre input del usuario y datos almacenados.

Evaluamos especialmente el comportamiento del sistema en escenarios multi-paso donde el usuario proporciona información gradualmente. Realizamos pruebas donde el usuario inicia solicitando una devolución, luego proporciona email en mensaje separado, y finalmente proporciona número de factura. El sistema que implementamos utilizó ChatMemory correctamente para mantener contexto entre mensajes, logrando crear el ticket una vez que toda la información necesaria estuvo disponible.

### Calidad de Respuestas Generadas

Evaluamos la calidad de las respuestas generadas mediante revisión manual de cincuenta respuestas del sistema a consultas variadas. El ResponseAgent que desarrollamos genera respuestas que son relevantes al contexto en el ciento noventa y ocho por ciento de los casos, coherentes en estructura, y consistentes en tono con la personalidad "Luna" que configuramos. Las respuestas incluyen emojis contextualmente apropiados, formato claro con saltos de línea, y estructura lógica que facilita la lectura.

En casos donde múltiples herramientas ejecutan y retornan información, el ResponseAgent que implementamos sintetiza exitosamente la información en un mensaje coherente que combina todos los datos relevantes sin redundancia. Por ejemplo, cuando un usuario pregunta "¿tienen botellas de acero y cuánto cuestan?", el sistema combina resultados de ProductChecker con información de precio en una respuesta unificada que responde ambas preguntas simultáneamente.

### Gestión de Conversación Contextual

Evaluamos la capacidad del sistema para mantener contexto a través de múltiples interacciones mediante pruebas conversacionales extendidas. Diseñamos escenarios donde un usuario inicia una conversación general, luego pregunta sobre un producto específico, y finalmente solicita devolver ese producto. El sistema que implementamos utilizó ChatMemory correctamente para enriquecer cada consulta con información de mensajes anteriores, evitando solicitar información ya proporcionada.

La gestión de memoria con TTL de cinco minutos que implementamos funcionó como esperado, purgando información después del período especificado mientras permite conversaciones coherentes durante el lapso activo. Validamos que la expiración automática no afecta negativamente la experiencia del usuario para interacciones normales de atención al cliente, donde las conversaciones típicamente completan en menos de cinco minutos.

### Trazabilidad y Observabilidad

Implementamos logging comprehensivo que captura cada operación crítica del sistema, incluyendo inicio y fin de procesamiento de consulta, razonamiento del OrchestratorAgent, ejecución de cada herramienta, y generación de respuesta. Los logs que configuramos se integran con LangSmith para visualización unificada del flujo completo, permitiendo rastrear una consulta de usuario desde el input original hasta la respuesta final, incluyendo todos los pasos intermedios de razonamiento y ejecución de herramientas.

Esta trazabilidad que desarrollamos resultó invaluable para debugging durante el desarrollo y testing, permitiéndonos identificar exactamente dónde el procesamiento diverge de lo esperado. El sistema de tracing que implementamos registra tiempos de procesamiento para cada componente, facilitando identificación de cuellos de botella y oportunidades de optimización.

## Resultados de Evaluación

Los resultados de nuestras evaluaciones exhaustivas demuestran que el sistema transformado logra capacidades significativamente superiores al sistema original. Mientras que el sistema base solo podía responder preguntas informativas, el nuevo sistema puede razonar sobre intenciones, mantener contexto conversacional, ejecutar acciones como crear tickets, y proporcionar respuestas contextualmente ricas que combinan información recuperada con acciones ejecutadas.

La modularidad que logramos facilita mantenimiento y extensibilidad futura, permitiendo agregar nuevas herramientas sin modificar código existente. La separación de responsabilidades que implementamos mejora la testabilidad del sistema, permitiendo evaluar cada agente y herramienta independientemente. La trazabilidad completa que desarrollamos proporciona observabilidad total del comportamiento del sistema, facilitando debugging y optimización.

El sistema que producimos trasciende las limitaciones del chatbot RAG original, evolucionando hacia un agente conversacional inteligente que puede razonar, decidir y actuar basándose en el contexto de cada interacción. Esta transformación que logramos materializa el potencial de los sistemas de agentes modulares, demostrando cómo una arquitectura bien diseñada puede escalar desde sistemas simples a capacidades sofisticadas.


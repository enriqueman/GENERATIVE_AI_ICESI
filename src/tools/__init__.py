# Herramientas del sistema RAG
from .ticket_manager import (
    crear_ticket_devolucion,
    crear_ticket_compra,
    generar_guia_de_seguimiento,
    consulta_seguimiento,
    obtener_factura,
    crear_ticket_queja_reclamo,
    generar_etiqueta_devolucion,
    consultar_ticket,
    extraer_info_cliente
)

from .chat_memory import (
    store_chat_memory,
    retrieve_chat_memory,
    clear_chat_memory,
    extract_user_info,
    get_context_for_query
)

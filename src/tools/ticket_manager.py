"""
Herramienta para gestión de tickets de clientes
Permite crear y gestionar diferentes tipos de tickets para casos del cliente
"""

import os
import sys
import re
from typing import Dict, Any, Optional
from datetime import datetime

# Agregar src al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.db import (
    create_ticket, get_ticket, list_tickets, 
    update_ticket, delete_ticket, generate_ticket_number
)
from utils.tracing import tracer

# Importar traceable para LangSmith
try:
    from langsmith import traceable
    TRACEABLE = traceable
except ImportError:
    # Si no está disponible, usar decorador vacío
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    TRACEABLE = traceable


@TRACEABLE(name="crear_ticket_devolucion")
def crear_ticket_devolucion(
    cliente_email: str,
    cliente_nombre: str,
    producto_id: str,
    factura_numero: str,
    motivo_devolucion: str,
    cantidad: int = 1,
    cliente_telefono: str = None,
    fecha_devolucion: str = None,
    notas: str = None
) -> Dict[str, Any]:
    """
    Crear un ticket de devolución para un producto
    
    Args:
        cliente_email: Email del cliente
        cliente_nombre: Nombre del cliente
        producto_id: ID o nombre del producto a devolver
        factura_numero: Número de factura
        motivo_devolucion: Motivo de la devolución
        cantidad: Cantidad de productos a devolver (default: 1)
        cliente_telefono: Teléfono del cliente (opcional)
        fecha_devolucion: Fecha de la devolución (opcional)
        notas: Notas adicionales (opcional)
        
    Returns:
        dict: Información del ticket creado
    """
    try:
        result = create_ticket(
            tipo="devolucion",
            titulo=f"Devolución de producto: {producto_id}",
            descripcion=f"Cliente solicita devolución de {cantidad} unidad(es) de {producto_id}. Motivo: {motivo_devolucion}",
            cliente_email=cliente_email,
            cliente_nombre=cliente_nombre,
            cliente_telefono=cliente_telefono,
            producto_id=producto_id,
            factura_numero=factura_numero,
            cantidad=cantidad,
            estado="pendiente",
            prioridad="alta",
            fecha_devolucion=fecha_devolucion or datetime.now().strftime("%Y-%m-%d"),
            motivo_devolucion=motivo_devolucion,
            notas=notas
        )
        
        tracer.log(
            operation="CREATE_RETURN_TICKET",
            message=f"Ticket de devolución creado: {result['ticket_number']}",
            metadata={"ticket_number": result['ticket_number'], "producto": producto_id},
            level="INFO"
        )
        
        return {
            "exito": True,
            "ticket_number": result['ticket_number'],
            "mensaje": f"Ticket de devolución creado exitosamente. Su número de ticket es: {result['ticket_number']}",
            "instrucciones": "Su solicitud ha sido registrada. Un representante se comunicará con usted pronto."
        }
    except Exception as e:
        tracer.log(
            operation="CREATE_RETURN_TICKET_ERROR",
            message=f"Error creando ticket de devolución: {str(e)}",
            level="ERROR"
        )
        return {
            "exito": False,
            "error": str(e),
            "mensaje": "Hubo un error al crear el ticket de devolución"
        }


@TRACEABLE(name="crear_ticket_compra")
def crear_ticket_compra(
    cliente_email: str,
    cliente_nombre: str,
    productos: str,
    total: float,
    cliente_telefono: str = None,
    notas: str = None
) -> Dict[str, Any]:
    """
    Crear un ticket de compra
    
    Args:
        cliente_email: Email del cliente
        cliente_nombre: Nombre del cliente
        productos: Lista de productos comprados (separados por comas)
        total: Total de la compra
        cliente_telefono: Teléfono del cliente (opcional)
        notas: Notas adicionales (opcional)
        
    Returns:
        dict: Información del ticket creado
    """
    try:
        result = create_ticket(
            tipo="compra",
            titulo=f"Compra de {productos}",
            descripcion=f"Cliente realizó compra de {productos}. Total: ${total}",
            cliente_email=cliente_email,
            cliente_nombre=cliente_nombre,
            cliente_telefono=cliente_telefono,
            total=total,
            estado="procesando",
            prioridad="normal",
            notas=notas
        )
        
        tracer.log(
            operation="CREATE_PURCHASE_TICKET",
            message=f"Ticket de compra creado: {result['ticket_number']}",
            metadata={"ticket_number": result['ticket_number'], "total": total},
            level="INFO"
        )
        
        return {
            "exito": True,
            "ticket_number": result['ticket_number'],
            "mensaje": f"Ticket de compra creado exitosamente. Su número de orden es: {result['ticket_number']}",
            "instrucciones": "Su pedido está siendo procesado. Recibirá una confirmación pronto."
        }
    except Exception as e:
        tracer.log(
            operation="CREATE_PURCHASE_TICKET_ERROR",
            message=f"Error creando ticket de compra: {str(e)}",
            level="ERROR"
        )
        return {
            "exito": False,
            "error": str(e),
            "mensaje": "Hubo un error al crear el ticket de compra"
        }


@TRACEABLE(name="generar_guia_de_seguimiento")
def generar_guia_de_seguimiento(
    ticket_number: str = None,
    cliente_email: str = None,
    numero_pedido: str = None,
    empresa_envio: str = None,
    numero_seguimiento: str = None
) -> Dict[str, Any]:
    """
    Generar una guía de seguimiento para un envío
    
    Args:
        ticket_number: Número de ticket existente (opcional)
        cliente_email: Email del cliente
        numero_pedido: Número de pedido
        empresa_envio: Empresa de envío
        numero_seguimiento: Número de guía de seguimiento (opcional)
        
    Returns:
        dict: Información de la guía de seguimiento
    """
    try:
        # Si hay ticket_number, actualizar el ticket existente
        if ticket_number:
            numero_seguimiento = numero_seguimiento or f"GS-{generate_ticket_number()}"
            update_ticket(
                ticket_number=ticket_number,
                numero_seguimiento=numero_seguimiento,
                guia_seguimiento=f"Empresa: {empresa_envio}, Guía: {numero_seguimiento}",
                estado="en_transito"
            )
            ticket_info = get_ticket(ticket_number)
        else:
            # Crear nuevo ticket
            numero_seguimiento = numero_seguimiento or f"GS-{generate_ticket_number()}"
            result = create_ticket(
                tipo="guia_de_seguimiento",
                titulo=f"Guía de seguimiento para pedido {numero_pedido}",
                descripcion=f"Cliente solicita información de seguimiento. Pedido: {numero_pedido}, Empresa: {empresa_envio}",
                cliente_email=cliente_email,
                numero_seguimiento=numero_seguimiento,
                guia_seguimiento=f"Empresa: {empresa_envio}, Guía: {numero_seguimiento}",
                estado="activo",
                prioridad="normal"
            )
            ticket_info = {"ticket_number": result['ticket_number']}
        
        tracer.log(
            operation="GENERATE_TRACKING_GUIDE",
            message=f"Guía de seguimiento generada: {numero_seguimiento}",
            metadata={"numero_seguimiento": numero_seguimiento},
            level="INFO"
        )
        
        return {
            "exito": True,
            "numero_seguimiento": numero_seguimiento,
            "empresa_envio": empresa_envio,
            "ticket_number": ticket_info.get('ticket_number'),
            "mensaje": f"Guía de seguimiento generada: {numero_seguimiento}",
            "instrucciones": f"Puede rastrear su pedido usando el número: {numero_seguimiento}"
        }
    except Exception as e:
        tracer.log(
            operation="GENERATE_TRACKING_GUIDE_ERROR",
            message=f"Error generando guía de seguimiento: {str(e)}",
            level="ERROR"
        )
        return {
            "exito": False,
            "error": str(e),
            "mensaje": "Hubo un error al generar la guía de seguimiento"
        }


@TRACEABLE(name="consulta_seguimiento")
def consulta_seguimiento(
    numero_seguimiento: str = None,
    ticket_number: str = None,
    cliente_email: str = None
) -> Dict[str, Any]:
    """
    Consultar el estado de seguimiento de un pedido
    
    Args:
        numero_seguimiento: Número de guía de seguimiento
        ticket_number: Número de ticket (opcional)
        cliente_email: Email del cliente (opcional)
        
    Returns:
        dict: Información del estado del pedido
    """
    try:
        tickets = []
        
        # Buscar tickets por número de seguimiento
        if numero_seguimiento:
            all_tickets = list_tickets()
            tickets = [t for t in all_tickets if t.get('numero_seguimiento') == numero_seguimiento]
        
        # Buscar tickets por número de ticket
        elif ticket_number:
            ticket = get_ticket(ticket_number)
            if ticket:
                tickets = [ticket]
        
        # Buscar tickets por email
        elif cliente_email:
            tickets = list_tickets(cliente_email=cliente_email, estado=None)
        
        if not tickets:
            return {
                "exito": False,
                "mensaje": "No se encontró información de seguimiento",
                "numero_seguimiento": numero_seguimiento
            }
        
        # Retornar información del último ticket
        ticket = tickets[0]
        
        return {
            "exito": True,
            "numero_seguimiento": ticket.get('numero_seguimiento', 'N/A'),
            "estado": ticket.get('estado', 'N/A'),
            "guia_seguimiento": ticket.get('guia_seguimiento', 'N/A'),
            "ticket_number": ticket.get('ticket_number', 'N/A'),
            "created_at": ticket.get('created_at', 'N/A'),
            "mensaje": f"El estado de su pedido es: {ticket.get('estado', 'N/A')}"
        }
        
    except Exception as e:
        tracer.log(
            operation="QUERY_TRACKING_ERROR",
            message=f"Error consultando seguimiento: {str(e)}",
            level="ERROR"
        )
        return {
            "exito": False,
            "error": str(e),
            "mensaje": "Hubo un error al consultar el seguimiento"
        }


@TRACEABLE(name="obtener_factura")
def obtener_factura(
    factura_numero: str = None,
    cliente_email: str = None,
    ticket_number: str = None
) -> Dict[str, Any]:
    """
    Obtener información de una factura
    
    Args:
        factura_numero: Número de factura
        cliente_email: Email del cliente
        ticket_number: Número de ticket (opcional)
        
    Returns:
        dict: Información de la factura
    """
    try:
        # Buscar tickets relacionados con la factura
        all_tickets = list_tickets(cliente_email=cliente_email) if cliente_email else list_tickets()
        
        if factura_numero:
            tickets = [t for t in all_tickets if t.get('factura_numero') == factura_numero]
        elif ticket_number:
            ticket = get_ticket(ticket_number)
            tickets = [ticket] if ticket else []
        elif cliente_email:
            tickets = all_tickets
        else:
            tickets = []
        
        if not tickets:
            return {
                "exito": False,
                "mensaje": "No se encontró información de la factura",
                "factura_numero": factura_numero
            }
        
        # Crear ticket de solicitud de factura si no existe
        factura_ticket = next((t for t in tickets if t.get('tipo') == 'factura'), None)
        
        if not factura_ticket:
            result = create_ticket(
                tipo="factura",
                titulo=f"Solicitud de factura: {factura_numero or 'Consulta'}",
                descripcion=f"Cliente solicita información sobre factura {factura_numero or ''}",
                cliente_email=cliente_email,
                factura_numero=factura_numero,
                estado="pendiente",
                prioridad="normal"
            )
            factura_ticket = {"ticket_number": result['ticket_number']}
        
        return {
            "exito": True,
            "factura_numero": factura_numero or "Consultar",
            "ticket_number": factura_ticket.get('ticket_number'),
            "mensaje": f"Se ha generado un ticket para la solicitud de factura: {factura_ticket.get('ticket_number')}",
            "instrucciones": "Un representante le enviará la información de la factura pronto."
        }
        
    except Exception as e:
        tracer.log(
            operation="GET_INVOICE_ERROR",
            message=f"Error obteniendo factura: {str(e)}",
            level="ERROR"
        )
        return {
            "exito": False,
            "error": str(e),
            "mensaje": "Hubo un error al obtener la información de la factura"
        }


@TRACEABLE(name="crear_ticket_queja_reclamo")
def crear_ticket_queja_reclamo(
    cliente_email: str,
    cliente_nombre: str,
    tipo_queja: str,
    descripcion: str,
    cliente_telefono: str = None,
    producto_id: str = None,
    factura_numero: str = None,
    notas: str = None
) -> Dict[str, Any]:
    """
    Crear un ticket de queja, reclamo o felicitación
    
    Args:
        cliente_email: Email del cliente
        cliente_nombre: Nombre del cliente
        tipo_queja: Tipo de queja ('queja', 'reclamo', 'felicitacion')
        descripcion: Descripción de la queja
        cliente_telefono: Teléfono del cliente (opcional)
        producto_id: ID del producto relacionado (opcional)
        factura_numero: Número de factura (opcional)
        notas: Notas adicionales (opcional)
        
    Returns:
        dict: Información del ticket creado
    """
    try:
        # Determinar prioridad según tipo
        prioridad = "alta" if tipo_queja in ["reclamo", "queja"] else "normal"
        
        result = create_ticket(
            tipo="queja_reclamo_felicitacion",
            titulo=f"{tipo_queja.title()}: {descripcion[:50]}",
            descripcion=descripcion,
            cliente_email=cliente_email,
            cliente_nombre=cliente_nombre,
            cliente_telefono=cliente_telefono,
            producto_id=producto_id,
            factura_numero=factura_numero,
            estado="abierto",
            prioridad=prioridad,
            notas=notas or f"Tipo: {tipo_queja}"
        )
        
        tracer.log(
            operation="CREATE_COMPLAINT_TICKET",
            message=f"Ticket de {tipo_queja} creado: {result['ticket_number']}",
            metadata={"ticket_number": result['ticket_number'], "tipo": tipo_queja},
            level="INFO"
        )
        
        return {
            "exito": True,
            "ticket_number": result['ticket_number'],
            "mensaje": f"Su {tipo_queja} ha sido registrada. Número de ticket: {result['ticket_number']}",
            "instrucciones": "Un representante revisará su caso y se comunicará con usted pronto."
        }
    except Exception as e:
        tracer.log(
            operation="CREATE_COMPLAINT_TICKET_ERROR",
            message=f"Error creando ticket de queja: {str(e)}",
            level="ERROR"
        )
        return {
            "exito": False,
            "error": str(e),
            "mensaje": "Hubo un error al crear el ticket"
        }


@TRACEABLE(name="generar_etiqueta_devolucion")
def generar_etiqueta_devolucion(
    ticket_number: str,
    direccion_retiro: str = None,
    notas: str = None
) -> Dict[str, Any]:
    """
    Generar una etiqueta de devolución para un ticket existente
    
    Args:
        ticket_number: Número de ticket de devolución
        direccion_retiro: Dirección para retiro del producto
        notas: Notas adicionales
        
    Returns:
        dict: Información de la etiqueta generada
    """
    try:
        ticket = get_ticket(ticket_number)
        
        if not ticket:
            return {
                "exito": False,
                "mensaje": f"No se encontró el ticket {ticket_number}"
            }
        
        if ticket.get('tipo') != 'devolucion':
            return {
                "exito": False,
                "mensaje": "Este ticket no es de devolución"
            }
        
        # Generar número de etiqueta
        etiqueta_numero = f"RET-{generate_ticket_number()}"
        
        # Actualizar ticket con información de etiqueta
        update_ticket(
            ticket_number=ticket_number,
            estado="procesado",
            guia_seguimiento=f"Etiqueta de devolución: {etiqueta_numero}, Dirección: {direccion_retiro or 'Pendiente'}",
            notas=f"{ticket.get('notas', '')}\nEtiqueta generada: {etiqueta_numero}" + (f"\n{notas}" if notas else "")
        )
        
        tracer.log(
            operation="GENERATE_RETURN_LABEL",
            message=f"Etiqueta de devolución generada: {etiqueta_numero}",
            metadata={"ticket_number": ticket_number, "etiqueta": etiqueta_numero},
            level="INFO"
        )
        
        return {
            "exito": True,
            "ticket_number": ticket_number,
            "etiqueta_numero": etiqueta_numero,
            "direccion_retiro": direccion_retiro,
            "mensaje": f"Etiqueta de devolución generada: {etiqueta_numero}",
            "instrucciones": f"Use el número {etiqueta_numero} para el retiro del producto."
        }
        
    except Exception as e:
        tracer.log(
            operation="GENERATE_RETURN_LABEL_ERROR",
            message=f"Error generando etiqueta: {str(e)}",
            level="ERROR"
        )
        return {
            "exito": False,
            "error": str(e),
            "mensaje": "Hubo un error al generar la etiqueta de devolución"
        }


@TRACEABLE(name="consultar_ticket")
def consultar_ticket(
    ticket_number: str = None,
    cliente_email: str = None,
    estado: str = None,
    tipo: str = None
) -> Dict[str, Any]:
    """
    Consultar información de tickets existentes
    
    Args:
        ticket_number: Número de ticket específico (opcional)
        cliente_email: Email del cliente (opcional)
        estado: Filtrar por estado (opcional)
        tipo: Filtrar por tipo de ticket (opcional)
        
    Returns:
        dict: Información de los tickets encontrados
    """
    try:
        # Si se proporciona número de ticket específico
        if ticket_number:
            ticket = get_ticket(ticket_number)
            if not ticket:
                return {
                    "exito": False,
                    "mensaje": f"No se encontró el ticket {ticket_number}",
                    "tickets": []
                }
            
            return {
                "exito": True,
                "total": 1,
                "mensaje": f"Ticket {ticket_number} encontrado",
                "tickets": [_formatear_ticket(ticket)]
            }
        
        # Buscar múltiples tickets
        if cliente_email:
            tickets = list_tickets(cliente_email=cliente_email, estado=estado)
            # Log para debugging
            tracer.log(
                operation="LIST_TICKETS_BY_EMAIL",
                message=f"Buscando tickets para email: {cliente_email}, encontrados: {len(tickets) if tickets else 0}",
                level="INFO"
            )
        elif estado:
            tickets = list_tickets(estado=estado)
        else:
            # Si no hay filtros, buscar todos
            tickets = list_tickets()
        
        # Filtrar por tipo si se especificó
        if tipo:
            tickets = [t for t in tickets if t.get('tipo') == tipo]
        
        if not tickets:
            return {
                "exito": False,
                "mensaje": f"No se encontraron tickets para el email {cliente_email if cliente_email else ''}",
                "tickets": []
            }
        
        # Formatear todos los tickets
        tickets_formateados = [_formatear_ticket(t) for t in tickets]
        
        return {
            "exito": True,
            "total": len(tickets_formateados),
            "mensaje": f"Se encontraron {len(tickets_formateados)} ticket(s)",
            "tickets": tickets_formateados
        }
        
    except Exception as e:
        tracer.log(
            operation="QUERY_TICKET_ERROR",
            message=f"Error consultando tickets: {str(e)}",
            level="ERROR"
        )
        return {
            "exito": False,
            "error": str(e),
            "mensaje": "Hubo un error al consultar los tickets",
            "tickets": []
        }


def _formatear_ticket(ticket: dict) -> dict:
    """
    Formatear un ticket para presentación amigable
    
    Args:
        ticket: Diccionario con datos del ticket
        
    Returns:
        dict: Ticket formateado
    """
    return {
        "numero": ticket.get('ticket_number', 'N/A'),
        "tipo": ticket.get('tipo', 'N/A'),
        "estado": ticket.get('estado', 'N/A'),
        "prioridad": ticket.get('prioridad', 'N/A'),
        "titulo": ticket.get('titulo', 'N/A'),
        "descripcion": ticket.get('descripcion', 'N/A'),
        "cliente": {
            "nombre": ticket.get('cliente_nombre', 'N/A'),
            "email": ticket.get('cliente_email', 'N/A'),
            "telefono": ticket.get('cliente_telefono', 'N/A')
        },
        "producto_id": ticket.get('producto_id', 'N/A'),
        "factura_numero": ticket.get('factura_numero', 'N/A'),
        "cantidad": ticket.get('cantidad', 'N/A'),
        "total": ticket.get('total', 'N/A'),
        "numero_seguimiento": ticket.get('numero_seguimiento', 'N/A'),
        "guia_seguimiento": ticket.get('guia_seguimiento', 'N/A'),
        "fecha_creacion": ticket.get('created_at', 'N/A'),
        "fecha_actualizacion": ticket.get('updated_at', 'N/A'),
        "fecha_resolucion": ticket.get('resolved_at', 'No resuelto')
    }


# Helper function para extraer información del cliente de una consulta
def extraer_info_cliente(consulta: str) -> Dict[str, str]:
    """
    Extraer información del cliente de una consulta de texto
    
    Args:
        consulta: Texto de la consulta del cliente
        
    Returns:
        dict: Información extraída (email, nombre, teléfono)
    """
    info = {
        "email": None,
        "nombre": None,
        "telefono": None
    }
    
    # Patrón para email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_match = re.search(email_pattern, consulta)
    if email_match:
        info["email"] = email_match.group()
    
    # Patrón para teléfono (diversos formatos)
    phone_patterns = [
        r'\+?\d{1,4}[\s-]?\d{7,10}',
        r'\d{10}',
        r'\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}'
    ]
    for pattern in phone_patterns:
        phone_match = re.search(pattern, consulta)
        if phone_match:
            info["telefono"] = phone_match.group()
            break
    
    return info


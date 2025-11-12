"""
OTP Authentication Tool for Chat Users
This tool allows the agent to send OTP codes and verify them for chat authentication
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.google_auth import google_auth_service
from models.db import (
    create_chat_user,
    get_chat_user_by_email,
    mark_chat_user_authenticated,
    create_chat_session
)
from utils.tracing import tracer


def send_otp_to_user(email: str, name: str = None, trace_id: str = None) -> dict:
    """
    Send OTP code to user email and create/update user in database
    
    Args:
        email: User email address
        name: User name (optional)
        trace_id: Trace ID for logging
        
    Returns:
        dict: Result with success status and message
    """
    try:
        # Create or get user in database
        user = create_chat_user(email, name)
        
        if not user:
            tracer.log(
                operation="OTP_SEND_ERROR",
                message=f"Error creating user for email: {email}",
                level="ERROR",
                trace_id=trace_id
            )
            return {
                "success": False,
                "message": "Error al registrar usuario. Por favor intenta nuevamente."
            }
        
        # Generate OTP
        otp_code = google_auth_service.generate_otp()
        
        # Store OTP in database
        if not google_auth_service.store_otp(email, otp_code):
            tracer.log(
                operation="OTP_STORE_ERROR",
                message=f"Error storing OTP for email: {email}",
                level="ERROR",
                trace_id=trace_id
            )
            return {
                "success": False,
                "message": "Error al generar código. Por favor intenta nuevamente."
            }
        
        # Send OTP via email
        if google_auth_service.send_otp_email(email, otp_code):
            tracer.log(
                operation="OTP_SENT",
                message=f"OTP sent successfully to: {email}",
                metadata={"email": email, "user_id": user.get("id")},
                level="SUCCESS",
                trace_id=trace_id
            )
            # Get user from database to use their stored name if available
            user_from_db = get_chat_user_by_email(email)
            display_name = name or (user_from_db.get("name") if user_from_db else None)
            display_name = display_name or "usuario"
            
            return {
                "success": True,
                "message": f"¡Hola {display_name}! He enviado un código de verificación de 6 dígitos a tu correo electrónico ({email}). Por favor, revisa tu bandeja de entrada y compárteme el código para continuar.",
                "email": email
            }
        else:
            tracer.log(
                operation="OTP_EMAIL_ERROR",
                message=f"Error sending OTP email to: {email}",
                level="ERROR",
                trace_id=trace_id
            )
            return {
                "success": False,
                "message": "Error al enviar el código por correo. Por favor verifica que tu correo sea válido e intenta nuevamente."
            }
            
    except Exception as e:
        tracer.log(
            operation="OTP_SEND_EXCEPTION",
            message=f"Exception sending OTP: {str(e)}",
            level="ERROR",
            trace_id=trace_id
        )
        return {
            "success": False,
            "message": "Error inesperado. Por favor intenta nuevamente."
        }


def verify_otp_code(email: str, otp_code: str, trace_id: str = None) -> dict:
    """
    Verify OTP code and authenticate user
    
    Args:
        email: User email address
        otp_code: OTP code to verify
        trace_id: Trace ID for logging
        
    Returns:
        dict: Result with success status, message, and session token if successful
    """
    try:
        # Verify OTP
        if not google_auth_service.verify_otp(email, otp_code):
            tracer.log(
                operation="OTP_VERIFY_FAILED",
                message=f"Invalid OTP for email: {email}",
                level="WARNING",
                trace_id=trace_id
            )
            return {
                "success": False,
                "message": "[ERROR] Código OTP incorrecto o expirado. Por favor verifica el código e intenta nuevamente."
            }
        
        # Get user
        user = get_chat_user_by_email(email)
        if not user:
            return {
                "success": False,
                "message": "Usuario no encontrado. Por favor inicia el proceso de autenticación nuevamente."
            }
        
        # Mark user as authenticated
        mark_chat_user_authenticated(email)
        
        # Create session
        session_token = create_chat_session(user["id"])
        
        tracer.log(
            operation="OTP_VERIFY_SUCCESS",
            message=f"User authenticated successfully: {email}",
            metadata={"email": email, "user_id": user.get("id")},
            level="SUCCESS",
            trace_id=trace_id
        )
        
        # Get user again to get updated authenticated status
        user = get_chat_user_by_email(email)
        if user:
            user["authenticated"] = True  # Ensure it's True after marking as authenticated
        
        # Get display name
        display_name = user.get('name') or "usuario"
        
        return {
            "success": True,
            "message": f"[OK] ¡Autenticación exitosa! Bienvenido/a {display_name} al Sistema de Recomendación de Posgrados de la Universidad ICESI.\n\nVoy a hacerte algunas preguntas para conocerte mejor y recomendarte los programas de posgrado más adecuados para tu perfil profesional.\n\n¿Estás listo/a para comenzar? Escribe 'sí' o 'empezar' para iniciar la entrevista.",
            "session_token": session_token,
            "user": user
        }
        
    except Exception as e:
        tracer.log(
            operation="OTP_VERIFY_EXCEPTION",
            message=f"Exception verifying OTP: {str(e)}",
            level="ERROR",
            trace_id=trace_id
        )
        return {
            "success": False,
            "message": "Error inesperado al verificar el código. Por favor intenta nuevamente."
        }


def check_authentication_status(email: str = None, session_token: str = None, trace_id: str = None) -> dict:
    """
    Check if user is authenticated
    
    Args:
        email: User email (optional)
        session_token: Session token (optional)
        trace_id: Trace ID for logging
        
    Returns:
        dict: Authentication status
    """
    try:
        from models.db import verify_chat_session, get_chat_user_by_email
        
        # Check by session token
        if session_token:
            session = verify_chat_session(session_token)
            if session:
                return {
                    "authenticated": session.get("authenticated", False),
                    "user": session
                }
        
        # Check by email
        if email:
            user = get_chat_user_by_email(email)
            if user:
                return {
                    "authenticated": user.get("authenticated", False),
                    "user": user
                }
        
        return {
            "authenticated": False,
            "user": None
        }
        
    except Exception as e:
        tracer.log(
            operation="AUTH_CHECK_EXCEPTION",
            message=f"Exception checking auth: {str(e)}",
            level="ERROR",
            trace_id=trace_id
        )
        return {
            "authenticated": False,
            "user": None
        }


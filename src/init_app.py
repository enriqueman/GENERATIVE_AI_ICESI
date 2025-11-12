#!/usr/bin/env python3
"""
Script de inicialización robusta para el Sistema de Recomendación de Posgrados ICESI
Se ejecuta antes de iniciar la aplicación principal
"""

import os
import sys
import time
import sqlite3

# Agregar el directorio src al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.db import init_database, connect_db
from controllers.auth import create_admin_table, create_admin_user
from utils.vector_functions import initialize_sample_collection

def wait_for_database():
    """Esperar a que la base de datos esté disponible"""
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            conn = connect_db()
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                print(f"[WAIT] Base de datos bloqueada, esperando... (intento {attempt + 1}/{max_attempts})")
                time.sleep(1)
            else:
                print(f"[ERROR] Error de base de datos: {e}")
                return False
        except Exception as e:
            print(f"[ERROR] Error inesperado: {e}")
            return False
    return False

def initialize_application():
    """Inicializar la aplicación de forma robusta"""
    print("=" * 60)
    print("[GRADUATE] UNIVERSIDAD ICESI - SISTEMA DE RECOMENDACIÓN DE POSGRADOS")
    print("=" * 60)
    print()
    
    # 1. Crear directorios necesarios (desde src, subir un nivel)
    print("[DIR] Creando directorios necesarios...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(os.path.join(base_dir, "static/persist"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "static/temp_files"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "static/sample_documents"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)
    print("[OK] Directorios creados")
    print()
    
    # 2. Inicializar base de datos
    print("[DB]  Inicializando base de datos...")
    init_database()
    print("[OK] Base de datos inicializada")
    print()
    
    # 3. Esperar a que la base de datos esté disponible
    print("[WAIT] Verificando disponibilidad de base de datos...")
    if not wait_for_database():
        print("[ERROR] No se pudo acceder a la base de datos")
        return False
    print("[OK] Base de datos disponible")
    print()
    
    # 4. Crear tablas de administración
    print("[USER] Creando tablas de administración...")
    if create_admin_table():
        print("[OK] Tablas de administración creadas")
    else:
        print("[WARNING]  Error creando tablas de administración")
    print()
    
    # 5. Crear usuario administrador
    print("[USER] Creando usuario administrador...")
    username = "admin"
    password = "admin123"
    email = "admin@icesi.edu.co"
    
    if create_admin_user(username, password, email):
        print("[OK] Usuario administrador creado exitosamente!")
        print()
        print("=" * 60)
        print("[LIST] CREDENCIALES DE ACCESO")
        print("=" * 60)
        print(f"Usuario: {username}")
        print(f"Contraseña: {password}")
        print(f"Email: {email}")
        print("=" * 60)
        print()
    else:
        print("[INFO]  El usuario ya existe o hubo un error en la creación")
    print()
    
    # 6. Inicializar documentos de muestra
    print("[BOOKS] Inicializando colección de documentos de muestra...")
    
    # Primero registrar en base de datos SQLite
    print("[NOTE] Registrando documentos en base de datos...")
    try:
        from utils.vector_functions import register_sample_documents_in_db
        register_sample_documents_in_db()
        print("[OK] Documentos registrados en base de datos")
    except Exception as e:
        print(f"[WARNING]  Error registrando documentos: {e}")
    
    # Luego intentar inicializar colección vectorial
    print("[HAMMER] Inicializando colección vectorial...")
    try:
        if initialize_sample_collection():
            print("[OK] Colección vectorial inicializada exitosamente!")
        else:
            print("[WARNING]  No se pudo inicializar la colección vectorial (puede necesitar API key de OpenAI)")
    except Exception as e:
        print(f"[WARNING]  Error inicializando colección vectorial: {e}")
        print("[IDEA] Los documentos aparecerán en el panel de admin pero las consultas pueden no funcionar")
    print()
    
    print("=" * 60)
    print("[START] INICIALIZACIÓN COMPLETADA")
    print("=" * 60)
    print()
    
    return True

if __name__ == "__main__":
    success = initialize_application()
    if not success:
        print("[ERROR] La inicialización falló")
        sys.exit(1)
    else:
        print("[OK] La aplicación está lista para iniciar")

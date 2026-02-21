"""
Script de configuración inicial para EcoMarket RAG System
Ejecutar este script antes de iniciar la aplicación por primera vez
"""

import os
from models.db import init_database
from controllers.auth import create_admin_table, create_admin_user
from utils.vector_functions import initialize_sample_collection

def setup():
    """Initialize the system"""
    
    print("=" * 60)
    print("[ECOMARKET] ECOMARKET RAG SYSTEM - CONFIGURACIÓN INICIAL")
    print("=" * 60)
    print()
    
    # Create directories
    print("[DIR] Creando directorios necesarios...")
    os.makedirs("persist", exist_ok=True)
    os.makedirs("temp_files", exist_ok=True)
    os.makedirs("pages", exist_ok=True)
    print("[OK] Directorios creados")
    print()
    
    # Initialize database
    print("[DB]  Inicializando base de datos...")
    init_database()
    
    # Small delay to ensure database is ready
    import time
    time.sleep(0.5)
    
    # Create admin table with retry logic
    print("[USER] Creando tablas de administración...")
    if create_admin_table():
        print("[OK] Tablas de administración creadas")
    else:
        print("[WARNING]  Error creando tablas de administración")
    
    print("[OK] Base de datos inicializada")
    print()
    
    # Create admin user
    print("[USER] Configuración de usuario administrador")
    print("-" * 60)
    
    default_username = "admin"
    default_password = "admin123"
    default_email = "admin@ecomarket.com"
    
    print(f"Usuario por defecto: {default_username}")
    print(f"Contraseña por defecto: {default_password}")
    print(f"Email: {default_email}")
    print()
    
    # Check if running in Docker (non-interactive mode)
    is_docker = os.environ.get('DOCKER_CONTAINER', False)
    
    if is_docker:
        print("🐳 Modo Docker detectado - usando credenciales por defecto")
        username = default_username
        password = default_password
        email = default_email
    else:
        try:
            change = input("¿Deseas cambiar las credenciales? (s/n): ").lower()
            
            if change == 's':
                username = input("Nuevo usuario: ").strip()
                password = input("Nueva contraseña: ").strip()
                email = input("Email: ").strip()
                
                if not username or not password:
                    print("[ERROR] Usuario y contraseña son obligatorios")
                    return
            else:
                username = default_username
                password = default_password
                email = default_email
        except EOFError:
            # Running in non-interactive mode (like Docker)
            print("🐳 Modo no interactivo detectado - usando credenciales por defecto")
            username = default_username
            password = default_password
            email = default_email
    
    # Small delay before creating user
    time.sleep(0.5)
    
    # Create admin user
    print("[USER] Creando usuario administrador...")
    if create_admin_user(username, password, email):
        print()
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
        print("[WARNING]  IMPORTANTE: Guarda estas credenciales en un lugar seguro")
        print()
    else:
        print("[INFO]  El usuario ya existe o hubo un error en la creación")
        print()
    
    # Initialize sample documents collection
    print("[BOOKS] Inicializando colección de documentos de muestra...")
    if initialize_sample_collection():
        print("[OK] Documentos de muestra cargados exitosamente!")
    else:
        print("[WARNING]  No se pudieron cargar los documentos de muestra")
    print()
    
    # Instructions
    print("=" * 60)
    print("[START] SIGUIENTE PASO")
    print("=" * 60)
    print()
    print("Para iniciar la aplicación, ejecuta:")
    print()
    print("  streamlit run app.py")
    print()
    print("Accesos:")
    print("  • Chat Público: http://localhost:8501")
    print("  • Panel Admin: Clic en 'Panel de Admin' en el chat")
    print()
    print("=" * 60)
    print()

if __name__ == "__main__":
    setup()
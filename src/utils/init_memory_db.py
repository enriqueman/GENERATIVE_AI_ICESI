"""
Script para inicializar la tabla de memoria en la base de datos
Ejecutar este script una vez para agregar la nueva tabla chat_memory
"""

import os
import sys

# Agregar src al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.db import connect_db

def init_memory_table():
    """Inicializar tabla de memoria si no existe"""
    
    conn = None
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Verificar si la tabla existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='chat_memory'
        """)
        
        exists = cursor.fetchone()
        
        if not exists:
            print("Creando tabla chat_memory...")
            
            # Create chat_memory table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    memory_key TEXT NOT NULL,
                    memory_value TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL,
                    UNIQUE(session_id, memory_key)
                )
            """)
            
            conn.commit()
            print("[OK] Tabla chat_memory creada exitosamente")
        else:
            print("[OK] Tabla chat_memory ya existe")
        
        # Clean up expired memories
        cursor.execute("DELETE FROM chat_memory WHERE expires_at < datetime('now')")
        deleted = cursor.rowcount
        if deleted > 0:
            print(f"🧹 Limpieza: {deleted} memoria(s) expirada(s) eliminada(s)")
        
        conn.commit()
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    init_memory_table()


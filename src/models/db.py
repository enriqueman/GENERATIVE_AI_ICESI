import sqlite3
import time
import os

# Importar traceable para instrumentar funciones de base de datos
try:
    from langsmith import traceable
    TRACEABLE_AVAILABLE = True
except ImportError:
    TRACEABLE_AVAILABLE = False
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

def connect_db():
    """Connect to SQLite database with timeout and WAL mode"""
    # Obtener el directorio base del proyecto (dos niveles arriba desde src/models/)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, "doc_sage.sqlite")
    conn = sqlite3.connect(db_path, timeout=30.0)
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=1000")
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn

def init_database():
    """Initialize all database tables"""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Create 'chat' table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create 'sources' table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            source_text TEXT,
            type TEXT DEFAULT "document",
            chat_id INTEGER,
            FOREIGN KEY (chat_id) REFERENCES chat(id)
        )
    """)
    
    # Create 'messages' table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            sender TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(chat_id) REFERENCES chat(id)
        );
    """)
    
    # Create admin_users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES admin_users(id)
        )
    """)
    
    # Create tickets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT UNIQUE NOT NULL,
            tipo TEXT NOT NULL,
            estado TEXT DEFAULT 'abierto',
            prioridad TEXT DEFAULT 'normal',
            titulo TEXT NOT NULL,
            descripcion TEXT,
            cliente_email TEXT,
            cliente_nombre TEXT,
            cliente_telefono TEXT,
            producto_id TEXT,
            factura_numero TEXT,
            fecha_devolucion TEXT,
            motivo_devolucion TEXT,
            numero_seguimiento TEXT,
            guia_seguimiento TEXT,
            cantidad INTEGER DEFAULT 1,
            total DECIMAL(10, 2),
            notas TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            resolved_at DATETIME
        )
    """)
    
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
    
    # Create google_auth table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS google_auth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            google_id TEXT UNIQUE NOT NULL,
            name TEXT,
            picture_url TEXT,
            email_verified BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    """)
    
    # Create otp_codes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            used BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create chat_users table for public chat authentication
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT,
            authenticated BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
    """)
    
    # Create chat_sessions table for managing chat user sessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            expires_at DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES chat_users(id)
        )
    """)
    
    # Create interview_questions table for storing interview questions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT UNIQUE NOT NULL,
            question TEXT NOT NULL,
            field TEXT NOT NULL,
            field_secondary TEXT,
            validation TEXT NOT NULL,
            required BOOLEAN DEFAULT 1,
            category TEXT,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1
        )
    """)
    
    # Create 'posgrado_programs' table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posgrado_programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_name TEXT NOT NULL,
            program_type TEXT,
            description TEXT,
            areas_tematicas TEXT,
            requisitos TEXT,
            modalidad TEXT,
            duracion TEXT,
            inversion TEXT,
            source_file TEXT,
            source_type TEXT DEFAULT 'document',
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            active BOOLEAN DEFAULT 1,
            loaded_to_rag BOOLEAN DEFAULT 0
        )
    """)
    
    # Initialize default chats if they don't exist
    cursor.execute("SELECT COUNT(*) FROM chat")
    if cursor.fetchone()[0] == 0:
        # Create system chat (ID=1) for knowledge base
        cursor.execute("INSERT INTO chat (id, title) VALUES (1, 'Sistema - Base de Conocimiento')")
        # Create public chat (ID=2) for customer queries
        cursor.execute("INSERT INTO chat (id, title) VALUES (2, 'Chat Público - Clientes')")
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

# CRUD Operations for 'chat' table
def create_chat(title):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO chat (title) VALUES (?)", (title,))
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return chat_id

def list_chats():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat ORDER BY created_at DESC")
    chats = cursor.fetchall()
    conn.close()
    return chats

def read_chat(chat_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM chat WHERE id = ?", (chat_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_chat(chat_id, new_title):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE chat SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (new_title, chat_id),
    )
    conn.commit()
    conn.close()

def delete_chat(chat_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat WHERE id = ?", (chat_id,))
    conn.commit()
    conn.close()

# CRUD Operations for 'sources' table
def create_source(name, source_text, chat_id, source_type="document"):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sources (name, source_text, chat_id, type) VALUES (?, ?, ?, ?)",
        (name, source_text, chat_id, source_type),
    )
    conn.commit()
    conn.close()

def read_source(source_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sources WHERE id = ?", (source_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_source(source_id, new_name, new_source_text):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sources SET name = ?, source_text = ? WHERE id = ?",
        (new_name, new_source_text, source_id),
    )
    conn.commit()
    conn.close()

def list_sources(chat_id, source_type=None):
    conn = connect_db()
    cursor = conn.cursor()
    if source_type:
        cursor.execute(
            "SELECT * FROM sources WHERE chat_id = ? AND type = ?",
            (chat_id, source_type),
        )
    else:
        cursor.execute("SELECT * FROM sources WHERE chat_id = ?", (chat_id,))
    sources = cursor.fetchall()
    conn.close()
    return sources

def delete_source(source_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sources WHERE id = ?", (source_id,))
    conn.commit()
    conn.close()

# CRUD Operations for 'messages' table
def create_message(chat_id, sender, content):
    conn = None
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (chat_id, sender, content) VALUES (?, ?, ?)",
                (chat_id, sender, content),
            )
            conn.commit()
            return True
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and retry_count < max_retries - 1:
                retry_count += 1
                print(f"Database locked, retrying... ({retry_count}/{max_retries})")
                if conn:
                    conn.close()
                time.sleep(0.1 * retry_count)  # Exponential backoff
                continue
            else:
                print(f"Error creating message: {e}")
                if conn:
                    conn.rollback()
                return False
        except Exception as e:
            print(f"Error creating message: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
        break
    
    return False

def get_messages(chat_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sender, content FROM messages WHERE chat_id = ? ORDER BY timestamp ASC",
        (chat_id,),
    )
    messages = cursor.fetchall()
    conn.close()
    return messages

def delete_messages(chat_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

# CRUD Operations for 'tickets' table
def generate_ticket_number():
    """Generate a unique ticket number"""
    import uuid
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8].upper()
    return f"TKT-{timestamp}-{unique_id}"

def create_ticket(
    tipo: str,
    titulo: str,
    descripcion: str = None,
    cliente_email: str = None,
    cliente_nombre: str = None,
    cliente_telefono: str = None,
    producto_id: str = None,
    factura_numero: str = None,
    cantidad: int = 1,
    total: float = None,
    prioridad: str = "normal",
    estado: str = "abierto",
    **kwargs
):
    """Create a new ticket"""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Generate unique ticket number
    ticket_number = generate_ticket_number()
    
    # Prepare all fields
    fields = {
        "ticket_number": ticket_number,
        "tipo": tipo,
        "estado": estado,
        "prioridad": prioridad,
        "titulo": titulo,
        "descripcion": descripcion,
        "cliente_email": cliente_email,
        "cliente_nombre": cliente_nombre,
        "cliente_telefono": cliente_telefono,
        "producto_id": producto_id,
        "factura_numero": factura_numero,
        "cantidad": cantidad,
        "total": total,
        "fecha_devolucion": kwargs.get("fecha_devolucion"),
        "motivo_devolucion": kwargs.get("motivo_devolucion"),
        "numero_seguimiento": kwargs.get("numero_seguimiento"),
        "guia_seguimiento": kwargs.get("guia_seguimiento"),
        "notas": kwargs.get("notas")
    }
    
    # Filter out None values and build query
    filtered_fields = {k: v for k, v in fields.items() if v is not None}
    columns = ", ".join(filtered_fields.keys())
    placeholders = ", ".join(["?"] * len(filtered_fields))
    values = tuple(filtered_fields.values())
    
    cursor.execute(f"INSERT INTO tickets ({columns}) VALUES ({placeholders})", values)
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": ticket_id, "ticket_number": ticket_number}

def get_ticket(ticket_number):
    """Get a ticket by ticket number"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE ticket_number = ?", (ticket_number,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, result))
    return None

def get_ticket_by_id(ticket_id):
    """Get a ticket by ID"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, result))
    return None

def list_tickets(tipo=None, estado=None, cliente_email=None):
    """List tickets with optional filters"""
    conn = connect_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tickets WHERE 1=1"
    params = []
    
    if tipo:
        query += " AND tipo = ?"
        params.append(tipo)
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if cliente_email:
        query += " AND cliente_email = ?"
        params.append(cliente_email)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    conn.close()
    
    # Convert to list of dicts
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in results]

def update_ticket(ticket_number, **kwargs):
    """Update a ticket"""
    conn = connect_db()
    cursor = conn.cursor()
    
    # Filter valid fields
    valid_fields = [
        "tipo", "estado", "prioridad", "titulo", "descripcion",
        "cliente_email", "cliente_nombre", "cliente_telefono",
        "producto_id", "factura_numero", "cantidad", "total",
        "fecha_devolucion", "motivo_devolucion", "numero_seguimiento",
        "guia_seguimiento", "notas", "resolved_at"
    ]
    
    filtered_updates = {k: v for k, v in kwargs.items() if k in valid_fields and v is not None}
    
    if not filtered_updates:
        conn.close()
        return False
    
    # Add updated_at
    filtered_updates["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    
    set_clause = ", ".join([f"{k} = ?" for k in filtered_updates.keys()])
    values = list(filtered_updates.values()) + [ticket_number]
    
    cursor.execute(f"UPDATE tickets SET {set_clause} WHERE ticket_number = ?", values)
    conn.commit()
    conn.close()
    return cursor.rowcount > 0

def delete_ticket(ticket_number):
    """Delete a ticket"""
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tickets WHERE ticket_number = ?", (ticket_number,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# CRUD Operations for 'chat_memory' table
def store_memory(session_id: str, memory_key: str, memory_value: str, ttl_minutes: int = 5) -> bool:
    """
    Store a memory with TTL
    
    Args:
        session_id: Session identifier
        memory_key: Key for the memory
        memory_value: Value to store
        ttl_minutes: Time to live in minutes (default: 5)
        
    Returns:
        bool: True if successful
    """
    from datetime import datetime, timedelta
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # Calculate expiration time
    expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
    
    try:
        # Use INSERT OR REPLACE to handle duplicates
        cursor.execute("""
            INSERT OR REPLACE INTO chat_memory (session_id, memory_key, memory_value, expires_at)
            VALUES (?, ?, ?, ?)
        """, (session_id, memory_key, memory_value, expires_at.isoformat()))
        
        conn.commit()
        success = True
    except Exception as e:
        print(f"Error storing memory: {e}")
        conn.rollback()
        success = False
    finally:
        conn.close()
    
    return success

def get_memory(session_id: str, memory_key: str = None) -> dict:
    """
    Retrieve memory(ies) for a session
    
    Args:
        session_id: Session identifier
        memory_key: Specific key to retrieve (optional)
        
    Returns:
        dict: Memory value(s)
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # First, clean up expired memories
        cursor.execute("DELETE FROM chat_memory WHERE expires_at < datetime('now')")
        
        # Retrieve memories
        if memory_key:
            cursor.execute("""
                SELECT memory_key, memory_value 
                FROM chat_memory 
                WHERE session_id = ? AND memory_key = ? AND expires_at >= datetime('now')
            """, (session_id, memory_key))
        else:
            cursor.execute("""
                SELECT memory_key, memory_value 
                FROM chat_memory 
                WHERE session_id = ? AND expires_at >= datetime('now')
            """, (session_id,))
        
        rows = cursor.fetchall()
        
        # If specific key requested, return just the value
        if memory_key and rows:
            return rows[0][1]  # memory_value
        
        # Otherwise return all as dict
        memories = {row[0]: row[1] for row in rows}
        
        conn.commit()
        return memories
        
    except Exception as e:
        print(f"Error retrieving memory: {e}")
        return {}
    finally:
        conn.close()

def delete_memory(session_id: str, memory_key: str = None) -> bool:
    """
    Delete memory(ies) for a session
    
    Args:
        session_id: Session identifier
        memory_key: Specific key to delete (optional, if None deletes all)
        
    Returns:
        bool: True if successful
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        if memory_key:
            cursor.execute("DELETE FROM chat_memory WHERE session_id = ? AND memory_key = ?", 
                         (session_id, memory_key))
        else:
            cursor.execute("DELETE FROM chat_memory WHERE session_id = ?", (session_id,))
        
        conn.commit()
        deleted = cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting memory: {e}")
        conn.rollback()
        deleted = False
    finally:
        conn.close()
    
    return deleted

def cleanup_expired_memories():
    """Remove expired memories from the database"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM chat_memory WHERE expires_at < datetime('now')")
        conn.commit()
        deleted = cursor.rowcount
        return deleted
    except Exception as e:
        print(f"Error cleaning up memories: {e}")
        return 0
    finally:
        conn.close()

# CRUD Operations for 'chat_users' table
def create_chat_user(email: str, name: str = None) -> dict:
    """Create a new chat user or return existing user"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT id, email, name, authenticated FROM chat_users WHERE email = ?", (email,))
        existing = cursor.fetchone()
        
        if existing:
            user_id = existing[0]
            # Update name if provided and different
            if name and name != existing[2]:
                cursor.execute("UPDATE chat_users SET name = ? WHERE id = ?", (name, user_id))
                conn.commit()
            return {
                "id": user_id,
                "email": existing[1],
                "name": name or existing[2],
                "authenticated": bool(existing[3])
            }
        else:
            # Create new user
            cursor.execute(
                "INSERT INTO chat_users (email, name) VALUES (?, ?)",
                (email, name)
            )
            user_id = cursor.lastrowid
            conn.commit()
            return {
                "id": user_id,
                "email": email,
                "name": name,
                "authenticated": False
            }
    except Exception as e:
        print(f"Error creating chat user: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_chat_user_by_email(email: str) -> dict:
    """Get chat user by email"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT id, email, name, authenticated, created_at, last_login FROM chat_users WHERE email = ?",
            (email,)
        )
        result = cursor.fetchone()
        
        if result:
            return {
                "id": result[0],
                "email": result[1],
                "name": result[2],
                "authenticated": bool(result[3]),
                "created_at": result[4],
                "last_login": result[5]
            }
        return None
    except Exception as e:
        print(f"Error getting chat user: {e}")
        return None
    finally:
        conn.close()

def mark_chat_user_authenticated(email: str) -> bool:
    """Mark chat user as authenticated"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        from datetime import datetime
        cursor.execute("""
            UPDATE chat_users 
            SET authenticated = 1, last_login = ? 
            WHERE email = ?
        """, (datetime.now().isoformat(), email))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error marking user as authenticated: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def create_chat_session(user_id: int, expires_in_hours: int = 24) -> str:
    """Create a session token for chat user"""
    import secrets
    from datetime import datetime, timedelta
    
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        session_token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        cursor.execute(
            "INSERT INTO chat_sessions (user_id, session_token, expires_at) VALUES (?, ?, ?)",
            (user_id, session_token, expires_at.isoformat())
        )
        conn.commit()
        return session_token
    except Exception as e:
        print(f"Error creating chat session: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def verify_chat_session(session_token: str) -> dict:
    """Verify if chat session is valid"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT cs.user_id, cu.email, cu.name, cu.authenticated, cs.expires_at
            FROM chat_sessions cs
            JOIN chat_users cu ON cs.user_id = cu.id
            WHERE cs.session_token = ?
        """, (session_token,))
        
        result = cursor.fetchone()
        
        if result:
            from datetime import datetime
            expires_at = datetime.fromisoformat(result[4])
            if expires_at > datetime.now():
                return {
                    "id": result[0],
                    "email": result[1],
                    "name": result[2],
                    "authenticated": bool(result[3])
                }
        return None
    except Exception as e:
        print(f"Error verifying chat session: {e}")
        return None
    finally:
        conn.close()

# CRUD Operations for 'interview_questions' table
def create_interview_question(
    question_id: str,
    question: str,
    field: str,
    field_secondary: str = None,
    validation: str = "text",
    required: bool = True,
    category: str = None,
    metadata: str = None
) -> dict:
    """Create a new interview question"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO interview_questions 
            (question_id, question, field, field_secondary, validation, required, category, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (question_id, question, field, field_secondary, validation, required, category, metadata))
        
        conn.commit()
        question_db_id = cursor.lastrowid
        
        return {
            "id": question_db_id,
            "question_id": question_id,
            "question": question,
            "field": field,
            "field_secondary": field_secondary,
            "validation": validation,
            "required": required,
            "category": category,
            "metadata": metadata
        }
    except sqlite3.IntegrityError:
        # If question_id already exists, update instead
        return update_interview_question(question_id, question, field, field_secondary, validation, required, category, metadata)
    except Exception as e:
        print(f"Error creating interview question: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_interview_question(question_id: str = None, active_only: bool = True) -> list:
    """Get interview question(s)"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        if question_id:
            query = "SELECT * FROM interview_questions WHERE question_id = ?"
            params = (question_id,)
            if active_only:
                query += " AND active = 1"
            cursor.execute(query, params)
            result = cursor.fetchone()
            
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
            return None
        else:
            query = "SELECT * FROM interview_questions"
            if active_only:
                query += " WHERE active = 1"
            query += " ORDER BY created_at ASC"
            cursor.execute(query)
            results = cursor.fetchall()
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in results]
    except Exception as e:
        print(f"Error getting interview question: {e}")
        return []
    finally:
        conn.close()

def update_interview_question(
    question_id: str,
    question: str = None,
    field: str = None,
    field_secondary: str = None,
    validation: str = None,
    required: bool = None,
    category: str = None,
    metadata: str = None
) -> dict:
    """Update an interview question"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if question is not None:
            updates.append("question = ?")
            params.append(question)
        if field is not None:
            updates.append("field = ?")
            params.append(field)
        if field_secondary is not None:
            updates.append("field_secondary = ?")
            params.append(field_secondary)
        if validation is not None:
            updates.append("validation = ?")
            params.append(validation)
        if required is not None:
            updates.append("required = ?")
            params.append(required)
        if category is not None:
            updates.append("category = ?")
            params.append(category)
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(metadata)
        
        if not updates:
            return None
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(question_id)
        
        query = f"UPDATE interview_questions SET {', '.join(updates)} WHERE question_id = ?"
        cursor.execute(query, params)
        conn.commit()
        
        if cursor.rowcount > 0:
            return get_interview_question(question_id)
        return None
    except Exception as e:
        print(f"Error updating interview question: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

# CRUD Operations for 'posgrado_programs' table
@traceable(name="DB.create_posgrado_program")
def create_posgrado_program(
    program_name: str,
    program_type: str = None,
    description: str = None,
    areas_tematicas: str = None,
    requisitos: str = None,
    modalidad: str = None,
    duracion: str = None,
    inversion: str = None,
    source_file: str = None,
    source_type: str = "document",
    metadata: str = None,
    active: bool = True
) -> int:
    """
    Crear un nuevo programa de posgrado en la base de datos.
    
    Args:
        program_name: Nombre del programa
        program_type: Tipo (maestría, especialización, MBA, etc.)
        description: Descripción del programa
        areas_tematicas: Áreas temáticas (JSON string o texto)
        requisitos: Requisitos del programa
        modalidad: Modalidad (presencial, virtual, híbrida)
        duracion: Duración del programa
        inversion: Inversión aproximada
        source_file: Archivo fuente del programa
        source_type: Tipo de fuente (document, manual)
        metadata: Metadata adicional (JSON string)
        active: Si el programa está activo
    
    Returns:
        ID del programa creado
    """
    import json
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # Convertir metadata a JSON string si es dict
    if metadata and isinstance(metadata, dict):
        metadata = json.dumps(metadata, ensure_ascii=False)
    elif metadata is None:
        metadata = None
    
    # Convertir areas_tematicas a string si es lista
    # Convertir areas_tematicas a string si es lista
    if areas_tematicas is not None:
        if isinstance(areas_tematicas, list):
            areas_tematicas = ", ".join([str(a).strip() for a in areas_tematicas if a])
        elif not isinstance(areas_tematicas, str):
            areas_tematicas = str(areas_tematicas) if areas_tematicas else None
    else:
        areas_tematicas = None
    
    # Asegurar que todos los campos sean strings o None
    program_name = str(program_name) if program_name else None
    program_type = str(program_type) if program_type else None
    description = str(description) if description else None
    requisitos = str(requisitos) if requisitos else None
    modalidad = str(modalidad) if modalidad else None
    duracion = str(duracion) if duracion else None
    inversion = str(inversion) if inversion else None
    source_file = str(source_file) if source_file else None
    source_type = str(source_type) if source_type else "document"
    
    try:
        cursor.execute("""
            INSERT INTO posgrado_programs (
                program_name, program_type, description, areas_tematicas,
                requisitos, modalidad, duracion, inversion, source_file,
                source_type, metadata, active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            program_name, program_type, description, areas_tematicas,
            requisitos, modalidad, duracion, inversion, source_file,
            source_type, metadata, 1 if active else 0
        ))
        
        program_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return program_id
    except sqlite3.IntegrityError as e:
        conn.close()
        raise Exception(f"Error creando programa: {str(e)}")


@traceable(name="DB.get_posgrado_program")
def get_posgrado_program(program_id: int = None, program_name: str = None, active_only: bool = True) -> list:
    """
    Obtener programa(s) de posgrado de la base de datos.
    
    Args:
        program_id: ID del programa (opcional)
        program_name: Nombre del programa (opcional)
        active_only: Solo programas activos
    
    Returns:
        Lista de programas (como diccionarios)
    """
    import json
    
    conn = connect_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM posgrado_programs WHERE 1=1"
    params = []
    
    if program_id:
        query += " AND id = ?"
        params.append(program_id)
    
    if program_name:
        query += " AND program_name = ?"
        params.append(program_name)
    
    if active_only:
        query += " AND active = 1"
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    # Convertir a diccionarios
    columns = [
        'id', 'program_name', 'program_type', 'description', 'areas_tematicas',
        'requisitos', 'modalidad', 'duracion', 'inversion', 'source_file',
        'source_type', 'metadata', 'created_at', 'updated_at', 'active', 'loaded_to_rag'
    ]
    
    programs = []
    for row in rows:
        program = dict(zip(columns, row))
        
        # Parsear metadata si existe
        if program['metadata']:
            try:
                program['metadata'] = json.loads(program['metadata'])
            except:
                pass
        
        programs.append(program)
    
    return programs


@traceable(name="DB.list_posgrado_programs")
def list_posgrado_programs(active_only: bool = True) -> list:
    """
    Listar todos los programas de posgrado.
    
    Args:
        active_only: Solo programas activos
    
    Returns:
        Lista de programas
    """
    return get_posgrado_program(active_only=active_only)


def update_posgrado_program(
    program_id: int,
    program_name: str = None,
    program_type: str = None,
    description: str = None,
    areas_tematicas: str = None,
    requisitos: str = None,
    modalidad: str = None,
    duracion: str = None,
    inversion: str = None,
    metadata: str = None,
    active: bool = None,
    loaded_to_rag: bool = None
) -> bool:
    """
    Actualizar un programa de posgrado.
    
    Args:
        program_id: ID del programa
        ... (otros campos opcionales)
    
    Returns:
        True si se actualizó exitosamente
    """
    import json
    
    conn = connect_db()
    cursor = conn.cursor()
    
    updates = []
    params = []
    
    if program_name is not None:
        updates.append("program_name = ?")
        params.append(program_name)
    
    if program_type is not None:
        updates.append("program_type = ?")
        params.append(program_type)
    
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    
    if areas_tematicas is not None:
        # Convertir lista a string si es necesario
        if isinstance(areas_tematicas, list):
            areas_tematicas = ", ".join([str(a).strip() for a in areas_tematicas if a])
        elif not isinstance(areas_tematicas, str):
            areas_tematicas = str(areas_tematicas) if areas_tematicas else None
        updates.append("areas_tematicas = ?")
        params.append(areas_tematicas)
    
    if requisitos is not None:
        # Convertir a string si no lo es
        if not isinstance(requisitos, str):
            requisitos = str(requisitos) if requisitos else None
        updates.append("requisitos = ?")
        params.append(requisitos)
    
    if modalidad is not None:
        # Convertir a string si no lo es
        if not isinstance(modalidad, str):
            modalidad = str(modalidad) if modalidad else None
        updates.append("modalidad = ?")
        params.append(modalidad)
    
    if duracion is not None:
        # Convertir a string si no lo es
        if not isinstance(duracion, str):
            duracion = str(duracion) if duracion else None
        updates.append("duracion = ?")
        params.append(duracion)
    
    if inversion is not None:
        # Convertir a string si no lo es
        if not isinstance(inversion, str):
            inversion = str(inversion) if inversion else None
        updates.append("inversion = ?")
        params.append(inversion)
    
    if metadata is not None:
        if isinstance(metadata, dict):
            metadata = json.dumps(metadata, ensure_ascii=False)
        elif not isinstance(metadata, str):
            metadata = str(metadata) if metadata else None
        updates.append("metadata = ?")
        params.append(metadata)
    
    if active is not None:
        updates.append("active = ?")
        params.append(1 if active else 0)
    
    if loaded_to_rag is not None:
        updates.append("loaded_to_rag = ?")
        params.append(1 if loaded_to_rag else 0)
    
    if not updates:
        conn.close()
        return False
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(program_id)
    
    query = f"UPDATE posgrado_programs SET {', '.join(updates)} WHERE id = ?"
    
    try:
        cursor.execute(query, params)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"[ERROR] Error updating program: {e}")
        return False


def delete_posgrado_program(program_id: int, soft_delete: bool = True) -> bool:
    """
    Eliminar un programa de posgrado.
    
    Args:
        program_id: ID del programa
        soft_delete: Si True, solo marca como inactivo (default: True)
    
    Returns:
        True si se eliminó exitosamente
    """
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        if soft_delete:
            cursor.execute(
                "UPDATE posgrado_programs SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (program_id,)
            )
        else:
            cursor.execute("DELETE FROM posgrado_programs WHERE id = ?", (program_id,))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        conn.close()
        print(f"[ERROR] Error deleting program: {e}")
        return False


def delete_interview_question(question_id: str, soft_delete: bool = True) -> bool:
    """Delete an interview question (soft delete by default)"""
    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        if soft_delete:
            cursor.execute("""
                UPDATE interview_questions 
                SET active = 0, updated_at = CURRENT_TIMESTAMP 
                WHERE question_id = ?
            """, (question_id,))
        else:
            cursor.execute("DELETE FROM interview_questions WHERE question_id = ?", (question_id,))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting interview question: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()
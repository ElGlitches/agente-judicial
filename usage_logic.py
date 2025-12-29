import sqlite3
import streamlit as st

DB_PATH = "saas.db"
FREE_LIMIT = 3

def init_usage_db():
    """Inicializa la DB si no existe."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Tabla USAGE
    c.execute('''CREATE TABLE IF NOT EXISTS users_usage
                 (username TEXT PRIMARY KEY, 
                  generations_count INTEGER DEFAULT 0, 
                  is_pro INTEGER DEFAULT 0)''')
    
    # Tabla USERS (Auth)
    c.execute('''CREATE TABLE IF NOT EXISTS users_auth
                 (username TEXT PRIMARY KEY, 
                  password_text TEXT, 
                  name TEXT,
                  email TEXT)''')
    
    # Usuario Admin por defecto (si no existe)
    c.execute("SELECT * FROM users_auth WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users_auth (username, password_text, name, email) VALUES (?, ?, ?, ?)", 
                  ('admin', 'admin123', 'Administrador', 'admin@legal.cl'))
                  
    conn.commit()
    conn.close()

# --- HELPER DE MIGRACION ---
# (Si quisieras borrar tablas antiguas: os.remove(DB_PATH))

# --- AUTH FUNCTIONS ---
def verify_login(username, password):
    """
    Simula verificación de hash. 
    En producción usar bcrypt.checkpw(password.encode(), stored_hash).
    Aquí comparamos texto plano por simplicidad del requerimiento MVP, 
    pero la arquitectura soporta hash facilmente.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT password_text, name FROM users_auth WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    
    if row:
        stored_password, name = row
        if stored_password == password:
            return True, name
    return False, None

def register_user_db(username, password, name, email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users_auth (username, password_text, name, email) VALUES (?, ?, ?, ?)", 
                  (username, password, name, email))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

# --- USAGE FUNCTIONS ---
def get_user_status(username):
    """Retorna (count, is_pro)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT generations_count, is_pro FROM users_usage WHERE username=?", (username,))
    row = c.fetchone()
    
    if row:
        return row[0], bool(row[1])
    else:
        # Si existe en Auth pero no en Usage, lo creamos
        c.execute("INSERT INTO users_usage (username, generations_count, is_pro) VALUES (?, 0, 0)", (username,))
        conn.commit()
        return 0, False
    conn.close()

def log_generation(username):
    """Incrementa el contador."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE users_usage SET generations_count = generations_count + 1 WHERE username=?", (username,))
    conn.commit()
    conn.close()

def check_can_generate(username):
    """
    Retorna True si puede generar.
    Retorna False si alcanzó límite y no es pro.
    """
    count, is_pro = get_user_status(username)
    if is_pro:
        return True, "PRO"
    
    if count < FREE_LIMIT:
        return True, f"{count}/{FREE_LIMIT}"
    else:
        return False, "LIMIT_REACHED"

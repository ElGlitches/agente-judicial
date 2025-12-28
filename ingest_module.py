
import os
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
import docx2txt
from docx import Document
from pypdf import PdfReader

load_dotenv()

# --- CONFIGURACIÓN ---
DB_URL = "postgresql://admin:admin@localhost:5432/pjud_db"
DOCS_FOLDER = "./docs/"

def run_ingestion():
    """
    Escanea la carpeta DOCS_FOLDER y regenera la base de datos vectorial.
    Retorna un string con el resumen del proceso.
    """
    log_messages = []
    
    def log(msg):
        print(msg)
        log_messages.append(msg)

    try:
        # 1. Conexión y Limpieza de Tabla
        log("🔌 Conectando a Base de Datos...")
        # Nota: Usamos autocommit=True para operaciones DDL (DROP/CREATE)
        with psycopg.connect(DB_URL, autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.execute("DROP TABLE IF EXISTS escritos")
            conn.execute("""
                CREATE TABLE escritos (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    filename TEXT,
                    chunk_index INTEGER,
                    embedding vector(384)
                )
            """)
        log("✅ Base de datos limpiada y estructurada (v2).")

        # 2. Cargar Modelo
        # Usamos caché de Streamlit en app.py, pero aquí cargamos fresco o podríamos reusar si pasamos el modelo.
        # Para simplificar y aislar, cargamos aquí. Es rápido 'all-MiniLM-L6-v2'.
        log("🧠 Cargando modelo neuronal...")
        model = SentenceTransformer('all-MiniLM-L6-v2')

        # 3. Procesar Archivos
        log(f"📂 Escaneando carpeta {DOCS_FOLDER}...")
        
        if not os.path.exists(DOCS_FOLDER):
            os.makedirs(DOCS_FOLDER)
            log(f"⚠️ Carpeta creada. Estaba vacía.")

        files = [f for f in os.listdir(DOCS_FOLDER) if not f.startswith(".")]
        if not files:
            return "⚠️ No hay archivos en la carpeta 'docs/'. Agrega archivos y reintenta."

        processed_count = 0
        
        # Reconectamos para insertar
        with psycopg.connect(DB_URL) as conn:
            register_vector(conn)
            
            for filename in files:
                file_path = os.path.join(DOCS_FOLDER, filename)
                raw_text = ""

                try:
                    # Detectar tipo
                    if filename.lower().endswith(".docx"):
                        # Intentar primero con python-docx (mejor calidad a veces) o docx2txt
                        try:
                            doc = Document(file_path)
                            raw_text = "\n".join([p.text for p in doc.paragraphs])
                        except:
                            raw_text = docx2txt.process(file_path)
                            
                    elif filename.lower().endswith(".doc"):
                         log(f"⚠️ SALTADO: {filename} (Formato .doc antiguo no soportado, convierte a .docx)")
                         continue
                         
                    elif filename.lower().endswith(".pdf"):
                        reader = PdfReader(file_path)
                        for page in reader.pages:
                            raw_text += page.extract_text() + "\n"
                    else:
                        log(f"⚠️ SALTADO: {filename} (Formato desconocido)")
                        continue
                    
                    if raw_text:
                        # Insertar nombre de archivo como metadato clave en el texto tambien
                        text_with_meta = f"[[NOMBRE ARCHIVO: {filename}]]\n\n" + raw_text
                        
                        # Chunks
                        chunks = [text_with_meta[i:i+1000] for i in range(0, len(text_with_meta), 900)]
                        
                        for idx, chunk in enumerate(chunks):
                            vector = model.encode(chunk).tolist()
                            conn.execute(
                                "INSERT INTO escritos (content, filename, chunk_index, embedding) VALUES (%s, %s, %s, %s)",
                                (chunk, filename, idx, vector)
                            )
                        
                        log(f"   - ✅ {filename} ({len(chunks)} fragmentos)")
                        processed_count += 1
                        
                except Exception as e:
                    log(f"❌ Error en {filename}: {e}")

        conn.close()
        return "\n".join(log_messages) + f"\n\n🎉 ¡Listo! {processed_count} documentos procesados (Modo Estructurado v2)."

    except Exception as e:
        return f"❌ Error Crítico: {e}"

if __name__ == "__main__":
    print(run_ingestion())

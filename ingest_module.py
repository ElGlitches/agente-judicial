
import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import docx2txt
from docx import Document
from pypdf import PdfReader

load_dotenv()

# --- CONFIGURACIÓN ---
CHROMA_PATH = "chroma_db"
DOCS_FOLDER = "./docs/"

def run_ingestion():
    """
    Escanea la carpeta DOCS_FOLDER y regenera la base de datos vectorial local (ChromaDB).
    Retorna un string con el resumen del proceso.
    """
    log_messages = []
    
    def log(msg):
        print(msg)
        log_messages.append(msg)

    try:
        # 1. Inicializar Cliente Chroma (Persistente)
        log(f"🧠 Inicializando ChromaDB en '{CHROMA_PATH}'...")
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        
        # 2. Configurar Función de Embeddings
        # Usamos la misma 'all-MiniLM-L6-v2' que es estándar y ligera
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # 3. Resetear Colección (Borrar anterior y crear nueva)
        collection_name = "escritos_judiciales"
        try:
            client.delete_collection(name=collection_name)
            log("🗑️ Colección anterior eliminada.")
        except Exception:
            pass # No existía o error irrelevante al borrar
            
        collection = client.get_or_create_collection(
            name=collection_name, 
            embedding_function=sentence_transformer_ef
        )
        log("✅ Nueva colección creada.")

        # 4. Procesar Archivos
        log(f"📂 Escaneando carpeta {DOCS_FOLDER}...")
        
        if not os.path.exists(DOCS_FOLDER):
            os.makedirs(DOCS_FOLDER)
            log(f"⚠️ Carpeta creada. Estaba vacía.")

        files = [f for f in os.listdir(DOCS_FOLDER) if not f.startswith(".")]
        if not files:
            return "⚠️ No hay archivos en la carpeta 'docs/'. Agrega archivos y reintenta."

        processed_count = 0
        
        for filename in files:
            file_path = os.path.join(DOCS_FOLDER, filename)
            raw_text = ""

            try:
                # Detectar tipo
                if filename.lower().endswith(".docx"):
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
                    # Esto ayuda al modelo a "ver" el nombre del archivo en el contexto
                    text_with_meta = f"[[NOMBRE ARCHIVO: {filename}]]\n\n" + raw_text
                    
                    # Chunks
                    chunk_size = 1000
                    overlap = 100
                    chunks = [text_with_meta[i:i+chunk_size] for i in range(0, len(text_with_meta), chunk_size - overlap)]
                    
                    # Preparar listas para batch
                    ids = [f"{filename}_{i}" for i in range(len(chunks))]
                    metadatas = [{"filename": filename, "chunk_index": i} for i in range(len(chunks))]
                    documents = chunks
                    
                    if documents:
                        collection.add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                    
                    log(f"   - ✅ {filename} ({len(chunks)} fragmentos)")
                    processed_count += 1
                    
            except Exception as e:
                log(f"❌ Error en {filename}: {e}")

        return "\n".join(log_messages) + f"\n\n🎉 ¡Listo! {processed_count} documentos procesados en ChromaDB (Sin Docker)."

    except Exception as e:
        return f"❌ Error Crítico: {e}"

if __name__ == "__main__":
    print(run_ingestion())

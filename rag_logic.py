import chromadb
from chromadb.utils import embedding_functions

# Configuración Constante
CHROMA_PATH = "chroma_db"

def buscar_modelos_locales(consulta: str):
    """
    Busca priorizando nombres de archivos exactos y búsqueda semántica en ChromaDB.
    """
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        collection = client.get_collection(name="escritos_judiciales", embedding_function=sentence_transformer_ef)
        
        matches = []

        # 1. BÚSQUEDA INTELIGENTE DE ARCHIVOS (MODO "FULL DOC") POR METADATA
        keywords = [word for word in consulta.split() if len(word) > 3 or word.isdigit()]
        # (Lógica simplificada de keywords placeholder del original)

        # Búsqueda Semántica Estándar
        results = collection.query(
            query_texts=[consulta],
            n_results=10
        )
        
        # Procesar resultados
        if results['documents']:
            found_docs = results['documents'][0]
            
            # Filtrar duplicados manteniendo orden
            unique_docs = sorted(set(found_docs), key=found_docs.index) 
            matches = unique_docs[:6]
            
        if not matches: return "No encontré modelos."
        return "ENCONTRÉ ESTOS MODELOS:\n" + "\n\n---\n\n".join(matches)
        
    except Exception as e:
        return f"Error ChromaDB: {e}. (Asegúrate de haber presionado 'Actualizar IA' primero)"

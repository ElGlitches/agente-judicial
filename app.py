import streamlit as st
import os
import io
import google.generativeai as genai
import psycopg
from pgvector.psycopg import register_vector
from dotenv import load_dotenv
from docx import Document
from tools_bcn import obtener_ley_bcn
import ingest_module  # Nuevo módulo de ingesta

# --- TRUCO ANTI-CONGELAMIENTO ---
# No importamos la IA pesada arriba, sino cuando la necesitemos
@st.cache_resource
def get_model():
    # Importación "Tardía" para que la app arranque rápido
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer('all-MiniLM-L6-v2')

load_dotenv()

st.set_page_config(page_title="Abogado IA", page_icon="⚖️")

# --- SIDEBAR: GESTIÓN DE DOCUMENTOS ---
with st.sidebar:
    st.header("📚 Biblioteca")
    st.info("Pon tus archivos .docx o .pdf en la carpeta 'docs/' o súbelos aquí:")
    
    uploaded_files = st.file_uploader("📤 Subir Nuevos Modelos", accept_multiple_files=True, type=["docx", "pdf"])
    if uploaded_files:
        if not os.path.exists("./docs/"): os.makedirs("./docs/")
        for uploaded_file in uploaded_files:
            file_path = os.path.join("./docs/", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        st.success(f"¡{len(uploaded_files)} archivo(s) guardado(s)! Ahora presiona 'Actualizar'.")
    
    if st.button("🔄 Actualizar IA con nuevos Docs"):
        with st.spinner("Leyendo y aprendiendo documentos..."):
            log_result = ingest_module.run_ingestion()
            st.success("¡Actualización Completa!")
            st.text_area("Log de Proceso:", log_result, height=200)

    st.divider()
    st.header("🤖 Configuración Cerebro")
    model_option = st.selectbox(
        "Elige tu Modelo:",
        (
            "gemini-flash-lite-latest",  # Default: El más ligero y seguro
            "gemini-flash-latest",
            "gemini-2.0-flash-lite", 
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash", 
            "gemini-2.5-flash"
        ),
        index=0, 
        help="Los modelos 'Lite' consumen menos energía y suelen funcionar cuando los grandes están ocupados."
    )

st.title(f"⚖️ Abogado IA ({model_option})")

# Configuración API
if "google_api_key" not in st.session_state:
    st.session_state.google_api_key = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=st.session_state.google_api_key)
DB_URL = "postgresql://admin:admin@localhost:5432/pjud_db"

# --- HERRAMIENTA DE BÚSQUEDA ---
def buscar_modelos_locales(consulta: str):
    """Busca priorizando nombres de archivos exactos."""
    try:
        # Cargamos el modelo AQUÍ, solo cuando se usa
        embedding_model = get_model()
        
        matches = []
        with psycopg.connect(DB_URL) as conn:
            register_vector(conn)
            cursor = conn.cursor()
            
            # 1. BÚSQUEDA INTELIGENTE DE ARCHIVOS (MODO "FULL DOC")
            print(f"DEBUG: Consultando por '{consulta}'")
            keywords = [word for word in consulta.split() if len(word) > 3 or word.isdigit()]
            print(f"DEBUG: Keywords extraídas: {keywords}")
            
            full_doc_found = False
            
            for word in keywords:
                # Si es un número o palabra clave, verificamos si machea con un FILENAME exacto
                if word.isdigit():
                    print(f"DEBUG: Verificando archivo con ID '{word}'")
                    # Intentamos encontrar el nombre exacto del archivo que contiene ese ID
                    cursor.execute("SELECT DISTINCT filename FROM escritos WHERE filename ILIKE %s LIMIT 1", (f"%{word}%",))
                    file_result = cursor.fetchone()
                    
                    if file_result:
                        target_filename = file_result[0]
                        print(f"DEBUG: ¡ARCHIVO ENCONTRADO! -> {target_filename}")
                        print("DEBUG: Recuperando documento COMPLETO (reconstrucción)...")
                        
                        # RECUPERACIÓN TOTAL: Traemos TODOS los chunks ordenados
                        cursor.execute("SELECT content FROM escritos WHERE filename = %s ORDER BY chunk_index ASC", (target_filename,))
                        all_chunks = [r[0] for r in cursor.fetchall()]
                        
                        full_document = "\n".join(all_chunks)
                        matches = [full_document] # Reemplazamos los snippets con el documento entero
                        full_doc_found = True
                        break # Ya encontramos el archivo objetivo, no buscamos más
            
            if not full_doc_found:
                print("DEBUG: No se encontró archivo específico. Usando búsqueda semántica estándar.")
                # Fallback: Búsqueda Semántica Tradicional (Vectores) si no hay ID específico
                vector = embedding_model.encode(consulta).tolist()
                cursor.execute("SELECT content FROM escritos ORDER BY embedding <=> %s::vector LIMIT 15", (vector,))
                matches.extend([r[0] for r in cursor.fetchall()])
            
        # FILTRO VIP
        prioritarios = [t for t in matches if "[[NOMBRE ARCHIVO:" in t]
        resto = [t for t in matches if "[[NOMBRE ARCHIVO:" not in t]
        
        finales = list(dict.fromkeys(prioritarios + resto))[:6]
        
        if not finales: return "No encontré modelos."
        return "ENCONTRÉ ESTOS MODELOS:\n" + "\n\n---\n\n".join(finales)
        
    except Exception as e:
        return f"Error DB: {e}"

tools_list = [buscar_modelos_locales, obtener_ley_bcn]

# --- INICIAR CHAT ---
# Reiniciar chat si cambia el modelo
if "current_model" not in st.session_state:
    st.session_state.current_model = model_option

if st.session_state.current_model != model_option:
    st.session_state.current_model = model_option
    if "chat_session" in st.session_state:
        del st.session_state.chat_session
    st.session_state.history = []
    st.rerun()

if "chat_session" not in st.session_state:
    model = genai.GenerativeModel(
        model_name=model_option,
        tools=tools_list,
        system_instruction="""Eres un Digitador Legal (No un abogado creativo).
        TU MISIÓN: Actuar como una FOTOCOPIADORA INTELIGENTE.
        
        FILOSOFÍA:
        - "El formato es sagrado". No lo mejores, no lo resumas, no cambies el estilo.
        - **PROHIBIDO REESTRUCTURAR**: Si el original usa párrafos narrativos, TÚ USAS PÁRRAFOS. No conviertas textos en listas numeradas.
        - **RESTRICCIÓN DE TEMA**: SOLO respondes solicitudes sobre redacción de escritos legales o consultas de leyes.
          - Si te preguntan "cómo estás", "chiste", "poema" o temas no jurídicos, responde: "Soy una herramienta exclusivamente jurídica."
        - **PROHIBIDO USAR MARKDOWN**: No uses asteriscos (**texto**) ni guiones bajos.
        - **PROHIBIDO HABLAR**: Tu respuesta debe contener EXCLUSIVAMENTE el texto del escrito legal (o la respuesta jurídica directa).

        PASOS OBLIGATORIOS:
        1. ANALIZAR TEMA: ¿Es sobre redactar un escrito o consultar una Ley?
           - SI: Procede.
           - NO: Ignora y responde con el mensaje de error estándar.
        2. ANALIZAR DATOS: Lee atentamente el mensaje del usuario. ¿Ya te dio los nombres, RUTs, domicilio? ¡ÚSALOS!
        3. BUSCAR: Usa 'buscar_modelos_locales'.
        4. COPIAR ESTRUCTURA: Si encuentras un archivo '[[NOMBRE ARCHIVO: ...]]', debes replicar EXACTAMENTE su redacción y tono.
           - **REGLA DE ORO**: MANTÉN LA FORMA, CAMBIA EL FONDO.
           - Si el archivo cuenta una historia en párrafos ("Nuestro matrimonio fue..."), tú TAMBIÉN usa párrafos.
           - PEGA la nueva historia del usuario (fechas, hechos nuevos) usando ESE MISMO ESTILO de redacción.
           - ¡NO RESUMAS la historia en puntos (1, 2, 3) si el original no lo hace!
        5. SI FALTAN DATOS (CRÍTICO):
           - SOLO si el usuario NO te dio los datos en su mensaje, entonces PÍDELOS.
           - Si ya están ahí, NO PREGUNTES, simplemente REDACTA.
        6. VALIDAR DERECHO (OBLIGATORIO):
           - Si el escrito cita artículos o leyes, usa `obtener_ley_bcn` para verificar.
        """
    )
    st.session_state.chat_session = model.start_chat(enable_automatic_function_calling=True)
    st.session_state.history = []

# --- FICHA DEL CASO (FORMULARIO) ---
with st.expander("📝 Ficha del Caso (Generador Automático)", expanded=False):
    st.caption("Llena estos datos para generar una demanda sin errores.")
    col1, col2 = st.columns(2)
    with col1:
        tribunal = st.text_input("Tribunal", placeholder="Ej: 1º Juzgado de Familia de Santiago")
        materia = st.text_input("Materia", placeholder="Ej: Alimentos Menores")
        nombre_dte = st.text_input("Demandante (Nombre)", placeholder="Juan Pérez")
        rut_dte = st.text_input("Demandante (RUT)", placeholder="11.111.111-1")
        abogado = st.text_input("Abogado Patrocinante", placeholder="Tu Nombre")
        
    with col2:
        nombre_ddo = st.text_input("Demandado (Nombre)", placeholder="Pedro González")
        rut_ddo = st.text_input("Demandado (RUT)", placeholder="22.222.222-2")
        domicilio = st.text_input("Domicilio Demandado", placeholder="Calle Falsa 123, Santiago")
        otros_datos = st.text_area("Otros Hechos / Historia", placeholder="La relación comenzó el año... (Pegar hechos aquí)", height=100)

    # Selector de Documentos Dinámico
    docs_path = "./docs/"
    if not os.path.exists(docs_path): os.makedirs(docs_path)
    available_docs = ["Selección Inteligente (Buscar por tema)"] + [f for f in os.listdir(docs_path) if not f.startswith(".")]
    selected_doc = st.selectbox("📌 Plantilla Base:", available_docs)

    if st.button("✨ Redactar Escrito", type="primary"):
        # Construcción del Prompt Estructurado
        doc_instruction = ""
        if selected_doc != "Selección Inteligente (Buscar por tema)":
            doc_instruction = f"Basa tu redacción EXACTAMENTE en el formato del archivo '[[NOMBRE ARCHIVO: {selected_doc}]]'."
        else:
            doc_instruction = "Busca en la base de datos el modelo más apropiado para esta materia."
        
        full_prompt = f"""Redacta una demanda de: {materia}
        Tribunal: {tribunal}
        {doc_instruction}
        
        DATOS DE LAS PARTES:
        - Demandante: {nombre_dte}, RUT {rut_dte}. Abogado: {abogado}.
        - Demandado: {nombre_ddo}, RUT {rut_ddo}. Domicilio: {domicilio}.
        
        HECHOS / HISTORIA:
        {otros_datos}
        
        INSTRUCCIÓN:
        1. Rellena el formato seleccionado con estos datos.
        2. Mantén el tono narrativo y estilo del original.
        """
        
        # Inyectar al Chat
        st.session_state.history.append({"role": "user", "text": full_prompt})
        
        with st.spinner("⚖️ Analizando caso y redactando..."):
            try:
                response = st.session_state.chat_session.send_message(full_prompt)
                st.session_state.history.append({"role": "assistant", "text": response.text})
                st.rerun()
            except Exception as e:
                st.error(f"Error al generar: {e}")

# --- INTERFAZ ---
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["text"])

if prompt := st.chat_input("Ej: Redacta demanda usando archivo 1025..."):
    st.chat_message("user").write(prompt)
    st.session_state.history.append({"role": "user", "text": prompt})

    with st.chat_message("assistant"):
        with st.spinner("⚖️ Trabajando..."):
            try:
                response = st.session_state.chat_session.send_message(prompt)
                text_response = response.text
                st.write(text_response)
                st.session_state.history.append({"role": "assistant", "text": text_response})

                if len(text_response) > 100:
                    doc = Document()
                    # ELIMINADO: doc.add_heading('Borrador Legal IA', 0) -> El usuario quiere el doc limpio
                    doc.add_paragraph(text_response)
                    bio = io.BytesIO()
                    doc.save(bio)
                    
                    st.download_button(
                        label="📥 Descargar Word",
                        data=bio.getvalue(),
                        file_name="Escrito_Legal.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "quota" in error_msg.lower():
                    st.error(f"🚨 SE AGOTÓ LA ENERGÍA DE {model_option}")
                    st.warning(f"""
                        El modelo '{model_option}' ha alcanzado su límite diario.
                        
                        👉 **SOLUCIÓN:** En la barra izquierda, cambia a otro modelo de la lista.
                        (Prueba 'gemini-2.0-flash-exp' o 'gemini-2.0-flash').
                    """)
                else:
                    st.error(f"Error inesperado: {e}")
import streamlit as st
import os
import io
import time
import google.generativeai as genai
from dotenv import load_dotenv
from docx import Document

# Custom Modules
import ingest_module
from tools_bcn import obtener_ley_bcn
from auth_logic import check_authentication
from rag_logic import buscar_modelos_locales
from doc_logic import get_header_docx

load_dotenv()

st.set_page_config(page_title="Agente Jurídico", page_icon="⚖️")

# --- AUTHENTICATION ---
# Protege toda la app. Si falla, detiene la ejecución.
authenticator = check_authentication()

# --- PATHS ---
DOCS_PATH = "./docs/"

# --- SIDEBAR ---
with st.sidebar:
    st.write(f"👤 **{st.session_state['name']}**")
    authenticator.logout("Cerrar Sesión", "sidebar")
    st.divider()
    
    st.header("📚 Biblioteca")
    st.info("Pon tus archivos .docx o .pdf en la carpeta 'docs/' o súbelos aquí:")
    
    uploaded_files = st.file_uploader("📤 Subir Nuevos Modelos", accept_multiple_files=True, type=["docx", "pdf"])
    if uploaded_files:
        if not os.path.exists(DOCS_PATH): os.makedirs(DOCS_PATH)
        for uploaded_file in uploaded_files:
            file_path = os.path.join(DOCS_PATH, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        st.success(f"¡{len(uploaded_files)} archivo(s) guardado(s)! Ahora presiona 'Actualizar'.")
    
    if st.button("🔄 Actualizar IA con nuevos Docs"):
        with st.spinner("Leyendo y aprendiendo documentos (Local)..."):
            log_result = ingest_module.run_ingestion()
            st.success("¡Actualización Completa!")
            st.text_area("Log de Proceso:", log_result, height=200)

    st.divider()
    st.header("🤖 Configuración Cerebro")
    st.caption("Cerebro: gemini-flash-latest (Optimizado)")
    model_option = "gemini-flash-latest"

st.title("⚖️ Agente Jurídico")

# Configuración API
if "google_api_key" not in st.session_state:
    st.session_state.google_api_key = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=st.session_state.google_api_key)

tools_list = [buscar_modelos_locales, obtener_ley_bcn]

# --- INICIAR CHAT ---
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
        REGLAS DE ORO (SI LAS ROMPES, FALLAS):
        1. **NO REDACTES NADA NUEVO**. No cambies el estilo. No cambies las palabras "jurídicas".
        2. **MANTÉN CADA PÁRRAFO**. Si el original tiene 5 párrafos de hechos, tú devuelves 5.
        3. **SI EL ORIGINAL DICE "PRIMER OTROSÍ"**, TÚ LO COPIAS.
        4. **JAMÁS USES CORCHETES `[...]`**. Si no tienes un dato, déjalo en blanco.
        5. **DETECTA Y REEMPLAZA "XXXXX"**: Si ves "XXXXX", "..." o placeholders en el original, REEMPLÁZALOS por los datos nuevos (Nombre, RUT, Domicilio).
        6. **NO RESUMAS**. Copia y pega mentalmente, solo inyectando los datos nuevos.
        
        PASOS:
        1. ANALIZAR TEMA.
        2. ANALIZAR DATOS: Usa los nombres y RUTs provistos.
        3. COPIAR ESTRUCTURA: Replica la redacción del modelo fuente.
        4. VALIDAR DERECHO: Si cita leyes, verifica vigencia.
        """
    )
    # enable_automatic_function_calling=True se mantiene para el CHAT interactivo.
    # Para la generación masiva (streaming), usaremos generate_content directo (bypass).
    st.session_state.chat_session = model.start_chat(enable_automatic_function_calling=True)
    st.session_state.history = []

# --- UI PRINCIPAL (FORMULARIO) ---
st.write("---")
st.subheader("📝 Redactar Escrito")

# Select Doc
doc_files = [f for f in os.listdir(DOCS_PATH) if f.endswith(".docx")] if os.path.exists(DOCS_PATH) else []
doc_files.insert(0, "Selección Inteligente (Buscar por tema)")

col1, col2 = st.columns([1, 1])

with col1:
    selected_doc = st.selectbox("📌 Plantilla Base:", doc_files)
    materia = st.text_input("Materia (Ej: Divorcio, Alimentos):", value="Alimentos Menores")
    tribunal = st.text_input("Tribunal:", value="Juzgado de Familia de San Miguel")

with col2:
    nombre_dte = st.text_input("Demandante (Nombre):", value="Laura Andrea Soto")
    rut_dte = st.text_input("RUT Demandante:", value="15.111.111-1")
    nombre_ddo = st.text_input("Demandado (Nombre):", value="Pedro Pablo Perez")
    rut_ddo = st.text_input("RUT Demandado:", value="12.222.222-2")
    domicilio = st.text_input("Domicilio Demandado:", value="Calle Falsa 123")

with st.expander("Ver más datos (Abogado, Niño, Historia, etc)"):
    col3, col4 = st.columns(2)
    with col3:
        nombre_menor = st.text_input("Nombre Niño/a:", value="Juanito Perez Soto")
        abogado = st.text_input("Abogado:", value="Iván Abogado")
        rut_abogado_val = st.text_input("RUT Abogado:", value="10.000.000-0")
    with col4:
        domicilio_abogado = st.text_input("Domicilio Abogado:", value="Huérfanos 1111, Of. 88")
        otros_datos = st.text_area("Historia / Hechos Nuevos:", height=150, 
            value="Se casaron el 2010, se separaron el 2022. El padre aporta irregularmente. Se solicita pensión de $350.000.")

# Botón Generar
if st.button("✨ Redactar Escrito", type="primary"):
    # 1. Analizar si es búsqueda inteligente
    if selected_doc == "Selección Inteligente (Buscar por tema)":
        with st.spinner("🔍 Buscando modelo..."):
            hallazgo = buscar_modelos_locales(f"Demanda de {materia}")
            st.info(hallazgo)
            st.warning("Por favor selecciona manualmente una de las plantillas encontradas arriba en 'Plantilla Base'.")
    else:
        # Preparamos Data
        data_dict = {
            "materia": materia, "nombre_menor": nombre_menor, 
            "nombre_dte": nombre_dte, "nombre_ddo": nombre_ddo,
            "abogado": abogado, "rut_dte": rut_dte, "rut_ddo": rut_ddo,
            "domicilio": domicilio, "domicilio_dte": "GENERAL CELEDÓN Nº 10290, DEPTO 202",
            "domicilio_abogado": domicilio_abogado, "rut_abogado_val": rut_abogado_val
        }
        
        # LLAMADA A DOC_LOGIC (Recuperar Header + Preview)
        doc_obj, header_preview = get_header_docx(selected_doc, data_dict)
        
        # LEER CONTENIDO DEL ARCHIVO PARA INYECTARLO AL PROMPT (Critical for Bypass)
        doc_text_content = ""
        try:
            source_path = os.path.join(DOCS_PATH, selected_doc)
            temp_doc = Document(source_path)
            
            # --- CONTEXT CLEANING: Cortar Header del Contexto ---
            full_paras = [p.text for p in temp_doc.paragraphs if p.text.strip()]
            start_idx = 0
            for i, txt in enumerate(full_paras):
                # Usamos match estricto. "HECHOS" solo es peligroso pq coincide con "Fundamentos de Hecho".
                # Buscamos variaciones comunes de titulos.
                clean_txt = txt.upper().strip()
                if "LOS HECHOS" in clean_txt or clean_txt == "HECHOS" or "1.- HECHOS" in clean_txt:
                    start_idx = i
                    break
            
            # Si start_idx sigue siendo 0, intentamos una heurística de emergencia:
            final_paras = full_paras[start_idx:]
            doc_text_content = "\n".join(final_paras)
            
            # --- SAFETY CHECK: Si el corte dejó el texto vacío (o muy corto), usar todo ---
            if len(doc_text_content) < 200:
                doc_text_content = "\n".join(full_paras)
            
        except Exception as e:
            doc_text_content = f"[Error leyendo archivo fuente: {e}]"
            
        # --- DEBUG UI (Solo visible si hay problemas o para verificar) ---
        with st.expander("🛠️ Debug: Información enviada a la IA"):
            st.write(f"Caracteres leídos del modelo: {len(doc_text_content)}")
            st.write(f"Inicio del texto (preview): {doc_text_content[:200]}...")

        full_prompt = f"""ROL: MÁQUINA DE COPIADO INTELIGENTE.
        
        INPUT:
        1. MODELO FUENTE (Texto Legal).
        2. DATOS NUEVOS (Cliente).
        
        INSTRUCCIÓN MAESTRA:
        "COPIA EL TEXTO DEL MODELO FUENTE REEMPLAZANDO LOS DATOS ANTIGUOS POR LOS NUEVOS".
        
        REGLA DE ORO DE INICIO:
        **TU RESPUESTA DEBE COMENZAR OBLIGATORIAMENTE CON EL TÍTULO: "LOS HECHOS"**.
        (Ignora cualquier tabla, suma o introducción que veas antes de "LOS HECHOS" en el modelo fuente. YA ESTÁN ESCRITOS).
        
        PROHIBICIONES (FATALES):
        - NO COPIES EL ENCABEZADO (Nada antes de "LOS HECHOS").
        - **PROHIBIDO USAR LISTAS O MARKDOWN**: No uses asteriscos (**texto**), ni guiones (-), ni numeración automática (1.). Escribe en PÁRRAFOS como un escrito judicial tradicional.
        - NO INVENTES LEYES.
        - NO RESUMAS LOS HECHOS.
        - NO OLVIDES LOS OTROSÍS.
        - **DETECTA Y REEMPLAZA TEXTO GENÉRICO**: Si ves "XXXXX", "..." o "[DATOS]" en el original, REEMPLÁZALOS por los datos reales (Nombre, RUT, Abogado). NO LOS DEJES VACÍOS.
        
        DATOS NUEVOS:
        - DEMANDANTE: {nombre_dte} ({rut_dte}).
        - DEMANDADO: {nombre_ddo} ({rut_ddo}).
        - NIÑO/A: {nombre_menor}.
        - HISTORIA: {otros_datos}.
        
        MODELO FUENTE A PROCESAR:
        [[[
        {doc_text_content[:25000]} 
        ]]]
        """
        
        ui_prompt = f"Generar escrito basado en '{selected_doc}' para {nombre_dte} vs {nombre_ddo}."
        st.session_state.history.append({"role": "user", "text": ui_prompt})
        
        max_retries = 3
        
        # 1. INICIAR CONEXIÓN (CON SPINNER)
        response = None
        with st.spinner("⚖️ Digitando y reemplazando datos..."):
            for attempt in range(max_retries):
                try:
                    # BYPASS CHAT SESSION AUTO-TOOLS to allow STREAMING
                    # Usamos el modelo directo (sin herramientas) para evitar conflicto de SDK.
                    # Le inyectamos el texto del archivo directamente en el prompt.
                    response = st.session_state.chat_session.model.generate_content(full_prompt, stream=True)
                    break 
                except Exception as e:
                    is_quota_error = "429" in str(e) or "Quota exceeded" in str(e)
                    if is_quota_error and attempt < max_retries - 1:
                        time.sleep(20)
                    else:
                        st.error(f"Error al conectar: {e}")
                        response = None
                        break
        
        # 2. STREAMING & CLEANING
        if response:
            try:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    if header_preview.strip():
                        full_response += f"**VISTA PREVIA ENCABEZADO (Automático):**\n```text\n{header_preview}\n```\n\n**DESARROLLO (IA):**\n"
                    
                    accumulated_raw = ""
                    
                    for chunk in response:
                        if chunk.text:
                            accumulated_raw += chunk.text
                            # Lógica visual simple (mostramos todo por ahora para no romper UX de streaming)
                            # La limpieza real la haremos al final para el documento.
                            message_placeholder.markdown(full_response + accumulated_raw + "▌")
                    
                    # --- POST-PROCESSING FORCE CLEAN ---
                    # Si la IA desobedeció y puso el header, lo cortamos programáticamente.
                    final_body_text = accumulated_raw
                    if "LOS HECHOS" in final_body_text:
                         # Cortamos todo lo que esté antes de "LOS HECHOS"
                         parts = final_body_text.split("LOS HECHOS", 1)
                         if len(parts) > 1:
                             # Reconstruimos: "LOS HECHOS" + lo que sigue
                             final_body_text = "LOS HECHOS" + parts[1]
                    
                    message_placeholder.markdown(full_response + final_body_text)
                
                # Persistencia
                body_text = final_body_text.replace("\n", "\n\n") # Markdown friendly spacing
                st.session_state.is_generated_doc = True
                st.session_state.last_header = header_preview
                st.session_state.last_body = body_text
                st.session_state.selected_doc_for_download = selected_doc
                st.session_state.data_dict_for_download = data_dict
                
                st.session_state.history.append({"role": "assistant", "text": full_response + final_body_text})
                st.rerun()
                
            except Exception as e:
                    st.error(f"Error durante streaming: {e}")

# --- INTERFAZ CHAT ---
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["text"])

# --- ÁREA DE DESCARGA ---
if st.session_state.get("is_generated_doc", False):
    st.divider()
    st.subheader("📥 Documento Generado")
    
    try:
        final_doc, _ = get_header_docx(st.session_state.selected_doc_for_download, st.session_state.data_dict_for_download)
        final_doc.add_paragraph(st.session_state.last_body.replace("\n\n", "\n"))
        
        bio = io.BytesIO()
        final_doc.save(bio)
        
        st.download_button(
            label="📄 Descargar Documento (Word)",
            data=bio.getvalue(),
            file_name="Demanda_Final.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary"
        )
    except Exception as e:
        st.error(f"Error preparando descarga: {e}")

# --- CHAT CONSULTAS (TEXTO) ---
if prompt := st.chat_input("Consulta jurídica (No genera documento)..."):
    if st.session_state.get("is_generated_doc"):
        st.session_state.is_generated_doc = False
        st.rerun()

    st.chat_message("user").write(prompt)
    st.session_state.history.append({"role": "user", "text": prompt})

    with st.chat_message("assistant"):
        with st.spinner("⚖️ Consultando leyes..."):
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # AQUÍ SÍ USAMOS LA SESIÓN CON TOOLS (send_message)
                    response = st.session_state.chat_session.send_message(prompt)
                    text_response = response.text
                    st.write(text_response)
                    st.session_state.history.append({"role": "assistant", "text": text_response})
                    break 
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        time.sleep(20)
                        continue
                    else:
                        st.error(f"Error: {e}")
                        break
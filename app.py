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
import docx2txt
from usage_logic import init_usage_db, get_user_status, check_can_generate, log_generation

load_dotenv()

st.set_page_config(page_title="Agente Jurídico", page_icon="⚖️")

# --- DATABASE INIT ---
init_usage_db()

# --- AUTHENTICATION ---
# Protege toda la app. Si falla, detiene la ejecución.
authenticator = check_authentication()

# --- PATHS ---
DOCS_PATH = "./docs/"

# --- SIDEBAR ---
with st.sidebar:
    st.write(f"👤 **{st.session_state['name']}**")
    
    # --- SAAS BILLING INFO ---
    user_count, is_pro = get_user_status(st.session_state['username'])
    if is_pro:
        st.metric("Plan", "⭐ PRO", "Ilimitado")
    else:
        st.metric("Tus Créditos", f"{user_count}/3", f"{3-user_count} restantes")
        if user_count >= 3:
            st.error("🔒 Límite Alcanzado")
            st.markdown("[🚀 Actualizar a PRO](https://buy.stripe.com/test_placeholder)")
        else:
            st.progress(user_count / 3)
    
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
    st.caption("Cerebro: gemini-flash-lite-latest (Respaldo Funcionando)")
    model_option = "gemini-flash-lite-latest"

st.title("⚖️ Agente Jurídico")

# Configuración API
if "google_api_key" not in st.session_state:
    if os.getenv("GOOGLE_API_KEY"):
        st.session_state.google_api_key = os.getenv("GOOGLE_API_KEY")

if not st.session_state.get("google_api_key"):
    st.warning("⚠️ Falta API Key. Configura .env o Secrets.")
    st.stop()
    
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
        gen_menor = st.selectbox("Género Menor:", ["Niño", "Niña"])
        abogado = st.text_input("Abogado:", value="Iván Abogado")
        rut_abogado_val = st.text_input("RUT Abogado:", value="10.000.000-0")
    with col4:
        rel_ddo = st.selectbox("Relación del Demandado con el Menor:", ["Padre", "Madre"])
        domicilio_abogado = st.text_input("Domicilio Abogado:", value="Huérfanos 1111, Of. 88")
        otros_datos = st.text_area("Historia / Hechos Nuevos:", height=150, 
            value="Se casaron el 2010, se separaron el 2022. El padre aporta irregularmente. Se solicita pensión de $350.000.")

# Botón Generar
if st.button("✨ Redactar Escrito", type="primary"):
    # --- SAAS CHECK ---
    can_gen, status_code = check_can_generate(st.session_state['username'])
    if not can_gen:
        st.error(f"🛑 Límite de documentos alcanzado ({status_code}).")
        st.markdown(f"""
        <div style="background-color:#ffebee; padding:15px; border-radius:10px; border:1px solid #ffcdd2;">
            <h4>🔒 Actualiza a PRO</h4>
            <p>Has consumido tus 3 documentos de cortesía del Plan Freemium.</p>
            <ul>
                <li>✅ Generaciones Ilimitadas</li>
                <li>✅ Prioridad de Procesamiento</li>
                <li>✅ Descargas en Word</li>
            </ul>
            <a href="https://buy.stripe.com/test_placeholder" target="_blank" style="background-color:#d32f2f; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; font-weight:bold;">👉 COMPRAR ACCESO ILIMITADO ($20.000)</a>
        </div>
        """, unsafe_allow_html=True)
        st.stop()
    
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
            "domicilio_abogado": domicilio_abogado, "rut_abogado_val": rut_abogado_val,
            "gen_menor": gen_menor, "rel_ddo": rel_ddo
        }
        
        # LLAMADA A DOC_LOGIC (Recuperar Header + Preview)
        doc_obj, header_preview = get_header_docx(selected_doc, data_dict)
        
        # LEER CONTENIDO DEL ARCHIVO
        doc_text_content = ""
        try:
            source_path = os.path.join(DOCS_PATH, selected_doc)
            # Usar docx2txt para extraer texto completo rapido para contexto
            doc_text_content = docx2txt.process(source_path)
            
            # Smart Slicing para quitar header del contexto que se envia a la IA
            if "LOS HECHOS" in doc_text_content.upper():
                 parts = doc_text_content.upper().split("LOS HECHOS", 1)
                 # Reconstruimos usando el casing original (aproximado, aquí perdemos casing si spliteamos Upper)
                 # Mejor buscamos índice.
                 idx = doc_text_content.upper().find("LOS HECHOS")
                 if idx != -1:
                      doc_text_content = "LOS HECHOS" + doc_text_content[idx+10:]
            
            # Fallback length
            if len(doc_text_content) < 200:
                 doc_text_content = docx2txt.process(source_path)

        except Exception as e:
            st.error(f"Error leyendo archivo fuente: {e}")
            st.stop()
            
        # --- BCN GROUNDING (NUEVO) ---
        bcn_context = ""
        with st.status("🏛️ Consultando Biblioteca del Congreso (BCN)...", expanded=False) as status:
            from tools_bcn import obtener_ley_bcn
            # Detectar ley relevante según materia
            leyes_clave = []
            if "Alimentos" in materia:
                leyes_clave.append("14908") # Ley de Alimentos
            
            if leyes_clave:
                status.write(f"Detectadas leyes clave: {leyes_clave}")
                for ley_id in leyes_clave:
                    texto_ley = obtener_ley_bcn(ley_id)
                    if "Error" not in texto_ley:
                         # Truncamos para no explotar ventana de contexto, aunque Flash aguanta mucho.
                         bcn_context += f"\n--- LEY {ley_id} (TEXTO OFICIAL VIGENTE) ---\n{texto_ley[:15000]}\n"
                         status.write(f"✅ Ley {ley_id} descargada.")
                    else:
                         status.write(f"⚠️ No se pudo descargar Ley {ley_id}.")
            else:
                status.write("No se detectaron leyes específicas para descarga automática.")
            status.update(label="Validación BCN Completa", state="complete", expanded=False)

        # --- DEBUG UI (Solo visible si hay problemas o para verificar) ---
        with st.expander("🛠️ Debug: Información enviada a la IA"):
            st.write(f"Caracteres leídos del modelo: {len(doc_text_content)}")
            st.write(f"Inicio del texto (preview): {doc_text_content[:200]}...")
            if bcn_context:
                st.write(f"Caracteres de contexto BCN: {len(bcn_context)}")
                st.write(f"Inicio contexto BCN (preview): {bcn_context[:200]}...")

        # ---------------- PROMPT ENGINEERING ----------------
        full_prompt = f"""ROL: ABOGADO EXPERTO + FOTOCOPIADORA INTELIGENTE.
        
        INPUT:
        1. MODELO FUENTE (Tu base).
        2. CONTEXTO BCN (La Ley Oficial).
        3. DATOS NUEVOS (Cliente).
        
        INSTRUCCIÓN MAESTRA:
        "ADAPTA LOS HECHOS, COPIA EL RESTO, Y VALIDA EL DERECHO CON LA BCN".
        
        TUS 3 MODOS DE OPERACIÓN:
        
        1. **MODO NARRATIVO ("LOS HECHOS")**:
           - Redacta una historia coherente usando los DATOS NUEVOS.
           - Adapta el estilo del modelo, pero haz que suene natural.
        
        2. **MODO LEGAL ("EL DERECHO")**:
           - **PRIORIDAD BCN**: Si el modelo cita la Ley 14.908 (Alimentos), VERIFICA el articulado con el CONTEXTO BCN provisto.
           - Si el modelo tiene una cita desactualizada, CORRÍGELA usando el texto de la BCN.
           - Si no tienes la ley completa, mantén la cita del modelo (Fallback).
        
        3. **MODO FOTOCOPIADORA ("OTROSÍS")**:
           - Copia y pega exacto. Reemplaza Placeholders.

        REGLAS DE FORMATO:
        - **PROHIBIDO MARKDOWN**: Nada de negritas, escriba texto plano.
        - **CERO PLACEHOLDERS**: Rellena todo.
        - **INICIO**: Empieza desde "LOS HECHOS".
        
        DATOS NUEVOS:
        - DEMANDANTE: {nombre_dte} ({rut_dte}).
        - DEMANDADO: {nombre_ddo} ({rut_ddo}).
        - NIÑO/A: {nombre_menor}.
        - ABOGADO: {abogado} (RUT: {rut_abogado_val}).
        - HISTORIA DEL CLIENTE: "{otros_datos}".

        CONTEXTO LEGAL OFICIAL (BCN):
        [[[
        {bcn_context}
        ]]]
        
        MODELO FUENTE:
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
                        try:
                            if chunk.text:
                                accumulated_raw += chunk.text
                                # Lógica visual simple (mostramos todo por ahora para no romper UX de streaming)
                                # La limpieza real la haremos al final para el documento.
                                message_placeholder.markdown(full_response + accumulated_raw + "▌")
                        except ValueError:
                             # Captura error cuando chunk.text no tiene contenido (finish_reason)
                             pass
                    
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
                
                # --- SAAS LOGGING ---
                log_generation(st.session_state['username'])
                
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
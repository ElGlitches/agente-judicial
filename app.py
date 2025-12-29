
import streamlit as st
import os
import io
import google.generativeai as genai
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from docx import Document
from tools_bcn import obtener_ley_bcn
import ingest_module  # Nuevo módulo de ingesta

load_dotenv()

st.set_page_config(page_title="Agente Jurídico", page_icon="⚖️")

# --- PATHS ---
CHROMA_PATH = "chroma_db"
DOCS_PATH = "./docs/"

# --- SIDEBAR: GESTIÓN DE DOCUMENTOS ---
with st.sidebar:
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

# --- HERRAMIENTA DE BÚSQUEDA CHROMA ---
def buscar_modelos_locales(consulta: str):
    """Busca priorizando nombres de archivos exactos."""
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        collection = client.get_collection(name="escritos_judiciales", embedding_function=sentence_transformer_ef)
        
        matches = []
        full_doc_found = False

        # 1. BÚSQUEDA INTELIGENTE DE ARCHIVOS (MODO "FULL DOC") POR METADATA
        # Si el usuario menciona un archivo, intentamos encontrarlo
        # Extraemos palabras clave
        keywords = [word for word in consulta.split() if len(word) > 3 or word.isdigit()]
        
        for word in keywords:
            if word.isdigit():
                 # Buscar en metadatos "filename"
                 # Chroma where clause
                 # where={"filename": {"$contains": word}} # Chroma doesn't support contains string easily in standard meta
                 # But we can query normally.
                 pass

        # Búsqueda Semántica Estándar
        # query_texts genera embeddings automaticamente usando la funcion definida en la coleccion
        results = collection.query(
            query_texts=[consulta],
            n_results=10
        )
        
        # Procesar resultados
        # results['documents'] es lista de listas
        if results['documents']:
            found_docs = results['documents'][0]
            found_metas = results['metadatas'][0]
            
            # Reconstruir documento completo si hay match fuerte de nombre? 
            # Por simplicidad, devolvemos los chunks más relevantes.
            # Filtrar duplicados
            unique_docs = sorted(set(found_docs), key=found_docs.index) # Preserve order
            matches = unique_docs[:6]

            # Verificamos si en la metadata está el archivo solicitado
            # Si en los top matches aparece insistentemente un filename, quizás deberíamos traerlo todo?
            # En esta versión simple, devolvemos los chunks. La IA reconstruye.
            
        if not matches: return "No encontré modelos."
        return "ENCONTRÉ ESTOS MODELOS:\n" + "\n\n---\n\n".join(matches)
        
    except Exception as e:
        return f"Error ChromaDB: {e}. (Asegúrate de haber presionado 'Actualizar IA' primero)"

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

# --- HELPER HEADER FUNCTION (Restaurada) ---
def get_header_docx(selected_doc, data_dict):
    """
    Genera el objeto Document MODIFICANDO el original para mantener tablas y formato.
    Elimina el cuerpo antiguo y deja solo el encabezado (Presuma + Suma + Intro).
    """
    if selected_doc == "Selección Inteligente (Buscar por tema)" or not selected_doc.endswith(".docx"):
        return Document(), ""
        
    try:
        import re
        from docx.oxml.ns import qn
        source_path = os.path.join(DOCS_PATH, selected_doc)
        doc = Document(source_path) # Usamos el original para mantener TABLAS
        preview_text = ""
        
        # Datos para reemplazo
        replacements = {
            "MATERIA": data_dict["materia"],
            "MENOR": data_dict["nombre_menor"],
            "DEMANDANTE": data_dict["nombre_dte"],
            "DEMANDADO": data_dict["nombre_ddo"],
            "ABOGADO": data_dict["abogado"],
            "PATROCINANTE": data_dict["abogado"],
            "APODERADO": data_dict["abogado"],
            "R.U.T": [data_dict["rut_dte"], data_dict["abogado"], data_dict["rut_ddo"]], 
            "DOMICILIO": [data_dict["domicilio"]] 
        }
        ruts = list(replacements["R.U.T"])
        ruts2 = list(replacements["R.U.T"]) # Copia para parrafos

        # --- FUNCIÓN HELPER DE REEMPLAZO ---
        def apply_replacements(text, ruts_list):
            text_upper = text.upper()
            found_change = False
            
            # Reemplazo Genérico
            for key, val in replacements.items():
                if key in ["R.U.T", "DOMICILIO"]: continue
                if key in text_upper and val:
                    pattern = re.compile(rf"({key}.*?:)(.*)", re.IGNORECASE)
                    if pattern.search(text):
                        text = pattern.sub(rf"\1 \t {val}", text)
                        found_change = True
            
            # Reemplazo RUT (Consumiendo lista)
            if "R.U.T" in text_upper and ruts_list:
                # Regex estricto para evitar falsos positivos como "PROCEDIMIENTO" (R...T)
                # Busca 'R.U.T', 'RUT', 'R. U. T.' seguido de dos puntos opcionales
                pattern = re.compile(r"(\bR\.?\s?U\.?\s?T\.?\s?:?)(.*)", re.IGNORECASE)
                if pattern.search(text):
                    text = pattern.sub(rf"\1 \t {ruts_list[0]}", text)
                    ruts_list.pop(0)
                    found_change = True
            
        # 1. ESTRATEGIA: RECONSTRUCCIÓN TOTAL para Alimentos
        # Si es Alimentos Menores, reconstruimos TODO el encabezado (Tabla + Suma + Tribunal + Intro)
        if "ALIMENTOS" in data_dict["materia"].upper():
            # A. ENCONTRAR ANCLA (LOS HECHOS)
            anchor_par = None
            paragraphs_to_delete = []
            
            for p in doc.paragraphs:
                if "LOS HECHOS" in p.text.upper():
                    anchor_par = p
                    break
                paragraphs_to_delete.append(p)
            
            # Si no encontramos "LOS HECHOS", asumimos el final o el principio?
            # Mejor dejar uno vacío si falla.
            if not anchor_par and doc.paragraphs:
                 anchor_par = doc.paragraphs[0] # Fallback
            
            # B. LIMPIAR HEADER ANTIGUO
            # Borramos párrafos previos (Suma vieja, Intro vieja, etc)
            for p in paragraphs_to_delete:
                p._element.getparent().remove(p._element)
                
            # Borrar tablas previas (Presuma vieja)
            if doc.tables:
                # Borrar TODAS las tablas que estén antes del ancla? 
                # Simplificación: Borrar la primera tabla (Presuma)
                tbl = doc.tables[0]
                tbl._element.getparent().remove(tbl._element)

            # C. CONSTRUIR NUEVO HEADER (INVERSO desde el Ancla hacia arriba)
            # Orden deseado: [TABLA] -> [SUMA] -> [TRIBUNAL] -> [INTRO] -> [ANCHOR]
            # Usando insert_paragraph_before, el orden de inserción debe ser:
            # 1. Intro (quedará pegada al Anchor)
            # 2. Tribunal (quedará pegado a Intro)
            # 3. Suma (...)
            # 4. Tabla (...)
            
            # Datos
            suma_text = "EN LO PRINCIPAL: DEMANDA DE ALIMENTOS; PRIMER OTROSÍ: ALIMENTOS PROVISORIOS; SEGUNDO OTROSÍ: ACOMPAÑA DOCUMENTOS; TERCER OTROSÍ: SOLICITA OFICIOS; CUARTO OTROSÍ: PATROCINIO Y PODER."
            trib_text = f"S. J. L. DE FAMILIA DE SAN MIGUEL" # Ojo: data_dict['tribunal'] si queremos que sea dinámico, pero usuario quiere San Miguel
            intro_text = (
                     f"{data_dict['nombre_dte'].upper()}, chilena, cédula nacional de identidad número {data_dict['rut_dte']}, "
                     f"con domicilio (según otrosí), en representación legal de su hijo menor "
                     f"{data_dict['nombre_menor'].upper()}, chileno, del mismo domicilio, a S.S. respetuosamente digo:"
                 )
            
            bridge_text = (
                f"Que vengo en interponer la presente demanda de {data_dict['materia']} en contra de {data_dict['nombre_ddo'].upper()}, "
                f"cédula nacional de identidad Nº {data_dict['rut_ddo']}, domiciliado en {data_dict['domicilio'].upper()}, "
                "en su calidad de progenitor del niño/a anteriormente individualizado/a, "
                "todo ello en virtud de los fundamentos de hecho y de derecho que paso a exponer:"
            )
            
            # Insertar Párrafos (Orden Inverso desde Anchor)
            # Anchor <--- Bridge <--- Intro <--- Trib <--- Suma
            
            p_bridge = anchor_par.insert_paragraph_before(bridge_text)
            p_bridge.alignment = 3 # Justificado
            
            p_intro = p_bridge.insert_paragraph_before(intro_text)
            p_intro.alignment = 3 
            
            p_trib = p_intro.insert_paragraph_before(trib_text.upper())
            p_trib.insert_paragraph_before("") 
            
            p_suma = p_trib.insert_paragraph_before(suma_text)
            p_suma.insert_paragraph_before("")

            # Insertar Tabla
            # Truco: Crear tabla y moverla antes de p_suma
            table = doc.add_table(rows=0, cols=2)
            table.style = 'Table Grid'
            p_suma._element.addprevious(table._element)
            
            # Llenar Tabla (Presuma Estándar)
            presuma_data = [
                ("PROCEDIMIENTO", "ORDINARIO"),
                ("MATERIA", data_dict["materia"]),
                ("MENOR", data_dict["nombre_menor"]),
                ("DEMANDANTE", data_dict["nombre_dte"].upper()),
                ("R.U.T", data_dict["rut_dte"]),
                ("DOMICILIO", "GENERAL CELEDÓN Nº 10290, DEPTO 202"), # HARDCODED SEGUN CLIENTE
                ("", ""), 
                ("ABOGADO PATROCINANTE", data_dict["abogado"].upper()),
                ("R.U.T.", data_dict["rut_abogado_val"]),
                ("DOMICILIO", data_dict["domicilio_abogado"].upper()),
                ("APODERADO", data_dict["abogado"].upper()),
                ("R.U.T.", data_dict["rut_abogado_val"]),
                ("", ""), 
                ("DEMANDADO", data_dict["nombre_ddo"].upper()),
                ("R.U.T.", data_dict["rut_ddo"]),
                ("DOMICILIO", data_dict["domicilio"].upper())
            ]
            
            for label, val in presuma_data:
                row_cells = table.add_row().cells
                row_cells[0].text = label
                row_cells[1].text = str(val)

            preview_text += "[HEADER ALIMENTOS RECONSTRUIDO TOTALMENTE]\n"
            
            # RETORNO ANTICIPADO PARA EVITAR DOBLE PROCESAMIENTO
            # Ya hicimos todo, no necesitamos los loops de abajo
            # ... Salvo el truncado final por si acaso
            
        else:
            # --- LÓGICA ANTIGUA (Para otras materias que no sean Alimentos) ---
            # 1. PROCESAR TABLAS
            if doc.tables:
                pass # (Mantener lógica existente de replacement)


        # 3. TRUNCAR DOCUMENTO (Eliminar cuerpo antiguo)
        # Iteramos sobre el XML para borrar todo DESDE "EN LO PRINCIPAL" (Inclusive)
        # Así la IA pone su propio "EN LO PRINCIPAL" y no se duplica.
        body_element = doc._body._body
        elements_to_remove = []
        found_cutoff = False
        
        for child in body_element.iterchildren():
            if found_cutoff:
                elements_to_remove.append(child)
                continue
            
            try:
                xml_text = child.xpath('.//w:t')
                full_text = "".join([t.text for t in xml_text if t.text]).upper()
                
                # Criterios de Corte: LOS HECHOS
                if "LOS HECHOS" in full_text:
                    found_cutoff = True
                    elements_to_remove.append(child)
            except:
                pass
        
        # Ejecutar borrado
        for child in elements_to_remove:
            body_element.remove(child)

        # Añadir separador visual para el usuario
        doc.add_paragraph("\n" + "_"*40 + "\n(Cuerpo generado por IA comienza aquí)\n")
        
        return doc, preview_text
        
    except Exception as e:
        print(f"Error grave: {e}")
        return Document(), f"[Error Header: {e}]"


# --- FICHA DEL CASO (FORMULARIO) ---
with st.expander("📝 Ficha del Caso (Generador Automático)", expanded=False):
    st.caption("Llena estos datos para generar una demanda sin errores.")
    col1, col2 = st.columns(2)
    with col1:
        tribunal = st.text_input("Tribunal", value="1º Juzgado de Familia de San Miguel")
        materia = st.text_input("Materia", value="Alimentos Menores")
        nombre_dte = st.text_input("Demandante (Nombre)", value="Laura Andrea Soto Tapia")
        rut_dte = st.text_input("Demandante (RUT)", value="15.111.222-3")
        abogado = st.text_input("Abogado Patrocinante", value="Iván Abogado")
        
    with col2:
        nombre_ddo = st.text_input("Demandado (Nombre)", value="Carlos Alberto Pérez Ruiz")
        rut_ddo = st.text_input("Demandado (RUT)", value="14.888.999-k")
        domicilio = st.text_input("Domicilio Demandado", value="Calle Los Libertadores 500, Maipú")
        nombre_menor = st.text_input("Nombre Niño/a", value="Tomasito Pérez Soto")
        otros_datos = st.text_area("Otros Hechos / Historia", value="Se casaron el 2010, se separaron el 2022. El padre aporta irregularmente. Se solicita pensión de $350.000.", height=100)

    # Selector de Documentos Dinámico
    if not os.path.exists(DOCS_PATH): os.makedirs(DOCS_PATH)
    available_docs = ["Selección Inteligente (Buscar por tema)"] + [f for f in os.listdir(DOCS_PATH) if not f.startswith(".")]
    
    # Intentar seleccionar por defecto el 1025
    default_index = 0
    for i, doc in enumerate(available_docs):
        if "1025" in doc:
            default_index = i
            break
            
    selected_doc = st.selectbox("📌 Plantilla Base:", available_docs, index=default_index)

    if st.button("✨ Redactar Escrito", type="primary"):
        # MARK: INICIO GENERACIÓN
        st.session_state.is_generated_doc = False # Reset
        
        # Construcción del Prompt
        contexto_adicional = ""

        header_preview = ""
        doc_instruction = ""
        
        # Datos fijos/derivados
        domicilio_abogado = "Av. Alejandro Guzmán Nº 735, El Bosque" # Predeterminado según instruccion
        rut_abogado_val = "15.111.222-3" # Valor por defecto o tomar de input si existiera

        # 1. Preparar Header Python si corresponde
        if selected_doc != "Selección Inteligente (Buscar por tema)":
            try:
                # Leer Texto
                file_path = os.path.join(DOCS_PATH, selected_doc)
                doc_text = ""
                if selected_doc.endswith(".docx"):
                    doc_obj = Document(file_path)
                    doc_text = "\n".join([p.text for p in doc_obj.paragraphs])
                elif selected_doc.endswith(".pdf"):
                    from pypdf import PdfReader
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        doc_text += page.extract_text() + "\n"
                
                contexto_adicional = f"\n📄 MODELO FUENTE (TEXTO EXACTO A USAR):\n{doc_text[:15000]}..." 
                doc_instruction = "Tu tarea es RELLENAR los espacios del 'MODELO FUENTE' con los datos nuevos. Manten el texto lo más idéntico posible."
                
                # Generar Preview Header
                data_dict = {
                    "materia": materia, "nombre_menor": nombre_menor, 
                    "nombre_dte": nombre_dte, "nombre_ddo": nombre_ddo,
                    "abogado": abogado, "rut_dte": rut_dte, "rut_ddo": rut_ddo,
                    "domicilio": domicilio, "domicilio_dte": "GENERAL CELEDÓN Nº 10290, DEPTO 202",
                    "domicilio_abogado": domicilio_abogado, "rut_abogado_val": rut_abogado_val
                }
                _, header_preview = get_header_docx(selected_doc, data_dict)
                
            except Exception as e:
                doc_instruction = f"Error leyendo archivo: {e}"
        else:
            doc_instruction = "Busca en la base de datos el modelo más apropiado para esta materia."
        
        full_prompt = f"""ACTÚA COMO UN DIGITADOR LEGAL EXPERTO.
        Objetivo: Generar una demanda de {materia} para presentar en: {tribunal}.
        
        INSTRUCCIONES CLAVE DE ESTILO:
        1. **LENGUAJE NATURAL Y PROFESIONAL**: Redacta como un abogado humano experimentado. 
           - Evita frases robóticas, listas innecesarias o repeticiones mecánicas.
           - Mantén la fluidez narrativa de los hechos.
           - Usa terminología jurídica precisa (ej: "alimentante", "alimentario", "causante").
        
        INSTRUCCIONES DE FORMATO:
        2. Tienes abajo un 'MODELO FUENTE'. Tu trabajo es COPIAR el cuerpo de ese modelo.
        3. REEMPLAZAR los datos antiguos (Nombres, RUTs, 'XXXXX') por los DATOS NUEVOS que te doy.
        4. ACTUALIZAR cualquier ley citada que esté derogada.
        5. **MUY IMPORTANTE**: YO YA ESCRIBÍ EL ENCABEZADO (LA TABLA, LA SUMA, EL TRIBUNAL, LA COMPARECENCIA Y LA INTERPOSICIÓN DE LA DEMANDA).
        6. **TU TRABAJO EMPIEZA DONDE DICE "LOS HECHOS"**.
        7. NO repitas la suma, ni "A S.S. RESPETUOSAMENTE DIGO", ni "Que vengo en interponer...".
        8. EMPIEZA TU RESPUESTA DIRECTAMENTE CON EL TÍTULO "LOS HECHOS" y el primer párrafo narrativo.
        
        DATOS NUEVOS:
        - Dte: {nombre_dte} ({rut_dte}). Abogado: {abogado} (RUT: {rut_abogado_val}).
        - Domicilio Abogado/Estudio: {domicilio_abogado} (Usar en el "Cuarto Otrosí" o donde corresponda).
        - Ddo: {nombre_ddo} ({rut_ddo}). Domicilio: {domicilio}.
        - Niño: {nombre_menor}.
        - Historia nueva: {otros_datos}
        
        {contexto_adicional}
        """
        
        # Inyectar al Chat (Visible usuario)
        ui_prompt = f"Generar escrito basado en '{selected_doc}' para {nombre_dte} vs {nombre_ddo}."
        st.session_state.history.append({"role": "user", "text": ui_prompt})
        
        import time
        max_retries = 3
        wait_time = 20

        # 1. INICIAR CONEXIÓN (CON SPINNER)
        response = None
        with st.spinner("⚖️ Digitando y reemplazando datos..."):
            for attempt in range(max_retries):
                try:
                    response = st.session_state.chat_session.send_message(full_prompt, stream=True)
                    break 
                except Exception as e:
                    # Retry logic inside spinner
                    is_quota_error = "429" in str(e) or "Quota exceeded" in str(e)
                    if is_quota_error and attempt < max_retries - 1:
                        time.sleep(20)
                    else:
                        st.error(f"Error al conectar: {e}")
                        response = None
                        break
        
        # 2. STREAMING (SIN SPINNER PUES YA TENEMOS CONEXIÓN)
        if response:
            try:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = ""
                    
                    # Header Preview
                    if header_preview.strip():
                        full_response += f"**VISTA PREVIA ENCABEZADO (Automático):**\n```text\n{header_preview}\n```\n\n**DESARROLLO (IA):**\n"
                    
                    accumulated_body = ""
                    # Consumir el stream
                    for chunk in response:
                        if chunk.text:
                            accumulated_body += chunk.text
                            message_placeholder.markdown(full_response + accumulated_body + "▌")
                    
                    # Final flush
                    message_placeholder.markdown(full_response + accumulated_body)
                
                # Guardar persistencia
                body_text = accumulated_body.replace("\n", "\n\n")
                st.session_state.is_generated_doc = True
                st.session_state.last_header = header_preview
                st.session_state.last_body = body_text
                st.session_state.selected_doc_for_download = selected_doc
                st.session_state.data_dict_for_download = data_dict
                
                st.session_state.history.append({"role": "assistant", "text": full_response + accumulated_body})
                st.rerun()
                
            except Exception as e:
                    st.error(f"Error durante streaming: {e}")

# --- INTERFAZ ---
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["text"])

# --- ÁREA DE DESCARGA PERSISTENTE ---
if st.session_state.get("is_generated_doc", False):
    st.divider()
    st.subheader("📥 Documento Generado")
    
    # Re-generar doc binario
    try:
        final_doc, _ = get_header_docx(st.session_state.selected_doc_for_download, st.session_state.data_dict_for_download)
        # Añadir body
        # Ojo: last_body tiene saltos markdown \n\n. Para docx queremos \n.
        # Pero bueno, dejemoslo tal cual por ahora o hagamos replace inverso si queda muy separado.
        final_doc.add_paragraph(st.session_state.last_body.replace("\n\n", "\n"))
        
        bio = io.BytesIO()
        final_doc.save(bio)
        
        st.download_button(
            label="📄 Descargar Documento",
            data=bio.getvalue(),
            file_name="Demanda_Final.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary"
        )
    except Exception as e:
        st.error(f"Error preparando descarga: {e}")

# --- CHAT CONSULTAS (SOLO TEXTO) ---
if prompt := st.chat_input("Hacer consulta jurídica (No genera documento)..."):
    st.session_state.is_generated_doc = False # Ocultar descarga anterior si empieza chat nuevo? O mantenerlo? Mejor mantener.
    # Pero si el usuario chatea, es confuso tener el boton descarga del doc anterior.
    # Desactivemos descarga si cambia contexto.
    if st.session_state.get("is_generated_doc"):
        st.session_state.is_generated_doc = False
        st.rerun()

    st.chat_message("user").write(prompt)
    st.session_state.history.append({"role": "user", "text": prompt})

    with st.chat_message("assistant"):
        with st.spinner("⚖️ Consultando leyes..."):
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = st.session_state.chat_session.send_message(prompt)
                    text_response = response.text
                    st.write(text_response)
                    st.session_state.history.append({"role": "assistant", "text": text_response})
                    break # Success
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        wait_time = 20 # Default wait
                        st.warning(f"⚠️ Límite de tráfico gratuito alcanzado. Reintentando en {wait_time} segundos... (Habilitar facturación elimina esto)")
                        time.sleep(wait_time)
                        continue
                    else:
                        st.error(f"Error: {e}")
                        break
# ⚖️ Agente Judicial (Motor Documental AI)

## Descripción del Proyecto
Software de automatización documental (LegalTech) diseñado para la generación masiva de escritos legales con alta fidelidad estructural. El sistema busca resolver el problema de la "alucinación de formato" en LLMs mediante un enfoque híbrido de procesamiento.

## Stack Técnico
*   **Frontend**: Streamlit.
*   **LLM Engine**: Google Gemini (via `google-generativeai`).
*   **Vector Store**: ChromaDB (Persistencia local en disco).
*   **Procesamiento Doc**: `python-docx` (Manipulación XML de documentos Word).

## Arquitectura de Solución
El sistema opera bajo un pipeline RAG (Retrieval Augmented Generation) modificado:
1.  **Ingesta Vectorial**: Los documentos `.docx` se indexan en ChromaDB para búsqueda semántica.
2.  **Context Slicing (Python)**: Antes de enviar un documento al LLM, un algoritmo de corte elimina el encabezado y preámbulo para evitar tokens redundantes.
3.  **Prompt Engineering**: Se utiliza una "Persona de Fotocopiadora" con restricciones negativas (Negative Constraints) para prohibir resúmenes y Markdown.
4.  **Reconstrucción Programática**: El encabezado legal (Suma, Tribunal, Intro) se genera 100% con código Python para garantizar consistencia, mientras la IA se encarga solo del cuerpo narrativo.

## Flujo de Trabajo (Pipeline)
1.  Usuario selecciona plantilla (ID: 1025).
2.  Sistema recupera Docx físico + Metadatos.
3.  Python inyecta datos clave (RUTs, Nombres) en el prompt.
4.  Gemini genera el cuerpo ("Los Hechos" -> "Otrosís").
5.  Python ensambla Encabezado + Cuerpo IA.
6.  Salida: Documento `.docx` listo para descarga.

## Instalación y Uso
1.  Pon tus modelos Word/PDF en la carpeta `docs/`.
2.  Ejecuta `streamlit run app.py`.
3.  En la barra lateral, presiona "Actualizar IA" para procesar tus nuevos documentos.
4.  **Método Recomendado:** Usa la **"📝 Ficha del Caso"** en la parte superior para ingresar los datos (Demandante, Demandado, RUTs) de forma ordenada y elegir tu modelo.
5.  O bien, chatea directamente con el agente para generar tus escritos.

## Gestión de Archivos (Nuevo)
Puedes agregar modelos de dos formas:
*   **Manual:** Arrastrando archivos a la carpeta `docs/`.
*   **Visual:** Usando el **"Cargador de Archivos"** en el menú lateral de la App.

## Tecnología de Redacción 2.0 (La "Fotocopiadora Inteligente")
Hemos actualizado el motor de IA para garantizar fidelidad absoluta:
1.  **Cero Alucinaciones:** El sistema ahora corta quirúrgicamente el texto del modelo base para evitar duplicar encabezados.
2.  **Modo "Find & Replace":** La IA tiene prohibido resumir. Su única función es reemplazar datos (Nombres, RUTs) manteniendo intacta la redacción original.
3.  **Seguridad de Formato:** Un algoritmo de post-procesamiento elimina cualquier intento de la IA de generar tablas o títulos que ya existen.

## Guía Para Agregar Nuevos Modelos 📁
Para que la IA encuentre y use tus nuevos documentos a la perfección, sigue estas "Reglas de Oro":

### 1. Nombres de Archivo Claros
Usa nombres que incluyan un **Número Identificador** o una **Materia Clara**. La IA busca mejor por números.
*   ✅ `DEMANDA_ALIMENTOS_1025.docx` (Excelente, el "1025" es único)
*   ✅ `DIVORCIO_MUTUO_ACUERDO_2024.docx`
*   ❌ `documento final version 2.docx` (Muy genérico)

### 2. Estructura del Documento
El sistema es robusto, pero funciona mejor si tu documento tiene:
*   Un **Encabezado Claro** ("EN LO PRINCIPAL...").
*   Un Título **"1.- LOS HECHOS"** o **"LOS HECHOS"** para que el sistema sepa dónde empieza el cuerpo del escrito.

### 3. Actualización
¡Muy Importante! Cada vez que agregues un archivo a la carpeta `docs/`, debes ir a la App y presionar el botón **"🔄 Actualizar IA con nuevos Docs"**. Si no lo haces, la IA no sabrá que el archivo existe.

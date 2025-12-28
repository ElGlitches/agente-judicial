# El Digitador Legal IA

## Resumen del Proyecto
**El digitador Legal IA** es un software propio de redacción jurídica diseñado para automatizar la creación de escritos legales manteniendo un control estricto sobre el formato.

## El Problema
Los abogados gastamos horas redactando escritos que son, en un 80%, "copiar y pegar" formatos antiguos (cambiando nombres, RUTs y fechas). Las IAs genéricas (como ChatGPT) "alucinan" formatos, inventan estructuras o ignoran el estilo visual específico de la oficina (Sumas, Otrosíes, márgenes).

## La Solución
Hemos construido un sistema híbrido que combina:
1.  **Tu Biblioteca Privada ("La Memoria"):** Una base de datos segura (ChromaDB Local) donde guardas tus escritos exitosos (ej. "Modelo 1025").
2.  **Un Cerebro Inteligente ("El Digitador"):** Un motor (Google Gemini) instruido para actuar como un digitador obediente, no creativo.

## Cómo Funciona (El Flujo)
1.  **Solicitud:** Pides *"Redacta una demanda usando mi formato 1025"*.
2.  **Búsqueda:** El sistema busca el archivo físico en tu carpeta `docs/`.
3.  **Clonación:** La IA lee el archivo y "clona" la estructura visual exacta (márgenes, tablas, otrosíes).
4.  **Relleno:** La IA rellena solo los datos variables (Nombres, RUTs) y fundamenta con Ley actualizada (conectándose a la BCN si es necesario).

## Filosofía
> "El formato es sagrado". 
La IA no debe "mejorar" el estilo, solo rellenar los datos.

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

## Guía Para Agregar Nuevos Modelos 📁
Para que la IA encuentre y use tus nuevos documentos a la perfección, sigue estas "Reglas de Oro":

### 1. Nombres de Archivo Claros
Usa nombres que incluyan un **Número Identificador** o una **Materia Clara**. La IA busca mejor por números.
*   ✅ `DEMANDA_ALIMENTOS_1025.docx` (Excelente, el "1025" es único)
*   ✅ `DIVORCIO_MUTUO_ACUERDO_2024.docx`
*   ❌ `documento final version 2.docx` (Muy genérico)

### 2. Formato del Documento
No necesitas hacer nada especial, pero ayuda si:
*   Mantienes los títulos claros (**EN LO PRINCIPAL**, **PRIMER OTROSÍ**).
*   Si quieres que la IA sepa exactamente cómo se llama el archivo (para confirmar que lo encontró), puedes poner en la primera línea en letra pequeña: `[[NOMBRE ARCHIVO: MODELO 1025]]`.

### 3. Actualización
¡Muy Importante! Cada vez que agregues un archivo a la carpeta `docs/`, debes ir a la App y presionar el botón **"🔄 Actualizar IA con nuevos Docs"**. Si no lo haces, la IA no sabrá que el archivo existe.

# ⚖️ Agente Judicial IA
**Asistente Inteligente de Redacción Legal**

## 📄 ¿Qué es este sistema?
**Agente Judicial** es una herramienta profesional diseñada para facilitar la labor del abogado, automatizando la redacción de escritos repetitivos (demandas, escritos de mero trámite, etc.) sin sacrificar la calidad ni el formato visual de su oficina.

A diferencia de otras inteligencias artificiales, este sistema **respeta sagradamente sus formatos**: utiliza sus propios archivos Word como plantilla, copiando el estilo visual (tablas, márgenes, sumas) y redactando únicamente el contenido narrativo necesario.

## ✨ Funcionalidades Clave

### 1. Fidelidad Absoluta de Formato 
El sistema toma su modelo Word y lo replica con exactitud.
*   **Encabezados y Tablas:** Se mantienen idénticos.
*   **Otrosíes:** Se copian textuales.
*   **Cero Riesgos:** La IA no tiene permiso para "inventar" formatos nuevos.

### 2. Redacción Adaptativa e Inteligente
Para secciones como "LOS HECHOS", el sistema actúa como un redactor experto:
*   Toma la historia base del caso.
*   La adapta al estilo de redacción de su plantilla.
*   **Sensibilidad de Género:** Distingue automáticamente si se trata de un "Niño" o "Niña", y si el demandado es "Padre" o "Madre", ajustando la gramática del texto.

### 3. Conexión Directa a la BCN 🏛️
Seguridad jurídica ante todo. Si el sistema detecta qu se cita una ley (ej. Ley de Alimentos 14.908), **descarga el texto oficial y vigente desde la Biblioteca del Congreso Nacional** antes de redactar. Esto asegura que sus escritos nunca citen normas derogadas.

## 🚀 Guía de Uso (Paso a Paso)

### Paso 1: Seleccione su Caso
En el panel lateral izquierdo, encontrará una lista con sus modelos disponibles (ej. `DEMANDA_ALIMENTOS_1025.docx`). Seleccione el que corresponda a su trámite.

### Paso 2: Complete la Ficha
En la pantalla aparecerá un formulario simple. Ingrese los datos clave:
*   **Tribunal y Materia.**
*   **Partes:** Demandante, Demandado, Niño/a.
*   **Abogados:** Patrocinante y Apoderado.
*   **Historia:** Un breve resumen de los hechos nuevos.

### Paso 3: Genere el Documento
Presione el botón **"✨ Redactar Escrito"**.
El sistema procesará la información y le mostrará una vista previa en tiempo real. Al finalizar, podrá descargar el archivo `.docx` listo para imprimir o firmar, sin necesidad de ediciones complejas.

## 📂 Gestión de Sus Modelos (Carpeta `docs/`)
Para que el sistema aprenda sus formatos, simplemente guarde sus archivos Word en la carpeta `docs` del proyecto.
*   **Recomendación:** Use nombres claros como `DIVORCIO_MUTUO.docx`.
*   **Nota:** Una vez guardado el archivo, presione el botón "🔄 Recargar" en la aplicación.

## 🔐 Gestión de Usuarios y SaaS
El sistema incluye un módulo de administración completo:
*   **Usuarios:** Gestión vía base de datos local (`saas.db`).
*   **Créditos:** Sistema de cuotas (ej: 3 escritos gratis) con bloqueo automático (Paywall).
*   **Admin:** Usuario `admin` con privilegios ilimitados.

---
*Desarrollado con tecnología de vanguardia para la eficiencia legal.*

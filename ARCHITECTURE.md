# Arquitectura del Sistema: Agente Judicial

Este documento describe el flujo de datos y la arquitectura técnica del Agente Judicial, con énfasis en la integridad de datos y la orquestación de servicios externos (BCN, RAG y Motor de Documentos).

## Diagrama de Flujo de Datos

El siguiente diagrama Mermaid ilustra cómo una solicitud de usuario se transforma en un documento legal válido.

```mermaid
graph TD
    %% Nodos Principales
    User([👤 Usuario])
    UI[🖥️ Interfaz Streamlit app.py]
    
    subgraph "Capas de Lógica"
        Orchestrator{⚙️ Orquestador}
        Extractor[🧠 LLM Extractor - JSON]
        Redactor[📝 LLM Redactor - Fase 1 & 2]
    end

    subgraph "Servicios Externos & APIs"
        BCN[🏛️ API BCN - tools_bcn.py]
        RAG[📚 ChromaDB - rag_logic.py]
        PJUD[📊 PJUD Stats - tools_pjud.py]
    end

    subgraph "Motor de Documentos"
        TemplateReader[📂 Lector Plantilla - doc_logic.py]
        DocBuilder[🔨 Constructor .docx]
        FileSystem[💾 Sistema de Archivos]
    end

    %% Flujo
    User -->|1. Historia / Evidencia PDF| UI
    UI -->|2. Datos Crudos| Orchestrator
    
    Orchestrator -->|3. Extraer Entidades| Extractor
    Extractor -->|4. JSON Estructurado| Orchestrator
    
    Orchestrator -->|5. Identificar Materia/Leyes| BCN
    BCN -->|6. Texto Ley Oficial| Orchestrator
    
    Orchestrator -->|7. Buscar Modelos Similares| RAG
    RAG -->|8. Contexto Semántico| Orchestrator
    
    Orchestrator -->|9. Prompt + Contexto + JSON| Redactor
    Redactor -->|10. Texto Generado - Hechos y Derecho| DocBuilder
    
    Orchestrator -->|11. Seleccionar Plantilla Base| TemplateReader
    TemplateReader -->|12. Objeto Docx - Header y Tablas| DocBuilder
    
    DocBuilder -->|13. Ensamble Final| FileSystem
    FileSystem -->|14. Descarga WORD| UI
    UI -->|15. Archivo Final| User

    %% Estilos
    style BCN fill:#f9f,stroke:#333,stroke-width:2px
    style RAG fill:#bbf,stroke:#333,stroke-width:2px
    style DocBuilder fill:#bfb,stroke:#333,stroke-width:2px
```

## Explicación de Componentes

### 1. Orquestador (`app.py`)
Es el cerebro de la aplicación. Maneja el estado de la sesión (`st.session_state`), decide qué herramientas llamar y coordina el flujo en dos fases críticas:
*   **Fase de Análisis:** Llama al Extractor para convertir texto libre en datos estructurados.
*   **Fase de Generación:** Construye el prompt final inyectando el contexto legal (BCN) y los ejemplos (RAG).

### 2. Conector BCN (`tools_bcn.py`)
Garantiza la validez jurídica.
*   **Input:** Identificador de Ley (ej: "14908").
*   **Proceso:** Consulta la API XML de leychile.cl.
*   **Output:** Texto limpio y vigente de la norma para que el LLM no "alucine" leyes derogadas.

### 3. Motor de Documentos (`doc_logic.py`)
Responsable de la fidelidad visual.
*   **Preservación:** No genera texto plano; manipula objetos `python-docx`.
*   **Hibridación:** Mantiene el encabezado y las tablas originales de la plantilla del usuario y solo inyecta el contenido nuevo generado por la IA en el cuerpo del documento.

# Guía de Despliegue: Agente Jurídico en la Nube ☁️

Para que tu cliente en otra ciudad pueda usar el **Agente Jurídico**, la mejor opción es desplegarlo en **Streamlit Community Cloud**. Es gratuito, seguro y fácil de actualizar.

## Pasos para Desplegar

### 1. Preparar GitHub
¡Buenas noticias! Ya tienes tu repositorio listo en: `https://github.com/ElGlitches/agente-judicial`.
Solo necesitamos "empujar" (push) los últimos cambios para que estén disponibles en la nube.

(Si no hubieras tenido uno, aquí te explicaría cómo crearlo, pero ya estás cubierto).

### 2. Conectar a Streamlit Cloud
1.  Ve a [streamlit.io/cloud](https://streamlit.io/cloud) e inicia sesión (puedes usar tu cuenta de GitHub).
2.  Haz clic en **"New app"**.
3.  Selecciona tu repositorio (`agente-juridico-privado`), la rama (`main`) y el archivo principal (`app.py`).

### 3. Configurar Secretos (La Clave API) 🔑
Esta es la parte más importante. **NO subas tu archivo `.env` a GitHub.** Streamlit usa un gestor de secretos seguro.

1.  En la configuración de tu App en Streamlit (antes o después de desplegar), ve a **Settings** -> **Secrets**.
2.  Copia y pega el contenido de tu archivo `.env` local, o escribe manualmente:

```toml
GOOGLE_API_KEY = "TU_CLAVE_AQUI_PEGA_LA_LARGA"
```

### 4. Desplegar 🚀
Haz clic en **Deploy!**. Streamlit instalará las librerías (`requirements.txt`) y arrancará tu Agente.

## ¿Qué verá tu cliente?
Obtendrás una URL única (ej: `https://agente-juridico-ivan.streamlit.app`).
*   Envía esa URL a tu cliente.
*   Él podrá entrar, llenar los datos y generar demandas desde su navegador, sin instalar nada.

## Notas Importantes
## Opción B: Compartir desde tu PC (Túnel) 🚇
Si prefieres no subir nada a la nube y que la gente se conecte directo a tu computador:

### Usando `ngrok` (Recomendado)
Esta herramienta crea un "puente" seguro desde internet hasta tu puerto 8501.

1.  **Instalar**: ¡Ya lo hice por ti!
2.  **Autenticar (Solo la primera vez)**: 
    *   Crea una cuenta gratis en [ngrok.com](https://dashboard.ngrok.com/signup).
    *   Copia tu "Authtoken" del panel de control.
    *   Ejecuta en la terminal:
        ```bash
        ./ngrok config add-authtoken TU_TOKEN_AQUI
        ```
3.  **Conectar**: Ahora sí, lanza el túnel:
    ```bash
    ./ngrok http 8504
    ```
4.  **Compartir**: Ngrok te dará una URL (ej: `https://a1b2-c3d4.ngrok-free.app`).
4.  **Listo**: Mándale ese link a tu cliente.

### Opción C: Túnel Mágico (Sin instalación ni cuentas) 🪄
Este es un truco secreto de programadores. Usa `ssh`, que ya viene en tu Mac.

1.  Abre la terminal.
2.  Escribe y presiona Enter:
    ```bash
    ssh -R 80:localhost:8504 nokey@localhost.run
    ```
    *(Si te pregunta "Are you sure...", escribe `yes` y dale Enter).*
3.  Te mostrará un mensaje como:
    `Connect to http://tunel-xyz.localhost.run`
4.  ¡Ese es tu link público! Copialo y úsalo.

### Pros y Contras
*   ✅ **Ultra Rápido**: Sin cuentas, sin bajar nada.
*   ✅ **Fácil**: 1 línea de comando.
*   ❌ **Inestable**: A veces se desconecta si hay mucha gente usándolo.
*   ❌ **Pc Encendido**: Igual que el anterior, muere si cierras la terminal.

---
## Notas Importantes sobre SaaS
*   **Base de Datos (`saas.db`)**: En Streamlit Cloud, el sistema de archivos es "efímero". Si la app se reinicia, **se perderán los usuarios y créditos acumulados**.
*   **Solución Profesional**: Para producción real, deberíamos conectar `saas.db` a una base de datos externa (como Supabase o Google Sheets) o usar un hosting con disco persistente (Railway/Render). Por ahora, para demos, funciona perfecto.
*   **Velocidad**: La primera vez puede tardar unos minutos en instalar todo.

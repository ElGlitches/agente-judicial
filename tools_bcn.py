import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re

def obtener_ley_bcn(input_usuario):
    """
    Versión Optimizada: Consulta directamente la API XML de la BCN usando el número de ley (idLey),
    evitando la necesidad de 'scrapear' el idNorma primero.
    """
    input_usuario = str(input_usuario).strip()
    # User-Agent de navegador real para evitar bloqueos
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    # 1. Limpiar input (dejar solo números)
    numero_limpio = ''.join(filter(str.isdigit, input_usuario))
    if not numero_limpio:
        return "❌ Error: Ingresa solo el número de la ley."

    print(f"⬇️  Descargando texto oficial Ley N° {numero_limpio}...")
    
    # 2. CONSULTA DIRECTA (Usando idLey en vez de idNorma)
    url_api = f"https://www.leychile.cl/Consulta/obtxml?opt=7&idLey={numero_limpio}"
    
    try:
        resp_xml = requests.get(url_api, headers=headers, timeout=30)
        resp_xml.encoding = 'utf-8' # Forzamos UTF-8
        
        if resp_xml.status_code != 200:
            return "❌ Error al descargar el contenido (Status Code no es 200)."

        if len(resp_xml.content) == 0:
             return f"❌ La Ley {numero_limpio} no parece existir o no tiene contenido digital disponible en esta API."

        # Limpieza simple
        soup = BeautifulSoup(resp_xml.content, "xml") # Usamos xml parser explícitamente
        
        # Borrar basura (metadatos XML que no son texto de la ley)
        for tag in soup.find_all(['Identificador', 'Metadatos', 'Promulgacion', 'Publicacion', 'Anexos', 'Encabezado']):
            tag.decompose()
            
        texto = soup.get_text(separator="\n").strip()
        texto = re.sub(r'\n\s*\n', '\n\n', texto)
        
        if len(texto) < 50:
             return "⚠️ El texto descargado está vacío o es muy corto."
             
        return texto

    except Exception as e:
        return f"❌ Error procesando XML: {e}"

if __name__ == "__main__":
    ley = input("Ingresa N° de Ley (ej: 21000): ")
    res = obtener_ley_bcn(ley)
    print("\n--- INICIO DEL TEXTO LEGAL ---\n")
    print(res[:1000] + "..." if len(res) > 1000 else res)
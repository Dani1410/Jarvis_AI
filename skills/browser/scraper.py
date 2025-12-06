import os
import requests
from bs4 import BeautifulSoup
from . import voz

def leer_pagina(url):
    """Extrae contenido inteligente de una página web."""
    try:
        voz.hablar("Analizando contenido inteligente...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        respuesta = requests.get(url, headers=headers)
        
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        
        texto_acumulado = ""

        # 1. Extraer Título Principal (H1)
        titulo = soup.find('h1')
        if titulo:
            texto_acumulado += f"TITULO: {titulo.text.strip()}\n"

        # 2. Extraer Subtítulos y Texto (H2 y P)
        bloques = soup.find_all(['h2', 'p'])
        
        for bloque in bloques:
            texto = bloque.text.strip()
            if bloque.name == 'h2':
                texto_acumulado += f"\nSUBTÍTULO: {texto}\n"
            elif bloque.name == 'p' and len(texto) > 50:
                texto_acumulado += f"{texto} "
        
        return texto_acumulado[:3500]
        
    except Exception as e:
        return f"Error de lectura: {e}"

def descargar_archivo(url, nombre_salida):
    """Descarga un archivo desde una URL."""
    try:
        voz.hablar("Iniciando descarga...")
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            ruta_carpeta = os.path.join(os.getcwd(), "Descargas_Jarvis")
            os.makedirs(ruta_carpeta, exist_ok=True)
            
            ruta_final = os.path.join(ruta_carpeta, nombre_salida)
            
            with open(ruta_final, 'wb') as f:
                f.write(response.content)
            return f"Archivo guardado en la carpeta Descargas Jarvis."
        else:
            return "El enlace no parece válido."
    except Exception as e:
        return f"Error en descarga: {e}"
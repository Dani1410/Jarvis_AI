import os
import time
import requests
import psutil
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from . import voz

# Cargar variables de entorno
load_dotenv()
RUTA_PERFIL = os.getenv('CHROME_PROFILE_PATH')

def chrome_esta_abierto():
    """Verifica si hay procesos de Chrome corriendo que bloqueen el perfil."""
    for proc in psutil.process_iter(['name']):
        try:
            if 'chrome' in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def iniciar_driver():
    """Inicia Chrome de forma segura y robusta."""
    
    # 1. Si detectamos Chrome abierto, intentamos cerrarlo nosotros mismos (Opcional)
    # Si prefieres que te avise, deja el aviso. Si prefieres que sea agresivo:
    if chrome_esta_abierto():
        voz.hablar("Cerrando procesos de Chrome para liberar tu perfil...")
        os.system("taskkill /F /IM chrome.exe /T") # /T mata el árbol de procesos
        time.sleep(2) # Damos tiempo a que muera

    opciones = Options()
    if RUTA_PERFIL:
        opciones.add_argument(f"user-data-dir={RUTA_PERFIL}")
        # Asegúrate que este sea el nombre correcto que viste en chrome://version
        opciones.add_argument("--profile-directory=Profile 1") 
    
    # --- LA SOLUCIÓN AL ERROR DevToolsActivePort ---
    opciones.add_argument("--remote-debugging-port=9222") # Fuerza el puerto
    opciones.add_argument("--no-sandbox") # Vital para algunos sistemas
    opciones.add_argument("--disable-dev-shm-usage") # Evita problemas de memoria compartida
    # -----------------------------------------------

    opciones.add_experimental_option("detach", True) 
    opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    try:
        voz.hablar("Abriendo navegador...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opciones)
        return driver
    except Exception as e:
        voz.hablar("Falló el inicio de Chrome.")
        print(f"Error Crítico Selenium: {e}")
        return None

# --- SCRAPING INTELIGENTE (MEJORADO) ---
def leer_pagina(url):
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
        # Buscamos etiquetas h2 y p para dar estructura
        bloques = soup.find_all(['h2', 'p'])
        
        for bloque in bloques:
            texto = bloque.text.strip()
            if bloque.name == 'h2':
                texto_acumulado += f"\nSUBTÍTULO: {texto}\n"
            elif bloque.name == 'p' and len(texto) > 50: # Ignoramos párrafos basura muy cortos
                texto_acumulado += f"{texto} "
        
        # Limpieza final y recorte
        return texto_acumulado[:3500] # Un poco más de contexto para Llama 3.2
        
    except Exception as e:
        return f"Error de lectura: {e}"

# --- 2. DESCARGAS ---
def descargar_archivo(url, nombre_salida):
    try:
        voz.hablar("Iniciando descarga...")
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            # Crea la carpeta si no existe
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

# --- 3. REDES SOCIALES (Twitter/X) ---
def publicar_twitter(mensaje):
    driver = iniciar_driver()
    if not driver: return

    try:
        voz.hablar("Entrando a X...")
        driver.get("https://twitter.com/compose/tweet")
        time.sleep(6) # Esperamos a que cargue
        
        # Escribe en el elemento activo (la caja de tweet)
        elemento_activo = driver.switch_to.active_element
        elemento_activo.send_keys(mensaje)
        
        voz.hablar("Tweet escrito. Presiona Control + Enter para enviarlo.")
        
    except Exception as e:
        print(e)
        voz.hablar("Hubo un problema con la interfaz de Twitter.")
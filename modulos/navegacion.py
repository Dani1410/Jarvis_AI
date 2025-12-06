import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from . import voz

# --- CONFIGURACIÓN PARA TU USUARIO axel0 ---
# Esta ruta apunta a tu perfil real de Chrome para no tener que loguearte cada vez
RUTA_PERFIL_CHROME = r"C:\Users\axel0\AppData\Local\Google\Chrome\User Data"

def iniciar_driver():
    """Inicia Chrome con tu perfil real (cookies, sesiones abiertas)"""
    opciones = Options()
    opciones.add_argument(f"user-data-dir={RUTA_PERFIL_CHROME}")
    opciones.add_argument("--profile-directory=Default") # Usa el perfil principal
    # Mantiene el navegador abierto aunque acabe el script
    opciones.add_experimental_option("detach", True) 
    # Oculta mensajes molestos de automatización
    opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    try:
        voz.hablar("Abriendo navegador...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opciones)
        return driver
    except Exception as e:
        voz.hablar("Error. Cierra todas las ventanas de Chrome y vuelve a intentar.")
        print(f"Error Selenium: {e}")
        return None

# --- 1. LEER NOTICIAS ---
def leer_pagina(url):
    try:
        voz.hablar("Analizando sitio web...")
        # Headers para parecer un humano y no un robot
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        respuesta = requests.get(url, headers=headers)
        
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        
        # Extraemos párrafos <p>
        parrafos = soup.find_all('p')
        texto_completo = " ".join([p.text for p in parrafos])
        
        # Cortamos a 3000 caracteres para no saturar a Ollama
        return texto_completo[:3000]
    except Exception as e:
        return f"No pude leer la página: {e}"

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
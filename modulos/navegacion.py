import os
import time
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from . import voz
from dotenv import load_dotenv 

load_dotenv()

CHROME_PROFILE_SELENIUM_PATH = os.getenv('CHROME_PROFILE_SELENIUM_PATH')
RUTA_PERFIL = os.getenv('CHROME_PROFILE_SELENIUM_PATH')

# --- CONFIGURACIÓN DE PERFIL DEDICADO ---
# Usamos la carpeta que tú definiste para que no choque con tu Chrome normal
PROFILE_DIR = Path(CHROME_PROFILE_SELENIUM_PATH)

def ensure_profile_dir():
    """Asegura que la carpeta del perfil exista"""
    if not PROFILE_DIR.exists():
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)

def iniciar_driver():
    """Inicia el Chrome de Jarvis (independiente del tuyo)."""
    ensure_profile_dir()
    
    opciones = Options()
    # Usamos el perfil dedicado en C:\temp...
    opciones.add_argument(f"user-data-dir={PROFILE_DIR}")
    
    # Optimizaciones para estabilidad
    opciones.add_argument("--no-first-run")
    opciones.add_argument("--no-default-browser-check")
    opciones.add_argument("--disable-extensions")
    opciones.add_experimental_option("detach", True) 
    opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    try:
        # Ya no hace falta voz.hablar aquí para no ser repetitivo, 
        # a menos que falle.
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opciones)
        return driver
    except Exception as e:
        voz.hablar("Error crítico al iniciar el navegador de Jarvis.")
        print(f"Error Selenium: {e}")
        return None

# --- FUNCIONES DE WHATSAPP ---
def abrir_whatsapp_web():
    driver = iniciar_driver()
    if not driver: return

    try:
        voz.hablar("Abriendo WhatsApp Web en perfil dedicado...")
        driver.get("https://web.whatsapp.com/")
        
        # Esperamos un poco para verificar si pide QR o si ya entró
        voz.hablar("Cargando... Si es la primera vez, escanea el código QR ahora.")
        time.sleep(10) 
        
        return "WhatsApp abierto exitosamente."
    except Exception as e:
        return f"Error abriendo WhatsApp: {e}"

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

def leer_mensajes_whatsapp():
    driver = iniciar_driver()
    if not driver: return "Error de navegador."

    try:
        voz.hablar("Buscando mensajes nuevos...")
        driver.get("https://web.whatsapp.com/")
        time.sleep(10) # Espera importante para que cargue la lista
        
        # --- PASO 1: ENCONTRAR CHAT NO LEÍDO EN LA BARRA LATERAL ---
        try:
            # Buscamos en el HTML que me pasaste el aria-label="X mensajes no leídos"
            chat_nuevo = driver.find_element(By.XPATH, '//span[contains(@aria-label, "no leído")]')
            
            # Dibujamos borde rojo para que veas cuál encontró (Depuración)
            driver.execute_script("arguments[0].style.border='3px solid red'", chat_nuevo)
            
            voz.hablar("Encontré mensajes nuevos. Abriendo chat...")
            chat_nuevo.click() # Damos clic para entrar a la conversación
            time.sleep(3) # Esperamos a que carguen los mensajes de la derecha
            
        except:
            voz.hablar("No veo chats nuevos. Leeré la conversación que tengas abierta.")

        # --- PASO 2: LEER LOS MENSAJES DE LA DERECHA (EL CHAT REAL) ---
        print("[DEBUG] Analizando conversación...")
        
        try:
            # Buscamos burbujas de mensaje. 
            # La clase 'message-in' son los mensajes RECIBIDOS (blancos).
            # La clase 'message-out' son los tuyos (verdes).
            # Queremos leer el último recibido.
            
            # Buscamos todos los contenedores de mensajes recibidos
            mensajes_recibidos = driver.find_elements(By.XPATH, '//div[contains(@class, "message-in")]')
            
            if not mensajes_recibidos:
                # Si no hay 'message-in', quizás el último mensaje es tuyo o es un sticker
                return "El chat está vacío o el último mensaje lo enviaste tú."

            # Tomamos el último mensaje de la lista (el más reciente)
            ultimo_bloque = mensajes_recibidos[-1]
            
            # Dentro del bloque, buscamos el texto copiable (selectable-text)
            try:
                elemento_texto = ultimo_bloque.find_element(By.CSS_SELECTOR, "span.selectable-text")
                texto_mensaje = elemento_texto.text
                
                # Coloreamos amarillo para que veas qué leyó
                driver.execute_script("arguments[0].style.backgroundColor='yellow'", elemento_texto)
                
                return f"El mensaje dice: {texto_mensaje}"
            except:
                return "El último mensaje parece ser una foto, sticker o audio."

        except Exception as e:
            print(f"Error extrayendo texto: {e}")
            return "No pude leer el texto del chat abierto."

    except Exception as e:
        print(f"Error general WA: {e}")
        return "Hubo un error técnico."
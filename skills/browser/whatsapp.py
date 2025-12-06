import time
import re
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException

# ✅ CORRECTO: Importar desde el módulo local
from . import driver as browser_handler 

# ❌ FALTA: Importar voz desde core
try:
    from core import voz
except ImportError:
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from core import voz

# Configuración básica de espera
WAIT_TIMEOUT = 20

def abrir():
    """Abre WhatsApp Web usando el driver compartido."""
    driver = browser_handler.iniciar_driver()  # ✅ CAMBIAR get_driver() por iniciar_driver()
    if not driver: 
        return "Error: Navegador no disponible."
    
    try:
        voz.hablar("Abriendo WhatsApp Web...")
        driver.get("https://web.whatsapp.com/")
        wait = WebDriverWait(driver, 60)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='grid']")))
        voz.hablar("WhatsApp Web cargado y listo.")
        return "WhatsApp Web cargado y listo."
    except Exception as e:
        return f"Error cargando WhatsApp: {e}"

def leer_nuevos():
    """Busca chats con indicadores de mensajes no leídos."""
    driver = browser_handler.iniciar_driver()
    if not driver: 
        return "Navegador no iniciado."

    try:
        voz.hablar("Buscando mensajes nuevos...")
        unread_badges = driver.find_elements(By.XPATH, '//span[@aria-label and contains(@aria-label, "no leído")]')
        
        if not unread_badges:
            voz.hablar("No tienes mensajes nuevos visibles.")
            return "No tienes mensajes nuevos visibles."

        mensajes = []
        for badge in unread_badges[:3]:
            try:
                row = badge.find_element(By.XPATH, "./../../../../..") 
                nombre_elemento = row.find_element(By.CSS_SELECTOR, "span[title]")
                nombre = nombre_elemento.get_attribute("title")
                mensajes.append(f"Tienes mensajes nuevos de {nombre}")
            except:
                mensajes.append("Tienes mensajes de un contacto que no pude identificar.")
        
        resultado = ". ".join(mensajes)
        voz.hablar(resultado)
        return resultado

    except Exception as e:
        return f"Error leyendo mensajes: {e}"

def enviar_mensaje(contacto, mensaje):
    """Busca un contacto y le envía un mensaje."""
    driver = browser_handler.iniciar_driver()
    if not driver:
        return "Navegador no disponible."
    
    voz.hablar(f"Buscando contacto {contacto}...")
    
    search_box = _buscar_caja_busqueda(driver)
    if not search_box: 
        return "No encontré dónde buscar el contacto."
    
    _limpiar_y_escribir(search_box, contacto)
    time.sleep(2)
    search_box.send_keys(Keys.ENTER)
    time.sleep(1)
    
    try:
        caja_mensaje = driver.find_element(By.CSS_SELECTOR, "footer div[contenteditable='true']")
        caja_mensaje.click()
        caja_mensaje.send_keys(mensaje)
        caja_mensaje.send_keys(Keys.ENTER)
        
        resultado = f"Mensaje enviado a {contacto}."
        voz.hablar(resultado)
        return resultado
    except Exception as e:
        return f"No pude escribir el mensaje: {e}"

def _buscar_caja_busqueda(driver):
    try:
        wait = WebDriverWait(driver, 5)
        box = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[@contenteditable='true' and (contains(@aria-label,'Search') or contains(@aria-label,'Buscar'))]")
        ))
        return box
    except:
        return None

def _limpiar_y_escribir(elemento, texto):
    elemento.click()
    elemento.send_keys(Keys.CONTROL + "a")
    elemento.send_keys(Keys.BACKSPACE)
    elemento.send_keys(texto)
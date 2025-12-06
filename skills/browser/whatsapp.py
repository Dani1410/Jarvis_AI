import time
import re
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException

# Importamos el gestor del driver que crearemos en driver.py
from . import driver as browser_handler 

# Configuración básica de espera
WAIT_TIMEOUT = 20

def abrir():
    """Abre WhatsApp Web usando el driver compartido."""
    driver = browser_handler.get_driver() # Obtiene el navegador activo
    if not driver: return "Error: Navegador no disponible."
    
    try:
        driver.get("https://web.whatsapp.com/")
        # Esperamos a que cargue la lista de chats para confirmar éxito
        wait = WebDriverWait(driver, 60)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='grid']")))
        return "WhatsApp Web cargado y listo."
    except Exception as e:
        return f"Error cargando WhatsApp: {e}"

def leer_nuevos():
    """Busca chats con indicadores de mensajes no leídos."""
    driver = browser_handler.get_driver()
    if not driver: return "Navegador no iniciado."

    try:
        # Buscamos indicadores de no leídos (círculos verdes con números)
        # Usamos un selector genérico para encontrar el indicador
        unread_badges = driver.find_elements(By.XPATH, '//span[@aria-label and contains(@aria-label, "no leído")]')
        
        if not unread_badges:
            return "No tienes mensajes nuevos visibles."

        mensajes = []
        # Procesamos los primeros 3 chats no leídos
        for badge in unread_badges[:3]:
            # Intentamos obtener el nombre del contacto subiendo en el HTML
            try:
                # Subimos al contenedor de la fila (ajusta los parent según necesidad)
                row = badge.find_element(By.XPATH, "./../../../../..") 
                nombre_elemento = row.find_element(By.CSS_SELECTOR, "span[title]")
                nombre = nombre_elemento.get_attribute("title")
                mensajes.append(f"Tienes mensajes nuevos de {nombre}")
            except:
                mensajes.append("Tienes mensajes de un contacto que no pude identificar.")
        
        return ". ".join(mensajes)

    except Exception as e:
        return f"Error leyendo mensajes: {e}"

def enviar_mensaje(contacto, mensaje):
    """
    Busca un contacto y le envía un mensaje.
    contacto: Nombre o número
    """
    driver = browser_handler.get_driver()
    
    # 1. Buscar contacto
    search_box = _buscar_caja_busqueda(driver)
    if not search_box: return "No encontré dónde buscar el contacto."
    
    _limpiar_y_escribir(search_box, contacto)
    time.sleep(2) # Espera a que filtre
    search_box.send_keys(Keys.ENTER) # Abre el primer resultado
    
    # 2. Esperar a que cargue el chat
    time.sleep(1) # Breve pausa para la transición
    
    # 3. Escribir mensaje
    try:
        # Buscamos el input de texto (footer)
        caja_mensaje = driver.find_element(By.CSS_SELECTOR, "footer div[contenteditable='true']")
        caja_mensaje.click()
        caja_mensaje.send_keys(mensaje)
        caja_mensaje.send_keys(Keys.ENTER)
        return f"Mensaje enviado a {contacto}."
    except Exception as e:
        return f"No pude escribir el mensaje: {e}"

# --- Funciones auxiliares privadas (del script que probaste) ---

def _buscar_caja_busqueda(driver):
    try:
        wait = WebDriverWait(driver, 5)
        # XPath robusto para la caja de búsqueda lateral
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
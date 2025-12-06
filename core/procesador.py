import os
import pyautogui
import screen_brightness_control as sbc
from AppOpener import open as app_open
import pywhatkit
import datetime
import psutil 
import random
import pyperclip 

# --- IMPORTS ACTUALIZADOS PARA LA NUEVA ESTRUCTURA ---
from core import voz, cerebro, memoria_vectorial as memoria
from skills.social import email_handler
from skills.productividad import agenda, tareas
from skills.browser import scraper, whatsapp, driver as nav_driver

# Configuración básica
CONTACTOS = {
    "dani": "+5243715364",
    "keni": "+525611263777"
}

def ejecutar(texto):
    """
    Procesa el texto y ejecuta acciones. Retorna True si ejecutó algo, False si no.
    """
    
    # --- 1. NAVEGACIÓN WEB ---
    if "resume esta web" in texto or "lee esta página" in texto:
        try:
            url = pyperclip.paste()
            if "http" not in url:
                voz.hablar("Primero copia una URL válida.")
                return True
            # Usamos el scraper nuevo
            contenido = scraper.leer_pagina(url)
            resumen = cerebro.pensar(f"Resume este texto: {contenido}")
            voz.hablar(resumen)
        except Exception as e:
            voz.hablar("Error leyendo el portapapeles.")
        return True
    
    # --- WHATSAPP (Integrando tu código nuevo) ---
    if "abre whatsapp" in texto:
        voz.hablar("Abriendo WhatsApp...")
        whatsapp.abrir() # Asegúrate de crear esta función en skills/browser/whatsapp.py
        return True

    # --- DESCARGAS ---
    if "descarga esto" in texto:
        url = pyperclip.paste()
        ext = url.split(".")[-1]
        if len(ext) > 4: ext = "file"
        nombre = f"descarga_jarvis.{ext}"
        # Usamos el scraper para descargar
        resp = scraper.descargar_archivo(url, nombre)
        voz.hablar(resp)
        return True
    
    # --- MEMORIA ---
    if "recuerda que" in texto:
        dato = texto.replace("recuerda que", "").strip()
        memoria.guardar(dato)
        voz.hablar("Dato guardado.")
        return True

    # --- SISTEMA (Hardware) ---
    if "batería" in texto:
        bateria = psutil.sensors_battery()
        voz.hablar(f"Batería al {bateria.percent} por ciento.")
        return True
    
    if "cpu" in texto:
        uso = psutil.cpu_percent(interval=1)
        voz.hablar(f"Uso del procesador: {uso} por ciento.")
        return True

    # --- FECHA Y HORA ---
    if "hora" in texto:
        hora = datetime.datetime.now().strftime('%I:%M %p')
        voz.hablar(f"Son las {hora}")
        return True
        
    if "fecha" in texto:
        fecha = datetime.datetime.now().strftime('%d/%m/%Y')
        voz.hablar(f"Hoy es {fecha}")
        return True

    # --- MULTIMEDIA (Youtube / Control) ---
    if "reproduce" in texto:
        cancion = texto.replace("reproduce", "").strip()
        voz.hablar(f"Poniendo {cancion}.")
        pywhatkit.playonyt(cancion)
        return True

    if "busca" in texto:
        busqueda = texto.replace("busca", "").strip()
        voz.hablar(f"Buscando {busqueda}.")
        pywhatkit.search(busqueda)
        return True

    # --- CONTROL DE LAPTOP ---
    if "sube el volumen" in texto:
        pyautogui.press("volumeup", presses=5)
        return True
        
    if "baja el volumen" in texto:
        pyautogui.press("volumedown", presses=5)
        return True
    
    if "captura" in texto:
        voz.hablar("Tomando foto.")
        # Guarda en la carpeta temporal o descargas
        ruta = os.path.join("data", "downloads", f"captura_{random.randint(1,1000)}.png")
        pyautogui.screenshot(ruta)
        os.system(f"start {ruta}")
        return True

    # --- APLICACIONES ---
    if "abre" in texto and "whatsapp" not in texto: # Evitar conflicto
        app = texto.replace("abre", "").strip()
        voz.hablar(f"Abriendo {app}")
        try: app_open(app, match_closest=True, throw_error=True)
        except: voz.hablar(f"No encontré {app}")
        return True
    
    # --- SOCIAL (Email) ---
    if "correos" in texto or "email" in texto:
        email_handler.leer_correos_gmail()
        return True
    
    # --- PRODUCTIVIDAD (Agenda/Tareas) ---
    if "crea tarea" in texto:
        t = texto.replace("crea tarea", "").strip()
        resp = tareas.agregar_tarea(t) # Usamos skills.productividad.tareas
        voz.hablar(resp)
        return True

    if "evento" in texto:
        # Lógica simplificada, asume que 'agenda' tiene la función
        resp = agenda.procesar_evento_voz(texto) 
        voz.hablar(resp)
        return True

    if "qué tengo" in texto or "pendientes" in texto:
        # Combinamos respuesta de tareas y agenda
        t = tareas.ver_pendientes()
        a = agenda.ver_eventos()
        voz.hablar(f"{t}. {a}")
        return True

    # --- EXIT ---
    if "descansa" in texto:
        voz.hablar("Desconectando.")
        exit()

    return False
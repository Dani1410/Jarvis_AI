import os
import pyautogui
import screen_brightness_control as sbc
from AppOpener import open as app_open
import pywhatkit
import datetime
import psutil 
import random
from . import memoria_vectorial as memoria
from . import voz 
from . import social 
from . import cerebro 
from . import organizacion 
from . import navegacion
import pyperclip # Para leer el portapapeles

CONTACTOS = {
    "dani": "+5243715364",
    "keni": "+525611263777"
}

def ejecutar(texto):
    """
    Procesa el texto y ejecuta acciones. Retorna True si ejecutó algo, False si no.
    """
    
    # --- 1. NAVEGACIÓN WEB (NUEVO) ---
    if "resume esta web" in texto or "lee esta página" in texto:
        try:
            # Lee la URL que tengas copiada en el portapapeles (Ctrl+C)
            url = pyperclip.paste()
            if "http" not in url:
                voz.hablar("Primero copia una URL válida (Ctrl + C).")
                return True
            
            contenido = navegacion.leer_pagina(url)
            # Le pedimos a Ollama que resuma
            resumen = cerebro.pensar(f"Resume este texto brevemente: {contenido}")
            voz.hablar(resumen)
        except Exception as e:
            voz.hablar("Error leyendo el portapapeles.")
        return True
    
    # --- COMUNICACIÓN AVANZADA ---
    if "abre whatsapp" in texto or "inicia whatsapp" in texto:
        voz.hablar("Iniciando protocolo de mensajería.")
        navegacion.abrir_whatsapp_web()
        return True
    
    # ... dentro de def ejecutar(texto): ...

    if "lee mis mensajes" in texto or "qué me dijeron" in texto:
        respuesta = navegacion.leer_mensajes_whatsapp()
        voz.hablar(respuesta)
        # Opcional: Pedirle a Cerebro (Ollama) que te de una respuesta sugerida
        sugerencia = cerebro.pensar(f"Alguien me escribió esto en WhatsApp: '{respuesta}'. ¿Qué le puedo responder de forma breve y casual?")
        voz.hablar(f"Sugerencia de respuesta: {sugerencia}")
        return True

    if "descarga esto" in texto:
        url = pyperclip.paste()
        ext = url.split(".")[-1]
        if len(ext) > 4: ext = "file"
        nombre = f"descarga_jarvis.{ext}"
        
        resp = navegacion.descargar_archivo(url, nombre)
        voz.hablar(resp)
        return True
    
    # --- 1. MEMORIA Y APRENDIZAJE ---
    if "recuerda que" in texto or "guarda que" in texto:
        dato = texto.replace("recuerda que", "").replace("guarda que", "").strip()
        memoria.guardar(dato)
        voz.hablar(f"Entendido, dato guardado.")
        return True

    # --- 2. INFORMACIÓN DEL SISTEMA ---
    if "batería" in texto or "carga" in texto:
        bateria = psutil.sensors_battery()
        porcentaje = bateria.percent
        estado = "cargando" if bateria.power_plugged else "descargando"
        voz.hablar(f"La batería está al {porcentaje} por ciento y {estado}.")
        return True
    
    if "cpu" in texto or "procesador" in texto:
        uso = psutil.cpu_percent(interval=1)
        voz.hablar(f"El uso del procesador es del {uso} por ciento.")
        return True

    # --- 3. FECHA Y HORA ---
    if "qué hora es" in texto or "dime la hora" in texto:
        hora = datetime.datetime.now().strftime('%I:%M %p')
        voz.hablar(f"Son las {hora}")
        return True
        
    if "fecha" in texto or "qué día es" in texto:
        fecha = datetime.datetime.now().strftime('%d/%m/%Y')
        voz.hablar(f"Hoy es {fecha}")
        return True

    # --- 4. MULTIMEDIA Y WEB ---
    if "reproduce" in texto:
        cancion = texto.replace("reproduce", "").strip()
        voz.hablar(f"Reproduciendo {cancion} en YouTube.")
        pywhatkit.playonyt(cancion)
        return True

    if "busca" in texto or "google" in texto:
        busqueda = texto.replace("busca", "").replace("google", "").strip()
        voz.hablar(f"Buscando {busqueda} en la web.")
        pywhatkit.search(busqueda)
        return True

    # --- 5. CONTROL DE LAPTOP ---
    if "sube el volumen" in texto:
        pyautogui.press("volumeup", presses=5)
        voz.hablar("Subiendo.")
        return True
        
    if "baja el volumen" in texto:
        pyautogui.press("volumedown", presses=5)
        voz.hablar("Bajando.")
        return True
        
    if "silencio" in texto or "mute" in texto:
        pyautogui.press("volumemute")
        return True

    if "captura" in texto or "screenshot" in texto:
        voz.hablar("Tomando captura.")
        nombre_foto = f"captura_{random.randint(1,1000)}.png"
        ruta = os.path.join(os.getcwd(), nombre_foto)
        pyautogui.screenshot(ruta)
        os.system(f"start {ruta}")
        return True
    
    if "brillo al máximo" in texto:
        try: sbc.set_brightness(100)
        except: pass
        voz.hablar("Brillo al 100.")
        return True

    if "baja el brillo" in texto:
        try: sbc.set_brightness(30)
        except: pass
        voz.hablar("Modo descanso visual.")
        return True

    # --- 6. APLICACIONES ---
    if "abre" in texto:
        app = texto.replace("abre", "").strip()
        voz.hablar(f"Iniciando {app}")
        try:
            app_open(app, match_closest=True, throw_error=True)
        except:
            voz.hablar(f"No tengo instalada la app {app}")
        return True
    
    # --- COMUNICACIÓN ---
    if "lee mis correos" in texto or "tengo mensajes" in texto or "revisar email" in texto:
        social.leer_correos_gmail()
        return True
    
    # --- ORGANIZACIÓN Y TAREAS (AHORA SÍ ESTÁ AL NIVEL CORRECTO) ---
    if "crea tarea" in texto or "agrega tarea" in texto:
        tarea = texto.replace("crea tarea", "").replace("agrega tarea", "").strip()
        resp = organizacion.agregar_tarea(tarea)
        voz.hablar(resp)
        return True

    if "evento" in texto or "reunión" in texto:
        if " el " in texto: separator = " el "
        elif " para " in texto: separator = " para "
        else: 
            voz.hablar("Dime la fecha usando 'el' o 'para'. Ejemplo: Reunión EL viernes.")
            return True
        
        partes = texto.split(separator, 1) 
        descripcion = partes[0].replace("agrega", "").replace("reunión", "").replace("evento", "").strip()
        fecha = separator + partes[1]
        
        resp = organizacion.agregar_evento(descripcion, fecha)
        voz.hablar(resp)
        return True

    if "qué tengo que hacer" in texto or "agenda" in texto or "pendientes" in texto:
        resp = organizacion.ver_pendientes()
        voz.hablar(resp)
        return True

    # --- RECORDATORIOS ---
    if "recuérdame" in texto:
        mensaje = ""
        tiempo = ""
        
        if " cada " in texto:
            partes = texto.split(" cada ", 1)
            mensaje = partes[0].replace("recuérdame", "").strip()
            tiempo = "cada " + partes[1]
        elif " en " in texto:
            partes = texto.split(" en ", 1)
            mensaje = partes[0].replace("recuérdame", "").strip()
            tiempo = "en " + partes[1]
        else:
            voz.hablar("Dime cuándo quieres el recordatorio. Ejemplo: 'en 5 minutos' o 'cada hora'.")
            return True
            
        resp = organizacion.programar_recordatorio(mensaje, tiempo)
        voz.hablar(resp)
        return True
        
    # --- NOTAS RÁPIDAS ---
    if "nota rápida" in texto or "anota esto" in texto:
        nota = texto.replace("nota rápida", "").replace("anota esto", "").strip()
        memoria.guardar(f"NOTA: {nota}")
        voz.hablar("Nota guardada en memoria.")
        return True

    # --- MEMORIA ---
    if "olvida la conversación" in texto or "reinicia el chat" in texto:
        cerebro.historial_chat = [] 
        voz.hablar("Memoria a corto plazo borrada. Empezamos de cero.")
        return True

    # --- 7. APAGADO ---
    if "descansa" in texto or "terminar" in texto:
        voz.hablar("Entendido. Desconectando sistemas.")
        exit()

    return False
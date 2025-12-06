import os
import pyautogui
import screen_brightness_control as sbc
from AppOpener import open as app_open
import pywhatkit
import datetime
import psutil # Para batería y hardware
import random
import memoria_vectorial as memoria
import voz 
import social # <--- NUEVO
import cerebro # <--- NUEVO

def ejecutar(texto):
    """
    Procesa el texto y ejecuta acciones. Retorna True si ejecutó algo, False si no.
    """
    
    # --- 1. MEMORIA Y APRENDIZAJE ---
    if "recuerda que" in texto or "guarda que" in texto:
        dato = texto.replace("recuerda que", "").replace("guarda que", "").strip()
        memoria.guardar(dato)
        voz.hablar(f"Entendido, dato guardado.")
        return True

    # --- 2. INFORMACIÓN DEL SISTEMA (Laptop) ---
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
        # Formato simple. Para español completo se requiere librería locale, 
        # pero esto funciona bien por defecto.
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
    
    # --- COMUNICACIÓN (NUEVO) ---
    if "lee mis correos" in texto or "tengo mensajes" in texto or "revisar email" in texto:
        social.leer_correos_gmail()
        return True

    # --- MEMORIA (NUEVO) ---
    if "olvida la conversación" in texto or "reinicia el chat" in texto:
        cerebro.historial_chat = [] # Borramos la lista
        voz.hablar("Memoria a corto plazo borrada. Empezamos de cero.")
        return True

    # --- 7. APAGADO ---
    if "descansa" in texto or "terminar" in texto:
        voz.hablar("Entendido. Desconectando sistemas.")
        exit()

    return False
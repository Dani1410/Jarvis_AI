import os
import pyautogui
import screen_brightness_control as sbc
from AppOpener import open as app_open
import pywhatkit
import datetime
import memoria_vectorial as memoria
import voz # Importamos nuestro propio módulo de voz

def ejecutar(texto):
    # MEMORIA
    if "recuerda que" in texto or "guarda que" in texto:
        dato = texto.replace("recuerda que", "").replace("guarda que", "").strip()
        memoria.guardar(dato)
        voz.hablar(f"Guardado: {dato}")
        return True

    # MULTIMEDIA
    if "reproduce" in texto:
        cancion = texto.replace("reproduce", "").strip()
        voz.hablar(f"Poniendo {cancion}")
        pywhatkit.playonyt(cancion)
        return True

    # SISTEMA
    if "sube el volumen" in texto:
        pyautogui.press("volumeup", presses=5)
        return True
        
    if "captura" in texto:
        voz.hablar("Foto.")
        ruta = os.path.join(os.getcwd(), "captura.png")
        pyautogui.screenshot(ruta)
        os.system(f"start {ruta}")
        return True

    if "terminar" in texto:
        voz.hablar("Adiós.")
        exit()

    return False
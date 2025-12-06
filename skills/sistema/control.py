"""
Módulo para control de hardware mediante pyautogui.
Responsabilidad: Interactuar con controles del sistema (volumen, captura, brillo)
"""
import os
import random
import pyautogui
import screen_brightness_control as sbc


def subir_volumen(presses=5):
    """Aumenta el volumen del sistema."""
    try:
        pyautogui.press("volumeup", presses=presses)
        return f"Volumen aumentado {presses} niveles."
    except Exception as e:
        return f"Error al subir volumen: {e}"


def bajar_volumen(presses=5):
    """Reduce el volumen del sistema."""
    try:
        pyautogui.press("volumedown", presses=presses)
        return f"Volumen reducido {presses} niveles."
    except Exception as e:
        return f"Error al bajar volumen: {e}"


def silenciar():
    """Silencia el sistema."""
    try:
        pyautogui.press("volumemute")
        return "Sistema silenciado."
    except Exception as e:
        return f"Error al silenciar: {e}"


def tomar_captura(carpeta_destino="data/downloads"):
    """Toma una captura de pantalla y la guarda."""
    try:
        os.makedirs(carpeta_destino, exist_ok=True)
        nombre_archivo = f"captura_{random.randint(1000, 9999)}.png"
        ruta_completa = os.path.join(carpeta_destino, nombre_archivo)
        
        pyautogui.screenshot(ruta_completa)
        
        # Abre la captura
        os.system(f"start {ruta_completa}")
        
        return f"Captura guardada en {ruta_completa}"
    except Exception as e:
        return f"Error al tomar captura: {e}"


def obtener_brillo():
    """Obtiene el nivel de brillo actual."""
    try:
        brillo = sbc.get_brightness()
        if isinstance(brillo, list):
            return brillo[0]
        return brillo
    except Exception as e:
        return None


def establecer_brillo(nivel):
    """Establece el nivel de brillo (0-100)."""
    try:
        if 0 <= nivel <= 100:
            sbc.set_brightness(nivel)
            return f"Brillo ajustado a {nivel}%"
        return "El nivel debe estar entre 0 y 100."
    except Exception as e:
        return f"Error al ajustar brillo: {e}"
# test-console-main.py
# Este script ejecuta Jarvis en modo texto/consola para depuración.

import sys
import os

# Añadir la carpeta raíz del proyecto al path para importar main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import run_jarvis_session
from core import voz

# -------------------------------------------------------------
# FUNCIONES MOCK (Para forzar la entrada/salida de texto)
# -------------------------------------------------------------

def text_input():
    """Simula el micrófono pidiendo input por teclado."""
    try:
        texto = input("\n👉 TÚ: ").strip().lower()
        return texto
    except EOFError:
        return "salir"

def text_output(texto):
    """Simula el TTS imprimiendo el texto en la consola."""
    # NO USAMOS print(f"🗣️ [JARVIS DICE]: {texto}") de core/voz.py
    # sino el simple print para evitar el log extra de voz en modo debug.
    print(f"🤖 [JARVIS (TEST)]: {texto}") 

# -------------------------------------------------------------
# PUNTO DE ENTRADA (MODO TEXTO)
# -------------------------------------------------------------

if __name__ == "__main__":
    # Sobrescribir la función voz.hablar globalmente SÓLO en este script
    # para que las skills (ej: en email_handler) no intenten usar TTS.
    voz.hablar = text_output 
    
    # Iniciar la sesión
    run_jarvis_session(get_input_fn=text_input, mode_name="TEXTO/DEBUG")
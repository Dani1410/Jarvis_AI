# import pyttsx3 # <--- Comentado para que no cargue el motor

def hablar(texto):
    # Imprimimos lo que diría Jarvis
    print(f"🗣️ [JARVIS DICE]: {texto}")
    
    # --- BLOQUE SILENCIADO TEMPORALMENTE ---
    # try:
    #     engine = pyttsx3.init()
    #     # ... (toda tu configuración de Sabina) ...
    #     engine.say(texto)
    #     engine.runAndWait()
    #     engine.stop()
    # except Exception as e:
    #     print(f"Error de audio: {e}")
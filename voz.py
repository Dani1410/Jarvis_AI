import pyttsx3

def hablar(texto):
    print(f"JARVIS: {texto}")
    try:
        # Inicializamos el motor cada vez para evitar bloqueos
        engine = pyttsx3.init()
        
        # Buscamos a Sabina dinámicamente
        voices = engine.getProperty('voices')
        for voice in voices:
            if "sabina" in voice.name.lower() or "mexico" in voice.name.lower():
                engine.setProperty('voice', voice.id)
                break
        
        engine.setProperty('rate', 155)
        engine.say(texto)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"⚠️ Error de audio: {e}")
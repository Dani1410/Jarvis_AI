import speech_recognition as sr
import whisper
# Al principio
import os
ruta_audio = os.path.join("datos", "temp_audio.wav") 
# Usa 'ruta_audio' en lugar de "temp_audio.wav"

# Cargamos el modelo una sola vez al importar este archivo
print("Cargando sistema auditivo...")
try:
    ear_model = whisper.load_model("base")
except:
    print("⚠️ Error cargando Whisper. Verifica que tengas internet la primera vez.")

def escuchar():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Escuchando...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        if r.energy_threshold > 2000: r.energy_threshold = 1000 
        r.pause_threshold = 0.8 
        
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            return ""
    
    try:
        with open("temp_audio.wav", "wb") as f:
            f.write(audio.get_wav_data())
            
        result = ear_model.transcribe("temp_audio.wav", language="es", fp16=False)
        texto = result["text"].strip()
        if texto:
            print(f"TÚ: {texto}")
        return texto.lower()
    except:
        return ""
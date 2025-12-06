import speech_recognition as sr
import whisper
import os

RUTA_AUDIO = os.path.join("data", "temp", "temp_audio.wav")

# Asegurar que la carpeta existe
os.makedirs(os.path.dirname(RUTA_AUDIO), exist_ok=True)

# Cargamos el modelo una sola vez al importar este archivo
print("Cargando sistema auditivo...")
try:
    ear_model = whisper.load_model("base")
    print("✅ Whisper cargado correctamente")
except Exception as e:
    print(f"⚠️ Error cargando Whisper: {e}")
    ear_model = None

def transcribe(wav_path: str, language: str = "es") -> str:
    """
    Transcribe un WAV usando el modelo cargado.
    Retorna el texto (string) o levanta excepción en caso de error.
    """
    if ear_model is None:
        raise RuntimeError("Modelo de ASR no cargado en oido.py (ear_model es None).")
    
    result = ear_model.transcribe(wav_path, language=language, fp16=False)
    return result.get("text", "").strip()

def escuchar():
    """Escucha por el micrófono y retorna el texto transcrito."""
    r = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("🎤 Escuchando...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        if r.energy_threshold > 2000: 
            r.energy_threshold = 1000 
        r.pause_threshold = 0.8 
        
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            print("⏱️ Timeout - No se detectó audio")
            return ""
    
    try:
        # ✅ Usar la ruta correcta definida arriba
        with open(RUTA_AUDIO, "wb") as f:
            f.write(audio.get_wav_data())
        
        # ✅ Usar la función transcribe que ya definimos
        texto = transcribe(RUTA_AUDIO, language="es")
        
        if texto:
            print(f"👤 TÚ: {texto}")
        
        return texto.lower()
        
    except Exception as e:
        print(f"❌ Error en transcripción: {e}")
        return ""
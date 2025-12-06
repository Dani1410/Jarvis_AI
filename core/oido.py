import speech_recognition as sr
import whisper
import os
import pvporcupine
import pyaudio
from dotenv import load_dotenv

# --- CONFIGURACIÓN DE VOZ ---
load_dotenv()
PICOVOICE_API_KEY = os.getenv('PICOVOICE_API_KEY')
WAKE_WORD = "computer" # Usa la palabra clave 'computer' ya integrada
# WAKE_WORD = "jarvis" # Opción si usas un modelo personalizado
# --- FIN CONFIGURACIÓN ---

RUTA_AUDIO = os.path.join("data", "temp", "temp_audio.wav")
os.makedirs(os.path.dirname(RUTA_AUDIO), exist_ok=True)

# Cargamos el modelo Whisper una sola vez
print("Cargando sistema auditivo (Whisper)...")
try:
    ear_model = whisper.load_model("base")
    print("✅ Whisper cargado correctamente")
except Exception as e:
    print(f"⚠️ Error cargando Whisper: {e}")
    ear_model = None

def transcribe(wav_path: str, language: str = "es") -> str:
    """Transcribe un WAV usando el modelo cargado."""
    if ear_model is None:
        raise RuntimeError("Modelo de ASR no cargado.")
    
    # Se añade un logging de debug para saber qué transcribe
    result = ear_model.transcribe(wav_path, language=language, fp16=False)
    return result.get("text", "").strip()

def escuchar_comando():
    """Escucha por el micrófono SÓLO DESPUÉS de detectar el Wake Word."""
    r = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("🎤 LISTENING: Grabando comando...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        # Ajustar umbral si es muy alto
        if r.energy_threshold > 2000: 
            r.energy_threshold = 1000 
            
        r.pause_threshold = 0.8 
        
        try:
            # Escucha el comando completo (máximo 8 segundos)
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            print("⏱️ Timeout - Fin del comando")
            return ""
    
    try:
        with open(RUTA_AUDIO, "wb") as f:
            f.write(audio.get_wav_data())
        
        texto = transcribe(RUTA_AUDIO, language="es")
        
        if texto:
            print(f"👤 TÚ: {texto}")
        
        return texto.lower()
        
    except Exception as e:
        print(f"❌ Error en transcripción: {e}")
        return ""

def detectar_wake_word():
    """
    Loop de baja latencia que escucha la palabra de activación y 
    llama a 'escuchar_comando()' si la detecta.
    """
    if not PICOVOICE_API_KEY:
        raise RuntimeError("PICOVOICE_API_KEY no configurada en .env")

    # Si tu palabra clave es personalizada (no 'computer'), debes especificar el path del modelo
    # keywords = [pvporcupine.KEYWORD_FILE_PATHS["es"]["computer"]]
    
    # Usaremos el keyword 'computer' integrado por ser rápido y estándar en español
    keywords = [pvporcupine.KEYWORD_FILE_PATHS["es"]["computer"]]
    
    pa = pyaudio.PyAudio()
    
    try:
        # Inicializar el motor Porcupine
        porcupine = pvporcupine.create(
            access_key=PICOVOICE_API_KEY, 
            keyword_paths=keywords
        )
        
        # Abrir stream de audio
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
        
        print(f"\n🎧 Jarvis ONLINE. Esperando 'Computer' ({WAKE_WORD})")
        print("------------------------------------------")

        while True:
            # Leer un fragmento del micrófono
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm_16 = pvporcupine.struct.unpack_from("h" * porcupine.frame_length, pcm)
            
            # Procesar el fragmento
            keyword_index = porcupine.process(pcm_16)
            
            if keyword_index >= 0:
                print("\n\n🚨 WAKE WORD DETECTED! 🚨")
                return escuchar_comando()
                
    except Exception as e:
        print(f"❌ Error crítico en Wake Word: {e}")
        return ""
    finally:
        if 'porcupine' in locals() and porcupine is not None:
            porcupine.delete()
        if 'audio_stream' in locals() and audio_stream is not None:
            audio_stream.close()
        pa.terminate()

# La función 'escuchar' original de main.py ahora llama a detectar_wake_word
escuchar = detectar_wake_word
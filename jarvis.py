import speech_recognition as sr
import pyttsx3
import ollama
import whisper
import os
import warnings
import memoria_vectorial as memoria  # Importamos tu archivo con alias
from AppOpener import open as app_open

# Configuración inicial
warnings.filterwarnings("ignore") # Ocultar alertas de hardware
MODELO_OLLAMA = "llama3.2" 

# 1. Configurar VOZ (Lo que Jarvis habla)
engine = pyttsx3.init()
voices = engine.getProperty('voices')
# Intentamos buscar una voz en español (Sabo o Helena en Windows)
for voice in voices:
    if "spanish" in voice.name.lower() or "mexico" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break
engine.setProperty('rate', 160) # Un poco más rápido que el defecto

# 2. Configurar OÍDO (Whisper) - Se carga al iniciar
print("Cargando sistema auditivo (Whisper)... espere un momento.")
ear_model = whisper.load_model("base") 

def hablar(texto):
    """Convierte texto a audio"""
    print(f"JARVIS: {texto}")
    engine.say(texto)
    engine.runAndWait()

def escuchar():
    """Escucha el micrófono y transcribe con Whisper"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Escuchando...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            return ""
    
    # Guardamos temporalmente para que Whisper lo lea
    with open("temp_audio.wav", "wb") as f:
        f.write(audio.get_wav_data())

    try:
        # Transcripción OFFLINE potente
        result = ear_model.transcribe("temp_audio.wav", language="es", fp16=False)
        texto = result["text"].strip()
        if texto:
            print(f"TÚ: {texto}")
        return texto.lower()
    except Exception as e:
        return ""

def pensar_y_responder(pregunta):
    """Consulta a Ollama usando recuerdos si es necesario"""
    
    # PASO A: Buscar en la memoria si sabemos algo del tema
    recuerdos = memoria.buscar(pregunta)
    
    prompt_sistema = (
        "Eres Jarvis, un asistente virtual útil, sarcástico y breve. "
        "Tu dueño es un estudiante de Ingeniería de Software. "
        "Responde en español latino. Máximo 2 oraciones."
    )
    
    if recuerdos:
        prompt_sistema += f"\nINFORMACIÓN RECUPERADA DE TU MEMORIA: {recuerdos}"

    try:
        response = ollama.chat(model=MODELO_OLLAMA, messages=[
            {'role': 'system', 'content': prompt_sistema},
            {'role': 'user', 'content': pregunta},
        ])
        return response['message']['content']
    except:
        return "Error: No puedo conectar con mi cerebro (Ollama no está corriendo)."

def ejecutar_comandos(texto):
    """Detecta comandos directos de Windows/Apps"""
    
    # COMANDO: Guardar recuerdo
    if "recuerda que" in texto or "guarda que" in texto:
        dato = texto.replace("recuerda que", "").replace("guarda que", "").strip()
        memoria.guardar(dato)
        hablar(f"Entendido, he guardado: {dato}")
        return True

    # COMANDO: Abrir aplicaciones
    if "abre" in texto:
        app = texto.replace("abre", "").strip()
        hablar(f"Abriendo {app}")
        try:
            app_open(app, match_closest=True, throw_error=True)
        except:
            hablar(f"No encontré la app {app}")
        return True

    if "terminar" in texto or "apágate" in texto:
        hablar("Desconectando sistemas. Hasta luego, ingeniero.")
        exit()

    return False

def main():
    hablar("Sistemas inicializados. Estoy a la espera.")
    
    while True:
        texto_usuario = escuchar()
        
        if not texto_usuario:
            continue # Si hubo silencio, repetimos el ciclo
        
        # 1. Intentamos ejecutar comando directo
        if ejecutar_comandos(texto_usuario):
            continue
            
        # 2. Si no es comando, conversamos con Ollama
        respuesta = pensar_y_responder(texto_usuario)
        hablar(respuesta)

if __name__ == "__main__":
    main()
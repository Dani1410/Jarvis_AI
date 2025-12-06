import speech_recognition as sr
import pyttsx3
import ollama
import whisper
import os
import warnings
import pyautogui
import screen_brightness_control as sbc
import memoria_vectorial as memoria 
import config # Opcional
from AppOpener import open as app_open

# Configuración inicial
warnings.filterwarnings("ignore") 
MODELO_OLLAMA = "llama3.2" 

# --- 1. CONFIGURACIÓN DE VOZ (ESTRATEGIA NUEVA) ---
# Buscamos el ID de Sabina una sola vez al principio para usarlo después
print("Configurando voz...")
temp_engine = pyttsx3.init()
voices = temp_engine.getProperty('voices')
ID_SABINA = None

for voice in voices:
    # Buscamos algo que sea español de México o Sabina
    if "sabina" in voice.name.lower() or "mexico" in voice.name.lower():
        ID_SABINA = voice.id
        break

if ID_SABINA:
    print(f"✅ Voz detectada: Sabina/México")
else:
    print("⚠️ No se encontró Sabina, se usará la voz por defecto.")
temp_engine.stop() # Cerramos este motor temporal

# --- 2. CONFIGURACIÓN DE OÍDO ---
print("Cargando sistema auditivo (Whisper Base)...")
ear_model = whisper.load_model("base")

def hablar(texto):
    print(f"JARVIS: {texto}")
    try:
        engine = pyttsx3.init('sapi5')
        # Solo cambia la voz si estás seguro de que existe
        if ID_SABINA:
            engine.setProperty('voice', ID_SABINA)
        # Si no existe, no setProperty (usa default)
        engine.setProperty('rate', 155)
        engine.say(texto)
        engine.runAndWait()
        engine.stop()
    except Exception as e:
        print(f"⚠️ Error de audio: {e}")

def escuchar():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Escuchando...")
        # Calibración rápida del entorno
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        # AJUSTE: Si detecta mucho ruido base, lo forzamos a ser sensible
        if r.energy_threshold > 2000:
            r.energy_threshold = 1000 
            
        r.pause_threshold = 0.8 
        
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            return ""
    
    with open("temp_audio.wav", "wb") as f:
        f.write(audio.get_wav_data())

    try:
        result = ear_model.transcribe("temp_audio.wav", language="es", fp16=False)
        texto = result["text"].strip()
        if texto:
            print(f"TÚ: {texto}")
        return texto.lower()
    except:
        return ""

def pensar_y_responder(pregunta):
    recuerdos = memoria.buscar(pregunta)
    
    prompt_sistema = (
        "Eres Jarvis, un asistente virtual útil, sarcástico y breve. "
        "Tu dueño es un estudiante de Ingeniería de Software. "
        "Responde en español latino. SÉ MUY BREVE (máximo 1 frase)."
    )
    
    if recuerdos:
        prompt_sistema += f"\nMEMORIA: {recuerdos}"

    print("--> Procesando respuesta...") 

    try:
        response = ollama.chat(model=MODELO_OLLAMA, messages=[
            {'role': 'system', 'content': prompt_sistema},
            {'role': 'user', 'content': pregunta},
        ])
        return response['message']['content']
    except:
        return "Error: Ollama no responde."

def ejecutar_comandos(texto):
    # MEMORIA
    if "recuerda que" in texto or "guarda que" in texto:
        dato = texto.replace("recuerda que", "").replace("guarda que", "").strip()
        memoria.guardar(dato)
        hablar(f"Entendido, guardado: {dato}")
        return True

    # APPS
    if "abre" in texto:
        app = texto.replace("abre", "").strip()
        hablar(f"Abriendo {app}")
        try:
            app_open(app, match_closest=True, throw_error=True)
        except:
            hablar(f"No encontré {app}")
        return True

    # AUTOMATIZACIÓN
    if "sube el volumen" in texto:
        pyautogui.press("volumeup", presses=5)
        hablar("Subiendo volumen.")
        return True
        
    if "baja el volumen" in texto:
        pyautogui.press("volumedown", presses=5)
        hablar("Bajando volumen.")
        return True

    if "captura" in texto:
        hablar("Tomando foto.")
        ruta = os.path.join(os.getcwd(), "captura.png")
        pyautogui.screenshot(ruta)
        os.system(f"start {ruta}")
        return True
        
    if "brillo al máximo" in texto:
        try: sbc.set_brightness(100)
        except: pass
        hablar("Brillo al máximo.")
        return True
        
    if "baja el brillo" in texto:
        try: sbc.set_brightness(30)
        except: pass
        hablar("Bajando brillo.")
        return True

    if "terminar" in texto or "apágate" in texto:
        hablar("Desconectando. Adiós.")
        exit()

    return False

def main():
    hablar("Sistemas listos. Te escucho.")
    
    while True:
        texto_usuario = escuchar()
        
        if not texto_usuario:
            continue 
        
        if ejecutar_comandos(texto_usuario):
            continue
            
        respuesta = pensar_y_responder(texto_usuario)
        hablar(respuesta)

if __name__ == "__main__":
    main()
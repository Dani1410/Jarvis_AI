import os
import torch
import pygame
from TTS.api import TTS

# --- CONFIGURACIÓN ---
# Usamos un modelo VITS en español que es rápido y suena muy natural
NOMBRE_MODELO = "tts_models/es/css10/vits"
RUTA_AUDIO = os.path.join("data", "temp", "voz_jarvis.wav")

print("🧠 Cargando sistema neuronal de voz (esto puede tardar la primera vez)...")

# Detectar si tienes tarjeta gráfica NVIDIA (CUDA) para ir más rápido, si no usa CPU
dispositivo = "cuda" if torch.cuda.is_available() else "cpu"

try:
    # Carga el modelo en memoria RAM
    tts = TTS(NOMBRE_MODELO).to(dispositivo)
    print(f"✅ Voz Neuronal cargada en {dispositivo.upper()}")
except Exception as e:
    print(f"❌ Error crítico cargando modelo TTS: {e}")
    tts = None

# Inicializar mixer de audio
pygame.mixer.init()

def hablar(texto):
    """Genera audio local con IA y lo reproduce."""
    print(f"🗣️ [JARVIS]: {texto}")
    
    if not texto or not tts:
        return

    try:
        # 1. Asegurar que la carpeta existe
        os.makedirs(os.path.dirname(RUTA_AUDIO), exist_ok=True)
        
        # 2. Generar el archivo de audio (Inferencia)
        # Si ya existe, lo borramos para evitar conflictos de bloqueo
        if os.path.exists(RUTA_AUDIO):
            try:
                os.remove(RUTA_AUDIO)
            except PermissionError:
                pass # A veces pygame tarda en soltar el archivo
        
        tts.tts_to_file(text=texto, file_path=RUTA_AUDIO)
        
        # 3. Reproducir el audio
        pygame.mixer.music.load(RUTA_AUDIO)
        pygame.mixer.music.play()
        
        # Esperar a que termine de hablar (bloqueante para que no se interrumpa a sí mismo)
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        pygame.mixer.music.unload()

    except Exception as e:
        print(f"❌ Error de audio: {e}")
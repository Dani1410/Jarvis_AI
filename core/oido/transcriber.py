"""
Transcripción de audio usando Whisper.
Responsabilidad: Convertir audio WAV a texto.
"""
import whisper
from typing import Optional

# Modelo cargado globalmente (carga única al importar)
_whisper_model = None

def load_model(model_name: str = "base") -> whisper.Whisper:
    """Carga el modelo Whisper (solo una vez)."""
    global _whisper_model
    if _whisper_model is None:
        print(f"Cargando modelo Whisper '{model_name}'...")
        try:
            _whisper_model = whisper.load_model(model_name)
            print("✅ Whisper cargado correctamente")
        except Exception as e:
            print(f"⚠️ Error cargando Whisper: {e}")
            raise
    return _whisper_model

def transcribe(wav_path: str, language: str = "es") -> str:
    """
    Transcribe un archivo WAV usando Whisper.
    
    Args:
        wav_path: Ruta al archivo WAV
        language: Código de idioma (ej: 'es', 'en')
        
    Returns:
        Texto transcrito (string vacío si falla)
        
    Raises:
        RuntimeError: Si el modelo no está cargado
    """
    model = load_model()
    
    try:
        result = model.transcribe(wav_path, language=language, fp16=False)
        texto = result.get("text", "").strip()
        return texto
    except Exception as e:
        print(f"❌ Error en transcripción: {e}")
        return ""
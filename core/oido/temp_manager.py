"""
Gestión de archivos temporales de audio.
Responsabilidad: Crear/guardar/limpiar archivos WAV temporales.
"""
import os
import time
import numpy as np
import soundfile as sf
from pathlib import Path
from typing import Optional
import speech_recognition as sr

class TempManager:
    """Administra archivos temporales de audio."""
    
    def __init__(self, temp_dir: Optional[str] = None):
        if temp_dir is None:
            temp_dir = os.path.join(os.getcwd(), "data", "temp")
        
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.audio_path = self.temp_dir / "temp_audio.wav"
    
    def save_audio(self, audio_data: sr.AudioData) -> str:
        """
        Guarda AudioData como archivo WAV.
        
        Args:
            audio_data: Objeto AudioData de speech_recognition
            
        Returns:
            Ruta del archivo guardado
        """
        with open(self.audio_path, "wb") as f:
            f.write(audio_data.get_wav_data())
        return str(self.audio_path)
    
    def save_audio_array(self, audio_array: np.ndarray, sample_rate: int) -> str:
        """
        Guarda un numpy array como archivo WAV con timestamp único.
        
        Args:
            audio_array: Array de audio (int16)
            sample_rate: Frecuencia de muestreo
            
        Returns:
            Ruta del archivo guardado
        """
        # Generar ruta única con timestamp
        timestamp_ms = int(time.time() * 1000)
        audio_path = self.temp_dir / f"temp_audio_{timestamp_ms}.wav"
        
        # Guardar usando soundfile
        sf.write(str(audio_path), audio_array, sample_rate)
        
        return str(audio_path)
    
    def cleanup(self):
        """Elimina archivos temporales."""
        # Limpiar el archivo default
        if self.audio_path.exists():
            self.audio_path.unlink()
        
        # Limpiar archivos con timestamp (más de 1 hora)
        try:
            ahora = time.time()
            for archivo in self.temp_dir.glob("temp_audio_*.wav"):
                edad = ahora - archivo.stat().st_mtime
                if edad > 3600:  # 1 hora
                    archivo.unlink()
        except Exception as e:
            print(f"Error limpiando archivos temp: {e}")
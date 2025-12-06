"""
Wrapper para Porcupine (Wake Word Detection).
Responsabilidad: Detectar palabra de activación y gestionar el stream de audio.
"""
import os
import pyaudio
import pvporcupine
import numpy as np
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class PorcupineDetector:
    """Detector de wake words usando Porcupine."""
    
    def __init__(self, api_key: str, wake_word: str = "computadora", 
                 mic_id: int = 1, sensitivity: float = 0.65):
        """
        Args:
            api_key: API key de Picovoice
            wake_word: Nombre de la palabra de activación
            mic_id: Índice del micrófono
            sensitivity: Sensibilidad de detección (0.0 - 1.0)
        """
        self.api_key = api_key
        self.wake_word = wake_word
        self.preferred_mic_id = mic_id
        self.sensitivity = sensitivity
        
        self.porcupine = None
        self.audio_stream = None
        self.pa = None
        
        # Rutas de modelos
        self._setup_paths()
    
    def _setup_paths(self):
        """Configura las rutas de modelos."""
        base_path = Path(__file__).parent.parent.parent / "data" / "modelos"
        
        self.keyword_path = base_path / f"{self.wake_word}.ppn"
        self.model_path = base_path / "porcupine_params_es.pv"
        
        # Validar existencia
        if not self.keyword_path.exists():
            raise FileNotFoundError(
                f"Archivo .ppn no encontrado: {self.keyword_path}"
            )
        
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Modelo español no encontrado: {self.model_path}\n"
                "Descárgalo desde: https://github.com/Picovoice/porcupine"
            )
        
        logger.info(f"✅ Modelo wake word: {self.keyword_path}")
        logger.info(f"✅ Modelo español: {self.model_path}")
    
    def initialize(self):
        """Inicializa Porcupine y el stream de audio."""
        try:
            # Crear instancia de Porcupine
            self.porcupine = pvporcupine.create(
                access_key=self.api_key,
                keyword_paths=[str(self.keyword_path)],
                sensitivities=[self.sensitivity],
                model_path=str(self.model_path)
            )
            
            # Inicializar PyAudio
            self.pa = pyaudio.PyAudio()
            mic_index = self._choose_input_device()
            
            # Abrir stream
            self.audio_stream = self.pa.open(
                rate=self.porcupine.sample_rate,
                channels=1,
                format=pyaudio.paInt16,
                input=True,
                frames_per_buffer=self.porcupine.frame_length,
                input_device_index=mic_index,
            )
            
            logger.info(f"🎧 Porcupine inicializado - Esperando '{self.wake_word}'")
            
        except Exception as e:
            logger.error(f"Error inicializando Porcupine: {e}")
            raise
    
    def _choose_input_device(self) -> int:
        """Selecciona el dispositivo de entrada válido."""
        # Intentar usar el preferido
        if self.preferred_mic_id is not None:
            try:
                info = self.pa.get_device_info_by_index(self.preferred_mic_id)
                if int(info.get("maxInputChannels", 0)) > 0:
                    logger.info(f"Usando micrófono: {self.preferred_mic_id}")
                    return self.preferred_mic_id
            except Exception:
                pass
        
        # Usar el por defecto
        try:
            info = self.pa.get_default_input_device_info()
            idx = int(info["index"])
            logger.info(f"Usando micrófono por defecto: {idx}")
            return idx
        except Exception:
            pass
        
        # Buscar cualquiera con entrada
        for i in range(self.pa.get_device_count()):
            try:
                d = self.pa.get_device_info_by_index(i)
                if int(d.get("maxInputChannels", 0)) > 0:
                    logger.info(f"Fallback micrófono: {i}")
                    return i
            except Exception:
                continue
        
        raise RuntimeError("No se encontró dispositivo de entrada válido")
    
    def detectar(self) -> bool:
        """
        Lee un frame y detecta wake word.
        
        Returns:
            True si se detectó la palabra, False si no
        """
        try:
            pcm = self.audio_stream.read(
                self.porcupine.frame_length, 
                exception_on_overflow=False
            )
        except IOError as e:
            logger.warning(f"Error leyendo audio: {e}")
            return False
        
        pcm_16 = np.frombuffer(pcm, dtype=np.int16)
        if pcm_16.size == 0:
            return False
        
        try:
            keyword_index = self.porcupine.process(pcm_16)
            return keyword_index >= 0
        except Exception as e:
            logger.error(f"Error procesando Porcupine: {e}")
            return False
    
    def get_stream(self):
        """Retorna el stream de audio (para usarlo con Recorder)."""
        return self.audio_stream
    
    def cleanup(self):
        """Libera recursos."""
        if self.audio_stream is not None:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                logger.debug("Audio stream cerrado")
            except Exception as e:
                logger.warning(f"Error cerrando stream: {e}")
        
        if self.porcupine is not None:
            try:
                self.porcupine.delete()
                logger.debug("Porcupine eliminado")
            except Exception as e:
                logger.warning(f"Error eliminando Porcupine: {e}")
        
        if self.pa is not None:
            try:
                self.pa.terminate()
                logger.debug("PyAudio terminado")
            except Exception as e:
                logger.warning(f"Error terminando PyAudio: {e}")
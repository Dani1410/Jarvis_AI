"""
Servicio principal de reconocimiento de voz.
Orquesta: PorcupineDetector, AudioRecorder, Transcriber, TempManager, Metrics.
"""
import os
import time
import threading
import soundfile as sf
from concurrent.futures import ThreadPoolExecutor
from collections import deque

from .porcupine_wrapper import PorcupineDetector
from .recorder import AudioRecorder
from .transcriber import transcribe, load_model
from .temp_manager import TempManager
from .metrics import registrar_metrica, obtener_estadisticas

import logging
logger = logging.getLogger(__name__)

# Cola thread-safe para comunicar transcripciones
transcripciones_cola = deque()
lock_cola = threading.Lock()

class WakeWordService:
    """
    Servicio completo de reconocimiento de voz con wake word.
    """
    
    def __init__(self, api_key: str, wake_word: str = "computadora", 
                 mic_id: int = 1):
        # Cargar Whisper
        load_model("base")
        
        # Componentes
        self.detector = PorcupineDetector(api_key, wake_word, mic_id)
        self.recorder = AudioRecorder()
        self.temp_manager = TempManager()
        
        # Executor para transcripción asíncrona
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Control de reentrancia
        self.lock_escucha = threading.Lock()
        self.ultima_activacion = 0
        self.debounce_segundos = 1.5
    
    def iniciar(self):
        """Inicializa el detector de wake word."""
        self.detector.initialize()
        logger.info("✅ WakeWordService iniciado")
    
    def escuchar(self) -> str:
        """
        Loop principal: detecta wake word, graba, transcribe.
        Retorna el texto transcrito cuando esté listo.
        """
        try:
            while True:
                # Verificar si hay texto en la cola
                with lock_cola:
                    if transcripciones_cola:
                        texto = transcripciones_cola.popleft()
                        logger.debug(f"📤 Retornando: {texto}")
                        return texto
                
                # Detectar wake word
                if self.detector.detectar():
                    ahora = time.time()
                    
                    # Debounce
                    if ahora - self.ultima_activacion < self.debounce_segundos:
                        continue
                    
                    logger.info("🚨 WAKE WORD DETECTADO!")
                    self.ultima_activacion = ahora
                    
                    # Intentar adquirir lock (solo si no está grabando)
                    if self.lock_escucha.acquire(blocking=False):
                        self._procesar_comando()
                    else:
                        logger.debug("🔄 Ya grabando...")
        
        except KeyboardInterrupt:
            logger.info("Interrupción por usuario")
            raise
        except Exception as e:
            logger.error(f"Error en loop principal: {e}")
            return ""
    
    def _procesar_comando(self):
        """Graba y transcribe el comando (ejecuta en background)."""
        try:
            # Grabar desde el stream de Porcupine
            audio_stream = self.detector.get_stream()
            audio_array, rms_max, tiempo_grab = self.recorder.grabar_desde_stream(
                audio_stream, self.detector.porcupine, duracion_max=10.0
            )
            
            if audio_array.size == 0:
                logger.warning("No se capturó audio")
                self.lock_escucha.release()
                return
            
            # Guardar WAV
            ruta_audio = self.temp_manager.save_audio_array(
                audio_array, self.detector.porcupine.sample_rate
            )
            
            # Transcribir en background
            future = self.executor.submit(self._transcribir, ruta_audio)
            future.add_done_callback(
                lambda f: self._callback_transcripcion(
                    f, tiempo_grab, rms_max, ruta_audio
                )
            )
            
        except Exception as e:
            logger.error(f"Error procesando comando: {e}")
            if self.lock_escucha.locked():
                self.lock_escucha.release()
    
    def _transcribir(self, wav_path: str) -> tuple:
        """Ejecuta transcripción. Retorna (texto, tiempo)."""
        inicio = time.time()
        texto = transcribe(wav_path, language="es")
        tiempo_total = time.time() - inicio
        return (texto.lower(), tiempo_total)
    
    def _callback_transcripcion(self, future, tiempo_grab, rms, archivo):
        """Callback cuando termina la transcripción."""
        try:
            texto, tiempo_trans = future.result()
            
            if texto:
                # Registrar métrica
                registrar_metrica(tiempo_grab, tiempo_trans, texto, rms, archivo)
                logger.info(f"✅ Transcrito: {texto}")
                
                # Agregar a la cola
                with lock_cola:
                    transcripciones_cola.append(texto)
            
        except Exception as e:
            logger.error(f"Error en callback: {e}")
        finally:
            if self.lock_escucha.locked():
                self.lock_escucha.release()
    
    def cerrar(self):
        """Libera recursos."""
        logger.info("Cerrando WakeWordService...")
        self.detector.cleanup()
        self.executor.shutdown(wait=True)
        
        # Mostrar estadísticas
        stats = obtener_estadisticas()
        if stats:
            logger.info(f"📊 Estadísticas: {stats}")
        
        logger.info("✅ WakeWordService cerrado")
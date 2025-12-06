"""
Grabación de audio desde stream de Porcupine.
Responsabilidad: Capturar audio post-wake-word con detección de silencio.
"""
import numpy as np
import logging
import time

try:
    import webrtcvad
    HAS_VAD = True
except ImportError:
    HAS_VAD = False

logger = logging.getLogger(__name__)

class AudioRecorder:
    """Graba audio desde un stream de PyAudio."""
    
    def __init__(self, vad_aggressiveness: int = 2, 
                 silence_threshold_rms: int = 80):
        """
        Args:
            vad_aggressiveness: Nivel de agresividad VAD (0-3)
            silence_threshold_rms: Umbral RMS para detectar silencio
        """
        self.vad_aggressiveness = vad_aggressiveness
        self.silence_threshold_rms = silence_threshold_rms
        
        # Inicializar VAD si está disponible
        self.vad = None
        if HAS_VAD:
            try:
                self.vad = webrtcvad.Vad(vad_aggressiveness)
                logger.info("✅ webrtcvad inicializado")
            except Exception as e:
                logger.warning(f"Error inicializando VAD: {e}")
    
    def grabar_desde_stream(self, audio_stream, porcupine, 
                           duracion_max: float = 10.0) -> tuple:
        """
        Graba audio desde el stream abierto hasta detectar silencio.
        
        Args:
            audio_stream: Stream de PyAudio abierto
            porcupine: Instancia de Porcupine (para obtener frame_length y sample_rate)
            duracion_max: Duración máxima en segundos
            
        Returns:
            (audio_array, rms_máximo, tiempo_grabacion)
        """
        frames_grabados = []
        frame_size = porcupine.frame_length
        sample_rate = porcupine.sample_rate
        max_frames = int((duracion_max * sample_rate) / frame_size)
        
        logger.info("🎤 Grabando comando...")
        tiempo_inicio = time.time()
        silencio_frames = 0
        rms_maximo = 0
        frames_con_audio = 0
        
        # Configurar umbral de silencio según si tenemos VAD
        if self.vad is not None:
            umbral_silencio = 15  # frames con VAD
        else:
            umbral_silencio = int(1.0 * sample_rate / frame_size)
        
        try:
            for i in range(max_frames):
                try:
                    pcm = audio_stream.read(frame_size, exception_on_overflow=False)
                except IOError as e:
                    logger.warning(f"⚠️ Audio read error: {e}")
                    continue
                
                pcm_16 = np.frombuffer(pcm, dtype=np.int16)
                if pcm_16.size == 0:
                    continue
                
                frames_grabados.append(pcm_16)
                
                # Calcular RMS
                rms = int(np.sqrt(np.mean(pcm_16.astype(np.float32) ** 2)))
                rms_maximo = max(rms_maximo, rms)
                
                # Detectar silencio
                silencio_detectado = self._detectar_silencio(
                    pcm, rms, sample_rate
                )
                
                if silencio_detectado:
                    silencio_frames += 1
                else:
                    silencio_frames = 0
                    frames_con_audio += 1
                
                # Condición de salida: suficiente silencio tras detectar audio
                if silencio_frames > umbral_silencio and frames_con_audio > 5:
                    logger.info(f"⏱️ Silencio detectado - Fin del comando")
                    break
                
                # Timeout
                if time.time() - tiempo_inicio > duracion_max:
                    logger.info(f"⏱️ Timeout ({duracion_max}s) - Fin del comando")
                    break
                    
        except Exception as e:
            logger.error(f"Error durante grabación: {e}")
        
        tiempo_grabacion = time.time() - tiempo_inicio
        
        if frames_grabados:
            audio_final = np.concatenate(frames_grabados)
            duracion = len(audio_final) / sample_rate
            logger.info(
                f"📊 Grabación: {len(frames_grabados)} frames "
                f"({duracion:.2f}s, RMS máx: {rms_maximo})"
            )
            return (audio_final, rms_maximo, tiempo_grabacion)
        
        logger.warning("⚠️ No se grabaron frames")
        return (np.array([], dtype=np.int16), 0, tiempo_grabacion)
    
    def _detectar_silencio(self, pcm: bytes, rms: int, 
                          sample_rate: int) -> bool:
        """Detecta si el frame actual es silencio."""
        if self.vad is not None:
            try:
                return not self.vad.is_speech(pcm, sample_rate)
            except Exception as e:
                logger.debug(f"VAD error: {e}")
                return rms < self.silence_threshold_rms
        else:
            return rms < self.silence_threshold_rms
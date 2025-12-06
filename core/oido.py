import whisper
import os
import pvporcupine
import pyaudio
import numpy as np
import soundfile as sf
from dotenv import load_dotenv
import threading
import time
import logging
import atexit
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from collections import deque

# --- PREPARAR DIRECTORIO DE LOGS Y TEMP ---
os.makedirs("logs", exist_ok=True)
os.makedirs("data/temp", exist_ok=True)

# --- LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/oido.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("oido")

# --- CONFIGURACIÓN DE VOZ ---
load_dotenv()
PICOVOICE_API_KEY = os.getenv('PICOVOICE_API_KEY')
WAKE_WORD = "computadora"
MIC_ID = int(os.getenv('MIC_ID', '1'))
WHISPER_MODEL_SIZE = os.getenv('WHISPER_MODEL', 'small')

RUTA_PPC = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'modelos', 'computadora.ppn'))
RUTA_TEMP = os.path.join("data", "temp")

# --- COLA THREAD-SAFE PARA COMUNICAR TRANSCRIPCIONES ---
transcripciones_cola = deque()
lock_cola = threading.Lock()

# Limpiar archivos WAV antiguos (>1 hora)
def _limpiar_archivos_temp(max_edad_segundos: int = 3600):
    """Elimina archivos WAV temporales más antiguos que max_edad_segundos."""
    try:
        ahora = time.time()
        for archivo in Path(RUTA_TEMP).glob("temp_audio_*.wav"):
            edad = ahora - archivo.stat().st_mtime
            if edad > max_edad_segundos:
                archivo.unlink()
                logger.debug(f"Archivo temp limpiado: {archivo.name}")
    except Exception as e:
        logger.warning(f"Error limpiando archivos temp: {e}")

_limpiar_archivos_temp()

# --- VAD (Voice Activity Detection) ---
try:
    import webrtcvad
    HAS_VAD = True
    logger.info("✅ webrtcvad disponible")
except ImportError:
    HAS_VAD = False
    logger.warning("⚠️ webrtcvad no instalado - usando RMS para VAD")

VAD_AGRESIVENESS = 2

# --- MÉTRICAS ---
@dataclass
class MetricasActivacion:
    """Métricas de una activación wake-word."""
    timestamp: float
    tiempo_grabacion: float
    tiempo_transcripcion: float
    texto: str
    rms: int
    archivo_audio: str
    
    def tiempo_total(self) -> float:
        return self.tiempo_grabacion + self.tiempo_transcripcion

HISTORIAL_METRICAS = []
MAX_METRICAS = 100

# Detectar GPU y fp16
try:
    import torch
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    USE_FP16 = (DEVICE == "cuda")
    logger.info(f"🔧 Torch detectado - Device: {DEVICE}, fp16: {USE_FP16}")
except ImportError:
    DEVICE = "cpu"
    USE_FP16 = False
    logger.warning("⚠️ PyTorch no instalado - usando CPU")

# Cargamos el modelo Whisper una sola vez
logger.info(f"Cargando Whisper modelo '{WHISPER_MODEL_SIZE}' en {DEVICE}...")
try:
    ear_model = whisper.load_model(WHISPER_MODEL_SIZE, device=DEVICE)
    logger.info(f"✅ Whisper cargado correctamente ({WHISPER_MODEL_SIZE})")
except Exception as e:
    logger.error(f"Error cargando Whisper: {e}")
    ear_model = None

# ThreadPoolExecutor para transcripción NO bloqueante
executor = ThreadPoolExecutor(max_workers=2)

# Control de reentrancia / debounce
lock_escucha = threading.Lock()
ultima_activacion = 0
DEBOUNCE_SEGUNDOS = 1.5

def _generar_ruta_audio() -> str:
    """Genera ruta única para archivo WAV con timestamp."""
    timestamp_ms = int(time.time() * 1000)
    return os.path.join(RUTA_TEMP, f"temp_audio_{timestamp_ms}.wav")

def _registrar_metrica(tiempo_grab: float, tiempo_trans: float, texto: str, rms: int, archivo: str):
    """Registra métrica de una activación."""
    metrica = MetricasActivacion(
        timestamp=time.time(),
        tiempo_grabacion=tiempo_grab,
        tiempo_transcripcion=tiempo_trans,
        texto=texto,
        rms=rms,
        archivo_audio=archivo
    )
    HISTORIAL_METRICAS.append(metrica)
    if len(HISTORIAL_METRICAS) > MAX_METRICAS:
        HISTORIAL_METRICAS.pop(0)
    
    logger.info(f"⏱️ Métrica: grab={tiempo_grab:.2f}s, trans={tiempo_trans:.2f}s, "
                f"total={metrica.tiempo_total():.2f}s, rms={rms}")

def obtener_estadisticas_metricas() -> dict:
    """Retorna estadísticas de las últimas activaciones."""
    if not HISTORIAL_METRICAS:
        return {}
    
    tiempos_trans = [m.tiempo_transcripcion for m in HISTORIAL_METRICAS]
    tiempos_grab = [m.tiempo_grabacion for m in HISTORIAL_METRICAS]
    
    return {
        "total_activaciones": len(HISTORIAL_METRICAS),
        "tiempo_transcripcion_promedio": sum(tiempos_trans) / len(tiempos_trans),
        "tiempo_grabacion_promedio": sum(tiempos_grab) / len(tiempos_grab),
        "tiempo_transcripcion_min": min(tiempos_trans),
        "tiempo_transcripcion_max": max(tiempos_trans),
    }

def transcribe(wav_path: str, language: str = "es") -> str:
    """Transcribe un WAV usando el modelo cargado con fp16 si está disponible."""
    if ear_model is None:
        raise RuntimeError("Modelo de ASR no cargado.")
    
    try:
        result = ear_model.transcribe(wav_path, language=language, fp16=USE_FP16)
        return result.get("text", "").strip()
    except Exception as e:
        logger.error(f"Error en transcripción: {e}")
        raise

def _transcribir_en_background(wav_path: str) -> tuple:
    """Función interna para ejecutar transcripción en hilo. Retorna (texto, tiempo)."""
    tiempo_inicio = time.time()
    try:
        texto = transcribe(wav_path, language="es")
        tiempo_total = time.time() - tiempo_inicio
        if texto:
            logger.info(f"Transcripción exitosa ({tiempo_total:.2f}s): {texto}")
        else:
            logger.warning("Transcripción vacía")
        return (texto.lower(), tiempo_total)
    except Exception as e:
        logger.error(f"Error en transcripción background: {e}")
        return ("", time.time() - tiempo_inicio)

def _grabar_desde_stream(audio_stream, porcupine, duracion_max: float = 10.0) -> tuple:
    """
    Graba audio directamente desde el stream abierto de Porcupine.
    Usa webrtcvad si está disponible para detección robusta de silencio.
    Retorna (audio_array, rms_máximo, tiempo_grabacion).
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
    
    # Inicializar VAD si está disponible
    vad = None
    if HAS_VAD:
        try:
            vad = webrtcvad.Vad(1)
            UMBRAL_SILENCIO = 15
        except Exception as e:
            logger.warning(f"Error inicializando VAD: {e}")
            vad = None
            UMBRAL_SILENCIO = int(1.0 * sample_rate / frame_size)
    else:
        UMBRAL_SILENCIO = int(1.0 * sample_rate / frame_size)
    
    UMBRAL_RMS = 80
    
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
            
            rms = int(np.sqrt(np.mean(pcm_16.astype(np.float32) ** 2)))
            rms_maximo = max(rms_maximo, rms)
            
            if i % 10 == 0:
                logger.debug(f"Frame {i}: RMS={rms}, frames_audio={frames_con_audio}")
            
            silencio_detectado = False
            if vad is not None:
                try:
                    is_speech = vad.is_speech(pcm, sample_rate)
                    silencio_detectado = not is_speech
                except Exception as e:
                    logger.debug(f"VAD error: {e}")
                    silencio_detectado = rms < UMBRAL_RMS
            else:
                silencio_detectado = rms < UMBRAL_RMS
            
            if silencio_detectado:
                silencio_frames += 1
            else:
                silencio_frames = 0
                frames_con_audio += 1
            
            if silencio_frames > UMBRAL_SILENCIO and frames_con_audio > 5:
                logger.info(f"⏱️ Silencio detectado - Fin del comando (audio frames: {frames_con_audio})")
                break
            
            if time.time() - tiempo_inicio > duracion_max:
                logger.info(f"⏱️ Timeout ({duracion_max}s) - Fin del comando")
                break
                
    except Exception as e:
        logger.error(f"Error leyendo stream: {e}")
    
    tiempo_grabacion = time.time() - tiempo_inicio
    
    if frames_grabados:
        audio_final = np.concatenate(frames_grabados)
        duracion = len(audio_final) / sample_rate
        logger.info(f"📊 Grabadas {len(frames_grabados)} frames ({duracion:.2f}s, RMS máx: {rms_maximo}, frames audio: {frames_con_audio})")
        return (audio_final, rms_maximo, tiempo_grabacion)
    
    logger.warning("⚠️ No se grabaron frames")
    return (np.array([], dtype=np.int16), 0, tiempo_grabacion)

def _callback_transcripcion(future, lock, tiempo_grab: float, rms: int, archivo: str):
    """Callback que se ejecuta cuando la transcripción termina."""
    try:
        texto, tiempo_trans = future.result()
        if texto:
            _registrar_metrica(
                tiempo_grab=tiempo_grab,
                tiempo_trans=tiempo_trans,
                texto=texto,
                rms=rms,
                archivo=archivo
            )
            logger.info(f"✅ Comando capturado: {texto}")
            
            # ✅ AGREGAR A LA COLA PARA QUE MAIN.PY LO LEA
            with lock_cola:
                transcripciones_cola.append(texto)
                logger.debug(f"📥 Texto agregado a la cola: {texto}")
        else:
            logger.debug("Comando vacío")
    except Exception as e:
        logger.error(f"❌ Error en callback: {e}")
    finally:
        try:
            if lock.locked():
                lock.release()
        except RuntimeError:
            logger.debug("Lock ya liberado")

def _validar_wake_word() -> str:
    """Valida que WAKE_WORD existe en Porcupine y retorna el path."""
    if not os.path.exists(RUTA_PPC):
        raise FileNotFoundError(f"Archivo .ppn no encontrado: {RUTA_PPC}")
    
    logger.info(f"✅ Modelo personalizado '{WAKE_WORD}' en: {RUTA_PPC}")
    return RUTA_PPC

def _choose_input_device_index(pa: pyaudio.PyAudio, preferred_index: int) -> int:
    """Elige el índice de dispositivo de entrada válido o None si no hay."""
    if preferred_index is not None:
        try:
            info = pa.get_device_info_by_index(preferred_index)
            if int(info.get("maxInputChannels", 0)) > 0:
                logger.info(f"Usando MIC_ID configurado: {preferred_index}")
                return preferred_index
            else:
                logger.warning(f"MIC_ID {preferred_index} no tiene canales de entrada válidos")
        except Exception:
            logger.warning(f"MIC_ID {preferred_index} no válido")
    
    try:
        info = pa.get_default_input_device_info()
        idx = int(info["index"])
        logger.info(f"Usando dispositivo por defecto: {idx}")
        return idx
    except Exception:
        for i in range(pa.get_device_count()):
            try:
                d = pa.get_device_info_by_index(i)
                if int(d.get("maxInputChannels", 0)) > 0:
                    logger.info(f"Fallback input device: {i}")
                    return i
            except Exception:
                continue
    
    logger.error("No se encontró dispositivo de entrada válido")
    return None

def detectar_wake_word():
    """
    Loop de baja latencia que escucha la palabra de activación.
    Reutiliza el stream de audio para evitar conflictos.
    """
    global ultima_activacion
    
    if not PICOVOICE_API_KEY:
        logger.error("PICOVOICE_API_KEY no configurada en .env")
        raise RuntimeError("PICOVOICE_API_KEY no configurada en .env")
    
    try:
        keyword_path = _validar_wake_word()
    except FileNotFoundError as e:
        logger.error(f"{e}")
        return ""
    
    MODELO_ESPANOL = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', 'data', 'modelos', 'porcupine_params_es.pv'
    ))
    
    if not os.path.exists(MODELO_ESPANOL):
        logger.error(f"❌ Modelo español no encontrado: {MODELO_ESPANOL}")
        logger.error("Descárgalo desde: https://github.com/Picovoice/porcupine/tree/master/lib/common")
        return ""
    
    logger.info(f"✅ Usando modelo español: {MODELO_ESPANOL}")
    
    keywords = [keyword_path]
    sensitivities = [0.65]
    
    pa = pyaudio.PyAudio()
    porcupine = None
    audio_stream = None
    
    try:
        porcupine = pvporcupine.create(
            access_key=PICOVOICE_API_KEY,
            keyword_paths=keywords,
            sensitivities=sensitivities,
            model_path=MODELO_ESPANOL
        )
        
        input_index = _choose_input_device_index(pa, MIC_ID)
        if input_index is None:
            logger.critical("No hay dispositivo de entrada disponible.")
            return ""
        
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length,
            input_device_index=input_index,
        )
        
        logger.info(f"🎧 Jarvis ONLINE - Esperando '{WAKE_WORD}'")
        
        contador_frames = 0
        
        while True:
            # ✅ VERIFICAR SI HAY TEXTO EN LA COLA
            with lock_cola:
                if transcripciones_cola:
                    texto = transcripciones_cola.popleft()
                    logger.debug(f"📤 Retornando texto al main: {texto}")
                    return texto
            
            try:
                pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            except IOError as e:
                logger.warning(f"⚠️ Audio read error: {e}")
                continue
            except KeyboardInterrupt:
                logger.info("⚠️ Interrupción en lectura de audio")
                raise
            
            pcm_16 = np.frombuffer(pcm, dtype=np.int16)
            if pcm_16.size == 0:
                continue
            
            rms = int(np.sqrt(np.mean(pcm_16.astype(np.float32) ** 2)))
            
            contador_frames += 1
            if contador_frames % 30 == 0:
                logger.debug(f"Nivel RMS: {rms}")
            
            try:
                keyword_index = porcupine.process(pcm_16)
            except Exception as e:
                logger.error(f"Error procesando Porcupine: {e}")
                continue
            
            if keyword_index >= 0:
                ahora = time.time()
                if ahora - ultima_activacion < DEBOUNCE_SEGUNDOS:
                    logger.debug("Debounce activo")
                    continue
                
                logger.info(f"🚨 WAKE WORD DETECTED! (RMS: {rms})")
                ultima_activacion = ahora
                
                if lock_escucha.acquire(blocking=False):
                    try:
                        audio_grabado, rms_max, tiempo_grab = _grabar_desde_stream(
                            audio_stream, porcupine, duracion_max=10.0
                        )
                        
                        if audio_grabado.size == 0:
                            logger.warning("⚠️ No se capturó audio")
                            try:
                                if lock_escucha.locked():
                                    lock_escucha.release()
                            except RuntimeError:
                                pass
                            continue
                        
                        ruta_audio = _generar_ruta_audio()
                        
                        try:
                            sf.write(ruta_audio, audio_grabado, samplerate=porcupine.sample_rate)
                            logger.debug(f"WAV guardado: {ruta_audio}")
                        except Exception as e:
                            logger.error(f"Error guardando WAV: {e}")
                            try:
                                if lock_escucha.locked():
                                    lock_escucha.release()
                            except RuntimeError:
                                pass
                            continue
                        
                        future = executor.submit(_transcribir_en_background, ruta_audio)
                        future.add_done_callback(
                            lambda f: _callback_transcripcion(f, lock_escucha, tiempo_grab, rms_max, ruta_audio)
                        )
                        
                    except Exception as e:
                        logger.error(f"❌ Error durante grabación: {e}")
                        try:
                            if lock_escucha.locked():
                                lock_escucha.release()
                        except RuntimeError:
                            pass
                else:
                    logger.debug("🔄 Grabación en progreso")
                    
    except KeyboardInterrupt:
        logger.info("👋 Interrupción por usuario (Ctrl+C)")
        raise
    except Exception as e:
        logger.critical(f"Error crítico: {e}", exc_info=True)
        return ""
    finally:
        logger.info("Limpiando recursos de sesión...")
        
        if audio_stream is not None:
            try:
                audio_stream.stop_stream()
                audio_stream.close()
                logger.debug("Audio stream cerrado")
            except Exception as e:
                logger.warning(f"Error cerrando stream: {e}")
        
        if porcupine is not None:
            try:
                porcupine.delete()
                logger.debug("Porcupine eliminado")
            except Exception as e:
                logger.warning(f"Error borrando Porcupine: {e}")
        
        try:
            pa.terminate()
            logger.debug("PyAudio terminado")
        except Exception as e:
            logger.warning(f"Error terminando PyAudio: {e}")
        
        logger.info("Sesión de escucha finalizada")

def cerrar_sistema():
    """
    Cierra recursos globales al finalizar el programa completamente.
    Debe ser llamado desde main.py en el finally del __main__.
    """
    logger.info("🔌 Cerrando sistema de audio completo...")
    
    try:
        # Cerrar el executor global
        executor.shutdown(wait=True)
        logger.debug("✅ Executor apagado")
    except Exception as e:
        logger.warning(f"Error cerrando executor: {e}")
    
    # Mostrar estadísticas finales
    stats = obtener_estadisticas_metricas()
    if stats:
        logger.info(f"📊 Estadísticas finales de sesión:")
        logger.info(f"   • Total activaciones: {stats['total_activaciones']}")
        logger.info(f"   • Tiempo transcripción promedio: {stats['tiempo_transcripcion_promedio']:.2f}s")
        logger.info(f"   • Tiempo grabación promedio: {stats['tiempo_grabacion_promedio']:.2f}s")
    
    logger.info("✅ Sistema auditivo completamente apagado")

# ✅ REGISTRAR LIMPIEZA AUTOMÁTICA AL SALIR DEL PROGRAMA
atexit.register(cerrar_sistema)

# Alias público
escuchar = detectar_wake_word
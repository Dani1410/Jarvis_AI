"""
API pública del módulo de reconocimiento de voz.
Exporta solo las funciones principales que otros módulos necesitan.
"""
from .service import WakeWordService
from .transcriber import transcribe, load_model

# Instancia global del servicio (singleton)
_service_instance = None

def get_service(api_key: str = None, wake_word: str = "computadora", mic_id: int = 1):
    """
    Retorna la instancia del servicio de wake word (lazy loading).
    
    Args:
        api_key: API key de Picovoice (requerido en primera llamada)
        wake_word: Palabra de activación
        mic_id: ID del micrófono
    """
    global _service_instance
    if _service_instance is None:
        if api_key is None:
            raise ValueError("api_key es requerido para inicializar el servicio")
        _service_instance = WakeWordService(api_key, wake_word, mic_id)
    return _service_instance

def escuchar():
    """
    Interfaz simple para escuchar y transcribir audio.
    Mantiene compatibilidad con el código existente.
    """
    service = get_service()
    return service.escuchar()

__all__ = ['escuchar', 'transcribe', 'get_service', 'load_model']
"""
Manejo de entrada de audio desde el micrófono.
Responsabilidad: Capturar audio del hardware.
"""
import speech_recognition as sr
from typing import Optional

class AudioInput:
    """Captura audio desde el micrófono usando PyAudio."""
    
    def __init__(self, energy_threshold: int = 1000, pause_threshold: float = 0.8):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.pause_threshold = pause_threshold
    
    def capture(self, timeout: int = 5, phrase_time_limit: int = 8) -> Optional[sr.AudioData]:
        """
        Captura audio desde el micrófono.
        
        Args:
            timeout: Segundos máximos de espera para detectar audio
            phrase_time_limit: Duración máxima de la frase en segundos
            
        Returns:
            AudioData object o None si timeout
        """
        with sr.Microphone() as source:
            print("🎤 Escuchando...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            try:
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
                return audio
            except sr.WaitTimeoutError:
                print("⏱️ Timeout - No se detectó audio")
                return None
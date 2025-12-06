"""
Sistema de métricas y monitoreo del módulo de voz.
Responsabilidad: Registrar y analizar estadísticas de rendimiento.
"""
from dataclasses import dataclass
from typing import List
import time

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

class MetricsCollector:
    """Recolector centralizado de métricas."""
    
    def __init__(self, max_metricas: int = 100):
        self.historial: List[MetricasActivacion] = []
        self.max_metricas = max_metricas
    
    def registrar(self, tiempo_grab: float, tiempo_trans: float, 
                  texto: str, rms: int, archivo: str):
        """Registra una nueva métrica."""
        metrica = MetricasActivacion(
            timestamp=time.time(),
            tiempo_grabacion=tiempo_grab,
            tiempo_transcripcion=tiempo_trans,
            texto=texto,
            rms=rms,
            archivo_audio=archivo
        )
        self.historial.append(metrica)
        
        # Limitar tamaño del historial
        if len(self.historial) > self.max_metricas:
            self.historial.pop(0)
        
        return metrica
    
    def obtener_estadisticas(self) -> dict:
        """Retorna estadísticas agregadas."""
        if not self.historial:
            return {}
        
        tiempos_trans = [m.tiempo_transcripcion for m in self.historial]
        tiempos_grab = [m.tiempo_grabacion for m in self.historial]
        tiempos_totales = [m.tiempo_total() for m in self.historial]
        
        return {
            "total_activaciones": len(self.historial),
            "tiempo_transcripcion_promedio": sum(tiempos_trans) / len(tiempos_trans),
            "tiempo_grabacion_promedio": sum(tiempos_grab) / len(tiempos_grab),
            "tiempo_total_promedio": sum(tiempos_totales) / len(tiempos_totales),
            "tiempo_transcripcion_min": min(tiempos_trans),
            "tiempo_transcripcion_max": max(tiempos_trans),
            "rms_promedio": sum(m.rms for m in self.historial) / len(self.historial),
        }
    
    def limpiar(self):
        """Limpia el historial."""
        self.historial.clear()

# Instancia global
_collector = MetricsCollector()

def registrar_metrica(tiempo_grab: float, tiempo_trans: float, 
                     texto: str, rms: int, archivo: str):
    """Función pública para registrar métricas."""
    return _collector.registrar(tiempo_grab, tiempo_trans, texto, rms, archivo)

def obtener_estadisticas() -> dict:
    """Función pública para obtener estadísticas."""
    return _collector.obtener_estadisticas()
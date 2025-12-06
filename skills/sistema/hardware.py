"""
Módulo para monitoreo de hardware del sistema.
Responsabilidad: Leer métricas del hardware (batería, CPU, RAM, etc.)
"""
import psutil


def obtener_bateria():
    """Retorna el porcentaje de batería o None si no está disponible."""
    bateria = psutil.sensors_battery()
    if bateria:
        return {
            'porcentaje': bateria.percent,
            'conectado': bateria.power_plugged,
            'tiempo_restante': bateria.secsleft if bateria.secsleft != psutil.POWER_TIME_UNLIMITED else None
        }
    return None


def obtener_uso_cpu(intervalo=1):
    """Retorna el porcentaje de uso del CPU."""
    return psutil.cpu_percent(interval=intervalo)


def obtener_memoria():
    """Retorna información sobre el uso de memoria RAM."""
    memoria = psutil.virtual_memory()
    return {
        'porcentaje': memoria.percent,
        'total_gb': round(memoria.total / (1024**3), 2),
        'disponible_gb': round(memoria.available / (1024**3), 2)
    }


def obtener_disco():
    """Retorna información sobre el uso de disco."""
    disco = psutil.disk_usage('/')
    return {
        'porcentaje': disco.percent,
        'total_gb': round(disco.total / (1024**3), 2),
        'libre_gb': round(disco.free / (1024**3), 2)
    }
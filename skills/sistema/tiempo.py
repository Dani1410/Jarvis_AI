"""
Módulo para manejo de fecha y hora.
Responsabilidad: Proveer información temporal.
"""
import datetime


def obtener_hora_actual():
    """Retorna la hora actual en formato legible."""
    hora = datetime.datetime.now().strftime('%I:%M %p')
    return f"Son las {hora}"


def obtener_fecha_actual():
    """Retorna la fecha actual en formato legible."""
    fecha = datetime.datetime.now().strftime('%d de %B de %Y')
    return f"Hoy es {fecha}"


def obtener_dia_semana():
    """Retorna el día de la semana actual."""
    dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
    dia_numero = datetime.datetime.now().weekday()
    return dias[dia_numero]


def obtener_timestamp():
    """Retorna un timestamp formateado."""
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def es_fin_de_semana():
    """Retorna True si es sábado o domingo."""
    return datetime.datetime.now().weekday() >= 5
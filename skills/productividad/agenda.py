from .tiempo_parser import parsear_tiempo_a_segundos  # Importa la nueva función

def programar_recordatorio(mensaje, tiempo_str):
    """Programa un recordatorio único o recurrente."""
    segundos, recurrente = parsear_tiempo_a_segundos(tiempo_str)  # Usa la nueva función
    
    if segundos > 0:
        t = threading.Thread(
            target=_proceso_recordatorio, 
            args=(mensaje, segundos, recurrente),
            daemon=True
        )
        t.start()
        
        tipo = "recurrente" if recurrente else "único"
        tiempo_legible = f"{int(segundos/3600)}h" if segundos >= 3600 else f"{int(segundos/60)}m" if segundos >= 60 else f"{int(segundos)}s"
        
        return f"Recordatorio {tipo} configurado cada {tiempo_legible}: '{mensaje}'"
    else:
        return "No pude calcular el tiempo para el recordatorio."
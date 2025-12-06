import datetime
import time
import threading
import dateparser
from .utils import cargar_datos, guardar_datos

# Importar voz de forma relativa al proyecto principal
try:
    from modulos import voz
except ImportError:
    # Fallback si se ejecuta desde otro contexto
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from modulos import voz

def agregar_evento(descripcion, fecha_texto):
    """Agrega un evento a la agenda con interpretación de fecha natural."""
    # Parsear fecha en español
    dt = dateparser.parse(fecha_texto, languages=['es'], settings={'PREFER_DATES_FROM': 'future'})
    
    if not dt:
        return "No entendí la fecha del evento. Intenta ser más claro."
    
    # Si la fecha ya pasó, asumimos que es para la próxima semana
    if dt < datetime.datetime.now():
        dt = dt + datetime.timedelta(days=7)

    fecha_str = dt.strftime("%Y-%m-%d %H:%M")
    
    data = cargar_datos()
    data["eventos"].append({
        "evento": descripcion, 
        "fecha": fecha_str,
        "notificado": False
    })
    guardar_datos(data)
    
    return f"Evento '{descripcion}' agendado para el {fecha_str}"

def ver_eventos():
    """Muestra los próximos eventos."""
    data = cargar_datos()
    
    if not data["eventos"]:
        return "No tienes eventos programados."
    
    respuesta = "Próximos eventos:\n"
    
    # Ordenar por fecha
    eventos_ordenados = sorted(data["eventos"], key=lambda x: x["fecha"])
    
    for i, evento in enumerate(eventos_ordenados[:5], 1):
        respuesta += f"📅 {i}. {evento['fecha']}: {evento['evento']}\n"
    
    return respuesta

def ver_pendientes():
    """Muestra un resumen de tareas y eventos."""
    data = cargar_datos()
    respuesta = ""
    
    # Tareas
    if data["tareas"]:
        tareas_pendientes = [t for t in data["tareas"] if t["estado"] == "pendiente"]
        respuesta += f"Tienes {len(tareas_pendientes)} tareas pendientes.\n"
        for t in tareas_pendientes[-3:]:
            respuesta += f"  ⏳ {t['descripcion']}\n"
    else:
        respuesta += "No tienes tareas pendientes.\n"

    # Eventos
    if data["eventos"]:
        respuesta += "\nPróximos eventos:\n"
        for e in data["eventos"][-3:]:
            respuesta += f"  📅 {e['fecha']}: {e['evento']}\n"
    else:
        respuesta += "No tienes eventos programados.\n"
            
    if not respuesta.strip():
        respuesta = "Tu agenda está vacía, eres libre."
        
    return respuesta

# --- SISTEMA DE RECORDATORIOS ---
def _proceso_recordatorio(mensaje, segundos, recurrente):
    """Hilo que ejecuta el recordatorio en segundo plano."""
    while True:
        time.sleep(segundos)
        voz.hablar(f"⏰ RECORDATORIO: {mensaje}")
        print(f"\n🔔 RECORDATORIO: {mensaje}")
        
        if not recurrente:
            break

def programar_recordatorio(mensaje, tiempo_str):
    """Programa un recordatorio único o recurrente."""
    segundos = 0
    recurrente = False
    
    # 1. Detectar recurrencia ("cada hora", "cada 30 minutos")
    if "cada" in tiempo_str.lower():
        recurrente = True
        
        if "hora" in tiempo_str:
            segundos = 3600
        elif "minuto" in tiempo_str:
            # Extraer número si existe
            palabras = tiempo_str.split()
            for palabra in palabras:
                if palabra.isdigit():
                    segundos = int(palabra) * 60
                    break
            if segundos == 0:
                segundos = 60  # 1 minuto por defecto
        elif "segundo" in tiempo_str:
            segundos = 1
    
    # 2. Detectar tiempo puntual ("en 20 minutos", "mañana a las 3")
    else:
        dt = dateparser.parse(tiempo_str, languages=['es'], settings={'PREFER_DATES_FROM': 'future'})
        if dt:
            ahora = datetime.datetime.now()
            segundos = (dt - ahora).total_seconds()
    
    if segundos > 0:
        # Lanzar hilo demonio
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
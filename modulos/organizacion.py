import json
import os
import time
import threading
import dateparser # El experto en fechas
import datetime
from . import voz

ARCHIVO_AGENDA = os.path.join("datos", "agenda_jarvis.json")

# --- GESTIÓN DE DATOS ---
def cargar_datos():
    if not os.path.exists(ARCHIVO_AGENDA):
        return {"tareas": [], "eventos": []}
    try:
        with open(ARCHIVO_AGENDA, "r") as f:
            return json.load(f)
    except:
        return {"tareas": [], "eventos": []}

def guardar_datos(data):
    with open(ARCHIVO_AGENDA, "w") as f:
        json.dump(data, f, indent=4)

# --- FUNCIONES PRINCIPALES ---
def agregar_tarea(descripcion):
    data = cargar_datos()
    # Guardamos la tarea con fecha de creación
    nueva = {
        "descripcion": descripcion,
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "estado": "pendiente"
    }
    data["tareas"].append(nueva)
    guardar_datos(data)
    return f"Tarea anotada: {descripcion}"

def agregar_evento(descripcion, fecha_texto):
    # fecha_texto es lo que dices: "el viernes a las 5", "mañana"
    dt = dateparser.parse(fecha_texto, languages=['es'])
    
    if not dt:
        return "No entendí la fecha del evento. Intenta ser más claro."
    
    # Si la fecha ya pasó (ej: "el viernes" y hoy es sábado), dateparser asume pasado.
    # Ajuste simple para fechas futuras:
    if dt < datetime.datetime.now():
        dt = dt + datetime.timedelta(days=7)

    fecha_str = dt.strftime("%Y-%m-%d %H:%M")
    
    data = cargar_datos()
    data["eventos"].append({"evento": descripcion, "fecha": fecha_str})
    guardar_datos(data)
    return f"Evento '{descripcion}' agendado para el {fecha_str}"

def ver_pendientes():
    data = cargar_datos()
    respuesta = ""
    
    if data["tareas"]:
        respuesta += f"Tienes {len(data['tareas'])} tareas pendientes.\n"
        for i, t in enumerate(data["tareas"][-3:]): # Muestra las últimas 3
            respuesta += f"- {t['descripcion']}\n"
    else:
        respuesta += "No tienes tareas pendientes. "

    if data["eventos"]:
        respuesta += "\nPróximos eventos:\n"
        for e in data["eventos"][-3:]:
            respuesta += f"- {e['fecha']}: {e['evento']}\n"
            
    if not respuesta:
        respuesta = "Tu agenda está vacía, eres libre."
        
    return respuesta

# --- MOTOR DE RECORDATORIOS (BACKGROUND) ---
def _proceso_recordatorio(mensaje, segundos, recurrente):
    """Esta función corre en un universo paralelo (hilo)"""
    while True:
        time.sleep(segundos)
        voz.hablar(f"⏰ RECORDATORIO: {mensaje}")
        if not recurrente:
            break # Si no es recurrente, el hilo muere aquí

def programar_recordatorio(mensaje, tiempo_str):
    segundos = 0
    recurrente = False
    
    # 1. Detectar recurrencia ("cada hora", "cada minuto")
    if "cada" in tiempo_str:
        recurrente = True
        if "hora" in tiempo_str: segundos = 3600
        elif "minuto" in tiempo_str: segundos = 60
        elif "segundo" in tiempo_str: segundos = 1 # Solo para pruebas
    
    # 2. Detectar tiempo puntual ("en 20 minutos")
    else:
        dt = dateparser.parse(tiempo_str)
        if dt:
            ahora = datetime.datetime.now()
            segundos = (dt - ahora).total_seconds()
    
    if segundos > 0:
        # Lanzamos el hilo demonio (se cierra si cierras el programa)
        t = threading.Thread(target=_proceso_recordatorio, args=(mensaje, segundos, recurrente))
        t.daemon = True 
        t.start()
        
        tipo = "recurrente" if recurrente else "único"
        return f"Recordatorio {tipo} configurado en {int(segundos)} segundos."
    else:
        return "No pude calcular el tiempo para el recordatorio."
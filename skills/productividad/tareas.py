import datetime
from .utils import cargar_datos, guardar_datos

def agregar_tarea(descripcion):
    """Agrega una nueva tarea a la lista de pendientes."""
    data = cargar_datos()
    
    nueva = {
        "descripcion": descripcion,
        "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "estado": "pendiente"
    }
    
    data["tareas"].append(nueva)
    guardar_datos(data)
    
    return f"Tarea anotada: {descripcion}"

def ver_tareas():
    """Muestra las tareas pendientes."""
    data = cargar_datos()
    
    if not data["tareas"]:
        return "No tienes tareas pendientes."
    
    respuesta = f"Tienes {len(data['tareas'])} tareas pendientes:\n"
    
    # Muestra las últimas 5 tareas
    for i, tarea in enumerate(data["tareas"][-5:], 1):
        estado_emoji = "✅" if tarea["estado"] == "completada" else "⏳"
        respuesta += f"{estado_emoji} {i}. {tarea['descripcion']}\n"
    
    return respuesta

def marcar_tarea_completada(indice):
    """Marca una tarea como completada por su índice."""
    data = cargar_datos()
    
    if not data["tareas"]:
        return "No hay tareas para completar."
    
    try:
        # Los índices en la interfaz empiezan en 1
        data["tareas"][indice - 1]["estado"] = "completada"
        guardar_datos(data)
        return f"Tarea {indice} marcada como completada."
    except IndexError:
        return "Ese número de tarea no existe."

def eliminar_tarea(indice):
    """Elimina una tarea por su índice."""
    data = cargar_datos()
    
    if not data["tareas"]:
        return "No hay tareas para eliminar."
    
    try:
        tarea_eliminada = data["tareas"].pop(indice - 1)
        guardar_datos(data)
        return f"Tarea eliminada: {tarea_eliminada['descripcion']}"
    except IndexError:
        return "Ese número de tarea no existe."
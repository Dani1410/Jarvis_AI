import json
import os

ARCHIVO_AGENDA = os.path.join("data", "agenda.json")

def cargar_datos():
    """Carga los datos de la agenda desde el archivo JSON."""
    # Asegurar que la carpeta data exista
    os.makedirs(os.path.dirname(ARCHIVO_AGENDA), exist_ok=True)
    
    if not os.path.exists(ARCHIVO_AGENDA):
        return {"tareas": [], "eventos": []}
    try:
        with open(ARCHIVO_AGENDA, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"tareas": [], "eventos": []}

def guardar_datos(data):
    """Guarda los datos de la agenda en el archivo JSON."""
    os.makedirs(os.path.dirname(ARCHIVO_AGENDA), exist_ok=True)
    with open(ARCHIVO_AGENDA, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
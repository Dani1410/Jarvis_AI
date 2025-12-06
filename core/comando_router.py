from skills.productividad import (
    agregar_tarea, 
    ver_tareas, 
    agregar_evento, 
    ver_pendientes,
    programar_recordatorio
)
from skills.social import leer_correos_gmail, contar_correos_nuevos
from skills.browser import (
    gestionar_whatsapp, 
    leer_pagina, 
    descargar_archivo
)

def ejecutar_comando(texto):
    """
    Mapea el texto de entrada a la función de habilidad correcta.
    Retorna True si ejecutó algo, False si no.
    """
    
    # === PRODUCTIVIDAD ===
    if "agregar tarea" in texto or "nueva tarea" in texto:
        if "agregar tarea" in texto:
            descripcion = texto.split("agregar tarea", 1)[1].strip()
        else:
            descripcion = texto.split("nueva tarea", 1)[1].strip()
        
        if descripcion:
            return agregar_tarea(descripcion)
        return "¿Qué tarea quieres agregar?"
    
    if "ver tareas" in texto or "mis tareas" in texto:
        return ver_tareas()
    
    if "agregar evento" in texto or "nuevo evento" in texto:
        partes = texto.split("evento", 1)[1].strip().split(" en ", 1)
        if len(partes) == 2:
            descripcion, fecha = partes
            return agregar_evento(descripcion.strip(), fecha.strip())
        return "¿Qué evento y cuándo?"
    
    if "ver pendientes" in texto or "qué tengo pendiente" in texto:
        return ver_pendientes()
    
    if "recordatorio" in texto:
        partes = texto.split("recordatorio", 1)[1].strip()
        return programar_recordatorio(partes.strip())
    
    # === EMAIL ===
    if "leer correos" in texto or "revisar email" in texto or "correo" in texto:
        return leer_correos_gmail()
    
    if "cuántos correos" in texto:
        cantidad = contar_correos_nuevos()
        return f"Tienes {cantidad} correos sin leer"
    
    # === WHATSAPP ===
    if "whatsapp" in texto or "whats" in texto:
        gestionar_whatsapp()
        return True
    
    # === WEB SCRAPING ===
    if "leer página" in texto or "extraer contenido" in texto:
        return "¿Qué URL quieres que lea?"
    
    if "descargar archivo" in texto:
        return "URL del archivo: "
    
    return False
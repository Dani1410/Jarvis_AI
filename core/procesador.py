"""
Procesador de comandos centralizado.
Responsabilidad: Enrutar comandos a los módulos especializados.
"""
import os
import pyperclip
import pywhatkit

try:
    from core import voz, cerebro
    from core import memoria_vectorial as memoria
except ImportError:
    import voz
    import cerebro
    import memoria_vectorial as memoria

from skills.social import email_handler
from skills.productividad import agenda, tareas
from skills.browser import scraper, whatsapp
from skills.browser import driver as nav_driver
from skills.sistema import hardware, control, apps
from skills.utilidades import tiempo

def ejecutar(texto):
    """
    Procesa el texto y ejecuta acciones. Retorna True si ejecutó algo, False si no.
    """
    
    # --- 1. NAVEGACIÓN WEB ---
    if "resume esta web" in texto or "lee esta página" in texto:
        try:
            url = pyperclip.paste()
            if "http" not in url:
                voz.hablar("Primero copia una URL válida.")
                return True
            
            contenido = scraper.leer_pagina(url)
            resumen = cerebro.pensar(f"Resume este texto: {contenido}")
            voz.hablar(resumen)
        except Exception as e:
            voz.hablar(f"Error leyendo el portapapeles: {e}")
        return True
    
    # --- WHATSAPP ---
    if "abre whatsapp" in texto or "whatsapp" in texto:
        voz.hablar("Abriendo WhatsApp...")
        resultado = whatsapp.abrir_whatsapp_web()
        voz.hablar(resultado)
        return True
    
    if "lee whatsapp" in texto or "mensajes whatsapp" in texto:
        resultado = whatsapp.leer_mensajes_whatsapp()
        voz.hablar(resultado)
        return True

    # --- DESCARGAS ---
    if "descarga esto" in texto or "descargar archivo" in texto:
        url = pyperclip.paste()
        
        if "http" not in url:
            voz.hablar("Copia primero una URL válida.")
            return True
            
        ext = url.split(".")[-1]
        if len(ext) > 4: 
            ext = "file"
        
        import random
        nombre = f"descarga_jarvis_{random.randint(1000, 9999)}.{ext}"
        resp = scraper.descargar_archivo(url, nombre)
        voz.hablar(resp)
        return True
    
    # --- MEMORIA ---
    if "recuerda que" in texto or "guarda que" in texto:
        dato = texto.replace("recuerda que", "").replace("guarda que", "").strip()
        memoria.guardar(dato)
        voz.hablar("Dato guardado en memoria.")
        return True

    # --- SISTEMA (Hardware) ---
    if "batería" in texto:
        info_bateria = hardware.obtener_bateria()
        if info_bateria:
            voz.hablar(f"Batería al {info_bateria['porcentaje']} por ciento.")
        else:
            voz.hablar("No puedo leer la batería.")
        return True
    
    if "cpu" in texto or "procesador" in texto:
        uso = hardware.obtener_uso_cpu()
        voz.hablar(f"Uso del procesador: {uso} por ciento.")
        return True

    # --- FECHA Y HORA ---
    if "hora" in texto or "qué hora" in texto:
        respuesta = tiempo.obtener_hora_actual()
        voz.hablar(respuesta)
        return True
        
    if "fecha" in texto or "qué día" in texto:
        respuesta = tiempo.obtener_fecha_actual()
        voz.hablar(respuesta)
        return True

    # --- MULTIMEDIA ---
    if "reproduce" in texto or "pon" in texto:
        cancion = texto.replace("reproduce", "").replace("pon", "").strip()
        voz.hablar(f"Poniendo {cancion}.")
        pywhatkit.playonyt(cancion)
        return True

    if "busca" in texto or "búscame" in texto:
        busqueda = texto.replace("busca", "").replace("búscame", "").strip()
        voz.hablar(f"Buscando {busqueda}.")
        pywhatkit.search(busqueda)
        return True

    # --- CONTROL DE LAPTOP ---
    if "sube el volumen" in texto or "más volumen" in texto:
        respuesta = control.subir_volumen(5)
        voz.hablar("Subiendo volumen.")
        return True
        
    if "baja el volumen" in texto or "menos volumen" in texto:
        respuesta = control.bajar_volumen(5)
        voz.hablar("Bajando volumen.")
        return True
    
    if "captura" in texto or "screenshot" in texto:
        voz.hablar("Tomando captura.")
        respuesta = control.tomar_captura()
        print(respuesta)
        voz.hablar("Captura guardada.")
        return True

    # --- APLICACIONES ---
    if "abre" in texto and "whatsapp" not in texto:
        app = texto.replace("abre", "").strip()
        voz.hablar(f"Abriendo {app}")
        respuesta = apps.abrir_aplicacion(app)
        print(respuesta)
        return True
    
    # --- SOCIAL (Email) ---
    if "correos" in texto or "email" in texto or "gmail" in texto:
        email_handler.leer_correos_gmail()
        return True
    
    # --- PRODUCTIVIDAD ---
    if "crea tarea" in texto or "nueva tarea" in texto or "agregar tarea" in texto:
        tarea_texto = texto.replace("crea tarea", "").replace("nueva tarea", "").replace("agregar tarea", "").strip()
        resp = tareas.agregar_tarea(tarea_texto)
        voz.hablar(resp)
        return True

    if "ver tareas" in texto or "mis tareas" in texto:
        resp = tareas.ver_tareas()
        voz.hablar(resp)
        print(resp)
        return True

    if "evento" in texto and ("agregar" in texto or "nuevo" in texto):
        voz.hablar("¿Qué evento quieres agendar?")
        return True

    if "qué tengo" in texto or "pendientes" in texto or "agenda" in texto:
        from skills.productividad import ver_pendientes
        resp = ver_pendientes()
        voz.hablar(resp)
        print(resp)
        return True

    # --- EXIT ---
    if "descansa" in texto or "apágate" in texto or "adiós" in texto:
        voz.hablar("Desconectando sistemas. Hasta pronto, jefe.")
        exit()

    return False
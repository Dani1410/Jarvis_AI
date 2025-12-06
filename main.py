import logging
import os
from dotenv import load_dotenv

# Importaciones de CORE
from core import voz, cerebro, oido

# Importaciones de skills organizadas
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

# 1. Cargar secretos (.env) al inicio
load_dotenv()

# 2. Configuración de Logs
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    filename='logs/jarvis.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# FUNCIÓN DE LÓGICA PRINCIPAL
# -------------------------------------------------------------

def ejecutar_accion(texto):
    """Procesa comandos específicos y retorna True si ejecutó algo."""
    
    # === PRODUCTIVIDAD ===
    if "agregar tarea" in texto or "nueva tarea" in texto:
        if "agregar tarea" in texto:
            descripcion = texto.split("agregar tarea", 1)[1].strip()
        else:
            descripcion = texto.split("nueva tarea", 1)[1].strip()
        
        if descripcion:
            resultado = agregar_tarea(descripcion)
            voz.hablar(resultado)
            print(f"✅ {resultado}")
        else:
            voz.hablar("¿Qué tarea quieres agregar?")
        return True
    
    if "ver tareas" in texto or "mis tareas" in texto:
        resultado = ver_tareas()
        print(f"\n📋 {resultado}")
        voz.hablar(resultado)
        return True
    
    if "agregar evento" in texto or "nuevo evento" in texto:
        partes = texto.split("evento", 1)[1].strip().split(" en ", 1)
        
        if len(partes) == 2:
            descripcion, fecha = partes
            resultado = agregar_evento(descripcion.strip(), fecha.strip())
        else:
            descripcion = input("¿Qué evento? ")
            fecha = input("¿Cuándo? (ej: mañana a las 3, el viernes) ")
            resultado = agregar_evento(descripcion, fecha)
        
        voz.hablar(resultado)
        print(f"📅 {resultado}")
        return True
    
    if "ver pendientes" in texto or "qué tengo pendiente" in texto:
        resultado = ver_pendientes()
        print(f"\n{resultado}")
        voz.hablar(resultado)
        return True
    
    if "recordatorio" in texto:
        partes = texto.split("recordatorio", 1)[1].strip()
        
        if " cada " in partes or " en " in partes:
            if " cada " in partes:
                mensaje, tiempo = partes.split(" cada ", 1)
                tiempo = "cada " + tiempo
            else:
                mensaje, tiempo = partes.split(" en ", 1)
                tiempo = "en " + tiempo
            
            resultado = programar_recordatorio(mensaje.strip(), tiempo.strip())
        else:
            mensaje = input("¿Qué te recuerdo? ")
            tiempo = input("¿Cuándo? (ej: cada hora, en 20 minutos) ")
            resultado = programar_recordatorio(mensaje, tiempo)
        
        voz.hablar(resultado)
        print(f"⏰ {resultado}")
        return True
    
    # === EMAIL ===
    if "leer correos" in texto or "revisar email" in texto or "correo" in texto:
        resultado = leer_correos_gmail()
        print(f"📧 {resultado}")
        return True
    
    if "cuántos correos" in texto:
        cantidad = contar_correos_nuevos()
        mensaje = f"Tienes {cantidad} correos sin leer"
        voz.hablar(mensaje)
        print(f"📧 {mensaje}")
        return True
    
    # === WHATSAPP ===
    if "whatsapp" in texto or "whats" in texto:
        gestionar_whatsapp()
        return True
    
    # === WEB SCRAPING ===
    if "leer página" in texto or "extraer contenido" in texto:
        url = input("¿Qué URL quieres que lea? ")
        contenido = leer_pagina(url)
        print(f"\n📄 CONTENIDO EXTRAÍDO:\n{contenido}\n")
        voz.hablar("He extraído el contenido de la página")
        return True
    
    if "descargar archivo" in texto:
        url = input("URL del archivo: ")
        nombre = input("Nombre del archivo (con extensión): ")
        resultado = descargar_archivo(url, nombre)
        voz.hablar(resultado)
        print(f"💾 {resultado}")
        return True
    
    return False

def run_jarvis_session(get_input_fn, mode_name):
    """Ejecuta el bucle principal de Jarvis."""
    
    print("\n" + "="*60)
    print("🤖 JARVIS AI - SISTEMA ACTIVADO")
    print("="*60)
    print(f"📝 MODO {mode_name} ACTIVADO")
    print("Comandos disponibles:")
    print("  • Agregar tarea [descripción]")
    print("  • Ver tareas")
    print("  • Agregar evento [fecha] [descripción]")
    print("  • Ver pendientes")
    print("  • Programar recordatorio [tiempo] [mensaje]")
    print("  • Leer correos / Contar correos nuevos")
    print("  • Abrir WhatsApp")
    print("  • O pregunta cualquier cosa a la IA")
    print("\n(Escribe 'salir' para terminar)\n")
    print("="*60 + "\n")
    
    logger.info(f"SISTEMA INICIADO EN MODO {mode_name}")
    voz.hablar("Sistemas online. Escribe tu orden.")

    while True:
        try:
            texto = get_input_fn()
            
            if not texto:
                continue
            
            if texto.lower() in ['salir', 'exit', 'apagar', 'cerrar']:
                voz.hablar("Hasta pronto, jefe.")
                logger.info("Sistema detenido normalmente")
                break
            
            logger.info(f"Input Usuario: {texto}")

            if ejecutar_accion(texto):
                logger.info("Acción ejecutada con éxito.")
                continue
            
            print("\n🧠 Procesando con Llama 3.2...")
            respuesta = cerebro.pensar(texto)
            
            logger.info(f"Respuesta IA: {respuesta[:100]}...")
            print(f"\n🤖 JARVIS: {respuesta}\n")
            voz.hablar(respuesta)

        except KeyboardInterrupt:
            print("\n\n⚠️ Apagado forzado (Ctrl+C)")
            voz.hablar("Apagado de emergencia.")
            logger.info("Sistema detenido por usuario (Ctrl+C)")
            break
            
        except Exception as e:
            logger.error(f"Error crítico en ciclo main: {e}", exc_info=True)
            print(f"\n❌ Ocurrió un error: {e}\n")
            voz.hablar("Hubo un error procesando tu comando")

# --- PUNTO DE ENTRADA PRINCIPAL ---
if __name__ == "__main__":
    try:
        run_jarvis_session(oido.escuchar, "VOZ/MIC")
    except KeyboardInterrupt:
        print("\n⚠️ Programa terminado por usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        print(f"\n❌ Error fatal: {e}")
    finally:
        print("\n🔌 Jarvis AI - Desconectado")
        logger.info("Sistema completamente apagado")
        # La función cerrar_sistema() se llama automáticamente por atexit
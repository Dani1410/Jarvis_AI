"""
JARVIS AI - Asistente Virtual Inteligente
Punto de entrada principal del sistema.
"""
import logging
import os
from dotenv import load_dotenv

# ====== IMPORTACIONES CORE ======
from core import voz, cerebro
from core.oido import get_service

# ====== SKILLS ======
from skills.productividad import (
    agregar_tarea, 
    ver_tareas, 
    agregar_evento, 
    ver_pendientes,
    programar_recordatorio
)
from skills.social import leer_correos_gmail, contar_correos_nuevos
from skills.browser import gestionar_whatsapp, leer_pagina, descargar_archivo

# ====== IMPORTAR MÓDULOS DE SISTEMA ======
from skills.sistema import control, hardware, apps

# ====== CONFIGURACIÓN ======
load_dotenv()

# Configurar logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/jarvis.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ====== VARIABLES DE CONFIGURACIÓN ======
PICOVOICE_API_KEY = os.getenv('PICOVOICE_API_KEY')
WAKE_WORD = os.getenv('WAKE_WORD', 'computadora')
MIC_ID = int(os.getenv('MIC_ID', '1'))

# ====== PROCESADOR DE COMANDOS ======

def ejecutar_accion(texto: str) -> bool:
    """
    Procesa comandos específicos y retorna True si ejecutó algo.
    
    Args:
        texto: Comando del usuario
        
    Returns:
        True si se ejecutó una acción específica, False si debe ir a la IA
    """
    texto = texto.lower().strip()
    
    # === CONTROL DE SISTEMA ===
    if "captura" in texto or "screenshot" in texto or "pantallazo" in texto:
        voz.hablar("Tomando captura de pantalla.")
        try:
            resultado = control.tomar_captura()
            logger.info(f"Captura: {resultado}")
            print(f"📸 {resultado}")
            voz.hablar("Captura guardada correctamente.")
        except Exception as e:
            logger.error(f"Error tomando captura: {e}")
            voz.hablar("Error al tomar la captura.")
        return True
    
    if "sube el volumen" in texto or "subir volumen" in texto or "más volumen" in texto:
        try:
            incremento = 10
            resultado = control.subir_volumen(incremento)
            voz.hablar("Volumen subido.")
            logger.info(f"Volumen: +{incremento}%")
        except Exception as e:
            logger.error(f"Error subiendo volumen: {e}")
            voz.hablar("No pude subir el volumen.")
        return True
    
    if "baja el volumen" in texto or "bajar volumen" in texto or "menos volumen" in texto:
        try:
            decremento = 10
            resultado = control.bajar_volumen(decremento)
            voz.hablar("Volumen bajado.")
            logger.info(f"Volumen: -{decremento}%")
        except Exception as e:
            logger.error(f"Error bajando volumen: {e}")
            voz.hablar("No pude bajar el volumen.")
        return True
    
    if "silenciar" in texto or "mutear" in texto:
        try:
            control.silenciar()
            voz.hablar("Sistema silenciado.")
        except Exception as e:
            voz.hablar("Error al silenciar.")
        return True
    
    # === INFORMACIÓN DE HARDWARE ===
    if "batería" in texto or "nivel de batería" in texto:
        try:
            info = hardware.obtener_bateria()
            if info:
                porcentaje = info['porcentaje']
                estado = "conectado" if info['conectado'] else "desconectado"
                mensaje = f"Batería al {porcentaje} por ciento, {estado}."
                voz.hablar(mensaje)
                print(f"🔋 {mensaje}")
            else:
                voz.hablar("No puedo leer la batería.")
        except Exception as e:
            logger.error(f"Error leyendo batería: {e}")
            voz.hablar("Error consultando batería.")
        return True
    
    if "uso de cpu" in texto or "procesador" in texto or "cpu" in texto:
        try:
            uso = hardware.obtener_uso_cpu()
            mensaje = f"Uso del procesador: {uso} por ciento."
            voz.hablar(mensaje)
            print(f"💻 {mensaje}")
        except Exception as e:
            logger.error(f"Error leyendo CPU: {e}")
            voz.hablar("Error consultando procesador.")
        return True
    
    if "uso de ram" in texto or "memoria ram" in texto or "memoria" in texto:
        try:
            uso = hardware.obtener_uso_ram()
            mensaje = f"Uso de memoria RAM: {uso} por ciento."
            voz.hablar(mensaje)
            print(f"🧠 {mensaje}")
        except Exception as e:
            logger.error(f"Error leyendo RAM: {e}")
            voz.hablar("Error consultando memoria.")
        return True
    
    # === ABRIR APLICACIONES ===
    if "abre" in texto or "abrir" in texto:
        # Extraer nombre de la app
        app_nombre = texto.replace("abre", "").replace("abrir", "").strip()
        
        # Filtrar comandos que no son apps
        if app_nombre and app_nombre not in ["whatsapp", "whats"]:
            voz.hablar(f"Abriendo {app_nombre}.")
            try:
                resultado = apps.abrir_aplicacion(app_nombre)
                logger.info(f"App abierta: {resultado}")
                print(f"🚀 {resultado}")
            except Exception as e:
                logger.error(f"Error abriendo app: {e}")
                voz.hablar(f"No pude abrir {app_nombre}.")
            return True
    
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
            voz.hablar("¿Qué evento y cuándo?")
            return True
        
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
            voz.hablar("¿Qué te recuerdo y cuándo?")
            return True
        
        voz.hablar(resultado)
        print(f"⏰ {resultado}")
        return True
    
    # === EMAIL ===
    if "leer correos" in texto or "revisar email" in texto:
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
        voz.hablar("Copia la URL que quieres que lea")
        return True
    
    if "descargar archivo" in texto:
        voz.hablar("Copia la URL del archivo a descargar")
        return True
    
    # === COMANDOS DE SISTEMA ===
    if any(word in texto for word in ['salir', 'exit', 'apagar', 'cerrar', 'descansa', 'adiós']):
        return "EXIT"
    
    return False

# ====== LOOP PRINCIPAL ======

def run_jarvis_with_wake_word():
    """
    Ejecuta Jarvis con detección de wake word usando Porcupine.
    Este es el modo de operación principal.
    """
    if not PICOVOICE_API_KEY:
        logger.error("PICOVOICE_API_KEY no configurada en .env")
        print("❌ Error: PICOVOICE_API_KEY no encontrada en .env")
        return
    
    print("\n" + "="*70)
    print("🤖 JARVIS AI - SISTEMA ACTIVADO (MODO WAKE WORD)")
    print("="*70)
    print(f"🎯 Wake Word: '{WAKE_WORD}'")
    print(f"🎤 Micrófono ID: {MIC_ID}")
    print("\n📋 Comandos de sistema:")
    print("  • Toma una captura / screenshot")
    print("  • Sube/baja el volumen")
    print("  • Batería / CPU / RAM")
    print("  • Abre [aplicación]")
    print("\n📌 Comandos de productividad:")
    print("  • Agregar tarea [descripción]")
    print("  • Ver tareas / Ver pendientes")
    print("  • Agregar evento [descripción] en [fecha]")
    print("  • Leer correos / WhatsApp")
    print(f"\nDi '{WAKE_WORD}' seguido de tu comando")
    print("(Presiona Ctrl+C para salir)\n")
    print("="*70 + "\n")
    
    logger.info("Sistema iniciado en modo WAKE WORD")
    
    # Inicializar servicio de wake word
    try:
        service = get_service(
            api_key=PICOVOICE_API_KEY,
            wake_word=WAKE_WORD,
            mic_id=MIC_ID
        )
        service.iniciar()
        
        voz.hablar("Sistemas online. Di mi nombre para activarme.")
        
    except FileNotFoundError as e:
        logger.error(f"Archivos de modelo no encontrados: {e}")
        print(f"❌ {e}")
        print("\nAsegúrate de tener:")
        print(f"  • data/modelos/{WAKE_WORD}.ppn")
        print("  • data/modelos/porcupine_params_es.pv")
        return
    except Exception as e:
        logger.error(f"Error inicializando servicio: {e}", exc_info=True)
        print(f"❌ Error crítico: {e}")
        return
    
    # Loop principal
    while True:
        try:
            # Escuchar wake word y comando
            texto = service.escuchar()
            
            if not texto:
                continue
            
            logger.info(f"Comando recibido: {texto}")
            print(f"\n👤 TÚ: {texto}")
            
            # Procesar comando
            resultado = ejecutar_accion(texto)
            
            if resultado == "EXIT":
                voz.hablar("Hasta pronto, jefe.")
                logger.info("Sistema apagado por comando de usuario")
                break
            
            if resultado:  # Si ejecutó una acción específica
                logger.info("Acción específica ejecutada")
                continue
            
            # Si no es un comando específico, usar IA
            print("🧠 Procesando con IA...")
            respuesta = cerebro.pensar(texto)
            
            logger.info(f"Respuesta IA: {respuesta[:100]}...")
            print(f"\n🤖 JARVIS: {respuesta}\n")
            voz.hablar(respuesta)
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Apagado por usuario (Ctrl+C)")
            voz.hablar("Apagado de emergencia.")
            logger.info("Sistema detenido por Ctrl+C")
            break
        
        except Exception as e:
            logger.error(f"Error en ciclo principal: {e}", exc_info=True)
            print(f"\n❌ Error: {e}")
            voz.hablar("Hubo un error. Intenta de nuevo.")
    
    # Limpieza
    try:
        service.cerrar()
        logger.info("Servicio cerrado correctamente")
    except Exception as e:
        logger.warning(f"Error cerrando servicio: {e}")

# ====== PUNTO DE ENTRADA ======

if __name__ == "__main__":
    try:
        run_jarvis_with_wake_word()
        
    except KeyboardInterrupt:
        print("\n⚠️ Programa terminado por usuario")
        
    except Exception as e:
        logger.critical(f"Error fatal: {e}", exc_info=True)
        print(f"\n❌ Error fatal: {e}")
        
    finally:
        print("\n" + "="*70)
        print("🔌 JARVIS AI - DESCONECTADO")
        print("="*70)
        logger.info("Sistema completamente apagado")
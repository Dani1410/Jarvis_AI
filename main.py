import logging
import os
from dotenv import load_dotenv

# Importaciones de módulos core
from modulos import voz, cerebro

# Importaciones de skills organizadas
from skills.productividad import (
    agregar_tarea, 
    ver_tareas, 
    agregar_evento, 
    ver_pendientes,
    programar_recordatorio
)
from skills.social import leer_correos_gmail, contar_correos_nuevos
from modulos.whatsapp import gestionar_whatsapp
from modulos.web_scraper import leer_pagina, descargar_archivo

# from modulos import oido # Mantén esto comentado mientras uses solo texto

# 1. Cargar secretos (.env) al inicio
load_dotenv()

# 2. Configuración de Logs (Historial de errores y acciones)
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    filename='logs/jarvis.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

def ejecutar_accion(texto):
    """
    Procesa comandos específicos y retorna True si ejecutó algo.
    """
    
    # === PRODUCTIVIDAD ===
    if "agregar tarea" in texto or "nueva tarea" in texto:
        # Extraer descripción después del comando
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
        # Ejemplo: "agregar evento reunión mañana a las 3"
        partes = texto.split("evento", 1)[1].strip().split(" en ", 1)
        
        if len(partes) == 2:
            descripcion, fecha = partes
            resultado = agregar_evento(descripcion.strip(), fecha.strip())
        else:
            # Si no tiene " en ", intentar interpretar todo
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
        # Ejemplo: "recordatorio tomar agua cada 30 minutos"
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
    
    # No se ejecutó ninguna acción
    return False

def main():
    print("\n" + "="*60)
    print("🤖 JARVIS AI - SISTEMA ACTIVADO")
    print("="*60)
    print("📝 MODO DEBUG (TEXTO) ACTIVADO")
    print("Comandos disponibles:")
    print("  • Agregar tarea [descripción]")
    print("  • Ver tareas")
    print("  • Agregar evento [descripción] en [fecha]")
    print("  • Recordatorio [mensaje] cada/en [tiempo]")
    print("  • Leer correos")
    print("  • WhatsApp")
    print("  • O pregunta cualquier cosa a la IA")
    print("\n(Escribe 'salir' para terminar)\n")
    print("="*60 + "\n")
    
    logging.info("SISTEMA INICIADO EN MODO TEXTO")
    voz.hablar("Sistemas online. Escribe tu orden.")

    while True:
        try:
            # 1. ENTRADA: Usamos input() en lugar de micrófono
            texto = input("\n👉 TÚ: ").strip().lower()
        except KeyboardInterrupt:
            print("\n\n⚠️ Apagado forzado.")
            logging.info("Sistema detenido por usuario (Ctrl+C)")
            break 

        if not texto: 
            continue
        
        if texto == "salir":
            voz.hablar("Hasta pronto, jefe.")
            logging.info("Sistema detenido normalmente")
            break
        
        # Guardamos en el log lo que escribiste
        logging.info(f"Input Usuario: {texto}")

        try:
            # 2. ACCIONES: Probamos si ejecuta comandos
            if ejecutar_accion(texto):
                logging.info("Acción ejecutada con éxito.")
                continue
            
            # 3. PENSAMIENTO: Si no es comando, preguntamos a Ollama
            print("\n🧠 Procesando con Llama 3.2...")
            respuesta = cerebro.pensar(texto)
            
            logging.info(f"Respuesta IA: {respuesta[:100]}...")
            print(f"\n🤖 JARVIS: {respuesta}\n")
            voz.hablar(respuesta)

        except Exception as e:
            logging.error(f"Error crítico en ciclo main: {e}")
            print(f"\n❌ Ocurrió un error: {e}\n")
            voz.hablar("Hubo un error procesando tu comando")

if __name__ == "__main__":
    main()
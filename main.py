import logging
import os
from dotenv import load_dotenv
# Importamos los módulos desde la carpeta 'modulos'
from modulos import voz, cerebro, acciones
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
    encoding='utf-8' # <--- AGREGA ESTO
)

def main():
    print("\n--- 📝 MODO DEBUG (TEXTO) ACTIVADO ---")
    print("Escribe tus comandos para probar las nuevas funciones.")
    print("(Escribe 'salir' para terminar)\n")
    
    logging.info("SISTEMA INICIADO EN MODO TEXTO")
    voz.hablar("Sistemas online. Escribe tu orden.")

    while True:
        try:
            # 1. ENTRADA: Usamos input() en lugar de micrófono
            texto = input("\n👉 TÚ: ").strip().lower()
        except KeyboardInterrupt:
            print("\nApagado forzado.")
            break 

        if not texto: continue
        if texto == "salir": break
        
        # Guardamos en el log lo que escribiste
        logging.info(f"Input Usuario: {texto}")

        try:
            # 2. ACCIONES: Probamos si ejecuta comandos (Twitter, Noticias, Tareas, etc.)
            if acciones.ejecutar(texto):
                logging.info("Acción ejecutada con éxito.")
                continue
            
            # 3. PENSAMIENTO: Si no es comando, preguntamos a Ollama
            # Agregamos un print visual para saber que está pensando
            print("--> Procesando con Llama 3.2...")
            respuesta = cerebro.pensar(texto)
            
            logging.info(f"Respuesta IA: {respuesta[:50]}...") # Logueamos solo el inicio
            voz.hablar(respuesta)

        except Exception as e:
            logging.error(f"Error crítico en ciclo main: {e}")
            print(f"❌ Ocurrió un error: {e}")

if __name__ == "__main__":
    main()
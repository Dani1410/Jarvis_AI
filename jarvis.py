import voz
import oido
import cerebro
import acciones
import os  # <--- NUEVO
from dotenv import load_dotenv  # <--- NUEVO

load_dotenv()

EMAIL_USUARIO = os.getenv('EMAIL_USUARIO')
EMAIL_PASS = os.getenv('EMAIL_PASS')

def main():
    print("--- MODO DEBUG (TEXTO) ACTIVADO ---")
    print("Escribe tus comandos. (Escribe 'salir' para terminar)")
    
    while True:
        # 1. ENTRADA: Usamos input() en lugar de oido.escuchar()
        try:
            texto = input("\n👉 TÚ: ").lower()
        except KeyboardInterrupt:
            break # Permite salir con Ctrl+C

        if not texto: continue
        
        if texto == "salir": break
        
        # 2. ACCIONES: Probamos si ejecuta comandos (Spotify, Volumen, etc.)
        if acciones.ejecutar(texto):
            continue
            
        # 3. PENSAMIENTO: Si no es comando, preguntamos a Ollama
        respuesta = cerebro.pensar(texto)
        voz.hablar(respuesta)

if __name__ == "__main__":
    main()
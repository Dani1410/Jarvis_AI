import voz
import oido
import cerebro
import acciones

def main():
    voz.hablar("Sistemas modulares en línea. Te escucho.")
    
    while True:
        # 1. Escuchar
        texto = oido.escuchar()
        if not texto: continue
        
        # 2. Verificar si es una acción (Música, Volumen, etc.)
        if acciones.ejecutar(texto):
            continue
            
        # 3. Si no es acción, pensar respuesta
        respuesta = cerebro.pensar(texto)
        voz.hablar(respuesta)

if __name__ == "__main__":
    main()
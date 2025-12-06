from .driver import iniciar_driver, ensure_profile_dir
from .scraper import leer_pagina, descargar_archivo
from .whatsapp import abrir, leer_nuevos, enviar_mensaje

# Crear alias para mantener compatibilidad con main.py
def gestionar_whatsapp():
    """Menú interactivo de WhatsApp."""
    print("\n" + "="*50)
    print("🟢 MENÚ WHATSAPP - JARVIS AI")
    print("="*50)
    print("1. Abrir WhatsApp Web")
    print("2. Leer mensajes nuevos")
    print("3. Enviar mensaje")
    print("4. Salir")
    print("="*50)
    
    while True:
        try:
            opcion = input("\n👉 Selecciona una opción (1-4): ").strip()
            
            if opcion == "1":
                resultado = abrir()
                print(f"\n✅ {resultado}")
                
            elif opcion == "2":
                resultado = leer_nuevos()
                print(f"\n📩 {resultado}")
                
            elif opcion == "3":
                contacto = input("Nombre del contacto: ").strip()
                mensaje = input("Mensaje: ").strip()
                resultado = enviar_mensaje(contacto, mensaje)
                print(f"\n💬 {resultado}")
                
            elif opcion == "4":
                print("Saliendo del menú de WhatsApp.")
                break
                
            else:
                print("❌ Opción inválida. Intenta de nuevo.")
                
        except KeyboardInterrupt:
            print("\n\n⚠️ Operación cancelada por el usuario.")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {e}")

__all__ = [
    'iniciar_driver',
    'ensure_profile_dir', 
    'leer_pagina',
    'descargar_archivo',
    'gestionar_whatsapp',
    'abrir',
    'leer_nuevos',
    'enviar_mensaje'
]
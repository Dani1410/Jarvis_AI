"""
Script de prueba para enviar archivos adjuntos por WhatsApp Web.
Prueba específica: Enviar un archivo fijo a un contacto predefinido.
"""
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
import sys
import time
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Cargar módulos locales
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "test"))
load_dotenv(ROOT / ".env")

# Importar módulos personalizados
import whatsapp_features as WF
from usar_perfil_selenium import open_chat

# Configuración
PROFILE_DIR = Path(os.getenv("CHROME_PROFILE_SELENIUM_PATH"))
CHAT_TEST = "Dani SIM Telcel"  # Contacto fijo para pruebas

# Archivo a enviar (ajusta esta ruta según tu sistema)
FILE_TO_SEND = r"C:\Users\axel0\Downloads\grafica1.png"
CAPTION = "Prueba de envío automático"  # Caption opcional


def create_driver():
    """Crea el driver de Selenium con el perfil configurado."""
    opciones = Options()
    opciones.add_argument(f"--user-data-dir={PROFILE_DIR}")
    opciones.add_argument("--no-first-run")
    opciones.add_experimental_option("detach", True)
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opciones)


def main():
    print("=" * 60)
    print("TEST: Envío de archivo adjunto por WhatsApp")
    print("=" * 60)
    
    # Validar que el archivo existe
    if not Path(FILE_TO_SEND).exists():
        print(f"❌ ERROR: El archivo no existe: {FILE_TO_SEND}")
        print("Por favor, ajusta la variable FILE_TO_SEND en el script.")
        return
    
    print(f"\n📄 Archivo a enviar: {FILE_TO_SEND}")
    print(f"👤 Contacto destino: {CHAT_TEST}")
    print(f"📝 Caption: {CAPTION if CAPTION else '(sin caption)'}")
    
    driver = create_driver()
    
    try:
        # 1. Abrir WhatsApp Web
        print("\n[1/4] Abriendo WhatsApp Web...")
        driver.get("https://web.whatsapp.com/")
        
        # Esperar grid de chats
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='grid']")))
        print("✅ WhatsApp Web cargado correctamente")
        time.sleep(2)
        
        # 2. Abrir chat del contacto
        print(f"\n[2/4] Abriendo chat con '{CHAT_TEST}'...")
        panel = open_chat(driver, CHAT_TEST, wait_time=10)
        
        if not panel:
            print(f"❌ ERROR: No se pudo abrir el chat con '{CHAT_TEST}'")
            return
        
        print("✅ Chat abierto correctamente")
        time.sleep(1)
        
        # 3. Enviar el archivo
        print(f"\n[3/4] Enviando archivo adjunto...")
        print(f"    📎 Archivo: {Path(FILE_TO_SEND).name}")
        
        success = WF.send_file(driver, FILE_TO_SEND, caption=CAPTION)
        
        if success:
            print("\n✅ ÉXITO: Archivo enviado correctamente")
        else:
            print("\n❌ ERROR: No se pudo enviar el archivo")
            print("Revisa los logs anteriores para más detalles")
        
        # 4. Resultado final
        print("\n[4/4] Prueba completada")
        print("=" * 60)
        
        if success:
            print("✅ RESULTADO: PRUEBA EXITOSA")
        else:
            print("❌ RESULTADO: PRUEBA FALLIDA")
        
        print("=" * 60)
        
    except Exception as e:
        logging.exception(f"Error durante la prueba: {e}")
        print(f"\n❌ ERROR INESPERADO: {e}")
    
    finally:
        # Mantener navegador abierto para inspección
        input("\nPresiona ENTER para cerrar el navegador...")
        driver.quit()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  TEST DE ENVÍO DE ARCHIVOS ADJUNTOS - WhatsApp Web")
    print("=" * 60)
    
    # Verificar archivo antes de iniciar
    if not Path(FILE_TO_SEND).exists():
        print(f"\n⚠️  ADVERTENCIA: El archivo configurado no existe")
        print(f"    Ruta: {FILE_TO_SEND}")
        print("\nPor favor, edita la variable FILE_TO_SEND en el script")
        print("con la ruta de un archivo válido en tu sistema.")
        input("\nPresiona ENTER para salir...")
    else:
        main()
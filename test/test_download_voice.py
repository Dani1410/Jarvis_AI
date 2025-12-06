"""
Script rápido para probar descarga de notas de voz sin menú interactivo.
"""
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os
import sys
import logging

# Cargar módulos locales
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "test"))
load_dotenv(ROOT / ".env")

import whatsapp_features as WF

logging.basicConfig(level=logging.INFO)

PROFILE_DIR = Path(os.getenv("CHROME_PROFILE_SELENIUM_PATH"))
CHAT_TEST = "Dani SIM Telcel"  # El chat fijo para pruebas

def create_driver():
    opciones = Options()
    opciones.add_argument(f"--user-data-dir={PROFILE_DIR}")
    opciones.add_argument("--no-first-run")
    opciones.add_experimental_option("detach", True)
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opciones)

def main():
    print("=== Test rápido: Descarga de nota de voz ===")
    driver = create_driver()
    
    try:
        # Abrir WhatsApp directo al chat
        print(f"Abriendo WhatsApp y navegando a {CHAT_TEST}...")
        driver.get("https://web.whatsapp.com/")
        
        # Esperar grid de chats
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='grid']")))
        
        # Importar función de abrir chat
        from usar_perfil_selenium import open_chat
        panel = open_chat(driver, CHAT_TEST, wait_time=10)
        
        if not panel:
            print("❌ No se pudo abrir el chat.")
            return
        
        print("✅ Chat abierto. Leyendo mensajes...")
        msgs = WF.read_last_messages(driver, n=20)
        
        # DEBUG: Imprimir estructura de TODOS los mensajes
        print(f"\n📋 Se encontraron {len(msgs)} mensajes:")
        for i, m in enumerate(msgs):
            print(f"\n--- Mensaje {i+1} ---")
            print(f"Tipo: {m.get('type')}")
            print(f"Dirección: {m.get('direction')}")
            print(f"Texto: {m.get('text')[:100] if m.get('text') else 'N/A'}")
            
            # Imprimir HTML del elemento para debug
            try:
                html = m["element"].get_attribute("outerHTML")[:500]
                print(f"HTML (primeros 500 chars): {html}")
            except Exception as e:
                print(f"No se pudo obtener HTML: {e}")
        
        # Buscar nota de voz
        audio_msg = None
        for m in msgs:
            if m.get("type") == "audio" and m.get("direction") == "in":
                audio_msg = m
                break
        
        if not audio_msg:
            print("\n❌ No hay notas de voz entrantes en los últimos 20 mensajes.")
            print("👆 Revisa el output arriba para ver qué tipos de mensajes se detectaron.")
            input("Presiona ENTER para cerrar...")
            return
        
        print("\n🎤 Nota de voz encontrada. Intentando descargar...")
        ogg_path = WF.download_voice_from_message(driver, audio_msg["element"])
        
        if ogg_path:
            print(f"✅ Descargado: {ogg_path}")
            wav_path = WF.convert_ogg_to_wav(ogg_path)
            if wav_path:
                print(f"✅ Convertido a WAV: {wav_path}")
        else:
            print("❌ No se pudo descargar.")
            
    except Exception as e:
        logging.exception("Error en test:")
    finally:
        input("Presiona ENTER para cerrar el navegador...")
        driver.quit()

if __name__ == "__main__":
    main()
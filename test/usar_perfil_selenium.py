from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys
import os
from dotenv import load_dotenv

# Carga el .env desde el raíz del proyecto
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

profile_str = os.getenv("CHROME_PROFILE_SELENIUM_PATH")
if not profile_str:
    raise RuntimeError("CHROME_PROFILE_SELENIUM_PATH no está definido en .env")
PROFILE_DIR = Path(profile_str)

def ensure_profile_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Directorio de perfil creado en: {path}")
    else:
        print(f"Usando directorio de perfil existente: {path}")

def create_driver(profile_path: Path) -> webdriver.Chrome:
    opciones = Options()
    opciones.add_argument(f"--user-data-dir={profile_path}")
    opciones.add_argument("--no-first-run")
    opciones.add_argument("--no-default-browser-check")
    opciones.add_argument("--disable-extensions")
    opciones.add_argument("--disable-popup-blocking")
    opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
    opciones.add_experimental_option("detach", True)
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opciones)

def get_first_chat_name(driver, timeout=10):
    wait = WebDriverWait(driver, timeout)
    grid = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='grid']")))
    rows = grid.find_elements(By.CSS_SELECTOR, "div[role='row']")
    if not rows:
        return None
    first = rows[0]
    aria = first.get_attribute("aria-label") or ""
    if aria:
        return aria.split(",")[0].strip()
    try:
        title = first.find_element(By.CSS_SELECTOR, "span[title]")
        return title.get_attribute("title") or title.text
    except Exception:
        return None

def get_first_unread_chat_name(driver, timeout=10):
    wait = WebDriverWait(driver, timeout)
    # Esperamos a que aparezca la lista de chats
    grid = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='grid']")))
    
    # Obtenemos todas las filas (chats) visibles
    rows = grid.find_elements(By.CSS_SELECTOR, "div[role='row']")
    
    for row in rows:
        try:
            # --- CORRECCIÓN CLAVE ---
            # Buscamos DENTRO de la fila (usando .//) cualquier elemento cuyo aria-label
            # contenga la frase "no leí" (esto detecta "no leído" y "no leídos").
            badge = row.find_elements(By.XPATH, ".//span[contains(@aria-label, 'no leí')]")
            
            # También buscamos por el icono visual del punto verde (por si acaso)
            if not badge:
                badge = row.find_elements(By.CSS_SELECTOR, "span[aria-label*='no leí']")

            if badge:
                # ¡ENCONTRADO! Este chat tiene mensajes pendientes.
                # Ahora extraemos el nombre. El nombre siempre está en un span con atributo 'title'.
                title_element = row.find_element(By.CSS_SELECTOR, "span[title]")
                name = title_element.get_attribute("title")
                
                # Opcional: Imprimir para debug
                # count = badge[0].get_attribute("aria-label")
                # print(f"Detectado: {name} ({count})")
                
                return name
                
        except Exception as e:
            # Si falla leer una fila específica, pasamos a la siguiente
            continue
            
    return None

def main():
    try:
        ensure_profile_dir(PROFILE_DIR)
        print("Abriendo Chrome con perfil exclusivo para Selenium...")
        driver = create_driver(PROFILE_DIR)
        driver.get("https://web.whatsapp.com/")
        print("WhatsApp Web abierto. Esperando 8s a que cargue la sesión...")
        time.sleep(8)

        unread = get_first_unread_chat_name(driver)
        if unread:
            print("Primer chat con no leídos:", unread)
        else:
            print("No hay chats con mensajes sin leer.")

        first = get_first_chat_name(driver)
        if first:
            print("Primer chat (más reciente):", first)
        time.sleep(5)
    except Exception as e:
        print("Ocurrió un error al lanzar Chrome:", e, file=sys.stderr)

if __name__ == "__main__":
    main()
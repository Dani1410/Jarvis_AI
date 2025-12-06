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
    # Fallback: intentar por título visible
    try:
        title = first.find_element(By.CSS_SELECTOR, "span[title]")
        return title.get_attribute("title") or title.text
    except Exception:
        return None

def main():
    try:
        ensure_profile_dir(PROFILE_DIR)
        print("Abriendo Chrome con perfil exclusivo para Selenium...")
        driver = create_driver(PROFILE_DIR)
        driver.get("https://web.whatsapp.com/")
        print("WhatsApp Web abierto. Esperando 8s a que cargue la sesión...")
        time.sleep(8)

        name = get_first_chat_name(driver)
        if name:
            print("Primer chat (más reciente):", name)
        else:
            print("No se pudo obtener el nombre del primer chat.")
        time.sleep(5)
    except Exception as e:
        print("Ocurrió un error al lanzar Chrome:", e, file=sys.stderr)

if __name__ == "__main__":
    main()
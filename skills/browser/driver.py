import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv 

# ❌ INCORRECTO: from . import voz
# ✅ CORRECTO:
try:
    from core import voz
except ImportError:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from core import voz

load_dotenv()

CHROME_PROFILE_SELENIUM_PATH = os.getenv('CHROME_PROFILE_SELENIUM_PATH')
PROFILE_DIR = Path(CHROME_PROFILE_SELENIUM_PATH)

def ensure_profile_dir():
    """Asegura que la carpeta del perfil exista"""
    if not PROFILE_DIR.exists():
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)

def iniciar_driver():
    """Inicia el Chrome de Jarvis (independiente del tuyo)."""
    ensure_profile_dir()
    
    opciones = Options()
    opciones.add_argument(f"user-data-dir={PROFILE_DIR}")
    opciones.add_argument("--no-first-run")
    opciones.add_argument("--no-default-browser-check")
    opciones.add_argument("--disable-extensions")
    opciones.add_experimental_option("detach", True) 
    opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=opciones
        )
        return driver
    except Exception as e:
        voz.hablar("Error crítico al iniciar el navegador de Jarvis.")
        print(f"Error Selenium: {e}")
        return None
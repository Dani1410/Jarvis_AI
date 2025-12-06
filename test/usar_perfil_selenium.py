#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script interactivo para usar WhatsApp Web con Selenium + perfil de Chrome.
Integración con funcionalidades avanzadas (historial de mensajes).
Se espera que exista el archivo test/whatsapp_features.py (módulo con read_last_messages).

Dependencias recomendadas:
 - selenium, webdriver-manager
"""
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
)
from typing import Optional
import importlib.util
import time
import sys
import os
import re
import logging
from dotenv import load_dotenv
from selenium.webdriver.chrome.options import Options

# Config logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Carga el .env desde el raíz del proyecto
ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

profile_str = os.getenv("CHROME_PROFILE_SELENIUM_PATH")
if not profile_str:
    raise RuntimeError("CHROME_PROFILE_SELENIUM_PATH no está definido en .env")
PROFILE_DIR = Path(profile_str)


# ---------------- Helper: cargar módulos locales por path (importlib) ---------------- #
def load_module_from_path(name: str, path: Path):
    """Carga dinámicamente un módulo Python desde un archivo si existe."""
    if not path.exists():
        logging.debug(f"Module path {path} does not exist.")
        return None
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None:
        logging.warning(f"No se pudo crear spec para {path}")
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)  # type: ignore
        logging.info(f"Modulo cargado: {name} desde {path}")
        return mod
    except Exception as e:
        logging.exception(f"Fallo cargando módulo {path}: {e}")
        return None


# ---------------------- Resto de tus funciones (detección / apertura / envío) ---------------------- #
def ensure_profile_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Directorio de perfil creado en: {path}")
    else:
        logging.info(f"Usando directorio de perfil existente: {path}")


def create_driver(profile_path: Path, headless=False, download_dir: Optional[str] = None):
    opciones = Options()
    opciones.add_argument(f"--user-data-dir={profile_path}")
    opciones.add_argument("--no-first-run")
    opciones.add_argument("--no-default-browser-check")
    opciones.add_argument("--disable-extensions")
    opciones.add_argument("--disable-popup-blocking")
    opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
    opciones.add_experimental_option("detach", True)
    
    if headless:
        opciones.add_argument("--headless=new")
        opciones.add_argument("--disable-gpu")
    
    if download_dir:
        prefs = {
            "download.default_directory": str(download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0
        }
        opciones.add_experimental_option("prefs", prefs)
    
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opciones)


def wait_for_chat_grid(driver, timeout=30):
    wait = WebDriverWait(driver, timeout)
    grid = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='grid']")))
    return grid


def get_chat_rows_from_grid(grid):
    return grid.find_elements(By.CSS_SELECTOR, "div[role='row']")


UNREAD_RE = re.compile(
    r"("
    r"(no\s*le[ií]d[oa]s?)|"
    r"(sin\s+leer)|"
    r"(mensajes?\s+sin\s+leer)|"
    r"(mensaje?s?\s+nuevo?s?)|"
    r"(nuev[oa]s?\s+mensajes?)|"
    r"(unread)|(unread\s+message)"
    r")",
    re.I
)


def row_has_unread_indicator(row) -> bool:
    try:
        aria = (row.get_attribute("aria-label") or "").strip()
        if aria and UNREAD_RE.search(aria):
            return True
        candidates = row.find_elements(By.XPATH, ".//span | .//div")
        for c in candidates:
            try:
                txt = (c.text or "").strip()
                if txt and re.fullmatch(r"\d+", txt):
                    return True
                aria_c = (c.get_attribute("aria-label") or "").strip()
                if aria_c and UNREAD_RE.search(aria_c):
                    return True
            except Exception:
                continue
    except Exception:
        return False
    return False


def extract_name_from_row(row) -> Optional[str]:
    try:
        aria = (row.get_attribute("aria-label") or "").strip()
        if aria:
            parts = aria.split(",")
            if parts:
                name = parts[0].strip()
                if name:
                    return name
        try:
            title_el = row.find_element(By.CSS_SELECTOR, "span[title]")
            title = title_el.get_attribute("title") or title_el.text
            if title:
                return title.strip()
        except Exception:
            pass
        for selector in ("h4", "div[role='gridcell'] > div > span"):
            try:
                el = row.find_element(By.CSS_SELECTOR, selector)
                txt = (el.text or "").strip()
                if txt:
                    return txt
            except Exception:
                continue
        txt_all = (row.text or "").strip()
        if txt_all:
            return txt_all.splitlines()[0].strip()
    except Exception:
        return None
    return None


def find_unread_chats(driver, max_scrolls=6, wait_between_scrolls=1.0, timeout_grid=30):
    grid = wait_for_chat_grid(driver, timeout=timeout_grid)
    unread = []
    seen_rows = set()
    for attempt in range(max_scrolls):
        rows = get_chat_rows_from_grid(grid)
        logging.debug(f"Intento {attempt+1}: filas visibles = {len(rows)}")
        for row in rows:
            try:
                rid = row.id if hasattr(row, "id") else (row.get_attribute("data-id") or row.text)
                if rid in seen_rows:
                    continue
                seen_rows.add(rid)
                if row_has_unread_indicator(row):
                    name = extract_name_from_row(row)
                    if name:
                        if name not in unread:
                            unread.append(name)
                            logging.info(f"Unread encontrado: {name}")
                    else:
                        logging.info("Unread encontrado pero no se pudo extraer el nombre de la fila.")
            except Exception as e:
                logging.debug(f"Fallo leyendo fila: {e}")
                continue
        if unread:
            return unread
        try:
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].clientHeight;", grid)
        except Exception:
            driver.execute_script("window.scrollBy(0, 300);")
        time.sleep(wait_between_scrolls)
    return unread


SEARCH_ARIA_KEYWORDS = [
    "Search", "Buscar", "Buscar o iniciar", "Search or start", "Suchen", "Chercher",
    "Buscar o iniciar un chat", "Buscar chats"
]
BUTTON_USE_WHATSAPP_PATTERNS = [
    re.compile(r".*Use WhatsApp Web.*", re.I),
    re.compile(r".*Usar WhatsApp Web.*", re.I),
    re.compile(r".*Continue to chat.*", re.I),
    re.compile(r".*Continuar.*", re.I),
    re.compile(r".*Message.*", re.I),
    re.compile(r".*Enviar mensaje.*", re.I),
    re.compile(r".*Abrir chat.*", re.I),
]


def find_search_box(driver, timeout=5) -> WebElement:
    wait = WebDriverWait(driver, timeout)
    xpaths = [
        "//div[@contenteditable='true' and (contains(@aria-label,'Search') or contains(@aria-label,'Buscar') or contains(@title,'Search') or contains(@title,'Buscar'))]",
        "//input[contains(@placeholder,'Search') or contains(@placeholder,'Buscar')]",
        "//div[@contenteditable='true' and @data-tab and not(ancestor::footer)]"
    ]
    for xp in xpaths:
        try:
            el = wait.until(lambda d: d.find_element(By.XPATH, xp))
            if el and el.is_displayed():
                return el
        except Exception:
            continue
    try:
        candidates = driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true']")
        for c in candidates:
            try:
                if not c.is_displayed():
                    continue
                ancestor_footer = None
                try:
                    ancestor_footer = c.find_element(By.XPATH, "ancestor::footer")
                except Exception:
                    ancestor_footer = None
                if ancestor_footer:
                    continue
                return c
            except Exception:
                continue
    except Exception:
        pass
    raise RuntimeError("No se pudo localizar el input de búsqueda de chats.")


def clear_and_type(element: WebElement, text: str):
    try:
        element.click()
    except Exception:
        pass
    try:
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.DELETE)
    except Exception:
        element.send_keys(Keys.BACKSPACE * 10)
    time.sleep(0.1)
    element.send_keys(text)
    time.sleep(0.2)


def wait_for_chat_panel(driver, timeout=15) -> Optional[WebElement]:
    wait = WebDriverWait(driver, timeout)
    try:
        footer_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "footer div[contenteditable='true']")))
        if footer_input:
            return footer_input
    except Exception:
        pass
    possible_selectors = [
        "div[id='main']",
        "div[data-testid='conversation-panel']",
        "div[role='region']"
    ]
    for sel in possible_selectors:
        try:
            el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
            if el:
                return el
        except Exception:
            continue
    return None


def _wait_for_panel_after_click(driver, max_wait=10) -> Optional[WebElement]:
    """
    Espera de forma incremental a que el panel del chat (footer input o contenedor) esté disponible.
    Esto evita problemas donde el DOM se re-renderiza justo tras el click.
    """
    end_ts = time.time() + max_wait
    while time.time() < end_ts:
        panel = wait_for_chat_panel(driver, timeout=1)
        if panel:
            # tratar de comprobar si está visible / interactuable
            try:
                if panel.is_displayed():
                    return panel
            except StaleElementReferenceException:
                # reintentar si stale
                pass
        time.sleep(0.25)
    return None


def open_chat_by_name(driver, name: str, wait_time=10) -> Optional[WebElement]:
    logging.info(f"Intentando abrir chat por nombre: {name}")
    try:
        search = find_search_box(driver, timeout=5)
        clear_and_type(search, name)
        wait = WebDriverWait(driver, wait_time)
        grid = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='grid']")))

        def any_row_matches(d):
            rows = grid.find_elements(By.CSS_SELECTOR, "div[role='row']")
            for r in rows:
                nm = extract_name_from_row(r)
                if nm and name.lower() in nm.lower():
                    # Intentar click robusto
                    try:
                        r.click()
                        logging.info(f"Se hizo clic en la fila del chat: {nm}")
                        return True
                    except ElementClickInterceptedException:
                        logging.debug("Click interceptado, intentando click en hijo...")
                        try:
                            child = r.find_element(By.CSS_SELECTOR, "div")
                            child.click()
                            logging.info(f"Se hizo clic en el hijo de la fila: {nm}")
                            return True
                        except Exception:
                            logging.debug("No se pudo clickear la fila encontrada.")
                            continue
                    except StaleElementReferenceException:
                        logging.debug("Fila stale al clickear; continuando búsqueda.")
                        continue
                    except Exception as e:
                        logging.debug(f"Error al clickear fila: {e}")
                        continue
            return False

        found = wait.until(any_row_matches)
        if not found:
            logging.info("No se encontraron filas que coincidan con el nombre buscado.")
            return None

        # Esperar el panel de chat de forma robusta y devolverlo
        panel = _wait_for_panel_after_click(driver, max_wait=wait_time)
        if panel:
            logging.info("Panel del chat detectado y devuelto.")
        else:
            logging.info("No se detectó el panel del chat tras el click.")
        return panel
    except Exception as e:
        logging.exception(f"Error abriendo chat por nombre: {e}")
        return None


def normalize_phone_number(number: str) -> str:
    digits = re.sub(r"\D", "", number or "")
    return digits


def open_chat_by_phone(driver, phone: str, wait_time=20) -> Optional[WebElement]:
    logging.info(f"Intentando abrir chat por teléfono: {phone}")
    phone_digits = normalize_phone_number(phone)
    if not phone_digits or len(phone_digits) < 7:
        logging.warning("Número inválido o demasiado corto después de normalizar.")
        return None
    url = f"https://web.whatsapp.com/send?phone={phone_digits}&text=&app_absent=0"
    try:
        driver.get(url)
        # Espera robusta para panel tras la navegación
        panel = _wait_for_panel_after_click(driver, max_wait=wait_time)
        if panel:
            logging.info("Chat cargado (se detectó el input de mensajes o panel).")
            return panel
        # Si no apareció, intentar cerrar overlays si existen
        buttons = driver.find_elements(By.XPATH, "//button")
        for b in buttons:
            try:
                txt = (b.text or "").strip()
                for pat in BUTTON_USE_WHATSAPP_PATTERNS:
                    if txt and pat.match(txt):
                        try:
                            b.click()
                            logging.info("Se clickeó botón para continuar en WhatsApp Web.")
                            time.sleep(1)
                            panel = _wait_for_panel_after_click(driver, max_wait=5)
                            if panel:
                                return panel
                        except Exception:
                            continue
            except Exception:
                continue
    except Exception as e:
        logging.exception(f"Error abriendo chat por teléfono: {e}")
    return None


def open_chat(driver, identifier: str, wait_time=15) -> Optional[WebElement]:
    if not identifier:
        return None
    digits = re.sub(r"\D", "", identifier)
    letters = re.sub(r"[^A-Za-zÁÉÍÓÚáéíóúñÑüÜ]", "", identifier)
    if len(digits) >= max(6, len(letters)):
        return open_chat_by_phone(driver, identifier, wait_time=wait_time)
    else:
        return open_chat_by_name(driver, identifier, wait_time=wait_time)


def send_message(driver, panel_or_footer: Optional[WebElement], text: str, press_enter: bool = True) -> bool:
    try:
        input_el = None
        # Si el panel provisto es el propio input contenteditable:
        if panel_or_footer is not None:
            try:
                ce = panel_or_footer.get_attribute("contenteditable")
                if ce and ce.lower() == "true":
                    input_el = panel_or_footer
            except StaleElementReferenceException:
                input_el = None
            except Exception:
                input_el = None
        # Si no, tratar de encontrar un contenteditable dentro del panel
        if input_el is None and panel_or_footer is not None:
            try:
                input_el = panel_or_footer.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
            except StaleElementReferenceException:
                input_el = None
            except Exception:
                input_el = None
        # Fallback global: buscar footer input
        if input_el is None:
            try:
                input_el = driver.find_element(By.CSS_SELECTOR, "footer div[contenteditable='true']")
            except StaleElementReferenceException:
                input_el = None
            except Exception:
                input_el = None
        # Si aún no encontramos input, intentar una búsqueda adicional rápida
        if input_el is None:
            try:
                candidates = driver.find_elements(By.CSS_SELECTOR, "footer [contenteditable='true'], div[contenteditable='true']")
                for c in candidates:
                    try:
                        if c.is_displayed():
                            input_el = c
                            break
                    except StaleElementReferenceException:
                        continue
            except Exception:
                pass

        if input_el is None:
            logging.warning("No se pudo localizar el input de mensajes para enviar texto.")
            return False

        # Si el elemento está stale justo antes de usarlo, re-localizar
        try:
            _ = input_el.is_enabled()
        except StaleElementReferenceException:
            logging.debug("input_el stale antes de usarlo; re-localizando globalmente")
            try:
                input_el = driver.find_element(By.CSS_SELECTOR, "footer div[contenteditable='true']")
            except Exception:
                input_el = None
            if input_el is None:
                logging.warning("No se pudo re-localizar el input tras StaleElement.")
                return False

        # Intentar método "natural" con send_keys
        try:
            input_el.click()
            lines = text.splitlines() or [text]
            for i, line in enumerate(lines):
                input_el.send_keys(line)
                if i < len(lines) - 1:
                    input_el.send_keys(Keys.SHIFT + Keys.ENTER)
            if press_enter:
                input_el.send_keys(Keys.ENTER)
            logging.info("Mensaje enviado usando send_keys.")
            return True
        except (StaleElementReferenceException, Exception) as e:
            logging.debug(f"send_keys falló: {e}. Intentando fallback JS...")

        # Fallback JS: set innerHTML con <br> por saltos de línea y despachar evento input
        try:
            safe_html = text.replace("\n", "<br>")
            js = (
                "arguments[0].focus();"
                "arguments[0].innerHTML = arguments[1];"
                "var ev = document.createEvent('HTMLEvents');"
                "ev.initEvent('input', true, false);"
                "arguments[0].dispatchEvent(ev);"
            )
            driver.execute_script(js, input_el, safe_html)
            time.sleep(0.1)
            if press_enter:
                input_el.send_keys(Keys.ENTER)
            logging.info("Mensaje enviado usando fallback JS.")
            return True
        except Exception as e:
            logging.exception(f"Fallback JS para enviar mensaje falló: {e}")
            return False

    except Exception as e:
        logging.exception(f"send_message excepción inesperada: {e}")
        return False


# ---------------------- Integración con whatsapp_features ---------------------- #
WF_MODULE = load_module_from_path("whatsapp_features", ROOT / "whatsapp_features.py")


# ---------------------- Interfaz interactiva ---------------------- #
def prompt_multiline_message() -> str:
    print("Escribe el mensaje. Para terminar, deja una línea vacía y presiona ENTER:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


def interactive_menu(driver: webdriver.Chrome):
    whatsapp_open = False
    while True:
        print("\n--- Menú WhatsApp Selenium ---")
        print("1) Ir a WhatsApp Web (abrir URL / esperar sesión)")
        print("2) Ver nombre del último chat con mensajes sin leer")
        print("3) Buscar y abrir chat por NOMBRE")
        print("4) Buscar y abrir chat por NÚMERO")
        print("5) Enviar mensaje (a nombre o número; podrás tipear el mensaje)")
        print("6) Enviar archivo adjunto (con caption opcional)")
        print("7) Leer últimos N mensajes del chat abierto")
        print("8) Leer solo mensajes del CONTACTO (filtrar propios)")
        print("9) Salir")
        choice = input("Elige una opción (1-9): ").strip()
        if choice == "1":
            print("Abriendo https://web.whatsapp.com/ ...")
            driver.get("https://web.whatsapp.com/")
            print("Esperando lista de chats (si es la primera vez, escanea el QR)...")
            try:
                wait_for_chat_grid(driver, timeout=60)
                whatsapp_open = True
                print("WhatsApp Web cargado.")
            except Exception:
                print("No se detectó la lista de chats en el tiempo esperado. Asegúrate de haber iniciado sesión.")
        elif choice == "2":
            if not whatsapp_open:
                print("Primero abre WhatsApp Web (opción 1).")
                continue
            try:
                unread = find_unread_chats(driver, max_scrolls=6, wait_between_scrolls=1.0, timeout_grid=20)
                if unread:
                    print("Último(s) chat(s) con no leídos (lista):", unread)
                    print("Primer chat sin leer:", unread[0])
                else:
                    print("No hay chats con mensajes sin leer (detectados).")
            except Exception as e:
                print("Error buscando chats sin leer:", e)
        elif choice == "3":
            if not whatsapp_open:
                print("Primero abre WhatsApp Web (opción 1).")
                continue
            name = input("Escribe el nombre (o parte del nombre) a buscar: ").strip()
            if not name:
                print("Nombre vacío. Abortando.")
                continue
            panel = open_chat(driver, name)
            if panel:
                print(f"Chat '{name}' abierto correctamente.")
            else:
                print(f"No se pudo abrir el chat con nombre '{name}'.")
        elif choice == "4":
            if not whatsapp_open:
                print("Primero abre WhatsApp Web (opción 1).")
                continue
            number = input("Escribe el número (incluye código de país, ej: +521... o 521...): ").strip()
            if not number:
                print("Número vacío. Abortando.")
                continue
            panel = open_chat(driver, number)
            if panel:
                print(f"Chat del número '{number}' abierto correctamente.")
            else:
                print(f"No se pudo abrir el chat para el número '{number}'.")
        elif choice == "5":
            if not whatsapp_open:
                print("Primero abre WhatsApp Web (opción 1).")
                continue
            identifier = input("A qué (nombre o número) quieres enviar el mensaje?: ").strip()
            if not identifier:
                print("Identificador vacío. Abortando.")
                continue
            print("Ahora escribe el mensaje (soporta varias líneas):")
            message = prompt_multiline_message()
            if not message:
                print("Mensaje vacío. Abortando.")
                continue
            print("Abriendo chat...")
            panel = open_chat(driver, identifier)
            if not panel:
                print("No se pudo abrir el chat. Abortando envío.")
                continue
            ok = send_message(driver, panel, message, press_enter=True)
            print("Resultado envío:", "OK" if ok else "FALLÓ")
        elif choice == "6":
            if not whatsapp_open:
                print("Primero abre WhatsApp Web (opción 1).")
                continue
            if WF_MODULE is None:
                print("No está disponible whatsapp_features.py")
                continue
            
            identifier = input("¿A quién enviar el archivo? (nombre o número): ").strip()
            if not identifier:
                print("Identificador vacío. Abortando.")
                continue
            
            file_path = input("Ruta completa del archivo a enviar: ").strip()
            if not file_path:
                print("Ruta vacía. Abortando.")
                continue
            
            caption = input("Caption opcional (Enter para omitir): ").strip()
            
            print("Abriendo chat...")
            panel = open_chat(driver, identifier)
            if not panel:
                print("No se pudo abrir el chat. Abortando envío.")
                continue
            
            ok = WF_MODULE.send_file(driver, file_path, caption)
            print("Resultado envío:", "✅ ENVIADO" if ok else "❌ FALLÓ")
        
        elif choice == "7":
            if not whatsapp_open:
                print("Primero abre WhatsApp Web (opción 1).")
                continue
            if WF_MODULE is None:
                print("No está disponible whatsapp_features.py. Cópialo en test/whatsapp_features.py")
                continue
            try:
                n = input("¿Cuántos mensajes quieres leer? (por defecto 10): ").strip()
                n = int(n) if n else 10
                msgs = WF_MODULE.read_last_messages(driver, n=n)
                if not msgs:
                    print("No se encontraron mensajes o no está cargado el panel de conversación.")
                else:
                    print(f"\n📋 Últimos {len(msgs)} mensajes:\n")
                    for i, m in enumerate(msgs, 1):
                        direction_icon = "📤" if m.get('is_mine') else "📥"
                        type_icon = {
                            "text": "💬",
                            "audio": "🎤",
                            "image": "🖼️",
                            "video": "🎥",
                            "document": "📄"
                        }.get(m.get('type'), "❓")
                        
                        sender = m.get('sender', 'Desconocido')
                        print(f"{direction_icon} {type_icon} Mensaje {i} [{sender}]")
                        print(f"   Tipo: {m.get('type')}")
                        print(f"   Dirección: {m.get('direction')}")
                        print(f"   Es mío: {m.get('is_mine')}")
                        
                        texto = m.get('text', '')
                        if texto and len(texto) > 100:
                            texto = texto[:100] + "..."
                        print(f"   Texto: {texto}")
                        print()
            except Exception as e:
                logging.exception("Error leyendo historial:")
                print("Error:", e)
        
        elif choice == "8":
            if not whatsapp_open:
                print("Primero abre WhatsApp Web (opción 1).")
                continue
            if WF_MODULE is None:
                print("No está disponible whatsapp_features.py")
                continue
            try:
                n = input("¿Cuántos mensajes quieres leer? (por defecto 10): ").strip()
                n = int(n) if n else 10
                msgs = WF_MODULE.read_last_messages(driver, n=n)
                
                # Filtrar solo mensajes del contacto
                their_msgs = WF_MODULE.filter_only_their_messages(msgs)
                
                if not their_msgs:
                    print("No se encontraron mensajes del contacto.")
                else:
                    print(f"\n📥 Últimos {len(their_msgs)} mensajes DEL CONTACTO:\n")
                    for i, m in enumerate(their_msgs, 1):
                        type_icon = {
                            "text": "💬",
                            "audio": "🎤",
                            "image": "🖼️",
                            "video": "🎥",
                            "document": "📄"
                        }.get(m.get('type'), "❓")
                        
                        print(f"📥 {type_icon} Mensaje {i}")
                        print(f"   Tipo: {m.get('type')}")
                        
                        texto = m.get('text', '')
                        if texto and len(texto) > 100:
                            texto = texto[:100] + "..."
                        print(f"   Texto: {texto}")
                        print()
            except Exception as e:
                logging.exception("Error leyendo mensajes:")
                print("Error:", e)
        
        elif choice == "9":
            confirm = input("¿Cerrar navegador y salir? (s/N): ").strip().lower()
            if confirm == "s" or confirm == "si":
                try:
                    driver.quit()
                except Exception:
                    pass
            print("Saliendo.")
            break
        else:
            print("Opción no válida. Intenta de nuevo.")


def main():
    driver = None
    try:
        ensure_profile_dir(PROFILE_DIR)
        logging.info("Creando Chrome con perfil exclusivo para Selenium (se abrirá la ventana)...")
        driver = create_driver(PROFILE_DIR, headless=False)
        interactive_menu(driver)
    except Exception as e:
        logging.exception("Ocurrió un error en la ejecución:")
        if driver:
            save = input("Ocurrió un error. ¿Quieres guardar screenshot antes de salir? (s/N): ").strip().lower()
            if save in ("s", "si"):
                try:
                    path = Path.cwd() / "whatsapp_error.png"
                    driver.save_screenshot(str(path))
                    print("Screenshot guardado en:", path)
                except Exception:
                    print("No se pudo guardar screenshot.")
    finally:
        pass


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Versión más robusta para detectar el primer (o todos) chats con mensajes sin leer
en WhatsApp Web usando Selenium + Chrome profile.

Se agregó funcionalidad para:
 - abrir un chat por nombre de contacto (buscándolo en la lista)
 - abrir un chat por número de teléfono (usando la URL de send)
 - heurísticas multilenguaje para buscar el input de búsqueda y el input de mensajes
 - enviar mensajes (función send_message)

Notas:
 - Para abrir por número inevitablemente necesitas el número con código de país
   (ej: 521XXXXXXXXXX para México). La función hará un "normalize" básico,
   pero no puede adivinar el código de país.
 - El comportamiento de WhatsApp Web cambia con frecuencia (atributos data-tab,
   labels, estructura DOM). Las heurísticas aquí intentan ser robustas, pero
   podrían necesitar ajustes si WhatsApp cambia su DOM.
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
from typing import Optional
import time
import sys
import os
import re
import logging
from dotenv import load_dotenv

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


def ensure_profile_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Directorio de perfil creado en: {path}")
    else:
        logging.info(f"Usando directorio de perfil existente: {path}")


def create_driver(profile_path: Path, headless=False) -> webdriver.Chrome:
    opciones = Options()
    opciones.add_argument(f"--user-data-dir={profile_path}")
    opciones.add_argument("--no-first-run")
    opciones.add_argument("--no-default-browser-check")
    opciones.add_argument("--disable-extensions")
    opciones.add_argument("--disable-popup-blocking")
    opciones.add_experimental_option("excludeSwitches", ["enable-automation"])
    opciones.add_experimental_option("detach", True)
    if headless:
        # Headless puede romper QR/UX; usar solo si sabes lo que haces
        opciones.add_argument("--headless=new")
        opciones.add_argument("--disable-gpu")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opciones)


def wait_for_chat_grid(driver, timeout=30):
    """
    Espera y devuelve el elemento contenedor de chats (grid).
    Si no lo encuentra lanza TimeoutException.
    """
    wait = WebDriverWait(driver, timeout)
    grid = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='grid']")))
    return grid


def get_chat_rows_from_grid(grid):
    # Devolver filas visibles dentro del grid
    return grid.find_elements(By.CSS_SELECTOR, "div[role='row']")


# patrón para detectar "no leídos" en diferentes idiomas y variantes
# He ampliado expresiones en español e inglés y variantes comunes
UNREAD_RE = re.compile(
    r"("
    r"(no\s*le[ií]d[oa]s?)|"               # no leídos / no leido
    r"(sin\s+leer)|"                       # sin leer
    r"(mensajes?\s+sin\s+leer)|"           # mensajes sin leer
    r"(mensaje?s?\s+nuevo?s?)|"            # mensaje nuevo / mensajes nuevos
    r"(nuev[oa]s?\s+mensajes?)|"           # nuevos mensajes
    r"(unread)|(unread\s+message)"
    r")",
    re.I
)


def row_has_unread_indicator(row) -> bool:
    """
    Heurística para decidir si una fila tiene mensajes sin leer:
     - aria-label de la fila contiene palabras clave
     - existen badges dentro de la fila que contienen un número (p. ej. "2")
     - aria-label del badge contiene palabras clave
    """
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
    """
    Extrae el nombre del chat con varios intentos:
     - aria-label de la fila (antes de la coma suele venir el nombre)
     - span con title
     - texto visible dentro del row
    """
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
    """
    Busca chats con mensajes sin leer.
    Recorre las filas visibles; si no encuentra hace scroll en el grid para cargar más.
    Devuelve lista de nombres (puede estar vacía).
    """
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


def save_screenshot_on_error(driver, name="error_screenshot.png"):
    try:
        path = Path.cwd() / name
        driver.save_screenshot(str(path))
        logging.info(f"Screenshot guardado en: {path}")
    except Exception as e:
        logging.warning(f"No se pudo guardar screenshot: {e}")


# -------------------- Nuevas funciones: abrir chat por nombre o número -------------------- #

# He ampliado palabras clave de búsqueda/placeholder/aria-label para español y más idiomas
SEARCH_ARIA_KEYWORDS = [
    "Search", "Buscar", "Buscar o iniciar", "Search or start", "Suchen", "Chercher",
    "Buscar o iniciar un chat", "Buscar o comenzar", "Buscar o crear chat", "Buscar o iniciar chat",
    "Buscar chats"
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
    """
    Intentos heurísticos para localizar el input de búsqueda de la lista de chats.
    Devuelve el elemento contenteditable (div) para escribir la búsqueda.
    """
    wait = WebDriverWait(driver, timeout)
    # Intentos con XPaths que buscan aria-labels/titles que contengan 'Search' / 'Buscar'
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

    # Fallback: buscar el primer div contenteditable visible que esté fuera del footer (probablemente search)
    try:
        candidates = driver.find_elements(By.CSS_SELECTOR, "div[contenteditable='true']")
        for c in candidates:
            try:
                if not c.is_displayed():
                    continue
                # si está dentro de footer es input de mensajes -> saltarlo
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
    """
    Limpia un contenteditable o input y escribe el texto.
    """
    try:
        element.click()
    except Exception:
        pass
    # Seleccionar todo y borrar (CTRL+A DELETE funciona en la mayoría de contenteditable)
    try:
        element.send_keys(Keys.CONTROL + "a")
        element.send_keys(Keys.DELETE)
    except Exception:
        # fallback: enviar varias teclas de backspace
        element.send_keys(Keys.BACKSPACE * 10)
    time.sleep(0.1)
    element.send_keys(text)
    time.sleep(0.2)


def wait_for_chat_panel(driver, timeout=15) -> Optional[WebElement]:
    """
    Esperar hasta que se cargue el panel de conversación. Devuelve preferiblemente
    el footer/input de mensajes (contenteditable) o el contenedor principal del chat.
    """
    wait = WebDriverWait(driver, timeout)
    try:
        # preferimos detectar el input del footer (para poder enviar mensajes)
        footer_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "footer div[contenteditable='true']")))
        if footer_input:
            return footer_input
    except Exception:
        pass

    # Fallback: intentar detectar el contenedor principal de la conversación
    possible_selectors = [
        "div[id='main']",
        "div[data-testid='conversation-panel']",
        "div[role='region']"  # menos fiable
    ]
    for sel in possible_selectors:
        try:
            el = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
            if el:
                return el
        except Exception:
            continue

    return None


def open_chat_by_name(driver, name: str, wait_time=10) -> Optional[WebElement]:
    """
    Busca en la barra de búsqueda y abre el primer chat cuyo nombre contenga la cadena.
    Devuelve el WebElement del panel cargado (footer/input o contenedor) o None si falla.
    """
    logging.info(f"Intentando abrir chat por nombre: {name}")
    try:
        search = find_search_box(driver, timeout=5)
        clear_and_type(search, name)

        # Esperar que la lista de resultados se actualice: debe aparecer al menos una fila en el grid
        wait = WebDriverWait(driver, wait_time)
        grid = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='grid']")))

        def any_row_matches(d):
            rows = grid.find_elements(By.CSS_SELECTOR, "div[role='row']")
            for r in rows:
                nm = extract_name_from_row(r)
                if nm and name.lower() in nm.lower():
                    # click en el elemento visible que representa el chat
                    try:
                        r.click()
                        logging.info(f"Se hizo clic en la fila del chat: {nm}")
                        return True
                    except Exception:
                        try:
                            child = r.find_element(By.CSS_SELECTOR, "div")
                            child.click()
                            logging.info(f"Se hizo clic en el hijo de la fila: {nm}")
                            return True
                        except Exception:
                            logging.debug("No se pudo clickear la fila encontrada.")
                            continue
            return False

        found = wait.until(any_row_matches)
        if not found:
            logging.info("No se encontraron filas que coincidan con el nombre buscado.")
            return None

        # esperar el panel del chat cargado y devolver el elemento (footer/input preferido)
        panel = wait_for_chat_panel(driver, timeout=wait_time)
        if panel:
            logging.info("Panel del chat detectado y devuelto.")
        else:
            logging.info("No se detectó el panel del chat tras el click.")
        # limpiar búsqueda (opcional)
        try:
            search.send_keys(Keys.ESCAPE)
        except Exception:
            pass
        return panel
    except Exception as e:
        logging.exception(f"Error abriendo chat por nombre: {e}")
        return None


def normalize_phone_number(number: str) -> str:
    """Quita todo lo que no sean dígitos y devuelve la cadena."""
    digits = re.sub(r"\D", "", number or "")
    return digits


def open_chat_by_phone(driver, phone: str, wait_time=20) -> Optional[WebElement]:
    """
    Abre un chat usando la URL de send de WhatsApp Web.
    phone debe incluir el código de país (p. ej. 521XXXXXXXXXX). La función
    normaliza quitando espacios, signos, paréntesis y +.

    Devuelve el WebElement del panel cargado (footer/input preferido) o None si falla.
    """
    logging.info(f"Intentando abrir chat por teléfono: {phone}")
    phone_digits = normalize_phone_number(phone)
    if not phone_digits or len(phone_digits) < 7:
        logging.warning("Número inválido o demasiado corto después de normalizar.")
        return None

    url = f"https://web.whatsapp.com/send?phone={phone_digits}&text=&app_absent=0"
    try:
        driver.get(url)
        wait = WebDriverWait(driver, wait_time)
        time.sleep(1)
        # Intento de detectar el panel
        panel = wait_for_chat_panel(driver, timeout=wait_time)
        if panel:
            logging.info("Chat cargado (se detectó el input de mensajes o panel).")
            return panel

        # Si hay overlays/diálogos, intentar buscar botones que permitan continuar
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
                            panel = wait_for_chat_panel(driver, timeout=5)
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
    """
    Determina si identifier es número (abre por phone) o nombre (abre por search) y
    realiza la apertura. Devuelve el WebElement del panel abierto o None.
    """
    if not identifier:
        return None
    digits = re.sub(r"\D", "", identifier)
    letters = re.sub(r"[^A-Za-zÁÉÍÓÚáéíóúñÑüÜ]", "", identifier)
    if len(digits) >= max(6, len(letters)):
        return open_chat_by_phone(driver, identifier, wait_time=wait_time)
    else:
        return open_chat_by_name(driver, identifier, wait_time=wait_time)


# -------------------- NUEVA FUNCIÓN: ENVIAR MENSAJE -------------------- #

def send_message(driver, panel_or_footer: Optional[WebElement], text: str, press_enter: bool = True) -> bool:
    """
    Envía `text` al chat actualmente abierto.
    - panel_or_footer: elemento devuelto por open_chat (puede ser el footer/input o el contenedor del chat).
      Si es None, la función intentará localizar el input del footer globalmente.
    - press_enter: si True, enviará el mensaje presionando Enter al final.
    Retorna True si parece haberse enviado o False en caso de error.
    Notas:
    - Para nuevas líneas se usa SHIFT+ENTER (intento automático).
    - Si enviar por send_keys falla, se intenta un fallback por JS para insertar HTML y luego
      simular el envío con ENTER.
    """
    try:
        input_el = None

        # Si el elemento provisto es el propio input contenteditable:
        if panel_or_footer is not None:
            try:
                ce = panel_or_footer.get_attribute("contenteditable")
                if ce and ce.lower() == "true":
                    input_el = panel_or_footer
            except Exception:
                input_el = None

        # Si no, tratar de encontrar un contenteditable dentro del panel
        if input_el is None and panel_or_footer is not None:
            try:
                input_el = panel_or_footer.find_element(By.CSS_SELECTOR, "div[contenteditable='true']")
            except Exception:
                input_el = None

        # Fallback global: buscar footer input
        if input_el is None:
            try:
                input_el = driver.find_element(By.CSS_SELECTOR, "footer div[contenteditable='true']")
            except Exception:
                input_el = None

        if input_el is None:
            logging.warning("No se pudo localizar el input de mensajes para enviar texto.")
            return False

        # Intentar método "natural" con send_keys
        try:
            input_el.click()
            # Limpiar antes si hay texto (opcional)
            try:
                input_el.send_keys(Keys.CONTROL + "a")
                input_el.send_keys(Keys.DELETE)
            except Exception:
                pass

            # Mandar líneas respetando saltos con SHIFT+ENTER
            lines = text.splitlines() or [text]
            for i, line in enumerate(lines):
                input_el.send_keys(line)
                if i < len(lines) - 1:
                    # SHIFT+ENTER para nueva línea
                    input_el.send_keys(Keys.SHIFT + Keys.ENTER)
            if press_enter:
                input_el.send_keys(Keys.ENTER)
            logging.info("Mensaje enviado usando send_keys.")
            return True
        except Exception as e:
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


# ----------------------------------------------------------------------------------------- #


def main():
    driver = None
    try:
        ensure_profile_dir(PROFILE_DIR)
        logging.info("Abriendo Chrome con perfil exclusivo para Selenium...")
        driver = create_driver(PROFILE_DIR, headless=False)
        driver.get("https://web.whatsapp.com/")

        logging.info("Esperando a que cargue la lista de chats (puede requerir escanear QR en primer uso)...")
        # esperar hasta 60s a que aparezca el grid; si ya hay sesión, será rápido
        unread = find_unread_chats(driver, max_scrolls=8, wait_between_scrolls=1.2, timeout_grid=60)
        if unread:
            logging.info(f"Chats con mensajes sin leer (encontrados): {unread}")
            print("Primer chat con no leídos:", unread[0])
        else:
            logging.info("No se detectaron chats con mensajes sin leer.")
            print("No hay chats con mensajes sin leer.")

        # ejemplo: abrir por nombre y enviar mensaje
        ejemplo_nombre = "Dani SIM Telcel"
        panel_by_name = open_chat(driver, ejemplo_nombre)
        logging.info(f"Abrir por nombre ('{ejemplo_nombre}') resultado: {'OK' if panel_by_name else 'NO'}")
        if panel_by_name:
            ok = send_message(driver, panel_by_name, "Hola desde Selenium.\nPrueba de envío.", press_enter=True)
            logging.info(f"Enviar mensaje a '{ejemplo_nombre}': {'OK' if ok else 'NO'}")

        # ejemplo: abrir por número (asegúrate de incluir código de país; puede incluir '+') y enviar
        ejemplo_numero = "+525643715364"
        panel_by_phone = open_chat(driver, ejemplo_numero)
        logging.info(f"Abrir por teléfono ('{ejemplo_numero}') resultado: {'OK' if panel_by_phone else 'NO'}")
        if panel_by_phone:
            ok2 = send_message(driver, panel_by_phone, "Mensaje automático por número.", press_enter=True)
            logging.info(f"Enviar mensaje a '{ejemplo_numero}': {'OK' if ok2 else 'NO'}")

        # también mostrar el primer chat (más reciente)
        try:
            grid = wait_for_chat_grid(driver, timeout=10)
            rows = get_chat_rows_from_grid(grid)
            if rows:
                first_name = extract_name_from_row(rows[0])
                if first_name:
                    print("Primer chat (más reciente):", first_name)
        except Exception:
            logging.debug("No se pudo determinar el primer chat.")
        # Mantener navegador abierto unos segundos para inspección manual si es necesario
        time.sleep(3)
    except Exception as e:
        logging.exception("Ocurrió un error al ejecutar el script:")
        if driver:
            save_screenshot_on_error(driver, name="whatsapp_error.png")
    finally:
        # NO cerramos el navegador automáticamente si quieres inspección.
        # Descomenta la siguiente línea para cerrar el navegador siempre.
        # if driver:
        #     driver.quit()
        pass


if __name__ == "__main__":
    main()
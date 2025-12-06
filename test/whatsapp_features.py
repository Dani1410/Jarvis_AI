#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funciones auxiliares para WhatsApp Web:
 - read_last_messages(driver, n): obtener últimos n mensajes (texto, imagen, audio)
 - download_voice_from_message(driver, message_element): intento por blob/currentSrc/agresivo
 - download_voice_via_context_menu(driver, message_element): abre menú y pulsa "Descargar"
 - convert_ogg_to_wav(ogg_path)
"""
from pathlib import Path
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import base64
import time
import re
import os
import logging
from typing import List, Dict, Optional

# pydub (opcional)
try:
    from pydub import AudioSegment
except Exception:
    AudioSegment = None

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_PRE_PLAIN_RE = re.compile(r"^\[?(?P<time>[^]]+)\]?\s*(?P<sender>[^:]+):\s*")

def parse_pre_plain_text(s: Optional[str]) -> Dict[str, Optional[str]]:
    if not s:
        return {"timestamp": None, "sender": None}
    m = _PRE_PLAIN_RE.match(s.strip())
    if m:
        return {"timestamp": m.group("time").strip(), "sender": m.group("sender").strip()}
    return {"timestamp": None, "sender": s.strip()}


def _debug_outer_html(el: WebElement, max_len: int = 4000) -> str:
    try:
        html = el.get_attribute("outerHTML") or ""
        return (html[:max_len] + "... (trunc)" ) if len(html) > max_len else html
    except Exception as e:
        return f"<no outerHTML: {e}>"


def _find_audio_element_in_container(driver, msg_container: WebElement) -> Optional[WebElement]:
    # 1) <audio>
    try:
        aud = msg_container.find_element(By.XPATH, ".//audio")
        if aud:
            return aud
    except Exception:
        pass
    # 2) data-testid heuristics
    try:
        aud_candidates = msg_container.find_elements(
            By.XPATH,
            ".//*[contains(@data-testid,'audio') or contains(@data-testid,'voice') or contains(@data-testid,'audio_playback') or contains(@data-testid,'playback')]"
        )
        if aud_candidates:
            return aud_candidates[0]
    except Exception:
        pass
    # 3) play buttons (aria-label)
    try:
        btns = msg_container.find_elements(
            By.XPATH,
            ".//button[contains(@aria-label,'Play') or contains(@aria-label,'Reproducir') or contains(@aria-label,'Reproducir mensaje') or contains(@aria-label,'play')]"
        )
        if btns:
            return btns[0]
    except Exception:
        pass
    # 4) SVG icon heuristics
    try:
        icons = msg_container.find_elements(
            By.XPATH,
            ".//*[name()='svg' and (contains(@outerHTML,'microphone') or contains(@outerHTML,'wave') or contains(@outerHTML,'play') or contains(@outerHTML,'audio-play'))]"
        )
        if icons:
            return icons[0]
    except Exception:
        pass
    return None


def _extract_audio_src_from_element(driver, candidate_el: WebElement, msg_container: WebElement) -> Optional[str]:
    try:
        tag = (candidate_el.tag_name or "").lower()
    except Exception:
        tag = ""
    # if audio tag
    try:
        if tag == "audio":
            src = candidate_el.get_attribute("src") or candidate_el.get_attribute("currentSrc")
            if src:
                return src
    except Exception:
        pass
    # attribute src
    try:
        src = candidate_el.get_attribute("src")
        if src:
            return src
    except Exception:
        pass
    # audio inside candidate
    try:
        aud = candidate_el.find_element(By.XPATH, ".//audio")
        if aud:
            src = aud.get_attribute("src") or aud.get_attribute("currentSrc")
            if src:
                return src
    except Exception:
        pass
    # data-* attrs
    try:
        attrs = ["data-src", "data-audio", "data-url", "data-download", "href"]
        for a in attrs:
            try:
                v = candidate_el.get_attribute(a)
                if v:
                    return v
            except Exception:
                continue
    except Exception:
        pass
    # JS fallback look for audio
    try:
        js_get_current = "var el = arguments[0].querySelector('audio'); return el ? el.currentSrc || el.src : null;"
        src = driver.execute_script(js_get_current, msg_container)
        if src:
            return src
    except Exception:
        pass
    try:
        src = driver.execute_script(
            "var aud = arguments[0].querySelectorAll('audio');"
            "for (var i=0;i<aud.length;i++){ if (aud[i].currentSrc) return aud[i].currentSrc; if (aud[i].src) return aud[i].src; }"
            "return null;",
            msg_container
        )
        if src:
            return src
    except Exception:
        pass
    return None


def read_last_messages(driver, n=10):
    """
    Lee los últimos N mensajes del chat actual, detectando texto, audios, imágenes, etc.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time
    
    try:
        # Esperar el contenedor de mensajes con selectores alternativos
        wait = WebDriverWait(driver, 10)
        
        # Intentar varios selectores para el área de conversación
        conversation = None
        selectors = [
            "div[data-testid='conversation-panel-messages']",
            "div.x3psx0u",  # clase común del contenedor de mensajes
            "div[role='row']",  # filas de mensajes
            "div#main",  # panel principal
        ]
        
        for selector in selectors:
            try:
                conversation = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                logging.info(f"Contenedor de conversación encontrado con: {selector}")
                break
            except:
                continue
        
        if not conversation:
            logging.error("No se pudo localizar el contenedor de conversación.")
            return []
        
        # Obtener burbujas de mensajes con múltiples selectores
        message_bubbles = []
        bubble_selectors = [
            "div.message-in, div.message-out",
            "div[data-id*='@']",  # mensajes tienen data-id con @ del número
            "div.focusable-list-item",
        ]
        
        for selector in bubble_selectors:
            try:
                bubbles = conversation.find_elements(By.CSS_SELECTOR, selector)
                if bubbles:
                    message_bubbles = bubbles
                    logging.info(f"Encontradas {len(bubbles)} burbujas con: {selector}")
                    break
            except:
                continue
        
        if not message_bubbles:
            logging.warning("No se encontraron burbujas de mensajes.")
            return []
        
        # Tomar los últimos N
        recent = message_bubbles[-n:] if len(message_bubbles) > n else message_bubbles
        
        messages = []
        for bubble in recent:
            try:
                msg = {
                    "element": bubble,
                    "id": bubble.get_attribute("data-id") or bubble.id or str(hash(bubble)),
                    "direction": "in" if "message-in" in bubble.get_attribute("class") else "out",
                    "type": "text",
                    "text": "",
                    "timestamp": None,
                    "sender": None
                }
                
                # Detectar tipo de mensaje
                # Audio / Nota de voz - buscar múltiples indicadores
                audio_indicators = bubble.find_elements(
                    By.CSS_SELECTOR,
                    (
                        "button[aria-label*='Reproducir'], "
                        "button[aria-label*='Pausar'], "
                        "button[aria-label*='Play'], "
                        "button[aria-label*='Pause'], "
                        "button[aria-label*='mensaje de voz'], "
                        "span[data-icon='audio-play'], "
                        "span[data-icon='audio-pause'], "
                        "span[aria-label*='Mensaje de voz'], "
                        "div[aria-label*='mensaje de voz']"
                    )
                )
                
                if audio_indicators:
                    msg["type"] = "audio"
                    msg["text"] = "[Audio/Nota de voz]"
                    messages.append(msg)
                    continue
                
                # Imagen
                imgs = bubble.find_elements(By.CSS_SELECTOR, "img[src*='blob:'], img[src*='https://']")
                if imgs:
                    msg["type"] = "image"
                    msg["text"] = "[Imagen]"
                    messages.append(msg)
                    continue
                
                # Video
                videos = bubble.find_elements(By.CSS_SELECTOR, "video, span[data-icon='video']")
                if videos:
                    msg["type"] = "video"
                    msg["text"] = "[Video]"
                    messages.append(msg)
                    continue
                
                # Documento
                docs = bubble.find_elements(By.CSS_SELECTOR, "span[data-icon='document'], span[data-icon='audio-file']")
                if docs:
                    msg["type"] = "document"
                    msg["text"] = "[Documento]"
                    messages.append(msg)
                    continue
                
                # Texto normal
                text_spans = bubble.find_elements(By.CSS_SELECTOR, "span.selectable-text span")
                if text_spans:
                    msg["text"] = " ".join([s.text for s in text_spans if s.text])
                else:
                    msg["text"] = bubble.text
                
                messages.append(msg)
                
            except Exception as e:
                logging.debug(f"Error procesando burbuja: {e}")
                continue
        
        return messages
        
    except Exception as e:
        logging.exception(f"Error leyendo mensajes: {e}")
        return []
    
# ----- fetch blob -> base64 helper (used for blobs/URLs) -----
_FETCH_BLOB_AS_BASE64 = """
var src = arguments[0];
var callback = arguments[arguments.length - 1];
if (!src) { callback(null); }
fetch(src).then(function(r){ return r.blob(); })
.then(function(blob){
  var reader = new FileReader();
  reader.onload = function(){ callback(reader.result.split(',')[1]); };
  reader.onerror = function(e){ callback(null); };
  reader.readAsDataURL(blob);
}).catch(function(e){ callback(null); });
"""


def download_voice_from_message(driver, msg_element, download_dir: Path = None):
    """
    Intenta descargar nota de voz reproduciendo primero el audio
    y luego buscando el botón de descarga (3 puntos > Descargar).
    """
    import time
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    if download_dir is None:
        download_dir = Path.cwd() / "downloads"
    download_dir.mkdir(exist_ok=True)
    
    try:
        # 1. Hacer clic en play para que descargue el blob
        play_btn = msg_element.find_element(By.CSS_SELECTOR, "button[aria-label*='Reproducir'], button[aria-label*='Play']")
        play_btn.click()
        time.sleep(2)  # esperar que se cargue
        
        # 2. Buscar menú contextual (3 puntos)
        menu_btn = msg_element.find_element(By.CSS_SELECTOR, "button[aria-label*='Menú'], button[aria-label*='Menu'], span[data-icon='down-context']")
        menu_btn.click()
        time.sleep(0.5)
        
        # 3. Buscar opción "Descargar"
        download_option = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Descargar') or contains(text(), 'Download')]"))
        )
        download_option.click()
        time.sleep(2)
        
        # 4. El archivo se descargó en la carpeta de descargas del navegador
        # Buscar el .opus más reciente
        files = list(download_dir.glob("*.opus")) + list(download_dir.glob("*.ogg"))
        if not files:
            return None
        latest = max(files, key=lambda p: p.stat().st_mtime)
        return str(latest)
        
    except Exception as e:
        logging.exception(f"Error descargando nota de voz: {e}")
        return None

def _wait_for_download_completion(download_dir: Path, timeout: float = 20.0, poll_interval: float = 0.5) -> Optional[Path]:
    start = time.time()
    snapshot = set(download_dir.iterdir()) if download_dir.exists() else set()
    while time.time() - start < timeout:
        current = set(download_dir.iterdir())
        added = current - snapshot
        new_completed = [p for p in added if not p.name.endswith(".crdownload")]
        if new_completed:
            return sorted(new_completed, key=lambda p: p.stat().st_mtime, reverse=True)[0]
        for p in added:
            if p.name.endswith(".crdownload"):
                end_wait = time.time() + (timeout - (time.time() - start))
                while time.time() < end_wait:
                    without = p.parent / p.name.replace(".crdownload","")
                    if without.exists():
                        return without
                    time.sleep(poll_interval)
        time.sleep(poll_interval)
    return None


def download_voice_via_context_menu(driver, message_element: WebElement, download_dir: Optional[str] = None, timeout: float = 25.0) -> Optional[str]:
    if download_dir is None:
        download_dir = Path.cwd() / "downloads"
    download_dir = Path(download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)

    menu_labels = ["Descargar", "Download", "Descargar archivo", "Download file"]

    try:
        # context click
        from selenium.webdriver import ActionChains
        try:
            ActionChains(driver).move_to_element(message_element).context_click(message_element).perform()
        except Exception:
            try:
                driver.execute_script("var ev = new MouseEvent('contextmenu', {bubbles: true, cancelable: true, view: window}); arguments[0].dispatchEvent(ev);", message_element)
            except Exception:
                pass

        menu = None
        wait = WebDriverWait(driver, 6)
        try:
            menu = wait.until(EC.presence_of_element_located((By.XPATH, "//div[@role='menu' or @role='dialog' or contains(@class,'_')][.//text()]")))
        except Exception:
            try:
                menu = wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@style,'position: fixed') and .//button]")))
            except Exception:
                menu = None

        if menu is None:
            logger.warning("No context menu detected")
            return None

        # find item
        item = None
        for lab in menu_labels:
            try:
                item = menu.find_element(By.XPATH, f".//*[contains(normalize-space(.), '{lab}')]")
                if item:
                    break
            except Exception:
                item = None

        if item is None:
            try:
                item = menu.find_element(By.XPATH, ".//*[contains(@data-icon,'download') or contains(@aria-label,'Download') or contains(@aria-label,'Descargar')]")
            except Exception:
                item = None

        if item is None:
            logger.warning("Download item not found in menu; outerHTML: %s", _debug_outer_html(menu, max_len=2000))
            try:
                from selenium.webdriver.common.keys import Keys as _K
                from selenium.webdriver.common.action_chains import ActionChains as _AC
                _AC(driver).send_keys(_K.ESCAPE).perform()
            except Exception:
                pass
            return None

        snapshot = set(download_dir.iterdir()) if download_dir.exists() else set()

        try:
            item.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", item)
            except Exception:
                logger.exception("Could not click download item")
                return None

        file_path = _wait_for_download_completion(download_dir, timeout=timeout)
        if file_path:
            logger.info("Downloaded file detected: %s", file_path)
            return str(file_path)
        else:
            logger.warning("No downloaded file detected in %s within %s s", download_dir, timeout)
            return None
    except Exception as e:
        logger.exception("Context menu download error: %s", e)
        return None


def convert_ogg_to_wav(ogg_path: str, wav_out: Optional[str] = None) -> Optional[str]:
    if AudioSegment is None:
        logger.error("pydub not available")
        return None
    ogg_path = Path(ogg_path)
    if not ogg_path.exists():
        logger.error("ogg not found: %s", ogg_path)
        return None
    if wav_out is None:
        wav_out = str(ogg_path.with_suffix(".wav"))
    try:
        audio = AudioSegment.from_file(str(ogg_path))
        audio.export(wav_out, format="wav")
        logger.info("Converted to WAV: %s", wav_out)
        return wav_out
    except Exception:
        logger.exception("Conversion failed")
        return None
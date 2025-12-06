#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Funciones auxiliares para WhatsApp Web:
 - read_last_messages(driver, n): obtener últimos n mensajes (texto, imagen, audio)
 - send_file(driver, file_path, caption): enviar archivo adjunto con caption opcional
"""
from pathlib import Path
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import logging
from typing import List, Dict, Optional
from selenium.webdriver.common.action_chains import ActionChains

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def read_last_messages(driver, n=10):
    """
    Lee los últimos N mensajes del chat actual, detectando texto, audios, imágenes, etc.
    Identifica claramente si el mensaje es propio (out) o ajeno (in).
    """
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
                # Identificar dirección del mensaje
                classes = bubble.get_attribute("class") or ""
                is_mine = "message-out" in classes
                is_theirs = "message-in" in classes
                
                # Verificación adicional por aria-label
                aria_label = bubble.get_attribute("aria-label") or ""
                if "Tú:" in aria_label or "You:" in aria_label:
                    is_mine = True
                    is_theirs = False
                
                msg = {
                    "element": bubble,
                    "id": bubble.get_attribute("data-id") or bubble.id or str(hash(bubble)),
                    "direction": "out" if is_mine else "in",
                    "is_mine": is_mine,
                    "is_theirs": is_theirs,
                    "type": "text",
                    "text": "",
                    "timestamp": None,
                    "sender": "Tú" if is_mine else "Contacto"
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
                    # Intentar extraer nombre del archivo
                    try:
                        doc_name = bubble.find_element(By.CSS_SELECTOR, "span[title]").get_attribute("title")
                        msg["text"] = f"[Documento: {doc_name}]"
                    except:
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

def send_file(driver, file_path: str, caption: str = "", timeout: int = 30) -> bool:
    """
    Envía un archivo adjunto con caption opcional.
    """
    try:
        logging.info(f"Intentando enviar archivo: {file_path}")
        
        # 1. Buscar botón de clip (adjuntar)
        clip_selectors = [
            "button[aria-label*='Adjuntar']",
            "button[data-tab='10']",
            "span[data-icon='plus']",
            "div[title*='Adjuntar']"
        ]
        
        clip_button = None
        for selector in clip_selectors:
            try:
                clip_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                logging.info(f"Botón de clip encontrado con: {selector}")
                break
            except:
                continue
        
        if not clip_button:
            logging.error("No se encontró el botón de adjuntar")
            return False
        
        clip_button.click()
        time.sleep(1)
        
        # 2. Buscar input de archivo
        file_input = None
        input_selectors = [
            "input[type='file'][accept*='image']",
            "input[type='file']",
        ]
        
        for selector in input_selectors:
            try:
                file_input = driver.find_element(By.CSS_SELECTOR, selector)
                logging.info(f"Input file encontrado con: {selector}")
                break
            except:
                continue
        
        if not file_input:
            logging.error("No se encontró el input de archivo")
            return False
        
        # 3. Enviar el archivo
        abs_path = Path(file_path).resolve()
        file_input.send_keys(str(abs_path))
        logging.info(f"Archivo cargado en el input: {abs_path.name}")
        time.sleep(2)
        
        # 4. Si hay caption, agregarlo
        if caption:
            try:
                caption_box = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true'][data-tab='10']"))
                )
                caption_box.send_keys(caption)
                logging.info("Caption agregado")
                time.sleep(0.5)
            except Exception as e:
                logging.warning(f"No se pudo agregar caption: {e}")
        
        # 5. Buscar el botón de enviar - USANDO EL HTML CORRECTO
        try:
            # Buscar directamente el div con role="button" y aria-label="Enviar"
            logging.info("Buscando botón de enviar...")
            send_button = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR, 
                    "div[role='button'][aria-label='Enviar']"
                ))
            )
            
            logging.info("Botón de enviar encontrado")
            
            # Intentar hacer click con JavaScript directamente
            driver.execute_script("arguments[0].click();", send_button)
            logging.info("✅ Archivo enviado correctamente")
            time.sleep(2)
            return True
            
        except Exception as e:
            logging.warning(f"Método principal falló: {e}")
            
            # Fallback: buscar el ícono y hacer click en él
            try:
                logging.info("Intentando fallback: click en ícono...")
                icon = driver.find_element(By.CSS_SELECTOR, "span[data-icon='wds-ic-send-filled']")
                driver.execute_script("arguments[0].click();", icon)
                logging.info("✅ Archivo enviado con fallback (ícono)")
                time.sleep(2)
                return True
            except Exception as e2:
                logging.warning(f"Fallback de ícono falló: {e2}")
                
                # Último fallback: tecla ENTER
                try:
                    logging.info("Último intento: tecla ENTER...")
                    ActionChains(driver).send_keys(Keys.ENTER).perform()
                    logging.info("✅ Archivo enviado con tecla ENTER")
                    time.sleep(2)
                    return True
                except Exception as e3:
                    logging.error(f"Todos los métodos fallaron: {e3}")
                    return False
        
    except Exception as e:
        logging.exception(f"Error enviando archivo: {e}")
        return False

def filter_only_their_messages(messages: List[Dict]) -> List[Dict]:
    """
    Filtra solo los mensajes del contacto (no los propios).
    Útil para que la IA no se confunda con sus propias respuestas.
    """
    return [m for m in messages if not m.get("is_mine", False)]


def filter_only_my_messages(messages: List[Dict]) -> List[Dict]:
    """
    Filtra solo los mensajes propios.
    """
    return [m for m in messages if m.get("is_mine", False)]
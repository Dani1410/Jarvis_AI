# macros/actions.py
# Implementaciones de acciones atómicas soportadas por el motor de macros.
# Nota: intenta importar PyAutoGUI, psutil, etc. y proporciona mensajes de error útiles si faltan.

import os
import shutil
import subprocess
import sys
import time
from typing import Dict, Any, Optional

try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    import psutil
except Exception:
    psutil = None

# Funciones de alto nivel que el engine invocará.
def action_wait(params: Dict[str, Any]):
    seconds = float(params.get("seconds", 1))
    time.sleep(seconds)
    return {"ok": True, "detail": f"Waited {seconds}s"}


def action_keyboard(params: Dict[str, Any]):
    if pyautogui is None:
        raise RuntimeError("pyautogui no está instalado. Instálalo con `pip install pyautogui`.")
    # params: {"keys": "ctrl+c"} ó {"text": "hola mundo", "interval": 0.05}
    if "text" in params:
        interval = float(params.get("interval", 0.0))
        pyautogui.write(str(params["text"]), interval=interval)
        return {"ok": True, "detail": "Wrote text"}
    elif "keys" in params:
        # keys como "ctrl+c" o lista ["ctrl","c"]
        keys = params["keys"]
        if isinstance(keys, str):
            # soporte básico para combos separados por '+'
            parts = [p.strip() for p in keys.split("+") if p.strip()]
            if len(parts) == 1:
                pyautogui.press(parts[0])
            else:
                pyautogui.hotkey(*parts)
        elif isinstance(keys, (list, tuple)):
            pyautogui.hotkey(*keys)
        return {"ok": True, "detail": f"Sent keys {keys}"}
    else:
        raise ValueError("keyboard action requiere 'text' o 'keys'.")


def action_mouse(params: Dict[str, Any]):
    if pyautogui is None:
        raise RuntimeError("pyautogui no está instalado. Instálalo con `pip install pyautogui`.")
    # params: {"move_to": [x,y], "click": true, "button": "left"}
    if "move_to" in params:
        x, y = params["move_to"]
        duration = float(params.get("duration", 0.0))
        pyautogui.moveTo(x, y, duration=duration)
    if params.get("click"):
        button = params.get("button", "left")
        pyautogui.click(button=button)
    return {"ok": True, "detail": "Mouse action executed"}


def action_file(params: Dict[str, Any]):
    # operaciones: copy, move, delete, rename, open
    op = params.get("op")
    src = params.get("src")
    dest = params.get("dest")
    if op == "copy":
        shutil.copy(src, dest)
        return {"ok": True, "detail": f"Copied {src} -> {dest}"}
    if op == "move":
        shutil.move(src, dest)
        return {"ok": True, "detail": f"Moved {src} -> {dest}"}
    if op == "delete":
        if os.path.isdir(src):
            shutil.rmtree(src)
        else:
            os.remove(src)
        return {"ok": True, "detail": f"Deleted {src}"}
    if op == "rename":
        os.rename(src, dest)
        return {"ok": True, "detail": f"Renamed {src} -> {dest}"}
    if op == "open":
        # cross-platform open
        if sys.platform.startswith("darwin"):
            subprocess.Popen(["open", src])
        elif os.name == "nt":
            os.startfile(src)
        else:
            subprocess.Popen(["xdg-open", src])
        return {"ok": True, "detail": f"Opened {src}"}
    raise ValueError("file action requiere 'op' válido (copy/move/delete/rename/open).")


def action_app(params: Dict[str, Any]):
    # op: open, close, is_running
    op = params.get("op")
    name = params.get("name")  # nombre del ejecutable o comando
    if op == "open":
        cmd = params.get("cmd")
        if cmd:
            subprocess.Popen(cmd, shell=isinstance(cmd, str))
            return {"ok": True, "detail": f"Opened with cmd {cmd}"}
        elif name:
            subprocess.Popen([name])
            return {"ok": True, "detail": f"Opened {name}"}
        else:
            raise ValueError("open requiere 'cmd' o 'name'")
    if op == "close":
        if psutil is None:
            raise RuntimeError("psutil no está instalado. Instálalo con `pip install psutil`.")
        for proc in psutil.process_iter(["name", "pid"]):
            if proc.info["name"] and name and name.lower() in proc.info["name"].lower():
                proc.terminate()
        return {"ok": True, "detail": f"Close attempted for {name}"}
    if op == "is_running":
        if psutil is None:
            raise RuntimeError("psutil no está instalado. Instálalo con `pip install psutil`.")
        for proc in psutil.process_iter(["name"]):
            if proc.info["name"] and name.lower() in proc.info["name"].lower():
                return {"ok": True, "running": True}
        return {"ok": True, "running": False}
    raise ValueError("app action requiere 'op' válido (open/close/is_running).")


def action_command(params: Dict[str, Any]):
    # ⚠️ PROBLEMA: shell=True es un riesgo de seguridad
    cmd = params.get("cmd")
    if cmd is None:
        raise ValueError("command action requiere 'cmd'")
    
    # MEJORA: Validar y sanitizar comandos
    allowed_commands = params.get("allowed_commands", [])  # Lista blanca
    if allowed_commands:
        cmd_base = cmd.split()[0] if isinstance(cmd, str) else cmd[0]
        if cmd_base not in allowed_commands:
            raise ValueError(f"Comando no permitido: {cmd_base}")
    
    cwd = params.get("cwd")
    wait = params.get("wait", True)
    
    # Preferir shell=False cuando sea posible
    if isinstance(cmd, str) and not any(c in cmd for c in ['|', '>', '<', '&']):
        cmd = cmd.split()
        shell_flag = False
    else:
        shell_flag = True
    
    proc = subprocess.Popen(
        cmd, 
        shell=shell_flag, 
        cwd=cwd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True
    )
# macros/triggers.py
# Módulo para registrar triggers: voz, scheduler y event-driven (esqueleto).
# Scheduler usa APScheduler; voice trigger es un hook que la app debe conectar.

import logging
from typing import Callable, Dict, Any, Optional
import threading

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:
    BackgroundScheduler = None

logger = logging.getLogger("jarvis.macros.triggers")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())


class MacroTriggers:
    def __init__(self):
        # scheduler background
        self.voice_hooks = {}
        self.last_trigger_time = {}
        
        if BackgroundScheduler is not None:
            self.scheduler = BackgroundScheduler()
            self.scheduler.start()
        else:
            self.scheduler = None
            logger.warning("APScheduler no está instalado. Scheduler deshabilitado.")
        # voice hooks: la app de Jarvis debe registrar un callback que llame a trigger_by_voice
        self.voice_hooks = {}  # phrase -> callable

    # VOICE TRIGGERS
    def register_voice_phrase(self, phrase: str, callback: Callable[[Dict[str, Any]], Any]):
        # La integración con el módulo de escucha de voz de Jarvis debe invocar MacroTriggers.trigger_by_voice
        self.voice_hooks[phrase.lower()] = callback
        logger.info("Registro voice trigger para frase: %s", phrase)

    def trigger_by_voice(self, phrase: str, meta: Optional[Dict[str, Any]] = None):
        meta = meta or {}
        callback = self.voice_hooks.get(phrase.lower())
        
        if callback:
            # MEJORA: Evitar ejecuciones repetidas accidentales
            now = time.time()
            last_time = self.last_trigger_time.get(phrase, 0)
            cooldown = meta.get("cooldown_seconds", 2)  # 2s por defecto
            
            if now - last_time < cooldown:
                logger.warning(f"Trigger {phrase} en cooldown")
                return {"ok": False, "reason": "cooldown"}
            
            self.last_trigger_time[phrase] = now
            logger.info("Voice trigger activado: %s", phrase)
            return callback(meta)

    # SCHEDULER
    def schedule_cron(self, job_id: str, cron_expr: Dict[str, Any], func: Callable, args=None, kwargs=None):
        if self.scheduler is None:
            raise RuntimeError("Scheduler no disponible (instala apscheduler).")
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        self.scheduler.add_job(func, id=job_id, trigger="cron", args=args, kwargs=kwargs, **cron_expr)
        logger.info("Scheduled cron job %s %s", job_id, cron_expr)

    def schedule_interval(self, job_id: str, seconds: int, func: Callable, args=None, kwargs=None):
        if self.scheduler is None:
            raise RuntimeError("Scheduler no disponible (instala apscheduler).")
        self.scheduler.add_job(func, id=job_id, trigger="interval", seconds=seconds, args=args or [], kwargs=kwargs or {})
        logger.info("Scheduled interval job %s every %ds", job_id, seconds)

    # EVENT-DRIVEN (esqueleto)
    def register_event(self, event_name: str, callback: Callable[[Dict[str, Any]], Any]):
        # Ejemplos de eventos: "usb_inserted", "email_received:URGENTE"
        # La app principal debe conectar los detectores de eventos (ej: watchdog/pyudev/imap) y llamar aquí.
        # Esta implementación solo almacena callback y devuelve handle.
        if not hasattr(self, "_events"):
            self._events = {}
        self._events.setdefault(event_name, []).append(callback)
        logger.info("Registered event %s", event_name)

    def emit_event(self, event_name: str, payload: Dict[str, Any]):
        if not hasattr(self, "_events") or event_name not in self._events:
            logger.warning("No handlers for event %s", event_name)
            return
        for cb in self._events[event_name]:
            try:
                cb(payload)
            except Exception:
                logger.exception("Error en handler de evento %s", event_name)
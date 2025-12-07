"""
Skill de Macros para Jarvis
Integra el sistema de macros con el asistente de voz
"""
import logging
from typing import Dict, Any, Optional
from .engine import MacroEngine
from .storage import MacroStorage
from .triggers import MacroTriggers

logger = logging.getLogger("jarvis.skills.macros")


class MacroSkill:
    def __init__(self, jarvis_instance=None):
        self.storage = MacroStorage()
        self.engine = MacroEngine(self.storage)
        self.triggers = MacroTriggers()
        self.jarvis = jarvis_instance
        
        # Hook para invocar otras skills desde macros
        self.engine.invoke_skill_hook = self._invoke_jarvis_skill
        
        # Registrar comandos de voz básicos
        self._register_voice_commands()
    
    def _invoke_jarvis_skill(self, skill_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Hook para que las macros puedan llamar a otras skills de Jarvis"""
        if self.jarvis and hasattr(self.jarvis, 'execute_skill'):
            try:
                return self.jarvis.execute_skill(skill_name, params)
            except Exception as e:
                logger.error(f"Error invocando skill {skill_name}: {e}")
                return {"ok": False, "error": str(e)}
        return {"ok": False, "error": "Jarvis instance not available"}
    
    def _register_voice_commands(self):
        """Registra comandos de voz básicos para gestionar macros"""
        # Estos se conectarán con tu sistema de reconocimiento de voz
        self.voice_commands = {
            "crear macro": self.handle_create_macro,
            "ejecutar macro": self.handle_run_macro,
            "listar macros": self.handle_list_macros,
            "eliminar macro": self.handle_delete_macro,
        }
    
    # Comandos de voz manejados
    def handle_create_macro(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comando: 'Jarvis, crear macro [nombre]'"""
        name = params.get("name") or params.get("macro_name")
        if not name:
            return {"ok": False, "response": "Necesito un nombre para la macro"}
        
        # Aquí podrías iniciar un modo interactivo para definir la macro
        return {
            "ok": True,
            "response": f"Iniciando creación de macro '{name}'. Dime qué acciones quieres agregar.",
            "state": "creating_macro",
            "macro_name": name
        }
    
    def handle_run_macro(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comando: 'Jarvis, ejecutar macro [nombre]'"""
        name = params.get("name") or params.get("macro_name")
        if not name:
            return {"ok": False, "response": "¿Qué macro quieres ejecutar?"}
        
        try:
            result = self.engine.run_macro(name, params.get("macro_params", {}))
            return {
                "ok": True,
                "response": f"Macro '{name}' ejecutada exitosamente",
                "result": result
            }
        except Exception as e:
            logger.exception(f"Error ejecutando macro {name}")
            return {"ok": False, "response": f"Error: {str(e)}"}
    
    def handle_list_macros(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comando: 'Jarvis, lista las macros' o 'qué macros tengo'"""
        macros = self.storage.list_macros()
        if not macros:
            return {"ok": True, "response": "No tienes macros guardadas"}
        
        macro_list = ", ".join(macros)
        return {
            "ok": True,
            "response": f"Tienes {len(macros)} macros: {macro_list}",
            "macros": macros
        }
    
    def handle_delete_macro(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Comando: 'Jarvis, eliminar macro [nombre]'"""
        name = params.get("name") or params.get("macro_name")
        if not name:
            return {"ok": False, "response": "¿Qué macro quieres eliminar?"}
        
        try:
            self.storage.delete_macro(name)
            return {"ok": True, "response": f"Macro '{name}' eliminada"}
        except Exception as e:
            return {"ok": False, "response": f"Error: {str(e)}"}
    
    # Método principal para procesar comandos
    def process_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa un comando de voz relacionado con macros
        
        Args:
            command: El comando de voz reconocido
            params: Parámetros extraídos del comando
        """
        params = params or {}
        command_lower = command.lower()
        
        # Buscar el handler apropiado
        for trigger, handler in self.voice_commands.items():
            if trigger in command_lower:
                return handler(params)
        
        # Si no es un comando de gestión, buscar macro con trigger de voz
        result = self.triggers.trigger_by_voice(command, params)
        if result:
            return result
        
        return {
            "ok": False,
            "response": "No entendí ese comando de macro"
        }
    
    # Métodos para registrar macros con triggers
    def register_macro_with_voice_trigger(self, macro_name: str, phrase: str):
        """Registra una macro para que se ejecute con una frase específica"""
        def callback(meta):
            return self.engine.run_macro(macro_name, meta)
        
        self.triggers.register_voice_phrase(phrase, callback)
        logger.info(f"Macro '{macro_name}' registrada con trigger: '{phrase}'")
    
    def register_macro_with_schedule(self, macro_name: str, schedule_type: str, **schedule_params):
        """Registra una macro para ejecutarse en un horario"""
        def job_func():
            try:
                self.engine.run_macro(macro_name)
            except Exception as e:
                logger.exception(f"Error en macro programada {macro_name}")
        
        if schedule_type == "cron":
            cron_expr = schedule_params.get("cron_expr", {})
            self.triggers.schedule_cron(
                f"macro_{macro_name}",
                cron_expr,
                job_func
            )
        elif schedule_type == "interval":
            seconds = schedule_params.get("seconds", 60)
            self.triggers.schedule_interval(
                f"macro_{macro_name}",
                seconds,
                job_func
            )
        
        logger.info(f"Macro '{macro_name}' programada con {schedule_type}")
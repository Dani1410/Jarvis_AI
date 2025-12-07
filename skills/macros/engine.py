# macros/engine.py
# Motor principal de ejecución de macros con encadenamiento, condicionales y parámetros.

import copy
import logging
from typing import Any, Dict, List, Optional

from .storage import MacroStorage
from . import actions

logger = logging.getLogger("jarvis.macros")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(ch)


class MacroExecutionError(Exception):
    pass


class MacroEngine:
    def __init__(self, storage: Optional[MacroStorage] = None):
        self.storage = storage or MacroStorage()
        self.call_stack = []
        self.context = {}  # NUEVO: Variables globales entre ejecuciones
    
    def execute_action(self, action: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        action = self.interpolate(action, params)
        typ = action.get("type")
        
        # NUEVO: Acción para guardar/leer variables
        if typ == "set_variable":
            var_name = action.get("params", {}).get("name")
            value = action.get("params", {}).get("value")
            self.context[var_name] = self.interpolate(value, params)
            return {"ok": True, "detail": f"Set {var_name}"}
        
        if typ == "get_variable":
            var_name = action.get("params", {}).get("name")
            default = action.get("params", {}).get("default")
            return {"ok": True, "value": self.context.get(var_name, default)}
        
    def interpolate(self, obj: Any, params: Dict[str, Any]) -> Any:
        # Reemplaza strings con formato {param}
        if isinstance(obj, str):
            try:
                return obj.format(**params)
            except Exception:
                return obj
        if isinstance(obj, dict):
            return {k: self.interpolate(v, params) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.interpolate(v, params) for v in obj]
        return obj

    def execute_action(self, action: Dict[str, Any], params: Dict[str, Any]) -> Dict[str, Any]:
        action = self.interpolate(action, params)
        typ = action.get("type")
        if typ == "keyboard":
            return actions.action_keyboard(action.get("params", {}))
        if typ == "mouse":
            return actions.action_mouse(action.get("params", {}))
        if typ == "file":
            return actions.action_file(action.get("params", {}))
        if typ == "app":
            return actions.action_app(action.get("params", {}))
        if typ == "command":
            return actions.action_command(action.get("params", {}))
        if typ == "wait":
            return actions.action_wait(action.get("params", {}))
        if typ == "call_macro":
            name = action.get("params", {}).get("name")
            macro_params = action.get("params", {}).get("params", {})
            return self.run_macro(name, {**params, **macro_params})
        if typ == "conditional":
            cond = action.get("params", {}).get("if")
            then_steps = action.get("params", {}).get("then", [])
            else_steps = action.get("params", {}).get("else", [])
            cond_ok = self.evaluate_condition(cond, params)
            steps = then_steps if cond_ok else else_steps
            return self.execute_steps(steps, params)
        if typ == "call_skill":
            # Integración con Jarvis: invocar una skill registrada. Aquí devolvemos un placeholder
            skill_name = action.get("params", {}).get("skill")
            payload = action.get("params", {}).get("payload", {})
            # Buscador hook: the host app should monkeypatch `invoke_skill_hook`
            if hasattr(self, "invoke_skill_hook") and callable(getattr(self, "invoke_skill_hook")):
                return self.invoke_skill_hook(skill_name, {**params, **payload})
            else:
                raise MacroExecutionError("No hay hook para invocar habilidades (invoke_skill_hook no definido).")
        raise ValueError(f"Tipo de acción desconocido: {typ}")

    def evaluate_condition(self, cond: Dict[str, Any], params: Dict[str, Any]) -> bool:
    # ...existing code...
    
    # MEJORA: Soportar operadores lógicos
    if typ == "and":
        conditions = cond.get("conditions", [])
        return all(self.evaluate_condition(c, params) for c in conditions)
    
    if typ == "or":
        conditions = cond.get("conditions", [])
        return any(self.evaluate_condition(c, params) for c in conditions)
    
    if typ == "not":
        return not self.evaluate_condition(cond.get("condition"), params)
    
    # Comparaciones de valores
    if typ == "compare":
        left = self.interpolate(cond.get("left"), params)
        right = self.interpolate(cond.get("right"), params)
        op = cond.get("operator", "==")
        operators = {
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            ">": lambda a, b: a > b,
            "<": lambda a, b: a < b,
            ">=": lambda a, b: a >= b,
            "<=": lambda a, b: a <= b,
        }
        return operators.get(op, lambda a, b: False)(left, right)

    def execute_steps(self, steps: List[Dict[str, Any]], params: Dict[str, Any]) -> Dict[str, Any]:
        results = []
        for idx, step in enumerate(steps):
            step_name = step.get("name", f"Step {idx}")  # MEJORA: Nombres descriptivos
            logger.info(f"Ejecutando: {step_name}")
            
            try:
                start_time = time.time()  # MEJORA: Métricas de rendimiento
                r = self.execute_action(step, params)
                elapsed = time.time() - start_time
                
                results.append({
                    "step": idx,
                    "name": step_name,
                    "ok": True,
                    "result": r,
                    "elapsed_ms": round(elapsed * 1000, 2)
                })
                logger.info(f"✓ {step_name} completado en {elapsed:.2f}s")
            except Exception as e:
                logger.exception(f"✗ Error en {step_name}: {e}")

    def run_macro(self, name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        params = params or {}
        if name in self.call_stack:
            raise MacroExecutionError(f"Recursión detectada en macro '{name}'")
        macro = self.storage.get_macro(name)
        if not macro:
            raise MacroExecutionError(f"Macro '{name}' no encontrada")
        logger.info("Ejecutando macro '%s' con params %s", name, params)
        self.call_stack.append(name)
        try:
            steps = macro.get("steps", [])
            local_params = {**macro.get("defaults", {}), **params}
            result = self.execute_steps(steps, local_params)
            return result
        finally:
            self.call_stack.pop()
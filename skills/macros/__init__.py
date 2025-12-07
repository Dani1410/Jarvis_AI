# macros/__init__.py
# Exports principales del paquete de macros

from .engine import MacroEngine
from .storage import MacroStorage
from .triggers import MacroTriggers
from .macro_skill import MacroSkill  # ← AÑADIR ESTA LÍNEA

__all__ = ["MacroEngine", "MacroStorage", "MacroTriggers", "MacroSkill"]
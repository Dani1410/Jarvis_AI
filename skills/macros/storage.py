# macros/storage.py
# Gestión de almacenamiento de macros en JSON

import json
import os
from typing import Dict, Any, List

DEFAULT_DIR = os.path.join(os.path.expanduser("~"), ".jarvis")
DEFAULT_FILE = os.path.join(DEFAULT_DIR, "macros.json")


class MacroStorage:
    def __init__(self, path: str = DEFAULT_FILE):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._write({"version": 1, "macros": {}})

    def _read(self) -> Dict[str, Any]:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: Dict[str, Any]):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list_macros(self) -> List[str]:
        data = self._read()
        return list(data.get("macros", {}).keys())

    def get_macro(self, name: str) -> Dict[str, Any]:
        data = self._read()
        return data.get("macros", {}).get(name)

    def save_macro(self, name: str, macro_def: Dict[str, Any]):
        data = self._read()
        if "macros" not in data:
            data["macros"] = {}
        data["macros"][name] = macro_def
        self._write(data)

    def delete_macro(self, name: str):
        data = self._read()
        if "macros" in data and name in data["macros"]:
            del data["macros"][name]
            self._write(data)
from .voz import hablar
from .cerebro import pensar
from .memoria_vectorial import guardar as guardar_memoria, buscar as buscar_memoria

# Exportar solo las funciones que existen
__all__ = ['hablar', 'pensar', 'guardar_memoria', 'buscar_memoria']
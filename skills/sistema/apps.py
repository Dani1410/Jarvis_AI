"""
Módulo para gestión de aplicaciones.
Responsabilidad: Abrir y gestionar aplicaciones del sistema.
"""
from AppOpener import open as app_open, close as app_close


def abrir_aplicacion(nombre_app):
    """Abre una aplicación por nombre."""
    try:
        app_open(nombre_app, match_closest=True, throw_error=True)
        return f"{nombre_app} abierta correctamente."
    except Exception as e:
        return f"No pude encontrar la aplicación '{nombre_app}'. Error: {e}"


def cerrar_aplicacion(nombre_app):
    """Cierra una aplicación por nombre."""
    try:
        app_close(nombre_app, match_closest=True, throw_error=True)
        return f"{nombre_app} cerrada correctamente."
    except Exception as e:
        return f"No pude cerrar '{nombre_app}'. Error: {e}"


def abrir_multiples(lista_apps):
    """Abre múltiples aplicaciones."""
    resultados = []
    for app in lista_apps:
        resultado = abrir_aplicacion(app)
        resultados.append(resultado)
    return resultados
import imaplib
import email
import os
from dotenv import load_dotenv
from email.header import decode_header

# Importar voz desde el módulo principal
try:
    from modulos import voz
except ImportError:
    # Fallback si se ejecuta desde otro contexto
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
    from modulos import voz

load_dotenv()

EMAIL_USUARIO = os.getenv('EMAIL_USUARIO')
EMAIL_PASS = os.getenv('EMAIL_PASS')

def leer_correos_gmail():
    """Lee los correos no leídos de Gmail usando IMAP."""
    try:
        voz.hablar("Conectando con los servidores de Google...")
        
        # Verificar credenciales
        if not EMAIL_USUARIO or not EMAIL_PASS:
            voz.hablar("No se encontraron las credenciales de email en el archivo .env")
            return "Error: Credenciales no configuradas"
        
        # Conexión SSL al servidor IMAP de Gmail
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USUARIO, EMAIL_PASS)
        
        # Seleccionamos la bandeja de entrada
        mail.select("inbox")
        
        # Buscamos correos NO LEÍDOS (UNSEEN)
        status, messages = mail.search(None, "UNSEEN")
        ids_correos = messages[0].split()
        
        if not ids_correos:
            voz.hablar("No tienes correos nuevos, jefe.")
            return "No hay correos nuevos"

        cantidad = len(ids_correos)
        voz.hablar(f"Tienes {cantidad} correos nuevos. Te leeré los últimos 3.")

        correos_leidos = []
        
        # Leemos los últimos 3 (de atrás para adelante)
        for i in range(cantidad - 1, max(cantidad - 4, -1), -1):
            res, msg = mail.fetch(ids_correos[i], "(RFC822)")
            
            for response in msg:
                if isinstance(response, tuple):
                    msg_obj = email.message_from_bytes(response[1])
                    
                    # Decodificar el Asunto
                    subject, encoding = decode_header(msg_obj["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    # Decodificar el Remitente
                    frm, encoding = decode_header(msg_obj["From"])[0]
                    if isinstance(frm, bytes):
                        frm = frm.decode(encoding if encoding else "utf-8")
                    
                    correo_info = f"De: {frm} - Asunto: {subject}"
                    correos_leidos.append(correo_info)
                    
                    voz.hablar(f"Correo de {frm}. Asunto: {subject}")
        
        voz.hablar("Esos son todos los recientes.")
        mail.close()
        mail.logout()
        
        return f"Se leyeron {len(correos_leidos)} correos nuevos"

    except imaplib.IMAP4.error as e:
        error_msg = "Error de autenticación. Verifica tu contraseña de aplicación de Gmail."
        print(f"Error IMAP: {e}")
        voz.hablar(error_msg)
        return error_msg
        
    except Exception as e:
        error_msg = f"Hubo un error al intentar acceder a tu cuenta: {str(e)}"
        print(error_msg)
        voz.hablar("Hubo un error al intentar acceder a tu cuenta.")
        return error_msg

def verificar_configuracion():
    """Verifica que las credenciales estén configuradas correctamente."""
    if not EMAIL_USUARIO or not EMAIL_PASS:
        return False, "Faltan credenciales en .env (EMAIL_USUARIO y EMAIL_PASS)"
    return True, "Credenciales encontradas"

def contar_correos_nuevos():
    """Retorna la cantidad de correos no leídos sin leerlos."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USUARIO, EMAIL_PASS)
        mail.select("inbox")
        
        status, messages = mail.search(None, "UNSEEN")
        cantidad = len(messages[0].split())
        
        mail.close()
        mail.logout()
        
        return cantidad
        
    except Exception as e:
        print(f"Error al contar correos: {e}")
        return 0
import imaplib
import email
import os  # <--- NUEVO
from dotenv import load_dotenv  # <--- NUEVO
from email.header import decode_header
import voz

load_dotenv()

EMAIL_USUARIO = os.getenv('EMAIL_USUARIO')
EMAIL_PASS = os.getenv('EMAIL_PASS')

def leer_correos_gmail():
    try:
        
        voz.hablar("Conectando con los servidores de Google...")
        
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
            return

        cantidad = len(ids_correos)
        voz.hablar(f"Tienes {cantidad} correos nuevos. Te leeré los últimos 3.")

        # Leemos los últimos 3 (de atrás para adelante)
        for i in range(cantidad - 1, max(cantidad - 4, -1), -1):
            res, msg = mail.fetch(ids_correos[i], "(RFC822)")
            
            for response in msg:
                if isinstance(response, tuple):
                    msg = email.message_from_bytes(response[1])
                    
                    # Decodificar el Asunto
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    # Decodificar el Remitente
                    frm, encoding = decode_header(msg["From"])[0]
                    if isinstance(frm, bytes):
                        frm = frm.decode(encoding if encoding else "utf-8")
                    
                    voz.hablar(f"Correo de {frm}. Asunto: {subject}")
        
        voz.hablar("Esos son todos los recientes.")
        mail.close()
        mail.logout()

    except Exception as e:
        print(e)
        voz.hablar("Hubo un error al intentar acceder a tu cuenta.")
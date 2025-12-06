import ollama
from . import memoria_vectorial as memoria

MODELO = "llama3.2"

# Aquí guardaremos la conversación activa
historial_chat = []

def pensar(pregunta, reiniciar=False):
    global historial_chat
    
    if reiniciar:
        historial_chat = []

    # 1. Buscamos en la memoria a largo plazo (Vectorial)
    recuerdos = memoria.buscar(pregunta)
    
    # 2. Definimos la personalidad base
    sistema = (
        "Eres Jarvis. Tu personalidad es sarcástica, técnica y leal. "
        "Responde siempre en español de México. "
        "Mantén las respuestas breves y directas."
    )
    
    if recuerdos:
        sistema += f"\nCONTEXTO EXTRA DE MEMORIA: {recuerdos}"

    # 3. Construimos la estructura de mensajes para Ollama
    # Si el historial está vacío, iniciamos con el sistema
    if not historial_chat:
        historial_chat.append({'role': 'system', 'content': sistema})
    
    # Añadimos la pregunta actual del usuario
    historial_chat.append({'role': 'user', 'content': pregunta})

    # Ojo: Para no saturar la RAM, mantenemos solo los últimos 10 mensajes
    if len(historial_chat) > 10:
        # Mantenemos el sistema (índice 0) y los últimos 9
        historial_chat = [historial_chat[0]] + historial_chat[-9:]

    print("--> Pensando con contexto...") 
    try:
        response = ollama.chat(model=MODELO, messages=historial_chat)
        respuesta_texto = response['message']['content']
        
        # Añadimos la respuesta de Jarvis al historial para que se acuerde después
        historial_chat.append({'role': 'assistant', 'content': respuesta_texto})
        
        return respuesta_texto
    except Exception as e:
        return f"Error cerebral: {e}"
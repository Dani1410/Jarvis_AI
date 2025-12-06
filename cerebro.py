import ollama
import memoria_vectorial as memoria

MODELO = "llama3.2"

def pensar(pregunta):
    recuerdos = memoria.buscar(pregunta)
    
    prompt = (
        "Eres Jarvis. Responde en español de México. "
        "SÉ MUY BREVE."
    )
    
    if recuerdos:
        prompt += f"\nMEMORIA: {recuerdos}"

    print("--> Procesando...") 
    try:
        response = ollama.chat(model=MODELO, messages=[
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': pregunta},
        ])
        return response['message']['content']
    except:
        return "No puedo conectar con Ollama."
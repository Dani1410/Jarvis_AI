import chromadb
import os

# ✅ CAMBIAR: Usar carpeta 'data' en lugar de raíz
ruta_db = os.path.join(os.getcwd(), "data", "cerebro_vectorial")

# Crear carpeta si no existe
os.makedirs(ruta_db, exist_ok=True)

client = chromadb.PersistentClient(path=ruta_db)
collection = client.get_or_create_collection(name="recuerdos_jarvis")

def guardar(texto):
    """Guarda un nuevo recuerdo en la base de datos vectorial."""
    count = collection.count()
    nuevo_id = str(count + 1)
    
    collection.add(
        documents=[texto],
        ids=[nuevo_id]
    )
    print(f"[MEMORIA] Dato guardado: {texto}")

def buscar(pregunta, n_resultados=2):
    """Busca recuerdos relacionados semánticamente."""
    if collection.count() == 0:
        return ""
    
    try:
        results = collection.query(
            query_texts=[pregunta],
            n_results=n_resultados
        )
        
        recuerdos = results['documents'][0]
        
        if not recuerdos:
            return ""
            
        contexto_texto = "\n".join([f"- {r}" for r in recuerdos])
        return contexto_texto
        
    except Exception as e:
        print(f"[ERROR MEMORIA]: {e}")
        return ""
import chromadb
import os

# Guardamos la base de datos en una carpeta local llamada "cerebro_vectorial"
ruta_db = os.path.join(os.getcwd(), "cerebro_vectorial")
client = chromadb.PersistentClient(path=ruta_db)

# Creamos la colección (como una tabla de SQL)
collection = client.get_or_create_collection(name="recuerdos_jarvis")

def guardar(texto):
    """Guarda un nuevo recuerdo en la base de datos vectorial."""
    # Usamos el total de documentos para generar un ID simple
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
        return "" # No hay recuerdos aún
    
    try:
        results = collection.query(
            query_texts=[pregunta],
            n_results=n_resultados
        )
        
        # Chroma devuelve una lista de listas, la aplanamos
        recuerdos = results['documents'][0]
        
        if not recuerdos:
            return ""
            
        contexto_texto = "\n".join([f"- {r}" for r in recuerdos])
        return contexto_texto
        
    except Exception as e:
        print(f"[ERROR MEMORIA]: {e}")
        return ""
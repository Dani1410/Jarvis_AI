import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

print("--- VOCES DETECTADAS ---")
for index, voice in enumerate(voices):
    print(f"Índice {index}: {voice.name} - ID: {voice.id}")

# Prueba forzando la voz 0 (suele ser la gringa default)
print("\nProbando voz 0...")
engine.setProperty('voice', voices[0].id)
engine.say("Prueba de voz número cero.")
engine.runAndWait()

# Intenta buscar una en español
found = False
for voice in voices:
    if "spanish" in voice.name.lower() or "mexico" in voice.name.lower() or "sabina" in voice.name.lower():
        print(f"\n¡ENCONTRADA! Usando: {voice.name}")
        engine.setProperty('voice', voice.id)
        engine.say("Hola ingeniero, ahora sí me escuchas correctamente.")
        engine.runAndWait()
        found = True
        break

if not found:
    print("\n⚠️ No encontré voz en español explícita.")
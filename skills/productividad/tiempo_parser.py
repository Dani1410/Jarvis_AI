import dateparser

def parsear_tiempo_a_segundos(tiempo_str):
    """Parses a time string and returns the equivalent seconds."""
    segundos = 0
    recurrente = False
    
    if "cada" in tiempo_str.lower():
        recurrente = True
        
        if "hora" in tiempo_str:
            segundos = 3600
        elif "minuto" in tiempo_str:
            palabras = tiempo_str.split()
            for palabra in palabras:
                if palabra.isdigit():
                    segundos = int(palabra) * 60
                    break
            if segundos == 0:
                segundos = 60
        elif "segundo" in tiempo_str:
            segundos = 1
    else:
        dt = dateparser.parse(tiempo_str, languages=['es'], settings={'PREFER_DATES_FROM': 'future'})
        if dt:
            ahora = datetime.datetime.now()
            segundos = (dt - ahora).total_seconds()
    
    return segundos, recurrente
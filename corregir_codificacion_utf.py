input_path = "progarchives_albums_full_actualizado.json"
output_path = "progarchives_albums_full_actualizado_utf.json"
import json

import re

with open("progarchives_albums_full_actualizado.json", "r", encoding="utf-8", errors="replace") as f:
    contenido = f.read()

# Buscar palabras con caracteres fuera del rango típico (acentos mal codificados, caracteres extraños, etc.)
malos = re.findall(r"\b[\w\u00A0-\u00FF]*[^\x00-\x7F]{1,}[\w\u00A0-\u00FF]*\b", contenido)
print(set(malos))


# # Diccionario de reemplazos comunes
# reemplazos = {
#     "Ã¡": "á", "Ã©": "é", "Ã­": "í", "Ã³": "ó", "Ãº": "ú",
#     "Ã±": "ñ", "Ã": "Á", "Ã‰": "É", "Ã": "Í", "Ã“": "Ó",
#     "Ãš": "Ú", "Ã‘": "Ñ", "â": "“", "â": "”", "â": "’",
#     "â": "–", "â": "—", "â¦": "…", "Â": ""
# }

# def reemplazar(texto):
#     for malo, bueno in reemplazos.items():
#         texto = texto.replace(malo, bueno)
#     return texto

# # Aplicar reemplazo a todo
# def corregir(obj):
#     if isinstance(obj, dict):
#         return {k: corregir(v) for k, v in obj.items()}
#     elif isinstance(obj, list):
#         return [corregir(i) for i in obj]
#     elif isinstance(obj, str):
#         return reemplazar(obj)
#     return obj

# # Cargar archivo
# with open("progarchives_albums_full_actualizado.json", "r", encoding="utf-8") as f:
#     data = json.load(f)

# # Corregir y guardar
# data_limpia = corregir(data)

# with open("progarchives_albums_full_actualizado_utf.json", "w", encoding="utf-8") as f:
#     json.dump(data_limpia, f, ensure_ascii=False, indent=2)

# print("¡Archivo reparado guardado como 'arreglado.json'!")

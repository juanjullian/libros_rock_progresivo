import json
import requests
from bs4 import BeautifulSoup
import chardet
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuración
INPUT_JSON = "progarchives_albums_full_actualizado.json"
OUTPUT_JSON = "progarchives_albums_full_actualizado_corregido.json"
HEADERS = {"User-Agent": "Mozilla/5.0"}
MAX_WORKERS = 10

# Cargar el JSON existente
with open(INPUT_JSON, "r", encoding="utf-8") as f:
    data = json.load(f)

def detectar_y_arreglar_encoding(res):
    result = chardet.detect(res.content)
    real_encoding = result['encoding']
    return res.content.decode(real_encoding, errors='replace')

def corregir_album(album):
    try:
        res = requests.get(album["album_url"], headers=HEADERS, timeout=10)
        html = detectar_y_arreglar_encoding(res)
        soup = BeautifulSoup(html, "html.parser")

        # Tracklist
        tracklist_tag = soup.find("strong", string="Songs / Tracks Listing")
        if tracklist_tag:
            p = tracklist_tag.find_next("p")
            if p:
                album["tracklist"] = p.get_text(separator="\n", strip=True)

        # Lineup
        lineup_tag = soup.find("strong", string="Line-up / Musicians")
        if lineup_tag:
            p = lineup_tag.find_next("p")
            if p:
                album["lineup"] = p.get_text(separator="\n", strip=True)

    except Exception as e:
        print(f"⚠️ Error actualizando álbum {album.get('title')}: {e}")
    return album

# Crear lista plana de (banda, album) para procesar en paralelo
tareas = []
for banda, info in data.items():
    for album in info.get("albums", []):
        tareas.append((banda, album))

# Procesar en paralelo
with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futuros = {executor.submit(corregir_album, album): (banda, album) for banda, album in tareas}
    for future in as_completed(futuros):
        banda, album = futuros[future]
        try:
            resultado = future.result()
            print(f"✅ Corregido: {resultado.get('title')} ({banda})")
        except Exception as e:
            print(f"❌ Falló {album.get('title')} ({banda}): {e}")

# Guardar el nuevo JSON corregido
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n📁 Archivo corregido guardado en: {OUTPUT_JSON}")

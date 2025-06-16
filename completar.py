import json
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import time
import os
import openai

# Configuración
INPUT_JSON = "progarchives_albums_full.json"
OUTPUT_JSON = "progarchives_albums_full_actualizado.json"
MAX_WORKERS = 10
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}
GPT_TRANSLATE = True
OPENAI_API_KEY = "OPEN AI API KEY AQUI"
openai.api_key = OPENAI_API_KEY

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def traducir(texto):
    if not GPT_TRANSLATE or not texto:
        return texto
    try:
        logging.debug("→ Traduciendo con GPT...")
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": f"Traduce al español el siguiente texto manteniendo el estilo original:\n\n{texto}"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error al traducir: {e}")
        return texto

def extraer_info_banda(band_name, band_url, current_bio=None):
    try:
        logging.info(f"🌐 Extrayendo info: {band_name}")
        res = requests.get(band_url, headers=HEADERS)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        # País
        h2 = soup.find("h2")
        country = None
        if h2 and "•" in h2.text:
            country = h2.text.split("•")[-1].strip()

        # Imagen principal
        img_tag = soup.select_one("#artist-box img")
        photo_url = img_tag["src"] if img_tag else None

        # Biografía (solo si no existe)
        bio_text = ""
        translated_bio = ""

        if not current_bio or not current_bio.get("original_biography"):
            more_bio = soup.select_one("span#moreBio")
            if more_bio:
                for a in more_bio.find_all("a"): a.unwrap()
                bio_text = more_bio.get_text(separator="\n", strip=True)
            else:
                alt_bio = soup.select_one("#artist-biography")
                if alt_bio:
                    bio_text = alt_bio.get_text(separator="\n", strip=True)

            translated_bio = traducir(bio_text) if bio_text else ""

        return {
            "country": country,
            "photo_url": photo_url,
            "original_biography": bio_text or current_bio.get("original_biography", ""),
            "translated_biography": translated_bio or current_bio.get("translated_biography", "")
        }

    except Exception as e:
        logging.error(f"❌ Error procesando {band_name}: {e}")
        return current_bio or {}

def guardar_json(data):
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logging.info("✅ Archivo guardado: %s", OUTPUT_JSON)

def procesar_banda(nombre, datos):
    url = datos.get("band_url")
    bio_actual = datos.get("biography", {})
    nueva_info = extraer_info_banda(nombre, url, bio_actual)
    datos["biography"] = nueva_info
    return nombre, datos

if __name__ == "__main__":
    if not os.path.exists(INPUT_JSON):
        logging.error(f"No se encuentra el archivo {INPUT_JSON}")
        exit(1)

    with open(INPUT_JSON, encoding="utf-8") as f:
        bandas = json.load(f)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(procesar_banda, nombre, datos): nombre for nombre, datos in bandas.items()}

        for future in as_completed(futures):
            nombre = futures[future]
            try:
                nombre_banda, nuevos_datos = future.result()
                bandas[nombre_banda] = nuevos_datos
                guardar_json(bandas)  # Guardar tras cada banda
            except Exception as e:
                logging.error(f"❌ Error procesando banda {nombre}: {e}")

    logging.info("🎉 Proceso finalizado.")

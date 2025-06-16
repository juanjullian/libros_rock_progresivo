import json
import os
import time
import logging
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import openai

# Config
HTML_FILE = "table.html"
OUTPUT_JSON = "progarchives_albums_full.json"
BASE_URL = "https://www.progarchives.com/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
MAX_WORKERS = 12
MAX_REVIEW_CHARS = 4000
GPT_TRANSLATE = True
OPENAI_API_KEY = "OPENAI_API_KEY"
openai.api_key = OPENAI_API_KEY

# Logger setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Cargar archivo JSON existente si lo hay
if os.path.exists(OUTPUT_JSON):
    with open(OUTPUT_JSON, "r", encoding="utf-8") as f:
        bands = json.load(f)
else:
    bands = {}

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

def fetch_artist_info(band_url):
    try:
        res = requests.get(band_url, headers=HEADERS)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        bio_span = soup.select_one("span#moreBio")
        bio_text = ""

        if bio_span:
            for tag in bio_span.find_all("a"):
                tag.unwrap()
            bio_text = bio_span.get_text(separator="\n", strip=True)

        translated_bio = traducir(bio_text)
        return {
            "band_url": band_url,
            "biography": {
                "original_biography": bio_text,
                "translated_biography": translated_bio
            },
            "albums": []
        }
    except Exception as e:
        logging.error(f"Error al obtener biografía de {band_url}: {e}")
        return {
            "band_url": band_url,
            "biography": {"original_biography": "", "translated_biography": ""},
            "albums": []
        }

def fetch_album_details(album_url):
    try:
        res = requests.get(album_url, headers=HEADERS)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")

        details = {
            "album_type": None,
            "release_info": None,
            "tracklist": None,
            "lineup": None,
            "collaborator_reviews": []
        }

        type_block = soup.find("strong", string=lambda x: x and "Album" in x)
        if type_block:
            details["album_type"] = type_block.get_text(strip=True)
            release_info = type_block.find_next("p")
            if release_info:
                details["release_info"] = release_info.get_text(separator="\n", strip=True)

        tracklist_tag = soup.find("strong", string="Songs / Tracks Listing")
        if tracklist_tag:
            tracklist = tracklist_tag.find_next("p")
            if tracklist:
                details["tracklist"] = tracklist.get_text(separator="\n", strip=True)

        lineup_tag = soup.find("strong", string="Line-up / Musicians")
        if lineup_tag:
            lineup = lineup_tag.find_next("p")
            if lineup:
                details["lineup"] = lineup.get_text(separator="\n", strip=True)

        reviews = soup.find_all("div", style=lambda x: x and "background-color:#f0f0f0" in x)
        char_count = 0
        for r in reviews:
            if "SPECIAL COLLABORATOR" in r.get_text():
                content = r.find("div", style=lambda x: x and "color:#333" in x)
                if content:
                    text = content.get_text(separator="\n", strip=True)
                    if char_count + len(text) > MAX_REVIEW_CHARS:
                        break
                    char_count += len(text)
                    author_tag = r.find("a")
                    author = author_tag.get_text(strip=True) if author_tag else "Desconocido"
                    translated = traducir(text)
                    details["collaborator_reviews"].append({
                        "author": author,
                        "text": text,
                        "translated_text": translated
                    })

        return details
    except Exception as e:
        logging.error(f"Error en detalles del álbum {album_url}: {e}")
        return {}

def process_album(row):
    cols = row.find_all("td")
    if len(cols) < 4:
        return None

    try:
        rank = int(cols[0].text.strip())
    except:
        return None

    album_link = cols[2].find_all("a")[0]
    band_link = cols[2].find_all("a")[1]

    album_name = album_link.text.strip()
    band_name = band_link.text.strip()

    if band_name in bands:
        if any(a["title"] == album_name for a in bands[band_name]["albums"]):
            logging.info(f"⏩ Álbum ya existe: {album_name} ({band_name})")
            return None

    album_url = BASE_URL + album_link["href"]
    band_url = BASE_URL + band_link["href"]

    img_tag = cols[1].find("img")
    cover_url = img_tag["src"] if img_tag else ""
    info = cols[3].text.strip()
    year = int(info[-4:]) if info[-4:].isdigit() else None

    rating_span = cols[4].find("span", id=lambda x: x and "avgRatings_" in x)
    count_span = cols[4].find("span", id=lambda x: x and "nbRatings_" in x)
    avg_rating = float(rating_span.text.strip()) if rating_span else None
    rating_count = int(count_span.text.strip().replace(",", "")) if count_span else None

    logging.info(f"→ Procesando álbum: {album_name} ({band_name})")

    album_data = {
        "rank": rank,
        "title": album_name,
        "album_url": album_url,
        "cover_url": cover_url,
        "year": year,
        "average_rating": avg_rating,
        "ratings_count": rating_count
    }

    album_data.update(fetch_album_details(album_url))

    if band_name not in bands:
        logging.info(f"→ Extrayendo biografía de: {band_name}")
        bands[band_name] = fetch_artist_info(band_url)

    bands[band_name]["albums"].append(album_data)

    # Guardar después de cada álbum
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(bands, f, indent=2, ensure_ascii=False)

    return album_name

def main():
    logging.info("Cargando tabla desde archivo local...")
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    rows = soup.find_all("tr")
    logging.info(f"Filas encontradas: {len(rows)})")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_album, row) for row in rows]
        for future in as_completed(futures):
            result = future.result()
            if result:
                logging.info(f"✓ Álbum procesado: {result}")

if __name__ == "__main__":
    main()

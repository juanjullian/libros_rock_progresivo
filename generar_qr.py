import os
import time
import json
import requests
import urllib.parse
from PIL import Image
import qrcode

# ---------------------------
# Configuración
# ---------------------------
SPOTIFY_CLIENT_ID = ''
SPOTIFY_CLIENT_SECRET = ''
TIDAL_CLIENT_ID = ''
TIDAL_CLIENT_SECRET = ''
TIDAL_TOKEN = ''

QR_SAVE_DIR_SPOTIFY = "./qr/spotify/"
QR_SAVE_DIR_TIDAL = "./qr/tidal/"
LOGO_SPOTIFY = "./logos/spotify_logo.png"
LOGO_TIDAL = "./logos/tidal_logo.png"

# ---------------------------
# QR con logo centrado
# ---------------------------
def generar_qr_con_logo(url, logo_path, save_path, size_px=500):
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_img = qr_img.resize((size_px, size_px), Image.LANCZOS)

    logo = Image.open(logo_path).convert("RGBA")
    logo_size = int(size_px * 0.25)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

    logo_bg = Image.new("RGB", logo.size, "white")
    logo_bg.paste(logo, mask=logo.split()[3])

    pos = ((qr_img.size[0] - logo_size) // 2, (qr_img.size[1] - logo_size) // 2)
    qr_img.paste(logo_bg, pos)

    qr_img.save(save_path)
    print(f"[✅] QR con logo guardado en: {save_path}")

# ---------------------------
# Funciones auxiliares
# ---------------------------
def get_spotify_token(client_id, client_secret):
    print("[DEBUG] Solicitando token de Spotify...")
    url = "https://accounts.spotify.com/api/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "client_credentials"}
    try:
        response = requests.post(url, headers=headers, data=data, auth=(client_id, client_secret), timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"[ERROR] No se pudo conectar con Spotify: {e}")

    token = response.json()['access_token']
    print("[DEBUG] Token de Spotify obtenido.")
    return token

def search_spotify_album(search_query, token):
    print(f"[DEBUG] Buscando en Spotify: {search_query}")
    url = "https://api.spotify.com/v1/search"
    params = {"q": search_query, "type": "album", "limit": 1}
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Falló la búsqueda en Spotify: {e}")
        return None

    items = response.json().get("albums", {}).get("items", [])
    if items:
        print(f"[DEBUG] Álbum encontrado: {items[0]['name']} ({items[0]['id']})")
        return items[0]["id"]
    print("[DEBUG] No se encontraron álbumes en Spotify.")
    return None

def extract_progarchives_album_id(album_url):
    if not album_url:
        return None
    parsed = urllib.parse.urlparse(album_url)
    qs = urllib.parse.parse_qs(parsed.query)
    return qs.get("id", [None])[0]

def generate_tidal_album_url_from_id(tidal_album_id):
    return f"https://tidal.com/browse/album/{tidal_album_id}"

def get_tidal_token(client_id, client_secret):
    url = "https://auth.tidal.com/v1/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "client_credentials",
        "client_id": TIDAL_CLIENT_ID,
        "client_secret": TIDAL_CLIENT_SECRET,
        "scope": "r_usr w_usr"  # puedes personalizar los scopes si es necesario
    }

    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error al obtener token de Tidal: {e}")
        return None





def search_tidal_album_id(query, access_token):
    """
    Busca el primer álbum en Tidal usando el token de acceso.
    La consulta se URL-encodea para igualar la llamada de curl, y se intenta extraer
    el album id tanto de 'relationships.albums.data' como del arreglo 'included'.
    """
    # Codificar el query para asegurar que la URL sea correcta
    encoded_query = urllib.parse.quote(query)
    url = f"https://openapi.tidal.com/v2/searchResults/{encoded_query}"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "accept": "application/vnd.api+json"
    }
    
    params = {
        "countryCode": "US",
        "include": "albums"
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"[DEBUG] Respuesta completa: {data}")
        
        # Intentar extraer desde relationships.albums.data
        albums_rel = data.get("data", {}).get("relationships", {}).get("albums", {}).get("data", [])
        if albums_rel and len(albums_rel) > 0:
            album_id = albums_rel[0].get("id")
            if album_id:
                print(f"[✅] Tidal (relationships): '{query}' → ID {album_id}")
                return album_id
        
        # Si no se encontró allí, buscar en "included"
        included = data.get("included", [])
        for item in included:
            if item.get("type") == "albums" and item.get("id"):
                album_id = item.get("id")
                print(f"[✅] Tidal (included): '{query}' → ID {album_id}")
                return album_id
        
        print(f"[⚠️] No se encontró álbum en Tidal para: {query}")
        return None
    
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error buscando en Tidal: {e}")
        return None



# ---------------------------
# Procesamiento principal
# ---------------------------
def procesar_albums(json_data):
    print("[INFO] Iniciando procesamiento de álbumes...")
    results = []

    try:
        spotify_token = get_spotify_token(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    except Exception as e:
        print(f"[ERROR] {e}")
        return []
    



    os.makedirs(QR_SAVE_DIR_SPOTIFY, exist_ok=True)
    os.makedirs(QR_SAVE_DIR_TIDAL, exist_ok=True)

    for band_name, band_data in json_data.items():
        print(f"\n[INFO] Procesando banda: {band_name}")
        for album in band_data.get("albums", []):
            album_title = album.get("title")
            album_year = album.get("year")
            prog_album_url = album.get("album_url")
            prog_album_id = extract_progarchives_album_id(prog_album_url)
            search_query = f"{band_name} - {album_title}"

            print(f"\n➡️  Álbum: {album_title} ({album_year})")
            print(f"[DEBUG] Query búsqueda: {search_query}")
            print(f"[DEBUG] ID ProgArchives: {prog_album_id}")

            # --- Spotify ---
            spotify_album_id = search_spotify_album(search_query, spotify_token)
            if spotify_album_id:
                spotify_url = f"https://open.spotify.com/album/{spotify_album_id}"
                spotify_path = os.path.join(QR_SAVE_DIR_SPOTIFY, f"{prog_album_id}.png")
                generar_qr_con_logo(spotify_url, LOGO_SPOTIFY, spotify_path)
            else:
                spotify_path = None

            # --- Tidal (mock) ---
            tidal_album_id = search_tidal_album_id(search_query, TIDAL_TOKEN)
            if tidal_album_id:
                tidal_url = f"https://tidal.com/browse/album/{tidal_album_id}"
                tidal_path = os.path.join(QR_SAVE_DIR_TIDAL, f"{prog_album_id}.png")
                generar_qr_con_logo(tidal_url, LOGO_TIDAL, tidal_path)
            else:
                print("[WARN] No se encontró ID de Tidal; no se genera QR.")
                      

            results.append({
                "band": band_name,
                "album": album_title,
                "spotify_id": spotify_album_id,
                "spotify_path": spotify_path,
                "tidal_id": tidal_album_id,
                "tidal_path": tidal_path
            })

            time.sleep(5)


    print("\n✅ Procesamiento finalizado.")
    return results

# ---------------------------
# Ejecución principal
# ---------------------------
if __name__ == "__main__":
    print("[INFO] Cargando archivo JSON...")
    with open("progarchives_albums_full_actualizado.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)

    resultado = procesar_albums(json_data)

    for r in resultado:
        print("======================================")
        print(f"Banda: {r['band']}")
        print(f"Álbum: {r['album']}")
        print(f"  🎧 Spotify → {r['spotify_path']}")
        print(f"  📀 Tidal   → {r['tidal_path']}")

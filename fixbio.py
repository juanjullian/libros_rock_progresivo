import re

with open("libro3.html", "r", encoding="utf-8") as f:
    contenido = f.read()

def reemplazar_bio(m):
    texto = m.group(1)
    parrafos = re.split(r'<br\s*/?>\s*<br\s*/?>', texto)
    nuevo = '\n'.join(f'  <p class="bio-p">{p.strip()}</p>' for p in parrafos)
    return f'<div class="bio">\n{nuevo}\n</div>'

nuevo_contenido = re.sub(r'(?s)<p class="bio">(.*?)</p>', reemplazar_bio, contenido)

with open("libro3v2.html", "w", encoding="utf-8") as f:
    f.write(nuevo_contenido)
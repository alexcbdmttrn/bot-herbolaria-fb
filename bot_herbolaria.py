import requests
import random
import os
import json
import base64
import asyncio
import re
import glob
from datetime import datetime
import pytz
import time
import edge_tts
import shutil
import numpy as np
from PIL import Image

# ================================================================
# IMPORTACIONES DE MOVIEPY (v1.0.3)
# ================================================================
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips,
    concatenate_audioclips,
    AudioClip
)

# ================================================================
# CONFIGURACIÓN
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUD_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUD_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

CLOUDINARY_DISPONIBLE = False
if all([CLOUD_NAME, CLOUD_API_KEY, CLOUD_API_SECRET]):
    import cloudinary
    import cloudinary.uploader
    cloudinary.config(
        cloud_name=CLOUD_NAME,
        api_key=CLOUD_API_KEY,
        api_secret=CLOUD_API_SECRET
    )
    CLOUDINARY_DISPONIBLE = True
    print("✅ Cloudinary configurado correctamente")
else:
    print("⚠️ Cloudinary NO configurado. Se usará file.io como fallback.")

ESTADO_FILE = "estado_herbolaria.json"
CATALOGO_FILE = "catalogo_ingredientes.json"
CATALOGO_CURIOSIDADES_FILE = "catalogo_curiosidades_salud.json"

# ================================================================
# DICCIONARIO DE TRADUCCIÓN (Español → Inglés para Pexels)
# ================================================================
TRADUCCIONES = {
    # Hierbas y plantas
    "manzanilla": "chamomile flower",
    "jengibre": "ginger root",
    "lavanda": "lavender",
    "eucalipto": "eucalyptus leaves",
    "valeriana": "valerian root",
    "cúrcuma": "turmeric root",
    "menta": "mint leaves",
    "romero": "rosemary",
    "albahaca": "basil",
    "tomillo": "thyme",
    "orégano": "oregano",
    "perejil": "parsley",
    "cilantro": "cilantro",
    "salvia": "sage",
    "hinojo": "fennel",
    "anís": "anise seeds",
    "comino": "cumin seeds",
    "canela": "cinnamon sticks",
    "clavo": "clove buds",
    "nuez moscada": "nutmeg",
    "vainilla": "vanilla pods",
    "limón": "lemon fruit",
    "naranja": "orange fruit",
    "toronja": "grapefruit",
    "uva": "grapes",
    "fresa": "strawberry",
    "frambuesa": "raspberry",
    "arándano": "blueberry",
    "mora": "blackberry",
    "kiwi": "kiwi fruit",
    "mango": "mango fruit",
    "papaya": "papaya fruit",
    "piña": "pineapple",
    "coco": "coconut",
    "aguacate": "avocado",
    "granada": "pomegranate",
    "higo": "fig fruit",
    "dátil": "dates fruit",
    "ciruela": "plum fruit",
    "melocotón": "peach fruit",
    "cereza": "cherries",
    "sandía": "watermelon",
    "melón": "cantaloupe",
    "maracuyá": "passion fruit",
    "guayaba": "guava",
    "mamey": "mamey sapote",
    "zapote": "sapote",
    "chirimoya": "cherimoya",
    "lúcuma": "lucuma",
    "pitaya": "dragon fruit",
    "tuna": "prickly pear",
    "zanahoria": "carrot",
    "cebolla": "onion",
    "ajo": "garlic",
    "pimiento": "bell pepper",
    "tomate": "tomato",
    "pepino": "cucumber",
    "calabacín": "zucchini",
    "berenjena": "eggplant",
    "espinaca": "spinach leaves",
    "lechuga": "lettuce",
    "acelga": "swiss chard",
    "col": "cabbage",
    "brócoli": "broccoli",
    "coliflor": "cauliflower",
    "apio": "celery",
    "espárrago": "asparagus",
    "alcachofa": "artichoke",
    "calabaza": "pumpkin",
    "batata": "sweet potato",
    "papa": "potato",
    "yuca": "cassava",
    "maíz": "corn",
    "elote": "corn on the cob",
    "chícharo": "peas",
    "haba": "broad beans",
    "lenteja": "lentils",
    "garbanzo": "chickpeas",
    "frijol": "beans",
    "soja": "soybeans",
    "arroz": "rice grains",
    "trigo": "wheat grains",
    "cebada": "barley grains",
    "avena": "oats",
    "centeno": "rye",
    "mijo": "millet",
    "quinoa": "quinoa grains",
    "amaranto": "amaranth",
    "teff": "teff grains",
    "sorgo": "sorghum",
    "kamut": "kamut grains",
    "espelta": "spelt grains",
    "champiñón": "mushroom",
    "portobello": "portobello mushroom",
    "setas": "wild mushrooms",
    "hongo": "mushroom",
    "algas": "seaweed",
    "espirulina": "spirulina powder",
    "clorella": "chlorella powder",
    "almendra": "almonds",
    "nuez": "walnuts",
    "cacahuate": "peanuts",
    "avellana": "hazelnuts",
    "pistache": "pistachios",
    "piñón": "pine nuts",
    "nuez de la india": "cashews",
    "chía": "chia seeds",
    "linaza": "flax seeds",
    "sésamo": "sesame seeds",
    "girasol": "sunflower seeds",
    "calabaza": "pumpkin seeds",
    "amapola": "poppy seeds",
    "canela": "cinnamon sticks",
    "clavo": "cloves",
    "mostaza": "mustard seeds",
    "comino": "cumin seeds",
    "anís": "anise seeds",
    "cardamomo": "cardamom pods",
    "nuez moscada": "nutmeg",
    # Plantas medicinales
    "zabila": "aloe vera plant",
    "sábila": "aloe vera plant",
    "hojas de sen": "senna leaves",
    "cola de caballo": "horsetail plant",
    "diente de león": "dandelion leaves",
    "pasiflora": "passionflower plant",
    "valeriana": "valerian plant",
    "boldo": "boldo leaves",
    "árnica": "arnica flowers",
    "caléndula": "calendula flowers",
    "cardo mariano": "milk thistle",
    "tepezcohuite": "tepezcohuite bark",
    "cuachalalate": "cuachalalate bark",
    "palo santo": "palo santo wood",
    "damiana": "damiana plant",
    "toronjil": "lemon balm plant",
    "tilia": "linden flowers",
    "flor de azahar": "orange blossoms",
    "jamaica": "hibiscus flowers",
    "cempasúchil": "marigold flowers",
    "gordolobo": "mullein plant",
    "marrubio": "horehound plant",
    "estafiate": "estafiate plant",
    "pingüica": "pingüica plant",
    "guarumbo": "guarumbo tree",
    "tepozán": "tepozán plant",
    "cocolmeca": "cocolmeca plant",
    "cancerina": "cancerina plant",
    "suelda": "suelda plant",
    "rusco": "ruscus plant",
    "cenizo": "cenizo plant",
    "muicle": "muicle plant",
    "capitaneja": "capitaneja plant",
    "espinosilla": "espinosilla plant",
    "hámula": "hamula plant",
    "anacahuita": "anacahuita tree",
    "palo mulato": "palo mulato tree",
    "axocopaque": "axocopaque plant",
    "salvadora": "salvadora plant",
    "yerbanís": "yerbanís plant",
    "hierbabuena": "spearmint plant",
    "zacate limón": "lemongrass",
    "cabellos de elote": "corn silk",
    "hojas de naranjo": "orange leaves",
    "hojas de aguacate": "avocado leaves",
    "hojas de nogal": "walnut leaves",
    "corteza de pino": "pine bark",
    "raíz de maguey": "maguey root",
    "rosa silvestre": "wild rose hips",
    "rosa canina": "rose hips",
    "black cohosh": "black cohosh plant",
    "gotu-kola": "gotu kola plant",
    "centella asiática": "centella asiatica plant",
    "ginseng": "ginseng root",
    "ashwagandha": "ashwagandha root",
    "moringa": "moringa leaves",
    "equinácea": "echinacea flowers",
    "hierba de la golondrina": "swallow wort plant",
    "flor de manita": "manita flower",
    "hinojo": "fennel plant",
    "malva": "mallow flowers",
    "sauce": "willow bark",
    "fresno": "ash tree leaves",
    "laurel": "bay leaves",
    "tejocote": "tejocote fruit",
    "capulín": "capulin cherry",
    "zapote blanco": "white sapote fruit",
    "mangosteen": "mangosteen fruit",
    "acai": "acai berries",
    "noni": "noni fruit",
    "goji": "goji berries",
    "cranberry": "cranberries",
    "bilberry": "bilberries",
    "zarzamora": "blackberries",
    "guanábana": "soursop fruit",
    "membrillo": "quince fruit",
    "chayote": "chayote squash",
    "jícama": "jicama root",
    "betabel": "beetroot",
    "nabo": "turnip",
    "rábano": "radish",
    "calabacita": "zucchini squash",
    "nopal": "nopal cactus pads",
}

# ================================================================
# VOCES (Priorizando las más naturales)
# ================================================================
VOCES_FEMENINAS = [
    "es-MX-DaliaNeural",
    "es-MX-JorgeNeural",
    "es-ES-ElviraNeural",
    "es-CO-SalomeNeural",
    "es-AR-ElenaNeural",
]
VOZ_SELECCIONADA = random.choice(VOCES_FEMENINAS)
print(f"🎤 Voz seleccionada: {VOZ_SELECCIONADA}")

# ================================================================
# CARGA DE CATÁLOGOS Y ESTADO
# ================================================================
def cargar_catalogo_hierbas():
    try:
        with open(CATALOGO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return [{"nombre": "Manzanilla", "categoria": "hierba", "descripcion": "Flor blanca y amarilla", "caracteristicas_visuales": "Flores blancas con centro amarillo"}]

def cargar_catalogo_curiosidades():
    try:
        with open(CATALOGO_CURIOSIDADES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return [{"nombre": "El cerebro y la energía", "categoria": "cerebro", "descripcion": "El cerebro consume el 20% de la energía", "caracteristicas_visuales": "Cerebro brillante"}]

def cargar_estado():
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            estado = json.load(f)
            if "publicadas" not in estado:
                estado["publicadas"] = {"hierbas": [], "curiosidades": []}
            if "hierbas" not in estado["publicadas"]:
                estado["publicadas"]["hierbas"] = []
            if "curiosidades" not in estado["publicadas"]:
                estado["publicadas"]["curiosidades"] = []
            return estado
    except:
        return {"publicadas": {"hierbas": [], "curiosidades": []}}

def guardar_estado(estado):
    try:
        with open(ESTADO_FILE, "w", encoding="utf-8") as f:
            json.dump(estado, f, indent=2, ensure_ascii=False)
        print(f"✅ Estado guardado en {ESTADO_FILE}")
    except Exception as e:
        print(f"❌ Error guardando estado: {e}")

def obtener_item_no_repetido(catalogo, estado, tipo, excluir_nombre=None):
    clave_estado = tipo + "s"
    publicadas = set(p["nombre"] if isinstance(p, dict) else p for p in estado["publicadas"][clave_estado])
    disponibles = [item for item in catalogo if item["nombre"] not in publicadas and item["nombre"] != excluir_nombre]
    
    if not disponibles:
        print(f"🔄 Reiniciando historial de {clave_estado}")
        estado["publicadas"][clave_estado] = []
        guardar_estado(estado)
        disponibles = [item for item in catalogo if item["nombre"] != excluir_nombre]
        if not disponibles:
            disponibles = catalogo
            
    return random.choice(disponibles)

def detectar_tipo_publicacion():
    cdmx = pytz.timezone("America/Mexico_City")
    hora = datetime.now(cdmx).hour
    print(f"🕒 Hora actual en CDMX: {hora}:00")
    if hora == 8:
        return "hierba"
    elif hora == 15:
        return "curiosidad"
    else:
        return "hierba"

# ================================================================
# GENERACIÓN DE TEXTO (POST)
# ================================================================
def generar_texto_hierba(ingrediente):
    prompt = f"""Escribe un post viral para Facebook sobre {ingrediente['nombre']}.
Reglas:
- Línea 1: Emoji + pregunta impactante
- Líneas 2-4: ✅ 3 beneficios concretos
- Línea 5: 🍵 Tip práctico
- Línea 6: Pregunta al lector
- Línea 7: ✨ Descubre tu remedio ideal (gratis) 👉 https://t.me/alex_xanax_bot
- Línea 8: 5 hashtags
- Línea 9: 📸 Edición digital con IA."""
    try:
        r = requests.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.75, "max_tokens": 400}, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return f"🚨 {ingrediente['nombre']}: el secreto que nadie te cuenta.\n✅ Alivia molestias en 10 min.\n✅ Fortalece tu sistema inmune.\n✅ Mejora digestión.\n🍵 Tip: Tómalo caliente.\n👇 ¿Lo usas? Reacciona 🔥.\n✨ Descubre tu remedio ideal 👉 https://t.me/alex_xanax_bot\n#SaludNatural #Bienestar #Herbolaria #NaturalHealth #RemedioEfectivo\n📸 Edición digital con IA."

def generar_texto_curiosidad(curiosidad):
    prompt = f"""Escribe un post fascinante sobre "{curiosidad['nombre']}".
Reglas:
- PROHIBIDO plantas/hierbas
- Línea 1: Emoji + dato impactante
- Líneas 2-4: ✅ 3 datos científicos
- Línea 5: 💡 Sabías que...
- Línea 6: Pregunta al lector
- Línea 7: ✨ Más ciencia gratis 👉 https://t.me/alex_xanax_bot
- Línea 8: 5 hashtags
- Línea 9: 📸 Edición digital con IA."""
    try:
        r = requests.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.8, "max_tokens": 400}, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return f"💡 {curiosidad['nombre']}: dato sorprendente.\n✅ 25M células nuevas/segundo.\n✅ Estómago se renueva cada 3 días.\n✅ Hígado 500+ funciones.\n💡 Sabías que: la piel se renueva cada mes.\n👇 ¿Sorprendido? Dale 👍.\n✨ Más ciencia 👉 https://t.me/alex_xanax_bot\n#Ciencia #CuerpoHumano #DatosIncreibles #HealthScience #Biologia\n📸 Edición digital con IA."

# ================================================================
# GUION PARA REEL (VOZ NATURAL, SIN CTA FINAL EN AUDIO)
# ================================================================
def generar_guion_reel(item, tipo):
    if tipo == "hierba":
        prompt = f"""Crea un guion de 30 segundos (3 segmentos de 10s) sobre {item['nombre']}.
CARACTERÍSTICAS: {item['caracteristicas_visuales']}
DESCRIPCIÓN: {item['descripcion']}
REGLAS DE VOZ NATURAL:
- Usa puntuación natural (comas y puntos) para que la voz de IA haga pausas reales.
- SIN emojis, SIN URLs en el texto hablado.
- S1: Gancho impactante (15-20 palabras).
- S2: 3 beneficios detallados (40-50 palabras).
- S3: Solo un Tip práctico breve (15-20 palabras). NO menciones el asistente ni los comentarios en el audio, eso ya va en la descripción del video.
FORMATO:
SEGMENTO_1: [texto]
SEGMENTO_2: [texto]
SEGMENTO_3: [texto]"""
    else:
        prompt = f"""Crea un guion de 30 segundos (3 segmentos de 10s) sobre {item['nombre']}.
CARACTERÍSTICAS: {item['caracteristicas_visuales']}
DESCRIPCIÓN: {item['descripcion']}
REGLAS DE VOZ NATURAL:
- PROHIBIDO mencionar plantas o hierbas.
- Usa puntuación natural para pausas reales.
- SIN emojis, SIN URLs en el texto hablado.
- S1: Dato impactante (15-20 palabras).
- S2: 3 datos científicos (40-50 palabras).
- S3: Solo una curiosidad o tip breve (15-20 palabras). NO menciones el asistente ni los comentarios en el audio.
FORMATO:
SEGMENTO_1: [texto]
SEGMENTO_2: [texto]
SEGMENTO_3: [texto]"""
    
    try:
        r = requests.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 500}, timeout=60)
        r.raise_for_status()
        texto = r.json()["choices"][0]["message"]["content"].strip()
        segmentos = {}
        if "SEGMENTO_1:" in texto:
            segmentos['s1'] = texto.split("SEGMENTO_1:")[1].split("SEGMENTO_2:")[0].strip()
        if "SEGMENTO_2:" in texto:
            segmentos['s2'] = texto.split("SEGMENTO_2:")[1].split("SEGMENTO_3:")[0].strip()
        if "SEGMENTO_3:" in texto:
            segmentos['s3'] = texto.split("SEGMENTO_3:")[1].strip()
            
        for k in segmentos:
            segmentos[k] = re.sub(r'http\S+', '', segmentos[k])
            segmentos[k] = re.sub(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF]', '', segmentos[k]).strip()
        return segmentos
    except:
        if tipo == "hierba":
            return {
                's1': "¿Sabías que este ingrediente puede acelerar tu metabolismo, mientras descansas?",
                's2': "Acelera tu metabolismo basal, hasta un 15 por ciento en solo 30 minutos. Reduce la inflamación muscular, y activa la circulación sanguínea de forma natural.",
                's3': "Tip práctico: consúmelo fresco por la mañana para obtener mejores resultados."
            }
        else:
            return {
                's1': "¿Sabías que este es un dato fascinante que muy pocos conocen?",
                's2': "Cada día, tu cuerpo genera 25 millones de células nuevas. El estómago se renueva cada 3 días, y el hígado tiene más de 500 funciones diferentes.",
                's3': "Tu piel se reemplaza por completo cada mes. Mantén una rutina saludable para potenciarlo."
            }

# ================================================================
# GENERACIÓN DE QUERY OPTIMIZADA (con traducción + categoría)
# ================================================================
def traducir_a_ingles(texto):
    """Traduce del español al inglés usando el diccionario o DeepSeek."""
    if texto.lower() in TRADUCCIONES:
        return TRADUCCIONES[texto.lower()]
    
    print(f"   🔍 Traduciendo con DeepSeek: '{texto}'")
    prompt = f"Traduce al inglés la siguiente palabra o frase, devolviendo SOLO la traducción sin puntos ni comillas. Es para buscar imágenes en Pexels, así que usa el término más común en fotografía de alimentos o naturaleza. Texto: '{texto}'"
    try:
        r = requests.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 30}, timeout=10)
        if r.status_code == 200:
            traduccion = r.json()["choices"][0]["message"]["content"].strip()
            print(f"   ✅ Traducción: '{traduccion}'")
            return traduccion
    except Exception as e:
        print(f"   ⚠️ Error en traducción: {e}")
    
    # Fallback: eliminar tildes
    return texto.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")

def generar_query_imagen_hierba(ingrediente):
    """Genera query para Pexels usando categoría del catálogo."""
    nombre = ingrediente.get('nombre', '')
    categoria = ingrediente.get('categoria', 'hierba').lower()
    
    termino_ingles = traducir_a_ingles(nombre)
    
    # Palabras clave según categoría (usando tu catálogo)
    if categoria in ['fruta', 'frutas']:
        keywords = "fresh fruit close-up food photography"
    elif categoria in ['verdura', 'verduras', 'hortaliza', 'raíz']:
        keywords = "fresh vegetable close-up food photography"
    elif categoria in ['cereal', 'cereales', 'grano']:
        keywords = "grain close-up food photography"
    elif categoria in ['legumbre']:
        keywords = "legumes beans close-up food photography"
    elif categoria in ['fruto seco', 'frutos secos']:
        keywords = "nuts close-up food photography"
    elif categoria in ['semilla', 'semillas']:
        keywords = "seeds close-up food photography"
    elif categoria in ['hierba', 'hierbas', 'planta', 'plantas', 'flor', 'arbusto']:
        keywords = "herbal plant fresh botanical photography"
    elif categoria in ['hongo', 'hongos', 'seta']:
        keywords = "mushroom close-up food photography"
    elif categoria in ['alga', 'algas']:
        keywords = "seaweed close-up food photography"
    elif categoria in ['especia', 'especias']:
        keywords = "spice close-up food photography"
    elif categoria in ['aceite', 'aceites']:
        keywords = "oil bottle food photography"
    elif categoria in ['mineral']:
        keywords = "mineral rock texture"
    else:
        keywords = "natural ingredient close-up food photography"
    
    query = f"{termino_ingles} {keywords}"
    print(f"   🔍 Query generada: '{query}'")
    return query

def generar_query_imagen_curiosidad(curiosidad):
    """Genera query para Pexels para curiosidades científicas (sin plantas)."""
    nombre = curiosidad.get('nombre', '')
    categoria = curiosidad.get('categoria', 'ciencia').lower()
    
    termino_ingles = traducir_a_ingles(nombre)
    
    if 'cerebro' in categoria or 'mente' in categoria:
        keywords = "brain anatomy science illustration"
    elif 'corazón' in categoria or 'circulación' in categoria:
        keywords = "human heart anatomy medical"
    elif 'intestino' in categoria or 'digestión' in categoria:
        keywords = "human digestive system medical"
    elif 'hueso' in categoria or 'esqueleto' in categoria:
        keywords = "human skeleton anatomy"
    elif 'músculo' in categoria or 'ejercicio' in categoria:
        keywords = "human muscle anatomy"
    elif 'hormona' in categoria or 'endocrino' in categoria:
        keywords = "endocrine system medical"
    elif 'célula' in categoria or 'microscopio' in categoria:
        keywords = "cell biology microscopic"
    else:
        keywords = "medical health infographic"
    
    query = f"{termino_ingles} {keywords} 3D render"
    print(f"   🔍 Query generada: '{query}'")
    return query

# ================================================================
#  GENERACIÓN DE IMÁGENES CON PEXELS
# ================================================================
def buscar_imagen_pexels(query, orientation="portrait"):
    """Busca imagen en Pexels API"""
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "per_page": 1,
        "orientation": orientation
    }
    
    try:
        print(f"   🔍 Buscando en Pexels: '{query}'...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('photos') and len(data['photos']) > 0:
                image_url = data['photos'][0]['src']['large2x']
                print(f"   ✅ Imagen encontrada en Pexels")
                return image_url
        print(f"   ⚠️ No se encontró imagen en Pexels")
        return None
    except Exception as e:
        print(f"   ❌ Error en Pexels: {e}")
        return None

def buscar_imagenes_pexels(query, cantidad=3, orientation="portrait"):
    """Busca múltiples imágenes en Pexels de una sola vez"""
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "per_page": cantidad,
        "orientation": orientation
    }
    
    try:
        print(f"   🔍 Buscando {cantidad} imágenes en Pexels: '{query}'...")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('photos'):
                urls = [photo['src']['large2x'] for photo in data['photos']]
                print(f"   ✅ {len(urls)} imágenes encontradas en Pexels")
                return urls
        print(f"   ⚠️ No se encontraron imágenes en Pexels")
        return []
    except Exception as e:
        print(f"   ❌ Error en Pexels: {e}")
        return []

# ================================================================
# GENERACIÓN DE AUDIO (VOZ NATURAL +8%)
# ================================================================
async def generar_audio(texto, output_path, velocidad=1.08):
    voces_prioritarias = ["es-MX-DaliaNeural", "es-MX-JorgeNeural"] + [v for v in VOCES_FEMENINAS if v not in ["es-MX-DaliaNeural", "es-MX-JorgeNeural"]]
    
    for voz_intento in voces_prioritarias:
        try:
            communicate = edge_tts.Communicate(texto, voz_intento, rate="+8%")
            await communicate.save(output_path)
            print(f"   ✅ Audio generado con {voz_intento}")
            return True
        except Exception as e:
            print(f"   Falló {voz_intento}: {e}")
            continue
    return False

# ================================================================
# GENERACIÓN DE VIDEO REEL (MÚSICA CONTINUA AL 15%)
# ================================================================
def generar_video_reel(imagenes_urls, guion, tipo, duracion_segmento=10):
    print("🎬 Renderizando video Reel...")
    
    imagenes_contenido = []
    for idx, url in enumerate(imagenes_urls):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                path = f"temp_img_{idx}.jpg"
                with open(path, "wb") as f:
                    f.write(r.content)
                imagenes_contenido.append(path)
            else:
                raise Exception("Status no 200")
        except:
            if idx > 0 and len(imagenes_contenido) > 0:
                shutil.copy(imagenes_contenido[0], f"temp_img_{idx}.jpg")
                imagenes_contenido.append(f"temp_img_{idx}.jpg")
            else:
                img = Image.new("RGB", (1080, 1920), (30, 30, 60))
                img.save(f"temp_img_{idx}.jpg")
                imagenes_contenido.append(f"temp_img_{idx}.jpg")
    
    clips = []
    for i, path in enumerate(imagenes_contenido):
        with Image.open(path) as img:
            img_resized = img.resize((1080, 1920), Image.Resampling.LANCZOS)
            resized_path = f"resized_{i}.jpg"
            img_resized.save(resized_path)
        
        clip = ImageClip(resized_path).set_duration(duracion_segmento)
        clip = clip.resize(lambda t: 1 + 0.15 * (t / duracion_segmento))
        clip = clip.set_position(('center', 'center'))
        clips.append(clip)
    
    video_final = concatenate_videoclips(clips, method="compose")
    
    audios = []
    for i, key in enumerate(['s1', 's2', 's3']):
        texto = guion.get(key, "").strip()
        if not texto:
            texto = "Contenido informativo sobre salud y bienestar natural."
        
        audio_path = f"audio_seg_{i}.mp3"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        exito = loop.run_until_complete(generar_audio(texto, audio_path, velocidad=1.08))
        loop.close()
        
        if exito and os.path.exists(audio_path):
            audios.append(AudioFileClip(audio_path))
        else:
            print(f"   ⚠️ No se generó audio segmento {i+1}")
    
    if not audios:
        print("   ⚠️ Sin audios. Creando pista de silencio...")
        try:
            def make_frame(t):
                return np.zeros((1,))
            silent_clip = AudioClip(make_frame, duration=30, fps=44100)
            silent_clip.write_audiofile("silencio.mp3", verbose=False, logger=None)
            audios.append(AudioFileClip("silencio.mp3"))
        except Exception as e:
            print(f"   ⚠️ No se pudo crear silencio: {e}")
    
    if audios:
        audio_combinado = concatenate_audioclips(audios)
        
        musicas = glob.glob("*.mp3") + glob.glob("**/*.mp3", recursive=True)
        musicas = [m for m in musicas if not m.startswith("temp_") and not m.startswith("audio_") and not m.startswith("narracion_") and not m.startswith("silencio")]
        if not musicas:
            musicas = [m for m in glob.glob("*") if m in ["Green Remedy.mp3", "Sacred Root.mp3", "Verdant Stillness.mp3"]]
        
        if musicas:
            musica_path = random.choice(musicas)
            print(f"   🎵 Música seleccionada: {musica_path}")
            try:
                musica = AudioFileClip(musica_path)
                
                if musica.duration < 30:
                    veces = int(30 / musica.duration) + 1
                    musica = concatenate_audioclips([musica] * veces).subclip(0, 30)
                else:
                    musica = musica.subclip(0, 30)
                
                musica = musica.volumex(0.15)
                
                audio_final = CompositeAudioClip([
                    musica.set_start(0),
                    audio_combinado.set_start(2.0)
                ])
                video_final = video_final.set_audio(audio_final)
            except Exception as e:
                print(f"   ⚠️ Error mezclando música: {e}")
                video_final = video_final.set_audio(audio_combinado)
        else:
            print("   ⚠️ Sin música. Solo voz.")
            video_final = video_final.set_audio(audio_combinado)
    else:
        print("   ⚠️ Sin audio. Video mudo.")
    
    output_path = "reel_temp.mp4"
    video_final.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac', verbose=False, logger=None)
    print(f"✅ Video exportado: {output_path}")
    
    if CLOUDINARY_DISPONIBLE:
        try:
            print("☁️ Subiendo a Cloudinary...")
            respuesta = cloudinary.uploader.upload(
                output_path,
                resource_type="video",
                public_id=f"reel_herbolaria_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                overwrite=True
            )
            video_url = respuesta.get('secure_url')
            print(f"✅ Video subido a Cloudinary: {video_url}")
            
            archivos_a_borrar = imagenes_contenido + [f"resized_{i}.jpg" for i in range(len(imagenes_contenido))] + [f"audio_seg_{i}.mp3" for i in range(3)] + [output_path, "silencio.mp3"]
            for path in archivos_a_borrar:
                if os.path.exists(path):
                    try: os.remove(path)
                    except: pass
            return video_url
        except Exception as e:
            print(f"❌ Error Cloudinary: {e}. Usando file.io...")
    
    print("⚠️ Subiendo a file.io (servicio temporal)...")
    try:
        with open(output_path, "rb") as f:
            files = {"file": f}
            r_upload = requests.post("https://file.io/?expires=1h", files=files, timeout=60)
            if r_upload.status_code == 200:
                video_url = r_upload.json().get("link", "")
                print(f"✅ Video subido a file.io: {video_url}")
            else:
                print(f"❌ Error subiendo a file.io: {r_upload.status_code}")
                video_url = ""
    except Exception as e:
        print(f"❌ Error file.io: {e}")
        video_url = ""
    
    archivos_a_borrar = imagenes_contenido + [f"resized_{i}.jpg" for i in range(len(imagenes_contenido))] + [f"audio_seg_{i}.mp3" for i in range(3)] + [output_path, "silencio.mp3"]
    for path in archivos_a_borrar:
        if os.path.exists(path):
            try: os.remove(path)
            except: pass
    
    return video_url

# ================================================================
# MAIN
# ================================================================
def main():
    print("🌿 Bot Herbolaria + Reels (Versión 100% Final con Respaldo)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 🔍 DEBUG: Verificar qué variables llegan desde GitHub Secrets
    print(f"\n🔍 DEBUG - Variables de entorno:")
    print(f"   DEEPSEEK_API_KEY: {'✅ Presente' if DEEPSEEK_API_KEY else '❌ FALTA'}")
    print(f"   MAKE_WEBHOOK_URL: {'✅ Presente' if MAKE_WEBHOOK_URL else '❌ FALTA'}")
    print(f"   PEXELS_API_KEY: {'✅ Presente' if PEXELS_API_KEY else '❌ FALTA'} (Longitud: {len(PEXELS_API_KEY) if PEXELS_API_KEY else 0})")
    print(f"   CLOUDINARY: {'✅ Configurado' if CLOUDINARY_DISPONIBLE else '⚠️ No configurado'}\n")
    
    faltantes = []
    if not DEEPSEEK_API_KEY: faltantes.append("DEEPSEEK_API_KEY")
    if not MAKE_WEBHOOK_URL: faltantes.append("MAKE_WEBHOOK_URL")
    if not PEXELS_API_KEY: faltantes.append("PEXELS_API_KEY")
    
    if faltantes:
        print(f"❌ Faltan estas variables en GitHub Secrets: {', '.join(faltantes)}")
        return
    
    tipo = detectar_tipo_publicacion()
    print(f"🎯 Tipo detectado: {tipo.upper()}")
    
    estado = cargar_estado()
    catalogo = cargar_catalogo_hierbas() if tipo == "hierba" else cargar_catalogo_curiosidades()
    
    item_post = obtener_item_no_repetido(catalogo, estado, tipo)
    print(f"📝 POST: {item_post['nombre']}")
    
    item_reel = obtener_item_no_repetido(catalogo, estado, tipo, excluir_nombre=item_post['nombre'])
    print(f"🎬 REEL: {item_reel['nombre']} (Diferente al post)")
    
    # ==========================================
    # GENERAR POST
    # ==========================================
    print("\n📝 Generando texto POST...")
    if tipo == "hierba":
        post_texto = generar_texto_hierba(item_post)
        post_comentario = "🌿 ¿Qué opinas? Visita nuestro asistente 👉 https://t.me/alex_xanax_bot"
        query_post = generar_query_imagen_hierba(item_post)
    else:
        post_texto = generar_texto_curiosidad(item_post)
        post_comentario = "🧠 ¿Te sorprendió? Asistente gratis 👉 https://t.me/alex_xanax_bot"
        query_post = generar_query_imagen_curiosidad(item_post)
    
    print("🎨 Generando imagen POST...")
    post_image_url = buscar_imagen_pexels(query_post, orientation="portrait")
    
    if not post_image_url:
        if tipo == "hierba":
            post_image_url = "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=1350&fit=crop"
        else:
            post_image_url = "https://images.unsplash.com/photo-1559757175-5700dde675bc?w=1080&h=1350&fit=crop"
        print(f"   ⚠️ Usando imagen de respaldo de Unsplash")
    
    # ==========================================
    # GENERAR REEL
    # ==========================================
    print("\n🎬 Generando REEL...")
    guion = generar_guion_reel(item_reel, tipo)
    print(f"   S1: {guion['s1'][:50]}...")
    print(f"   S2: {guion['s2'][:50]}...")
    print(f"   S3: {guion['s3'][:50]}...")
    
    print("🎨 Generando 3 imágenes REEL...")
    query_reel = generar_query_imagen_hierba(item_reel) if tipo == "hierba" else generar_query_imagen_curiosidad(item_reel)
    imagenes_reel = buscar_imagenes_pexels(query_reel, cantidad=3, orientation="portrait")
    
    while len(imagenes_reel) < 3:
        if post_image_url and not post_image_url.startswith("https://images.unsplash.com"):
            imagenes_reel.append(post_image_url)
        else:
            imagenes_reel.append("https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=1080&h=1920&fit=crop")
    
    print("🎥 Renderizando video REEL...")
    reel_video_url = generar_video_reel(imagenes_reel, guion, tipo, duracion_segmento=10)
    
    if not reel_video_url:
        print("⚠️ No se pudo generar/subir el video. Se enviará sin reel.")
    
    # ==========================================
    # ENVIAR A MAKE.COM (CON SISTEMA DE RESPALDO Y REINTENTOS)
    # ==========================================
    # 🔥 AGREGAR 📸 Edición digital con IA a la descripción del REEL
    reel_caption = f"🌿 {item_reel['nombre']} - Asistente inteligente 👉 https://t.me/alex_xanax_bot\n📸 Edición digital con IA."
    
    payload = {
        "post_message": post_texto,
        "post_image_url": post_image_url,
        "post_comment": post_comentario,
        "reel_video_url": reel_video_url,
        "reel_caption": reel_caption,
        "reel_comment": "🎬 ¿Qué te pareció? Usa nuestro asistente, está en los comentarios 👉 https://t.me/alex_xanax_bot\n📸 Edición digital con IA."
    }
    
    print("\n📤 Enviando a Make.com...")
    exito = False
    
    # 🔥 Bucle de 3 intentos con pausas de 15 segundos (Respaldo automático)
    for intento in range(3):
        try:
            r = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=120)
            if r.status_code in [200, 201, 202]:
                print("✅ Enviado a Make.com correctamente")
                exito = True
                break
            else:
                print(f"⚠️ Intento {intento+1}/3 falló (Código: {r.status_code}). Reintentando en 15s...")
                time.sleep(15)
        except Exception as e:
            print(f"⚠️ Intento {intento+1}/3 falló por conexión: {e}. Reintentando en 15s...")
            time.sleep(15)
            
    if exito:
        # SOLO guardamos el estado si se publicó con éxito
        clave = tipo + "s"
        estado["publicadas"][clave].append({"nombre": item_post["nombre"], "fecha": datetime.now().isoformat()})
        estado["publicadas"][clave].append({"nombre": item_reel["nombre"], "fecha": datetime.now().isoformat()})
        guardar_estado(estado)
        print(f"🎉 ¡Publicados: {item_post['nombre']} y {item_reel['nombre']}!")
    else:
        print("❌ No se pudo enviar a Make.com después de 3 intentos.")
        print("⚠️ El estado NO se guardó. Los temas se reintentarán automáticamente en la próxima ejecución (manual o programada).")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

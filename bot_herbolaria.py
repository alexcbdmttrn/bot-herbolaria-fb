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
from moviepy.editor import ImageClip, AudioFileClip, CompositeAudioClip, concatenate_videoclips, CompositeVideoClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import shutil

# ================================================================
# CONFIGURACIÓN
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
AGNES_API_KEY = os.getenv("AGNES_API_KEY")

# Cloudinary
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
    print("✅ Cloudinary configurado para videos")
else:
    print("⚠️ Cloudinary NO configurado. Se usará Base64 (puede fallar por tamaño).")

ESTADO_FILE = "estado_herbolaria.json"
CATALOGO_FILE = "catalogo_ingredientes.json"
CATALOGO_CURIOSIDADES_FILE = "catalogo_curiosidades_salud.json"

# ================================================================
# VOCES FEMENINAS
# ================================================================
VOCES_FEMENINAS = [
    "es-MX-DaliaNeural",
    "es-MX-BeatrizNeural",
    "es-ES-ElviraNeural",
    "es-ES-AlbaNeural",
    "es-CO-SalomeNeural",
    "es-AR-ElenaNeural",
    "es-US-PalomaNeural",
]
VOZ_SELECCIONADA = random.choice(VOCES_FEMENINAS)
print(f"🎤 Voz: {VOZ_SELECCIONADA}")

# ================================================================
# CARGA DE CATÁLOGOS Y ESTADO
# ================================================================
def cargar_catalogo_hierbas():
    try:
        with open(CATALOGO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        print("⚠️ No se pudo cargar catálogo de hierbas. Usando respaldo.")
        return [{"nombre": "Manzanilla", "categoria": "hierba", "descripcion": "Flor blanca y amarilla, usada en infusiones", "caracteristicas_visuales": "Flores blancas con centro amarillo"}]

def cargar_catalogo_curiosidades():
    try:
        with open(CATALOGO_CURIOSIDADES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        print("⚠️ No se pudo cargar catálogo de curiosidades. Usando respaldo.")
        return [{"nombre": "El cerebro y la energía", "categoria": "cerebro", "descripcion": "Cómo el cerebro consume el 20% de la energía del cuerpo", "caracteristicas_visuales": "Cerebro humano brillante con conexiones neuronales"}]

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
    clave_estado = tipo + "s"  # 'hierbas' o 'curiosidades'
    publicadas = set(p["nombre"] if isinstance(p, dict) else p for p in estado["publicadas"][clave_estado])
    disponibles = [item for item in catalogo if item["nombre"] not in publicadas and item["nombre"] != excluir_nombre]
    
    if not disponibles:
        print(f"🔄 Todos los {clave_estado} publicados (excepto '{excluir_nombre}'). Reiniciando.")
        estado["publicadas"][clave_estado] = []
        guardar_estado(estado)
        disponibles = [item for item in catalogo if item["nombre"] != excluir_nombre]
        if not disponibles:
            disponibles = catalogo
    
    return random.choice(disponibles)

def detectar_tipo_publicacion():
    cdmx = pytz.timezone("America/Mexico_City")
    hora = datetime.now(cdmx).hour
    if hora == 8:
        return "hierba"
    elif hora == 15:
        return "curiosidad"
    else:
        return "hierba"

# ================================================================
# GENERACIÓN DE TEXTO PARA POST
# ================================================================
def generar_texto_hierba(ingrediente):
    prompt = f"""Eres un experto en copywriting viral para Facebook y herbolaria. 
Escribe un post CORTO, IMPACTANTE y con alto engagement sobre: {ingrediente['nombre']}.

REGLAS:
- Línea 1: [Emoji] + [Pregunta impactante con números o mitos]
- Línea 2: ✅ [Beneficio 1 con porcentaje o tiempo]
- Línea 3: ✅ [Beneficio 2 con porcentaje o tiempo]
- Línea 4: ✅ [Beneficio 3 con porcentaje o tiempo]
- Línea 5: 🍵 Tip práctico
- Línea 6: Pregunta DIRECTA al lector (pide reacción o comentario)
- Línea 7: ✨ Descubre tu remedio ideal (gratis) 👉 https://t.me/alex_xanax_bot
- Línea 8: [5 hashtags específicos]
- Línea 9: 📸 Edición digital con IA.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.75, "max_tokens": 400}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return f"🚨 {ingrediente['nombre']}: el secreto que nadie te cuenta.\n✅ Alivia molestias en solo 10 minutos.\n✅ Fortalece tu sistema inmune.\n✅ Mejora tu digestión y energía.\n🍵 Tip: Tómalo caliente antes de dormir.\n👇 ¿Lo usas? Reacciona 🔥 si te funciona.\n✨ Descubre tu remedio ideal (gratis) 👉 https://t.me/alex_xanax_bot\n#SaludNatural #RemedioEfectivo #Bienestar #NaturalHealth #Herbolaria\n📸 Edición digital con IA."

def generar_texto_curiosidad(curiosidad):
    prompt = f"""Eres un divulgador científico. Escribe un post fascinante sobre: "{curiosidad['nombre']}".

REGLAS:
- PROHIBIDO mencionar plantas o hierbas
- Línea 1: [Emoji] + [Dato impactante con número]
- Línea 2: ✅ [Dato científico 1 con porcentaje o cifra]
- Línea 3: ✅ [Dato científico 2 con porcentaje o cifra]
- Línea 4: ✅ [Dato científico 3 con porcentaje o cifra]
- Línea 5: 💡 Sabías que...
- Línea 6: Pregunta al lector (pide reacción o comentario)
- Línea 7: ✨ Más ciencia fascinante (gratis) 👉 https://t.me/alex_xanax_bot
- Línea 8: [5 hashtags específicos]
- Línea 9: 📸 Edición digital con IA.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.8, "max_tokens": 400}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return f"💡 {curiosidad['nombre']}: el dato que cambiará tu forma de verte.\n✅ Tu cuerpo produce 25 millones de células nuevas por segundo.\n✅ El estómago se renueva cada 3 días.\n✅ El hígado tiene más de 500 funciones diferentes.\n💡 Sabías que: tu piel se reemplaza por completo cada mes.\n👇 ¿Conocías esto? Dale 👍 si te sorprendió.\n✨ Más ciencia fascinante (gratis) 👉 https://t.me/alex_xanax_bot\n#CienciaCuriosa #CuerpoHumano #DatosIncreibles #HealthScience #BiologiaHumana\n📸 Edición digital con IA."

# ================================================================
# GENERACIÓN DE GUION PARA REEL
# ================================================================
def generar_guion_reel(item, tipo):
    if tipo == "hierba":
        prompt = f"""Eres un experto en guiones virales para Instagram Reels sobre herbolaria.
Crea un guion de 30 segundos sobre: {item['nombre']}

CARACTERÍSTICAS: {item['caracteristicas_visuales']}
DESCRIPCIÓN: {item['descripcion']}

REGLAS:
- 3 segmentos de 10 segundos cada uno
- SIN emojis, SIN URLs en el texto hablado
- Segmento 1: Gancho visual impactante (15-20 palabras)
- Segmento 2: 3 beneficios detallados (40-50 palabras)
- Segmento 3: Tip práctico + mención del asistente inteligente (20-25 palabras)

FORMATO:
SEGMENTO_1: [texto]
SEGMENTO_2: [texto]
SEGMENTO_3: [texto]
"""
    else:
        prompt = f"""Eres un experto en guiones virales para Instagram Reels científicos.
Crea un guion de 30 segundos sobre: {item['nombre']}

CARACTERÍSTICAS: {item['caracteristicas_visuales']}
DESCRIPCIÓN: {item['descripcion']}

REGLAS:
- PROHIBIDO mencionar plantas, hierbas o remedios naturales
- 3 segmentos de 10 segundos cada uno
- SIN emojis, SIN URLs en el texto hablado
- Segmento 1: Dato científico impactante (15-20 palabras)
- Segmento 2: 3 datos científicos detallados (40-50 palabras)
- Segmento 3: Curiosidad + mención del asistente inteligente (20-25 palabras)

FORMATO:
SEGMENTO_1: [texto]
SEGMENTO_2: [texto]
SEGMENTO_3: [texto]
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 500}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
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
            segmentos[k] = re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ.,;:!?¿¡\-]', '', segmentos[k]).strip()
        return segmentos
    except:
        if tipo == "hierba":
            return {
                's1': f"¿Sabías que el {item['nombre']} puede acelerar tu metabolismo mientras descansas?",
                's2': f"Acelera tu metabolismo basal hasta un 15% en solo 30 minutos. Reduce la inflamación muscular hasta un 40% después del entrenamiento. Activa la circulación sanguínea y ayuda a eliminar toxinas retenidas.",
                's3': f"Tip práctico: Rállalo fresco y tómalo con limón en ayunas. Visita nuestro asistente inteligente gratis."
            }
        else:
            return {
                's1': f"¿Sabías que {item['nombre']} es un dato que pocos conocen?",
                's2': f"Cada día tu cuerpo genera 25 millones de células nuevas. El estómago se renueva cada 3 días. El hígado tiene más de 500 funciones diferentes.",
                's3': f"Tu piel se reemplaza por completo cada mes. Conoce más datos fascinantes con nuestro asistente inteligente gratis."
            }

# ================================================================
# GENERACIÓN DE IMÁGENES
# ================================================================
def generar_prompt_imagen_hierba(ingrediente):
    prompt_ia = f"""Eres un EXPERTO EN FOTOGRAFÍA DE PRODUCTOS Y REDES SOCIALES.
Genera un PROMPT DE IMAGEN en INGLÉS para crear una foto vertical (4:5) de alta calidad para Facebook.

INGREDIENTE: {ingrediente['nombre']}
CATEGORÍA: {ingrediente['categoria']}
DESCRIPCIÓN: {ingrediente['descripcion']}
CARACTERÍSTICAS VISUALES: {ingrediente['caracteristicas_visuales']}

REGLAS:
- Imagen VERTICAL (proporción 4:5, 1080x1350).
- Enfoque hiperrealista con texturas nítidas y gotas de agua.
- Fondo: mesa de madera rústica, luz natural dorada, ambiente cálido.
- Deja un espacio inferior limpio (20%) para superponer texto.
- Estilo: "fotografía de producto profesional, hiperrealista, 4k, ultradetallado".
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt_ia}], "temperature": 0.7, "max_tokens": 300}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        prompt = r.json()["choices"][0]["message"]["content"].strip()
        prompt += " Vertical format 4:5, professional product photography, hyperrealistic, 4k, ultra detailed, natural lighting, vibrant colors, bottom area dark gradient for text overlay."
        return prompt
    except:
        return f"Fresh {ingrediente['nombre']} close-up botanical photography, natural light, wooden table background, photorealistic, 4k, vertical format 4:5, bottom space for text overlay"

def generar_prompt_imagen_curiosidad(curiosidad):
    prompt_ia = f"""Eres un EXPERTO EN ILUSTRACIÓN CIENTÍFICA Y DISEÑO MODERNO.
Genera un PROMPT DE IMAGEN en INGLÉS para crear una imagen vertical (4:5) de alto impacto para Facebook.

TEMA: {curiosidad['nombre']}
CATEGORÍA: {curiosidad['categoria']}
DESCRIPCIÓN: {curiosidad['descripcion']}
CARACTERÍSTICAS VISUALES: {curiosidad['caracteristicas_visuales']}

REGLAS:
- Imagen VERTICAL (proporción 4:5, 1080x1350).
- Estilo: ilustración científica moderna 3D o fotografía médica de alta gama.
- Colores: azul profundo, blanco clínico, acentos en dorado o neón.
- ⚠️ PROHIBIDO: plantas, hierbas, frutas, vegetales, remedios naturales.
- Deja un espacio inferior limpio (20%) para superponer texto.
- Ambiente: moderno, limpio, educativo, tipo portada de revista científica.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt_ia}], "temperature": 0.7, "max_tokens": 350}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        prompt = r.json()["choices"][0]["message"]["content"].strip()
        prompt += " Vertical format 4:5, scientific illustration, medical photography, modern clean aesthetic, 4k, ultra detailed, educational infographic style, no plants, no herbs, bottom area dark gradient for text overlay."
        return prompt
    except:
        return f"Scientific medical illustration, human anatomy diagram, modern clean design, blue and white color scheme, educational infographic style, 4k, vertical format 4:5, bottom space for text overlay"

def generar_imagen_agnes(prompt, tipo="hierba", width=1080, height=1350):
    prompt_limpio = prompt[:500]
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    negative = "deformed, blurry, low quality, text, watermark, logo, ugly, distorted, text overlay" if tipo == "hierba" else "plants, herbs, leaves, flowers, fruits, vegetables, botanical, natural remedies, herbal medicine, deformed, blurry, low quality, text, watermark, logo, ugly, grotesque, vintage, retro, text overlay"
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": prompt_limpio,
        "negative_prompt": negative,
        "width": width,
        "height": height,
        "num_images": 1
    }
    for intento in range(3):
        try:
            print(f"🎨 Intento {intento+1}/3 generando imagen...")
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            if response.status_code == 200:
                data = response.json()
                return data['data'][0]['url']
        except Exception as e:
            print(f"   Error: {e}")
        time.sleep(10)
    return None

# ================================================================
# GENERACIÓN DEL REEL (CON CLOUDINARY O BASE64)
# ================================================================
async def generar_audio(texto, output_path, velocidad=1.10):
    voz = VOZ_SELECCIONADA
    for voz_intento in [voz] + [v for v in VOCES_FEMENINAS if v != voz]:
        try:
            comunicate = edge_tts.Communicate(texto, voz_intento, rate=f"+{int((velocidad-1)*100)}%")
            await comunicate.save(output_path)
            print(f"✅ Audio generado con {voz_intento}")
            return True
        except Exception as e:
            print(f"   Falló {voz_intento}: {e}")
            continue
    return False

def generar_video_reel(imagenes_urls, guion, tipo, duracion_segmento=10):
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
                raise Exception("Status code no 200")
        except:
            if idx > 0 and len(imagenes_contenido) > 0:
                shutil.copy(imagenes_contenido[0], f"temp_img_{idx}.jpg")
                imagenes_contenido.append(f"temp_img_{idx}.jpg")
            else:
                # Imagen de respaldo
                img = Image.new("RGB", (1080, 1920), (30, 30, 60))
                img.save(f"temp_img_{idx}.jpg")
                imagenes_contenido.append(f"temp_img_{idx}.jpg")
    
    clips = []
    for i, path in enumerate(imagenes_contenido):
        # Redimensionar con PIL ANTES de crear el clip (evita el error ANTIALIAS)
        with Image.open(path) as img:
            # Redimensionar a 1080x1920 (vertical para Reel)
            img_resized = img.resize((1080, 1920), Image.Resampling.LANCZOS)
            # Guardar temporalmente
            resized_path = f"resized_{i}.jpg"
            img_resized.save(resized_path)
        
        clip = ImageClip(resized_path).set_duration(duracion_segmento)
        # Zoom lento: 1.15x en 10 segundos (simulado con resize en el tiempo)
        # Usamos la función resize de moviepy que ahora recibe un clip con tamaño fijo
        clip = clip.resize(lambda t: 1 + 0.15 * (t / duracion_segmento))
        clip = clip.set_position(('center', 'center'))
        clips.append(clip)
    
    video_final = concatenate_videoclips(clips, method="compose")
    
    # Generar audios
    audios = []
    for i, key in enumerate(['s1', 's2', 's3']):
        texto = guion.get(key, "")
        if not texto.strip():
            texto = "Contenido informativo sobre salud y bienestar."
        audio_path = f"audio_seg_{i}.mp3"
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        exito = loop.run_until_complete(generar_audio(texto, audio_path, velocidad=1.10))
        loop.close()
        if exito:
            audios.append(AudioFileClip(audio_path))
        else:
            print(f"⚠️ No se generó audio segmento {i+1}")
    
    if audios:
        audio_combinado = concatenate_videoclips(audios)
        # Buscar música
        musicas = glob.glob("*.mp3") + glob.glob("**/*.mp3", recursive=True)
        musicas = [m for m in musicas if not m.startswith("temp_") and not m.startswith("audio_") and not m.startswith("narracion_")]
        if not musicas:
            musicas = [m for m in glob.glob("*") if m in ["Green Remedy.mp3", "Sacred Root.mp3", "Verdant Stillness.mp3"]]
        if musicas:
            musica_path = random.choice(musicas)
            print(f"🎵 Música: {musica_path}")
            try:
                musica = AudioFileClip(musica_path).set_duration(video_final.duration).volumex(0.3)
                audio_final = CompositeAudioClip([
                    musica.set_start(0),
                    audio_combinado.set_start(2.0)
                ])
                video_final = video_final.set_audio(audio_final)
            except Exception as e:
                print(f"⚠️ Error mezclando música: {e}")
                video_final = video_final.set_audio(audio_combinado)
        else:
            video_final = video_final.set_audio(audio_combinado)
    else:
        print("⚠️ Sin audio. Video mudo.")
    
    output_path = "reel_temp.mp4"
    video_final.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
    
    # Subir a Cloudinary o Base64
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
            print(f"✅ Video subido: {video_url}")
            # Limpiar temporales
            for path in imagenes_contenido + [f"resized_{i}.jpg" for i in range(len(imagenes_contenido))] + [f"audio_seg_{i}.mp3" for i in range(3)] + [output_path]:
                if os.path.exists(path):
                    try: os.remove(path)
                    except: pass
            return video_url
        except Exception as e:
            print(f"❌ Error subiendo a Cloudinary: {e}. Usando Base64...")
    else:
        print("⚠️ Cloudinary no disponible. Usando Base64...")
    
    # Fallback Base64
    with open(output_path, "rb") as f:
        video_base64 = base64.b64encode(f.read()).decode('utf-8')
    # Limpiar
    for path in imagenes_contenido + [f"resized_{i}.jpg" for i in range(len(imagenes_contenido))] + [f"audio_seg_{i}.mp3" for i in range(3)] + [output_path]:
        if os.path.exists(path):
            try: os.remove(path)
            except: pass
    return video_base64

# ================================================================
# MAIN
# ================================================================
def main():
    print("🌿 Iniciando Bot de Herbolaria + Reels")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tipo = detectar_tipo_publicacion()
    print(f"🎯 Tipo: {tipo.upper()}")
    
    estado = cargar_estado()
    
    if tipo == "hierba":
        catalogo = cargar_catalogo_hierbas()
    else:
        catalogo = cargar_catalogo_curiosidades()
    
    # Item para POST
    item_post = obtener_item_no_repetido(catalogo, estado, tipo)
    print(f"📝 POST: {item_post['nombre']}")
    
    # Item para REEL (distinto)
    item_reel = obtener_item_no_repetido(catalogo, estado, tipo, excluir_nombre=item_post['nombre'])
    print(f"🎬 REEL: {item_reel['nombre']}")
    
    # ---- Generar POST ----
    print("📝 Generando texto POST...")
    if tipo == "hierba":
        post_texto = generar_texto_hierba(item_post)
        post_comentario = "🌿 ¿Qué opinas? Visita nuestro asistente 👉 https://t.me/alex_xanax_bot"
        prompt_img = generar_prompt_imagen_hierba(item_post)
    else:
        post_texto = generar_texto_curiosidad(item_post)
        post_comentario = "🧠 ¿Te sorprendió? Asistente gratis 👉 https://t.me/alex_xanax_bot"
        prompt_img = generar_prompt_imagen_curiosidad(item_post)
    
    print("🎨 Generando imagen POST...")
    post_image_url = generar_imagen_agnes(prompt_img, tipo=tipo)
    if not post_image_url:
        post_image_url = "https://via.placeholder.com/1080x1350/2a2a2a/6a6a6a?text=Imagen+no+disponible"
    
    # ---- Generar REEL ----
    print("🎬 Generando guion REEL...")
    guion = generar_guion_reel(item_reel, tipo)
    print(f"   S1: {guion['s1'][:50]}...")
    print(f"   S2: {guion['s2'][:50]}...")
    print(f"   S3: {guion['s3'][:50]}...")
    
    print("🎨 Generando 3 imágenes REEL...")
    imagenes_reel = []
    for i in range(3):
        if tipo == "hierba":
            prompt = generar_prompt_imagen_hierba(item_reel) + f" Different angle, variation {i+1}"
        else:
            prompt = generar_prompt_imagen_curiosidad(item_reel) + f" Different scientific visualization, variation {i+1}"
        url_img = generar_imagen_agnes(prompt, tipo=tipo)
        if url_img:
            imagenes_reel.append(url_img)
        else:
            # Fallback: usar la imagen del post o placeholder
            if post_image_url and post_image_url != "https://via.placeholder.com/1080x1350/2a2a2a/6a6a6a?text=Imagen+no+disponible":
                imagenes_reel.append(post_image_url)
            else:
                imagenes_reel.append("https://via.placeholder.com/1080x1920/2a2a2a/6a6a6a?text=Respaldo")
    
    print("🎥 Renderizando video REEL...")
    video_resultado = generar_video_reel(imagenes_reel, guion, tipo, duracion_segmento=10)
    
    if video_resultado and video_resultado.startswith("http"):
        reel_video_url = video_resultado
        reel_video_base64 = ""
    else:
        reel_video_url = ""
        reel_video_base64 = video_resultado if video_resultado else ""
    
    # ---- Enviar a Make.com ----
    payload = {
        "post_message": post_texto,
        "post_image_url": post_image_url,
        "post_comment": post_comentario,
        "reel_video_url": reel_video_url,
        "reel_video_base64": reel_video_base64,
        "reel_caption": f"🌿 {item_reel['nombre']} - Asistente 👉 https://t.me/alex_xanax_bot",
        "reel_comment": "🎬 ¿Qué te pareció? Visita nuestro asistente 👉 https://t.me/alex_xanax_bot"
    }
    
    print("📤 Enviando a Make.com...")
    try:
        r = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=60)
        if r.status_code in [200, 201, 202]:
            print("✅ Enviado a Make.com")
            # Guardar ambos items en el estado
            clave = tipo + "s"
            estado["publicadas"][clave].append({"nombre": item_post["nombre"], "fecha": datetime.now().isoformat()})
            estado["publicadas"][clave].append({"nombre": item_reel["nombre"], "fecha": datetime.now().isoformat()})
            guardar_estado(estado)
            print(f"🎉 ¡Publicados: {item_post['nombre']} (post) y {item_reel['nombre']} (reel)!")
        else:
            print(f"❌ Error Make: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()

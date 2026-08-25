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

# ================================================================
# CONFIGURACIÓN
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
AGNES_API_KEY = os.getenv("AGNES_API_KEY")

ESTADO_FILE = "estado_herbolaria.json"
CATALOGO_FILE = "catalogo_ingredientes.json"
CATALOGO_CURIOSIDADES_FILE = "catalogo_curiosidades_salud.json"

# ================================================================
# VOCES FEMENINAS DISPONIBLES (Edge-TTS)
# ================================================================
VOCES_FEMENINAS = [
    "es-MX-DaliaNeural",      # Mexicana - Muy natural
    "es-MX-BeatrizNeural",    # Mexicana - Profesional
    "es-ES-ElviraNeural",     # Española - Clara
    "es-ES-AlbaNeural",       # Española - Amable
    "es-CO-SalomeNeural",     # Colombiana - Cálida
    "es-AR-ElenaNeural",      # Argentina - Expresiva
    "es-US-PalomaNeural",     # USA Latina - Neutral
]

VOZ_SELECCIONADA = random.choice(VOCES_FEMENINAS)
print(f"🎤 Voz femenina seleccionada: {VOZ_SELECCIONADA}")

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
            return estado
    except:
        return {"publicadas": {"hierbas": [], "curiosidades": []}}

def guardar_estado(estado):
    try:
        with open(ESTADO_FILE, "w", encoding="utf-8") as f:
            json.dump(estado, f, indent=2, ensure_ascii=False)
        print(f"✅ Estado guardado correctamente en {ESTADO_FILE}")
    except Exception as e:
        print(f"❌ Error guardando estado: {e}")

def obtener_item_no_repetido(catalogo, estado, tipo, excluir_nombre=None):
    publicadas = set(p["nombre"] if isinstance(p, dict) else p for p in estado["publicadas"][tipo])
    disponibles = [item for item in catalogo if item["nombre"] not in publicadas and item["nombre"] != excluir_nombre]
    
    if not disponibles:
        print(f"🔄 Todos los {tipo} (excepto '{excluir_nombre}') publicados. Reiniciando historial.")
        estado["publicadas"][tipo] = []
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
# GENERACIÓN DE TEXTO PARA POST NORMAL (SEO ELITE)
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
# GENERACIÓN DE GUION PARA REEL (3 SEGMENTOS)
# ================================================================
def generar_guion_reel(item, tipo):
    """Genera un guion de 3 segmentos para el Reel (sin emojis ni URLs)"""
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
        # Limpieza agresiva
        for k in segmentos:
            segmentos[k] = re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ.,;:!?¿¡\-]', '', segmentos[k]).strip()
        return segmentos
    except Exception as e:
        print(f"⚠️ Error generando guion: {e}. Usando fallback.")
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
# GENERACIÓN DEL REEL CON ZOOM LENTO, VOZ FEMENINA Y MÚSICA
# ================================================================
async def generar_audio(texto, output_path, velocidad=1.10):
    voz = VOZ_SELECCIONADA
    # Intentar con otras voces si falla
    for voz_intento in [voz] + [v for v in VOCES_FEMENINAS if v != voz]:
        try:
            comunicate = edge_tts.Communicate(texto, voz_intento, rate=f"+{int((velocidad-1)*100)}%")
            await comunicate.save(output_path)
            print(f"✅ Audio generado con voz {voz_intento}")
            return True
        except Exception as e:
            print(f"   Falló con {voz_intento}: {e}")
            continue
    return False

def generar_video_reel(imagenes_urls, guion, tipo, duracion_segmento=10):
    """
    Recibe 3 URLs de imágenes y el guion (dict con s1, s2, s3).
    Retorna el video en base64 o None si falla.
    """
    # Descargar imágenes
    imagenes_contenido = []
    for idx, url in enumerate(imagenes_urls):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                # Guardar temporalmente
                path = f"temp_img_{idx}.jpg"
                with open(path, "wb") as f:
                    f.write(r.content)
                imagenes_contenido.append(path)
            else:
                raise Exception("Status code no 200")
        except:
            # Fallback: copiar la primera imagen si falla
            if idx > 0 and len(imagenes_contenido) > 0:
                print(f"   ⚠️ Imagen {idx+1} falló, copiando imagen 1")
                import shutil
                shutil.copy(imagenes_contenido[0], f"temp_img_{idx}.jpg")
                imagenes_contenido.append(f"temp_img_{idx}.jpg")
            else:
                # Crear una imagen de color de respaldo
                print(f"   ⚠️ Imagen {idx+1} falló, creando fondo de color")
                img = Image.new("RGB", (1080, 1920), (30, 30, 60))
                img.save(f"temp_img_{idx}.jpg")
                imagenes_contenido.append(f"temp_img_{idx}.jpg")
    
    # Crear clips con zoom lento (Ken Burns)
    clips = []
    for i, path in enumerate(imagenes_contenido):
        clip = ImageClip(path).resize(height=1920)
        clip = clip.set_duration(duracion_segmento)
        # Zoom lento: 1.15x en 10 segundos
        clip = clip.resize(lambda t: 1 + 0.15 * (t / duracion_segmento))
        # Centrar el zoom
        clip = clip.set_position(('center', 'center'))
        clips.append(clip)
    
    video_final = concatenate_videoclips(clips, method="compose")
    
    # Generar audio de cada segmento y combinarlos
    audios = []
    for i, key in enumerate(['s1', 's2', 's3']):
        texto = guion.get(key, "")
        if not texto.strip():
            texto = "Contenido informativo sobre salud y bienestar."
        audio_path = f"audio_seg_{i}.mp3"
        # Ejecutar la generación asíncrona
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        exito = loop.run_until_completo(generar_audio(texto, audio_path, velocidad=1.10))
        loop.close()
        if exito:
            audios.append(AudioFileClip(audio_path))
        else:
            print(f"⚠️ No se pudo generar audio para segmento {i+1}")
            # Crear un audio de silencio como fallback
            silencio = AudioFileClip(audio_path) if os.path.exists(audio_path) else None
            if silencio:
                audios.append(silencio)
    
    # Combinar audios (cada uno dura 10s)
    if audios:
        audio_combinado = concatenate_videoclips(audios)
        # Cargar música aleatoria de fondo
        musicas = glob.glob("*.mp3") + glob.glob("**/*.mp3", recursive=True)
        musicas = [m for m in musicas if not m.startswith("temp_") and not m.startswith("audio_") and not m.startswith("narracion_")]
        if not musicas:
            # Buscar exactamente los archivos que tienes
            musicas = [m for m in glob.glob("*") if m in ["Green Remedy.mp3", "Sacred Root.mp3", "Verdant Stillness.mp3"]]
        if musicas:
            musica_path = random.choice(musicas)
            print(f"🎵 Música seleccionada: {musica_path}")
            try:
                musica = AudioFileClip(musica_path)
                musica = musica.set_duration(video_final.duration)
                musica = musica.volumex(0.3)  # Bajar volumen para que no opaque la voz
                # Mezclar: la voz comienza en el segundo 2.0 (2 segundos de solo música)
                # Crear un audio de silencio de 2 segundos al inicio de la voz
                silencio_inicial = AudioFileClip(audio_combinado.path) if os.path.exists(audio_combinado.path) else None
                # Mezclar música con la voz (con retraso de 2s en la voz)
                # Para simplificar, overlay la voz sobre la música con un delay de 2s
                audio_final = CompositeAudioClip([
                    musica.set_start(0),
                    audio_combinado.set_start(2.0)
                ])
                video_final = video_final.set_audio(audio_final)
            except Exception as e:
                print(f"⚠️ Error al mezclar música: {e}. Usando solo voz.")
                video_final = video_final.set_audio(audio_combinado)
        else:
            print("⚠️ No se encontró música de fondo. Usando solo voz.")
            video_final = video_final.set_audio(audio_combinado)
    else:
        print("⚠️ No se pudo generar audio. El video será mudo.")
    
    # Renderizar video MP4
    output_path = "reel_temp.mp4"
    video_final.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
    
    # Leer y codificar en base64
    with open(output_path, "rb") as f:
        video_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # Limpiar archivos temporales
    for path in imagenes_contenido + [f"audio_seg_{i}.mp3" for i in range(3)] + [output_path]:
        if os.path.exists(path):
            try:
                os.remove(path)
            except:
                pass
    
    return video_base64

# ================================================================
# MAIN
# ================================================================
def main():
    print("🌿 Iniciando Bot de Herbolaria + Reels (Voz + Música)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tipo = detectar_tipo_publicacion()
    print(f"🎯 Tipo: {tipo.upper()}")
    
    estado = cargar_estado()
    
    # Seleccionar catálogo
    if tipo == "hierba":
        catalogo = cargar_catalogo_hierbas()
    else:
        catalogo = cargar_catalogo_curiosidades()
    
    # ---- ITEM PARA EL POST ----
    item_post = obtener_item_no_repetido(catalogo, estado, tipo)
    print(f"📝 Item para POST: {item_post['nombre']}")
    
    # ---- ITEM PARA EL REEL (DIFERENTE) ----
    item_reel = obtener_item_no_repetido(catalogo, estado, tipo, excluir_nombre=item_post['nombre'])
    print(f"🎬 Item para REEL: {item_reel['nombre']}")
    
    # ============================================================
    # 1. GENERAR POST
    # ============================================================
    print("📝 Generando texto del POST...")
    if tipo == "hierba":
        post_texto = generar_texto_hierba(item_post)
        post_comentario = "🌿 ¿Qué opinas? Déjanos tu comentario y no olvides visitar nuestro asistente inteligente 👉 https://t.me/alex_xanax_bot"
        prompt_img = generar_prompt_imagen_hierba(item_post)
    else:
        post_texto = generar_texto_curiosidad(item_post)
        post_comentario = "🧠 ¿Te sorprendió este dato? Reacciona y comparte. ¡Visita nuestro asistente gratis! 👉 https://t.me/alex_xanax_bot"
        prompt_img = generar_prompt_imagen_curiosidad(item_post)
    
    print("🎨 Generando imagen del POST...")
    post_image_url = generar_imagen_agnes(prompt_img, tipo=tipo)
    if not post_image_url:
        post_image_url = "https://via.placeholder.com/1080x1350/2a2a2a/6a6a6a?text=Imagen+no+disponible"
    
    # ============================================================
    # 2. GENERAR REEL
    # ============================================================
    print("🎬 Generando guion para REEL...")
    guion = generar_guion_reel(item_reel, tipo)
    print(f"   S1: {guion['s1'][:50]}...")
    print(f"   S2: {guion['s2'][:50]}...")
    print(f"   S3: {guion['s3'][:50]}...")
    
    # Generar 3 imágenes para el Reel (usando prompts específicos)
    print("🎨 Generando 3 imágenes para el REEL...")
    imagenes_reel = []
    for i in range(3):
        # Pequeña variación en el prompt para cada segmento
        if tipo == "hierba":
            prompt = generar_prompt_imagen_hierba(item_reel) + f" Different angle, variation {i+1}"
        else:
            prompt = generar_prompt_imagen_curiosidad(item_reel) + f" Different scientific visualization, variation {i+1}"
        url_img = generar_imagen_agnes(prompt, tipo=tipo)
        if url_img:
            imagenes_reel.append(url_img)
        else:
            # Si falla, usar una imagen de respaldo (la misma que el post o una genérica)
            if post_image_url and post_image_url != "https://via.placeholder.com/1080x1350/2a2a2a/6a6a6a?text=Imagen+no+disponible":
                imagenes_reel.append(post_image_url)
            else:
                imagenes_reel.append("https://via.placeholder.com/1080x1920/2a2a2a/6a6a6a?text=Imagen+de+respaldo")
    
    print("🎥 Renderizando video del REEL...")
    video_base64 = generar_video_reel(imagenes_reel, guion, tipo, duracion_segmento=10)
    if not video_base64:
        print("❌ Error al renderizar el Reel. Se enviará solo el Post.")
    
    # ============================================================
    # 3. ENVIAR A MAKE.COM
    # ============================================================
    payload = {
        "post_message": post_texto,
        "post_image_url": post_image_url,
        "post_comment": post_comentario,
        "reel_video_base64": video_base64 if video_base64 else "",
        "reel_caption": f"🌿 {item_reel['nombre']} - Descubre más en nuestro asistente gratis 👉 https://t.me/alex_xanax_bot",
        "reel_comment": "🎬 ¿Qué te pareció? Comenta y visita nuestro asistente inteligente para más remedios 👉 https://t.me/alex_xanax_bot"
    }
    
    print("📤 Enviando a Make.com...")
    try:
        r = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=60)
        if r.status_code in [200, 201, 202]:
            print("✅ Enviado correctamente a Make.com")
            # Guardar estado solo si se envió bien
            estado["publicadas"][tipo].append({"nombre": item_post["nombre"], "fecha": datetime.now().isoformat()})
            estado["publicadas"][tipo].append({"nombre": item_reel["nombre"], "fecha": datetime.now().isoformat()})
            guardar_estado(estado)
            print(f"🎉 ¡Publicación enviada: {item_post['nombre']} (post) y {item_reel['nombre']} (reel)!")
        else:
            print(f"❌ Error en Make: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Error al enviar: {e}")

if __name__ == "__main__":
    main()

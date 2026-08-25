import requests
import random
import os
import json
import re
from datetime import datetime
import pytz
import time

# ================================================================
# CONFIGURACIÓN (variables desde GitHub Secrets)
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
AGNES_API_KEY = os.getenv("AGNES_API_KEY")

# ================================================================
# ARCHIVOS
# ================================================================
ESTADO_FILE = "estado_herbolaria.json"
CATALOGO_FILE = "catalogo_ingredientes.json"
CATALOGO_CURIOSIDADES_FILE = "catalogo_curiosidades_salud.json"

# ================================================================
# CARGAR CATÁLOGOS
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
        print("️ No se pudo cargar catálogo de curiosidades. Usando respaldo.")
        return [{
            "nombre": "El cerebro y la energía",
            "categoria": "cerebro",
            "descripcion": "Cómo el cerebro consume el 20% de la energía del cuerpo",
            "caracteristicas_visuales": "Cerebro humano brillante con conexiones neuronales"
        }]

# ================================================================
# ESTADO (unificado pero separado por tipo)
# ================================================================
def cargar_estado():
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            estado = json.load(f)
            if "publicadas" in estado and not isinstance(estado.get("publicadas"), dict):
                publicadas_viejas = estado["publicadas"]
                estado = {
                    "publicadas": {
                        "hierbas": [{"nombre": p["nombre"], "fecha": p["fecha"]} if isinstance(p, dict) else p for p in publicadas_viejas],
                        "curiosidades": []
                    }
                }
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
        print(f"✅ Estado guardado correctamente en {ESTADO_FILE}")
    except Exception as e:
        print(f"❌ Error guardando estado: {e}")

def obtener_item_no_repetido(catalogo, estado, tipo):
    publicadas = set(p["nombre"] if isinstance(p, dict) else p for p in estado["publicadas"][tipo])
    disponibles = [item for item in catalogo if item["nombre"] not in publicadas]
    
    if not disponibles:
        print(f"🔄 Todos los {tipo} publicados. Reiniciando historial.")
        estado["publicadas"][tipo] = []
        guardar_estado(estado)
        disponibles = catalogo
    
    return random.choice(disponibles)

# ================================================================
# DETECTAR TIPO DE PUBLICACIÓN POR HORA (CDMX)
# ================================================================
def detectar_tipo_publicacion():
    # Forzamos la zona horaria de México
    cdmx = pytz.timezone("America/Mexico_City")
    hora_actual = datetime.now(cdmx).hour
    
    print(f"🕒 Hora actual en CDMX: {hora_actual}:00")
    
    # LÓGICA DE DISTRIBUCIÓN:
    # 8:00 AM (hora 8) -> HIERBA
    # 3:00 PM (hora 15) -> CURIOSIDAD
    
    if hora_actual == 8:
        print("🌿 Horario matutino (8 AM) -> Publicando HIERBA")
        return "hierba"
    elif hora_actual == 15:
        print(" Horario vespertino (3 PM) -> Publicando CURIOSIDAD")
        return "curiosidad"
    else:
        # Fallback por si se ejecuta manualmente a otra hora
        print("⚙️ Ejecución manual o fuera de horario. Publicando HIERBA por defecto.")
        return "hierba"

# ================================================================
# 🌿 PROMPT DE TEXTO PARA HIERBAS (SEO ELITE)
# ================================================================
def generar_texto_hierba(ingrediente):
    prompt = f"""Eres un experto en copywriting viral para Facebook y herbolaria. 
Escribe un post CORTO, IMPACTANTE y con alto engagement sobre: {ingrediente['nombre']}.

REGLAS ESTRICTAS (NO LAS ROMPAS):
- Usa EXACTAMENTE este formato con saltos de línea (sin líneas vacías):
  Línea 1: [Emoji de impacto como , 🚨 o ⚠️] + [Pregunta o afirmación contraintuitiva con números o mitos] 
  Línea 2: ✅ [Beneficio 1 con porcentaje, tiempo o comparación concreta]
  Línea 3: ✅ [Beneficio 2 con porcentaje, tiempo o comparación concreta]
  Línea 4: ✅ [Beneficio 3 con porcentaje, tiempo o comparación concreta]
  Línea 5: 🍵 Tip: [Consejo práctico y accionable de 1 línea]
  Línea 6: [Pregunta DIRECTA al lector, pídele que reaccione o comente con un emoji específico]
  Línea 7: ✨ Descubre tu remedio ideal (gratis) 👉 https://t.me/alex_xanax_bot
  Línea 8: [5 hashtags específicos: 3 en español + 2 en inglés, sin espacios entre #]
  Línea 9: 📸 Edición digital con IA.

- NO uses líneas en blanco entre cada línea.
- Cada línea debe ser corta (máx 80 caracteres).
- Tono: cercano, sorprendente, con datos reales.
- Los beneficios deben ser específicos (ej. "aumenta un 15%", "reduce en 30 minutos").
- La pregunta de la línea 6 debe pedir un emoji o una respuesta en comentarios.

EJEMPLO DE FORMATO (NO COPIES EL CONTENIDO, SOLO LA ESTRUCTURA):
⏳ ¿Sabías que el jengibre quema grasa mientras duermes?
✅ Acelera tu metabolismo basal en un 15% en solo 30 minutos.
✅ Reduce la inflamación muscular hasta un 40% post-entreno.
✅ Activa la circulación y elimina toxinas retenidas.
🍵 Tip: Rállalo fresco y tómalo con limón en ayunas.
 ¿Ya probaste el jengibre así? Cuéntame en comentarios.
✨ Descubre tu remedio ideal (gratis) 👉 https://t.me/alex_xanax_bot
#JengibreQuemaGrasa #AntiInflamatorioNatural #MetabolismoActivo #GingerHealth #RemedioCaseroEfectivo
📸 Edición digital con IA.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.75, "max_tokens": 400}
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        texto = r.json()["choices"][0]["message"]["content"].strip()
        
        # Verificar que contiene los elementos clave, si no, fallback
        if not any(emoji in texto for emoji in ["✅", "🍵", "✨"]):
            print("⚠️ Texto generado con formato incorrecto. Usando fallback.")
            return generar_fallback_hierba(ingrediente)
        return texto
    except Exception as e:
        print(f"❌ Error en DeepSeek: {e}")
        return generar_fallback_hierba(ingrediente)

def generar_fallback_hierba(ingrediente):
    return f"""🚨 {ingrediente['nombre']}: el secreto que nadie te cuenta.
✅ Alivia molestias en solo 10 minutos.
✅ Fortalece tu sistema inmune.
✅ Mejora tu digestión y energía.
 Tip: Tómalo caliente antes de dormir.
👇 ¿Lo usas? Reacciona  si te funciona.
✨ Descubre tu remedio ideal (gratis) 👉 https://t.me/alex_xanax_bot
#SaludNatural #RemedioEfectivo #Bienestar #NaturalHealth #Herbolaria
📸 Edición digital con IA."""

# ================================================================
# 🧠 PROMPT DE TEXTO PARA CURIOSIDADES (SEO ELITE)
# ================================================================
def generar_texto_curiosidad(curiosidad):
    prompt = f"""Eres un divulgador científico y copywriter viral. Escribe un post CORTO y FASCINANTE para Facebook sobre: "{curiosidad['nombre']}".

🚨 REGLAS ESTRICTAS:
- PROHIBIDO mencionar: plantas, hierbas, remedios naturales, tés, infusiones.
- PERMITIDO: datos científicos, porcentajes, estudios, anatomía, hormonas, cerebro, órganos.
- Usa EXACTAMENTE este formato (sin líneas vacías):
  Línea 1: [Emoji como ⚠️, 💡 o 🧠] + [Dato impactante con número o comparación sorprendente]
  Línea 2: ✅ [Dato científico 1 con porcentaje o cifra]
  Línea 3: ✅ [Dato científico 2 con porcentaje o cifra]
  Línea 4: ✅ [Dato científico 3 con porcentaje o cifra]
  Línea 5: 💡 Sabías que: [curiosidad extra breve]
  Línea 6: [Pregunta DIRECTA al lector con emoji, pide reacción o comentario]
  Línea 7: ✨ Más ciencia fascinante (gratis)  https://t.me/alex_xanax_bot
  Línea 8: [5 hashtags específicos: 3 en español + 2 en inglés]
  Línea 9: 📸 Edición digital con IA.

- Tono: educativo, asombroso, accesible pero riguroso.
- Cada línea máx 80 caracteres.

EJEMPLO DE ESTRUCTURA:
⚠️ El 90% de la gente ignora que su cerebro se "come" a sí mismo cuando tiene sueño.
✅ Pesa solo 1.4 kg pero consume el 20% de todo el oxígeno.
✅ Genera 20 vatios de electricidad (suficiente para un LED).
✅ Si duermes menos de 6 horas, pierde el 30% de sus conexiones.
💡 Sabías que: las neuronas no se regeneran, pero las sinapsis sí.
🤯 ¿Te dejó loco? Reacciona  si es nuevo o 🔥 si ya lo sabías.
✨ Más ciencia fascinante (gratis) 👉 https://t.me/alex_xanax_bot
#CerebroHumano #NeurocienciaReal #DatosQueSorprenden #BrainFacts #SaludMental
📸 Edición digital con IA.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.8, "max_tokens": 400}
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        texto = r.json()["choices"][0]["message"]["content"].strip()
        
        # Filtro anti-plantas
        palabras_prohibidas = ['manzanilla', 'lavanda', 'jengibre', 'té de', 'infusión', 'hierba', 'planta medicinal', 'eucalipto', 'valeriana', 'romero', 'albahaca', 'remedio natural']
        if any(p in texto.lower() for p in palabras_prohibidas):
            print("⚠️ Texto contiene plantas. Usando fallback científico.")
            return generar_fallback_curiosidad(curiosidad)
        return texto
    except Exception as e:
        print(f" Error en DeepSeek: {e}")
        return generar_fallback_curiosidad(curiosidad)

def generar_fallback_curiosidad(curiosidad):
    return f"""💡 {curiosidad['nombre']}: el dato que cambiará tu forma de verte.
✅ Tu cuerpo produce 25 millones de células nuevas por segundo.
✅ El estómago se renueva cada 3 días.
✅ El hígado tiene más de 500 funciones diferentes.
💡 Sabías que: tu piel se reemplaza por completo cada mes.
👇 ¿Conocías esto? Dale 👍 si te sorprendió.
✨ Más ciencia fascinante (gratis) 👉 https://t.me/alex_xanax_bot
#CienciaCuriosa #CuerpoHumano #DatosIncreibles #HealthScience #BiologiaHumana
📸 Edición digital con IA."""

# ================================================================
# 🌿 PROMPT IMAGEN HIERBAS (con espacio para texto/overlay)
# ================================================================
def generar_prompt_imagen_hierba(ingrediente):
    prompt_ia = f"""Eres un EXPERTO EN FOTOGRAFÍA DE PRODUCTOS Y REDES SOCIALES.
Genera un PROMPT DE IMAGEN en INGLÉS para crear una foto vertical (4:5) de alto impacto para Facebook.

INGREDIENTE: {ingrediente['nombre']}
CATEGORÍA: {ingrediente['categoria']}
DESCRIPCIÓN: {ingrediente['descripcion']}
CARACTERÍSTICAS VISUALES: {ingrediente['caracteristicas_visuales']}

REGLAS ESTRICTAS:
- Imagen VERTICAL (proporción 4:5, 1080x1350).
- Enfoque hiperrealista con texturas nítidas y gotas de agua o brillos.
- Fondo: mesa de madera rústica, luz natural dorada (hora dorada), ambiente cálido y acogedor.
- Colores vibrantes y naturales que resalten el ingrediente.
- IMPORTANTE: Deja un espacio inferior limpio (20% del encuadre) en tono oscuro o degradado para superponer texto (título) sin que se pierda.
- Estilo: "fotografía de producto profesional, hiperrealista, 4k, ultradetallado, estilo estudio".

Salida: SOLO el prompt en inglés, sin texto adicional.
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
    except Exception as e:
        print(f"❌ Error generando prompt: {e}")
        return f"Fresh {ingrediente['nombre']} close-up botanical photography, natural light, wooden table background, photorealistic, 4k, vertical format 4:5, bottom space for text overlay"

# ================================================================
# 🧠 PROMPT IMAGEN CURIOSIDADES (estilo científico moderno)
# ================================================================
def generar_prompt_imagen_curiosidad(curiosidad):
    prompt_ia = f"""Eres un EXPERTO EN ILUSTRACIÓN CIENTÍFICA Y DISEÑO MODERNO.
Genera un PROMPT DE IMAGEN en INGLÉS para crear una imagen vertical (4:5) de alto impacto para Facebook.

TEMA: {curiosidad['nombre']}
CATEGORÍA: {curiosidad['categoria']}
DESCRIPCIÓN: {curiosidad['descripcion']}
CARACTERÍSTICAS VISUALES: {curiosidad['caracteristicas_visuales']}

REGLAS ESTRICTAS:
- Imagen VERTICAL (proporción 4:5, 1080x1350).
- Estilo: ilustración científica moderna 3D o fotografía médica de alta gama.
- Colores: azul profundo, blanco clínico, acentos en dorado o neón para destacar datos.
- Elementos: órganos humanos estilizados, células, moléculas, gráficos de datos, siluetas humanas con resaltados.
- ️ PROHIBIDO: plantas, hierbas, frutas, vegetales, remedios naturales, estética vintage.
- IMPORTANTE: Deja un espacio inferior limpio (20%) con fondo oscuro o gradiente para superponer texto.
- Ambiente: moderno, limpio, educativo, tipo portada de National Geographic o revista científica.

Salida: SOLO el prompt en inglés, sin texto adicional.
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
    except Exception as e:
        print(f"❌ Error generando prompt: {e}")
        return f"Scientific medical illustration, human anatomy diagram, modern clean design, blue and white color scheme, educational infographic style, 4k, vertical format 4:5, bottom space for text overlay"

# ================================================================
# GENERAR IMAGEN CON AGNES AI
# ================================================================
def generar_imagen_agnes(prompt, tipo="hierba", width=1080, height=1350):
    prompt_limpio = prompt[:500]
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    
    if tipo == "curiosidad":
        negative = (
            "plants, herbs, leaves, flowers, fruits, vegetables, botanical, "
            "natural remedies, herbal medicine, tea leaves, foliage, "
            "deformed, blurry, low quality, text, watermark, logo, "
            "close-up face, portrait, ugly, grotesque, vintage, retro, "
            "text overlay, typography, words"
        )
    else:
        negative = (
            "deformed, blurry, low quality, text, watermark, logo, "
            "close-up face, portrait, ugly, grotesque, distorted, "
            "text overlay, typography, words"
        )
    
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": prompt_limpio,
        "negative_prompt": negative,
        "width": width,
        "height": height,
        "num_images": 1
    }
    
    intentos = 3
    for intento in range(1, intentos + 1):
        try:
            print(f"🎨 Intento {intento}/{intentos} generando imagen...")
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            if response.status_code == 200:
                data = response.json()
                image_url = data['data'][0]['url']
                print(f"✅ Imagen generada (1080x{height})")
                return image_url
            else:
                print(f"❌ Error Agnes AI: {response.status_code} - {response.text[:200]}")
        except Exception as e:
            print(f"❌ Error conexión: {e}")
        
        if intento < intentos:
            print("⏳ Esperando 10s antes de reintentar...")
            time.sleep(10)
    
    return None

# ================================================================
# ENVIAR A MAKE.COM
# ================================================================
def enviar_a_make(message, image_url):
    """Envía el texto y la URL de la imagen al webhook de Make.com"""
    payload = {
        "message": message,
        "image_url": image_url,  # Make descargará esta URL
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        print(f"📤 Enviando a Make.com...")
        print(f"   Message: {message[:100]}...")
        print(f"   Image URL: {image_url}")
        
        r = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=60)
        if r.status_code in [200, 201, 202]:
            print("✅ Enviado a Make.com correctamente")
            return True
        else:
            print(f"❌ Make respondió: {r.status_code} - {r.text}")
            return False
    except Exception as e:
        print(f" Error conexión con Make: {e}")
        return False

# ================================================================
# MAIN
# ================================================================
def main():
    print("🌿 Iniciando Bot de Herbolaria + Curiosidades (SEO Elite Edition)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return
    
    tipo = detectar_tipo_publicacion()
    print(f"🎯 Tipo de publicación detectado: {tipo.upper()}")
    
    estado = cargar_estado()
    
    if tipo == "hierba":
        catalogo = cargar_catalogo_hierbas()
        item = obtener_item_no_repetido(catalogo, estado, "hierbas")
        print(f"🌱 Hierba del día: {item['nombre']}")
        print(f" Publicadas: {len(estado['publicadas']['hierbas'])} / {len(catalogo)}")
        
        print("📝 Generando texto con DeepSeek (formato viral)...")
        texto = generar_texto_hierba(item)
        print("✅ Texto generado con gancho, pregunta y hashtags específicos.")
        
        print("🎨 Generando prompt de imagen con espacio para texto...")
        prompt_img = generar_prompt_imagen_hierba(item)
        
        image_url = generar_imagen_agnes(prompt_img, tipo="hierba", width=1080, height=1350)
        
        nombre_item = item["nombre"]
        tipo_registro = "hierbas"
    
    else:
        catalogo = cargar_catalogo_curiosidades()
        item = obtener_item_no_repetido(catalogo, estado, "curiosidades")
        print(f"🧠 Curiosidad del día: {item['nombre']}")
        print(f"📊 Publicadas: {len(estado['publicadas']['curiosidades'])} / {len(catalogo)}")
        
        print(" Generando texto científico con DeepSeek (formato viral)...")
        texto = generar_texto_curiosidad(item)
        print("✅ Texto científico generado con gancho, pregunta y hashtags específicos.")
        
        print("🎨 Generando prompt de imagen científica con espacio para texto...")
        prompt_img = generar_prompt_imagen_curiosidad(item)
        
        image_url = generar_imagen_agnes(prompt_img, tipo="curiosidad", width=1080, height=1350)
        
        nombre_item = item["nombre"]
        tipo_registro = "curiosidades"
    
    print(f"📝 Prompt imagen: {prompt_img[:150]}...")
    
    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviado = enviar_a_make(texto, None)
    else:
        print(f"✅ Imagen generada: {image_url}")
        enviado = enviar_a_make(texto, image_url)
    
    if enviado:
        estado["publicadas"][tipo_registro].append({
            "nombre": nombre_item,
            "fecha": datetime.now().isoformat()
        })
        guardar_estado(estado)
        print(f"🎉 ¡Publicación enviada: {nombre_item}!")
    else:
        print("⚠️ No se guardó el estado (error de Make).")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

import requests
import random
import os
import json
import re
from datetime import datetime
import pytz

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
# 🤖 DISCLOSURE DE IA (transparencia)
# ================================================================
ACTIVAR_DISCLOSURE_IA = True
# 🔽 Cambiamos el texto para que sea exactamente igual al del bot de terror
DISCLOSURE_TEXT = "\n\n_Imágenes generadas con IA_"

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
        print("⚠️ No se pudo cargar catálogo de curiosidades. Usando respaldo.")
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
            # Migrar estado viejo si es necesario
            if "publicadas" in estado and not isinstance(estado.get("publicadas"), dict):
                publicadas_viejas = estado["publicadas"]
                estado = {
                    "publicadas": {
                        "hierbas": [{"nombre": p["nombre"], "fecha": p["fecha"]} if isinstance(p, dict) else p for p in publicadas_viejas],
                        "curiosidades": []
                    }
                }
            # Asegurar estructura correcta
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
    """Obtiene un item no repetido según el tipo (hierba o curiosidad)."""
    publicadas = set(p["nombre"] if isinstance(p, dict) else p for p in estado["publicadas"][tipo])
    disponibles = [item for item in catalogo if item["nombre"] not in publicadas]
    
    if not disponibles:
        print(f"🔄 Todos los {tipo} publicados. Reiniciando historial.")
        estado["publicadas"][tipo] = []
        guardar_estado(estado)
        disponibles = catalogo
    
    return random.choice(disponibles)

# ================================================================
# DETECTAR TIPO DE PUBLICACIÓN POR CRON
# ================================================================
def detectar_tipo_publicacion():
    """
    Detecta si toca publicar hierba o curiosidad según el cron schedule.
    - cron '0 14 * * *' (7 AM CDMX) -> hierba
    - cron '0 21 * * *' (3 PM CDMX) -> hierba
    - cron '0 2 * * *'  (8 PM CDMX) -> curiosidad
    """
    cron = os.getenv("CRON_SCHEDULE", "")
    
    if cron == "0 14 * * *":
        return "hierba"
    elif cron == "0 21 * * *":
        return "hierba"
    elif cron == "0 2 * * *":
        return "curiosidad"
    else:
        # Fallback por hora actual (para pruebas manuales)
        cdmx = pytz.timezone("America/Mexico_City")
        hora = datetime.now(cdmx).hour
        if 19 <= hora <= 23:  # 7pm a 11pm
            return "curiosidad"
        else:
            return "hierba"

# ================================================================
# 🌿 PROMPT IMAGEN HIERBAS (vertical 1080x1350)
# ================================================================
def generar_prompt_imagen_hierba(ingrediente):
    prompt_ia = f"""Eres un EXPERTO EN FOTOGRAFÍA DE PRODUCTOS Y REDES SOCIALES.

Genera un PROMPT DE IMAGEN en INGLÉS para crear una foto vertical (4:5) de alta calidad para Facebook.

INGREDIENTE: {ingrediente['nombre']}
CATEGORÍA: {ingrediente['categoria']}
DESCRIPCIÓN: {ingrediente['descripcion']}
CARACTERÍSTICAS VISUALES: {ingrediente['caracteristicas_visuales']}

REGLAS ESTRICTAS:
- La imagen debe ser VERTICAL (proporción 4:5, como para móvil).
- Enfoque en el ingrediente con detalles nítidos y texturas.
- Fondo atractivo: mesa de madera rústica, luz natural, ambiente cálido.
- Colores vibrantes y naturales que resalten el ingrediente.
- Estilo: "fotografía de producto profesional, hiperrealista, 4k, ultradetallado".
- La imagen debe ser tan realista que parezca una foto de estudio profesional.

Salida: SOLO el prompt en inglés, sin texto adicional.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt_ia}], "temperature": 0.7, "max_tokens": 300}
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        prompt = r.json()["choices"][0]["message"]["content"].strip()
        prompt += " Vertical format 4:5, professional product photography, hyperrealistic, 4k, ultra detailed, perfect for Facebook feed, natural lighting, vibrant colors."
        return prompt
    except Exception as e:
        print(f"❌ Error generando prompt: {e}")
        return f"Fresh {ingrediente['nombre']} close-up botanical photography, natural light, wooden table background, photorealistic, 4k, vertical format 4:5 for social media"

# ================================================================
# 🧠 PROMPT IMAGEN CURIOSIDADES (científico/educativo)
# ================================================================
def generar_prompt_imagen_curiosidad(curiosidad):
    prompt_ia = f"""Eres un EXPERTO EN ILUSTRACIÓN CIENTÍFICA Y FOTOGRAFÍA MÉDICA.

Genera un PROMPT DE IMAGEN en INGLÉS para crear una foto vertical (4:5) de alta calidad para Facebook.

TEMA: {curiosidad['nombre']}
CATEGORÍA: {curiosidad['categoria']}
DESCRIPCIÓN: {curiosidad['descripcion']}
CARACTERÍSTICAS VISUALES: {curiosidad['caracteristicas_visuales']}

REGLAS ESTRICTAS:
- Imagen VERTICAL (proporción 4:5, móvil).
- Estilo: ilustración científica moderna, infografía médica, o fotografía anatómica profesional.
- Colores: azul médico, blanco clínico, tonos vibrantes que resalten datos científicos.
- Elementos: órganos humanos estilizados, células, moléculas, gráficos de datos, siluetas humanas con órganos visibles.
- ⚠️ PROHIBIDO: plantas, hierbas, frutas, vegetales, remedios naturales, estética vintage.
- Ambiente: moderno, limpio, educativo, tipo revista científica.

Salida: SOLO el prompt en inglés, sin texto adicional.
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt_ia}], "temperature": 0.7, "max_tokens": 350}
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        prompt = r.json()["choices"][0]["message"]["content"].strip()
        prompt += " Vertical format 4:5, scientific illustration, medical photography, modern clean aesthetic, 4k, ultra detailed, educational infographic style, no plants, no herbs."
        return prompt
    except Exception as e:
        print(f"❌ Error generando prompt: {e}")
        return f"Scientific medical illustration, human anatomy diagram, modern clean design, blue and white color scheme, educational infographic style, 4k, vertical format 4:5"

# ================================================================
# 🌿 TEXTO DEEPSEEK PARA HIERBAS (SIN hashtags en el prompt)
# ================================================================
def generar_texto_hierba(ingrediente):
    prompt = f"""Eres un experto en herbolaria y redacción para redes sociales. Escribe un post CORTO y ATRACTIVO para Facebook sobre {ingrediente['nombre']}.

REGLAS ESTRICTAS:
- Usa EXACTAMENTE este formato con saltos de línea después de cada icono:
  Línea 1: 🌿 {ingrediente['nombre']}: [frase gancho de una línea]
  Línea 2: ✅ [beneficio 1 corto y convincente]
  Línea 3: ✅ [beneficio 2 corto y convincente]
  Línea 4: ✅ [beneficio 3 corto y convincente]
  Línea 5: 🍵 Tip: [consejo práctico corto]
  Línea 6: ¿Quieres saber qué producto es ideal para ti? 
  Línea 7: ✨¡Pregunta gratis 24/7! 👉 https://t.me/alex_xanax_bot

- Cada línea DEBE ser corta (máx 60 caracteres).
- SIN líneas en blanco entre cada línea.
- Usa un tono cálido, cercano y convincente.
- Menciona beneficios reales y prácticos.
- NO agregues hashtags (yo los agregaré después).

Formato EXACTO:
🌿 Jengibre: la raíz que enciende tu vitalidad.
✅ Alivia la inflamación y el dolor muscular.
✅ Fortalece tu sistema inmune.
✅ Acelera la digestión.
🍵 Tip: Añade 3 rodajas a tu agua caliente.
¿Quieres saber qué producto es ideal para ti? 
✨¡Pregunta gratis 24/7! 👉 https://t.me/alex_xanax_bot
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 250}
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ Error en DeepSeek: {e}")
        return f"""🌿 {ingrediente['nombre']}: Tu aliado natural.
✅ Alivia síntomas de resfriado.
✅ Descongestiona vías respiratorias.
✅ Calma la tos y la irritación.
🍵 Tip: Prepara una infusión caliente.
¿Quieres saber qué producto es ideal para ti? 
✨¡Pregunta gratis 24/7! 👉 https://t.me/alex_xanax_bot"""

# ================================================================
# 🧠 TEXTO DEEPSEEK PARA CURIOSIDADES (SIN hashtags en el prompt)
# ================================================================
def generar_texto_curiosidad(curiosidad):
    prompt = f"""Eres un divulgador científico experto en biología humana, nutrición y salud. Escribe un post CORTO y FASCINANTE para Facebook sobre: "{curiosidad['nombre']}".

🚨 REGLAS ESTRICTAS:
- ⚠️ PROHIBIDO mencionar: plantas medicinales, hierbas, remedios naturales, tés de hierbas, suplementos herbales.
- ✅ PERMITIDO: datos científicos, estudios, porcentajes, curiosidades anatómicas, efectos fisiológicos, ejercicios, alimentos, hormonas, neurotransmisores.
- Formato EXACTO con saltos de línea después de cada icono:
  Línea 1: 🧠 {curiosidad['nombre']}: [dato impactante en una línea]
  Línea 2: ✅ [dato científico 1 con número/porcentaje]
  Línea 3: ✅ [dato científico 2 con número/porcentaje]
  Línea 4: ✅ [dato científico 3 con número/porcentaje]
  Línea 5: 💡 Sabías que: [curiosidad adicional breve]
  Línea 6: ¿Quieres más datos fascinantes?
  Línea 7: ✨Pregunta gratis 24/7 👉 https://t.me/alex_xanax_bot
- Cada línea máx 60 caracteres.
- SIN líneas en blanco entre cada línea.
- Tono: educativo, fascinante, accesible pero riguroso.
- Incluye números, porcentajes o datos concretos.
- NO agregues hashtags (yo los agregaré después).

Ejemplo:
🧠 Tu cerebro usa el 20% de tu energía total.
✅ Pesa solo 1.4 kg pero consume 20% del oxígeno.
✅ Tiene 86 mil millones de neuronas conectadas.
✅ Genera electricidad para encender un foco.
💡 Sabías que: nunca descansa, ni dormido.
¿Quieres más datos fascinantes?
✨Pregunta gratis 24/7 👉 https://t.me/alex_xanax_bot
"""
    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.75, "max_tokens": 280}
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        texto = r.json()["choices"][0]["message"]["content"].strip()
        
        # Filtro: si menciona plantas, usar fallback
        palabras_prohibidas = ['manzanilla', 'lavanda', 'jengibre', 'té de', 'infusión de', 'hierba', 'planta medicinal', 'eucalipto', 'valeriana', 'romero', 'albahaca', 'remedio natural']
        if any(p in texto.lower() for p in palabras_prohibidas):
            print("⚠️ Texto contiene plantas. Usando fallback.")
            return generar_fallback_curiosidad(curiosidad)
        return texto
    except Exception as e:
        print(f"❌ Error en DeepSeek: {e}")
        return generar_fallback_curiosidad(curiosidad)

def generar_fallback_curiosidad(curiosidad):
    return f"""🧠 {curiosidad['nombre']}: datos que te sorprenderán.
✅ Tu cuerpo es una máquina perfecta.
✅ Cada célula tiene un propósito específico.
✅ La ciencia aún descubre nuevos secretos.
💡 Sabías que: tu cuerpo se renueva constantemente.
¿Quieres más datos fascinantes?
✨Pregunta gratis 24/7 👉 https://t.me/alex_xanax_bot"""

# ================================================================
# 🏷️ AGREGAR HASHTAGS + DISCLOSURE IA SIEMPRE AL FINAL
# ================================================================
def agregar_hashtags_al_final(texto, tipo):
    """Agrega hashtags consistentes + disclosure de IA al final del post."""
    # Quitar hashtags existentes
    texto = re.sub(r'#\w+', '', texto)
    
    # Limpiar líneas vacías excesivas
    texto = texto.strip()
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    
    # Hashtags según tipo
    if tipo == "hierba":
        hashtags = "\n\n#Herbolaria #SaludNatural #RemediosCaseros #Bienestar #MedicinaNatural"
    else:
        hashtags = "\n\n#Curiosidades #Ciencia #Salud #Bienestar #CuerpoHumano"
    
    # 🆕 Agregar disclosure de IA si está activado
    resultado = texto + hashtags
    if ACTIVAR_DISCLOSURE_IA:
        resultado += DISCLOSURE_TEXT
    
    return resultado

# ================================================================
# GENERAR IMAGEN CON AGNES AI
# ================================================================
def generar_imagen_agnes(prompt, tipo="hierba", width=1080, height=1350):
    prompt_limpio = prompt[:500]
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    
    # Negative prompt diferente según tipo
    if tipo == "curiosidad":
        negative = (
            "plants, herbs, leaves, flowers, fruits, vegetables, botanical, "
            "natural remedies, herbal medicine, tea leaves, foliage, "
            "deformed, blurry, low quality, text, watermark, logo, "
            "close-up face, portrait, ugly, grotesque, vintage, retro"
        )
    else:
        negative = (
            "deformed, blurry, low quality, text, watermark, logo, "
            "close-up face, portrait, ugly, grotesque, distorted"
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
            import time
            time.sleep(10)
    
    return None

# ================================================================
# ENVIAR A MAKE.COM
# ================================================================
def enviar_a_make(message, image_url):
    payload = {"message": message, "image_url": image_url, "timestamp": datetime.now().isoformat()}
    try:
        r = requests.post(MAKE_WEBHOOK_URL, json=payload, timeout=60)
        if r.status_code in [200, 201, 202]:
            print("✅ Enviado a Make.com correctamente")
            return True
        else:
            print(f"❌ Make respondió: {r.status_code} - {r.text}")
            return False
    except Exception as e:
        print(f"❌ Error conexión con Make: {e}")
        return False

# ================================================================
# MAIN
# ================================================================
def main():
    print("🌿 Iniciando Bot de Herbolaria + Curiosidades (Vertical 1080x1350)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return
    
    # Detectar qué tipo de publicación toca
    tipo = detectar_tipo_publicacion()
    print(f"🎯 Tipo de publicación detectado: {tipo.upper()}")
    
    estado = cargar_estado()
    
    if tipo == "hierba":
        # Publicación de hierba (flujo original)
        catalogo = cargar_catalogo_hierbas()
        item = obtener_item_no_repetido(catalogo, estado, "hierbas")
        print(f"🌱 Hierba del día: {item['nombre']}")
        print(f"📊 Publicadas: {len(estado['publicadas']['hierbas'])} / {len(catalogo)}")
        
        print("📝 Generando texto con DeepSeek...")
        texto = generar_texto_hierba(item)
        texto = agregar_hashtags_al_final(texto, "hierba")  # 🆕 Hashtags + disclosure
        print("✅ Texto generado con hashtags y disclosure")
        
        print("🎨 Generando prompt de imagen...")
        prompt_img = generar_prompt_imagen_hierba(item)
        
        image_url = generar_imagen_agnes(prompt_img, tipo="hierba", width=1080, height=1350)
        
        nombre_item = item["nombre"]
        tipo_registro = "hierbas"
    
    else:
        # Publicación de curiosidad
        catalogo = cargar_catalogo_curiosidades()
        item = obtener_item_no_repetido(catalogo, estado, "curiosidades")
        print(f"🧠 Curiosidad del momento: {item['nombre']}")
        print(f"📊 Publicadas: {len(estado['publicadas']['curiosidades'])} / {len(catalogo)}")
        
        print("📝 Generando texto científico con DeepSeek...")
        texto = generar_texto_curiosidad(item)
        texto = agregar_hashtags_al_final(texto, "curiosidad")  # 🆕 Hashtags + disclosure
        print("✅ Texto científico generado con hashtags y disclosure")
        
        print("🎨 Generando prompt de imagen científica...")
        prompt_img = generar_prompt_imagen_curiosidad(item)
        
        image_url = generar_imagen_agnes(prompt_img, tipo="curiosidad", width=1080, height=1350)
        
        nombre_item = item["nombre"]
        tipo_registro = "curiosidades"
    
    print(f"📝 Prompt: {prompt_img[:150]}...")
    
    # Enviar a Make
    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviado = enviar_a_make(texto, None)
    else:
        print(f"✅ Imagen generada: {image_url}")
        enviado = enviar_a_make(texto, image_url)
    
    # Guardar estado solo si se envió correctamente
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

import requests
import random
import os
import json
import re
from datetime import datetime

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

# ================================================================
# CARGAR CATÁLOGO DESDE JSON
# ================================================================
def cargar_catalogo():
    try:
        with open(CATALOGO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        print("⚠️ No se pudo cargar el catálogo. Usando lista de respaldo.")
        return [{"nombre": "Manzanilla", "categoria": "hierba", "descripcion": "Flor blanca y amarilla, usada en infusiones", "caracteristicas_visuales": "Flores blancas con centro amarillo"}]

# ================================================================
# ESTADO
# ================================================================
def cargar_estado():
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"publicadas": []}

def guardar_estado(estado):
    try:
        with open(ESTADO_FILE, "w", encoding="utf-8") as f:
            json.dump(estado, f, indent=2, ensure_ascii=False)
        print(f"✅ Estado guardado correctamente en {ESTADO_FILE}")
    except Exception as e:
        print(f"❌ Error guardando estado: {e}")

def obtener_ingrediente_no_repetido(catalogo, estado):
    publicadas = set(p["nombre"] for p in estado["publicadas"])
    disponibles = [item for item in catalogo if item["nombre"] not in publicadas]
    if not disponibles:
        print("🔄 Todos los ingredientes ya han sido publicados. Reiniciando historial.")
        estado["publicadas"] = []
        guardar_estado(estado)
        disponibles = catalogo
    return random.choice(disponibles)

# ================================================================
# GENERAR PROMPT DE IMAGEN OPTIMIZADO PARA FACEBOOK (Vertical)
# ================================================================
def generar_prompt_imagen(ingrediente):
    """
    Genera un prompt detallado para imágenes verticales (1080x1350) 
    optimizado para Facebook móvil, con colores vibrantes y estilo profesional.
    """
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
        # Refuerzo para Facebook vertical
        prompt += " Vertical format 4:5, professional product photography, hyperrealistic, 4k, ultra detailed, perfect for Facebook feed, natural lighting, vibrant colors."
        return prompt
    except Exception as e:
        print(f"❌ Error generando prompt de imagen: {e}")
        return f"Fresh {ingrediente['nombre']} close-up botanical photography, natural light, wooden table background, photorealistic, 4k, vertical format 4:5 for social media"

# ================================================================
# GENERAR TEXTO CON DEEPSEEK (Optimizado para Facebook)
# ================================================================
def generar_texto_deepseek(ingrediente):
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
  Línea 8: [3 hashtags relevantes]

- Cada línea DEBE ser corta (máx 60 caracteres).
- SIN líneas en blanco entre cada línea.
- Usa un tono cálido, cercano y convincente.
- Menciona beneficios reales y prácticos.

Formato EXACTO:
🌿 Jengibre: la raíz que enciende tu vitalidad.
✅ Alivia la inflamación y el dolor muscular.
✅ Fortalece tu sistema inmune.
✅ Acelera la digestión.
🍵 Tip: Añade 3 rodajas a tu agua caliente.
¿Quieres saber qué producto es ideal para ti? 
✨¡Pregunta gratis 24/7! 👉 https://t.me/alex_xanax_bot
#Jengibre #SaludNatural #RemediosCaseros
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
✨¡Pregunta gratis 24/7! 👉 https://t.me/alex_xanax_bot
#SaludNatural #Herbolaria #Bienestar"""

# ================================================================
# GENERAR IMAGEN CON AGNES AI (VERTICAL 1080x1350)
# ================================================================
def generar_imagen_agnes(prompt, width=1080, height=1350):
    prompt_limpio = prompt[:500]
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": prompt_limpio,
        "width": width,
        "height": height,
        "num_images": 1
    }
    
    try:
        print("🎨 Generando imagen vertical para Facebook...")
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            data = response.json()
            image_url = data['data'][0]['url']
            print("✅ Imagen generada (1080x1350)")
            return image_url
        else:
            print(f"❌ Error en Agnes AI: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error de conexión con Agnes AI: {e}")
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
        print(f"❌ Error de conexión con Make: {e}")
        return False

# ================================================================
# MAIN
# ================================================================
def main():
    print("🌿 Iniciando Bot de Herbolaria (Vertical 1080x1350)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return
    
    catalogo = cargar_catalogo()
    estado = cargar_estado()
    
    ingrediente = obtener_ingrediente_no_repetido(catalogo, estado)
    print(f"🌱 Ingrediente del día: {ingrediente['nombre']}")
    print(f"📊 Publicados hasta ahora: {len(estado['publicadas'])} / {len(catalogo)}")
    
    print("📝 Generando texto con DeepSeek...")
    texto = generar_texto_deepseek(ingrediente)
    print("✅ Texto generado")
    
    print("🎨 Generando prompt de imagen vertical...")
    prompt_img = generar_prompt_imagen(ingrediente)
    print(f"📝 Prompt generado: {prompt_img[:150]}...")
    
    image_url = generar_imagen_agnes(prompt_img, width=1080, height=1350)
    
    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviar_a_make(texto, None)
    else:
        print(f"✅ Imagen vertical generada: {image_url}")
        enviar_a_make(texto, image_url)
    
    estado["publicadas"].append({
        "nombre": ingrediente["nombre"],
        "fecha": datetime.now().isoformat()
    })
    guardar_estado(estado)
    
    print(f"🎉 ¡Publicación enviada para {ingrediente['nombre']}!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

import requests
import random
import os
import json
from datetime import datetime

# ================================================================
# CONFIGURACIÓN (variables desde GitHub Secrets)
# ================================================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
AGNES_API_KEY = os.getenv("AGNES_API_KEY")

# ================================================================
# ARCHIVO DE ESTADO (guarda historial completo)
# ================================================================
ESTADO_FILE = "estado_herbolaria.json"

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

def obtener_hierba_no_repetida(hierbas, estado):
    publicadas = set(p["nombre"] for p in estado["publicadas"])
    disponibles = [h for h in hierbas if h["nombre"] not in publicadas]
    if not disponibles:
        print("🔄 Todas las hierbas ya han sido publicadas. Reiniciando historial.")
        estado["publicadas"] = []
        guardar_estado(estado)
        disponibles = hierbas
    return random.choice(disponibles)

# ================================================================
# BASE DE DATOS DE HIERBAS
# ================================================================
HIERBAS = [
    {
        "nombre": "Manzanilla",
        "nombre_cientifico": "Matricaria chamomilla",
        "prompt_img": (
            "Fresh chamomile flower with white petals and golden yellow center, "
            "close-up botanical photography on wooden table, next to a cup of "
            "chamomile tea with steam rising, soft natural window light, "
            "photorealistic, professional herbal brand photo, 8k, ultra detailed"
        ),
    },
    {
        "nombre": "Lavanda",
        "nombre_cientifico": "Lavandula angustifolia",
        "prompt_img": (
            "Fresh lavender plant with vibrant purple flower spikes and green stems, "
            "close-up botanical photography in morning light, bundle of lavender, "
            "soft natural light, photorealistic, professional herbal brand photo, 8k"
        ),
    },
    {
        "nombre": "Menta",
        "nombre_cientifico": "Mentha piperita",
        "prompt_img": (
            "Fresh mint leaves with vibrant green serrated edges, dew drops on leaves, "
            "close-up botanical photography, bright natural light, glass of mint tea "
            "in blurred background, photorealistic, professional herbal brand photo, 8k"
        ),
    },
    {
        "nombre": "Jengibre",
        "nombre_cientifico": "Zingiber officinale",
        "prompt_img": (
            "Fresh ginger root knobby beige rhizome, sliced pieces showing interior, "
            "small green shoots, close-up botanical photography on wooden cutting board, "
            "warm natural light, photorealistic, professional herbal brand photo, 8k"
        ),
    },
    {
        "nombre": "Cúrcuma",
        "nombre_cientifico": "Curcuma longa",
        "prompt_img": (
            "Fresh turmeric root cut open showing bright orange flesh, small bowl of "
            "golden turmeric powder, close-up botanical photography, warm natural light, "
            "photorealistic, professional herbal brand photo, 8k"
        ),
    },
    {
        "nombre": "Eucalipto",
        "nombre_cientifico": "Eucalyptus globulus",
        "prompt_img": (
            "Fresh eucalyptus branch with round silver-green aromatic leaves, "
            "close-up botanical photography, soft natural light, photorealistic, "
            "professional herbal brand photo, 8k"
        ),
    },
    {
        "nombre": "Valeriana",
        "nombre_cientifico": "Valeriana officinalis",
        "prompt_img": (
            "Fresh valerian plant with small white-pink flower clusters and green "
            "feathery foliage, close-up botanical photography, soft evening light, "
            "photorealistic, professional herbal brand photo, 8k"
        ),
    },
]

# ================================================================
# GENERADOR DE TEXTO CON DEEPSEEK
# ================================================================
def generar_texto_deepseek(hierba):
    prompt = f"""Eres un experto en herbolaria y redacción para redes sociales.
Escribe un post CORTO y ORDENADO para Facebook sobre la {hierba['nombre']}.

REGLAS ESTRICTAS:
- Usa EXACTAMENTE este formato con saltos de línea después de cada icono (NO uses doble espacio):
  Línea 1: 🌿 [Nombre]: [frase gancho de una línea]
  Línea 2: ✅ [beneficio 1 corto]
  Línea 3: ✅ [beneficio 2 corto]
  Línea 4: ✅ [beneficio 3 corto]
  Línea 5: 🍵 Tip: [consejo corto de una línea]
  Línea 6: ¿Quieres saber qué producto es ideal para ti? 
  Línea 7: ✨¡Pregunta gratis 24/7! 👉 https://t.me/alex_xanax_bot
  Línea 8: [3 hashtags relevantes separados por espacio]

- Cada línea DEBE ser corta (máx 60 caracteres, ideal para móvil).
- SIN líneas en blanco entre cada línea.
- El texto debe ser directo y atractivo.

Formato EXACTO (copiar):
🌿 Jengibre: la raíz que enciende tu vitalidad.
✅ Alivia la inflamación y el dolor muscular.
✅ Fortalece tu sistema inmune contra resfriados.
✅ Acelera la digestión eliminando la pesadez.
🍵 Tip: Añade 3 rodajas frescas a tu agua caliente con limón.
¿Quieres saber qué producto es ideal para ti? 
✨¡Pregunta gratis 24/7! 👉 https://t.me/alex_xanax_bot
#Jengibre #SaludNatural #RemediosCaseros

No uses puntos y aparte, solo los saltos de línea indicados.
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
        return f"""🌿 {hierba['nombre']}: Tu aliado natural.
✅ Alivia síntomas de resfriado.
✅ Descongestiona vías respiratorias.
✅ Calma la tos y la irritación.
🍵 Tip: Prepara una infusión caliente.
¿Quieres saber qué producto es ideal para ti? 
✨¡Pregunta gratis 24/7! 👉 https://t.me/alex_xanax_bot
#SaludNatural #Herbolaria #Bienestar"""

# ================================================================
# GENERADOR DE IMAGEN CON AGNES AI
# ================================================================
def generar_imagen_agnes(prompt):
    url = "https://apihub.agnes-ai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {AGNES_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": "agnes-image-2.1-flash", "prompt": prompt, "width": 1024, "height": 1024, "num_images": 1}
    
    try:
        print("🎨 Generando imagen con Agnes AI...")
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        if response.status_code == 200:
            data = response.json()
            image_url = data['data'][0]['url']
            print("✅ Imagen generada con Agnes AI")
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
    print("🌿 Iniciando Bot de Herbolaria")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL, AGNES_API_KEY]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return
    
    estado = cargar_estado()
    hierba = obtener_hierba_no_repetida(HIERBAS, estado)
    print(f"🌱 Hierba del día: {hierba['nombre']}")
    print(f"📊 Publicadas hasta ahora: {len(estado['publicadas'])} / {len(HIERBAS)}")
    
    print("📝 Generando texto con DeepSeek...")
    texto = generar_texto_deepseek(hierba)
    print("✅ Texto generado")
    
    image_url = generar_imagen_agnes(hierba["prompt_img"])
    
    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviar_a_make(texto, None)
    else:
        print(f"✅ Imagen generada: {image_url}")
        enviar_a_make(texto, image_url)
    
    estado["publicadas"].append({
        "nombre": hierba["nombre"],
        "fecha": datetime.now().isoformat()
    })
    guardar_estado(estado)
    
    print(f"🎉 ¡Publicación enviada para {hierba['nombre']}!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

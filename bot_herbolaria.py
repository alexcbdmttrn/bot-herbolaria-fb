import requests
import base64
import random
import os
import json
from datetime import datetime
from urllib.parse import quote

# ================================================================
# CONFIGURACIÓN (variables desde GitHub Secrets)
# ================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL")
TELEGRAM_BOT_LINK = os.getenv("TELEGRAM_BOT_LINK", "https://t.me/tu_bot")

# ================================================================
# BASE DE DATOS DE HIERBAS (con prompts en inglés curados)
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
    """Pide a DeepSeek que escriba un post atractivo sobre la hierba"""
    
    prompt = f"""Eres un experto en herbolaria tradicional mexicana.
Escribe un post breve y atractivo para Facebook sobre la {hierba['nombre']} 
(nombre científico: {hierba['nombre_cientifico']}).

Requisitos:
- Máximo 200 palabras
- Usa emojis relacionados con plantas y bienestar 🌿
- Menciona 3 beneficios principales de forma natural
- Da un tip práctico de cómo usarla en casa
- Al final, invita a probar nuestro asistente virtual por Telegram 
  para obtener más información personalizada: {TELEGRAM_BOT_LINK}
- Incluye 3 hashtags relevantes al final
- Tono cercano, educativo y cálido
- Escribe en español

Formato: texto directo, sin título ni encabezados."""

    url = "https://api.deepseek.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.8,
        "max_tokens": 400
    }
    
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"❌ Error en DeepSeek: {e}")
        # Texto de respaldo
        return f"""🌿 {hierba['nombre'].upper()} ({hierba['nombre_cientifico']})

Descubre los beneficios de esta maravillosa planta medicinal.

✨ Conoce más con nuestro asistente virtual: {TELEGRAM_BOT_LINK}

#Herbolaria #PlantasMedicinales #BienestarNatural"""

# ================================================================
# GENERADOR DE IMAGEN CON GEMINI (NANO BANANA)
# ================================================================
def generar_imagen_gemini(prompt):
    """Genera imagen con Gemini 2.5 Flash Image"""
    
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash-image:generateContent?key={GEMINI_API_KEY}"
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    try:
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        
        parts = data["candidates"][0]["content"]["parts"]
        for part in parts:
            if "inlineData" in part:
                return base64.b64decode(part["inlineData"]["data"])
        
        raise Exception("Gemini no devolvió imagen en la respuesta")
    
    except Exception as e:
        print(f"❌ Error en Gemini: {e}")
        return None

# ================================================================
# SUBIR A IMGBB (para obtener URL pública)
# ================================================================
def subir_a_imgbb(img_bytes, nombre):
    """Sube la imagen y devuelve la URL pública"""
    
    try:
        r = requests.post(
            "https://api.imgbb.com/1/upload",
            data={"key": IMGBB_API_KEY, "name": nombre},
            files={"image": (f"{nombre}.jpg", img_bytes, "image/jpeg")},
            timeout=90
        )
        r.raise_for_status()
        data = r.json()
        
        if data.get("success"):
            return data["data"]["url"]
        else:
            print(f"❌ imgbb falló: {data}")
            return None
    
    except Exception as e:
        print(f"❌ Error subiendo a imgbb: {e}")
        return None

# ================================================================
# ENVIAR A MAKE.COM
# ================================================================
def enviar_a_make(message, image_url):
    """Envía el paquete completo al webhook de Make"""
    
    payload = {
        "message": message,
        "image_url": image_url,
        "timestamp": datetime.now().isoformat()
    }
    
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
    
    # Validar que todas las llaves existan
    if not all([GEMINI_API_KEY, IMGBB_API_KEY, DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return
    
    # Elegir hierba del día (aleatoria)
    hierba = random.choice(HIERBAS)
    print(f"🌱 Hierba del día: {hierba['nombre']}")
    
    # Paso 1: Generar texto con DeepSeek
    print("📝 Generando texto con DeepSeek...")
    texto = generar_texto_deepseek(hierba)
    print("✅ Texto generado")
    
    # Paso 2: Generar imagen con Gemini
    print("🎨 Generando imagen con Gemini...")
    img_bytes = generar_imagen_gemini(hierba["prompt_img"])
    
    if img_bytes is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviar_a_make(texto, None)
        return
    
    print("✅ Imagen generada")
    
    # Paso 3: Subir a imgbb
    print("☁️ Subiendo a imgbb...")
    nombre_archivo = f"hierba_{hierba['nombre'].lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    image_url = subir_a_imgbb(img_bytes, nombre_archivo)
    
    if image_url is None:
        print("⚠️ No se pudo subir imagen. Enviando solo texto.")
        enviar_a_make(texto, None)
        return
    
    print(f"✅ Imagen en: {image_url}")
    
    # Paso 4: Enviar a Make.com
    print("📤 Enviando a Make.com...")
    exito = enviar_a_make(texto, image_url)
    
    if exito:
        print(f"🎉 ¡Publicación enviada para {hierba['nombre']}!")
    else:
        print("❌ Falló el envío a Make")

if __name__ == "__main__":
    main()

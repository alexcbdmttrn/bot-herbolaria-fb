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
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")  # <-- NUEVA

# ================================================================
# BASE DE DATOS DE HIERBAS (con prompts en inglés)
# ================================================================
HIERBAS = [
    {
        "nombre": "Manzanilla",
        "nombre_cientifico": "Matricaria chamomilla",
        "prompt_img": "Fresh chamomile flower with white petals and golden yellow center, close-up botanical photography on wooden table, next to a cup of chamomile tea with steam rising, soft natural window light, photorealistic, professional herbal brand photo, 8k, ultra detailed",
    },
    {
        "nombre": "Lavanda",
        "nombre_cientifico": "Lavandula angustifolia",
        "prompt_img": "Fresh lavender plant with vibrant purple flower spikes and green stems, close-up botanical photography in morning light, bundle of lavender, soft natural light, photorealistic, professional herbal brand photo, 8k",
    },
    {
        "nombre": "Menta",
        "nombre_cientifico": "Mentha piperita",
        "prompt_img": "Fresh mint leaves with vibrant green serrated edges, dew drops on leaves, close-up botanical photography, bright natural light, glass of mint tea in blurred background, photorealistic, professional herbal brand photo, 8k",
    },
    {
        "nombre": "Jengibre",
        "nombre_cientifico": "Zingiber officinale",
        "prompt_img": "Fresh ginger root knobby beige rhizome, sliced pieces showing interior, small green shoots, close-up botanical photography on wooden cutting board, warm natural light, photorealistic, professional herbal brand photo, 8k",
    },
    {
        "nombre": "Cúrcuma",
        "nombre_cientifico": "Curcuma longa",
        "prompt_img": "Fresh turmeric root cut open showing bright orange flesh, small bowl of golden turmeric powder, close-up botanical photography, warm natural light, photorealistic, professional herbal brand photo, 8k",
    },
    {
        "nombre": "Eucalipto",
        "nombre_cientifico": "Eucalyptus globulus",
        "prompt_img": "Fresh eucalyptus branch with round silver-green aromatic leaves, close-up botanical photography, soft natural light, photorealistic, professional herbal brand photo, 8k",
    },
    {
        "nombre": "Valeriana",
        "nombre_cientifico": "Valeriana officinalis",
        "prompt_img": "Fresh valerian plant with small white-pink flower clusters and green feathery foliage, close-up botanical photography, soft evening light, photorealistic, professional herbal brand photo, 8k",
    },
]

# ================================================================
# GENERADOR DE TEXTO CON DEEPSEEK
# ================================================================
def generar_texto_deepseek(hierba):
    prompt = f"""Eres un experto en herbolaria tradicional mexicana.
Escribe un post breve y atractivo para Facebook sobre la {hierba['nombre']} 
(nombre científico: {hierba['nombre_cientifico']}).

Requisitos:
- Máximo 200 palabras
- Usa emojis relacionados con plantas y bienestar 🌿
- Menciona 3 beneficios principales de forma natural
- Da un tip práctico de cómo usarla en casa
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
        return f"""🌿 {hierba['nombre'].upper()} ({hierba['nombre_cientifico']})

Descubre los beneficios de esta maravillosa planta medicinal.

#Herbolaria #PlantasMedicinales #BienestarNatural"""

# ================================================================
# GENERADOR DE IMAGEN CON REPLICATE (FLUX)
# ================================================================
def generar_imagen_replicate(prompt):
    """Genera imagen usando Replicate con modelo Flux"""
    
    url = "https://api.replicate.com/v1/predictions"
    
    headers = {
        "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "version": "black-forest-labs/flux-schnell",
        "input": {
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
            "num_outputs": 1,
        }
    }
    
    try:
        # Iniciar la predicción
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        
        # Obtener la URL de la predicción para monitorear
        predict_url = data["urls"]["get"]
        
        # Esperar a que termine
        import time
        while True:
            status_r = requests.get(predict_url, headers=headers)
            status_r.raise_for_status()
            status_data = status_r.json()
            
            if status_data["status"] == "succeeded":
                # Obtener la URL de la imagen generada
                image_url = status_data["output"][0]
                return image_url
            elif status_data["status"] == "failed":
                print(f"❌ Replicate falló: {status_data.get('error', 'Error desconocido')}")
                return None
            
            print("⏳ Generando imagen... esperando 2 segundos")
            time.sleep(2)
            
    except Exception as e:
        print(f"❌ Error en Replicate: {e}")
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
    if not all([DEEPSEEK_API_KEY, MAKE_WEBHOOK_URL, REPLICATE_API_TOKEN]):
        print("❌ Faltan variables de entorno. Revisa los Secrets de GitHub.")
        return
    
    # Elegir hierba del día (aleatoria)
    hierba = random.choice(HIERBAS)
    print(f"🌱 Hierba del día: {hierba['nombre']}")
    
    # Paso 1: Generar texto con DeepSeek
    print("📝 Generando texto con DeepSeek...")
    texto = generar_texto_deepseek(hierba)
    print("✅ Texto generado")
    
    # Paso 2: Generar imagen con Replicate
    print("🎨 Generando imagen con Replicate (Flux)...")
    image_url = generar_imagen_replicate(hierba["prompt_img"])
    
    if image_url is None:
        print("⚠️ No se pudo generar imagen. Enviando solo texto.")
        enviar_a_make(texto, None)
        return
    
    print(f"✅ Imagen generada: {image_url}")
    
    # Paso 3: Enviar a Make.com
    print("📤 Enviando a Make.com...")
    exito = enviar_a_make(texto, image_url)
    
    if exito:
        print(f"🎉 ¡Publicación enviada para {hierba['nombre']}!")
    else:
        print("❌ Falló el envío a Make")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

name: Bot Herbolaria - Publicación

on:
  schedule:
    - cron: '0 13 * * *'   # 7:00 AM CDMX (invierno) / 8:00 AM (verano)
    - cron: '0 21 * * *'   # 3:00 PM CDMX (siempre)
  workflow_dispatch:

jobs:
  publicar:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repositorio
        uses: actions/checkout@v4

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Instalar dependencias
        run: |
          pip install requests

      - name: Ejecutar bot
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
          MAKE_WEBHOOK_URL: ${{ secrets.MAKE_WEBHOOK_URL }}
          AGNES_API_KEY: ${{ secrets.AGNES_API_KEY }}
        run: python bot_herbolaria.py

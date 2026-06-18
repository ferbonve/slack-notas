#!/bin/bash
# Setup script para el environment de Claude Code on the web (claude.ai/code).
# Corre una vez al crear el ambiente y queda cacheado.
#
# Instala los paquetes directo (sin -r requirements.txt) para no depender del
# directorio de trabajo: el setup script puede correr fuera de la raíz del repo.
set -e
pip install \
  "slack_sdk>=3.27.0" \
  "python-dotenv>=1.0.0" \
  "google-api-python-client>=2.0.0" \
  "google-auth>=2.0.0" \
  "google-auth-oauthlib>=1.0.0"
echo "Dependencias instaladas."

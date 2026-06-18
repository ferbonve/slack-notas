#!/bin/bash
# Setup script para el environment de Claude Code on the web (claude.ai/code).
# Corre una vez al crear el ambiente y queda cacheado (no re-corre en cada rutina).
# Instala las dependencias de Python del proyecto.
set -e
pip install -r requirements.txt
echo "Dependencias instaladas."

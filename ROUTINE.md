# Rutina: Slack → notas en Drive

Convierte los mensajes de un canal de Slack en notas organizadas en Google
Drive. Pensada para correr como **rutina de Claude en la nube**, pero el flujo
completo se puede probar igual desde tu PC (mismas credenciales del `.env`).

## Flujo (4 pasos, en orden)

1. `python main.py` — el extractor trae los mensajes nuevos de Slack y los
   agrega al CSV `notas_slack.csv` en Drive (dedup por `ts`).
2. `python sync_pull.py` — baja a `./trabajo/` el CSV y la carpeta de notas
   existente (`trabajo/notas/AAAA-MM-DD_*.md`, archivos sueltos sin subcarpetas).
3. **Claude** procesa `./trabajo/` siguiendo `system_prompt.md`: lee el CSV,
   ignora los `ts` ya presentes en las notas y crea/actualiza los `.md` locales.
4. `python sync_push.py` — sube las notas nuevas/modificadas de vuelta a Drive.

`./trabajo/` es una copia local temporal (está en `.gitignore`); la fuente de
verdad siempre es Drive.

## Probar manualmente (local)

```bash
python main.py
python sync_pull.py
# (acá Claude aplica system_prompt.md sobre ./trabajo/)
python sync_push.py
```

## Correr en la nube (sin la PC prendida)

La rutina se programa en **Claude Code on the web** (claude.ai/code → Routines):
corre en la nube de Anthropic con tu suscripción, en horario fijo. Los pasos
exactos (conectar GitHub, setup script, variables de entorno, prompt y schedule)
están en **[GUIA-NUBE.md](GUIA-NUBE.md)**.

Variables de entorno que necesita (las del `.env`, que **no** se commitean): ver
plantilla en `.env.example`.

# Rutina: Slack → notas en Drive

Convierte los mensajes de un canal de Slack en notas organizadas en Google
Drive. Pensada para correr como **rutina de Claude en la nube**, pero el flujo
completo se puede probar igual desde tu PC (mismas credenciales del `.env`).

## Flujo (4 pasos, en orden)

1. `python main.py` — el extractor trae los mensajes nuevos de Slack y los
   agrega al CSV `notas_slack.csv` en Drive (dedup por `ts`).
2. `python sync_pull.py` — baja a `./trabajo/` el CSV y la carpeta de notas
   existente (`trabajo/notas/AAAA-MM-DD/*.md`).
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

## Convertir en rutina programada (cuando esté validado)

Crear una scheduled routine de Claude Code sobre este repo, con este prompt:

> Sos la rutina de notas de Slack. Ejecutá en orden, sin saltarte pasos:
> 1. `python main.py`
> 2. `python sync_pull.py`
> 3. Procesá las notas siguiendo EXACTAMENTE `system_prompt.md`. El CSV es
>    `trabajo/notas_slack.csv` y la carpeta de notas es `trabajo/notas/` (las
>    subcarpetas por día van ahí adentro). Creá/actualizá los `.md` en local.
> 4. `python sync_push.py`
>
> Al terminar, reportá cuántos mensajes nuevos procesaste y cuántas notas
> creaste o actualizaste.

La rutina necesita estas variables de entorno (las del `.env`, que **no** se
commitean) cargadas como secrets: `SLACK_TOKEN`, `CHANNEL_ID`,
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`,
`DRIVE_FOLDER_ID`, `DRIVE_CSV_NOMBRE`.

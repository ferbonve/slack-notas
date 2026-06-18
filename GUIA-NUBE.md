# Guía: correr la rutina en la nube (Claude Code on the web)

Esta rutina corre en la nube de Anthropic con tu suscripción de Claude —no hace
falta tener la PC prendida—. Se configura desde **claude.ai/code → Routines**.

> Requiere plan Pro / Max / Team / Enterprise con Claude Code on the web.

## Paso a paso

### 1. Conectar GitHub
Entrá a **https://claude.ai/code** y completá el onboarding conectando tu cuenta
de GitHub (o corré `/web-setup` desde el CLI). Tiene que poder ver el repo
privado `github.com/ferbonve/slack-notas`.

### 2. Crear la rutina
Andá a **https://claude.ai/code/routines → New routine** y completá:

- **Repository:** `ferbonve/slack-notas` (rama `main`).
- **Trigger:** `Schedule` → diario (elegí el horario en tu zona; ej. ~23:00).
- **Prompt:** pegá el de la sección "Prompt de la rutina" más abajo.

### 3. Environment — Setup script (dependencias)
En el environment de la rutina, en **Setup script**, pegá:

```bash
pip install -r requirements.txt
```

(Corre una vez y queda cacheado. El sandbox ya trae Python, pip y red con acceso
"Trusted" que alcanza a Slack, Google Drive y PyPI.)

### 4. Environment — Variables (los secretos del .env)
En **Environment variables** cargá estas claves con tus valores reales (formato
`.env`, una por línea). Son las mismas del `.env` local; **no** van al repo.

```
SLACK_TOKEN=xoxb-...
CHANNEL_ID=C0BB3CVCAQG
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REFRESH_TOKEN=...
DRIVE_FOLDER_ID=1Gg_64_oagQ-DSr90tk01fMGubrkKdRkE
DRIVE_CSV_NOMBRE=notas_slack.csv
NOTAS_CARPETA_DRIVE=notas
```

> Nota: hoy el store de variables no está encriptado por-secreto (quien pueda
> editar el environment las ve). Para un proyecto personal está bien.

El código las toma directo de `os.environ` (si no hay `.env`, `load_dotenv`
simplemente no hace nada), así que funciona igual en la nube.

### 5. Probar
Tocá **Run now** para una corrida de prueba (las corridas one-off no cuentan
contra tu límite diario de rutinas). Abrí el run, revisá el transcript y validá
en tu Drive que las notas se crearon/actualizaron. Si anda, ya queda corriendo
en el horario elegido.

## Prompt de la rutina

```
Sos la rutina automática "Slack → notas en Drive". Trabajás en la raíz de este
repo, que ya tiene las dependencias instaladas y las credenciales como variables
de entorno. Ejecutá EN ORDEN y frená si un paso falla (no sigas con los siguientes):

1. `python main.py` — extrae los mensajes nuevos de Slack y los agrega al CSV
   `notas_slack.csv` en Google Drive (dedup por `ts`).
2. `python sync_pull.py` — baja a `./trabajo/` el CSV (`trabajo/notas_slack.csv`)
   y la carpeta de notas existente (`trabajo/notas/AAAA-MM-DD/*.md`).
3. Aplicá EXACTAMENTE las instrucciones de `system_prompt.md` sobre esos archivos:
   juntá los `ts` que ya están en el frontmatter de las notas existentes; del CSV
   procesá SOLO los `ts` que no estén en ese conjunto, en orden cronológico. Para
   cada mensaje nuevo usá la carpeta del campo `fecha` DEL MENSAJE, asigná categoría
   (hashtag → contenido: Compras / miscellaneous / Meditations), y fusioná con una
   nota existente del MISMO día si es claramente el mismo ítem (sumando su `ts` al
   frontmatter y regenerando lo que está entre `<!-- AUTO:INICIO -->` y
   `<!-- AUTO:FIN -->`); si no, creá una nota nueva. NUNCA toques nada fuera de las
   marcas AUTO ni reproceses un `ts` ya presente. Limpiá el texto hablado al redactar.
4. `python sync_push.py` — sube las notas nuevas/modificadas a Drive.

Al terminar informá: cuántos mensajes nuevos trajo el extractor y cuántas notas
creaste vs. actualizaste/fusionaste.
```

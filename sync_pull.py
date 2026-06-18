"""
Paso 2 de la rutina: baja de Drive todo lo que Claude necesita para trabajar.

Deja en ./trabajo/ :
  - notas_slack.csv        (el CSV que dejo el extractor, main.py)
  - notas/AAAA-MM-DD/*.md  (las notas ya existentes, para no duplicar)

Claude despues procesa esa carpeta local siguiendo system_prompt.md y al final
se sube con sync_push.py. Corre SIEMPRE despues de main.py.
"""

from pathlib import Path

from modules.config import Config
from modules.drive_client import drive_csv
from modules.notas_drive import NotasDrive

TRABAJO = Path(__file__).resolve().parent / "trabajo"


def main() -> None:
    cfg = Config()
    if not cfg.validar():
        return

    TRABAJO.mkdir(parents=True, exist_ok=True)

    contenido = drive_csv.descargar_csv()
    (TRABAJO / cfg.drive_csv_nombre).write_text(contenido, encoding="utf-8")

    n = NotasDrive(cfg).bajar(TRABAJO / "notas")
    print(
        f"Bajado a {TRABAJO}: CSV ({len(contenido)} bytes) + {n} nota(s) existente(s)."
    )


if __name__ == "__main__":
    main()

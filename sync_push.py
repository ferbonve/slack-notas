"""
Paso 4 (ultimo) de la rutina: sube a Drive las notas que Claude creo/actualizo.

Toma ./trabajo/notas/AAAA-MM-DD_*.md y los sube sueltos (sin subcarpetas)
directo a DRIVE_FOLDER_ID. Corre DESPUES de que Claude termino de aplicar
system_prompt.md sobre la carpeta local.
"""

from pathlib import Path

from modules.config import Config
from modules.notas_drive import NotasDrive

TRABAJO = Path(__file__).resolve().parent / "trabajo"


def main() -> None:
    cfg = Config()
    if not cfg.validar():
        return

    carpeta = TRABAJO / "notas"
    if not carpeta.exists():
        print(f"No existe {carpeta}; no hay notas para subir.")
        return

    n = NotasDrive(cfg).subir(carpeta)
    print(f"Subidas/actualizadas {n} nota(s) en Drive.")


if __name__ == "__main__":
    main()

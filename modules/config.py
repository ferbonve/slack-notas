"""
Carga y valida la configuracion desde el archivo .env

Responsabilidad unica: leer los secretos/ajustes y avisar si falta algo.
Ningun otro modulo deberia leer variables de entorno; todos piden la config aca.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Carpeta raiz del proyecto (donde esta este paquete)
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Agrupa todos los valores de configuracion en un solo objeto."""

    def __init__(self) -> None:
        load_dotenv(BASE_DIR / ".env")
        self.slack_token = os.environ.get("SLACK_TOKEN", "")
        self.channel_id = os.environ.get("CHANNEL_ID", "")
        carpeta = os.environ.get("CARPETA_NOTAS", "notas")
        # Soporta tanto ruta relativa (al proyecto) como absoluta (ej: tu vault).
        ruta = Path(carpeta)
        self.notas_dir = ruta if ruta.is_absolute() else BASE_DIR / ruta

        # --- Google Drive (para guardar/leer el CSV via API) ---
        self.google_client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
        self.google_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
        self.google_refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
        self.drive_csv_nombre = os.environ.get("DRIVE_CSV_NOMBRE", "notas_slack.csv")
        self.drive_folder_id = os.environ.get("DRIVE_FOLDER_ID", "").strip()

    def validar(self) -> bool:
        """Devuelve True si la config esta completa; si no, explica que falta."""
        if not self.slack_token or self.slack_token.startswith("xoxb-PEGAR"):
            print("ERROR: falta SLACK_TOKEN en el archivo .env")
            return False
        if not self.channel_id or self.channel_id.startswith("PEGAR"):
            print("ERROR: falta CHANNEL_ID en el archivo .env")
            return False
        faltan_drive = [
            nombre
            for nombre, valor in (
                ("GOOGLE_CLIENT_ID", self.google_client_id),
                ("GOOGLE_CLIENT_SECRET", self.google_client_secret),
                ("GOOGLE_REFRESH_TOKEN", self.google_refresh_token),
            )
            if not valor
        ]
        if faltan_drive:
            print("ERROR: faltan credenciales de Drive en .env: " + ", ".join(faltan_drive))
            print("  -> corre 'python autorizar_drive.py' para generarlas")
            return False
        return True


def cargar_config() -> Config:
    return Config()

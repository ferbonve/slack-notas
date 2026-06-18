#%%

"""
Todo lo que tiene que ver con guardar/leer el CSV en Google Drive.

Responsabilidad unica: subir y bajar el CSV usando la API de Drive.
No sabe nada de Slack ni del formato de las notas.

Pensado para correr tanto en tu PC como en una Claude routine en la nube,
donde NO existe el Drive de escritorio montado (por eso usamos la API y no
una ruta de archivo).

Autenticacion: OAuth de usuario con refresh token (ver autorizar_drive.py).
Las credenciales salen de la config (.env / variables de entorno):
  GOOGLE_CLIENT_ID
  GOOGLE_CLIENT_SECRET
  GOOGLE_REFRESH_TOKEN
  DRIVE_CSV_NOMBRE   (nombre del archivo en Drive, ej: notas_slack.csv)
  DRIVE_FOLDER_ID    (opcional: carpeta donde crearlo la primera vez)
"""

import io

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from modules.config import Config

SCOPES = ["https://www.googleapis.com/auth/drive"]
TOKEN_URI = "https://oauth2.googleapis.com/token"


class DriveError(Exception):
    """Error 'lindo' para no tener que conocer googleapiclient afuera."""


def construir_service(config: Config):
    """Crea el cliente de la API de Drive a partir de la config.

    Centraliza la autenticacion OAuth (refresh token) para que todos los
    modulos que hablan con Drive (CSV, notas) compartan el mismo camino.
    """
    faltan = [
        nombre
        for nombre, valor in (
            ("GOOGLE_CLIENT_ID", config.google_client_id),
            ("GOOGLE_CLIENT_SECRET", config.google_client_secret),
            ("GOOGLE_REFRESH_TOKEN", config.google_refresh_token),
        )
        if not valor
    ]
    if faltan:
        raise DriveError(
            "Faltan credenciales de Drive en el .env: " + ", ".join(faltan)
        )
    creds = Credentials(
        token=None,
        refresh_token=config.google_refresh_token,
        client_id=config.google_client_id,
        client_secret=config.google_client_secret,
        token_uri=TOKEN_URI,
        scopes=SCOPES,
    )
    return build("drive", "v3", credentials=creds)


class DriveCSV:
    """Lee y escribe un unico CSV en Google Drive, buscandolo por nombre."""

    def __init__(self, config: Config):
        self.config = config
        self.nombre = config.drive_csv_nombre
        self.folder_id = config.drive_folder_id
        self._service = None
        self._file_id = None  # cache del ID una vez que lo encontramos

    # -- conexion (perezosa: no se conecta hasta usarla) ----------------- #
    @property
    def service(self):
        if self._service is None:
            self._service = construir_service(self.config)
        return self._service

    # -- helpers --------------------------------------------------------- #
    def _buscar_id(self) -> str | None:
        """Devuelve el ID del CSV en Drive, o None si todavia no existe."""
        if self._file_id:
            return self._file_id
        consulta = f"name = '{self.nombre}' and trashed = false"
        if self.folder_id:
            consulta += f" and '{self.folder_id}' in parents"
        resp = (
            self.service.files()
            .list(q=consulta, spaces="drive", fields="files(id, name)", pageSize=1)
            .execute()
        )
        archivos = resp.get("files", [])
        self._file_id = archivos[0]["id"] if archivos else None
        return self._file_id

    # -- operaciones ----------------------------------------------------- #
    def descargar_csv(self) -> str:
        """Devuelve el contenido del CSV como texto. Vacio si aun no existe."""
        file_id = self._buscar_id()
        if not file_id:
            return ""
        pedido = self.service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        descarga = MediaIoBaseDownload(buffer, pedido)
        listo = False
        while not listo:
            _, listo = descarga.next_chunk()
        return buffer.getvalue().decode("utf-8")

    def subir_csv(self, contenido: str) -> str:
        """Sobreescribe el CSV en Drive (lo crea si no existia). Devuelve su ID."""
        datos = io.BytesIO(contenido.encode("utf-8"))
        media = MediaIoBaseUpload(datos, mimetype="text/csv", resumable=False)
        file_id = self._buscar_id()
        if file_id:
            self.service.files().update(fileId=file_id, media_body=media).execute()
            return file_id
        metadata = {"name": self.nombre, "mimeType": "text/csv"}
        if self.folder_id:
            metadata["parents"] = [self.folder_id]
        creado = (
            self.service.files()
            .create(body=metadata, media_body=media, fields="id")
            .execute()
        )
        self._file_id = creado["id"]
        return self._file_id


#%%
drive_csv = DriveCSV(Config())

# %%
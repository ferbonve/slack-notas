"""
Sincroniza las notas .md entre Google Drive y una carpeta local.

Las notas viven como archivos sueltos directamente dentro de DRIVE_FOLDER_ID
(junto con el CSV), nombrados `AAAA-MM-DD_<tema>.md`: la fecha del mensaje va
al principio del nombre del archivo en vez de en una subcarpeta.

Responsabilidad unica: bajar esos .md a una carpeta local de trabajo y volver
a subir los que se crearon/modificaron. No sabe nada del contenido de las
notas ni del CSV; solo mueve archivos via la API de Drive.

Pensado para una Claude routine en la nube, donde NO existe el Drive de
escritorio montado: Claude trabaja sobre la copia local y esta clase se encarga
del ida y vuelta con Drive.
"""

import io
from pathlib import Path

from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from modules.config import Config
from modules.drive_client import DriveError, construir_service

FOLDER_MIME = "application/vnd.google-apps.folder"


class NotasDrive:
    """Lee y escribe las notas (.md sueltas) en Google Drive."""

    def __init__(self, config: Config):
        self.config = config
        self.parent_id = config.drive_folder_id  # misma carpeta donde vive el CSV
        self._service = None

    # -- conexion (perezosa) -------------------------------------------- #
    @property
    def service(self):
        if self._service is None:
            self._service = construir_service(self.config)
        return self._service

    # -- helpers de archivos -------------------------------------------- #
    def _listar(self, parent_id: str) -> list[dict]:
        """Lista hijos directos (id, name, mimeType) de una carpeta."""
        archivos: list[dict] = []
        token = None
        while True:
            resp = (
                self.service.files()
                .list(
                    q=f"'{parent_id}' in parents and trashed = false",
                    spaces="drive",
                    fields="nextPageToken, files(id, name, mimeType)",
                    pageToken=token,
                    pageSize=1000,
                )
                .execute()
            )
            archivos.extend(resp.get("files", []))
            token = resp.get("nextPageToken")
            if not token:
                break
        return archivos

    def _descargar(self, file_id: str) -> bytes:
        pedido = self.service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        descarga = MediaIoBaseDownload(buffer, pedido)
        listo = False
        while not listo:
            _, listo = descarga.next_chunk()
        return buffer.getvalue()

    def _notas_en_drive(self) -> list[dict]:
        """Archivos .md sueltos directamente en DRIVE_FOLDER_ID (sin carpetas)."""
        if not self.parent_id:
            raise DriveError(
                "Falta DRIVE_FOLDER_ID en el .env: no se donde estan las notas."
            )
        return [
            a
            for a in self._listar(self.parent_id)
            if a["mimeType"] != FOLDER_MIME and a["name"].endswith(".md")
        ]

    # -- operaciones ----------------------------------------------------- #
    def bajar(self, destino: Path) -> int:
        """Descarga las notas .md de Drive a 'destino' (carpeta plana). Devuelve cuantas bajo."""
        destino = Path(destino)
        destino.mkdir(parents=True, exist_ok=True)
        total = 0
        for archivo in self._notas_en_drive():
            (destino / archivo["name"]).write_bytes(self._descargar(archivo["id"]))
            total += 1
        return total

    def subir(self, origen: Path) -> int:
        """Sube/actualiza los .md de 'origen' a DRIVE_FOLDER_ID. Devuelve cuantos subio.

        Espera la estructura: origen/AAAA-MM-DD_<tema>.md (archivos sueltos,
        sin subcarpetas). Pisa los .md que ya existan con el mismo nombre.
        """
        origen = Path(origen)
        if not origen.exists():
            return 0
        existentes = {a["name"]: a["id"] for a in self._notas_en_drive()}
        total = 0
        for md in sorted(origen.glob("*.md")):
            media = MediaIoBaseUpload(
                io.BytesIO(md.read_bytes()),
                mimetype="text/markdown",
                resumable=False,
            )
            if md.name in existentes:
                self.service.files().update(
                    fileId=existentes[md.name], media_body=media
                ).execute()
            else:
                metadata = {"name": md.name, "parents": [self.parent_id]}
                self.service.files().create(
                    body=metadata, media_body=media, fields="id"
                ).execute()
            total += 1
        return total


notas_drive = NotasDrive(Config())

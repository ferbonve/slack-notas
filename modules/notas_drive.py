"""
Sincroniza la carpeta de notas entre Google Drive y una carpeta local.

Las notas viven en Drive como una subcarpeta (por defecto "notas") dentro de
DRIVE_FOLDER_ID, con una subcarpeta por dia: AAAA-MM-DD/<tema>.md

Responsabilidad unica: bajar ese arbol a una carpeta local de trabajo y volver
a subir los .md (creando las subcarpetas de dia que falten). No sabe nada del
contenido de las notas ni del CSV; solo mueve archivos via la API de Drive.

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
    """Lee y escribe el arbol de notas (.md por dia) en Google Drive."""

    def __init__(self, config: Config):
        self.config = config
        self.parent_id = config.drive_folder_id          # donde tambien vive el CSV
        self.nombre_carpeta = config.notas_carpeta_drive  # ej: "notas"
        self._service = None
        self._notas_root_id = None

    # -- conexion (perezosa) -------------------------------------------- #
    @property
    def service(self):
        if self._service is None:
            self._service = construir_service(self.config)
        return self._service

    # -- helpers de carpetas -------------------------------------------- #
    def _buscar_carpeta(self, nombre: str, parent_id: str | None) -> str | None:
        consulta = (
            f"name = '{nombre}' and mimeType = '{FOLDER_MIME}' and trashed = false"
        )
        if parent_id:
            consulta += f" and '{parent_id}' in parents"
        resp = (
            self.service.files()
            .list(q=consulta, spaces="drive", fields="files(id, name)", pageSize=1)
            .execute()
        )
        archivos = resp.get("files", [])
        return archivos[0]["id"] if archivos else None

    def _crear_carpeta(self, nombre: str, parent_id: str | None) -> str:
        metadata = {"name": nombre, "mimeType": FOLDER_MIME}
        if parent_id:
            metadata["parents"] = [parent_id]
        creado = self.service.files().create(body=metadata, fields="id").execute()
        return creado["id"]

    def _asegurar_carpeta(self, nombre: str, parent_id: str | None) -> str:
        """Devuelve el ID de la carpeta, creandola si no existe."""
        return self._buscar_carpeta(nombre, parent_id) or self._crear_carpeta(
            nombre, parent_id
        )

    def notas_root_id(self) -> str:
        """ID de la subcarpeta de notas (la crea la primera vez)."""
        if self._notas_root_id is None:
            if not self.parent_id:
                raise DriveError(
                    "Falta DRIVE_FOLDER_ID en el .env: no se donde crear la "
                    "carpeta de notas."
                )
            self._notas_root_id = self._asegurar_carpeta(
                self.nombre_carpeta, self.parent_id
            )
        return self._notas_root_id

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

    # -- operaciones ----------------------------------------------------- #
    def bajar(self, destino: Path) -> int:
        """Descarga el arbol de notas de Drive a 'destino'. Devuelve cuantas bajo."""
        destino = Path(destino)
        destino.mkdir(parents=True, exist_ok=True)
        total = 0
        for dia in self._listar(self.notas_root_id()):
            if dia["mimeType"] != FOLDER_MIME:
                continue  # solo nos interesan las subcarpetas de dia
            carpeta_local = destino / dia["name"]
            carpeta_local.mkdir(parents=True, exist_ok=True)
            for archivo in self._listar(dia["id"]):
                if archivo["mimeType"] == FOLDER_MIME:
                    continue
                (carpeta_local / archivo["name"]).write_bytes(
                    self._descargar(archivo["id"])
                )
                total += 1
        return total

    def subir(self, origen: Path) -> int:
        """Sube/actualiza los .md de 'origen' a Drive. Devuelve cuantos subio.

        Espera la estructura: origen/AAAA-MM-DD/<tema>.md
        Crea las subcarpetas de dia que falten y pisa los .md con el mismo nombre.
        """
        origen = Path(origen)
        if not origen.exists():
            return 0
        root = self.notas_root_id()
        total = 0
        for carpeta_dia in sorted(p for p in origen.iterdir() if p.is_dir()):
            dia_id = self._asegurar_carpeta(carpeta_dia.name, root)
            existentes = {
                a["name"]: a["id"]
                for a in self._listar(dia_id)
                if a["mimeType"] != FOLDER_MIME
            }
            for md in sorted(carpeta_dia.glob("*.md")):
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
                    metadata = {"name": md.name, "parents": [dia_id]}
                    self.service.files().create(
                        body=metadata, media_body=media, fields="id"
                    ).execute()
                total += 1
        return total


notas_drive = NotasDrive(Config())

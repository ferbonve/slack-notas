
#%%
from datetime import datetime
import csv
import io

from modules.drive_client import drive_csv

#%% VARIABLES
CAMPOS = ["ts", "fecha", "user", "text", "type"]

#%% FUNCTIONS
def cargar_ts_existentes(contenido: str) -> set:
    """Devuelve el conjunto de 'ts' ya guardados, leyendo el CSV en memoria."""
    if not contenido:
        return set()
    reader = csv.DictReader(io.StringIO(contenido))
    return {fila["ts"] for fila in reader}

def ultima_fecha(contenido: str):
    """Devuelve la fecha (date) del mensaje más reciente del CSV, o None si está vacío."""
    if not contenido:
        return None
    reader = csv.DictReader(io.StringIO(contenido))
    max_ts = None
    for fila in reader:
        try:
            ts = float(fila["ts"])
            if max_ts is None or ts > max_ts:
                max_ts = ts
        except (ValueError, KeyError):
            pass
    if max_ts is None:
        return None
    return datetime.fromtimestamp(max_ts).date()



def guardar_nuevos(mensajes) -> int:
    """Baja el CSV de Drive, agrega los mensajes nuevos y lo vuelve a subir.

    Devuelve cuantos mensajes nuevos se agregaron.
    """
    contenido = drive_csv.descargar_csv()
    existentes = cargar_ts_existentes(contenido)
    nuevos = [m for m in mensajes if m["ts"] not in existentes]
    if not nuevos:
        return 0

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CAMPOS)
    if not contenido:
        # CSV todavia no existe en Drive: arrancamos con encabezado.
        writer.writeheader()
    elif not contenido.endswith("\n"):
        # Aseguramos que las filas previas terminen en salto de linea.
        contenido += "\n"

    for m in nuevos:
        writer.writerow({
            "ts": m["ts"],
            "fecha": datetime.fromtimestamp(float(m["ts"])).date().isoformat(),
            "user": m.get("user", ""),
            "text": m.get("text", ""),
            "type": m.get("type", ""),
        })

    drive_csv.subir_csv(contenido + buffer.getvalue())
    return len(nuevos)


#%%



# %%

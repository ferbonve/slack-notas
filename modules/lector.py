#%%

"""
Lee el CSV de Drive y devuelve los mensajes de un dia concreto.

Responsabilidad unica: bajar el CSV (el mismo que escribe el extractor) y
filtrar las filas cuyo campo 'fecha' coincide con el dia pedido.
No habla con Slack ni con el LLM; solo lee y filtra.

Pensado para correr DESPUES del extractor: el extractor deja los mensajes
nuevos en el CSV de Drive y este modulo los recupera para el dia de hoy
(o cualquier otra fecha) para pasarselos despues al LLM.
"""

from datetime import datetime, date
import csv
import io

from modules.drive_client import drive_csv

#%% VARIABLES
CAMPOS = ["ts", "fecha", "user", "text", "type"]

#%% FUNCTIONS
def _leer_filas(contenido: str) -> list[dict]:
    """Parsea el contenido del CSV a una lista de diccionarios."""
    if not contenido:
        return []
    reader = csv.DictReader(io.StringIO(contenido))
    return list(reader)


def leer_mensajes_del_dia(dia: date | None = None) -> list[dict]:
    """Devuelve los mensajes del CSV de Drive correspondientes a 'dia'.

    Si no se pasa 'dia', usa la fecha de hoy. Las filas vienen ordenadas
    cronologicamente por 'ts' (igual que las dejo el extractor).
    """
    if dia is None:
        dia = datetime.today().date()

    contenido = drive_csv.descargar_csv()
    filas = _leer_filas(contenido)

    objetivo = dia.isoformat()
    del_dia = [fila for fila in filas if fila.get("fecha") == objetivo]
    del_dia.sort(key=lambda f: float(f["ts"]))
    return del_dia


#%%
if __name__ == "__main__":
    fecha = datetime.today().date()
    # fecha = datetime(2024, 6, 1).date()
    mensajes = leer_mensajes_del_dia(fecha)
    print(f"{fecha}: {len(mensajes)} mensaje(s) en el CSV.")
    for m in mensajes:
        print(f"  [{m['ts']}] {m.get('user', '')}: {m.get('text', '')}")

# %%

#%%
from datetime import datetime, timedelta
from modules.config import Config
from modules.drive_client import drive_csv
from modules.extractor import guardar_nuevos, cargar_ts_existentes
from modules.slack_client import slack

def main() -> None:
    if not Config().validar():
        return

    # Buscar desde el último ts del CSV para no perder mensajes enviados
    # después de la última ejecución (sin importar el día).
    contenido = drive_csv.descargar_csv()
    existentes = cargar_ts_existentes(contenido)

    if existentes:
        oldest = max(existentes, key=float)
    else:
        oldest = str((datetime.now() - timedelta(days=7)).timestamp())

    mensajes = slack.mensajes_desde(oldest)
    n = guardar_nuevos(mensajes)
    print(f"{datetime.today().date()}: {n} mensaje(s) nuevo(s) guardado(s) en Drive.")

if __name__ == "__main__":
    main()
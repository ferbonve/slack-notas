#%%
from datetime import datetime, timedelta
from modules.config import Config
from modules.drive_client import drive_csv
from modules.extractor import guardar_nuevos, ultima_fecha
from modules.slack_client import slack

# --------------------------------------------------------------------------- #

def main() -> None:
    if not Config().validar():
        return

    hoy = datetime.today().date()

    # Determinar desde qué día buscar: re-consulta el último día con mensajes
    # para capturar mensajes enviados después de que la rutina corrió ese día,
    # y avanza hasta hoy para cubrir días salteados.
    contenido_csv = drive_csv.descargar_csv()
    inicio = ultima_fecha(contenido_csv) or hoy

    mensajes = []
    dia = inicio
    while dia <= hoy:
        mensajes.extend(slack.mensajes_del_dia(dia))
        dia += timedelta(days=1)

    n = guardar_nuevos(mensajes)
    dias = (hoy - inicio).days + 1
    rango = f"{inicio} → {hoy}" if inicio != hoy else str(hoy)
    print(f"{rango} ({dias} día(s)): {n} mensaje(s) nuevo(s) guardado(s) en Drive.")



if __name__ == "__main__":
    main()

# %%

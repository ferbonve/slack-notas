#%%
from datetime import datetime
from modules.config import Config
from modules.extractor import guardar_nuevos
from modules.slack_client import slack

# --------------------------------------------------------------------------- #

def main() -> None:
    if not Config().validar():
        return

    fecha = datetime.today().date()
    #fecha = datetime(2024, 6, 1).date()

    # Extractor: trae los mensajes de Slack y los guarda en el CSV de Drive.
    # La clasificacion en notas la hace Claude por su conector de Drive,
    # deduplicando por `ts` contra las notas existentes (no hace falta el lector).
    mensajes = slack.mensajes_del_dia(fecha)
    n = guardar_nuevos(mensajes)
    print(f"{fecha}: {n} mensaje(s) nuevo(s) guardado(s) en Drive.")



if __name__ == "__main__":
    main()

# %%

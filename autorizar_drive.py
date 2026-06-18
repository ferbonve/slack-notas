"""
Autorizacion de Google Drive — ejecutalo UNA sola vez en tu PC.

Que hace: abre el navegador, te pide permiso para que la app acceda a Drive,
y al final imprime las 3 credenciales que tenes que pegar en tu .env (y como
secretos de la Claude routine):
    GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET
    GOOGLE_REFRESH_TOKEN

Requisito previo:
  1. En Google Cloud Console (https://console.cloud.google.com/) crea un
     proyecto, habilita la "Google Drive API".
  2. En "Pantalla de consentimiento de OAuth": tipo Externo, agregate como
     usuario de prueba, y publicala ("In production") para que el refresh token
     NO caduque a los 7 dias.
  3. En "Credenciales" crea un "ID de cliente de OAuth" de tipo
     "App de escritorio" y descarga el JSON.
  4. Guarda ese JSON en esta carpeta como  client_secret.json

Despues corre:   python autorizar_drive.py
"""

from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/drive"]
BASE_DIR = Path(__file__).resolve().parent
CLIENT_SECRET = BASE_DIR / "client_secret.json"


def main() -> None:
    if not CLIENT_SECRET.exists():
        print(f"ERROR: no encuentro {CLIENT_SECRET.name} en esta carpeta.")
        print("Descargalo de Google Cloud Console (OAuth, App de escritorio).")
        return

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    # prompt='consent' fuerza que Google devuelva el refresh_token.
    creds = flow.run_local_server(port=0, prompt="consent")

    print("\n=== Pega esto en tu .env y en los secretos de la routine ===\n")
    print(f"GOOGLE_CLIENT_ID={creds.client_id}")
    print(f"GOOGLE_CLIENT_SECRET={creds.client_secret}")
    print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
    print("\n(Opcional) DRIVE_FOLDER_ID=<id de la carpeta de Drive donde guardar el CSV>")


if __name__ == "__main__":
    main()

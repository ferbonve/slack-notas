#%%

"""
Todo lo que tiene que ver con hablar con Slack.

Responsabilidad unica: conectarse a la API y traer mensajes.
No sabe nada de archivos ni de Markdown.
"""

from datetime import datetime, timedelta, date

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from modules.config import Config


class SlackError(Exception):
    """Error 'lindo' para que main.py no tenga que conocer slack_sdk."""

    def __init__(self, codigo: str):
        self.codigo = codigo
        super().__init__(codigo)


def _explicacion(codigo: str) -> str:
    ayudas = {
        "not_in_channel": "El bot no esta en el canal. Invitalo con: /invite @tu-bot",
        "missing_scope": "Falta el scope channels:history (o groups:history si es privado). "
                         "Reinstala la app despues de agregar scopes.",
        "invalid_auth": "El token es invalido. Revisa que lo copiaste completo.",
        "channel_not_found": "CHANNEL_ID incorrecto. Revisa el ID del canal.",
    }
    return ayudas.get(codigo, "")


class SlackNotas:
    """Pequeño envoltorio sobre el cliente de Slack para este proyecto."""

    def __init__(self, config: Config):
        self.config = config
        self.client = WebClient(token=config.slack_token)
        self._cache_nombres: dict[str, str] = {}

    # -- nombres de usuario ---------------------------------------------- #
    def nombre_usuario(self, user_id: str | None) -> str:
        """Devuelve el nombre legible de un usuario. Cachea para no repetir llamadas.
        Si no se puede (falta el scope users:read), cae al ID."""
        if not user_id:
            return "desconocido"
        if user_id in self._cache_nombres:
            return self._cache_nombres[user_id]
        try:
            perfil = self.client.users_info(user=user_id)["user"]
            nombre = (
                perfil.get("profile", {}).get("display_name")
                or perfil.get("real_name")
                or user_id
            )
        except SlackApiError:
            nombre = user_id  # sin scope users:read, usamos el ID
        self._cache_nombres[user_id] = nombre
        return nombre

    # -- conexion -------------------------------------------------------- #
    def quien_soy(self) -> tuple[str, str]:
        """Devuelve (usuario, workspace). Lanza SlackError si falla."""
        try:
            auth = self.client.auth_test()
            return auth["user"], auth["team"]
        except SlackApiError as e:
            raise SlackError(e.response["error"]) from e

    def ultimos_mensajes(self, limite: int = 10) -> list[dict]:
        try:
            resp = self.client.conversations_history(
                channel=self.config.channel_id, limit=limite
            )
            return resp.get("messages", [])
        except SlackApiError as e:
            raise SlackError(e.response["error"]) from e

    def nombre_canal(self) -> str:
        """Devuelve '#nombre-del-canal'. Si no se puede, devuelve el ID."""
        try:
            info = self.client.conversations_info(channel=self.config.channel_id)["channel"]
            nombre = info.get("name")
            return f"#{nombre}" if nombre else self.config.channel_id
        except SlackApiError:
            return self.config.channel_id

    def workspace(self) -> str:
        """Nombre del workspace. Cadena vacia si no se puede obtener."""
        try:
            return self.client.auth_test().get("team", "")
        except SlackApiError:
            return ""

    # -- mensajes por dia ------------------------------------------------ #
    def mensajes_del_dia(self, dia: date) -> list[dict]:
        """Trae TODOS los mensajes del canal dentro de un dia (00:00 a 23:59)."""
        inicio = datetime(dia.year, dia.month, dia.day, 0, 0, 0)
        fin = inicio + timedelta(days=1)

        mensajes: list[dict] = []
        cursor = None
        try:
            while True:
                params = {
                    "channel": self.config.channel_id,
                    "oldest": str(inicio.timestamp()),
                    "latest": str(fin.timestamp()),
                    "inclusive": True,
                    "limit": 200,
                }
                if cursor:
                    params["cursor"] = cursor
                resp = self.client.conversations_history(**params)
                mensajes.extend(resp.get("messages", []))
                if resp.get("has_more"):
                    cursor = resp["response_metadata"]["next_cursor"]
                else:
                    break
        except SlackApiError as e:
            raise SlackError(e.response["error"]) from e

        # Slack devuelve del mas nuevo al mas viejo; ordenamos cronologicamente
        mensajes.sort(key=lambda m: float(m["ts"]))
        return mensajes


def explicar_error(codigo: str) -> None:
    """Imprime una ayuda segun el codigo de error de Slack."""
    print(f"ERROR de Slack: {codigo}")
    ayuda = _explicacion(codigo)
    if ayuda:
        print(f"  -> {ayuda}")




#%%
slack = SlackNotas(Config())


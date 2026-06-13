"""Helper de un solo uso: genera el GOOGLE_REFRESH_TOKEN para YouTube.

Cómo usarlo (en tu máquina local, una sola vez):

1. En Google Cloud Console crea un OAuth Client ID de tipo "Desktop app" y
   descarga el JSON de credenciales (client_secret_xxx.json).
2. Habilita "YouTube Data API v3" en el mismo proyecto.
3. Ejecuta:

       pip install -r requirements.txt
       python scripts/get_refresh_token.py /ruta/al/client_secret.json

4. Se abrirá el navegador para que autorices tu cuenta. Al terminar, el script
   imprime el refresh token. Guárdalo como variable de entorno
   GOOGLE_REFRESH_TOKEN (junto con GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET, que
   también se imprimen aquí).

Nota: el client secret de tipo Desktop no es un secreto de alto riesgo, pero aun
así trátalo con cuidado y no lo subas al repo.
"""

from __future__ import annotations

import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python scripts/get_refresh_token.py <client_secret.json>")
        return 2

    client_secrets_file = sys.argv[1]
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
    # access_type=offline + prompt=consent garantiza que se emita refresh_token.
    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
    )

    print("\n=== Copia estos valores a las variables de entorno ===\n")
    print(f"GOOGLE_CLIENT_ID={creds.client_id}")
    print(f"GOOGLE_CLIENT_SECRET={creds.client_secret}")
    print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
    print()
    if not creds.refresh_token:
        print(
            "ADVERTENCIA: no se recibió refresh_token. Revoca el acceso en "
            "https://myaccount.google.com/permissions y vuelve a correr el script.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Configuración central: credenciales, IDs y reglas de agendado.

Las credenciales se leen de variables de entorno para no versionar secretos.
Las reglas de agendado viven aquí como única fuente de verdad para el código;
su espejo legible para humanos está en AGENT_RULES.md (y en la página del
Custom Agent de Notion).
"""

from __future__ import annotations

import os

# --- Zona horaria del usuario (sin DST desde 2022) ---
TIMEZONE = "America/Mexico_City"

# --- Credenciales / IDs (variables de entorno) ---
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN", "")
YOUTUBE_PLAYLIST_ID = os.environ.get("YOUTUBE_PLAYLIST_ID", "")

# OAuth2 token endpoint (refresh flow).
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"

# Scope necesario para LEER una playlist privada y BORRAR sus items.
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

# --- Reglas de agendado (referencia para Claude; ver AGENT_RULES.md) ---
# Días permitidos: martes(1)..domingo(6). Se excluye lunes(0).
# weekday(): Monday=0 ... Sunday=6
ALLOWED_WEEKDAYS = [1, 2, 3, 4, 5, 6]  # Tue..Sun

# Ventanas diarias como (HH:MM inicio, HH:MM fin).
SCHEDULING_WINDOWS = [
    ("09:00", "10:00"),
    ("12:00", "13:00"),
    ("16:00", "16:30"),
]

# Tamaños de bloque permitidos (minutos). La duración del video se redondea
# hacia arriba al primero que la contenga (ceil a múltiplos de 15).
BLOCK_SIZES_MIN = [15, 30, 45, 60]

# Identificadores de Notion (referencia; el agendado real va por MCP).
NOTION_REMINDERS_DATASOURCE = "collection://c766b4e8-3188-4020-a99c-2b57cd3ef811"
NOTION_AGENT_PAGE_ID = "313d6d49-81de-8077-978c-df417d211e22"


def round_up_to_block(duration_min: int) -> int:
    """Redondea la duración (min) al bloque permitido más pequeño que la contenga.

    Ejemplos: 9->15, 24->30, 47->60. Los videos de más de 60 min se topan en el
    bloque mayor (60): se agendan como una sesión parcial de 60 min y el resto del
    video no se contabiliza.
    """
    for block in BLOCK_SIZES_MIN:
        if duration_min <= block:
            return block
    return BLOCK_SIZES_MIN[-1]  # tope: video largo -> bloque de 60


def require_env() -> None:
    """Valida que las variables de entorno necesarias estén presentes."""
    missing = [
        name
        for name, value in {
            "GOOGLE_CLIENT_ID": GOOGLE_CLIENT_ID,
            "GOOGLE_CLIENT_SECRET": GOOGLE_CLIENT_SECRET,
            "GOOGLE_REFRESH_TOKEN": GOOGLE_REFRESH_TOKEN,
            "YOUTUBE_PLAYLIST_ID": YOUTUBE_PLAYLIST_ID,
        }.items()
        if not value
    ]
    if missing:
        raise SystemExit(
            "Faltan variables de entorno: "
            + ", ".join(missing)
            + ".\nConfigúralas en el entorno (ver README.md)."
        )

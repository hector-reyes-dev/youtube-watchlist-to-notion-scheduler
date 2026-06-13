"""Cliente de YouTube Data API v3 para extraer y borrar items de una playlist.

Usa un refresh token OAuth2 (scope youtube.force-ssl) para autenticarse, de modo
que puede leer playlists privadas y borrar items.
"""

from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass

import google_auth_httplib2
import httplib2
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from . import config


@dataclass
class Video:
    """Un video de la playlist con lo necesario para agendar y luego borrar."""

    title: str
    video_id: str
    url: str
    duration_min: int  # duración redondeada hacia arriba al minuto
    playlist_item_id: str  # id del item en la playlist (necesario para borrar)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "video_id": self.video_id,
            "url": self.url,
            "duration_min": self.duration_min,
            "playlist_item_id": self.playlist_item_id,
        }


# ISO-8601 de YouTube: PT#H#M#S (cualquiera de los componentes puede faltar).
_ISO_DURATION_RE = re.compile(
    r"P(?:(?P<days>\d+)D)?T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
)


def parse_iso8601_duration_to_minutes(iso: str) -> int:
    """Convierte una duración ISO-8601 a minutos, redondeando hacia arriba.

    Un video de 0s (ej. en vivo) devuelve 0; el llamador decide qué hacer.
    """
    match = _ISO_DURATION_RE.fullmatch(iso or "")
    if not match:
        return 0
    parts = {k: int(v) if v else 0 for k, v in match.groupdict().items()}
    total_seconds = (
        parts["days"] * 86400
        + parts["hours"] * 3600
        + parts["minutes"] * 60
        + parts["seconds"]
    )
    return math.ceil(total_seconds / 60)


def _resolve_ca_bundle() -> str | None:
    """Devuelve un bundle de CA que incluya la CA del proxy del entorno, si la hay.

    httplib2 (capa HTTP del cliente de Google) usa por defecto los certificados de
    certifi, que NO contienen la CA del proxy de egress de algunos entornos
    sandbox (Claude Code on the web). Preferimos un bundle del sistema que sí la
    incluya. En local sin proxy, cualquiera de estos sirve igual; si ninguno
    existe, devolvemos None y httplib2 usa su default.
    """
    for candidate in (
        os.environ.get("REQUESTS_CA_BUNDLE"),
        os.environ.get("SSL_CERT_FILE"),
        "/etc/ssl/certs/ca-certificates.crt",
    ):
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def _build_service():
    """Construye el cliente autenticado de la YouTube Data API."""
    config.require_env()
    creds = Credentials(
        token=None,
        refresh_token=config.GOOGLE_REFRESH_TOKEN,
        client_id=config.GOOGLE_CLIENT_ID,
        client_secret=config.GOOGLE_CLIENT_SECRET,
        token_uri=config.GOOGLE_TOKEN_URI,
        scopes=config.YOUTUBE_SCOPES,
    )
    ca_bundle = _resolve_ca_bundle()
    base_http = httplib2.Http(ca_certs=ca_bundle) if ca_bundle else httplib2.Http()
    authed_http = google_auth_httplib2.AuthorizedHttp(creds, http=base_http)
    # cache_discovery=False evita warnings/escrituras en entornos efímeros.
    return build("youtube", "v3", http=authed_http, cache_discovery=False)


def _fetch_durations(service, video_ids: list[str]) -> dict[str, int]:
    """Devuelve {video_id: duración_min} para los ids dados (en lotes de 50)."""
    durations: dict[str, int] = {}
    for start in range(0, len(video_ids), 50):
        batch = video_ids[start : start + 50]
        resp = (
            service.videos()
            .list(part="contentDetails", id=",".join(batch), maxResults=50)
            .execute()
        )
        for item in resp.get("items", []):
            iso = item.get("contentDetails", {}).get("duration", "")
            durations[item["id"]] = parse_iso8601_duration_to_minutes(iso)
    return durations


def list_playlist_videos(playlist_id: str | None = None) -> list[Video]:
    """Lista todos los videos de la playlist con título, URL y duración.

    Pagina sobre playlistItems.list y luego resuelve las duraciones con
    videos.list. Omite items privados/borrados (sin videoId resoluble).
    """
    playlist_id = playlist_id or config.YOUTUBE_PLAYLIST_ID
    service = _build_service()

    raw_items: list[dict] = []
    page_token: str | None = None
    while True:
        resp = (
            service.playlistItems()
            .list(
                part="snippet,contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=page_token,
            )
            .execute()
        )
        raw_items.extend(resp.get("items", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    video_ids = [
        it["contentDetails"]["videoId"]
        for it in raw_items
        if it.get("contentDetails", {}).get("videoId")
    ]
    durations = _fetch_durations(service, video_ids) if video_ids else {}

    videos: list[Video] = []
    for it in raw_items:
        video_id = it.get("contentDetails", {}).get("videoId")
        if not video_id:
            continue  # item privado o eliminado
        snippet = it.get("snippet", {})
        videos.append(
            Video(
                title=snippet.get("title", "(sin título)"),
                video_id=video_id,
                url=f"https://www.youtube.com/watch?v={video_id}",
                duration_min=durations.get(video_id, 0),
                playlist_item_id=it["id"],
            )
        )
    return videos


def delete_playlist_items(playlist_item_ids: list[str]) -> list[str]:
    """Borra los items dados de la playlist. Devuelve los ids borrados con éxito."""
    if not playlist_item_ids:
        return []
    service = _build_service()
    deleted: list[str] = []
    for item_id in playlist_item_ids:
        service.playlistItems().delete(id=item_id).execute()
        deleted.append(item_id)
    return deleted

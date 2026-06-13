# Proyecto: YouTube "Por ver" → Notion Reminders

Rutina semanal que, cada **domingo 17:00 (America/Mexico_City)**, extrae los
videos de una playlist de YouTube y los agenda en la base **🔔 Reminders** de
Notion según su duración, evitando choques con el calendario. Al final, borra de
la playlist los videos ya agendados.

## Cómo se ejecuta
La orquestación la hace **Claude Code** (no GitHub Actions): una sesión
programada de Claude Code on the web corre el comando `/agendar-videos`
(`.claude/commands/agendar-videos.md`). Claude actúa como el "Custom Agent",
siguiendo las reglas de `AGENT_RULES.md`.

## Reparto de responsabilidades
- **Script Python (`src/`)** → única parte que toca YouTube: extrae la playlist
  (título, URL, duración, `playlist_item_id`) y borra items. Usa la YouTube Data
  API v3 con OAuth2 (credenciales por variables de entorno).
- **Claude vía conectores MCP** → agendado: lee Google Calendar y Reminders para
  evitar solapes, crea los ítems en Reminders y dispara el borrado en la playlist.

## Archivos clave
- `AGENT_RULES.md` — reglas de agendado (fuente de verdad; espejo del agente en Notion).
- `.claude/commands/agendar-videos.md` — el comando que corre la sesión programada.
- `src/youtube_client.py` — cliente de YouTube (listar/borrar, parseo de duración).
- `src/main.py` — CLI: `extract` y `delete`.
- `src/config.py` — env vars, ventanas, redondeo, IDs de Notion.
- `scripts/get_refresh_token.py` — generación única del refresh token de Google.

## IDs de Notion (referencia)
- Base destino **🔔 Reminders**: `collection://c766b4e8-3188-4020-a99c-2b57cd3ef811`.
- Página del Custom Agent (documentación): `313d6d49-81de-8077-978c-df417d211e22`.

## Comandos útiles
```bash
pip install -r requirements.txt
python -m src.main extract -o videos.json     # listar playlist → JSON
python -m src.main delete --ids ID1 ID2        # borrar items agendados
```

## Notas
- "Ver más tarde" de YouTube no es accesible por API: se usa una playlist normal "Por ver".
- Zona horaria fija: America/Mexico_City (UTC−6, sin DST).
- La política de red del entorno debe permitir `googleapis.com`.

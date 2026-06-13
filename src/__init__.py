"""YouTube 'Por ver' → Notion Reminders scheduler.

Extrae los videos de una playlist de YouTube (título, URL, duración) usando la
YouTube Data API v3 y expone utilidades para borrarlos de la playlist una vez
agendados. La lógica de agendado (reglas del Custom Agent) la ejecuta Claude
Code en la sesión programada usando los conectores MCP de Notion y Google
Calendar; este paquete solo cubre la parte de YouTube.
"""

__all__ = ["config", "youtube_client", "main"]

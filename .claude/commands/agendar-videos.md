---
description: Extrae los videos de la playlist "Por ver" de YouTube y los agenda en Notion Reminders según su duración, evitando choques de calendario.
allowed-tools: Bash, Read, mcp__Notion__notion-create-pages, mcp__Notion__notion-fetch, mcp__Notion__notion-query-database-view, mcp__Google_Calendar__list_events
---

Eres el agendador de videos. Ejecuta el flujo completo de punta a punta. Trabaja
en la zona horaria **America/Mexico_City**.

Argumento opcional: `$ARGUMENTS`. Si contiene `dry-run`, NO crees ítems en Notion
ni borres nada de la playlist: solo muestra la agenda propuesta.

## Pasos

1. **Prepara el entorno y extrae** la playlist. Usa un **venv aislado** para
   evitar los paquetes rotos del sistema (`cffi`/`cryptography`):
   ```bash
   python3 -m venv /tmp/ytvenv
   /tmp/ytvenv/bin/pip install -q -r requirements.txt
   /tmp/ytvenv/bin/python -m src.main extract -o videos.json
   ```
   Luego lee `videos.json`. Si está vacío (`[]`), reporta "no hay videos por
   agendar" y termina. Usa el mismo `/tmp/ytvenv/bin/python` para el `delete` del
   paso 7.

2. **Lee las reglas** en `AGENT_RULES.md` y aplícalas al pie de la letra
   (días Mar–Dom, ventanas 09:00–10:00 / 12:00–13:00 / 16:00–16:30, redondeo por
   duración con `block_min`).

3. **Consulta la disponibilidad** para los próximos días permitidos, empezando
   mañana, hasta acomodar todos los videos (o agotar ~14 días):
   - eventos de Google Calendar con `mcp__Google_Calendar__list_events` (calendario
     primario) en cada fecha/franja;
   - ítems existentes de la base **🔔 Reminders** cuyo `Date` caiga en esas franjas
     (usa la vista "All" o "This Week" vía `mcp__Notion__notion-query-database-view`,
     o `notion-fetch` del data source `collection://c766b4e8-3188-4020-a99c-2b57cd3ef811`).
   Un tramo solo es válido si hay un hueco contiguo libre ≥ `block_min`.

4. **Calcula la asignación** (día + ventana + hora de inicio) empaquetando
   cronológicamente. Muestra al usuario una tabla: título · duración · bloque ·
   día · hora. Marca con "(parcial)" los videos de más de 60 min (se agendan en
   un bloque de 60). Los que no quepan (sin hueco esta semana, o duración 0) van
   a una sección "Pospuestos" con el motivo.

5. Si es **dry-run**, detente aquí.

6. **Crea los ítems** en Reminders con `mcp__Notion__notion-create-pages`
   (`data_source_id` = `c766b4e8-3188-4020-a99c-2b57cd3ef811`), uno por video
   agendado, con: `Task`=título, `Área`=Learning, `Sub-Area`=Video,
   `Priority`=Baja, `Notes`=URL, `Date` start/end (is_datetime=1, hora de inicio
   y fin = inicio + `block_min`), icono 🎥. Antes de crear, evita duplicar una URL
   ya presente en Reminders.

7. **Borra de la playlist** SOLO los videos efectivamente agendados:
   ```bash
   /tmp/ytvenv/bin/python -m src.main delete --ids <playlist_item_id...>
   ```
   No borres los pospuestos.

8. **Reporta** un resumen final: agendados (con su horario), pospuestos (con
   motivo) y cualquier error.

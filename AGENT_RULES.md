# Reglas de agendado de videos (lógica del Custom Agent)

Estas son las reglas que Claude Code ejecuta cada domingo para agendar los
videos de la playlist "Por ver" en la base **🔔 Reminders** de Notion. Son el
espejo en el repo del Custom Agent de Notion "🔖 Bookmark Review Scheduler"
(página `313d6d49-81de-8077-978c-df417d211e22`), **adaptado** para recibir como
entrada la lista que produce la API de YouTube en vez de marcadores sueltos.

## Entrada
Un arreglo JSON (salida de `python -m src.main extract`), cada elemento:

```json
{
  "title": "…",
  "video_id": "…",
  "url": "https://www.youtube.com/watch?v=…",
  "duration_min": 24,
  "playlist_item_id": "…",
  "block_min": 30
}
```

- `duration_min`: duración real del video, redondeada hacia arriba al minuto.
- `block_min`: tamaño de bloque ya redondeado (`null` si el video dura > 60 min).

## Parámetros de agendado
- **Zona horaria:** `America/Mexico_City`.
- **Días permitidos:** martes, miércoles, jueves, viernes, sábado y domingo.
  **Nunca lunes.** Se empieza por el día siguiente a la corrida.
- **Ventanas diarias:**
  - `09:00–10:00` (60 min)
  - `12:00–13:00` (60 min)
  - `16:00–16:30` (30 min)
- **Redondeo por duración** (bloque = primer valor que contenga la duración):
  - `≤ 15 min` → bloque de **15**
  - `≤ 30 min` → bloque de **30**
  - `≤ 45 min` → bloque de **45**
  - `≤ 60 min` → bloque de **60**
  - `> 60 min` → **no cabe** (ver "Casos borde").
  - Ejemplos: 9→15, 24→30, 47→60.

## Algoritmo
1. Ordena los videos en el orden en que vienen de la playlist (orden del usuario).
2. Determina el rango de días: desde mañana hasta cubrir todos los videos,
   recorriendo solo días permitidos (Mar–Dom).
3. Construye la lista de tramos libres por día: para cada ventana, considera el
   tiempo ya ocupado por:
   - **Eventos de Google Calendar** (consulta vía el conector de Google Calendar,
     `list_events`, en esa fecha/franja), y
   - **Ítems existentes de 🔔 Reminders** con `Date` dentro de la franja.
   Un tramo solo sirve si hay un hueco contiguo libre ≥ `block_min`.
4. Empaqueta cronológicamente: por cada video toma el primer día permitido y la
   primera ventana con hueco contiguo suficiente; coloca el bloque al inicio del
   hueco libre. Varios videos cortos pueden compartir una ventana (p. ej. 15+15+30
   en `09:00–10:00`) siempre que no se solapen entre sí ni con lo ya ocupado.
   La ventana `16:00–16:30` solo admite un bloque de ≤ 30.
5. Si un día se llena, pasa al siguiente día permitido.

## Creación del ítem en 🔔 Reminders
Por cada video agendado, crea una página en el data source
`collection://c766b4e8-3188-4020-a99c-2b57cd3ef811` con:

| Propiedad   | Valor                                                        |
|-------------|--------------------------------------------------------------|
| `Task`      | el título del video                                          |
| `Área`      | `Learning`                                                   |
| `Sub-Area`  | `Video`                                                      |
| `Priority`  | `Baja`                                                       |
| `Notes`     | la URL del video                                             |
| `Date`      | `start` = inicio del bloque, `end` = inicio + `block_min`, `is_datetime` = 1, zona `America/Mexico_City` |
| icono       | 🎥                                                           |

## Después de agendar
- Reúne los `playlist_item_id` de **todos los videos efectivamente agendados** y
  bórralos de la playlist con `python -m src.main delete --ids <ids...>`.
- Los videos **no** agendados (sin hueco esta semana, o > 60 min) **se dejan** en
  la playlist para reintentarse la próxima corrida.

## Casos borde
- **Video > 60 min:** no cabe en ninguna ventana → no se agenda, no se borra, y
  se reporta para que el usuario lo divida o lo vea manualmente.
- **Sin huecos suficientes en el horizonte de días:** deja el sobrante en la
  playlist y repórtalo.
- **`duration_min == 0`** (en vivo / sin duración resoluble): trátalo como caso a
  reportar, no lo agendes automáticamente.
- **Idempotencia:** como los videos agendados se borran de la playlist, una
  segunda corrida no los vuelve a ver. Aun así, antes de crear un ítem evita
  duplicar uno con la misma URL ya presente en Reminders para esa semana.

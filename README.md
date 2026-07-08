# 📺 → 🗓️ YouTube "Por ver" → Notion Reminders Scheduler

Cada **domingo a las 5pm (hora de México)**, esta rutina:

1. **Extrae** los videos de tu playlist de YouTube **"Por ver"** (título, URL,
   duración) con la **YouTube Data API v3**.
2. **Agenda** cada video en tu base de Notion **🔔 Reminders** según su duración,
   acomodándolo en tus ventanas de visionado y **evitando choques** con tu Google
   Calendar y con otros recordatorios.
3. **Borra** de la playlist los videos que quedaron agendados.

La orquestación la ejecuta **Claude Code** (sesión programada en
[Claude Code on the web](https://code.claude.com/docs/en/claude-code-on-the-web)),
que actúa como tu Custom Agent siguiendo las reglas de
[`AGENT_RULES.md`](./AGENT_RULES.md).

## Cómo agenda (resumen)

- **Días:** martes a domingo (nunca lunes).
- **Ventanas:** `09:00–10:00`, `12:00–13:00`, `16:00–16:30`.
- **Duración → bloque** (redondeo hacia arriba): 9 min → 15, 24 min → 30,
  47 min → 60. Un video de más de 60 min no cabe y se pospone.
- No se usa ningún tramo que solape un evento de Google Calendar o un recordatorio
  existente.

Detalle completo en [`AGENT_RULES.md`](./AGENT_RULES.md).

---

## Puesta en marcha (una sola vez)

### 1. Crea la playlist "Por ver"
En YouTube crea una playlist (privada o no listada) llamada **"Por ver"** y ahí
guarda los videos que quieras agendar. Copia su **ID**: está en la URL de la
playlist como `...?list=PLxxxxxxxxxxxx` (el valor que empieza con `PL`).

> La lista nativa "Ver más tarde" **no** sirve: Google no la expone por API.

### 2. Configura el acceso a la YouTube Data API
En [Google Cloud Console](https://console.cloud.google.com/):

1. Crea (o elige) un proyecto.
2. **APIs & Services → Library →** habilita **"YouTube Data API v3"**.
3. **APIs & Services → OAuth consent screen:** configúrala (tipo *External*,
   modo *Testing* basta) y agrega tu propio correo como *Test user*.
4. **APIs & Services → Credentials → Create credentials → OAuth client ID →**
   tipo **Desktop app**. Descarga el JSON (`client_secret_xxx.json`).

### 3. Genera el refresh token
En tu máquina local:

```bash
pip install -r requirements.txt
python scripts/get_refresh_token.py /ruta/al/client_secret.json
```

Autoriza tu cuenta en el navegador. El script imprime tres valores:
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` y `GOOGLE_REFRESH_TOKEN`.

### 4. Carga las variables en el entorno de Claude Code
En la configuración del **entorno** de tu proyecto en Claude Code on the web,
define estas cuatro variables (ver `.env.example`):

| Variable | Valor |
|----------|-------|
| `GOOGLE_CLIENT_ID` | del paso 3 |
| `GOOGLE_CLIENT_SECRET` | del paso 3 |
| `GOOGLE_REFRESH_TOKEN` | del paso 3 |
| `YOUTUBE_PLAYLIST_ID` | el ID `PL...` del paso 1 |

Además, asegúrate de que la **política de red** del entorno permita el acceso a
`googleapis.com` (necesario para llamar a la API de YouTube).

> Notion y Google Calendar **no** necesitan secretos aquí: se usan a través de
> los conectores (MCP) ya autenticados en tu sesión de Claude Code.

### 5. Programa la rutina
Crea un **trigger programado** en Claude Code on the web que abra una sesión
sobre este repositorio y ejecute el comando:

```
/agendar-videos
```

con periodicidad **semanal, domingos 17:00 (America/Mexico_City)**.

---

### 6. (Recomendado) Verifica la app ante Google

El scope `youtube.force-ssl` es un scope **restringido/sensible**. Mientras la
app no complete la verificación de Google, el `GOOGLE_REFRESH_TOKEN` puede
dejar de funcionar cada 1–2 semanas (aunque el estado de publicación diga
"En producción"), obligando a regenerarlo a mano. Para eliminar ese problema:

1. **Activa GitHub Pages** en este repo: *Settings → Pages → Source: Deploy
   from a branch → Branch: `main` /`docs`*, con **dominio personalizado**
   (campo *Custom domain*) apuntando a un subdominio propio — ver `docs/CNAME`.
   Requiere un registro DNS `CNAME` en el proveedor del dominio:
   `<subdominio>` → `hector-reyes-dev.github.io`. Esto publica:
   - Homepage: `https://youtube-scheduler.hectorcreative.dev/`
   - Política de privacidad: `.../privacy.html`

   > Un subdominio de `github.io` **no sirve** para la verificación de marca
   > de Google: pide que el dominio esté "registrado a tu nombre", y
   > `github.io` es de GitHub, Inc. Se necesita un dominio propio (aunque sea
   > como subdominio de uno que ya tengas).
2. En **Google Cloud Console → Google Auth Platform → Branding**, agrega esas
   dos URLs en *Página principal de la aplicación* y *Vínculo a la Política de
   Privacidad*, y agrega el dominio raíz (`hectorcreative.dev`) como dominio
   autorizado.
3. Desde la misma pantalla, inicia el flujo de **verificación** ("Publicar
   app" / "Prepare for verification"). Google pedirá justificar el scope
   `youtube.force-ssl` (usar el texto de `docs/privacy.html` como base) y,
   posiblemente, un video corto mostrando el consentimiento OAuth y el uso del
   scope.
4. La revisión puede tardar de días a un par de semanas. Hasta que se
   apruebe, sigue aplicando la limitación de tokens de corta duración.

## Uso manual / pruebas

```bash
# 1. Ver qué hay en la playlist (no escribe nada en Notion):
python -m src.main extract -o videos.json

# 2. Ensayo del agendado completo, sin crear ni borrar nada:
/agendar-videos dry-run

# 3. Corrida real:
/agendar-videos

# Borrado manual de items concretos (normalmente lo hace el comando):
python -m src.main delete --ids PLAYLIST_ITEM_ID_1 PLAYLIST_ITEM_ID_2
```

## Estructura

```
.claude/commands/agendar-videos.md   Comando que ejecuta la sesión programada
AGENT_RULES.md                       Reglas de agendado (fuente de verdad)
src/youtube_client.py                Cliente YouTube: listar/borrar + duración
src/main.py                          CLI: extract / delete
src/config.py                        Variables, ventanas, redondeo, IDs
scripts/get_refresh_token.py         Helper OAuth (uso único)
docs/index.html, docs/privacy.html   Homepage y política de privacidad (GitHub Pages,
                                      para la verificación OAuth de Google)
requirements.txt  .env.example  CLAUDE.md
```

## Notas y limitaciones

- Los videos que no quepan esta semana (sin hueco) o que duren **más de 60 min**
  se quedan en la playlist y se reintentan en la siguiente corrida.
- La rutina respeta tu Google Calendar y tus recordatorios existentes; si quieres
  cambiar días, ventanas o el redondeo, edita `AGENT_RULES.md` y `src/config.py`.

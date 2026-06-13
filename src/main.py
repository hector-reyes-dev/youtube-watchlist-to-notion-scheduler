"""CLI para la parte de YouTube del flujo.

Subcomandos:
  extract            Lista los videos de la playlist "Por ver" e imprime JSON.
                     Cada item incluye duración (min) y el playlist_item_id
                     necesario para borrarlo después.
  delete --ids ...   Borra de la playlist los playlist_item_id indicados
                     (los videos ya agendados en Notion).

El agendado en Notion / chequeo de Google Calendar NO ocurre aquí: lo realiza
Claude Code en la sesión programada vía los conectores MCP, usando el JSON que
produce `extract` y las reglas de AGENT_RULES.md.
"""

from __future__ import annotations

import argparse
import json
import sys

from . import config, youtube_client


def _cmd_extract(args: argparse.Namespace) -> int:
    videos = youtube_client.list_playlist_videos()
    payload = []
    for v in videos:
        d = v.to_dict()
        d["block_min"] = config.round_up_to_block(v.duration_min)  # >60 min -> 60
        payload.append(d)

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"{len(payload)} videos escritos en {args.output}", file=sys.stderr)
    else:
        print(text)
    return 0


def _cmd_delete(args: argparse.Namespace) -> int:
    if args.dry_run:
        print(
            f"[dry-run] se borrarían {len(args.ids)} items: {', '.join(args.ids)}",
            file=sys.stderr,
        )
        return 0
    deleted = youtube_client.delete_playlist_items(args.ids)
    print(f"Borrados {len(deleted)} items de la playlist.", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="src.main", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser("extract", help="Lista videos de la playlist → JSON")
    p_extract.add_argument(
        "-o",
        "--output",
        help="Archivo de salida (por defecto stdout)",
        default=None,
    )
    p_extract.set_defaults(func=_cmd_extract)

    p_delete = sub.add_parser("delete", help="Borra items de la playlist por id")
    p_delete.add_argument(
        "--ids",
        nargs="+",
        required=True,
        metavar="PLAYLIST_ITEM_ID",
        help="playlist_item_id de los videos ya agendados",
    )
    p_delete.add_argument(
        "--dry-run",
        action="store_true",
        help="No borra; solo muestra qué se borraría",
    )
    p_delete.set_defaults(func=_cmd_delete)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())

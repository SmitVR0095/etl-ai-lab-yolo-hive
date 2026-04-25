#!/usr/bin/env python3
"""Utilidad simple para enviar notificaciones de Telegram desde el proyecto YOLO + Hive.

Variables soportadas por ambiente o por archivo .env.telegram:
  TELEGRAM_BOT_TOKEN=<token_del_bot>
  TELEGRAM_CHAT_ID=<chat_id>

Ejemplos:
  python scripts/telegram_notify.py --message "Sistema iniciado"
  python scripts/telegram_notify.py --photo data/processed/annotated/images/demo.jpg --caption "Detección"
  python scripts/telegram_notify.py --document data/processed/annotated/videos/demo.mp4 --caption "Video anotado"
"""
from __future__ import annotations

import argparse
import os
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env.telegram"


def load_env_file(path: Path = DEFAULT_ENV_FILE) -> Dict[str, str]:
    """Carga pares CLAVE=VALOR desde un archivo .env simple sin depender de python-dotenv."""
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def get_telegram_config() -> tuple[str, str]:
    """Obtiene token y chat_id desde variables de entorno o .env.telegram."""
    env_file = load_env_file()
    token = os.getenv("TELEGRAM_BOT_TOKEN") or env_file.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or env_file.get("TELEGRAM_CHAT_ID", "")
    return token, chat_id


def build_default_prefix() -> str:
    """Retorna prefijo estándar con host y hora local."""
    host = socket.gethostname()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"🖥️ Host: {host}\n🕒 Time: {ts}"


def send_message(token: str, chat_id: str, message: str, parse_mode: str | None = None) -> None:
    """Envía mensaje de texto por Telegram."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    if parse_mode:
        data["parse_mode"] = parse_mode
    response = requests.post(url, data=data, timeout=20)
    response.raise_for_status()


def send_file(
    token: str,
    chat_id: str,
    endpoint: str,
    field_name: str,
    file_path: Path,
    caption: str,
    parse_mode: str | None = None,
) -> None:
    """Envía archivo por Telegram usando sendPhoto, sendDocument o sendVideo."""
    if not file_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {file_path}")
    url = f"https://api.telegram.org/bot{token}/{endpoint}"
    data = {"chat_id": chat_id, "caption": caption}
    if parse_mode:
        data["parse_mode"] = parse_mode
    with file_path.open("rb") as file_obj:
        response = requests.post(url, data=data, files={field_name: file_obj}, timeout=60)
    response.raise_for_status()


def main() -> int:
    parser = argparse.ArgumentParser(description="Enviar notificaciones Telegram del proyecto YOLO + Hive")
    parser.add_argument("--message", default="", help="Mensaje de texto a enviar")
    parser.add_argument("--photo", default="", help="Ruta de imagen a enviar por sendPhoto")
    parser.add_argument("--document", default="", help="Ruta de archivo a enviar por sendDocument")
    parser.add_argument("--video", default="", help="Ruta de video a enviar por sendVideo")
    parser.add_argument("--caption", default="", help="Caption para foto/documento/video")
    parser.add_argument("--parse-mode", default="", choices=["", "Markdown", "HTML"], help="Modo de parseo Telegram")
    parser.add_argument("--optional", action="store_true", help="No falla si faltan credenciales")
    parser.add_argument("--no-prefix", action="store_true", help="No agrega host/hora al mensaje")
    args = parser.parse_args()

    token, chat_id = get_telegram_config()
    if not token or not chat_id:
        msg = "TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no configurado."
        if args.optional:
            print(f"[WARN] {msg}")
            return 0
        print(f"[ERROR] {msg}", file=sys.stderr)
        return 2

    parse_mode = args.parse_mode or None
    prefix = "" if args.no_prefix else build_default_prefix()

    try:
        if args.message:
            message = args.message if not prefix else f"{args.message}\n\n{prefix}"
            send_message(token, chat_id, message, parse_mode=parse_mode)

        caption = args.caption or args.message or "Notificación YOLO + Hive"
        if prefix:
            caption = f"{caption}\n\n{prefix}"

        if args.photo:
            send_file(token, chat_id, "sendPhoto", "photo", Path(args.photo), caption, parse_mode=parse_mode)
        if args.document:
            send_file(token, chat_id, "sendDocument", "document", Path(args.document), caption, parse_mode=parse_mode)
        if args.video:
            send_file(token, chat_id, "sendVideo", "video", Path(args.video), caption, parse_mode=parse_mode)

        if not args.message and not args.photo and not args.document and not args.video:
            send_message(token, chat_id, f"✅ Telegram configurado correctamente.\n\n{prefix}", parse_mode=parse_mode)

        print("[OK] Notificación Telegram enviada")
        return 0
    except Exception as exc:
        if args.optional:
            print(f"[WARN] No se pudo enviar Telegram: {exc}")
            return 0
        print(f"[ERROR] No se pudo enviar Telegram: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

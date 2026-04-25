from __future__ import annotations

import sys
from datetime import datetime


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def info(message: str) -> None:
    print(f"{C.CYAN}ℹ️  [{now()}] {message}{C.RESET}")


def success(message: str) -> None:
    print(f"{C.GREEN}✅ [{now()}] {message}{C.RESET}")


def warning(message: str) -> None:
    print(f"{C.YELLOW}⚠️  [{now()}] {message}{C.RESET}")


def error(message: str) -> None:
    print(f"{C.RED}❌ [{now()}] {message}{C.RESET}", file=sys.stderr)


def step(message: str) -> None:
    print(f"\n{C.BOLD}{C.BLUE}🚀 {message}{C.RESET}")


def model_msg(message: str) -> None:
    print(f"{C.MAGENTA}🧠 {message}{C.RESET}")


def image_msg(message: str) -> None:
    print(f"{C.CYAN}🖼️  {message}{C.RESET}")


def video_msg(message: str) -> None:
    print(f"{C.CYAN}🎬 {message}{C.RESET}")


def camera_msg(message: str) -> None:
    print(f"{C.CYAN}📷 {message}{C.RESET}")


def file_ok(path: str) -> None:
    print(f"{C.GREEN}📄 Archivo generado/actualizado: {path}{C.RESET}")


def folder_ok(path: str) -> None:
    print(f"{C.GREEN}📁 Carpeta validada: {path}{C.RESET}")


def hdfs_msg(message: str) -> None:
    print(f"{C.CYAN}🐘 {message}{C.RESET}")


def hive_msg(message: str) -> None:
    print(f"{C.YELLOW}🐝 {message}{C.RESET}")


def summary(title: str, items: dict[str, object]) -> None:
    print(f"\n{C.BOLD}{C.CYAN}📊 {title}{C.RESET}")
    for key, value in items.items():
        print(f"   {C.BOLD}{key}:{C.RESET} {value}")

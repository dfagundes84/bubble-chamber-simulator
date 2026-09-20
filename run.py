#!/usr/bin/env python3
"""Ponto de entrada único do simulador: sobe o servidor local e abre o
navegador na interface web.

Uso:
    python run.py [--port 8000] [--no-browser]
"""
from __future__ import annotations

import argparse
import sys
import threading
import webbrowser
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def main() -> None:
    parser = argparse.ArgumentParser(description="Simulador de Câmara de Bolhas (BCS)")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    import uvicorn
    from server.main import app

    url = f"http://{args.host}:{args.port}/"
    if not args.no_browser:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    print(f"\n  Simulador de Câmara de Bolhas (BCS) em {url}\n  (Ctrl+C para encerrar)\n")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()

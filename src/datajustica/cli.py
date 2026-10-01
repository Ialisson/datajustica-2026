from __future__ import annotations

import argparse
import json


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="datajustica", description="Atualiza e prepara as bases do DataJustiça."
    )
    parser.add_argument("command", choices=("update", "build", "refresh", "status"))
    command = parser.parse_args().command
    if command in ("update", "refresh"):
        from datajustica.sources.isp_rj import download_latest

        print(json.dumps(download_latest(), ensure_ascii=False, indent=2))
    if command in ("build", "refresh"):
        from datajustica.sources.isp_rj import build_warehouse

        print(json.dumps(build_warehouse(), ensure_ascii=False, indent=2))
    if command == "status":
        from datajustica.storage.warehouse import metadata

        print(json.dumps(metadata(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

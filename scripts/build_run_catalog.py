from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from analysis import build_catalog_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Construye el catalogo reproducible de corridas existentes.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Raiz del repositorio a escanear.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "derived" / "catalog",
        help="Directorio donde se escriben los CSV derivados.",
    )
    parser.add_argument(
        "--skip-latency",
        action="store_true",
        help="Omite la familia opcional data/latency_runs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = build_catalog_outputs(
        repo_root=args.repo_root.resolve(),
        output_dir=args.output_dir.resolve(),
        include_latency=not args.skip_latency,
    )
    printable = {
        key: str(value) if isinstance(value, Path) else value
        for key, value in results.items()
    }
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

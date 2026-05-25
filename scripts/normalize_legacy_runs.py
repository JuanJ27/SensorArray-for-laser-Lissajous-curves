from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from analysis.normalize import build_normalization_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalizes recoverable legacy run metadata into derived CSV outputs.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root to scan.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / "data" / "derived" / "normalized",
        help="Directory where normalized derived CSVs are written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = build_normalization_outputs(
        repo_root=args.repo_root.resolve(),
        output_dir=args.output_dir.resolve(),
    )
    printable = {key: str(value) if isinstance(value, Path) else value for key, value in results.items()}
    print(json.dumps(printable, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

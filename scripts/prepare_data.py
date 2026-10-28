"""Rebuild the auditable local snapshot; use --download to refresh the mirror."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from panganwatch.pipeline import prepare_data


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Unduh ulang CSV publik melalui konfigurasi HTTPS sistem (tanpa menonaktifkan verifikasi TLS)")
    args = parser.parse_args()
    print(json.dumps(prepare_data(ROOT, download=args.download), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

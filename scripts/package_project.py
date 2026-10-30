#!/usr/bin/env python3
"""Package the runnable project, reports, and attributed data snapshot."""

from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "analyst.zip"
DIRECTORIES = ["analyst", "scripts", "sql", "tests", "docs", "data", "reports"]
TOP_FILES = ["app.py", "README.md", "requirements.txt", "requirements.lock.txt", ".gitignore", ".streamlit/config.toml"]


def main():
    OUTPUT.parent.mkdir(exist_ok=True)
    paths = [ROOT / name for name in TOP_FILES]
    for directory in DIRECTORIES:
        paths.extend((ROOT / directory).rglob("*"))
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(paths)):
            if not path.is_file() or path == OUTPUT:
                continue
            if any(part in {"__pycache__", ".venv", ".git", ".pytest_cache"} for part in path.parts):
                continue
            if path.suffix in {".pyc", ".zip", ".log"} or path.name in {"secrets.toml", ".env"}:
                continue
            archive.write(path, Path("analyst") / path.relative_to(ROOT))
    print(f"Paket siap: {OUTPUT} ({OUTPUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()

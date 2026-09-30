"""Build the HA install ZIP from the reviewed custom component files only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent
COMPONENT = ROOT / "custom_components" / "heiko_w600"
VERSION = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))["version"]
OUTPUT = ROOT / "dist" / f"heiko_w600-ha-{VERSION}.zip"


def main() -> None:
    OUTPUT.parent.mkdir(exist_ok=True)
    files = sorted(
        path for path in COMPONENT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as package:
        for path in files:
            if path.is_symlink():
                raise RuntimeError("Symlinks are not permitted in the package")
            info = ZipInfo(path.relative_to(ROOT).as_posix(), (2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            package.writestr(info, path.read_bytes(), compresslevel=9)
    with ZipFile(OUTPUT) as package:
        if package.testzip() is not None:
            raise RuntimeError("Package integrity check failed")
        names = set(package.namelist())
        required = {
            "manifest.json", "__init__.py", "config_flow.py", "coordinator.py",
            "protocol.py", "parameters.json", "number.py", "select.py", "switch.py",
        }
        if not all(f"custom_components/heiko_w600/{name}" in names for name in required):
            raise RuntimeError("Install package is incomplete")
    print(f"{OUTPUT}  sha256={hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}  files={len(files)}")
    (OUTPUT.parent / "SHA256SUMS").write_text(
        f"{hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}  {OUTPUT.name}\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()

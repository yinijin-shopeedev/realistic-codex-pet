#!/usr/bin/env python3
"""Set a generated Codex custom pet as the persisted default pet."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path


PET_ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pet_id", help="Package directory name under ~/.codex/pets")
    parser.add_argument(
        "--codex-home",
        default=os.environ.get("CODEX_HOME") or str(Path.home() / ".codex"),
        help="Codex home directory. Defaults to CODEX_HOME or ~/.codex.",
    )
    parser.add_argument(
        "--state-path",
        default=None,
        help="Override the global state JSON path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print the state change without writing.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"state file is not valid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"state file root must be an object: {path}")
    return data


def atomic_write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n"
    mode = path.stat().st_mode if path.exists() else 0o600
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w") as tmp:
            tmp.write(encoded)
        os.chmod(tmp_path, mode)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def main() -> int:
    args = parse_args()
    pet_id = args.pet_id.strip()
    if not pet_id or not PET_ID_RE.fullmatch(pet_id):
        raise SystemExit("pet_id must be a package directory name using letters, numbers, dot, underscore, or dash")

    codex_home = Path(args.codex_home).expanduser().resolve()
    pet_dir = codex_home / "pets" / pet_id
    pet_json = pet_dir / "pet.json"
    spritesheet = pet_dir / "spritesheet.webp"
    state_path = Path(args.state_path).expanduser().resolve() if args.state_path else codex_home / ".codex-global-state.json"

    missing = [str(path) for path in (pet_json, spritesheet) if not path.is_file()]
    if missing:
        raise SystemExit("missing package file(s): " + ", ".join(missing))

    try:
        manifest = json.loads(pet_json.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"pet.json is not valid JSON: {pet_json}: {exc}") from exc
    if not isinstance(manifest, dict):
        raise SystemExit(f"pet.json root must be an object: {pet_json}")

    state = load_json(state_path)
    atom_state = state.setdefault("electron-persisted-atom-state", {})
    if not isinstance(atom_state, dict):
        raise SystemExit('"electron-persisted-atom-state" must be an object')

    selected_id = f"custom:{pet_id}"
    previous_id = atom_state.get("selected-avatar-id")
    atom_state["selected-avatar-id"] = selected_id

    backup_path = None
    if not args.dry_run:
        if state_path.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_path = state_path.with_name(f"{state_path.name}.bak-{stamp}")
            shutil.copy2(state_path, backup_path)
        atomic_write_json(state_path, state)

    print(
        json.dumps(
            {
                "ok": True,
                "dry_run": args.dry_run,
                "pet_id": pet_id,
                "manifest_id": manifest.get("id"),
                "selected_avatar_id": selected_id,
                "previous_selected_avatar_id": previous_id,
                "state_path": str(state_path),
                "backup_path": str(backup_path) if backup_path else None,
                "note": "Restart or reload Codex if the visible pet does not change immediately.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Patch hatch-pet prompts from default pixel style to realistic pet style."""

from __future__ import annotations

import re
import sys
import json
from pathlib import Path


STYLE = (
    "Style contract: Realistic compact Codex pet sprite: natural pet proportions, "
    "photo-faithful markings and colors, readable eyes/nose/ears/paws, and short fur "
    "texture simplified enough to remain clear at 192x208. Preserve a clean full-body "
    "cutout silhouette and consistent lighting. Do not use pixel-art blockiness, chibi "
    "exaggeration, cartoon mascot styling, anime key art, 3D toy rendering, vector icon "
    "styling, glossy app-icon lighting, heavy outlines, scenery, props, or noisy tiny fur detail."
)

AUTH = (
    "Use this prompt as an authoritative sprite-production spec. Keep it realistic, "
    "compact, and sprite-compatible: a clean small pet cutout with natural proportions, "
    "not a large portrait or scene."
)

RENDERING = (
    "- Keep the rendering as a realistic compact sprite cutout: clear silhouette, "
    "consistent natural fur color, simplified but realistic fur texture, and minimal "
    "tiny detail that would disappear at 192x208."
)


def patch_file(path: Path) -> bool:
    text = path.read_text()
    original = text

    text = re.sub(r"Style contract: .*?\n\n", STYLE + "\n\n", text, count=1, flags=re.S)
    text = re.sub(
        r"Use this prompt as an authoritative sprite-production spec\. .*?\n\n",
        AUTH + "\n\n",
        text,
        count=1,
        flags=re.S,
    )
    text = text.replace(
        "- Keep the rendering sprite-like: chunky silhouette, dark pixel-style outline, limited palette, flat shading, minimal tiny detail.",
        RENDERING,
    )
    text = text.replace("opaque, hard-edged, pixel-style", "opaque, hard-edged")
    text = text.replace("Simplify any high-resolution reference details into the Codex digital pet sprite style.", "Simplify high-resolution photo details into a realistic compact Codex pet sprite.")

    if text != original:
        path.write_text(text)
        return True
    return False


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: patch_realistic_prompts.py <run-dir>", file=sys.stderr)
        return 2

    run_dir = Path(sys.argv[1]).expanduser().resolve()
    if not run_dir.is_dir():
        print(f"run dir not found: {run_dir}", file=sys.stderr)
        return 1

    prompt_paths = [run_dir / "prompts" / "base-pet.md"]
    prompt_paths.extend(sorted((run_dir / "prompts" / "rows").glob("*.md")))

    patched = []
    missing = []
    for path in prompt_paths:
        if not path.exists():
            missing.append(str(path))
            continue
        if patch_file(path):
            patched.append(str(path))

    print(json.dumps({"ok": not missing, "patched": patched, "missing": missing}, ensure_ascii=False))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())

---
name: realistic-codex-pet
description: Use when a user wants to create or repair a realistic Codex custom pet from 3-6 uploaded pet photos, asks for a 写实版 pet, realistic pet sprite, Codex pet package, pet.json, spritesheet.webp, or wants pet photos turned into a loadable Codex desktop pet.
---

# Realistic Codex Pet

Create a realistic-style Codex custom pet from 3-6 pet photos. The final package is:

```text
${CODEX_HOME:-$HOME/.codex}/pets/<pet-id>/
  pet.json
  spritesheet.webp
```

Keep the experience simple for the user: photos plus an optional name are enough.

## Contract

- Atlas: `1536x1872`, 8 columns x 9 rows, each cell `192x208`.
- Required rows: `idle`, `running-right`, `running-left`, `waving`, `jumping`, `failed`, `waiting`, `running`, `review`.
- Background: transparent in the final atlas; unused cells fully transparent.
- Style: realistic compact sprite cutout, preserving natural markings and proportions. Do not use pixel-art/chibi/cartoon defaults unless the user asks.
- Write package, set the default Codex pet, and give upload guidance only after validation passes.

## Tooling

Prefer these local resources:

```text
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
HATCH_PET_DIR="$CODEX_HOME/vendor_imports/skills/skills/.curated/hatch-pet"
SKILL_DIR="$CODEX_HOME/skills/realistic-codex-pet"
PY="${CODEX_PET_PY:-python3}"
```

Use `${PY}` for hatch-pet scripts. If `python3` cannot import Pillow, locate a Codex runtime Python with Pillow or ask permission before installing dependencies. Users can override the interpreter with `CODEX_PET_PY=/abs/path/python`.

Use the built-in `image_gen` path for all visual generation. Do not synthesize pet art with local scripts; scripts may only prepare prompts, ingest selected generated images, extract frames, compose the atlas, validate, and package.

## Workflow

1. Copy uploaded photos into a stable workspace folder such as `refs/<pet-id>/`. Use 3-6 clear photos. If the user gives no name, infer a short pet name.
2. Prepare a run directory:

```bash
$PY "$HATCH_PET_DIR/scripts/prepare_pet_run.py" \
  --pet-name "<Display Name>" \
  --pet-id "<pet-id>" \
  --display-name "<Display Name>" \
  --description "<one short realistic description>" \
  --reference /abs/path/photo-01.jpg \
  --reference /abs/path/photo-02.jpg \
  --output-dir /abs/path/runs/<pet-id>-realistic \
  --pet-notes "<stable identity details from the photos>" \
  --style-notes "Realistic compact digital pet sprite: preserve natural markings, realistic proportions, simplified short fur texture, clean cutout on chroma key." \
  --chroma-key auto \
  --force
```

3. Patch generated prompts for realistic style:

```bash
$PY "$SKILL_DIR/scripts/patch_realistic_prompts.py" /abs/path/runs/<pet-id>-realistic
```

Resolve `scripts/patch_realistic_prompts.py` relative to this skill directory.

4. Generate and record the base image first. The base prompt must ask for one full-body realistic compact sprite on a flat pure blue `#0000FF` chroma-key background. Use the uploaded photos as identity references.

```bash
$PY "$HATCH_PET_DIR/scripts/record_imagegen_result.py" \
  --run-dir /abs/path/runs/<pet-id>-realistic \
  --job-id base \
  --source /abs/path/to/generated/ig_*.png
```

5. Run job status. Generate row strips with subagents when the user has explicitly approved subagents or the current environment allows them. If not, generate rows sequentially. Every row generation must use the prompt file plus the manifest input images.

```bash
$PY "$HATCH_PET_DIR/scripts/pet_job_status.py" --run-dir /abs/path/runs/<pet-id>-realistic
```

Start with `idle` and `running-right`; inspect both before continuing.

6. After `running-right` is recorded, derive `running-left` by mirror only when the pet has no side-specific accessory, readable text, or direction-dependent markings:

```bash
$PY "$HATCH_PET_DIR/scripts/derive_running_left_from_running_right.py" \
  --run-dir /abs/path/runs/<pet-id>-realistic \
  --confirm-appropriate-mirror \
  --decision-note "<why mirroring preserves identity>"
```

7. Record every selected row output with `record_imagegen_result.py`. Use `--force` only when replacing a row that was partially copied but still pending in `imagegen-jobs.json`.

8. Finalize once `pet_job_status.py` reports `complete: 10`:

```bash
$PY "$HATCH_PET_DIR/scripts/finalize_pet_run.py" \
  --run-dir /abs/path/runs/<pet-id>-realistic \
  --skip-videos \
  --package-dir "${CODEX_HOME:-$HOME/.codex}/pets/<pet-id>"
```

Use `--skip-videos` unless `ffmpeg` is available. Missing videos do not block the pet package.

9. After validation passes, set the generated package as the current Codex pet:

```bash
$PY "$SKILL_DIR/scripts/set_default_pet.py" "<pet-id>"
```

The selected avatar id uses the package directory name, not `pet.json.id`. For `~/.codex/pets/mango/`, the persisted value must be `custom:mango`.

If the command is blocked by filesystem sandboxing, request permission to update `${CODEX_HOME:-$HOME/.codex}/.codex-global-state.json`. If Codex is running and the visible pet does not change immediately, tell the user to restart or reload Codex because the app can keep this state in memory and write it back asynchronously.

10. Guide the user to publish the pet at `https://codex-pets.net/#/upload`. The current upload page accepts the two package files directly:

- `pet.json`
- `spritesheet.webp`

For real pets, choose kind `animal`. Tags are optional; useful tags include `animal`, `realistic`, `cat`, `dog`, or the pet name. Do not tell the user to upload a zip to this site unless the live page explicitly asks for one.

## Row Generation Handoff

For each row, give the generator or subagent:

- row id and prompt file path
- all manifest input images with roles
- instruction to return only `selected_source=/.../ig_*.png` and a one-sentence QA note

QA before recording:

- exact frame count for the row
- one complete pet per frame slot
- same individual pet identity as the base
- realistic compact sprite style, not pixel art/chibi/cartoon
- flat removable blue background
- no guide lines, text, scenery, shadows, detached effects, clipping, or slot crossing

## Verification

Before saying the pet is complete, run fresh verification:

```bash
jq '{ok, format, mode, width, height, errors, warnings}' /abs/path/runs/<pet-id>-realistic/final/validation.json
jq '{ok, errors, warnings, rows: [.rows[] | {state, ok, expected_frames, actual_frames}]}' /abs/path/runs/<pet-id>-realistic/qa/review.json
sips -g pixelWidth -g pixelHeight "${CODEX_HOME:-$HOME/.codex}/pets/<pet-id>/spritesheet.webp"
sed -n '1,120p' "${CODEX_HOME:-$HOME/.codex}/pets/<pet-id>/pet.json"
$PY "$SKILL_DIR/scripts/set_default_pet.py" "<pet-id>" --dry-run
```

Also inspect `qa/contact-sheet.png` visually. Report videos as skipped when `ffmpeg` is unavailable.

## Default Pet Verification

After running `set_default_pet.py`, verify the selected id:

```bash
jq -r '."electron-persisted-atom-state"."selected-avatar-id"' "${CODEX_HOME:-$HOME/.codex}/.codex-global-state.json"
```

Expected output:

```text
custom:<pet-id>
```

If the package directory is `<pet-id>` but `pet.json.id` differs, keep using `custom:<pet-id>`.

## Upload Handoff

When the local pet is complete and defaulted, give the user the exact file paths:

```text
${CODEX_HOME:-$HOME/.codex}/pets/<pet-id>/pet.json
${CODEX_HOME:-$HOME/.codex}/pets/<pet-id>/spritesheet.webp
```

Then open or link `https://codex-pets.net/#/upload` and tell them to select those two files, set kind to `animal`, add optional tags, and submit. The site derives preview/poster/share images in the browser from the uploaded spritesheet.

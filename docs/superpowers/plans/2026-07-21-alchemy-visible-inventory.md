# Alchemy Visible-Inventory Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a MaaFramework task that verifies the synthesis page, selects the largest visible small-gear and small-stone stacks with row-major tie-breaking, confirms quantity 1, and verifies the two filled slots without starting synthesis.

**Architecture:** JSON Pipeline owns the UI state machine and failure boundaries. A narrow Python custom recognition adapter delegates deterministic ordering to pure modules for grid geometry, OCR quantity validation, and candidate selection, then returns a small safe click box. MaaFramework remains responsible for template matching, OCR, clicks, logs, and failure screenshots.

**Tech Stack:** MaaFramework/MaaFw 5.11.1, MFAAvalonia, Python 3.13, pytest, JSONC Pipeline, `@nekosu/maa-tools` 1.0.23, Win32 FramePool capture.

---

## File map

- `requirements-dev.txt`: pinned Agent and test dependencies.
- `agent/selection.py`: candidate model and maximum/tie policy.
- `agent/inventory_grid.py`: 1280×720 first-screen grid geometry.
- `agent/stack_quantity.py`: strict OCR quantity validation.
- `agent/item_selector.py`: Maa custom-recognition adapter.
- `assets/interface.json`: Win32 controller, Agent and task entry.
- `assets/resource/pipeline/alchemy.json`: synthesis state machine and helper nodes.
- `assets/resource/image/alchemy/`: inventory and filled-slot templates.
- `tests/`: unit, config and screenshot-fixture tests.
- `tools/prepare_alchemy_fixtures.py`: normalize supplied screenshots and crop templates.
- `tools/sync_dev_runtime.py`: copy assets and Agent into the existing local MFA runtime.

### Task 1: Prepare the development environment

**Files:**
- Create: `requirements-dev.txt`
- Modify: `.gitignore`
- Create: `tests/fixtures/.gitkeep`

- [ ] Add `.venv/` and `.create-maa-project/` to `.gitignore`.

- [ ] Create `requirements-dev.txt`:

```text
MaaFw==5.11.1
pytest==8.4.2
jsonschema==4.26.0
referencing==0.37.0
json-with-comments==1.0.2
Pillow==11.3.0
```

- [ ] Install all dependencies and OCR assets:

```powershell
npm ci
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
git submodule update --init --recursive
.\.venv\Scripts\python.exe tools\configure.py
```

Expected: all commands exit 0 and `assets/resource/model/ocr/{det.onnx,keys.txt,rec.onnx}` exist.

- [ ] Verify MaaFw:

```powershell
.\.venv\Scripts\python.exe -c "import importlib.metadata, maa; print(importlib.metadata.version('MaaFw')); print(maa.__file__)"
```

Expected: version `5.11.1`, matching the existing local MaaFramework runtime, and a path inside `.venv`.

- [ ] Commit:

```powershell
git add .gitignore requirements-dev.txt tests/fixtures/.gitkeep
git commit -m "chore: prepare alchemy development environment"
```

### Task 2: Implement deterministic selection with TDD

**Files:**
- Create: `agent/__init__.py`
- Create: `agent/selection.py`
- Create: `tests/test_selection.py`

- [ ] Write failing tests covering a single candidate, different quantities, a 200/200 tie resolved by row then column, an empty list, and non-positive quantities. Core assertions:

```python
def test_selects_largest_quantity() -> None:
    assert select_best([Candidate(0, 3, 19, 0.99), Candidate(1, 0, 200, 0.85)]).quantity == 200


def test_tie_uses_row_major_position_not_template_score() -> None:
    selected = select_best([Candidate(1, 0, 200, 0.99), Candidate(0, 3, 200, 0.85)])
    assert (selected.row, selected.column) == (0, 3)
```

- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_selection.py -v` and verify it fails because `agent.selection` is absent.

- [ ] Implement:

```python
from dataclasses import dataclass


class SelectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class Candidate:
    row: int
    column: int
    quantity: int
    template_score: float

    def __post_init__(self) -> None:
        if self.row < 0 or self.column < 0:
            raise ValueError("row and column must be non-negative")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")


def select_best(candidates: list[Candidate]) -> Candidate:
    if not candidates:
        raise SelectionError("no valid candidates")
    return min(candidates, key=lambda item: (-item.quantity, item.row, item.column))
```

- [ ] Rerun the test and expect all cases to pass.

- [ ] Commit `agent/__init__.py`, `agent/selection.py`, and `tests/test_selection.py` with message `feat: select largest visible stack deterministically`.

### Task 3: Model the visible inventory grid with TDD

**Files:**
- Create: `agent/inventory_grid.py`
- Create: `tests/test_inventory_grid.py`

- [ ] Write failing tests for centre-to-cell mapping, rejection outside the grid and pitch gaps, quantity ROI containment, and a safe click rectangle at least 20 pixels from cell edges.

- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_inventory_grid.py -v` and verify the module import fails.

- [ ] Implement immutable `GridPosition` and `InventoryGrid` types using the measured 720p constants:

```python
INVENTORY_GRID = InventoryGrid(
    origin_x=844,
    origin_y=153,
    columns=4,
    rows=5,
    cell_width=90,
    cell_height=90,
    pitch_x=97,
    pitch_y=97,
    quantity_offset=(50, 55, 40, 35),
    safe_click_offset=(33, 28, 24, 24),
)
```

`position_for_point` rejects coordinates outside actual cell rectangles. `position_for_box` computes the box centre and delegates to it. `cell_box`, `quantity_box`, and `safe_click_box` return `(x, y, width, height)`.

- [ ] Rerun `tests/test_inventory_grid.py`; expect all tests to pass.

- [ ] Commit with message `feat: model visible alchemy inventory grid`.

### Task 4: Validate stack quantities with TDD

**Files:**
- Create: `agent/stack_quantity.py`
- Create: `tests/test_stack_quantity.py`

- [ ] Write failing tests for `200`, no OCR result, non-numeric text, zero, confidence `0.69`, and more than one numeric OCR result.

```python
def test_accepts_one_confident_positive_integer() -> None:
    assert parse_quantity([OcrResult("200", 0.98)]) == 200


def test_multiple_numbers_fail() -> None:
    with pytest.raises(QuantityError, match="exactly one"):
        parse_quantity([OcrResult("20", 0.99), OcrResult("0", 0.99)])
```

- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_stack_quantity.py -v` and verify the module import fails.

- [ ] Implement `QuantityError` and `parse_quantity(results, minimum_score=0.70)`. Keep only stripped text matching `^[1-9][0-9]*$`, require exactly one numeric result, reject low confidence, and return the integer.

- [ ] Rerun `tests/test_stack_quantity.py`; expect all tests to pass.

- [ ] Commit with message `feat: validate visible stack quantities`.

### Task 5: Add the Maa custom-recognition adapter with TDD

**Files:**
- Create: `agent/item_selector.py`
- Modify: `agent/main.py`
- Create: `tests/test_item_selector.py`
- Delete: `agent/my_reco.py`
- Delete: `agent/my_action.py`

- [ ] Create fake Maa result/context helpers and failing tests that prove: largest quantity wins, same-cell matches are deduplicated, ties are row-major, any unreliable candidate quantity returns a miss, and the returned box equals `safe_click_box`.

- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_item_selector.py -v` and verify `agent.item_selector` is absent.

- [ ] Register `VisibleStackSelector` as `pln_select_visible_stack`. Parse this node parameter:

```json
{
  "candidate_node": "Alchemy.GearCandidates",
  "quantity_node": "Alchemy.StackQuantity",
  "target": "gear"
}
```

- [ ] Implement the adapter data flow:

```python
match_detail = context.run_recognition(candidate_node, argv.image)
for match in match_detail.filtered_results:
    position = INVENTORY_GRID.position_for_box(match.box)
    # Keep the highest match.score per position.
    quantity_detail = context.run_recognition(
        quantity_node,
        argv.image,
        pipeline_override={quantity_node: {"roi": list(INVENTORY_GRID.quantity_box(position))}},
    )
    quantity = parse_quantity(quantity_detail.filtered_results)
selected = select_best(candidates)
return CustomRecognition.AnalyzeResult(
    box=INVENTORY_GRID.safe_click_box(GridPosition(selected.row, selected.column)),
    detail=diagnostics,
)
```

On invalid parameters, no candidates, invalid grid positions, or unreliable quantities, return `CustomRecognition.AnalyzeResult(box=None, detail={"target": target, "error": reason, "candidates": diagnostics})`. Do not click inside the recognizer.

- [ ] Import `item_selector` from `agent/main.py`; delete the demo action and recognition modules.

- [ ] Run all four Agent test modules; expect all tests to pass.

- [ ] Commit with message `feat: expose visible-stack Maa recognizer`.

### Task 6: Normalize screenshots and generate templates

**Files:**
- Create: `tools/prepare_alchemy_fixtures.py`
- Create: `tests/test_prepare_alchemy_fixtures.py`
- Create: `tests/fixtures/alchemy_inventory_720.png`
- Create: `tests/fixtures/alchemy_dialog_720.png`
- Create: `tests/fixtures/alchemy_filled_720.png`
- Create: `assets/resource/image/alchemy/{gear_inventory,stone_inventory,gear_slot,stone_slot}.png`

- [ ] Write failing tests that `normalize_game_client` returns `(1280, 720)`, strips the title bar from a `1433×849` source, and rejects a client aspect ratio differing from 16:9 by more than one percent.

- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_prepare_alchemy_fixtures.py -v`; expect the module import to fail.

- [ ] Implement Pillow normalization with client crop `(1, 46, 1432, 849)` and `Image.Resampling.LANCZOS`, plus named crop rectangles. Inventory crops must exclude green level digits, quantities, and cell borders; filled-slot crops must come from fixed slot ROIs.

- [ ] Generate assets:

```powershell
.\.venv\Scripts\python.exe tools\prepare_alchemy_fixtures.py `
  --inventory "C:\Users\hk\AppData\Local\Temp\codex-clipboard-c9129423-a9f7-4f72-bf3a-7a23fce4a3ee.png" `
  --dialog "C:\Users\hk\AppData\Local\Temp\codex-clipboard-6b466520-b333-4c91-ac30-f2be743ad538.png" `
  --filled "C:\Users\hk\AppData\Local\Temp\codex-clipboard-38ecc54b-b96d-4fdf-9cd6-5b6a09cef781.png"
```

Expected: three 1280×720 fixtures and four non-empty template PNGs.

- [ ] Visually verify every generated image. Adjust only named crop rectangles when a crop contains dynamic text or crosses a border, then rerun the tests and generator.

- [ ] Commit with message `test: add 720p alchemy recognition fixtures`.

### Task 7: Define ProjectInterface and Pipeline with config tests

**Files:**
- Modify: `assets/interface.json`
- Create: `assets/resource/default_pipeline.json`
- Delete: `assets/resource/pipeline/my_task.json`
- Create: `assets/resource/pipeline/alchemy.json`
- Create: `tests/test_project_config.py`

- [ ] Write failing JSONC tests asserting project name `pln-auto`, Agent args `./agent/main.py`, the only task entry `Alchemy.EnsureUI`, gear/stone selector parameters, and absence of the text `合成开始` from serialized Pipeline data.

- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_project_config.py -v`; expect failure against the template project.

- [ ] Configure the interface controller exactly as:

```jsonc
{
  "name": "Win32",
  "type": "Win32",
  "display_short_side": 720,
  "win32": {
    "class_regex": "UnityWndClass",
    "window_regex": "飘流幻境新世界",
    "screencap": "FramePool",
    "mouse": "PostMessageWithCursorPos",
    "keyboard": "PostMessageWithCursorPos"
  }
}
```

Enable `{"child_exec":"python","child_args":["./agent/main.py"]}` and expose one default task named `炼金第一屏选材`.

- [ ] Implement this Pipeline chain:

```text
Alchemy.EnsureUI -> Alchemy.SortReady -> Alchemy.SelectGear
-> Alchemy.WaitGearDialog -> Alchemy.ConfirmGear -> Alchemy.SelectStone
-> Alchemy.WaitStoneDialog -> Alchemy.ConfirmStone -> Alchemy.VerifyFilled
```

`EnsureUI` OCRs `合成` in the top-left ROI. `SortReady` OCRs `物等小→大` and fails if absent. Selector nodes use `recognition: Custom`, `custom_recognition: pln_select_visible_stack`, `action: Click`, and Task 5 parameters. Wait nodes OCR `输入数量`; confirm nodes OCR and click `确定`. `VerifyFilled` uses `And` with gear in the top-slot ROI and stone in the right-slot ROI.

Helper nodes `GearCandidates`, `StoneCandidates`, and `StackQuantity` use inventory ROI `[844,153,381,478]`. Candidate thresholds start at `0.82`. Quantity OCR uses regex `^[1-9][0-9]*$`; the Agent overrides its ROI per grid cell.

The first version verifies ascending sort instead of opening a sort popup whose menu state has no supplied fixture.

- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_project_config.py -v
npx maa-tools check
.\.venv\Scripts\python.exe tools\validate_schema.py --schema-dir deps/tools --resource-dirs assets/resource --exclude-dirs assets/resource/announcement --interface-files assets/interface.json
```

Expected: all commands exit 0.

- [ ] Commit with message `feat: add minimal visible-inventory alchemy pipeline`.

### Task 8: Verify recognition on screenshots

**Files:**
- Modify: `maatools.config.mts`
- Modify: `assets/resource/pipeline/alchemy.json`
- Modify: template PNGs only when fixture evidence requires it

- [ ] Add MaaTools cases proving page, sort, gear candidates, and stone candidates hit the inventory fixture; dialog hits only the dialog fixture; both slot subnodes hit the filled fixture; and filled verification misses the empty inventory fixture.

- [ ] Run `npx maa-tools test`; expect every fixture group to print green and exit 0.

- [ ] For a false result, inspect `maatoolsErrorDetails.json` and Maa draw output, then make one bounded change to a crop, ROI, or threshold. Do not lower a candidate threshold below `0.75` without a negative fixture proving unrelated items remain misses.

- [ ] Run the full non-live suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
npx maa-tools check
npx maa-tools test
.\.venv\Scripts\python.exe tools\validate_schema.py --schema-dir deps/tools --resource-dirs assets/resource --exclude-dirs assets/resource/announcement --interface-files assets/interface.json
```

Expected: every command exits 0.

- [ ] Commit with message `test: verify alchemy recognition fixtures`.

### Task 9: Sync the development runtime with TDD

**Files:**
- Create: `tools/sync_dev_runtime.py`
- Create: `tests/test_sync_dev_runtime.py`
- Modify locally only: `.create-maa-project/runtime/mfaa/win-x64/config/maa_option.json`

- [ ] Write a failing `tmp_path` test asserting `sync_runtime` copies `assets/interface.json`, `assets/resource`, and `agent` while preserving unrelated runtime files.

- [ ] Run `.\.venv\Scripts\python.exe -m pytest tests/test_sync_dev_runtime.py -v`; expect the module import to fail.

- [ ] Implement `sync_runtime(project_root, runtime_root)`: resolve roots, require `runtime_root/MFAAvalonia.exe`, copy the interface with `shutil.copy2`, and copy resource/Agent with `shutil.copytree(..., dirs_exist_ok=True)`. Never delete or modify `config`, `logs`, `libs`, or `runtimes`.

- [ ] Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_sync_dev_runtime.py -v
.\.venv\Scripts\python.exe tools\sync_dev_runtime.py --runtime .create-maa-project\runtime\mfaa\win-x64
```

Expected: the test passes and the real sync reports the three copied destinations.

- [ ] Set runtime-local options to `logging: true`, `save_on_error: true`, `save_draw: true`, and `stdout_level: 7`. Verify `git status --short` does not list the runtime.

- [ ] Commit with message `chore: sync project into development runtime`.

### Task 10: Run live no-consumption acceptance

**Files:**
- Modify tracked recognition assets or ROI values only when live evidence demonstrates a mismatch
- Inspect local runtime logs and debug images

- [ ] Confirm the game shows the synthesis page, `物等小→大`, empty synthesis slots, and both targets on the first screen. Stop if a material is already selected.

- [ ] Launch the local runtime:

```powershell
Start-Process -FilePath ".create-maa-project\runtime\mfaa\win-x64\MFAAvalonia.exe" -WorkingDirectory ".create-maa-project\runtime\mfaa\win-x64" -WindowStyle Normal
```

Connect the Win32 controller and run `炼金第一屏选材` once.

- [ ] Verify the selected gear is the first row-major maximum, the stone is the maximum, both dialogs remain at quantity 1, top/right slots contain gear/stone, `合成开始` was never clicked, and logs contain `Tasker.Task.Succeeded` without `PipelineNode.Failed`.

- [ ] Demonstrate failure handling once by moving off the synthesis page, running the task, and confirming failure at `Alchemy.EnsureUI` plus a new `debug/on_error` image. Return the game to the synthesis page afterward.

- [ ] Close MFAAvalonia and run fresh final verification:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
npx maa-tools check
npx maa-tools test
.\.venv\Scripts\python.exe tools\validate_schema.py --schema-dir deps/tools --resource-dirs assets/resource --exclude-dirs assets/resource/announcement --interface-files assets/interface.json
git status --short
```

Expected: all test/check commands exit 0 and no runtime, model, log, or debug file is tracked.

- [ ] If live evidence required tracked calibration, commit it with `fix: calibrate alchemy selection against live capture`. Do not create an empty commit.

## Completion checklist

- [ ] First-screen scope is enforced by the fixed grid ROI.
- [ ] Every visible target candidate has a reliable numeric quantity before success.
- [ ] Selection ordering is `(-quantity, row, column)`.
- [ ] Clicks use the custom recognizer's small safe box.
- [ ] Missing page, sort, item, quantity, dialog, confirm button, or final slot fails.
- [ ] A demonstrated failure produces an error screenshot.
- [ ] Pipeline contains no synthesis-start action.
- [ ] Unit, config, schema, fixture-recognition, and live checks have fresh evidence.

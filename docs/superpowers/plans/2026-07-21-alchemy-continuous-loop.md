# Continuous Alchemy Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the one-shot material-placement Pipeline with a JSON-driven continuous alchemy loop using small gear as main material and grass mushroom or small stone as secondary material.

**Architecture:** Keep all control flow in `alchemy.json`. Template matching identifies items and slot state inside fixed 1280×720 ROIs; OCR identifies page text, dialogs, start, and stop. Exhaustion reaches a successful terminal node, while unrecognized UI states time out so MaaFramework saves an error screenshot.

**Tech Stack:** MaaFramework Pipeline JSON, PNG template matching, MFAAvalonia Win32 controller, `@nekosu/maa-tools` schema validation.

---

### Task 1: Create minimal recognition templates

**Files:**
- Create: `assets/resource/image/alchemy/gear.png`
- Create: `assets/resource/image/alchemy/grass_mushroom.png`
- Create: `assets/resource/image/alchemy/small_stone.png`
- Create: `assets/resource/image/alchemy/empty_main.png`
- Create: `assets/resource/image/alchemy/empty_sub.png`

- [ ] **Step 1: Crop templates from the existing 1280×720 MaaFramework failure screenshot**

Use `debug/on_error/2026.07.21-17.17.50.225_Alchemy.ClickGear200.png` as the lossless source. Crop only the icon body or question-mark body, excluding stack numbers and green item-level digits:

```text
gear.png           = (860, 188, 61, 43)
grass_mushroom.png = (1055, 274, 59, 57)
small_stone.png    = (856, 472, 55, 51)
empty_main.png     = (510, 150, 70, 80)
empty_sub.png      = (675, 280, 70, 80)
```

- [ ] **Step 2: Visually verify every crop**

Expected: each file contains one icon only; inventory templates contain no quantity text, and empty-slot templates contain the question mark without neighboring slots.

- [ ] **Step 3: Commit the templates**

```powershell
git add assets/resource/image/alchemy
git commit -m "feat: add continuous alchemy templates"
```

### Task 2: Replace the one-shot Pipeline with the loop state machine

**Files:**
- Modify: `assets/resource/pipeline/alchemy.json`

- [ ] **Step 1: Define page and slot-state nodes**

Keep the existing `Alchemy.EnsureUI` and `Alchemy.EnsureSort` OCR checks. Add these branches:

```text
EnsureSort -> [MainFilled, MainEmpty]
MainFilled -> [SubFilled, SubEmpty]
MainEmpty -> [RefillMain, NormalEnd]
SubEmpty -> [RefillSub, NormalEnd]
SubFilled -> StartAlchemy
```

Use fixed slot ROIs and templates:

```text
main slot ROI = [460, 120, 170, 170]
sub slot ROI  = [620, 245, 170, 170]
MainFilled template = alchemy/gear.png
MainEmpty template  = alchemy/empty_main.png
SubFilled templates = [alchemy/grass_mushroom.png, alchemy/small_stone.png]
SubEmpty template   = alchemy/empty_sub.png
```

If neither the filled nor empty state matches, let the parent node time out and fail rather than guessing.

- [ ] **Step 2: Define inventory refill nodes**

Use inventory ROI `[835, 145, 405, 455]`. `RefillMain` matches `alchemy/gear.png`; `RefillSub` matches both secondary templates. Set `order_by` to `Vertical`, `index` to `0`, and use the recognized box as the click target. Each successful click must flow through its own `WaitDialog -> Confirm -> slot check` chain.

`NormalEnd` is the second candidate after each refill node. It uses `DirectHit` plus `DoNothing` and has no `next`, so an absent required material is a successful task end instead of an error screenshot.

- [ ] **Step 3: Define start, running, finish, and loop nodes**

```text
StartAlchemy: OCR and click 合成开始 in [1010, 570, 240, 120]
WaitRunning: OCR 停止 in [540, 565, 200, 120], timeout 15000
WaitFinished: same 停止 recognition with inverse=true, timeout=-1
DismissResult: DirectHit click [640, 430], post_delay 1000
DismissResult -> [MainFilled, MainEmpty]
```

The Pipeline never clicks `停止`. The absence of `停止` ends the current continuous run and sends control back through slot inspection and refill.

- [ ] **Step 4: Validate the Pipeline JSON**

Run:

```powershell
npx --yes @nekosu/maa-tools check
```

Expected: exit code `0`, with no schema error for `alchemy.json`.

- [ ] **Step 5: Commit the loop Pipeline**

```powershell
git add assets/resource/pipeline/alchemy.json
git commit -m "feat: add continuous alchemy loop"
```

### Task 3: Expose and deploy the continuous task

**Files:**
- Modify: `assets/interface.json`
- Modify locally only: `.create-maa-project/runtime/mfaa/win-x64/interface.json`
- Modify locally only: `.create-maa-project/runtime/mfaa/win-x64/resource/pipeline/alchemy.json`
- Create locally only: `.create-maa-project/runtime/mfaa/win-x64/resource/image/alchemy/*.png`

- [ ] **Step 1: Update the task label and description**

Set the task name to `连续炼金` and describe the exact scope: first inventory screen, small gear main material, grass mushroom or small stone secondary material, stop normally when either required category is unavailable.

- [ ] **Step 2: Copy source assets into the local MFAAvalonia runtime**

Copy `interface.json`, `alchemy.json`, and the five PNG templates to their matching runtime paths. Preserve the runtime instance setting `Win32ControlMouseType=Seize`.

- [ ] **Step 3: Run final static verification**

Run:

```powershell
npx --yes @nekosu/maa-tools check
git diff --check
git status --short
```

Expected: schema check exits `0`; `git diff --check` reports no whitespace error; only intentional source changes are listed.

- [ ] **Step 4: Commit the interface update**

```powershell
git add assets/interface.json
git commit -m "feat: expose continuous alchemy task"
```

### Task 4: Manual game verification

**Files:**
- Inspect: `.create-maa-project/runtime/mfaa/win-x64/debug/maafw.log`
- Inspect on failure: `.create-maa-project/runtime/mfaa/win-x64/debug/on_error/*.png`

- [ ] **Step 1: Restart MFAAvalonia and run with both slots empty**

Expected: the task inserts the first visible small gear, inserts the first visible grass mushroom or small stone, clicks `合成开始`, then recognizes `停止`.

- [ ] **Step 2: Observe one exhaustion/refill cycle**

Expected: after `停止` disappears, the task dismisses the result, detects exactly which slot is empty, refills only that slot, and starts again.

- [ ] **Step 3: Verify normal exhaustion**

Expected: when the empty category has no visible valid candidate in the first inventory screen, the task ends successfully and does not create an `on_error` screenshot.

- [ ] **Step 4: Verify abnormal failure once**

Run the task outside the synthesis page.

Expected: it fails at `Alchemy.EnsureUI` and saves a fresh `debug/on_error` screenshot.


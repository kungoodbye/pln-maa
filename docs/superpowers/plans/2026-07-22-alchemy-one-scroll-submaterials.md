# Alchemy One-Scroll Submaterials Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add steamed bun as a secondary alchemy material and retry secondary-material recognition after one controlled inventory swipe.

**Architecture:** Keep control flow in `alchemy.json`. The first matcher excludes the clipped bottom band; a DirectHit Swipe node moves the inventory up once, a second matcher retries, and a separate confirmation chain restores the inventory to the top after success.

**Tech Stack:** MaaFramework Pipeline JSON, PNG template matching, Pillow, `@nekosu/maa-tools`

---

### Task 1: Establish failing structural verification

**Files:**
- Verify: `assets/resource/pipeline/alchemy.json`

- [ ] Run a Python assertion that requires `steamed_bun.png`, `Alchemy.ScrollSubOnce`, `Alchemy.RefillSubAfterSwipe`, `Alchemy.RestoreInventoryTop`, the safe ROI, and one-swipe coordinates.
- [ ] Confirm it fails because the new behavior is absent.

### Task 2: Add steamed bun template

**Files:**
- Source: `../pln-recode/tools/item-icons/output/icons/s1207.png`
- Create: `assets/resource/image/alchemy/steamed_bun.png`

- [ ] Resize the source to `71×70` with Lanczos filtering.
- [ ] Composite transparent pixels onto pure green for `green_mask`.
- [ ] Crop to `71×55` to exclude the quantity-overlay area.
- [ ] Verify the image is RGB/RGBA, non-empty, and contains both green mask and non-green icon pixels.

### Task 3: Implement the one-scroll Pipeline

**Files:**
- Modify: `assets/resource/pipeline/alchemy.json`

- [ ] Add steamed bun to `SubFilled` and both refill matchers.
- [ ] Change first-pass refill ROI to `[835,145,405,390]`.
- [ ] Add `ScrollSubOnce` with begin `[880,570]`, end `[880,330]`, duration `500`, end hold `100`, and post delay `800`.
- [ ] Add the second-page matcher and independent wait/confirm chain.
- [ ] Add `RestoreInventoryTop` with the reverse swipe.
- [ ] Add a distinct normal-end node after the second matcher fails.
- [ ] Run the structural assertion again and confirm it passes.

### Task 4: Validate and deploy locally

**Files:**
- Copy: `assets/resource/pipeline/alchemy.json` to `.create-maa-project/runtime/mfaa/win-x64/resource/pipeline/alchemy.json`
- Copy: `assets/resource/image/alchemy/steamed_bun.png` to `.create-maa-project/runtime/mfaa/win-x64/resource/image/alchemy/steamed_bun.png`

- [ ] Run `npx --yes @nekosu/maa-tools check`; expect exit code 0.
- [ ] Parse the JSON with PowerShell and Python; expect no error.
- [ ] Copy the source Pipeline and template into the runtime.
- [ ] Compare SHA-256 of source/runtime Pipeline and source/runtime bun template; both pairs must match.
- [ ] Confirm `git diff --check` reports no whitespace errors.

### Task 5: Manual verification handoff

- [ ] Ask the user to restart/reload MFAAvalonia resources.
- [ ] Run from the screenshot-1 state and confirm the log records one upward swipe, a successful secondary-material dialog, and inventory restoration.
- [ ] Confirm no new `Alchemy.RefillSub` timeout screenshot is produced.

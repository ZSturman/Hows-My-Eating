# ChewSense-CycleReviewer

Single-purpose macOS app for **labeling chew cycles** in recorded sessions.
Each chew is defined by three timestamps — **Start → Peak → End** — and the
app writes a compact `review_overrides.json` delta back to the raw session
folder. The Python pipeline merges that delta onto the auto-generated labels.

The reviewer is video-first: the video fills the window, controls and the
chew strip overlay the bottom of the frame, and every label edit happens
either by dragging on the strip or by hotkey at the playhead.

## Build & run

This is a **standard Xcode project** — no SwiftPM, no `.build/`.

```bash
open 04-RealWorldTesting/ChewSense-CycleReviewer/ChewSenseCycleReviewer.xcodeproj
```

Then press **⌘R** in Xcode. Requires macOS 14+ and Xcode 15+.

## Workflow

1. **⌘O** — choose the ChewSense project root (the folder that contains
   `02-DataPipeline/`). Stored in `UserDefaults`; you only do this once.
2. Pick a session in the left sidebar (toggle with **⌘1**).
3. Drag horizontally on the chew strip below the video to add a chew, or
   press **A** at the playhead for a 0.4 s cycle centered on now.
4. Click an existing chew to select it. Drag any of its three white handles
   (Start / Peak / End) to fine-tune. Or press **1 / 2 / 3** to snap that
   marker to the playhead.
5. Press **⌘S** to save.

## Hotkeys

| Key | Action |
| --- | --- |
| Space | Play / pause |
| 1 / 2 / 3 | Set Start / Peak / End at playhead (on selected chew) |
| Drag on strip | Create new chew |
| A | Add chew at playhead |
| D / Delete | Delete selected chew |
| N / P | Next / previous chew |
| [ / ] | Jump to selected chew start / end |
| ← / → | Step ± one frame |
| ⇧ ← / ⇧ → | Skip ± 0.25 s |
| ⌥ ← / ⌥ → | Nudge last-touched marker ± one frame |
| J / L | −1 s / +1 s |
| R | Toggle loop on selected chew |
| ⌘Z / ⇧⌘Z | Undo / redo |
| ⌘S | Save overrides |
| ⌘1 | Toggle sidebar |
| ⌘ / | Toggle help panel |

A complete annotated reference lives inside the app — open it with **⌘ /**.

## Inputs

| File | Source |
| --- | --- |
| `<raw>/<sid>/<sid>.mov` (or .mp4) | Stage 01 |
| `<derived>/<sid>/motion_aligned_labels.csv` | Stage 02b — Phase 2 |
| `<derived>/<sid>/chew_cycles.json` | Stage 02b — Phase 2 |

## Outputs

| File | When written |
| --- | --- |
| `<raw>/<sid>/review_overrides.json` | On Save |
| `<derived>/<sid>/motion_aligned_labels.csv` | On Save (overwritten) |
| `<derived>/<sid>/motion_aligned_labels.auto.csv` | First Save only (snapshot of auto labels) |

The override schema preserves `flipped_eating_spans` and `unreliable_spans`
on round-trip for back-compatibility with the Python merger, even though the
reviewer no longer edits those.

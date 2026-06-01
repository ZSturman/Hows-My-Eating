import SwiftUI

struct HelpPanel: View {
    let onClose: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                Text("How to label chews").font(.headline)
                Spacer()
                Button(action: onClose) { Image(systemName: "xmark") }
                    .buttonStyle(.plain)
            }
            .padding(.horizontal, 14).padding(.vertical, 12)

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 18) {
                    section(title: "The basics") {
                        Text("Each chew has three markers — Start, Peak, End. The Start is when the jaw begins to close, Peak is teeth fully closed, End is teeth fully open again.")
                    }

                    section(title: "Add a chew") {
                        bullet("Drag horizontally on the chew strip below the video to define a Start → End range. Peak is auto-placed at the midpoint.")
                        bullet("Or, with no chew selected, press 1 / 2 / 3 to drop Start / Peak / End markers at the playhead and create a chew.")
                    }

                    section(title: "Adjust an existing chew") {
                        bullet("Click a chew block to select and seek to it.")
                        bullet("Drag a marker to fine-tune: green ▶ Start · yellow ◆ Peak · red ◀ End.")
                        bullet("With a chew selected, press 1, 2, or 3 to snap that marker to the playhead.")
                        bullet("Hold ⌥ + ←/→ to nudge the last-touched marker by one frame.")
                    }

                    section(title: "Zoom & navigate") {
                        bullet("Press = / − to zoom in/out around the playhead, 0 to fit, F to focus the selected chew.")
                        bullet("Mouse wheel pans the timeline; ⌘ or ⌥ + scroll zooms; ⇧ + scroll pans 4× faster.")
                        bullet("During playback the timeline keeps the playhead in frame; pan with the trackpad while paused.")
                        bullet(". and , jump to the next / previous marker on any chew.")
                        bullet("N / P jump between chews; [ / ] jump to start / end of the selected chew.")
                    }

                    section(title: "Review queue") {
                        bullet("Press M to open the Review Queue side panel — the video keeps playing in the main stage.")
                        bullet("The current chew loops automatically; the timeline zooms to fit it.")
                        bullet("Hold S, P, or E and tap ← / → to nudge that marker by one frame (⇧ for 5 frames).")
                    }

                    section(title: "Eating segments") {
                        bullet("Blue bands behind the chew row are eating episodes. Drag either edge of a band to extend or trim it.")
                        bullet("Edits persist as flipped_eating_spans in review_overrides.json.")
                    }

                    section(title: "Verify & advance") {
                        bullet("Press V to mark the selected chew verified and jump to the next unverified one.")
                        bullet("Shift+V toggles the verified state without advancing.")
                        bullet("Press M to open the Review Queue: a focused, looped per-chew review with progress.")
                    }

                    section(title: "Delete or revert") {
                        bullet("Press D or Delete to remove the selected chew.")
                        bullet("Right-click a chew → Revert to auto to undo edits and restore the original.")
                    }

                    section(title: "Hotkeys") {
                        hotkeyTable()
                    }
                }
                .padding(14)
            }
        }
        .frame(maxHeight: .infinity)
        .background(Color(nsColor: .windowBackgroundColor))
        .overlay(alignment: .leading) { Divider() }
    }

    @ViewBuilder
    private func section(title: String, @ViewBuilder _ content: () -> some View) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title).font(.subheadline).bold()
            content()
                .font(.callout)
                .foregroundStyle(.primary)
        }
    }

    private func bullet(_ text: String) -> some View {
        HStack(alignment: .top, spacing: 6) {
            Text("•").foregroundStyle(.secondary)
            Text(text)
        }
    }

    private func hotkeyTable() -> some View {
        let rows: [(String, String)] = [
            ("Space", "Play / pause"),
            ("1 / 2 / 3", "Set Start / Peak / End at playhead"),
            ("Drag on strip", "Create new chew"),
            ("A", "Add chew at playhead (0.4 s wide)"),
            ("D / Delete", "Delete selected chew"),
            ("N / P", "Next / previous chew"),
            (". / ,", "Next / previous marker (any chew)"),
            ("[ / ]", "Jump to selected chew start / end"),
            ("← / →", "Step ± one frame"),
            ("⇧ ← / ⇧ →", "Skip ± 0.25 s"),
            ("⌥ ← / ⌥ →", "Nudge last marker ± one frame"),
            ("S+← / S+→", "Nudge Start ± 1 frame (⇧ for 5)"),
            ("P+← / P+→", "Nudge Peak ± 1 frame (⇧ for 5)"),
            ("E+← / E+→", "Nudge End ± 1 frame (⇧ for 5)"),
            ("J / L", "−1 s / +1 s"),
            ("R", "Toggle loop on selected chew"),
            ("O", "Toggle Raw / Annotated reference video"),
            ("= / − / 0", "Zoom in / out / fit"),
            ("F", "Focus selected chew"),
            ("V", "Verify selected chew & advance"),
            ("⇧V", "Toggle verified (no advance)"),
            ("M / ⌘M", "Open review queue"),
            ("⌘Z / ⇧⌘Z", "Undo / redo"),
            ("⌘S", "Save"),
            ("⌘1", "Toggle sidebar"),
            ("⌘ /", "Toggle this help"),
        ]
        return VStack(alignment: .leading, spacing: 4) {
            ForEach(rows, id: \.0) { row in
                HStack(alignment: .top) {
                    Text(row.0)
                        .font(.system(.caption, design: .monospaced))
                        .frame(width: 110, alignment: .leading)
                        .foregroundStyle(.secondary)
                    Text(row.1).font(.caption)
                }
            }
        }
    }
}

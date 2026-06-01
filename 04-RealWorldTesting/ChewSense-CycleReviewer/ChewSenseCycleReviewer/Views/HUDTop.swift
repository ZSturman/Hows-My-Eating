import SwiftUI

/// Top HUD: session title, dirty/saved indicator, chew counter, action buttons.
struct HUDTop: View {
    @EnvironmentObject var state: ReviewerState
    @EnvironmentObject var playback: PlaybackController
    let toggleSidebar: () -> Void
    let toggleHelp: () -> Void
    let toggleReviewQueue: () -> Void

    var body: some View {
        HStack(spacing: 10) {
            Button(action: toggleSidebar) {
                Image(systemName: "sidebar.left")
            }
            .buttonStyle(.plain)
            .help("Toggle sidebar (⌘1)")

            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 6) {
                    saveDot
                    Text(state.selectedSession?.id ?? "—")
                        .font(.system(.body, design: .monospaced))
                        .lineLimit(1)
                    if state.overrides.verified {
                        Image(systemName: "checkmark.seal.fill").foregroundStyle(.green)
                    }
                }
                Text(state.statusMessage.isEmpty ? "Drag on the strip below to add a chew. 1/2/3 nudges Start/Peak/End." : state.statusMessage)
                    .font(.caption2)
                    .foregroundStyle(.white.opacity(0.7))
                    .lineLimit(1)
            }

            Spacer(minLength: 12)

            counterPill
            verifiedPill
            statsBadge

            Spacer(minLength: 12)

            Button {
                if state.selectedSession?.annotatedVideoURL != nil {
                    state.useAnnotatedVideo.toggle()
                }
            } label: {
                Label(state.useAnnotatedVideo ? "Annotated" : "Raw",
                      systemImage: state.useAnnotatedVideo ? "eye.fill" : "eye")
            }
            .buttonStyle(.plain)
            .disabled(state.selectedSession?.annotatedVideoURL == nil)
            .help(state.selectedSession?.annotatedVideoURL == nil
                  ? "No annotated_video.mp4 for this session"
                  : "Toggle annotated reference video (O)")

            Button(action: toggleReviewQueue) {
                Label("Queue", systemImage: "list.bullet.rectangle.portrait")
            }
            .buttonStyle(.plain)
            .help("Open review queue (M)")

            Button {
                state.toggleVerified()
            } label: {
                Label(state.overrides.verified ? "Verified" : "Mark Verified",
                      systemImage: state.overrides.verified ? "checkmark.seal.fill" : "checkmark.seal")
            }
            .buttonStyle(.plain)
            .help("Toggle verified status")

            Button { state.saveOverrides() } label: {
                Label("Save", systemImage: "square.and.arrow.down.fill")
            }
            .buttonStyle(.plain)
            .help("Save overrides (⌘S)")
            .disabled(state.selectedSession == nil)

            Button(action: toggleHelp) {
                Image(systemName: "questionmark.circle")
            }
            .buttonStyle(.plain)
            .help("Help (⌘/)")
        }
        .font(.callout)
        .foregroundStyle(.white)
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.black.opacity(0.55), in: RoundedRectangle(cornerRadius: 10, style: .continuous))
    }

    private var saveDot: some View {
        Circle()
            .fill(state.isDirty ? Color.orange : Color.green)
            .frame(width: 8, height: 8)
    }

    private var counterPill: some View {
        let total = state.chews.count
        let idx = (state.selectedChewIndex ?? -1) + 1
        return Text(idx > 0 ? "\(idx) / \(total)" : "0 / \(total)")
            .font(.system(.callout, design: .monospaced).monospacedDigit())
            .foregroundStyle(.white)
            .padding(.horizontal, 10).padding(.vertical, 4)
            .background(Color.white.opacity(0.12), in: Capsule())
    }

    private var verifiedPill: some View {
        HStack(spacing: 4) {
            Image(systemName: "checkmark.seal.fill").foregroundStyle(.green)
            Text("\(state.verifiedCount) / \(state.chews.count)")
                .font(.system(.callout, design: .monospaced).monospacedDigit())
        }
        .foregroundStyle(.white)
        .padding(.horizontal, 10).padding(.vertical, 4)
        .background(Color.green.opacity(0.18), in: Capsule())
        .help("Chews verified")
    }

    private var statsBadge: some View {
        let s = state.stats
        return HStack(spacing: 6) {
            statBadge("V", s.visible, .gray)
            statBadge("A", s.added, .blue)
            statBadge("E", s.edited, .orange)
            statBadge("D", s.deleted, .red)
        }
        .font(.system(.caption2, design: .monospaced).monospacedDigit())
    }

    private func statBadge(_ letter: String, _ count: Int, _ color: Color) -> some View {
        HStack(spacing: 3) {
            Text(letter).foregroundStyle(color)
            Text("\(count)").foregroundStyle(.white)
        }
        .padding(.horizontal, 6).padding(.vertical, 2)
        .background(Color.white.opacity(0.08), in: Capsule())
    }
}

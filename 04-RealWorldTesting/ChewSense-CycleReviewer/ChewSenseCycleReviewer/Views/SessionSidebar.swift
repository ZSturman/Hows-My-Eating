import SwiftUI

struct SessionSidebar: View {
    @EnvironmentObject var state: ReviewerState

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Sessions").font(.headline)
                Spacer()
                Button { state.refreshSessions() } label: {
                    Image(systemName: "arrow.clockwise")
                }
                .buttonStyle(.plain)
                .help("Rescan workspace")
            }
            .padding(.horizontal, 10)
            .padding(.top, 10)

            if let root = state.workspaceRoot {
                Text(root.lastPathComponent)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .padding(.horizontal, 10)
            }

            List(state.sessions, selection: bindingForSelection()) { session in
                HStack(spacing: 6) {
                    Circle().fill(statusColor(session.status)).frame(width: 8, height: 8)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(session.id)
                            .font(.system(.caption, design: .monospaced))
                            .lineLimit(1)
                            .truncationMode(.middle)
                        HStack(spacing: 4) {
                            Text(statusLabel(session.status))
                                .foregroundStyle(statusColor(session.status))
                            if session.videoURL == nil {
                                Text("• no video").foregroundStyle(.orange)
                            }
                        }
                        .font(.caption2)
                    }
                    Spacer(minLength: 0)
                }
                .tag(session.id)
                .contentShape(Rectangle())
                .onTapGesture { state.loadSession(session) }
            }
            .listStyle(.sidebar)
        }
    }

    private func bindingForSelection() -> Binding<String?> {
        Binding(
            get: { state.selectedSession?.id },
            set: { newID in
                if let id = newID, let s = state.sessions.first(where: { $0.id == id }) {
                    state.loadSession(s)
                }
            }
        )
    }

    private func statusLabel(_ s: Session.Status) -> String {
        switch s {
        case .auto: "auto"
        case .inReview: "in review"
        case .verified: "verified"
        }
    }

    private func statusColor(_ s: Session.Status) -> Color {
        switch s {
        case .auto: .gray
        case .inReview: .yellow
        case .verified: .green
        }
    }
}

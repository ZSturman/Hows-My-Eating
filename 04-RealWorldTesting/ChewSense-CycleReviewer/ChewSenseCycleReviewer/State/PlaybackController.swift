import AVFoundation
import Foundation

@MainActor
final class PlaybackController: ObservableObject {
    let player = AVPlayer()

    @Published private(set) var currentURL: URL?
    @Published private(set) var currentTime: Double = 0
    @Published private(set) var duration: Double = 0
    @Published private(set) var isPlaying = false
    @Published private(set) var isLooping = false
    @Published var playbackRate: Double = 1.0

    /// Set to true while a marker drag is in progress. While true, loop logic
    /// will not auto-seek so the drag interaction can't be interrupted.
    var suppressLoop: Bool = false

    private var timeObserver: Any?
    private var durationTask: Task<Void, Never>?
    private var rangeStart: Double?
    private var rangeEnd: Double?

    deinit {
        durationTask?.cancel()
        if let timeObserver {
            player.removeTimeObserver(timeObserver)
        }
    }

    func load(url: URL) {
        guard currentURL != url else { return }
        pause()
        removeTimeObserver()
        currentURL = url
        currentTime = 0
        duration = 0
        durationTask?.cancel()
        rangeStart = nil
        rangeEnd = nil
        isLooping = false
        let item = AVPlayerItem(url: url)
        player.replaceCurrentItem(with: item)
        installTimeObserver()
        loadDuration(for: item.asset)
    }

    func play() {
        player.playImmediately(atRate: Float(playbackRate))
        isPlaying = true
    }

    func pause() {
        player.pause()
        isPlaying = false
    }

    func togglePlay() { isPlaying ? pause() : play() }

    func seek(to seconds: Double) {
        let target = clampedTime(seconds)
        currentTime = target
        player.seek(
            to: CMTime(seconds: target, preferredTimescale: 600),
            toleranceBefore: .zero,
            toleranceAfter: .zero
        )
    }

    func skip(by delta: Double) { seek(to: currentTime + delta) }
    func seekToStart() { seek(to: 0) }
    func seekToEnd() {
        guard duration.isFinite, duration > 0 else { return }
        seek(to: max(0, duration - 0.05))
    }

    func setPlaybackRate(_ rate: Double) {
        playbackRate = rate
        if isPlaying { player.rate = Float(rate) }
    }

    func setLoop(start: Double, end: Double, enabled: Bool) {
        guard start < end else { clearLoop(); return }
        rangeStart = max(0, start)
        rangeEnd = max(rangeStart ?? start, end)
        isLooping = enabled
    }

    func clearLoop() {
        rangeStart = nil
        rangeEnd = nil
        isLooping = false
    }

    func playRange(start: Double, end: Double, loop: Bool) {
        setLoop(start: start, end: end, enabled: loop)
        seek(to: start)
        play()
    }

    /// Resume playback within a cycle window. If the playhead is already
    /// inside `[start, end - frameEpsilon)`, leave it where it is so the
    /// reviewer can scrub mid-cycle and press play to continue. Otherwise
    /// (before the cycle, or at/after the last frame) snap back to `start`.
    func playWithinCycle(start: Double, end: Double) {
        let frameEpsilon = 1.0 / 30.0
        if currentTime < start || currentTime >= max(start, end - frameEpsilon) {
            seek(to: start)
        }
        play()
    }

    private func installTimeObserver() {
        timeObserver = player.addPeriodicTimeObserver(
            forInterval: CMTime(seconds: 1.0 / 30.0, preferredTimescale: 600),
            queue: .main
        ) { [weak self] time in
            Task { @MainActor in
                self?.tick(time)
            }
        }
    }

    private func removeTimeObserver() {
        if let timeObserver {
            player.removeTimeObserver(timeObserver)
            self.timeObserver = nil
        }
    }

    private func tick(_ time: CMTime) {
        let seconds = CMTimeGetSeconds(time)
        guard seconds.isFinite else { return }
        currentTime = seconds

        guard !suppressLoop, let rangeEnd, seconds >= rangeEnd else { return }
        if isLooping, let rangeStart {
            seek(to: rangeStart)
            if isPlaying { play() }
        } else {
            pause()
            seek(to: rangeEnd)
        }
    }

    private func loadDuration(for asset: AVAsset) {
        durationTask = Task { [weak self] in
            do {
                let loadedDuration = try await asset.load(.duration)
                let seconds = CMTimeGetSeconds(loadedDuration)
                guard !Task.isCancelled, seconds.isFinite, seconds > 0 else { return }
                await MainActor.run { self?.duration = seconds }
            } catch {
                await MainActor.run { self?.duration = 0 }
            }
        }
    }

    private func clampedTime(_ seconds: Double) -> Double {
        let lowerBound = max(0, seconds)
        guard duration.isFinite, duration > 0 else { return lowerBound }
        return min(lowerBound, duration)
    }
}

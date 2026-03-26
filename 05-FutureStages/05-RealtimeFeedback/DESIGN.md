# Real-Time Feedback Engine - Technical Design

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Real-Time Bite Stream                         │
│                    (from BiteDetector)                           │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      FeedbackEngine                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    State Manager                            │ │
│  │  - meal_start_time      - last_feedback_time               │ │
│  │  - bite_count           - recent_ibis[]                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Rushed    │    │   Good      │    │    Milestone        │ │
│  │   Detector  │    │   Pace      │    │    Tracker          │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
│         │                    │                    │             │
│         └────────────────────┼────────────────────┘             │
│                              ▼                                   │
│                    ┌─────────────────┐                          │
│                    │  Feedback Queue │                          │
│                    │  (with cooldown)│                          │
│                    └────────┬────────┘                          │
│                              │                                   │
└──────────────────────────────┼──────────────────────────────────┘
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Feedback Delivery                            │
│                                                                  │
│    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐ │
│    │  Haptic  │    │  Audio   │    │  Visual  │    │  Push   │ │
│    │ (AirPods)│    │  (Tone)  │    │  (Badge) │    │  Notif  │ │
│    └──────────┘    └──────────┘    └──────────┘    └─────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

## Feedback Triggers

### Corrective Feedback
| Trigger | Condition | Feedback |
|---------|-----------|----------|
| Rushed eating | IBI < 2.0s | Gentle haptic tap |
| Continuous rushed | 3+ rushed in a row | Stronger haptic |

### Positive Reinforcement
| Trigger | Condition | Feedback |
|---------|-----------|----------|
| Good pace | 5.0s ≤ IBI ≤ 15.0s | Occasional positive tap |
| Improvement | Pace improving from rushed | "Nice slowdown!" |

### Milestones
| Trigger | Condition | Feedback |
|---------|-----------|----------|
| Bite count | 10, 25, 50 bites | Visual badge |
| Time milestone | 10, 20, 30 minutes | Visual progress |
| Meal complete | Gap > 5 minutes | Summary notification |

## Feedback Modalities

### Haptic (via AirPods)
- **Technical approach**: iOS `UIImpactFeedbackGenerator` + audio trick
- **Note**: AirPods don't have built-in haptics, but:
  - Brief silent audio pulse can create subtle "tap" sensation
  - Alternatively, use iPhone haptics
- **Intensity levels**: Light (notice), Medium (gentle), Strong (attention)

### Audio
- **Short tones**: Non-intrusive sound effects
- **Voice**: Optional spoken feedback
- **Considerations**: Don't interrupt eating experience

### Visual (On-Device)
- **Badge/Icon**: Status indicator in notification area
- **Widget**: Quick glance at eating progress
- **In-app**: If app is active

## Feedback Timing

### Cooldown System
```python
class FeedbackEngine:
    def _can_deliver_feedback(self) -> bool:
        now = time.time()
        elapsed = now - self._last_feedback_time
        return elapsed >= self.config.min_feedback_interval
```

### Timing Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_feedback_interval` | 10s | Minimum time between feedback |
| `rushed_warning_threshold` | 2s | IBI threshold for rushed |
| `positive_probability` | 0.3 | Chance of positive feedback (avoid spam) |
| `milestone_cooldown` | 60s | Time after milestone before next |

## State Machine

```
                                    ┌────────────┐
                   meal_start() ───▶│   IDLE     │
                                    └──────┬─────┘
                                           │
                                           │ first bite
                                           ▼
                                    ┌────────────┐
              ┌────────────────────▶│  ACTIVE    │◀───────────────────┐
              │                     └──────┬─────┘                    │
              │                            │                          │
              │ bite detected              │ gap > 30s                │
              │                            ▼                          │
              │                     ┌────────────┐                    │
              │                     │   PAUSED   │                    │
              │                     └──────┬─────┘                    │
              │                            │                          │
              └────────────────────────────┘ bite detected            │
                                                                      │
                               gap > 5 min                            │
                                    ▼                                 │
                             ┌────────────┐                           │
                             │ MEAL_DONE  │───────────────────────────┘
                             └────────────┘ meal_start()
```

## Swift Integration

```swift
// FeedbackEngine.swift

class FeedbackEngine: ObservableObject {
    private var config: FeedbackEngineConfig
    private var lastFeedbackTime: Date = .distantPast
    private var biteCount = 0
    
    func onBite(at timestamp: Date, duration: TimeInterval) {
        biteCount += 1
        
        // Calculate IBI
        let ibi = timestamp.timeIntervalSince(lastBiteTime)
        
        // Check triggers
        if ibi < config.rushedThreshold {
            deliverFeedback(.haptic, message: "Slow down")
        } else if config.goodPaceRange.contains(ibi) {
            if shouldDeliverPositive() {
                deliverFeedback(.haptic, message: "Nice pace!")
            }
        }
        
        // Check milestones
        if [10, 25, 50].contains(biteCount) {
            deliverFeedback(.visual, message: "\(biteCount) bites!")
        }
    }
    
    private func deliverFeedback(_ type: FeedbackType, message: String) {
        guard canDeliver() else { return }
        
        switch type {
        case .haptic:
            // iPhone haptic (if in foreground)
            let generator = UINotificationFeedbackGenerator()
            generator.notificationOccurred(.warning)
        case .visual:
            // Post notification
            NotificationCenter.default.post(...)
        case .audio:
            // Play sound
            AudioServicesPlaySystemSound(...)
        }
        
        lastFeedbackTime = Date()
    }
}
```

## Privacy & UX Considerations

1. **Opt-in**: All feedback modalities should be user-controlled
2. **Non-judgmental**: Focus on behavior, not character
3. **Positive framing**: "You're doing great" > "You're eating wrong"
4. **Subtle**: Don't disrupt social eating contexts
5. **Customizable**: Let users adjust sensitivity and frequency

## Testing Strategy

1. **Simulation mode**: Test with recorded bite sequences
2. **A/B testing**: Compare feedback effectiveness
3. **User studies**: Measure behavior change over time
4. **Battery impact**: Monitor power consumption

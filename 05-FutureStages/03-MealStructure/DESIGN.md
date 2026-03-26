# Meal Structure Analysis - Technical Design

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       Bite Event Sequence                        │
│               (from BiteDetector or historical data)             │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                        MealAnalyzer                              │
│                                                                  │
│  ┌──────────────┐   ┌────────────────┐   ┌───────────────────┐  │
│  │  Metric      │   │   Phase        │   │   Pattern         │  │
│  │  Calculator  │   │   Detector     │   │   Analyzer        │  │
│  └──────────────┘   └────────────────┘   └───────────────────┘  │
│         │                   │                     │              │
│         ▼                   ▼                     ▼              │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                      MealMetrics                             ││
│  │  - total_duration         - pace_variability                 ││
│  │  - total_bites            - first_half_pace                  ││
│  │  - eating_efficiency      - second_half_pace                 ││
│  │  - avg_bite_duration      - pace_trend                       ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

## Key Metrics

### Duration Metrics
- **Total meal duration**: Last bite end - first bite start
- **Total chewing time**: Sum of all bite durations
- **Eating efficiency**: chewing_time / total_duration

### Pace Metrics
- **Average inter-bite interval (IBI)**: Mean time between consecutive bite starts
- **IBI variability**: Standard deviation of IBIs
- **Pace trend**: Linear regression slope of IBIs over time

### Bite Metrics
- **Average bite duration**: Mean duration of individual bites
- **Bite duration variability**: Standard deviation
- **Bite count**: Total bites in meal

## Phase Detection

Meals often have distinct phases:
1. **Start phase**: Often faster eating (hungry)
2. **Middle phase**: Steady pace
3. **End phase**: Often slower (satiety signals)
4. **Pauses**: Conversation, drinking, etc.

### Detection Algorithm
```python
def detect_phases(bites, gap_threshold=30.0):
    """Detect phases separated by gaps > gap_threshold seconds."""
    phases = []
    phase_start = 0
    
    for i in range(1, len(bites)):
        gap = bites[i].start_time - bites[i-1].end_time
        if gap > gap_threshold:
            phases.append(MealPhase(
                start_time=bites[phase_start].start_time,
                end_time=bites[i-1].end_time,
                bite_count=i - phase_start,
                ...
            ))
            phase_start = i
    
    # Add final phase
    phases.append(...)
    return phases
```

## Temporal Pattern Analysis

### Pace Trend Detection
```python
def detect_pace_trend(ibis):
    """Detect if eating is slowing, speeding, or stable."""
    from scipy.stats import linregress
    
    x = range(len(ibis))
    slope, _, _, p_value, _ = linregress(x, ibis)
    
    if p_value > 0.05:
        return "stable"
    elif slope > 0:
        return "slowing"
    else:
        return "speeding"
```

### Half-Meal Comparison
```python
def compare_halves(ibis):
    """Compare eating pace between first and second half."""
    mid = len(ibis) // 2
    first_half_avg = np.mean(ibis[:mid])
    second_half_avg = np.mean(ibis[mid:])
    return first_half_avg, second_half_avg
```

## Data Structures

```python
@dataclass
class MealMetrics:
    total_duration: float      # seconds
    total_bites: int
    total_chewing_time: float  # seconds
    avg_bite_duration: float   # seconds
    avg_inter_bite_interval: float  # seconds
    eating_efficiency: float   # ratio
    pace_variability: float    # std of IBIs
    first_half_pace: float
    second_half_pace: float
    pace_trend: str           # "slowing", "speeding", "stable"

@dataclass
class MealPhase:
    start_time: float
    end_time: float
    bite_count: int
    avg_pace: float
    phase_label: str  # "eating", "pause", "fast", "slow"
```

## Visualization

```
Meal Timeline Visualization:

Time:  0s     60s    120s    180s    240s    300s
       │──────│──────│───────│───────│───────│
       
Bites: ▊▊▊▊▊▊▊    ▊▊▊▊▊▊▊▊▊▊    ▊▊▊▊▊▊▊
       └──────┘    └──────────┘    └───────┘
       Phase 1     Pause          Phase 2
       (fast)                     (moderate)
```

## Integration

- Input: `List[BiteEvent]` from BiteDetector
- Output: `MealMetrics` and `List[MealPhase]`
- Can be used for:
  - Post-meal analysis (retrospective)
  - Real-time tracking (during meal)
  - Trend analysis (across multiple meals)

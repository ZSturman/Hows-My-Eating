# Bite Segmentation - Technical Design

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Chewing Probability Stream                   │
│                 (from binary chewing detector)                  │
└─────────────────────────────┬──────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BiteDetector                                │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │  Threshold  │───▶│   Segment   │───▶│  Bite Event List    │ │
│  │  Chewing    │    │   Finder    │    │                     │ │
│  └─────────────┘    └─────────────┘    │  - start_time       │ │
│                                         │  - end_time         │ │
│                                         │  - duration         │ │
│                                         │  - confidence       │ │
│                                         │  - chew_count       │ │
│                                         └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Algorithm: Gap-Based Segmentation

### Step 1: Threshold
```python
is_chewing = probability >= threshold  # default 0.5
```

### Step 2: Find Continuous Segments
```python
segments = []
in_segment = False
for i, chewing in enumerate(is_chewing):
    if chewing and not in_segment:
        segment_start = i
        in_segment = True
    elif not chewing and in_segment:
        segments.append((segment_start, i))
        in_segment = False
```

### Step 3: Merge Adjacent Segments (if gap < min_gap)
```python
merged = [segments[0]]
for seg in segments[1:]:
    gap = timestamps[seg[0]] - timestamps[merged[-1][1]]
    if gap < min_gap_sec:
        merged[-1] = (merged[-1][0], seg[1])  # extend
    else:
        merged.append(seg)
```

### Step 4: Filter by Duration
```python
bites = [s for s in merged if duration(s) >= min_bite_duration]
```

## Data Structures

```python
@dataclass
class BiteEvent:
    start_time: float      # Unix timestamp or session-relative
    end_time: float
    duration: float        # end_time - start_time
    confidence: float      # avg probability during bite
    chew_count: int        # estimated from peak detection (optional)
```

## Integration Points

### Input
- CSV log from real-time app: `timestamp,probability,smoothed,state`
- Or direct stream from `MotionManager` (Swift)

### Output
- JSON array of `BiteEvent` objects
- Stream of events for real-time processing

## Validation Approach

1. **Manual Annotation**: Use video + audio to mark bite boundaries
2. **Metrics**:
   - Bite count accuracy: `|predicted - actual| / actual`
   - Boundary IoU: Intersection over Union of predicted vs. actual bite intervals
   - Precision/Recall for bite detection

## Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_gap_sec` | 3.0 | Minimum gap to separate bites |
| `min_bite_duration` | 1.0 | Minimum duration to consider as bite |
| `probability_threshold` | 0.5 | Threshold for chewing state |
| `peak_prominence` | 0.1 | For chew counting via peak detection |

## Future Enhancements

1. **Learning-based boundaries**: Train model specifically for bite transitions
2. **Chew cycle detection**: Count individual chews within bites
3. **Food type inference**: Different foods have different bite patterns
